"""Dataset preparation (D-015, D-017 held-out split, D-025 de-reverb switch). Stubs until plan step S-012."""
from __future__ import annotations

import hashlib
import json
import math
import os
import subprocess

from pathlib import Path

import numpy as np


def split_heldout(files: list[str], seed: int, fraction: float = 0.1) -> tuple[list[str], list[str]]:
    """Deterministic split by file into (train, heldout), both sorted.

    The order of ``files`` does not matter: the files are sorted, then shuffled with ``numpy.random.default_rng(seed)``
    (``rng.permutation``) and the first ``k`` go to heldout, where ``k = max(1, round(fraction * n))`` when ``n >= 2`` and
    ``k = 0`` when ``n < 2``. Duplicate names raise ``ValueError``; ``fraction`` outside ``[0, 0.5]`` raises ``ValueError``.
    """
    if not 0.0 <= fraction <= 0.5:
        raise ValueError(f"fraction must be in [0, 0.5], got {fraction}")
    if len(set(files)) != len(files):
        raise ValueError("duplicate file names")
    ordered = np.array(sorted(files))
    n = len(ordered)
    k = max(1, round(fraction * n)) if n >= 2 else 0
    if n == 0:
        return [], []
    permuted = ordered[np.random.default_rng(seed).permutation(n)]
    return sorted(permuted[k:].tolist()), sorted(permuted[:k].tolist())


def slice_on_silence(x: np.ndarray, sr: int, threshold_db: float = -40.0, min_sec: float = 2.0,
                     max_sec: float = 15.0) -> list[tuple[int, int]]:
    """Non-silent regions as ``[start, end)`` sample ranges, in order.

    Frames are 20 ms (``round(0.02 * sr)`` samples, non-overlapping, the last partial frame included). A frame is loud
    when its RMS in dBFS (``20*log10(rms)``, ``-inf`` for 0) is ``>= threshold_db``. A region is a maximal run of loud
    frames, spanning whole frames clipped to ``len(x)``. Regions shorter than ``min_sec`` are dropped; a region longer
    than ``max_sec`` is split into ``ceil(len / (max_sec * sr))`` chunks of equal length (the last absorbs the remainder
    samples). ``x`` must be 1-D float; otherwise ``ValueError``.
    """
    if x.ndim != 1 or not np.issubdtype(x.dtype, np.floating):
        raise ValueError("x must be a 1-D float array")
    frame = round(0.02 * sr)
    n = len(x)
    n_frames = math.ceil(n / frame) if n else 0
    loud = np.zeros(n_frames, dtype=bool)
    for i in range(n_frames):
        chunk = x[i * frame:(i + 1) * frame].astype(np.float64)
        rms = float(np.sqrt(np.mean(chunk * chunk)))
        loud[i] = rms > 0.0 and 20.0 * math.log10(rms) >= threshold_db
    regions: list[tuple[int, int]] = []
    i = 0
    while i < n_frames:
        if not loud[i]:
            i += 1
            continue
        j = i
        while j < n_frames and loud[j]:
            j += 1
        regions.append((i * frame, min(j * frame, n)))
        i = j
    out: list[tuple[int, int]] = []
    for start, end in regions:
        length = end - start
        if length < min_sec * sr:
            continue
        parts = math.ceil(length / (max_sec * sr))
        if parts <= 1:
            out.append((start, end))
            continue
        size = length // parts
        for k in range(parts):
            out.append((start + k * size, end if k == parts - 1 else start + (k + 1) * size))
    return out


def normalise(x: np.ndarray, target_rms_dbfs: float = -20.0, peak_ceiling_dbfs: float = -1.0) -> np.ndarray:
    """Return ``x * g`` (float32) with ``g`` setting the RMS to ``target_rms_dbfs``, then reduced if needed so the
    absolute peak is at most ``peak_ceiling_dbfs``. An all-zero input is returned unchanged (a copy)."""
    out = np.array(x, copy=True)
    x64 = x.astype(np.float64)
    peak = float(np.max(np.abs(x64))) if x64.size else 0.0
    if peak == 0.0:
        return out
    rms = float(np.sqrt(np.mean(x64 * x64)))
    gain = 10.0 ** (target_rms_dbfs / 20.0) / rms
    ceiling = 10.0 ** (peak_ceiling_dbfs / 20.0)
    if peak * gain > ceiling:
        gain = ceiling / peak
    return (x64 * gain).astype(np.float32)


def build_dataset_manifest(out_dir: Path, segments: list[dict], params: dict) -> dict:
    """Write ``out_dir/dataset.json`` = ``{"params": params, "segments": [...]}`` where each segment dict keeps its keys
    (``file`` relative to ``out_dir``, ``source``, ``start``, ``end``) and gains ``sha256`` of ``out_dir/file``.
    Written atomically (``pipeline.atomic_write_text``), keys sorted, 1-space indent. Returns the dict written.
    A missing segment file raises ``FileNotFoundError``."""
    from singvst_train.pipeline import atomic_write_text
    entries = []
    for seg in segments:
        path = Path(out_dir) / seg["file"]
        if not path.is_file():
            raise FileNotFoundError(f"segment file missing: {path}")
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1 << 20), b""):
                digest.update(chunk)
        entries.append(dict(seg, sha256=digest.hexdigest()))
    manifest = {"params": params, "segments": entries}
    atomic_write_text(Path(out_dir) / "dataset.json", json.dumps(manifest, sort_keys=True, indent=1) + "\n")
    return manifest


def dereverb(in_dir: Path, out_dir: Path) -> list[Path]:
    """Optional de-reverb (D-025, off by default): audio-separator 0.47.0 with
    ``dereverb_mel_band_roformer_anvuew_sdr_19.1729.ckpt`` keeping the ``noreverb`` stem for every ``*.wav`` in
    ``in_dir``. Runs only on the hosted GPU at gate G-004; not unit-tested (C-043: model licence unstated)."""
    python = os.environ.get("SINGVST_SEPARATOR_PYTHON")
    if not python:
        raise RuntimeError("SINGVST_SEPARATOR_PYTHON is not set (the de-reverb tool lives in its own venv, D-025)")
    in_dir, out_dir = Path(in_dir), Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    wavs = sorted(in_dir.glob("*.wav"))
    script = (
        "import sys, pathlib\n"
        "from audio_separator.separator import Separator\n"
        "in_dir, out_dir = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])\n"
        "s = Separator(output_dir=str(out_dir), output_single_stem='noreverb')\n"
        "s.load_model(model_filename='dereverb_mel_band_roformer_anvuew_sdr_19.1729.ckpt')\n"
        "for f in sorted(in_dir.glob('*.wav')):\n"
        "    s.separate(str(f), custom_output_names={'noreverb': f.stem})\n"
    )
    subprocess.run([python, "-c", script, str(in_dir), str(out_dir)], check=True)
    present = {q.name.lower(): q for q in out_dir.iterdir() if q.is_file()}
    missing = [f"{w.stem}.wav" for w in wavs if f"{w.stem}.wav".lower() not in present]
    if missing:
        raise RuntimeError("de-reverb did not write: " + ", ".join(missing))
    return sorted(present[f"{w.stem}.wav".lower()] for w in wavs)
