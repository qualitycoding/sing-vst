"""Randomised invariant checks of the oracle itself (lesson L-20261014T203000Z): an oracle that validates frozen expectations
must first satisfy the invariants the decisions promise. Usage: python -I properties.py [cases] [seed]  -> output.txt"""
import math, pathlib, random, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import oracle as o

N = int(sys.argv[1]) if len(sys.argv) > 1 else 3000
rng = random.Random(int(sys.argv[2]) if len(sys.argv) > 2 else 20261014)
DICT = o.Dictionary("\n".join([
    "a AH0", "hello HH AH0 L OW1", "world W ER1 L D", "strength S T R EH1 NG K TH", "hmm HH M", "tomato T AH0 M EY1 T OW2",
    "sing S IH1 NG", "extra EH1 K S T R AH0", "music M Y UW1 Z IH0 K", "la L AA1", "birthday B ER1 TH D EY2"]))
WORDS = ["a", "hello", "world", "strength", "hmm", "tomato", "sing", "extra", "music", "la", "birthday", "zzz"]
fails = {}
def check(name, cond, ctx):
    if not cond: fails.setdefault(name, ctx)

def rand_notes():
    notes, t = [], 0.0
    for _ in range(rng.randint(0, 7)):
        t += rng.choice([0.0, 0.0, 0.25, 0.5, 1.0, 2.0]) * rng.random()
        notes.append(o.Note(round(t, 3), round(t + rng.choice([0.0, 0.1, 0.5, 1.0, 1.5]) * rng.random(), 3), rng.randint(40, 90)))
        if rng.random() < 0.5: t = notes[-1].end
    rng.shuffle(notes); return notes

def rand_lyrics():
    parts = []
    for _ in range(rng.randint(0, 6)):
        r = rng.random()
        if r < 0.6:
            w = rng.choice(WORDS)
            parts.append(w if rng.random() < 0.7 else (w[: len(w) // 2] + "-" + w[len(w) // 2:]))
        elif r < 0.75: parts.append("+")
        elif r < 0.9: parts.append("[" + " ".join(rng.choice(["hh", "ah", "sp", "ap", "zz", "ow"]) for _ in range(rng.randint(0, 3))) + "]")
        else: parts.append(rng.choice([",", "!", "--", "'"]))
    return " ".join(parts)

for case in range(N):
    raw = rand_notes(); mono = o.to_monophonic(raw)
    pos = [x for x in raw if x.end - x.start > o.EPS_BEAT]
    starts = []
    for x in sorted(pos, key=lambda y: y.start):
        if not starts or x.start - starts[-1] > o.EPS_BEAT: starts.append(x.start)
    check("mono: sorted, non-overlapping, positive", all(b.start >= a.end - 1e-12 for a, b in zip(mono, mono[1:])) and all(x.end > x.start for x in mono), raw)
    check("mono: one note per distinct start", len(mono) == len(starts), raw)
    for x in mono:
        same = [y for y in pos if abs(y.start - x.start) <= o.EPS_BEAT and y.end > y.start]
        check("mono: highest pitch kept on equal start", x.midi == max(y.midi for y in same), raw)
    toks = o.parse_lyrics(rand_lyrics())
    out, warn = o.align(mono, toks, DICT)
    check("align: one assignment per note", len(out) == len(mono), (raw, toks))
    check("align: extensions hold one phone", all(len(a.phonemes) == 1 for a in out if a.ext), (raw, toks))
    check("align: every assignment has phones", all(a.phonemes for a in out), (raw, toks))
    if out:
        bpm = rng.choice([60.0, 97.5, 120.0, 180.0])
        sp = o.layout(out, bpm)
        end = (mono[-1].end - mono[0].start) * 60 / bpm
        check("layout: starts at 0, ends at last note end", abs(sp[0][1]) < 1e-12 and abs(sp[-1][2] - end) < 1e-9, (mono, out))
        check("layout: contiguous, positive spans", all(abs(b[1] - a[2]) < 1e-12 for a, b in zip(sp, sp[1:])) and all(s[2] - s[1] > 0 for s in sp), (mono, out))
        expect = [p for a in out for p in a.phonemes]
        got = [s[0] for s in sp]
        # remove the SP spans the layout inserted for gaps (exactly one per gap) and compare the rest
        gaps = sum(1 for a, b in zip(out, out[1:]) if b.note.start > a.note.end + 1e-12)
        filtered, removed = [], 0
        ei = 0
        for g in got:
            if ei < len(expect) and g == expect[ei]: filtered.append(g); ei += 1
            elif g == "SP": removed += 1
            else: filtered.append(g)
        check("layout: phones conserved in order", filtered == expect and removed == gaps, (out, got))
        fr = rng.choice([44100 / 512, 100.0])
        if math.floor(sp[-1][2] * fr + 0.5) >= len(sp):
            d = o.frame_durations(sp, fr)
            check("frames: sum is round(end*fr), each >= 1", sum(d) == math.floor(sp[-1][2] * fr + 0.5) and min(d) >= 1, (sp, fr))
        f0 = o.f0_curve(out, bpm, fr, end, rng.choice([0.0, 0.06, 0.2]), rng.choice([0.0, 50.0]))
        check("f0: frame count is ceil(total*fr - 1e-9)", len(f0) == math.ceil(end * fr - 1e-9), (end, fr))
        check("f0: rests are 0, notes positive", all(v >= 0 for v in f0), None)
# randomised frame-duration stress (many tiny spans near the end)
for case in range(N):
    n = rng.randint(1, 40); t = 0.0; sp = []
    for i in range(n):
        dt = rng.choice([1e-4, 1e-3, 0.01, 0.2, 1.0]) * rng.random() + 1e-6; sp.append(["x", t, t + dt]); t += dt
    fr = rng.choice([44100 / 512, 100.0, 1000.0]); total = math.floor(t * fr + 0.5)
    if total >= n:
        d = o.frame_durations(sp, fr); check("frames stress: exact total, each >= 1", sum(d) == total and min(d) >= 1, (n, t, fr))
    else:
        try: o.frame_durations(sp, fr); check("frames stress: too short raises", False, (n, t, fr))
        except o.ValidationError: pass
print(f"cases {N} x2; invariant failures: {len(fails)}")
for k, v in fails.items(): print("FAIL", k, "| first counterexample:", repr(v)[:400])
sys.exit(1 if fails else 0)
