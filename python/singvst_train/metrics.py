"""Objective metrics (D-017). Validated on known-answer signals (PK-31). Stubs until plan step S-012."""
from __future__ import annotations

from types import ModuleType

import numpy as np


def load_pyworld() -> ModuleType:
    """Return pyworld's compiled extension ``pyworld.pyworld`` loaded from its file, never through the package: the
    ``.so``/``.pyd`` is found in ``importlib.metadata.distribution("pyworld").files`` and executed with
    ``importlib.machinery.ExtensionFileLoader`` (research/spikes/pyworld-direct), because the package ``__init__``
    imports pkg_resources, which setuptools 84 no longer ships (C-046). Not installed → ``ModuleNotFoundError``."""
    raise NotImplementedError("load_pyworld")


def extract_f0(x: np.ndarray, sr: int, frame_period_ms: float = 10.0) -> np.ndarray:
    """F0 in Hz per frame (0 = unvoiced): harvest (``f0_floor=50``, ``f0_ceil=1100``, ``frame_period``) refined by
    stonemask, on ``x`` as float64. Frame ``i`` is centred at ``i * frame_period_ms / 1000`` s."""
    raise NotImplementedError("extract_f0")


def cents(est_hz: np.ndarray, ref_hz: np.ndarray) -> np.ndarray:
    """``1200 * log2(est / ref)`` elementwise; both arrays must be positive and of equal shape (``ValueError``)."""
    raise NotImplementedError("cents")


def score_f0(f0_hz: np.ndarray, frame_period_s: float, notes: list[tuple[float, float, int]], edge_s: float = 0.05,
             octave_cents: float = 600.0) -> dict:
    """Per-note F0 accuracy (D-017, PK-33). ``notes`` are ``(start_s, end_s, midi)``. A frame ``i`` (time ``i *
    frame_period_s``) is scored for a note when ``start + edge_s <= t <= end - edge_s`` and ``f0_hz[i] > 0``; its error is
    ``cents(f0, 440 * 2**((midi-69)/12))``. Frames with ``|error| > octave_cents`` are octave errors: counted, excluded.
    Returns ``{"rms_cents", "scored_frames", "octave_errors", "octave_fraction"}`` with ``octave_fraction =
    octave_errors / (scored_frames + octave_errors)``. No scorable frame → ``ValueError``."""
    raise NotImplementedError("score_f0")


def normalise_text(s: str) -> list[str]:
    """Lower-case; replace every character that is not a letter, digit, apostrophe or whitespace with a space; split
    on whitespace; strip leading/trailing apostrophes from each word; drop empty words."""
    raise NotImplementedError("normalise_text")


def wer(reference: str, hypothesis: str) -> float:
    """Word error rate: word-level Levenshtein distance (unit costs) / number of reference words, after
    ``normalise_text``. An empty reference raises ``ValueError``."""
    raise NotImplementedError("wer")


def cosine(a: np.ndarray, b: np.ndarray) -> float:
    """Cosine similarity of two non-zero 1-D vectors of equal length (``ValueError`` otherwise)."""
    raise NotImplementedError("cosine")


def judge(report: dict, thresholds: dict) -> dict:
    """Verdicts against ``eval/thresholds.json`` (D-017). ``report`` keys: ``speaker_similarity``,
    ``guide_similarity``, ``f0_rms_cents``, ``wer``, ``realtime_factor``. Returns ``{"speaker_similarity": s >=
    min, "similarity_gain": s - guide >= gain_min, "f0_rms_cents": f0 <= max, "wer": w <= max, "realtime_factor": r <=
    max, "all": all of these, "status": thresholds["status"]}``. A missing report key raises ``KeyError``."""
    raise NotImplementedError("judge")
