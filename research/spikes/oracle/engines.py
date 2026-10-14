"""Independent Python implementation of D-012 (guide and converter engines) and D-013 (renderTake) over onnxruntime, used to
derive the expected values of T-043..T-049 from the fixture models (PK-21). Not shipped."""
import json, math, pathlib, sys
import numpy as np, onnxruntime as ort
sys.path.insert(0, str(pathlib.Path(__file__).parent)); import oracle as o

FR_G = 44100 / 512
def sess(p): return ort.InferenceSession(str(p), providers=["CPUExecutionProvider"])

class Guide:
    def __init__(self, d, files, steps=20, depth=0.4, language="en"):
        d = pathlib.Path(d); self.ac = sess(d / files["acoustic"]); self.vo = sess(d / files["vocoder"])
        ph = d / files["phonemes"]
        self.vocab = json.loads(ph.read_text()) if ph.suffix == ".json" else {p: i for i, p in enumerate(ph.read_text().split("\n")[:-1] if ph.read_text().endswith("\n") else ph.read_text().split("\n"))}
        self.langs = json.loads((d / files["languages"]).read_text()) if "languages" in files else {}
        self.spk = np.fromfile(d / files["speaker"], "<f4") if "speaker" in files else None
        self.inputs = {i.name: i for i in self.ac.get_inputs()}
        allowed = {"tokens", "durations", "f0", "gender", "velocity", "spk_embed", "languages", "steps", "depth", "speedup"}
        bad = set(self.inputs) - allowed
        if bad: raise o.ValidationError(f"unsupported input {sorted(bad)}")
        if "spk_embed" in self.inputs:
            if self.spk is None: raise o.ValidationError("speaker required")
            dim = self.inputs["spk_embed"].shape[-1]
            if isinstance(dim, int) and dim != len(self.spk): raise o.ValidationError("speaker size")
        self.steps, self.depth, self.language = steps, depth, language
    def tok(self, p):
        if p in self.vocab: return self.vocab[p], 0
        q = f"{self.language}/{p}"
        if q in self.vocab: return self.vocab[q], self.langs.get(self.language, 0)
        raise o.ValidationError(f"unknown phoneme '{p}'")
    def scalar(self, name, v, dt):
        rank = len(self.inputs[name].shape); a = np.array(v, dtype=dt)
        return a.reshape([1]) if rank == 1 else a.reshape([])
    def render(self, spans, f0):
        dur = o.frame_durations([list(s) for s in spans], FR_G)
        if len(f0) != sum(dur): raise o.ValidationError("f0 length")
        f0 = np.array(f0, np.float32); v = np.nonzero(f0 > 0)[0]
        if len(v) == 0: raise o.ValidationError("no voiced frame")
        for i in range(len(f0)):
            if f0[i] <= 0:
                j = np.argmin(np.abs(v - i)); f0[i] = f0[v[j]]          # argmin returns the first (earlier) on ties
        out = np.zeros(sum(dur) * 512, np.float32)
        # phrases: maximal runs of spans not containing an SP span of >= 22 frames
        b = np.concatenate([[0], np.cumsum(dur)]).astype(int); runs, cur = [], []
        for k, s in enumerate(spans):
            if s[0] == "SP" and dur[k] >= 22:
                if cur: runs.append(cur); cur = []
            else: cur.append(k)
        if cur: runs.append(cur)
        for r in runs:
            ids, langs = zip(*[self.tok(spans[k][0]) for k in r])
            sp = self.vocab["SP"]; toks = [sp] + list(ids) + [sp]; ls = [0] + list(langs) + [0]; ds = [8] + [dur[k] for k in r] + [8]
            a, z = b[r[0]], b[r[-1] + 1]; pf = np.concatenate([np.full(8, f0[a]), f0[a:z], np.full(8, f0[z - 1])]).astype(np.float32); T = len(pf)
            feed = {"tokens": np.array([toks], np.int64), "durations": np.array([ds], np.int64), "f0": pf[None]}
            if "gender" in self.inputs: feed["gender"] = np.zeros((1, T), np.float32)
            if "velocity" in self.inputs: feed["velocity"] = np.ones((1, T), np.float32)
            if "spk_embed" in self.inputs: feed["spk_embed"] = np.tile(self.spk[None, None, :], (1, T, 1)).astype(np.float32)
            if "languages" in self.inputs: feed["languages"] = np.array([ls], np.int64)
            if "steps" in self.inputs:
                feed["steps"] = self.scalar("steps", self.steps, np.int64)
                if "depth" in self.inputs: feed["depth"] = self.scalar("depth", self.depth, np.float32)
            elif "speedup" in self.inputs:
                if "depth" in self.inputs:
                    d = int(math.floor(self.depth * 1000 + 0.5)); su = max(1, d // self.steps); d = d // su * su
                    feed["depth"] = self.scalar("depth", d, np.int64)
                else: su = max(x for x in range(1, 1001) if 1000 % x == 0 and x <= 1000 // self.steps)
                feed["speedup"] = self.scalar("speedup", su, np.int64)
            mel = self.ac.run(None, feed)[0]; wav = self.vo.run(None, {"mel": mel, "f0": pf[None]})[0][0]
            out[a * 512: z * 512] = wav[8 * 512: len(wav) - 8 * 512]
        return out

class Converter:
    def __init__(self, d, files, sr=48000, speaker_id=2):
        d = pathlib.Path(d); self.content = sess(d / files["content"]); self.synth = sess(d / files["synth"]); self.sr, self.sid = sr, speaker_id
    def convert(self, guide, gsr, f0, seed):
        g16 = np.asarray(o.resample(guide, gsr, 16000), np.float32); hop = self.sr // 100
        T = min(len(f0), len(g16) // 160)
        rnd = np.array(o.standard_normal(seed, 192 * T), np.float32).reshape(192, T)
        f0 = np.asarray(f0[:T], np.float32); pitch = np.array([o.rvc_coarse(float(h)) for h in f0], np.int64)
        out = np.zeros(T * hop, np.float32)
        for a in range(0, T, 1500):
            bnd = min(a + 1500, T); lo = max(0, a - 100); hi = min(T, bnd + 100); n = hi - lo
            u = self.content.run(None, {"source": g16[lo * 160: hi * 160][None]})[0][0]
            u2 = np.repeat(u, 2, axis=0)
            if len(u2) < n: u2 = np.concatenate([u2, np.repeat(u2[-1:], n - len(u2), axis=0)])
            u2 = u2[:n]
            y = self.synth.run(None, {"phone": u2[None].astype(np.float32), "phone_lengths": np.array([n], np.int64), "pitch": pitch[lo:hi][None],
                                      "pitchf": f0[lo:hi][None], "ds": np.array([self.sid], np.int64), "rnd": rnd[:, lo:hi][None]})[0][0, 0]
            out[a * hop: bnd * hop] = y[(a - lo) * hop: (bnd - lo) * hop]
        return out
