"""Spike R6 (round 3): renders a short English phrase through the TIGER DiffSinger v102 acoustic model and its bundled vocoder
with ONNX Runtime, using the input conventions read from OpenUtau a06ab28 (DiffSingerRenderer.cs lines 245-360,
DiffSingerUtils.cs lines 15-83). Measures wall time and the unclipped peak, and tests whether the scalar inputs need rank 0 or rank 1.
Usage: python -I run.py <extracted TIGER_DS_v102 voice-library dir> <out dir>"""
import sys, time, pathlib
import numpy as np, onnxruntime as ort, soundfile as sf

vb, out = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2]); out.mkdir(parents=True, exist_ok=True)
SR, HOP, HEAD, TAIL = 44100, 512, 8, 8
fr = SR / HOP
phones = (vb / "dsacoustic/phonemes.txt").read_text().split("\n")
tok = {p: i for i, p in enumerate(phones) if p}
print("phoneme count", len(tok), "| CMUdict ARPAbet missing:", [p for p in "aa ae ah ao aw ay b ch d dh eh er ey f g hh ih iy jh k l m n ng ow oy p r s sh t th uh uw v w y z zh".split() if p not in tok])
# "hello world" on C4 D4 E4 E4, 120 bpm, quarter notes (0.5 s each); simple layout: onset consonants 0.06 s each
spans = [("hh", .06), ("ah", .38), ("l", .06), ("ow", .44), ("w", .06), ("er", .82), ("l", .06), ("d", .06), ("SP", .06)]
notes_hz = [261.6256, 293.6648, 329.6276, 329.6276]
t = 0; bounds = []
for p, d in spans: bounds.append((p, t, t + d)); t += d
total = int(round(t * fr)); b = 0; durs = []
for i, (p, s, e) in enumerate(bounds):
    nb = max(int(round(e * fr)), b + 1) if i < len(bounds) - 1 else total; durs.append(nb - b); b = nb
durs = [HEAD] + durs + [TAIL]; ids = [tok["SP"]] + [tok[p] for p, _, _ in bounds] + [tok["SP"]]
T = sum(durs)
f0 = np.empty(T, np.float32)
for i in range(T):
    ts = (i - HEAD) / fr
    k = min(max(int(ts / 0.5), 0), 3); f0[i] = notes_hz[k]
emb = np.fromfile(vb / "dsacoustic/tiger_fresh.emb", dtype=np.float32)
so = ort.SessionOptions(); so.intra_op_num_threads = 2
t0 = time.perf_counter()
ac = ort.InferenceSession(str(vb / "dsacoustic/tiger_acou.onnx"), so, providers=["CPUExecutionProvider"])
vo = ort.InferenceSession(str(vb / "dsvocoder/tgm_hifigan.onnx"), so, providers=["CPUExecutionProvider"])
print(f"load {time.perf_counter() - t0:.2f} s")
base = {"tokens": np.array([ids], np.int64), "durations": np.array([durs], np.int64), "f0": f0[None],
        "gender": np.zeros((1, T), np.float32), "velocity": np.ones((1, T), np.float32),
        "spk_embed": np.repeat(emb[None, None, :], T, axis=1).astype(np.float32)}
for rank, mk in (("rank0", lambda v: np.array(v, np.int64)), ("rank1", lambda v: np.array([v], np.int64))):
    try:
        ac.run(None, dict(base, depth=mk(400), speedup=mk(20))); print(rank, "scalars accepted")
    except Exception as ex:
        print(rank, "scalars rejected:", str(ex).splitlines()[0][:160])
times = []
for _ in range(2):
    t0 = time.perf_counter(); mel = ac.run(None, dict(base, depth=np.array(400, np.int64), speedup=np.array(20, np.int64)))[0]; ta = time.perf_counter() - t0
    t0 = time.perf_counter(); wav = vo.run(None, {"mel": mel, "f0": f0[None]})[0][0]; tv = time.perf_counter() - t0
    times.append((ta, tv))
audio_sec = (T - HEAD - TAIL) * HOP / SR
print(f"frames {T} (incl. {HEAD}+{TAIL} pad), mel {mel.shape}, waveform {wav.shape[0]} samples = {wav.shape[0] / HOP:.1f} frames")
print(f"acoustic {times[-1][0]:.2f} s, vocoder {times[-1][1]:.2f} s for {audio_sec:.2f} s audio -> guide RTF {sum(times[-1]) / audio_sec:.2f} (2 threads, ORT {ort.__version__})")
trim = wav[HEAD * HOP: len(wav) - TAIL * HOP]
print(f"unclipped peak {np.max(np.abs(wav)):.3f}; trimmed length {len(trim)} = {len(trim) / HOP:.1f} frames; sha256 of inputs reproducible: seedless diffusion? second-run max|diff| mel n/a")
mel2 = ac.run(None, dict(base, depth=np.array(400, np.int64), speedup=np.array(20, np.int64)))[0]
print(f"acoustic determinism: max|mel1-mel2| = {float(np.max(np.abs(mel - mel2))):.3e}")
sf.write(out / "hello_world_guide.wav", trim, SR, subtype="FLOAT")
