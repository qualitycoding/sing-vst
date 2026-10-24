"""Objective metrics (D-017). Validated on known-answer signals (PK-31). Stubs until plan step S-012."""
from __future__ import annotations

import importlib.machinery
import importlib.metadata
import importlib.util
import math
import re

from types import ModuleType

import numpy as np


def load_pyworld() -> ModuleType:
    """Return pyworld's compiled extension ``pyworld.pyworld`` loaded from its file, never through the package: the
    ``.so``/``.pyd`` is found in ``importlib.metadata.distribution("pyworld").files`` and executed with
    ``importlib.machinery.ExtensionFileLoader`` (research/spikes/pyworld-direct), because the package ``__init__``
    imports pkg_resources, which setuptools 84 no longer ships (C-046). Not installed → ``ModuleNotFoundError``."""
    try:
        dist = importlib.metadata.distribution("pyworld")
    except importlib.metadata.PackageNotFoundError as exc:
        raise ModuleNotFoundError("pyworld is not installed") from exc
    candidates = [f for f in (dist.files or []) if f.name.startswith("pyworld.") and f.suffix in (".so", ".pyd")]
    if not candidates:
        raise ModuleNotFoundError("pyworld's compiled extension was not found in its distribution files")
    path = str(dist.locate_file(candidates[0]))
    loader = importlib.machinery.ExtensionFileLoader("pyworld.pyworld", path)
    spec = importlib.util.spec_from_file_location("pyworld.pyworld", path, loader=loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


def extract_f0(x: np.ndarray, sr: int, frame_period_ms: float = 10.0) -> np.ndarray:
    """F0 in Hz per frame (0 = unvoiced): harvest (``f0_floor=50``, ``f0_ceil=1100``, ``frame_period``) refined by
    stonemask, on ``x`` as float64. Frame ``i`` is centred at ``i * frame_period_ms / 1000`` s."""
    pw = load_pyworld()
    signal = np.asarray(x, dtype=np.float64)
    f0, t = pw.harvest(signal, sr, f0_floor=50, f0_ceil=1100, frame_period=frame_period_ms)
    return np.asarray(pw.stonemask(signal, f0, t, sr), dtype=np.float64)


def cents(est_hz: np.ndarray, ref_hz: np.ndarray) -> np.ndarray:
    """``1200 * log2(est / ref)`` elementwise; both arrays must be positive and of equal shape (``ValueError``)."""
    est, ref = np.asarray(est_hz, dtype=np.float64), np.asarray(ref_hz, dtype=np.float64)
    if est.shape != ref.shape:
        raise ValueError(f"shape mismatch: {est.shape} vs {ref.shape}")
    if np.any(est <= 0) or np.any(ref <= 0):
        raise ValueError("frequencies must be positive")
    return 1200.0 * np.log2(est / ref)


def score_f0(f0_hz: np.ndarray, frame_period_s: float, notes: list[tuple[float, float, int]], edge_s: float = 0.05,
             octave_cents: float = 600.0) -> dict:
    """Per-note F0 accuracy (D-017, PK-33). ``notes`` are ``(start_s, end_s, midi)``. A frame ``i`` (time ``i *
    frame_period_s``) is scored for a note when ``start + edge_s <= t <= end - edge_s`` and ``f0_hz[i] > 0``; its error is
    ``cents(f0, 440 * 2**((midi-69)/12))``. Frames with ``|error| > octave_cents`` are octave errors: counted, excluded.
    Returns ``{"rms_cents", "scored_frames", "octave_errors", "octave_fraction"}`` with ``octave_fraction =
    octave_errors / (scored_frames + octave_errors)``. No scorable frame → ``ValueError``."""
    errors: list[np.ndarray] = []
    octave_errors = 0
    times = np.arange(len(f0_hz)) * frame_period_s
    for start, end, midi in notes:
        mask = (times >= start + edge_s) & (times <= end - edge_s) & (np.asarray(f0_hz) > 0)
        if not mask.any():
            continue
        err = cents(np.asarray(f0_hz)[mask], np.full(int(mask.sum()), 440.0 * 2.0 ** ((midi - 69) / 12)))
        far = np.abs(err) > octave_cents
        octave_errors += int(far.sum())
        errors.append(err[~far])
    kept = np.concatenate(errors) if errors else np.zeros(0)
    scored = int(kept.size)
    if scored + octave_errors == 0:
        raise ValueError("no scorable frame")
    rms = float(np.sqrt(np.mean(kept ** 2))) if scored else float("nan")
    return {"rms_cents": rms, "scored_frames": scored, "octave_errors": octave_errors,
            "octave_fraction": octave_errors / (scored + octave_errors)}


def normalise_text(s: str) -> list[str]:
    """Lower-case; replace every character that is not a letter, digit, apostrophe or whitespace with a space; split
    on whitespace; strip leading/trailing apostrophes from each word; drop empty words."""
    cleaned = re.sub(r"[^\w\s']|_", " ", s.lower())
    return [w for w in (word.strip("'") for word in cleaned.split()) if w]


def wer(reference: str, hypothesis: str) -> float:
    """Word error rate: word-level Levenshtein distance (unit costs) / number of reference words, after
    ``normalise_text``. An empty reference raises ``ValueError``."""
    ref, hyp = normalise_text(reference), normalise_text(hypothesis)
    if not ref:
        raise ValueError("the reference has no words")
    previous = list(range(len(hyp) + 1))
    for i, rw in enumerate(ref, start=1):
        current = [i]
        for j, hw in enumerate(hyp, start=1):
            current.append(min(previous[j] + 1, current[j - 1] + 1, previous[j - 1] + (rw != hw)))
        previous = current
    return previous[-1] / len(ref)


def cosine(a: np.ndarray, b: np.ndarray) -> float:
    """Cosine similarity of two non-zero 1-D vectors of equal length (``ValueError`` otherwise)."""
    va, vb = np.asarray(a, dtype=np.float64), np.asarray(b, dtype=np.float64)
    if va.ndim != 1 or vb.ndim != 1 or va.shape != vb.shape:
        raise ValueError("vectors must be 1-D and of equal length")
    na, nb = float(np.linalg.norm(va)), float(np.linalg.norm(vb))
    if na == 0.0 or nb == 0.0:
        raise ValueError("vectors must be non-zero")
    return float(np.dot(va, vb) / (na * nb))


def judge(report: dict, thresholds: dict) -> dict:
    """Verdicts against ``eval/thresholds.json`` (D-017). ``report`` keys: ``speaker_similarity``,
    ``guide_similarity``, ``f0_rms_cents``, ``wer``, ``realtime_factor``. Returns ``{"speaker_similarity": s >=
    min, "similarity_gain": s - guide >= gain_min, "f0_rms_cents": f0 <= max, "wer": w <= max, "realtime_factor": r <=
    max, "all": all of these, "status": thresholds["status"]}``. A missing report key raises ``KeyError``."""
    s, g = report["speaker_similarity"], report["guide_similarity"]
    f0, w, rtf = report["f0_rms_cents"], report["wer"], report["realtime_factor"]
    verdicts = {
        "speaker_similarity": bool(s >= thresholds["speaker_similarity_min"]),
        "similarity_gain": bool(s - g >= thresholds["similarity_gain_min"]),
        "f0_rms_cents": bool(f0 <= thresholds["f0_rms_cents_max"]),
        "wer": bool(w <= thresholds["wer_max"]),
        "realtime_factor": bool(rtf <= thresholds["realtime_factor_max"]),
    }
    return dict(verdicts, all=all(verdicts.values()), status=thresholds["status"])
