# FROZEN — DO NOT MODIFY (plan/PLAN.md, tests/FROZEN_MANIFEST.sha256). Requirement, decision and claim IDs are cited per test.
import json

import numpy as np
import pytest

from singvst_train import prepare

ABC_SHA256 = "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"  # FIPS 180-2 B.1


def test_P01_split_heldout_is_deterministic_disjoint_and_order_free():
    """T-P01 (D-017 held-out 10 % by file, D-015)."""
    files = [f"take{i:02d}.wav" for i in range(20)]
    train, held = prepare.split_heldout(files, seed=7, fraction=0.1)
    assert len(held) == 2 and len(train) == 18
    assert set(train).isdisjoint(held) and set(train) | set(held) == set(files)
    assert train == sorted(train) and held == sorted(held)
    assert (train, held) == prepare.split_heldout(list(reversed(files)), seed=7, fraction=0.1)
    rng = np.random.default_rng(7)
    assert held == sorted(np.array(sorted(files))[rng.permutation(20)][:2].tolist())
    assert prepare.split_heldout(["a.wav"], seed=1) == (["a.wav"], [])
    assert len(prepare.split_heldout(["a.wav", "b.wav"], seed=1)[1]) == 1
    assert len(prepare.split_heldout([f"{i}.wav" for i in range(3)], seed=1, fraction=0.1)[1]) == 1
    with pytest.raises(ValueError):
        prepare.split_heldout(["a.wav", "a.wav"], seed=1)
    with pytest.raises(ValueError):
        prepare.split_heldout(["a.wav", "b.wav"], seed=1, fraction=0.6)


def _tone(sec: float, sr: int, amp: float = 0.5) -> np.ndarray:
    return (amp * np.sin(2 * np.pi * 220.0 * np.arange(round(sec * sr)) / sr)).astype(np.float32)


def test_P02_slice_on_silence_keeps_loud_regions_drops_short_splits_long():
    """T-P02 (D-015): 20 ms frames, threshold, min/max rules; region boundaries land on frame edges (PK-27)."""
    sr = 16000
    z = lambda s: np.zeros(round(s * sr), np.float32)
    x = np.concatenate([z(1.0), _tone(3.0, sr), z(1.0), _tone(1.0, sr), z(1.0), _tone(32.0, sr), z(1.0)])
    segs = prepare.slice_on_silence(x, sr, threshold_db=-40.0, min_sec=2.0, max_sec=15.0)
    assert segs[0] == (16000, 64000)
    assert len(segs) == 4                                  # 3 s kept, 1 s dropped, 32 s split into ceil(32/15) = 3
    long_start, long_end = 7 * sr, 39 * sr                # 1 + 3 + 1 + 1 + 1 s precede the 32 s tone
    assert segs[1][0] == long_start and segs[-1][1] == long_end
    assert [b - a for a, b in segs[1:]] == [170666, 170666, 170668]
    assert all(segs[i][1] == segs[i + 1][0] for i in (1, 2))
    assert prepare.slice_on_silence(np.zeros(sr * 5, np.float32), sr) == []
    with pytest.raises(ValueError):
        prepare.slice_on_silence(np.zeros((2, 100), np.float32), sr)


def test_P02b_slice_on_silence_frame_count_includes_the_partial_last_frame():
    """T-P02 (PK-27: a window parameter gets a test of how many items it yields): a loud tail shorter than a frame."""
    sr = 1000                                              # 20 ms = 20 samples
    x = np.concatenate([np.zeros(40, np.float32), np.full(2010, 0.5, np.float32)])
    assert prepare.slice_on_silence(x, sr, min_sec=2.0, max_sec=15.0) == [(40, 2050)]


def test_P03_normalise_sets_rms_then_limits_peak():
    """T-P03 (D-015)."""
    x = (0.01 * np.sin(np.linspace(0, 200 * np.pi, 48000))).astype(np.float32)
    y = prepare.normalise(x, target_rms_dbfs=-20.0, peak_ceiling_dbfs=-1.0)
    assert y.dtype == np.float32
    assert abs(20 * np.log10(np.sqrt(np.mean(y.astype(np.float64) ** 2))) + 20.0) < 0.01
    spiky = x.copy()
    spiky[100] = 1.0
    y2 = prepare.normalise(spiky, -20.0, -1.0)
    assert np.max(np.abs(y2)) <= 10 ** (-1 / 20) + 1e-6
    assert abs(np.max(np.abs(y2)) - 10 ** (-1 / 20)) < 1e-5     # the ceiling, not more reduction than needed
    s = np.zeros(100, np.float32)
    out = prepare.normalise(s)
    assert np.array_equal(out, s) and out is not s


def test_P04_dataset_manifest_records_sha256_and_params(tmp_path):
    """T-P04 (D-015, Rule 9 provenance)."""
    (tmp_path / "seg0.wav").write_bytes(b"abc")
    m = prepare.build_dataset_manifest(tmp_path, [{"file": "seg0.wav", "source": "take1.wav", "start": 0, "end": 3}],
                                       {"sr": 48000})
    on_disk = json.loads((tmp_path / "dataset.json").read_text(encoding="utf-8"))
    assert m == on_disk
    assert on_disk == {"params": {"sr": 48000},
                       "segments": [{"file": "seg0.wav", "source": "take1.wav", "start": 0, "end": 3, "sha256": ABC_SHA256}]}
    with pytest.raises(FileNotFoundError):
        prepare.build_dataset_manifest(tmp_path, [{"file": "missing.wav", "source": "x", "start": 0, "end": 1}], {})
