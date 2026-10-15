"""Writes the five D-017 evaluation phrases: eval/phrases/pN.mid (format 0, PPQ 480, tempo, one lyric meta event per note,
D-031) and pN.txt (the reference text for WER). Lyrics are original lines written for this project (no third-party lyrics).
Every word is checked against the vendored CMUdict: its hyphen-separated syllable count must equal its vowel count (D-005),
so alignment (D-006) produces no warnings. Usage: python -I tools/gen/phrases.py   (needs mido 1.3.3)"""
import pathlib
import re

import mido

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / "eval" / "phrases"
VOWELS = {"aa", "ae", "ah", "ao", "aw", "ay", "eh", "er", "ey", "ih", "iy", "ow", "oy", "uh", "uw"}
# (syllables with D-004 hyphens, MIDI pitches, beats per note) — melodies are stepwise, median near C4..E4.
PHRASES = [
    ("cop- per ket- tles hum at dawn", [60, 62, 64, 62, 60, 59, 60], [1, 1, 1, 1, 1, 1, 2]),
    ("sev- en win- dows o- pen wide", [64, 64, 65, 67, 65, 64, 62], [1, 1, 1, 1, 1, 1, 2]),
    ("fol- low the riv- er past the mill", [62, 64, 65, 67, 65, 64, 62, 60], [1, 1, 1, 1, 1, 1, 1, 2]),
    ("qui- et lan- terns light the hall", [67, 65, 64, 62, 64, 62, 60], [1, 1, 1, 1, 1, 1, 2]),
    ("ev- er- y morn- ing brings a song", [60, 62, 64, 67, 65, 64, 62, 60], [1, 1, 1, 1, 1, 1, 1, 2]),
]
BPM = 100


def load_dict():
    d = {}
    for line in (ROOT / "third_party" / "cmudict" / "cmudict.dict").read_text(encoding="utf-8").splitlines():
        line = line.split("#")[0].strip()
        if line:
            w, *ph = line.split()
            if "(" not in w and w not in d:
                d[w] = [re.sub(r"\d", "", p).lower() for p in ph]
    return d


def main():
    d = load_dict()
    OUT.mkdir(parents=True, exist_ok=True)
    for i, (lyr, pitches, beats) in enumerate(PHRASES, 1):
        sylls = lyr.split()
        assert len(sylls) == len(pitches) == len(beats), (i, len(sylls), len(pitches))
        words = " ".join(sylls).replace("- ", "").split()
        for w, parts in zip(words, re.sub(r"- ", "-", lyr).split()):
            n = len(parts.split("-"))
            assert w in d, f"{w} not in CMUdict"
            v = sum(p in VOWELS for p in d[w])
            assert n == v, f"{w}: {n} syllables but {v} vowels {d[w]}"
        mf = mido.MidiFile(type=0, ticks_per_beat=480)
        tr = mido.MidiTrack()
        mf.tracks.append(tr)
        tr.append(mido.MetaMessage("set_tempo", tempo=mido.bpm2tempo(BPM), time=0))
        for s, p, b in zip(sylls, pitches, beats):
            tr.append(mido.MetaMessage("lyrics", text=s, time=0))
            tr.append(mido.Message("note_on", note=p, velocity=90, time=0))
            tr.append(mido.Message("note_off", note=p, velocity=0, time=480 * b))
        tr.append(mido.MetaMessage("end_of_track", time=0))
        mf.save(OUT / f"p{i}.mid")
        (OUT / f"p{i}.txt").write_text(" ".join(words) + "\n", encoding="utf-8")
        print(f"p{i}: {' '.join(words)} | {len(sylls)} notes, median MIDI {sorted(pitches)[len(pitches)//2]}")


main()
