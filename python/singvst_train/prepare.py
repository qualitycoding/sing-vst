"""Dataset preparation (D-015, D-017 held-out split, D-025 de-reverb switch). Stubs until plan step S-012."""
from __future__ import annotations

from pathlib import Path

import numpy as np


def split_heldout(files: list[str], seed: int, fraction: float = 0.1) -> tuple[list[str], list[str]]:
    """Deterministic split by file into (train, heldout), both sorted.

    The order of ``files`` does not matter: the files are sorted, then shuffled with ``numpy.random.default_rng(seed)``
    (``rng.permutation``) and the first ``k`` go to heldout, where ``k = max(1, round(fraction * n))`` when ``n >= 2`` and
    ``k = 0`` when ``n < 2``. Duplicate names raise ``ValueError``; ``fraction`` outside ``[0, 0.5]`` raises ``ValueError``.
    """
    raise NotImplementedError("split_heldout")


def slice_on_silence(x: np.ndarray, sr: int, threshold_db: float = -40.0, min_sec: float = 2.0,
                     max_sec: float = 15.0) -> list[tuple[int, int]]:
    """Non-silent regions as ``[start, end)`` sample ranges, in order.

    Frames are 20 ms (``round(0.02 * sr)`` samples, non-overlapping, the last partial frame included). A frame is loud
    when its RMS in dBFS (``20*log10(rms)``, ``-inf`` for 0) is ``>= threshold_db``. A region is a maximal run of loud
    frames, spanning whole frames clipped to ``len(x)``. Regions shorter than ``min_sec`` are dropped; a region longer
    than ``max_sec`` is split into ``ceil(len / (max_sec * sr))`` chunks of equal length (the last absorbs the remainder
    samples). ``x`` must be 1-D float; otherwise ``ValueError``.
    """
    raise NotImplementedError("slice_on_silence")


def normalise(x: np.ndarray, target_rms_dbfs: float = -20.0, peak_ceiling_dbfs: float = -1.0) -> np.ndarray:
    """Return ``x * g`` (float32) with ``g`` setting the RMS to ``target_rms_dbfs``, then reduced if needed so the
    absolute peak is at most ``peak_ceiling_dbfs``. An all-zero input is returned unchanged (a copy)."""
    raise NotImplementedError("normalise")


def build_dataset_manifest(out_dir: Path, segments: list[dict], params: dict) -> dict:
    """Write ``out_dir/dataset.json`` = ``{"params": params, "segments": [...]}`` where each segment dict keeps its keys
    (``file`` relative to ``out_dir``, ``source``, ``start``, ``end``) and gains ``sha256`` of ``out_dir/file``.
    Written atomically (``pipeline.atomic_write_text``), keys sorted, 1-space indent. Returns the dict written.
    A missing segment file raises ``FileNotFoundError``."""
    raise NotImplementedError("build_dataset_manifest")


def dereverb(in_dir: Path, out_dir: Path) -> list[Path]:
    """Optional de-reverb (D-025, off by default): audio-separator 0.47.0 with
    ``dereverb_mel_band_roformer_anvuew_sdr_19.1729.ckpt`` keeping the ``noreverb`` stem for every ``*.wav`` in
    ``in_dir``. Runs only on the hosted GPU at gate G-004; not unit-tested (C-043: model licence unstated)."""
    raise NotImplementedError("dereverb")
