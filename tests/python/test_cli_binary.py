# FROZEN — DO NOT MODIFY (plan/PLAN.md, tests/FROZEN_MANIFEST.sha256). Requirement, decision and claim IDs are cited per test.
import json
import subprocess

import numpy as np
import pytest
import soundfile as sf

from conftest import need_env

PROVENANCE_KEYS = {"git_commit", "voice_sha256", "params", "seeds", "utc_timestamp", "hardware", "threads", "ort_version",
                   "warnings", "unclipped_peak", "render_seconds", "audio_seconds"}


@pytest.mark.binary
def test_P18_singvst_render_end_to_end_with_the_fixture_voice(tmp_path, root):
    """T-P18 (D-014, D-021, D-031): renders a MIDI file with lyric events, writes float32 mono WAV at 48 kHz soft-clipped
    to <= 0.98, a provenance sidecar, and reports errors with the documented exit codes."""
    binary = need_env("SINGVST_RENDER_BIN", "S-009")
    fx = root / "tests" / "fixtures"
    voice, mid, dic = fx / "voice-convert", fx / "lyrics.mid", fx / "cmudict-mini.dict"
    out = tmp_path / "out.wav"
    r = subprocess.run([binary, "--voice", str(voice), "--midi", str(mid), "--dict", str(dic), "--out", str(out),
                        "--seed", "0"], capture_output=True, text=True, timeout=300)
    assert r.returncode == 0, r.stderr
    info = sf.info(str(out))
    assert (info.samplerate, info.channels, info.subtype) == (48000, 1, "FLOAT")
    y, _ = sf.read(str(out), dtype="float32")
    assert len(y) > 0 and np.max(np.abs(y)) <= 0.98 + 1e-6
    side = json.loads((tmp_path / "out.wav.provenance.json").read_text(encoding="utf-8"))
    assert PROVENANCE_KEYS <= set(side)
    assert side["unclipped_peak"] >= float(np.max(np.abs(y))) - 1e-6
    assert abs(side["audio_seconds"] * 48000 - len(y)) <= 1
    assert side["seeds"] == {"converter": 0}
    chk = subprocess.run([binary, "--check-voice", str(voice)], capture_output=True, text=True, timeout=120)
    assert chk.returncode == 0 and chk.stdout.strip() == "ok voice-convert"
    missing = subprocess.run([binary, "--voice", str(tmp_path / "nope"), "--midi", str(mid), "--out", str(out)],
                             capture_output=True, text=True, timeout=120)
    assert missing.returncode == 2 and "voice" in missing.stderr.lower()
    bad_mid = tmp_path / "bad.mid"
    bad_mid.write_bytes(b"MThd\x00\x00")
    bad = subprocess.run([binary, "--voice", str(voice), "--midi", str(bad_mid), "--out", str(out)],
                         capture_output=True, text=True, timeout=120)
    assert bad.returncode == 2
    usage = subprocess.run([binary], capture_output=True, text=True, timeout=60)
    assert usage.returncode == 2
