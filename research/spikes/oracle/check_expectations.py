"""Every expected value in the frozen C++ tests, re-derived from the oracle (PK-21). Sections mirror tests/cpp/test_*.cpp.
Usage: python -I check_expectations.py  -> check_expectations-output.txt (exit 0 = all expectations satisfiable)."""
import math, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent)); import oracle as o
ROOT = pathlib.Path(__file__).resolve().parents[3]
results = []
def check(tid, what, got, exp):
    ok = got == exp if not isinstance(exp, float) else abs(got - exp) <= 1e-9 * max(1.0, abs(exp))
    results.append((tid, what, ok, got, exp))

# ---- test_lyrics.cpp ----
T = lambda t, c=False: (o.TEXT, t, (), c); P = lambda p, c=False: (o.PHON, "", tuple(p), c); E = (o.EXT, "", (), False)
toks = lambda s: [(x.kind, x.text, tuple(x.phonemes), x.cont) for x in o.parse_lyrics(s)]
def pos(s):
    try: o.parse_lyrics(s)
    except o.ParseError as e: return e.position
    return -1
for tid, s, exp in [
    ("T-001", "Hel-lo world", [T("hel", True), T("lo"), T("world")]), ("T-001", "to-ma-to", [T("to", True), T("ma", True), T("to")]),
    ("T-002", "Hel- lo, don't!\n(sing)", [T("hel", True), T("lo"), T("don't"), T("sing")]),
    ("T-002", "Café ÉTÉ R2-D2", [T("café"), T("ÉtÉ"), T("r2", True), T("d2")]),
    ("T-003", "la + , +", [T("la"), E, E]), ("T-003", "la+lo", [T("la"), E, T("lo")]), ("T-003", "la- +", [T("la", True), E]),
    ("T-004", "[HH ah]-[l  OW] x", [P(["hh", "ah"], True), P(["l", "ow"]), T("x")]), ("T-004", "ab[sp]cd", [T("ab"), P(["sp"]), T("cd")]),
    ("T-006", "", []), ("T-006", " \t\r\n ", []), ("T-006", "[] [ \t]", []), ("T-006", "--la", [T("la")]), ("T-006", "la-", [T("la", True)]),
    ("T-006", "- -- ,", [])]:
    check(tid, repr(s), toks(s), exp)
for s, exp in [("ab [hh ah", 3), ("ab ] c", 3), ("[a [b]]", 3), ("x]", 1), ("é [x", 3), ("fine [ok] text", -1)]:
    check("T-005", repr(s), pos(s), exp)

# ---- test_g2p.cpp ----
mini = o.Dictionary((ROOT / "tests/fixtures/cmudict-mini.dict").read_text(encoding="utf-8"))
check("T-007", "size", mini.size(), 48)
for w, exp in [("hello", ["hh", "ah", "l", "ow"]), ("HeLLo", ["hh", "ah", "l", "ow"]), ("world", ["w", "er", "l", "d"]), ("zzz", ["z", "iy"]),
               ("don't", ["d", "ow", "n", "t"]), ("qualitycoding", None), ("hello(2)", None)]:
    check("T-007", "lookup " + w, mini.lookup(w), exp)
for p, exp in [("ow", True), ("OW1", True), ("zh", False), ("zz", False)]: check("T-007", "hasPhone " + p, mini.has_phone(p), exp)
for v in ["aa", "ae", "ah", "ao", "aw", "ay", "eh", "er", "ey", "ih", "iy", "ow", "oy", "uh", "uw", "AH0", "er1", "Ow2"]: check("T-008", v, o.is_vowel(v), True)
for v in ["hh", "l", "ng", "y", "w", "r", "SP", "AP", "", "a", "0"]: check("T-008", repr(v), o.is_vowel(v), False)
for tid, w, n, exp in [("T-009", "hello", 2, [["hh", "ah"], ["l", "ow"]]), ("T-009", "singing", 2, [["s", "ih"], ["ng", "ih", "ng"]]),
        ("T-009", "extra", 2, [["eh", "k", "s"], ["t", "r", "ah"]]), ("T-009", "birthday", 2, [["b", "er", "th"], ["d", "ey"]]),
        ("T-009", "tomato", 3, [["t", "ah"], ["m", "ey"], ["t", "ow"]]), ("T-009", "strength", 1, [["s", "t", "r", "eh", "ng", "k", "th"]]),
        ("T-010", "tomato", 2, [["t", "ah"], ["m", "ey", "t", "ow"]]), ("T-010", "tomato", 1, [["t", "ah", "m", "ey", "t", "ow"]]),
        ("T-011", "hmm", 1, [["hh", "m"]])]:
    check(tid, f"syllabify {w} {n}", o.syllabify(mini.lookup(w), n), exp)
for w, n in [("love", 2), ("love", 0), ("hmm", 2)]:
    try: o.syllabify(mini.lookup(w), n); check("T-011", f"{w} {n} raises", False, True)
    except o.ValidationError: check("T-011", f"{w} {n} raises", True, True)
full = o.Dictionary((ROOT / "third_party/cmudict/cmudict.dict").read_text(encoding="utf-8"))
check("T-012", "size", full.size(), 126052)
check("T-012", "singing", full.lookup("singing"), ["s", "ih", "ng", "ih", "ng"]); check("T-012", "rhythm", full.lookup("rhythm"), ["r", "ih", "dh", "ah", "m"])
check("T-012", "all 39 phones", all(full.has_phone(p) for p in "aa ae ah ao aw ay b ch d dh eh er ey f g hh ih iy jh k l m n ng ow oy p r s sh t th uh uw v w y z zh".split()), True)
check("T-012", "ax absent", full.has_phone("ax"), False)

# ---- test_align.cpp ----
N = o.Note; nt = lambda xs: [(x.start, x.end, x.midi) for x in xs]
beats = lambda n: [N(float(i), float(i + 1), 60 + i) for i in range(n)]
check("T-013", "mono 1", nt(o.to_monophonic([N(2, 3, 64), N(0, 1.5, 60), N(1, 2, 62), N(1, 2, 67), N(4, 4, 70), N(1, 1, 90)])), [(0, 1, 60), (1, 2, 67), (2, 3, 64)])
check("T-013", "mono 2", nt(o.to_monophonic([N(5, 6, 50), N(5 + 5e-10, 6, 55)])), [(5 + 5e-10, 6, 55)])
check("T-013", "mono 3", nt(o.to_monophonic([N(0, 2, 60), N(0, 2, 60)])), [(0, 2, 60)]); check("T-013", "mono empty", o.to_monophonic([]), [])
def al(n, s, d=mini):
    out, w = o.align(beats(n) if isinstance(n, int) else n, o.parse_lyrics(s), d); return [(a.phonemes, a.ext) for a in out], w
check("T-014", "hel-lo world", al(3, "hel-lo world"), ([(["hh", "ah"], False), (["l", "ow"], False), (["w", "er", "l", "d"], False)], []))
check("T-015", "love +", al(2, "love +"), ([(["l", "ah", "v"], False), (["ah"], True)], []))
check("T-015", "la x3", al(3, "la"), ([(["l", "aa"], False), (["aa"], True), (["aa"], True)], ["2 note(s) have no lyric"]))
check("T-015", "hello x2", al(2, "hello"), ([(["hh", "ah", "l", "ow"], False), (["ow"], True)], ["1 note(s) have no lyric"]))
check("T-015", "+", al(1, "+"), ([(["ah"], True)], ["melisma '+' with no preceding syllable"]))
check("T-016", "oov", al(1, "qualitycoding"), ([(["ah"], False)], ["unknown word 'qualitycoding'"]))
check("T-016", "la la la", al(1, "la la la"), ([(["l", "aa"], False)], ["2 syllable(s) have no note"]))
check("T-016", "lo-ve", al(2, "lo-ve"), ([(["l", "ah", "v"], False), (["ah"], True)], ["word 'love' has 2 syllables marked but 1 vowel(s)"]))
check("T-016", "qual-ity", al(2, "qual-ity"), ([(["ah"], False), (["ah"], False)], ["unknown word 'quality'"]))
check("T-017", "no notes", al([], "la"), ([], ["1 syllable(s) have no note"])); check("T-017", "nothing", al([], ""), ([], []))
check("T-017", "no lyrics", al(2, ""), ([(["ah"], True), (["ah"], True)], ["2 note(s) have no lyric"]))
check("T-018", "sp/ap", al(1, "[sp hh ah ap]"), ([(["SP", "hh", "ah", "AP"], False)], []))
check("T-018", "unknown phones", al(2, "[zz qq] [hh zz ow]"), ([(["ah"], False), (["hh", "ow"], False)], ["unknown phonemes zz qq", "unknown phonemes zz"]))

# ---- test_synthesis.cpp ----
A = o.Assign
def lay(assigns, bpm=120.0): return o.layout(assigns, bpm)
def spans_eq(tid, what, got, exp):
    ok = len(got) == len(exp) and all(g[0] == e[0] and abs(g[1] - e[1]) <= 1e-9 and abs(g[2] - e[2]) <= 1e-9 for g, e in zip(got, exp))
    results.append((tid, what, ok, got, exp))
for m, hz in [(69, 440.0), (57, 220.0), (81, 880.0), (60, 261.6255653005986)]: check("T-019", f"midi {m}", o.midi_to_hz(m), hz)
check("T-019", "0 cents 0..127", max(abs(1200 * math.log2(o.midi_to_hz(m) / 440) - 100 * (m - 69)) for m in range(128)) <= 1e-9, True)
spans_eq("T-020", "hh ah / l ow", lay([A(N(0, 1, 60), ["hh", "ah"]), A(N(1, 2, 62), ["l", "ow"])]), [("hh", 0, .06), ("ah", .06, .44), ("l", .44, .5), ("ow", .5, 1.0)])
spans_eq("T-021", "clamp + SP", lay([A(N(0, .2, 60), ["l", "aa"]), A(N(.2, 1, 62), ["s", "t", "r", "ah", "ng", "k", "th"]), A(N(2, 3, 64), ["aa"])]),
         [("l", 0, .04), ("aa", .04, .06), ("s", .06, .06 + .04 / 3), ("t", .06 + .04 / 3, .06 + .08 / 3), ("r", .06 + .08 / 3, .1), ("ah", .1, .34),
          ("ng", .34, .34 + .16 / 3), ("k", .34 + .16 / 3, .34 + .32 / 3), ("th", .34 + .32 / 3, .5), ("SP", .5, 1.0), ("aa", 1.0, 1.5)])
spans_eq("T-022", "vowel-less keeps onset", lay([A(N(0, 1, 60), ["hh", "m"]), A(N(1, 2, 62), ["hh", "ah"])]), [("hh", 0, .22), ("m", .22, .44), ("hh", .44, .5), ("ah", .5, 1.0)])
spans_eq("T-022", "scale 2/3", lay([A(N(0, .2, 60), ["s", "t", "r", "eh", "ng", "k", "th"]), A(N(.2, 1.0, 62), ["s", "t", "ah"])]),
         [("s", 0, .08 / 9), ("t", .08 / 9, .16 / 9), ("r", .16 / 9, .24 / 9), ("eh", .24 / 9, .24 / 9 + .02), ("ng", .24 / 9 + .02, .32 / 9 + .02),
          ("k", .32 / 9 + .02, .40 / 9 + .02), ("th", .40 / 9 + .02, .48 / 9 + .02), ("s", .48 / 9 + .02, .48 / 9 + .02 + .04 / 3), ("t", .48 / 9 + .02 + .04 / 3, .1), ("ah", .1, .5)])
check("T-022", "empty", lay([]), [])
for what, a in [("overlap", [A(N(0, 2, 60), ["aa"]), A(N(1, 3, 62), ["aa"])]), ("zero", [A(N(1, 1, 60), ["aa"])]), ("no phones", [A(N(0, 1, 60), [])])]:
    try: lay(a); check("T-022", what + " raises", False, True)
    except o.ValidationError: check("T-022", what + " raises", True, True)
f = o.f0_curve([A(N(0, 1, 69), ["aa"]), A(N(1, 2, 81), ["aa"]), A(N(3, 4, 69), ["aa"])], 60.0, 100.0, 4.0, 0.1, 0.0)
check("T-023", "len", len(f), 400)
for i, hz in [(50, 440.0), (100, 440.0), (105, 622.2539674441622), (110, 880.0), (150, 880.0), (250, 0.0), (300, 440.0)]:
    results.append(("T-023", f"f[{i}]", abs(f[i] - hz) <= 1e-6 * max(1, hz), f[i], hz))
one = [A(N(0, 1, 69), ["aa"])]
for tot, n in [(0.5, 50), (0.501, 51), (0.5 + 1e-12, 50)]: check("T-024", f"frames {tot}", len(o.f0_curve(one, 120.0, 100.0, tot)), n)
v = o.f0_curve([A(N(0, 4, 69), ["aa"])], 60.0, 1000.0, 4.0, 0.0, 100.0, 5.0); cents = [1200 * math.log2(x / 440) for x in v]
results.append(("T-024", "vibrato +-100", abs(max(cents) - 100) <= .01 and abs(min(cents) + 100) <= .01 and all(x > 0 for x in v), (max(cents), min(cents)), (100, -100)))
results.append(("T-024", "v[50]", abs(v[50] - 466.1637615) <= 1e-6 * 466, v[50], 466.1637615))
for hz, b in [(0, 1), (-5, 1), (50, 1), (100, 20), (220, 60), (261.6255653005986, 73), (330, 93), (440, 122), (523.25, 143), (660, 174), (880, 217), (1046.5, 246), (1100, 255), (2000, 255)]:
    check("T-025", f"{hz} Hz", o.rvc_coarse(hz), b)
bins = [o.rvc_coarse(50 + 0.5 * k) for k in range(2101)]; check("T-025", "monotonic", all(b2 >= b1 for b1, b2 in zip(bins, bins[1:])), True)
check("T-026", "[1,1,84]", o.frame_durations([["SP", 0, .0101], ["hh", .0101, .0102], ["ah", .0102, 1.0]], 44100 / 512), [1, 1, 84])
check("T-026", "no overshoot", o.frame_durations([["a", 0, .5]] + [["x", .5 + i * 1e-4, .5 + (i + 1) * 1e-4] for i in range(5)], 100.0), [45, 1, 1, 1, 1, 1])
for what, s in [("too short", [["a", 0, .01], ["b", .01, .015], ["c", .015, .02]]), ("empty", [])]:
    try: o.frame_durations(s, 100.0); check("T-026", what + " raises", False, True)
    except o.ValidationError: check("T-026", what + " raises", True, True)
for x, y, tol in [(0.5, 0.5, 0), (-0.78, -0.78, 0), (1.0, 0.9410412542, 1e-6), (-1.0, -0.9410412542, 1e-6), (2.0, 0.9799983986, 1e-6)]:
    results.append(("T-027", f"softclip {x}", abs(o.soft_clip(x) - y) <= max(tol, 1e-12), o.soft_clip(x), y))
results.append(("T-027", "softclip(100) in (0.979, 0.98]", 0.979 < o.soft_clip(100.0) <= 0.98, o.soft_clip(100.0), 0.98))
results.append(("T-027", "ceiling 0.5", abs(o.soft_clip(1.0, 0.5) - 0.4999987712) <= 1e-6, o.soft_clip(1.0, 0.5), 0.4999987712))
check("T-027", "NaN", o.soft_clip(float("nan")), 0.0); check("T-027", "inf", o.soft_clip(float("inf")), 0.0)

# ---- test_voice.cpp (T-028..T-030): the C++ mutations, re-created here; each must be valid JSON breaking exactly its rule ----
import json
H64 = "a" * 64
BASE = '{"format": "singvoice", "format_version": 1, "name": "Me", "consent": "my own voice",\n "guide_licence": "TIGER v102, personal non-commercial",\n "guide": {"type": "diffsinger", "sample_rate": 44100, "hop_size": 512, "language": "en", "steps": 20, "depth": 0.4,\n           "files": {"acoustic": "guide/acoustic.onnx", "vocoder": "guide/vocoder.onnx", "phonemes": "guide/phonemes.txt"}},\n "converter": {"type": "rvc-v2", "sample_rate": 48000, "speaker_id": 0, "files": {"synth": "conv/rvc.onnx", "content": "conv/content.onnx"}},\n "sha256": {"guide/acoustic.onnx": "HASH", "guide/vocoder.onnx": "HASH", "guide/phonemes.txt": "HASH", "conv/rvc.onnx": "HASH", "conv/content.onnx": "HASH"}}'
def ra(s, a, b):
    assert a in s, f"pattern not in manifest: {a!r}"; return s.replace(a, b)
base = lambda: ra(BASE, "HASH", H64)
cpp = (ROOT / "tests/cpp/test_voice.cpp").read_text()
check("T-029", "C++ BASE literal == checker BASE", BASE in cpp.replace('R"(', "").replace(')"', ""), True)
def accepts(s):
    try: o.parse_manifest(s); return True
    except o.ValidationError: return False
check("T-029", "base accepted", accepts(base()), True)
m = o.parse_manifest(ra(ra(base(), '"language": "en", ', ""), '"speaker_id": 0, ', "")); check("T-028", "defaults", (m["guide"].get("language", "en"), m["converter"].get("speaker_id", 0)), ("en", 0))
noconv = ra(ra(ra(base(), '"converter": {"type": "rvc-v2", "sample_rate": 48000, "speaker_id": 0, "files": {"synth": "conv/rvc.onnx", "content": "conv/content.onnx"}},', ""),
         ', "conv/rvc.onnx": "' + H64 + '"', ""), ', "conv/content.onnx": "' + H64 + '"', "")
check("T-028", "no converter accepted", accepts(noconv) and o.parse_manifest(noconv).get("converter") is None, True)
check("T-028", "unknown top-level key accepted", accepts(ra(base(), '"format": "singvoice",', '"format": "singvoice", "comment": "x",')), True)
bad = {
 "not JSON": "{not json", "array": "[]", "empty": "",
 "format": ra(base(), '"singvoice"', '"voice"'), "format_version": ra(base(), '"format_version": 1', '"format_version": 2'),
 "name empty": ra(base(), '"name": "Me"', '"name": ""'), "consent missing": ra(base(), '"consent": "my own voice",', ""),
 "guide_licence empty": ra(base(), '"TIGER v102, personal non-commercial"', '""'), "guide type": ra(base(), '"diffsinger"', '"nnsvs"'),
 "guide sample_rate": ra(base(), '"sample_rate": 44100', '"sample_rate": 48000'), "hop_size": ra(base(), '"hop_size": 512', '"hop_size": 256'),
 "steps 0": ra(base(), '"steps": 20', '"steps": 0'), "steps 1001": ra(base(), '"steps": 20', '"steps": 1001'), "steps fractional": ra(base(), '"steps": 20', '"steps": 2.5'),
 "depth 0": ra(base(), '"depth": 0.4', '"depth": 0'), "depth 1.5": ra(base(), '"depth": 0.4', '"depth": 1.5'),
 "language empty": ra(base(), '"language": "en"', '"language": ""'),
 "acoustic role missing": ra(ra(base(), '"acoustic": "guide/acoustic.onnx", ', ""), '"guide/acoustic.onnx": "' + H64 + '", ', ""),
 "unknown guide role": ra(base(), '"phonemes": "guide/phonemes.txt"}', '"phonemes": "guide/phonemes.txt", "pitch": "guide/phonemes.txt"}'),
 "converter type": ra(base(), '"rvc-v2"', '"so-vits"'), "converter sample_rate": ra(base(), '"sample_rate": 48000', '"sample_rate": 22050'),
 "speaker_id negative": ra(base(), '"speaker_id": 0', '"speaker_id": -1'),
 "unknown converter role": ra(base(), '"content": "conv/content.onnx"}', '"content": "conv/content.onnx", "index": "conv/rvc.onnx"}'),
 "sha256 missing a file": ra(base(), '"conv/content.onnx": "' + H64 + '"', '"conv/other.onnx": "' + H64 + '"'),
 "sha256 extra key": ra(base(), '"conv/content.onnx": "' + H64 + '"', '"conv/content.onnx": "' + H64 + '", "extra.bin": "' + H64 + '"'),
 "sha256 upper case": ra(base(), '"conv/rvc.onnx": "' + H64 + '"', '"conv/rvc.onnx": "' + "A" * 64 + '"'),
 "sha256 63 digits": ra(base(), '"conv/rvc.onnx": "' + H64 + '"', '"conv/rvc.onnx": "' + "a" * 63 + '"')}
for what, s in bad.items():
    check("T-029", what + " rejected", accepts(s), False)
    if what not in ("not JSON", "empty"):
        try: json.loads(s); valid = True
        except Exception: valid = False
        check("T-029", what + " is valid JSON (only the rule is broken)", valid, True)
check("T-030", "safe path accepted", accepts(ra(base(), "guide/acoustic.onnx", "guide/a-b_c.1.onnx")), True)
for pth in ["../acoustic.onnx", "guide/../../acoustic.onnx", "/etc/acoustic.onnx", "C:/acoustic.onnx", "guide\\\\acoustic.onnx", "guide//acoustic.onnx",
            "./acoustic.onnx", "guide/./acoustic.onnx", "guide/", "guide/a b.onnx", "guide/café.onnx", ".."]:
    s = ra(base(), "guide/acoustic.onnx", pth)
    check("T-030", f"{pth!r} rejected", accepts(s), False)
    try: json.loads(s); check("T-030", f"{pth!r} valid JSON", True, True)
    except Exception: check("T-030", f"{pth!r} valid JSON", False, True)
for d in ("voice-legacy", "voice-convert", "voice-ca"):
    check("T-028", d + " fixture accepted", accepts((ROOT / f"tests/fixtures/{d}/manifest.json").read_text()), True)

if __name__ == "__main__":
    bad = [r for r in results if not r[2]]
    print(f"expectations checked: {len(results)}; mismatches: {len(bad)}")
    for tid, what, ok, got, exp in bad: print(f"MISMATCH {tid} {what}: oracle {got!r} vs test {exp!r}")
    sys.exit(1 if bad else 0)
