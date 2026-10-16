"""Held-out evaluation procedure (D-017; unknown outcomes, protocol 2B.4). Stubs until plan step S-015."""
from __future__ import annotations

from pathlib import Path

REPORT_KEYS = ("speaker_similarity", "guide_similarity", "f0_rms_cents", "octave_fraction", "wer", "guide_wer",
               "realtime_factor", "phrases", "transpose_semitones", "heldout_files", "status")
REPEATS = 5  # renders per phrase; the guide's noise is unseeded (C-040, R-018)


def transpose_semitones(phrase_midi: list[int], training_median_hz: float) -> int:
    """Whole-semitone shift ``k`` minimising ``|median(phrase_midi) + k - midi(training_median_hz)|`` with
    ``midi(f) = 69 + 12*log2(f/440)``; ties go to the smaller ``|k|``, then to negative ``k``. Empty input or a
    non-positive frequency → ``ValueError``."""
    raise NotImplementedError("transpose_semitones")


def evaluate_voice(voice_dir: Path, heldout_dir: Path, phrases_dir: Path, render_bin: Path, out_dir: Path,
                   seed: int = 0, lockfile: Path | None = None) -> dict:
    """Run the D-017 procedure (eval/PROCEDURE.md): transpose each phrase in ``phrases_dir`` (``*.mid`` with lyric events),
    render it REPEATS times with ``render_bin`` with and without conversion, and compute, per repeat, Resemblyzer similarity against the mean embedding of the
    held-out recordings, per-note F0 scores (``metrics.score_f0``), Whisper ``small.en`` WER for both renders, and the
    real-time factor. Writes ``out_dir/renders/<phrase>.converted.wav`` and ``<phrase>.guide.wav`` for repeat 0 and
    ``<phrase>.r<r>.converted.wav`` / ``<phrase>.r<r>.guide.wav`` for repeats 1…REPEATS-1 (phrase = MIDI file stem),
    ``out_dir/spread.json`` (per numeric report key: ``values`` per repeat, ``min``, ``max``), ``out_dir/report.json``
    (each numeric metric the mean over repeats; exactly REPORT_KEYS, ``status`` "measured", ``phrases`` the sorted stems,
    ``heldout_files`` the sorted held-out file names) and its provenance sidecar, whose ``lockfile_sha256`` is that of
    ``lockfile`` (default: ``python/requirements-lock.txt`` of the repository holding this package); returns the report. Each phrase's
    reference text is ``<phrase>.txt`` beside its MIDI file. Thresholds are not applied here (``metrics.judge``)."""
    raise NotImplementedError("evaluate_voice")
