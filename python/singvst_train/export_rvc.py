"""RVC v2 → ONNX export with the prior noise as an input (C-003, C-004, C-048, D-012). Stubs until plan step S-013."""
from __future__ import annotations

import sys
from pathlib import Path


def _rvc_classes(rvc_root: Path) -> dict:
    """RVC's model classes from the pinned checkout (put on ``sys.path``; heavy imports stay inside functions)."""
    root = str(Path(rvc_root).resolve())
    if root not in sys.path:
        sys.path.insert(0, root)
    from infer.module.models import SineGen, SynthesizerTrnMs768NSFsid
    return {"SineGen": SineGen, "SynthesizerTrnMs768NSFsid": SynthesizerTrnMs768NSFsid}


def _load_synth(rvc_root: Path, weights: Path):
    """The v2 f0 synthesiser with float32 weights, without ``enc_q`` and weight norm, in eval mode."""
    import torch

    classes = _rvc_classes(rvc_root)
    ckpt = torch.load(str(weights), map_location="cpu", weights_only=False)
    if ckpt.get("version") != "v2" or ckpt.get("f0") != 1:
        raise ValueError(f"{weights}: only RVC v2 models with pitch guidance (f0) are supported")
    config = list(ckpt["config"])
    config[-3] = ckpt["weight"]["emb_g.weight"].shape[0]
    net = classes["SynthesizerTrnMs768NSFsid"](*config, is_half=False)
    del net.enc_q
    net.load_state_dict({k: v.float() for k, v in ckpt["weight"].items()}, strict=False)
    net.dec.remove_weight_norm()
    net.flow.remove_weight_norm()
    return net.eval()


def _make_attention_dynamic(torch, net) -> None:
    """Replace the relative-position helpers of RVC's windowed self-attention with index-based versions.

    RVC's originals turn the sequence length into Python ints (``int(length)``, ``max(...)``), so tracing bakes in the
    example length and the ONNX graph fails for any other one. These versions give identical values (checked for lengths
    1..200 during development, difference 0.0) and keep the length dynamic."""
    import types

    def patch(attn) -> None:
        w = attn.window_size

        def get_relative_embeddings(self, embeddings, length):
            r = torch.arange(2 * length - 1, device=embeddings.device) - (length - 1)
            index = (r + w).clamp(0, 2 * w)
            keep = ((r >= -w) & (r <= w)).to(embeddings.dtype)
            return embeddings[:, index] * keep[None, :, None]

        def relative_to_absolute(self, x):
            length = x.size(2)
            rows = torch.arange(length, device=x.device)
            index = (rows[None, :] - rows[:, None] + (length - 1)).expand(x.size(0), x.size(1), length, length)
            return torch.gather(x, 3, index)

        def absolute_to_relative(self, x):
            length = x.size(2)
            i = torch.arange(length, device=x.device)[:, None]
            k = torch.arange(2 * length - 1, device=x.device)[None, :]
            j = i + k - (length - 1)
            keep = ((j >= 0) & (j < length)).to(x.dtype)
            index = j.clamp(0, length - 1).expand(x.size(0), x.size(1), length, 2 * length - 1)
            return torch.gather(x, 3, index) * keep

        attn._get_relative_embeddings = types.MethodType(get_relative_embeddings, attn)
        attn._relative_position_to_absolute_position = types.MethodType(relative_to_absolute, attn)
        attn._absolute_position_to_relative_position = types.MethodType(absolute_to_relative, attn)

    for layer in net.enc_p.encoder.attn_layers:
        if layer.window_size is not None:
            patch(layer)


def _SynthExport(torch, net):
    """Wrap ``net`` so ``forward(phone, phone_lengths, pitch, pitchf, ds, rnd)`` is deterministic.

    RVC's ``infer`` draws two kinds of random numbers: the prior noise (replaced by the ``rnd`` input, scaled by 0.66666) and
    the NSF source's additive noise inside ``SineGen`` (``torch.randn_like``). The second one is replaced here by values read
    from ``rnd`` itself (frame-major, each value held for 480 / 192 = 2.5 samples), so one seed fixes the whole output."""
    import numpy as np

    sine_gen_cls = type(net.dec.m_source.l_sin_gen)

    class DeterministicSineGen(sine_gen_cls):
        rnd = None

        def forward(self, f0, upp):
            if self.dim != 1:
                raise ValueError("only harmonic_num == 0 (RVC v2) is supported")
            with torch.no_grad():
                f0 = f0[:, None].transpose(1, 2)                                            # [1, T, 1]
                rad = f0 / self.sampling_rate * torch.arange(1, upp + 1, device=f0.device)  # [1, T, upp]
                rad2 = torch.fmod(rad[..., -1:].float() + 0.5, 1.0) - 0.5
                rad_acc = rad2.cumsum(dim=1).fmod(1.0).to(f0)
                shifted = torch.cat([torch.zeros_like(rad_acc[:, :1]), rad_acc[:, :-1]], dim=1)
                rad = (rad + shifted).reshape(f0.shape[0], -1, 1)
                sine_waves = torch.sin(2 * np.pi * rad) * self.sine_amp                     # the harmonic-0 phase offset is 0
                uv = (f0 > self.voiced_threshold).to(f0.dtype)
                uv = torch.nn.functional.interpolate(uv.transpose(2, 1), scale_factor=float(upp), mode="nearest").transpose(2, 1)
                channels = self.rnd.shape[1]
                per_sample = (torch.arange(upp) * channels) // upp                          # constant: 0..191 for upp 480
                frames = torch.arange(self.rnd.shape[2]) * channels
                index = (frames[:, None] + per_sample[None, :]).reshape(-1)
                source = self.rnd.transpose(1, 2).reshape(-1)[index].reshape(1, -1, 1)
                noise_amp = uv * self.noise_std + (1 - uv) * self.sine_amp / 3
                noise = noise_amp * source
                sine_waves = sine_waves * uv + noise
            return sine_waves, uv, noise

    _make_attention_dynamic(torch, net)
    gen = DeterministicSineGen.__new__(DeterministicSineGen)
    gen.__dict__.update(net.dec.m_source.l_sin_gen.__dict__)
    net.dec.m_source.l_sin_gen = gen

    class Export(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.net = net

        def forward(self, phone, phone_lengths, pitch, pitchf, ds, rnd):
            g = self.net.emb_g(ds).unsqueeze(-1)
            m_p, logs_p, x_mask = self.net.enc_p(phone, pitch, phone_lengths)
            z_p = (m_p + torch.exp(logs_p) * rnd * 0.66666) * x_mask
            z = self.net.flow(z_p, x_mask, g=g, reverse=True)
            gen.rnd = rnd
            return self.net.dec(z * x_mask, pitchf, g=g)

    return Export().eval()


def export_synth(rvc_root: Path, weights: Path, out_path: Path, opset: int = 17) -> Path:
    """Export ``SynthesizerTrnMs768NSFsid`` (from ``rvc_root``, weights loaded in float32 from the float16 file) as
    ONNX with inputs ``phone`` float[1,T,768], ``phone_lengths`` int64[1], ``pitch`` int64[1,T], ``pitchf`` float[1,T],
    ``ds`` int64[1], ``rnd`` float[1,192,T] (T dynamic) and output ``audio`` float[1,1,T*hop]; the graph computes
    ``z_p = m_p + exp(logs_p) * rnd * 0.66666`` instead of drawing noise. Runs ``onnx.checker``; returns ``out_path``."""
    import onnx
    import torch

    net = _load_synth(rvc_root, weights)
    model = _SynthExport(torch, net)
    t = 100
    args = (torch.randn(1, t, 768), torch.tensor([t], dtype=torch.int64), torch.full((1, t), 122, dtype=torch.int64),
            torch.full((1, t), 440.0), torch.tensor([0], dtype=torch.int64), torch.randn(1, net.enc_p.hidden_channels, t))
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    torch.onnx.export(model, args, str(out_path), input_names=["phone", "phone_lengths", "pitch", "pitchf", "ds", "rnd"],
                      output_names=["audio"], opset_version=opset, do_constant_folding=True, dynamo=False,
                      dynamic_axes={"phone": {1: "T"}, "pitch": {1: "T"}, "pitchf": {1: "T"}, "rnd": {2: "T"}, "audio": {2: "N"}})
    onnx.checker.check_model(str(out_path), full_check=True)
    return out_path


def export_content(rvc_root: Path, out_path: Path, opset: int = 17) -> Path:
    """Export RVC's hubert_base (``rvc_root/assets/hubert_base``) final layer as ONNX: input ``source`` float[1,N] at
    16 kHz (N dynamic, no padding) → output ``units`` float[1,Tc,768] with ``Tc = floor((N - 400) / 320) + 1`` (the
    hubert convolution stack: receptive field 400, stride 320; C-020); runs ``onnx.checker``; returns ``out_path``."""
    import onnx
    import torch
    from transformers import HubertModel

    hubert = HubertModel.from_pretrained(str(Path(rvc_root) / "assets" / "hubert_base"), local_files_only=True,
                                         torch_dtype=torch.float32, attn_implementation="eager").eval()

    class _Content(torch.nn.Module):
        def __init__(self, model):
            super().__init__()
            self.model = model

        def forward(self, source):
            return self.model(input_values=source, attention_mask=None, output_hidden_states=False,
                              return_dict=True).last_hidden_state

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    torch.onnx.export(_Content(hubert), (torch.zeros(1, 16000),), str(out_path), input_names=["source"], output_names=["units"],
                      opset_version=opset, do_constant_folding=True, dynamo=False,
                      dynamic_axes={"source": {1: "N"}, "units": {1: "Tc"}})
    onnx.checker.check_model(str(out_path), full_check=True)
    return out_path


def make_test_weights(rvc_root: Path, out_path: Path, seed: int = 0) -> Path:
    """Write a randomly initialised (``torch.manual_seed(seed)``) 48k v2 f0 synthesiser in RVC's inference-weight
    format (C-048: float16 weights, keys config, weight, sr, f0, version) for CI parity tests; returns ``out_path``."""
    import json

    import torch

    classes = _rvc_classes(rvc_root)
    cfg_file = Path(rvc_root) / "configs" / "v2" / "48k.json"
    hps = json.loads(cfg_file.read_text(encoding="utf-8"))
    m, d = hps["model"], hps["data"]
    config = [d["filter_length"] // 2 + 1, 32, m["inter_channels"], m["hidden_channels"], m["filter_channels"], m["n_heads"],
              m["n_layers"], m["kernel_size"], m["p_dropout"], m["resblock"], m["resblock_kernel_sizes"],
              m["resblock_dilation_sizes"], m["upsample_rates"], m["upsample_initial_channel"], m["upsample_kernel_sizes"],
              m["spk_embed_dim"], m["gin_channels"], d["sampling_rate"]]
    torch.manual_seed(seed)
    net = classes["SynthesizerTrnMs768NSFsid"](*config, is_half=False)
    weight = {k: v.half() for k, v in net.state_dict().items() if "enc_q" not in k}
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    torch.save({"weight": weight, "config": config, "info": "test weights", "sr": "48k", "f0": 1, "version": "v2"}, str(out_path))
    return out_path


def parity(rvc_root: Path, weights: Path, onnx_path: Path, seed: int = 0, frames: int = 200) -> float:
    """Max absolute difference between the torch synthesiser (float32, noise replaced by the same ``rnd``) and
    onnxruntime on random inputs of ``frames`` frames drawn from ``numpy.random.default_rng(seed)``."""
    import numpy as np
    import onnxruntime as ort
    import torch

    net = _load_synth(rvc_root, weights)
    model = _SynthExport(torch, net)
    rng = np.random.default_rng(seed)
    voiced = rng.random(frames) > 0.2
    feeds = {
        "phone": rng.standard_normal((1, frames, 768)).astype(np.float32),
        "phone_lengths": np.array([frames], np.int64),
        "pitch": rng.integers(1, 256, (1, frames)).astype(np.int64),
        "pitchf": np.where(voiced, rng.uniform(100.0, 500.0, frames), 0.0).astype(np.float32)[None],
        "ds": np.array([0], np.int64),
        "rnd": rng.standard_normal((1, net.enc_p.hidden_channels, frames)).astype(np.float32),
    }
    with torch.no_grad():
        expected = model(*(torch.from_numpy(feeds[k]) for k in ("phone", "phone_lengths", "pitch", "pitchf", "ds", "rnd"))).numpy()
    session = ort.InferenceSession(str(onnx_path), providers=["CPUExecutionProvider"])
    actual = session.run(None, feeds)[0]
    if actual.shape != expected.shape:
        raise ValueError(f"shape mismatch: onnx {actual.shape}, torch {expected.shape}")
    return float(np.max(np.abs(actual - expected)))
