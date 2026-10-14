"""Generates every committed test fixture deterministically (run from the repository root with the toolkit lock installed):
    python -I tests/fixtures/make_fixtures.py
ONNX fixtures implement the D-012 I/O contracts and *echo their inputs* into the output audio so the C++ tests can see what
the engines fed them (PK-28: every graph passes onnx.checker at opset 17). MIDI fixtures are written byte by byte (D-031).
The fixtures are frozen with the tests (tests/FROZEN_MANIFEST.sha256)."""
import hashlib, json, pathlib, struct
import numpy as np
import onnx
from onnx import TensorProto as TP, helper as H, numpy_helper as NH

ROOT = pathlib.Path(__file__).resolve().parent
OX = ROOT / "onnx"; OX.mkdir(exist_ok=True)
F, I = TP.FLOAT, TP.INT64
ARPA = "aa ae ah ao aw ay b ch d dh eh er ey f g hh ih iy jh k l m n ng ow oy p r s sh t th uh uw v w y z zh".split()
PHONES = ["SP", "AP"] + ARPA + ["en/qq"]          # ids: SP 0, AP 1, aa 2, ah 4, hh 17, l 22, ow 26, en/qq 41
LANGS = {"zh": 1, "ja": 2, "en": 3}

def save(name, nodes, inputs, outputs, inits=()):
    g = H.make_graph(nodes, name, inputs, outputs, initializer=list(inits))
    m = H.make_model(g, opset_imports=[H.make_opsetid("", 17)], producer_name="sing-vst-fixtures")
    m.ir_version = 9
    onnx.checker.check_model(m, full_check=True)
    onnx.save(m, OX / f"{name}.onnx")

def c(name, arr, dt=np.float32): return NH.from_array(np.array(arr, dtype=dt), name)
def vi(name, t, shape): return H.make_tensor_value_info(name, t, shape)

def acoustic(name, legacy, extra_input=None):
    """mel[1,T,128]: ch0 f0, ch1 sum(tokens), ch2 sum(durations), ch3 mean(gender), ch4 mean(velocity), ch5 sum(spk_embed)/T,
    ch6 depth, ch7 speedup (legacy) or steps, ch8 sum(languages), ch9 T, ch10..127 zero."""
    n = []; ins = [vi("tokens", I, [1, "n"]), vi("durations", I, [1, "n"]), vi("f0", F, [1, "T"])]
    inits = [c("ax1", [1], np.int64), c("zero", 0.0), c("one", 1.0), c("pad118", np.zeros((1, 1, 118), np.float32))]
    def scal(src, out, cast=True, reduce="ReduceSum"):   # scalar float from a tensor (sum or mean over all)
        x = src
        if cast: n.append(H.make_node("Cast", [src], [src + "_f"], to=F)); x = src + "_f"
        n.append(H.make_node(reduce, [x], [out], keepdims=0))
    n.append(H.make_node("Unsqueeze", ["f0", "ax2"], ["f0u"])); inits.append(c("ax2", [2], np.int64))    # [1,T,1]
    n.append(H.make_node("Mul", ["f0u", "zero"], ["z1"]))                                                   # zeros [1,T,1]
    def chan(scalar, out): n.append(H.make_node("Add", ["z1", scalar], [out]))                               # broadcast scalar
    scal("tokens", "s_tok"); scal("durations", "s_dur")
    if legacy:
        ins += [vi("gender", F, [1, "T"]), vi("velocity", F, [1, "T"]), vi("spk_embed", F, [1, "T", 4]), vi("depth", I, []), vi("speedup", I, [])]
        scal("gender", "s_gen", cast=False, reduce="ReduceMean"); scal("velocity", "s_vel", cast=False, reduce="ReduceMean")
        scal("spk_embed", "s_spk_sum", cast=False)
        n.append(H.make_node("Shape", ["f0"], ["f0shape"])); n.append(H.make_node("Gather", ["f0shape", "ax1"], ["Tvec"], axis=0))
        n.append(H.make_node("Cast", ["Tvec"], ["Tf"], to=F)); n.append(H.make_node("ReduceSum", ["Tf"], ["T_s"], keepdims=0))
        n.append(H.make_node("Div", ["s_spk_sum", "T_s"], ["s_spk"]))
        n.append(H.make_node("Cast", ["depth"], ["s_depth"], to=F)); n.append(H.make_node("Cast", ["speedup"], ["s_7"], to=F))
        n.append(H.make_node("Mul", ["zero", "one"], ["s_lang"]))
    else:
        ins += [vi("languages", I, [1, "n"]), vi("steps", I, [1]), vi("depth", F, [1])]
        n.append(H.make_node("Mul", ["zero", "one"], ["s_gen"])); n.append(H.make_node("Mul", ["zero", "one"], ["s_vel"]))
        n.append(H.make_node("Mul", ["zero", "one"], ["s_spk"]))
        n.append(H.make_node("ReduceSum", ["depth"], ["s_depth"], keepdims=0)); scal("steps", "s_7"); scal("languages", "s_lang")
        n.append(H.make_node("Shape", ["f0"], ["f0shape"])); n.append(H.make_node("Gather", ["f0shape", "ax1"], ["Tvec"], axis=0))
        n.append(H.make_node("Cast", ["Tvec"], ["Tf"], to=F)); n.append(H.make_node("ReduceSum", ["Tf"], ["T_s"], keepdims=0))
    if extra_input: ins.append(vi(extra_input, F, [1, "T"]))
    names = []
    for k, s in enumerate(["s_tok", "s_dur", "s_gen", "s_vel", "s_spk", "s_depth", "s_7", "s_lang", "T_s"]):
        chan(s, f"ch{k+1}"); names.append(f"ch{k+1}")
    n.append(H.make_node("Shape", ["f0u"], ["f0ushape"])); n.append(H.make_node("Slice", ["f0ushape", "s0", "s2", "s0"], ["bt"]))
    n.append(H.make_node("Concat", ["bt", "c118"], ["padshape"], axis=0))
    n.append(H.make_node("Expand", ["pad118", "padshape"], ["padT"]))
    inits += [c("s0", [0], np.int64), c("s2", [2], np.int64), c("c118", [118], np.int64)]
    n.append(H.make_node("Concat", ["f0u"] + names + ["padT"], ["mel"], axis=2))
    save(name, n, ins, [vi("mel", F, [1, "T", 128])], inits)

acoustic("acoustic_legacy", legacy=True)
acoustic("acoustic_ca", legacy=False)
acoustic("acoustic_energy", legacy=True, extra_input="energy")
# vocoder: waveform[1,T*512], sample t*512+j = mel[t, j % 128] (f0 accepted, unused)
save("vocoder", [H.make_node("Tile", ["mel", "reps"], ["tiled"]), H.make_node("Reshape", ["tiled", "shp"], ["waveform"])],
     [vi("mel", F, [1, "T", 128]), vi("f0", F, [1, "T"])], [vi("waveform", F, [1, "N"])],
     [c("reps", [1, 1, 4], np.int64), c("shp", [1, -1], np.int64)])
# content: units[1,floor(N/320),768] = mean of each 320-sample hop, every channel
save("content", [
    H.make_node("Shape", ["source"], ["sh"]), H.make_node("Gather", ["sh", "one_i"], ["Nv"], axis=0),
    H.make_node("Div", ["Nv", "hop"], ["Tc"]), H.make_node("Mul", ["Tc", "hop"], ["Nuse"]),
    H.make_node("Slice", ["source", "s0", "Nuse", "one_i"], ["src"]),
    H.make_node("Reshape", ["src", "shp3"], ["fr"]), H.make_node("ReduceMean", ["fr"], ["m"], axes=[2], keepdims=1),
    H.make_node("Mul", ["m", "ones768"], ["units"])],
    [vi("source", F, [1, "N"])], [vi("units", F, [1, "Tc", 768])],
    [c("one_i", [1], np.int64), c("hop", [320], np.int64), c("s0", [0], np.int64), c("shp3", [1, -1, 320], np.int64),
     c("ones768", np.ones((1, 1, 768)))])
# rvc synth (48 kHz, hop 480): audio[1,1,T*480], sample t*480+j = feat[t, j % 8],
# feat = [pitchf, float(pitch), float(ds), rnd[0,0,t], rnd[0,191,t], phone[0,t,0], float(phone_lengths), 0]
def gath(src, idx, axis, out): return H.make_node("Gather", [src, idx], [out], axis=axis)
save("rvc_synth", [
    H.make_node("Unsqueeze", ["pitchf", "ax2"], ["c0"]),
    H.make_node("Cast", ["pitch"], ["pf"], to=F), H.make_node("Unsqueeze", ["pf", "ax2"], ["c1"]),
    H.make_node("Mul", ["c0", "zero"], ["z"]),
    H.make_node("Cast", ["ds"], ["dsf"], to=F), H.make_node("Add", ["z", "dsf"], ["c2"]),
    gath("rnd", "i0", 1, "r0"), gath("rnd", "i191", 1, "r191"),                        # [1,1,T] each
    H.make_node("Transpose", ["r0"], ["c3"], perm=[0, 2, 1]), H.make_node("Transpose", ["r191"], ["c4"], perm=[0, 2, 1]),
    gath("phone", "i0", 2, "c5"),                                                      # [1,T,1]
    H.make_node("Cast", ["phone_lengths"], ["plf"], to=F), H.make_node("Add", ["z", "plf"], ["c6"]),
    H.make_node("Concat", ["c0", "c1", "c2", "c3", "c4", "c5", "c6", "z"], ["feat"], axis=2),   # [1,T,8]
    H.make_node("Tile", ["feat", "reps"], ["tiled"]), H.make_node("Reshape", ["tiled", "shp"], ["audio"])],
    [vi("phone", F, [1, "T", 768]), vi("phone_lengths", I, [1]), vi("pitch", I, [1, "T"]), vi("pitchf", F, [1, "T"]),
     vi("ds", I, [1]), vi("rnd", F, [1, 192, "T"])], [vi("audio", F, [1, 1, "N"])],
    [c("ax2", [2], np.int64), c("zero", 0.0), c("i0", [0], np.int64), c("i191", [191], np.int64),
     c("reps", [1, 1, 60], np.int64), c("shp", [1, 1, -1], np.int64)])
(OX / "corrupt.onnx").write_bytes(bytes(range(256)) * 4)
(ROOT / "not_ort.bin").write_bytes(b"\x7fELF-not-really-onnxruntime" + bytes(4000))
(OX / "phonemes.txt").write_text("\n".join(PHONES) + "\n")
(OX / "phonemes.json").write_text(json.dumps({p: i for i, p in enumerate(PHONES)}, indent=0) + "\n")
(OX / "languages.json").write_text(json.dumps(LANGS) + "\n")
np.array([0.25, 0.5, 0.75, 1.0], "<f4").tofile(OX / "speaker.emb")          # sum 2.5
np.array([0.25, 0.5, 0.75], "<f4").tofile(OX / "speaker3.emb")              # wrong size for the legacy fixture

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def voice(dirname, acoustic_file, converter, extra_guide=None, phonemes="phonemes.txt", steps=20, depth=0.4):
    """Voice package v1 (D-008) whose files are copies of the fixtures above."""
    d = ROOT / dirname; (d / "guide").mkdir(parents=True, exist_ok=True)
    files = {"acoustic": f"guide/{acoustic_file}", "vocoder": "guide/vocoder.onnx", "phonemes": f"guide/{phonemes}"}
    files.update(extra_guide or {})
    for rel in files.values(): (d / rel).write_bytes((OX / pathlib.Path(rel).name).read_bytes())
    m = {"format": "singvoice", "format_version": 1, "name": dirname, "consent": "test fixture, no human voice",
         "guide_licence": "test fixture (Apache-2.0, this repository)",
         "guide": {"type": "diffsinger", "sample_rate": 44100, "hop_size": 512, "language": "en", "steps": steps, "depth": depth, "files": files},
         "converter": None, "sha256": {}}
    if converter:
        (d / "conv").mkdir(exist_ok=True)
        cf = {"synth": "conv/rvc_synth.onnx", "content": "conv/content.onnx"}
        for rel in cf.values(): (d / rel).write_bytes((OX / pathlib.Path(rel).name).read_bytes())
        m["converter"] = {"type": "rvc-v2", "sample_rate": 48000, "speaker_id": 2, "files": cf}
        files = {**files, **cf}
    m["sha256"] = {rel: sha(d / rel) for rel in sorted(files.values())}
    (d / "manifest.json").write_text(json.dumps(m, indent=1) + "\n")
voice("voice-legacy", "acoustic_legacy.onnx", converter=False, extra_guide={"speaker": "guide/speaker.emb"})
voice("voice-convert", "acoustic_legacy.onnx", converter=True, extra_guide={"speaker": "guide/speaker.emb"})
voice("voice-ca", "acoustic_ca.onnx", converter=False, extra_guide={"languages": "guide/languages.json"}, phonemes="phonemes.json")

# ---- MIDI (D-031), written byte by byte ----
def vlq(v):
    out = [v & 0x7F]; v >>= 7
    while v: out.append(0x80 | (v & 0x7F)); v >>= 7
    return bytes(reversed(out))
def meta(t, data): return b"\xff" + bytes([t]) + vlq(len(data)) + data
def trk(events): body = b"".join(vlq(d) + e for d, e in events) + vlq(0) + meta(0x2F, b""); return b"MTrk" + struct.pack(">I", len(body)) + body
def smf(fmt, tracks, division=480): return b"MThd" + struct.pack(">IHHH", 6, fmt, len(tracks), division) + b"".join(tracks)
tempo = lambda bpm: meta(0x51, struct.pack(">I", round(60e6 / bpm))[1:])
lyr = lambda s: meta(0x05, s.encode("utf-8"))
(ROOT / "lyrics.mid").write_bytes(smf(0, [trk([
    (0, tempo(120)), (0, lyr("hel-")), (0, b"\x90\x3c\x5a"), (480, b"\x80\x3c\x00"),
    (0, lyr("lo")), (0, b"\x90\x3e\x5a"), (480, b"\x80\x3e\x00"),
    (0, lyr(" world ")), (0, b"\x90\x40\x5a"), (480, b"\x80\x40\x00")])]))
# complex: format 1, 3 tracks; running status; velocity-0 note-off; retrigger; held note closed at track end; sysex;
# a second tempo; lyrics on two tracks at equal ticks (track order); an unknown chunk between tracks.
t0 = trk([(0, tempo(90)), (960, tempo(140)), (0, meta(0x01, b"text event, not a lyric"))])
t1 = trk([(0, lyr("a")), (0, b"\x91\x45\x40"), (240, b"\x45\x00"), (0, b"\x47\x40"),       # running status: on 71, off via vel 0
          (240, b"\xf0\x03\x7e\x7f\xf7"),                                                 # sysex skipped
          (0, b"\x91\x47\x40"),                                                           # retrigger 71 at tick 480
          (480, b"\x81\x47\x00"), (0, lyr("c")), (0, b"\x91\x48\x40"),                      # 72 held to track end (tick 1200)
          (0, b"\x91\x49\x40"), (0, b"\x81\x49\x00"),                                         # 73: zero length, dropped
          (240, meta(0x01, b"pad"))])
t2 = trk([(0, lyr("b")), (480, b"\x92\x30\x40"), (480, b"\x82\x30\x00"), (0, b"\x82\x31\x00")])   # stray off ignored
unknown = b"XFIH" + struct.pack(">I", 4) + b"abcd"
(ROOT / "complex.mid").write_bytes(b"MThd" + struct.pack(">IHHH", 6, 1, 3, 480) + t0 + unknown + t1 + t2)
(ROOT / "smpte.mid").write_bytes(b"MThd" + struct.pack(">IHHH", 6, 0, 1, 0xE728) + trk([(0, b"\x90\x3c\x40"), (100, b"\x80\x3c\x00")]))
(ROOT / "format2.mid").write_bytes(smf(2, [trk([(0, b"\x90\x3c\x40"), (100, b"\x80\x3c\x00")])]))
print("fixtures written:", sorted(p.name for p in ROOT.rglob("*") if p.is_file() and p.suffix != ".py"))
