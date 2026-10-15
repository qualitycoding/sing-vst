# FROZEN — DO NOT MODIFY (plan/PLAN.md, tests/FROZEN_MANIFEST.sha256). Requirement, decision and claim IDs are cited per test.
import json
import math
from pathlib import Path

import pytest

from conftest import need_env
from singvst_train import evaluate, metrics, provenance


def test_P26_transpose_semitones_nearest_whole_shift():
    """T-P26 (D-017): phrases move by whole semitones toward the training data's median pitch (A4 = 440 Hz)."""
    assert evaluate.transpose_semitones([60, 62, 64], 440 * 2 ** ((55 - 69) / 12)) == -7
    assert evaluate.transpose_semitones([60, 62, 64], 440 * 2 ** ((62.4 - 69) / 12)) == 0
    assert evaluate.transpose_semitones([60, 62, 64], 440 * 2 ** ((62.6 - 69) / 12)) == 1
    assert evaluate.transpose_semitones([60, 61], 440 * 2 ** ((60 - 69) / 12)) == 0          # tie 0 / -1 -> 0
    assert evaluate.transpose_semitones([60, 61], 440 * 2 ** ((59 - 69) / 12)) == -1         # tie -1 / -2 -> -1
    with pytest.raises(ValueError):
        evaluate.transpose_semitones([], 220.0)
    with pytest.raises(ValueError):
        evaluate.transpose_semitones([60], 0.0)


def test_P26b_evaluation_phrases_exist_with_reference_text(root):
    """T-P26 (D-017): five phrases, each a MIDI file with a reference text."""
    d = root / "eval" / "phrases"
    stems = sorted(p.stem for p in d.glob("*.mid"))
    assert stems == ["p1", "p2", "p3", "p4", "p5"]
    for s in stems:
        assert metrics.normalise_text((d / f"{s}.txt").read_text(encoding="utf-8"))


@pytest.mark.voice
def test_P20_evaluation_procedure_produces_a_complete_measured_report(tmp_path, root):
    """T-P20 (D-017; unknown outcome, protocol 2B.4): the procedure and report format are frozen, not the values.
    Verdicts are recorded for gate G-001 and are not asserted here (PK-29, PK-35)."""
    voice = Path(need_env("SINGVST_VOICE", "S-017 (gate G-004)"))
    held = Path(need_env("SINGVST_HELDOUT", "S-017 (gate G-004)"))
    binary = Path(need_env("SINGVST_RENDER_BIN", "S-010"))
    rep = evaluate.evaluate_voice(voice, held, root / "eval" / "phrases", binary, tmp_path, seed=0)
    assert set(rep) == set(evaluate.REPORT_KEYS) and rep["status"] == "measured"
    assert json.loads((tmp_path / "report.json").read_text(encoding="utf-8")) == rep
    side = json.loads((tmp_path / "report.json.provenance.json").read_text(encoding="utf-8"))
    assert set(provenance.REQUIRED_KEYS) <= set(side)
    assert rep["phrases"] == ["p1", "p2", "p3", "p4", "p5"] and rep["heldout_files"]
    for s in rep["phrases"]:
        assert (tmp_path / "renders" / f"{s}.converted.wav").exists() and (tmp_path / "renders" / f"{s}.guide.wav").exists()
    for k in ("speaker_similarity", "guide_similarity", "f0_rms_cents", "wer", "guide_wer", "realtime_factor"):
        assert math.isfinite(rep[k])
    assert 0.0 <= rep["octave_fraction"] <= 1.0 and isinstance(rep["transpose_semitones"], int)
    th = json.loads((root / "eval" / "thresholds.json").read_text(encoding="utf-8"))
    verdict = metrics.judge(rep, th)
    (tmp_path / "verdict.json").write_text(json.dumps(verdict, indent=1))
    assert set(verdict) >= {"all", "status"}
