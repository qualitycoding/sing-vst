"""Held-out evaluation procedure (D-017; unknown outcomes, protocol 2B.4). Stubs until plan step S-015."""
from __future__ import annotations

from pathlib import Path

REPORT_KEYS = ("speaker_similarity", "guide_similarity", "f0_rms_cents", "octave_fraction", "wer", "guide_wer",
               "realtime_factor", "phrases", "transpose_semitones", "heldout_files", "status")


def transpose_semitones(phrase_midi: list[int], training_median_hz: float) -> int:
    """Whole-semitone shift ``k`` minimising ``|median(phrase_midi) + k - midi(training_median_hz)|`` with
    ``midi(f) = 69 + 12*log2(f/440)``; ties go to the smaller ``|k|``, then to negative ``k``. Empty input or a
    non-positive frequency → ``ValueError``."""
    raise NotImplementedError("transpose_semitones")


def evaluate_voice(voice_dir: Path, heldout_dir: Path, phrases_dir: Path, render_bin: Path, out_dir: Path,
                   seed: int = 0) -> dict:
    """Run the D-017 procedure: transpose each phrase in ``phrases_dir`` (``*.mid`` with lyric events), render it with
    ``render_bin`` with and without conversion, and compute Resemblyzer similarity against the mean embedding of the
    held-out recordings, per-note F0 scores (``metrics.score_f0``), Whisper ``small.en`` WER for both renders, and the
    real-time factor. Writes ``out_dir/renders/<phrase>.converted.wav`` and ``<phrase>.guide.wav`` (phrase = MIDI file
    stem), ``out_dir/report.json`` (exactly REPORT_KEYS, ``status`` "measured", ``phrases`` the sorted stems,
    ``heldout_files`` the sorted held-out file names) and its provenance sidecar; returns the report. Each phrase's
    reference text is ``<phrase>.txt`` beside its MIDI file. Thresholds are not applied here (``metrics.judge``)."""
    raise NotImplementedError("evaluate_voice")
