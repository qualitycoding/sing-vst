"""Independent Python oracle of the frozen rules D-004..D-009, D-011, D-021, D-022 (research spike, not shipped).
Used by check_expectations.py to confirm every expected value in the frozen C++ tests is satisfiable and consistent
(lessons L-20261009T234102Z, L-20261004T150400Z, L-20261004T162212Z)."""
from __future__ import annotations
import math, re
from dataclasses import dataclass, field

class ParseError(Exception):
    def __init__(self, msg, pos): super().__init__(msg); self.position = pos
class ValidationError(Exception): pass

# ---------------- D-004 lyrics ----------------
TEXT, PHON, EXT = 0, 1, 2
@dataclass
class Tok:
    kind: int = TEXT; text: str = ""; phonemes: list = field(default_factory=list); cont: bool = False

WS = " \t\r\n"
def _clean(s):
    out = []
    for ch in s:
        if ord(ch) >= 128 or ch.isalnum() or ch == "'": out.append(ch.lower() if ord(ch) < 128 else ch)
    return "".join(out)

def parse_lyrics(src: str):
    b = src.encode("utf-8"); s = b.decode("utf-8")
    toks, i, n = [], 0, len(b)
    # operate on bytes for positions; ASCII control chars only matter
    def ch(k): return chr(b[k]) if b[k] < 128 else None
    while i < n:
        c = ch(i)
        if c is not None and c in WS: i += 1; continue
        if c == "]": raise ParseError("unmatched ]", i)
        if c == "[":
            start = i; j = i + 1; buf = []
            while j < n and ch(j) != "]":
                if ch(j) == "[": raise ParseError("nested [", j)
                buf.append(b[j]); j += 1
            if j >= n: raise ParseError("unclosed [", start)
            phones = [p.lower() for p in bytes(buf).decode("utf-8").split()]
            i = j + 1; cont = False
            if i < n and ch(i) == "-": cont = True; i += 1
            if phones: toks.append(Tok(PHON, "", phones, cont))
            continue
        if c == "+": toks.append(Tok(EXT)); i += 1; continue
        j = i
        while j < n and not (ch(j) is not None and (ch(j) in WS or ch(j) in "[]+")): j += 1
        word = b[i:j].decode("utf-8"); i = j
        parts = word.split("-"); trailing = word.endswith("-")
        syl = [p for p in parts]
        out = []
        for k, p in enumerate(syl):
            t = _clean(p)
            if not t: continue
            out.append(Tok(TEXT, t, [], False))
        for k in range(len(out) - 1): out[k].cont = True
        if out and trailing: out[-1].cont = True
        toks.extend(out)
    return toks

# ---------------- D-005 g2p ----------------
VOWELS = {"aa","ae","ah","ao","aw","ay","eh","er","ey","ih","iy","ow","oy","uh","uw"}
def norm_phone(p): return re.sub(r"\d+$", "", p).lower()
def is_vowel(p): return norm_phone(p) in VOWELS
class Dictionary:
    def __init__(self, text):
        self.e, self.ph = {}, set()
        for line in text.splitlines():
            line = line.split("#", 1)[0].strip()
            if not line or line.startswith(";;;"): continue
            w, *ps = line.split()
            if re.search(r"\(\d+\)$", w): continue
            w = w.lower()
            if w in self.e: continue
            ps = [norm_phone(p) for p in ps]; self.e[w] = ps; self.ph.update(ps)
    def lookup(self, w): return self.e.get(w.lower())
    def size(self): return len(self.e)
    def has_phone(self, p): return norm_phone(p) in self.ph
def syllabify(phones, n):
    V = [i for i, p in enumerate(phones) if is_vowel(p)]
    if not V:
        if n == 1: return [list(phones)]
        raise ValidationError("vowel-less")
    if n == 0 or n > len(V): raise ValidationError("bad n")
    cuts = [0]
    for j in range(1, n):
        c = V[j] - V[j-1] - 1; cuts.append(V[j-1] + 1 + c // 2)
    cuts.append(len(phones))
    return [list(phones[cuts[k]:cuts[k+1]]) for k in range(n)]

# ---------------- D-006 align ----------------
@dataclass
class Note:
    start: float; end: float; midi: int
EPS_BEAT = 1e-9
def to_monophonic(notes):
    ns = sorted([x for x in notes if x.end - x.start > EPS_BEAT], key=lambda x: x.start)   # D-006 steps 1-2 (stable)
    groups = []                                   # step 3: starts within EPS_BEAT of a group's first start are simultaneous
    for x in ns:
        if groups and x.start - groups[-1][0].start <= EPS_BEAT: groups[-1].append(x)
        else: groups.append([x])
    out = []
    for g in groups:
        x = max(g, key=lambda y: y.midi)          # highest pitch; ties: first in input order (max keeps the first maximum)
        if out and out[-1].end > x.start: out[-1] = Note(out[-1].start, x.start, out[-1].midi)
        out.append(Note(x.start, x.end, x.midi))
    return [x for x in out if x.end - x.start > EPS_BEAT]
@dataclass
class Assign:
    note: Note; phonemes: list; ext: bool = False
def align(notes, toks, d: Dictionary):
    warn, units, i = [], [], 0
    while i < len(toks):
        t = toks[i]
        if t.kind == TEXT:
            grp = [t]
            while grp[-1].cont and i + len(grp) < len(toks) and toks[i + len(grp)].kind == TEXT: grp.append(toks[i + len(grp)])
            i += len(grp); g = len(grp); word = "".join(x.text for x in grp); ph = d.lookup(word)
            if ph is None:
                warn.append(f"unknown word '{word}'"); units += [("syl", ["ah"])] * g; continue
            k = sum(is_vowel(p) for p in ph)
            m = 1 if k == 0 else min(g, k)
            units += [("syl", s) for s in syllabify(ph, m)]
            if g > m: warn.append(f"word '{word}' has {g} syllables marked but {max(k,1)} vowel(s)"); units += [("ext", None)] * (g - m)
        elif t.kind == PHON:
            keep = [p for p in t.phonemes if d.has_phone(p) or p in ("sp", "ap")]
            bad = [p for p in t.phonemes if p not in keep]
            if bad: warn.append("unknown phonemes " + " ".join(bad))
            keep = [{"sp": "SP", "ap": "AP"}.get(p, p) for p in keep]
            units.append(("syl", keep or ["ah"])); i += 1
        else:
            units.append(("ext", None)); i += 1
    out = []
    surplus_notes = max(0, len(notes) - len(units))
    for j, nt in enumerate(notes):
        u = units[j] if j < len(units) else ("surplus", None)
        if u[0] == "syl": out.append(Assign(nt, list(u[1]), False)); continue
        if not out:
            if u[0] == "ext": warn.append("melisma '+' with no preceding syllable")
            out.append(Assign(nt, ["ah"], True)); continue
        prev = out[-1].phonemes; vs = [p for p in prev if is_vowel(p)]
        out.append(Assign(nt, [vs[-1] if vs else prev[-1]], True))
    if surplus_notes: warn.append(f"{surplus_notes} note(s) have no lyric")
    if len(units) > len(notes): warn.append(f"{len(units) - len(notes)} syllable(s) have no note")
    return out, warn

# ---------------- D-007 synthesis ----------------
def midi_to_hz(m): return 440.0 * 2 ** ((m - 69) / 12)
def layout(assigns, bpm, c=0.06):
    if not assigns: return []
    t0 = assigns[0].note.start; sec = lambda bt: (bt - t0) * 60.0 / bpm
    segs = []   # (kind, start, end, assign)
    for k, a in enumerate(assigns):
        s, e = sec(a.note.start), sec(a.note.end)
        if e - s <= 0 or (k > 0 and a.note.start < assigns[k-1].note.end - EPS_BEAT) or not a.phonemes:
            raise ValidationError("layout needs sorted, non-overlapping notes of positive length with phonemes")
        if segs and s > segs[-1][2] + 1e-12: segs.append(["gap", segs[-1][2], s, None])
        segs.append(["note", s, e, a])
    # per segment: lists of (phone, dur) at head and tail; nucleus fills the rest
    head = [[] for _ in segs]; tail = [[] for _ in segs]; equal = [False] * len(segs)
    for k, (kind, s, e, a) in enumerate(segs):
        if kind != "note": continue
        ph = a.phonemes; fv = next((i for i, p in enumerate(ph) if is_vowel(p)), None)
        dur = e - s
        if fv is None: equal[k] = True; continue
        onset, coda = ph[:fv], ph[fv+1:]
        if coda:
            tot = min(len(coda) * c, 0.4 * dur); tail[k] += [(p, tot / len(coda)) for p in coda]
        if onset:
            if k > 0:
                pd = segs[k-1][2] - segs[k-1][1]; tot = min(len(onset) * c, 0.4 * pd)
                tail[k-1] += [(p, tot / len(onset)) for p in onset]
            else:
                tot = min(len(onset) * c, 0.4 * dur); head[k] += [(p, tot / len(onset)) for p in onset]
    spans = []
    for k, (kind, s, e, a) in enumerate(segs):
        dur = e - s
        hsum = sum(x[1] for x in head[k]); tsum = sum(x[1] for x in tail[k])
        if kind == "note" and hsum + tsum > 0.8 * dur:
            f = 0.8 * dur / (hsum + tsum); head[k] = [(p, x * f) for p, x in head[k]]; tail[k] = [(p, x * f) for p, x in tail[k]]
            hsum *= f; tsum *= f
        t = s
        for p, x in head[k]: spans.append([p, t, t + x]); t += x
        if kind == "note" and equal[k]:          # no vowel: the phones share [s, e - tsum] equally; the tail still follows
            ph = a.phonemes; step = (e - tsum - t) / len(ph)
            for i, p in enumerate(ph): spans.append([p, t + i * step, t + (i + 1) * step])
        else:
            nuc = "SP" if kind == "gap" else a.phonemes[next(i for i, p in enumerate(a.phonemes) if is_vowel(p))]
            spans.append([nuc, t, e - tsum])
        t = e - tsum
        for p, x in tail[k]: spans.append([p, t, t + x]); t += x
        spans[-1][2] = e
    return spans
def f0_curve(assigns, bpm, fr, total, port=0.06, vib=0.0, vhz=5.5):
    n = math.ceil(total * fr - 1e-9); out = [0.0] * n
    if not assigns: return out
    t0 = assigns[0].note.start; sec = lambda bt: (bt - t0) * 60.0 / bpm
    for k, a in enumerate(assigns):
        s, e = sec(a.note.start), sec(a.note.end); f = midi_to_hz(a.note.midi)
        legato = k > 0 and abs(assigns[k-1].note.end - a.note.start) < 1e-9
        fp = midi_to_hz(assigns[k-1].note.midi) if legato else f
        pw = min(port, e - s)
        for i in range(max(0, math.ceil(s * fr - 1e-9)), min(n, math.ceil(e * fr - 1e-9))):
            t = i / fr
            if not (s - 1e-12 <= t < e - 1e-12): continue
            u = (t - s) / pw if (legato and pw > 0) else 1.0
            if u < 1.0: hz = math.exp(math.log(fp) + (math.log(f) - math.log(fp)) * (1 - math.cos(math.pi * u)) / 2)
            else: hz = f
            if vib: hz *= 2 ** (vib * math.sin(2 * math.pi * vhz * (t - s)) / 1200)
            out[i] = hz
    return out
def rvc_coarse(h):
    mmin = 1127 * math.log(1 + 50 / 700); mmax = 1127 * math.log(1 + 1100 / 700)
    m = 1127 * math.log(1 + h / 700)
    if m > 0: m = (m - mmin) * 254 / (mmax - mmin) + 1
    m = 1 if m <= 1 else min(m, 255)
    return int(math.floor(m + 0.5)) if abs((m % 1) - 0.5) > 1e-12 else int(round(m))   # numpy rint = half-to-even
def frame_durations(spans, fr):
    n = len(spans)
    if n == 0: raise ValidationError("no spans")
    total = int(math.floor(spans[-1][2] * fr + 0.5))
    if total < n: raise ValidationError("too short")
    b, out = 0, []
    for k, sp in enumerate(spans):
        nb = total if k == n - 1 else min(max(int(math.floor(sp[2] * fr + 0.5)), b + 1), total - (n - 1 - k))
        out.append(nb - b); b = nb
    return out
def soft_clip(x, c=0.98):
    if not math.isfinite(x): return 0.0
    knee = 0.8 * c
    if abs(x) <= knee: return x
    return math.copysign(knee + (c - knee) * math.tanh((abs(x) - knee) / (c - knee)), x)

# ---------------- D-009 playback ----------------
def take_sample_at(start, bpm, sr, nsamp, ppq, hbpm, tol=0.1):
    if abs(hbpm - bpm) > tol: return None
    k = math.floor((ppq - start) * 60.0 / bpm * sr + 0.5)
    return k if 0 <= k < nsamp else None
def phrase_hash(notes, toks, p):
    s = "".join("n:%.9f:%.9f:%d;" % (x.start, x.end, x.midi) for x in notes)
    s += "".join("t:%d:%s:%s:%d;" % (t.kind, t.text, " ".join(t.phonemes), 1 if t.cont else 0) for t in toks)
    s += "p:%s:%.9f:%d:%d:%.9f:%.9f:%d;" % (p["voiceId"], p["bpm"], p["outputSampleRate"], 1 if p["conversionEnabled"] else 0, p["portamentoSec"], p["vibratoCents"], p["seed"])
    h = 14695981039346656037
    for byte in s.encode("utf-8"): h ^= byte; h = (h * 1099511628211) % 2**64
    return h, s

# ---------------- D-012 converter prior noise ----------------
M64 = (1 << 64) - 1
def splitmix64(state):
    state = (state + 0x9E3779B97F4A7C15) & M64
    z = state
    z = ((z ^ (z >> 30)) * 0xBF58476D1CE4E5B9) & M64
    z = ((z ^ (z >> 27)) * 0x94D049BB133111EB) & M64
    return state, z ^ (z >> 31)
def standard_normal(seed, n):
    """D-012: SplitMix64 stream from `seed`; per pair u1 = ((x1 >> 11) + 1) * 2^-53 in (0, 1], u2 = (x2 >> 11) * 2^-53 in [0, 1);
    z0 = sqrt(-2 ln u1) cos(2 pi u2), z1 = sqrt(-2 ln u1) sin(2 pi u2); values in order z0, z1, ...; computed in double."""
    s, out = seed & M64, []
    while len(out) < n:
        s, x1 = splitmix64(s); s, x2 = splitmix64(s)
        u1 = ((x1 >> 11) + 1) * 2.0 ** -53; u2 = (x2 >> 11) * 2.0 ** -53
        r = math.sqrt(-2.0 * math.log(u1))
        out.append(r * math.cos(2 * math.pi * u2))
        if len(out) < n: out.append(r * math.sin(2 * math.pi * u2))
    return out
