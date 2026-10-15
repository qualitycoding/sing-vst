# FROZEN — DO NOT MODIFY (plan/PLAN.md, tests/FROZEN_MANIFEST.sha256). Requirement, decision and claim IDs are cited per test.
import json

import numpy as np
import pytest

from singvst_train import metrics


def _cents_hz(midi: float, c: float) -> float:
    return 440.0 * 2 ** ((midi - 69) / 12) * 2 ** (c / 1200)       # A4 = 440 Hz, MIDI 69 (PK-32)


def test_P09_cents_and_per_note_f0_scoring():
    """T-P09 (D-017, PK-31, PK-33): interior frames only, unvoiced skipped, octave errors counted and excluded.
    Note edges sit half-way between 10 ms frames, so no frame lies on a boundary."""
    assert np.allclose(metrics.cents(np.array([880.0, 440.0]), np.array([440.0, 440.0])), [1200.0, 0.0])
    with pytest.raises(ValueError):
        metrics.cents(np.array([0.0]), np.array([440.0]))
    f0 = np.zeros(210)
    for i in range(0, 106):
        f0[i] = _cents_hz(69, 10.0 if i % 2 == 0 else -10.0)
    for i in range(106, 210):
        f0[i] = _cents_hz(81, 0.0)
    f0[[20, 30, 40]] = 880.0                 # octave errors inside note 1
    f0[50] = 0.0                             # unvoiced inside note 1
    notes = [(0.005, 1.005, 69), (1.005, 2.005, 81)]   # scored frames: 6..95 and 106..195
    s = metrics.score_f0(f0, 0.01, notes, edge_s=0.05, octave_cents=600.0)
    assert s["scored_frames"] == 176 and s["octave_errors"] == 3
    assert s["rms_cents"] == pytest.approx(np.sqrt(86 * 100.0 / 176), rel=1e-9)
    assert s["octave_fraction"] == pytest.approx(3 / 179, rel=1e-12)
    with pytest.raises(ValueError):
        metrics.score_f0(np.zeros(50), 0.01, [(0.0, 0.5, 60)])


def test_P10_extract_f0_tracks_a_harmonic_tone():
    """T-P10 (D-017, C-027, C-046, PK-31): a 15-partial 220 Hz tone, the known answer measured at 0.098 cents RMS.
    Bound 1 cent: the measured value with a 10x margin for platform floating-point differences."""
    pw = metrics.load_pyworld()
    assert hasattr(pw, "harvest") and hasattr(pw, "stonemask")
    sr = 16000
    n = np.arange(2 * sr)
    x = sum((0.5 / k) * np.sin(2 * np.pi * 220 * k * n / sr) for k in range(1, 16))
    x = 0.5 * x / np.max(np.abs(x))
    f0 = metrics.extract_f0(x, sr, frame_period_ms=10.0)
    assert len(f0) == 201                          # frames at 0, 10, ..., 2000 ms
    interior = f0[20:-20]
    assert np.all(interior > 0)
    assert np.sqrt(np.mean(metrics.cents(interior, np.full_like(interior, 220.0)) ** 2)) < 1.0


def test_P11_wer_and_text_normalisation():
    """T-P11 (D-017): word-level Levenshtein after normalisation."""
    assert metrics.normalise_text("Don't, STOP! 'quoted' R2-D2") == ["don't", "stop", "quoted", "r2", "d2"]
    assert metrics.wer("a b c", "a x c") == pytest.approx(1 / 3)
    assert metrics.wer("Hello world", "hello, WORLD") == 0.0
    assert metrics.wer("a b", "a b c d") == pytest.approx(1.0)
    assert metrics.wer("a b c d", "b c") == pytest.approx(0.5)
    assert metrics.wer("a b", "") == pytest.approx(1.0)
    with pytest.raises(ValueError):
        metrics.wer("  ,  ", "a")


def test_P12_judge_and_thresholds_file(root):
    """T-P12 (D-017, A-012, PK-29): the thresholds are unmeasured defaults; judge reports verdicts and status."""
    th = json.loads((root / "eval" / "thresholds.json").read_text(encoding="utf-8"))
    assert th["status"] == "unmeasured-default"
    assert {k: th[k] for k in ("speaker_similarity_min", "similarity_gain_min", "f0_rms_cents_max", "wer_max",
                                "realtime_factor_max")} == {"speaker_similarity_min": 0.75, "similarity_gain_min": 0.15,
                                                            "f0_rms_cents_max": 25.0, "wer_max": 0.25,
                                                            "realtime_factor_max": 1.0}
    good = {"speaker_similarity": 0.80, "guide_similarity": 0.60, "f0_rms_cents": 20.0, "wer": 0.20, "realtime_factor": 0.5}
    j = metrics.judge(good, th)
    assert j == {"speaker_similarity": True, "similarity_gain": True, "f0_rms_cents": True, "wer": True,
                 "realtime_factor": True, "all": True, "status": "unmeasured-default"}
    j2 = metrics.judge(dict(good, guide_similarity=0.70), th)       # gain 0.10 < 0.15
    assert j2["similarity_gain"] is False and j2["all"] is False
    assert metrics.judge(dict(good, wer=0.26), th)["wer"] is False
    with pytest.raises(KeyError):
        metrics.judge({"speaker_similarity": 0.8}, th)
    assert metrics.cosine(np.array([1.0, 0.0]), np.array([1.0, 1.0])) == pytest.approx(2 ** -0.5)
    with pytest.raises(ValueError):
        metrics.cosine(np.zeros(2), np.ones(2))
