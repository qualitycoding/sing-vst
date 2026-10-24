"""Held-out evaluation procedure (D-017; unknown outcomes, protocol 2B.4). Stubs until plan step S-015."""
from __future__ import annotations

import hashlib
import json
import math
import subprocess
from pathlib import Path

import numpy as np

REPORT_KEYS = ("speaker_similarity", "guide_similarity", "f0_rms_cents", "octave_fraction", "wer", "guide_wer",
               "realtime_factor", "phrases", "transpose_semitones", "heldout_files", "status")
REPEATS = 5  # renders per phrase; the guide's noise is unseeded (C-040, R-018)


def _read_mono(path: Path):
    """(float64 mono samples, sample rate) of a wav file, channels averaged."""
    import soundfile as sf

    data, rate = sf.read(str(path), dtype="float64", always_2d=True)
    return data.mean(axis=1), int(rate)


def _midi_notes(path: Path):
    """([(start_beat, end_beat, midi)], bpm) of a MIDI file: beats = ticks / PPQ, bpm from the earliest tempo event (default 120)."""
    import mido

    mid = mido.MidiFile(str(path))
    notes, tempo, tempo_tick = [], 500000, None
    for track in mid.tracks:
        tick, held = 0, {}
        for msg in track:
            tick += msg.time
            if msg.type == "set_tempo" and (tempo_tick is None or tick < tempo_tick):
                tempo, tempo_tick = msg.tempo, tick
            elif msg.type == "note_on" and msg.velocity > 0:
                held[(msg.channel, msg.note)] = tick
            elif msg.type in ("note_off", "note_on") and (msg.channel, msg.note) in held:
                start = held.pop((msg.channel, msg.note))
                notes.append((start / mid.ticks_per_beat, tick / mid.ticks_per_beat, msg.note))
    if not notes:
        raise ValueError(f"no notes in {path}")
    return sorted(notes), 60e6 / tempo


def _write_transposed(src: Path, dst: Path, semitones: int) -> Path:
    """Copy of ``src`` with every note_on/note_off shifted by ``semitones`` (all other events unchanged)."""
    import mido

    mid = mido.MidiFile(str(src))
    for track in mid.tracks:
        for i, msg in enumerate(track):
            if msg.type in ("note_on", "note_off"):
                if not 0 <= msg.note + semitones <= 127:
                    raise ValueError(f"{src.name}: note {msg.note} shifted by {semitones} leaves 0..127")
                track[i] = msg.copy(note=msg.note + semitones)
    dst.parent.mkdir(parents=True, exist_ok=True)
    mid.save(str(dst))
    return dst


def transpose_semitones(phrase_midi: list[int], training_median_hz: float) -> int:
    """Whole-semitone shift ``k`` minimising ``|median(phrase_midi) + k - midi(training_median_hz)|`` with
    ``midi(f) = 69 + 12*log2(f/440)``; ties go to the smaller ``|k|``, then to negative ``k``. Empty input or a
    non-positive frequency → ``ValueError``."""
    if not phrase_midi:
        raise ValueError("no phrase pitches")
    if not training_median_hz > 0:
        raise ValueError(f"training_median_hz must be positive, got {training_median_hz}")
    target = 69.0 + 12.0 * math.log2(training_median_hz / 440.0)
    x = target - float(np.median(np.asarray(phrase_midi, dtype=np.float64)))
    lower = math.floor(x)
    d_lower, d_upper = x - lower, lower + 1 - x
    if abs(d_lower - d_upper) <= 1e-9:
        return int(min((lower, lower + 1), key=lambda k: (abs(k), k)))      # tie: smaller |k|, then negative
    return int(lower if d_lower < d_upper else lower + 1)


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
    import singvst_train
    from singvst_train import metrics, provenance
    from singvst_train.pipeline import atomic_write_text

    voice_dir, heldout_dir, phrases_dir, out_dir = Path(voice_dir), Path(heldout_dir), Path(phrases_dir), Path(out_dir)
    render_bin = Path(render_bin)
    repo_root = Path(singvst_train.__file__).resolve().parents[2]
    lockfile = Path(lockfile) if lockfile is not None else repo_root / "python" / "requirements-lock.txt"
    manifest_bytes = (voice_dir / "manifest.json").read_bytes()
    voice_name = json.loads(manifest_bytes.decode("utf-8"))["name"]
    voice_sha = hashlib.sha256(manifest_bytes).hexdigest()
    stems = sorted(q.stem for q in phrases_dir.glob("*.mid"))
    if not stems:
        raise ValueError(f"no *.mid phrases in {phrases_dir}")
    heldout_files = sorted(q.name for q in heldout_dir.glob("*.wav"))
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "renders").mkdir(exist_ok=True)

    numeric = ("speaker_similarity", "guide_similarity", "f0_rms_cents", "octave_fraction", "wer", "guide_wer", "realtime_factor")
    values: dict[str, list] = {k: [None] * REPEATS for k in numeric}
    reasons: list[str] = []
    shift: int | None = None

    def stage(label, fn):
        try:
            return fn()
        except (ValueError, RuntimeError, OSError, subprocess.SubprocessError) as exc:
            reasons.append(f"{label}: {exc}")
            return None

    def transposed_phrases():
        nonlocal shift
        if not heldout_files:
            raise ValueError("no held-out recordings")
        pooled = []
        for name in heldout_files:
            audio, rate = _read_mono(heldout_dir / name)
            f0 = metrics.extract_f0(audio, rate)
            pooled.extend(f0[f0 > 0].tolist())
        if not pooled:
            raise ValueError("no voiced frame in the held-out recordings")
        pitches = [n[2] for stem in stems for n in _midi_notes(phrases_dir / f"{stem}.mid")[0]]
        shift = transpose_semitones(pitches, float(np.median(pooled)))
        (out_dir / "phrases").mkdir(exist_ok=True)
        paths = {}
        for stem in stems:
            paths[stem] = _write_transposed(phrases_dir / f"{stem}.mid", out_dir / "phrases" / f"{stem}.mid", shift)
        return paths

    midi_paths = stage("transpose", transposed_phrases)

    def render_all():
        sidecars = {}
        for stem in stems:
            for r in range(REPEATS):
                for kind, extra in (("converted", []), ("guide", ["--no-convert"])):
                    name = f"{stem}.{kind}.wav" if r == 0 else f"{stem}.r{r}.{kind}.wav"
                    target = out_dir / "renders" / name
                    run = subprocess.run([str(render_bin), "--voice", str(voice_dir), "--midi", str(midi_paths[stem]), "--out", str(target),
                                          "--seed", str(seed), *extra], capture_output=True, text=True)
                    if run.returncode != 0:
                        raise RuntimeError(f"render of {name} failed (exit {run.returncode}): {run.stderr.strip()}")
                    side = json.loads(Path(str(target) + ".provenance.json").read_text(encoding="utf-8"))
                    if not side["unclipped_peak"] > 0:
                        raise ValueError(f"render {name} is silent (unclipped_peak {side['unclipped_peak']})")
                    sidecars[(stem, r, kind)] = (target, side)
        return sidecars

    renders = stage("render", render_all) if midi_paths is not None else None

    def similarity():
        from resemblyzer import VoiceEncoder, preprocess_wav
        encoder = VoiceEncoder("cpu")

        def embed(path):
            return np.asarray(encoder.embed_utterance(preprocess_wav(str(path))), dtype=np.float64)

        held = [embed(heldout_dir / n) for n in heldout_files]
        if len(held) != len(heldout_files) or not held:
            raise ValueError("a held-out file yielded no embedding")
        reference = np.mean(held, axis=0)
        for r in range(REPEATS):
            values["speaker_similarity"][r] = float(np.mean([metrics.cosine(embed(renders[(s, r, "converted")][0]), reference) for s in stems]))
            values["guide_similarity"][r] = float(np.mean([metrics.cosine(embed(renders[(s, r, "guide")][0]), reference) for s in stems]))

    def f0_accuracy():
        for r in range(REPEATS):
            scored = octave = 0
            squares = 0.0
            for s in stems:
                audio, rate = _read_mono(renders[(s, r, "converted")][0])
                notes, bpm = _midi_notes(midi_paths[s])
                first = min(n[0] for n in notes)
                timed = [((a - first) * 60.0 / bpm, (b - first) * 60.0 / bpm, m) for a, b, m in notes]
                score = metrics.score_f0(metrics.extract_f0(audio, rate), 0.01, timed, edge_s=0.05, octave_cents=600.0)
                if score["scored_frames"] < 20:
                    raise ValueError(f"only {score['scored_frames']} scored F0 frames in phrase {s} (repeat {r})")
                scored += score["scored_frames"]
                octave += score["octave_errors"]
                squares += score["scored_frames"] * score["rms_cents"] ** 2
            values["f0_rms_cents"][r] = float(math.sqrt(squares / scored))
            values["octave_fraction"][r] = octave / (scored + octave)

    def intelligibility():
        import whisper
        model = whisper.load_model("small.en")
        reference = {s: (phrases_dir / f"{s}.txt").read_text(encoding="utf-8") for s in stems}
        for r in range(REPEATS):
            for key, kind in (("wer", "converted"), ("guide_wer", "guide")):
                scores = []
                for s in stems:
                    text = model.transcribe(str(renders[(s, r, kind)][0]), language="en", temperature=0)["text"]
                    scores.append(metrics.wer(reference[s], text))
                values[key][r] = float(np.mean(scores))

    def speed():
        for r in range(REPEATS):
            sides = [renders[(s, r, "converted")][1] for s in stems]
            values["realtime_factor"][r] = sum(x["render_seconds"] for x in sides) / sum(x["audio_seconds"] for x in sides)

    if renders is not None:
        for label, fn in (("similarity", similarity), ("f0", f0_accuracy), ("intelligibility", intelligibility), ("speed", speed)):
            stage(label, fn)

    spread = {}
    for key in numeric:
        v = values[key]
        complete = all(x is not None for x in v)
        spread[key] = {"values": v, "min": min(v) if complete else None, "max": max(v) if complete else None}
    report = {key: (sum(values[key]) / REPEATS if all(x is not None for x in values[key]) else None) for key in numeric}
    report.update({"phrases": stems, "transpose_semitones": shift, "heldout_files": heldout_files,
                   "status": "measured" if not reasons else "invalid: " + "; ".join(reasons)})
    report = {key: report[key] for key in REPORT_KEYS}
    atomic_write_text(out_dir / "spread.json", json.dumps(spread, sort_keys=True, indent=1) + "\n")
    atomic_write_text(out_dir / "report.json", json.dumps(report, sort_keys=True, indent=1) + "\n")
    params = {"voice_name": voice_name, "voice_sha256": voice_sha, "phrases": str(phrases_dir), "heldout_files": len(heldout_files)}
    provenance.write_sidecar(out_dir / "report.json", provenance.collect(params, {"converter": seed}, repo_root, lockfile))
    return report
