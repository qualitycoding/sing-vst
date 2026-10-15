"""RVC v2 → ONNX export with the prior noise as an input (C-003, C-004, C-048, D-012). Stubs until plan step S-013."""
from __future__ import annotations

from pathlib import Path


def export_synth(rvc_root: Path, weights: Path, out_path: Path, opset: int = 17) -> Path:
    """Export ``SynthesizerTrnMs768NSFsid`` (from ``rvc_root``, weights loaded in float32 from the float16 file) as
    ONNX with inputs ``phone`` float[1,T,768], ``phone_lengths`` int64[1], ``pitch`` int64[1,T], ``pitchf`` float[1,T],
    ``ds`` int64[1], ``rnd`` float[1,192,T] (T dynamic) and output ``audio`` float[1,1,T*hop]; the graph computes
    ``z_p = m_p + exp(logs_p) * rnd * 0.66666`` instead of drawing noise. Runs ``onnx.checker``; returns ``out_path``."""
    raise NotImplementedError("export_synth")


def export_content(rvc_root: Path, out_path: Path, opset: int = 17) -> Path:
    """Export RVC's hubert_base (``rvc_root/assets/hubert_base``) final layer as ONNX: input ``source`` float[1,N] at
    16 kHz → output ``units`` float[1,Tc,768] (C-020); returns ``out_path``."""
    raise NotImplementedError("export_content")


def make_test_weights(rvc_root: Path, out_path: Path, seed: int = 0) -> Path:
    """Write a randomly initialised (``torch.manual_seed(seed)``) 48k v2 f0 synthesiser in RVC's inference-weight
    format (C-048: float16 weights, keys config, weight, sr, f0, version) for CI parity tests; returns ``out_path``."""
    raise NotImplementedError("make_test_weights")


def parity(rvc_root: Path, weights: Path, onnx_path: Path, seed: int = 0, frames: int = 200) -> float:
    """Max absolute difference between the torch synthesiser (float32, noise replaced by the same ``rnd``) and
    onnxruntime on random inputs of ``frames`` frames drawn from ``numpy.random.default_rng(seed)``."""
    raise NotImplementedError("parity")
