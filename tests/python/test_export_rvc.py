# FROZEN — DO NOT MODIFY (plan/PLAN.md, tests/FROZEN_MANIFEST.sha256). Requirement, decision and claim IDs are cited per test.
import numpy as np
import onnx
import onnxruntime as ort
import pytest

from conftest import need_env


@pytest.mark.torch
def test_P19_rvc_synth_export_matches_torch_and_applies_its_noise(tmp_path):
    """T-P19 (D-012, C-003, C-004, C-048, PK-34). Tolerance 1e-3 max-abs: float32 re-ordering error on a signal of
    order 1, about 60 dB below full scale (DR-14 forbids loosening it)."""
    from pathlib import Path
    from singvst_train import export_rvc
    rvc = Path(need_env("SINGVST_RVC_ROOT", "S-013"))
    w = export_rvc.make_test_weights(rvc, tmp_path / "w.pth", seed=0)
    onnx_path = export_rvc.export_synth(rvc, w, tmp_path / "synth.onnx")
    m = onnx.load(str(onnx_path))
    assert [i.name for i in m.graph.input] == ["phone", "phone_lengths", "pitch", "pitchf", "ds", "rnd"]
    assert [o.name for o in m.graph.output] == ["audio"]
    assert export_rvc.parity(rvc, w, onnx_path, seed=0, frames=200) <= 1e-3
    s = ort.InferenceSession(str(onnx_path), providers=["CPUExecutionProvider"])
    rng = np.random.default_rng(1)
    T = 50
    feeds = {"phone": rng.standard_normal((1, T, 768)).astype(np.float32), "phone_lengths": np.array([T], np.int64),
             "pitch": np.full((1, T), 122, np.int64), "pitchf": np.full((1, T), 440.0, np.float32),
             "ds": np.array([0], np.int64), "rnd": np.zeros((1, 192, T), np.float32)}
    a0 = s.run(None, feeds)[0]
    assert a0.shape == (1, 1, T * 480)
    assert np.array_equal(a0, s.run(None, feeds)[0])                     # deterministic for a given rnd
    feeds["rnd"] = rng.standard_normal((1, 192, T)).astype(np.float32)
    assert np.max(np.abs(s.run(None, feeds)[0] - a0)) > 1e-4             # the noise input is applied


@pytest.mark.torch
def test_P19b_content_encoder_export_shapes(tmp_path):
    """T-P19 (D-012, C-020): units [1, floor((N-400)/320)+1, 768] for 16 kHz input."""
    from pathlib import Path
    from singvst_train import export_rvc
    rvc = Path(need_env("SINGVST_RVC_ROOT", "S-013"))
    p = export_rvc.export_content(rvc, tmp_path / "content.onnx")
    s = ort.InferenceSession(str(p), providers=["CPUExecutionProvider"])
    for n in (16000, 16400, 32000):
        x = np.random.default_rng(n).standard_normal((1, n)).astype(np.float32) * 0.1
        assert s.run(None, {"source": x})[0].shape == (1, (n - 400) // 320 + 1, 768)
