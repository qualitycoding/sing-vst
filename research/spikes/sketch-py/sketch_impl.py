"""Reference sketch of the frozen Python interfaces (PK-21, PK-22): written from the docstrings alone, used only to show
that every frozen test can pass. Not shipped; the implementer writes the real modules (S-012..S-015).
run.sh overlays these functions onto a throw-away copy of the repository and runs the frozen suite there."""
from __future__ import annotations

import argparse, datetime, hashlib, importlib.machinery, importlib.metadata, importlib.util, json, math, os, platform
import random, re, shutil, struct, subprocess, tempfile
from pathlib import Path

import numpy as np


# ---- pipeline
def atomic_write_text(path: Path, text: str) -> None:
    path = Path(path)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=path.name + ".", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(text); f.flush(); os.fsync(f.fileno())
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def content_hash(paths):
    items = []
    for p in paths:
        p = Path(p)
        if not p.exists():
            raise ValueError(f"missing path {p}")
        files = [p] if p.is_file() else [f for f in p.rglob("*") if f.is_file()]
        items += [(f.relative_to(p.parent).as_posix(), f) for f in files]
    h = hashlib.sha256()
    for rel, f in sorted(items):
        data = f.read_bytes()
        h.update(rel.encode() + b"\0" + struct.pack("<Q", len(data)) + data)
    return h.hexdigest()


def run_stages(stages, state_dir):
    names = [s.name for s in stages]
    if len(set(names)) != len(names):
        raise ValueError("stage names must be unique")
    state_dir = Path(state_dir); state_dir.mkdir(parents=True, exist_ok=True)
    forced, ran = False, []
    for st in stages:
        h, marker = content_hash(st.inputs), state_dir / f"{st.name}.done"
        if not forced and marker.exists() and marker.read_text() == h and all(Path(o).exists() for o in st.outputs):
            continue
        forced = True
        for o in st.outputs:
            o = Path(o)
            if o.is_dir(): shutil.rmtree(o)
            elif o.exists(): o.unlink()
        st.run()
        for o in st.outputs:
            if not Path(o).exists():
                raise RuntimeError(f"stage {st.name}: output never produced: {o}")
        atomic_write_text(marker, h)
        ran.append(st.name)
    return ran


# ---- prepare
def split_heldout(files, seed, fraction=0.1):
    if len(set(files)) != len(files): raise ValueError("duplicate file names")
    if not 0.0 <= fraction <= 0.5: raise ValueError("fraction outside [0, 0.5]")
    s = sorted(files); n = len(s); k = 0 if n < 2 else max(1, round(fraction * n))
    perm = np.random.default_rng(seed).permutation(n)
    held = sorted(s[i] for i in perm[:k])
    return sorted(set(s) - set(held)), held


def slice_on_silence(x, sr, threshold_db=-40.0, min_sec=2.0, max_sec=15.0):
    x = np.asarray(x)
    if x.ndim != 1: raise ValueError("x must be 1-D")
    f = round(0.02 * sr); nf = math.ceil(len(x) / f); loud = []
    for i in range(nf):
        seg = x[i * f:(i + 1) * f].astype(np.float64); rms = math.sqrt(float(np.mean(seg ** 2)))
        loud.append((20 * math.log10(rms) if rms > 0 else -math.inf) >= threshold_db)
    out, i = [], 0
    while i < nf:
        if not loud[i]: i += 1; continue
        j = i
        while j < nf and loud[j]: j += 1
        a, b = i * f, min(j * f, len(x)); L = b - a
        if L >= min_sec * sr:
            if L > max_sec * sr:
                c = math.ceil(L / (max_sec * sr)); size = L // c
                out += [(a + q * size, a + (q + 1) * size if q < c - 1 else b) for q in range(c)]
            else:
                out.append((a, b))
        i = j
    return out


def normalise(x, target_rms_dbfs=-20.0, peak_ceiling_dbfs=-1.0):
    x64 = np.asarray(x, np.float64); rms = math.sqrt(float(np.mean(x64 ** 2))) if x64.size else 0.0
    if rms == 0: return np.array(x, copy=True)
    g = 10 ** (target_rms_dbfs / 20) / rms; ceil = 10 ** (peak_ceiling_dbfs / 20); peak = float(np.max(np.abs(x64))) * g
    if peak > ceil: g *= ceil / peak
    return (x64 * g).astype(np.float32)


def build_dataset_manifest(out_dir, segments, params):
    out_dir = Path(out_dir); segs = []
    for s in segments:
        p = out_dir / s["file"]
        if not p.exists(): raise FileNotFoundError(p)
        segs.append(dict(s, sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
    obj = {"params": params, "segments": segs}
    atomic_write_text(out_dir / "dataset.json", json.dumps(obj, indent=1, sort_keys=True))
    return obj


# ---- provenance
REQUIRED_KEYS = ("git_commit", "lockfile_sha256", "seeds", "params", "utc_timestamp", "hardware", "threads")


def collect(params, seeds, repo_root, lockfile):
    lock = hashlib.sha256(Path(lockfile).read_bytes()).hexdigest()
    r = subprocess.run(["git", "-C", str(repo_root), "rev-parse", "HEAD"], capture_output=True, text=True)
    commit = r.stdout.strip() if r.returncode == 0 and re.fullmatch(r"[0-9a-f]{40}", r.stdout.strip()) else "unknown"
    try:
        gpu = subprocess.run(["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"], capture_output=True,
                             text=True).stdout.splitlines()[0].strip() or "none"
    except (OSError, IndexError):
        gpu = "none"
    return {"git_commit": commit, "lockfile_sha256": lock, "seeds": dict(seeds), "params": dict(params),
            "utc_timestamp": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            "hardware": {"platform": platform.platform(), "cpu": platform.processor() or platform.machine(), "gpu": gpu},
            "threads": os.cpu_count()}


def write_sidecar(result_file, record):
    missing = [k for k in REQUIRED_KEYS if k not in record]
    if missing: raise ValueError(f"missing keys: {missing}")
    p = Path(result_file); side = p.with_name(p.name + ".provenance.json")
    atomic_write_text(side, json.dumps(record, indent=1, sort_keys=True)); return side


# ---- metrics
def load_pyworld():
    dist = importlib.metadata.distribution("pyworld")
    so = next(f for f in dist.files if f.name.startswith("pyworld.") and f.suffix in (".so", ".pyd"))
    path = str(dist.locate_file(so)); loader = importlib.machinery.ExtensionFileLoader("pyworld.pyworld", path)
    spec = importlib.util.spec_from_file_location("pyworld.pyworld", path, loader=loader)
    m = importlib.util.module_from_spec(spec); loader.exec_module(m); return m


def extract_f0(x, sr, frame_period_ms=10.0):
    pw = load_pyworld(); x = np.asarray(x, np.float64)
    f0, t = pw.harvest(x, sr, f0_floor=50.0, f0_ceil=1100.0, frame_period=frame_period_ms)
    return pw.stonemask(x, f0, t, sr)


def cents(est_hz, ref_hz):
    e, r = np.asarray(est_hz, float), np.asarray(ref_hz, float)
    if e.shape != r.shape or np.any(e <= 0) or np.any(r <= 0): raise ValueError("positive arrays of equal shape")
    return 1200 * np.log2(e / r)


def score_f0(f0_hz, frame_period_s, notes, edge_s=0.05, octave_cents=600.0):
    errs, octs = [], 0
    for a, b, m in notes:
        ref = 440 * 2 ** ((m - 69) / 12)
        for i, f in enumerate(f0_hz):
            t = i * frame_period_s
            if a + edge_s <= t <= b - edge_s and f > 0:
                c = float(1200 * math.log2(f / ref))
                if abs(c) > octave_cents: octs += 1
                else: errs.append(c)
    if not errs: raise ValueError("no scorable frame")
    return {"rms_cents": math.sqrt(sum(c * c for c in errs) / len(errs)), "scored_frames": len(errs),
            "octave_errors": octs, "octave_fraction": octs / (len(errs) + octs)}


def normalise_text(s):
    words = re.sub(r"[^\w'\s]|_", " ", s.lower()).split()
    return [w.strip("'") for w in words if w.strip("'")]


def wer(reference, hypothesis):
    r, h = normalise_text(reference), normalise_text(hypothesis)
    if not r: raise ValueError("empty reference")
    d = list(range(len(h) + 1))
    for i, rw in enumerate(r, 1):
        prev, d[0] = d[0], i
        for j, hw in enumerate(h, 1):
            prev, d[j] = d[j], min(d[j] + 1, d[j - 1] + 1, prev + (rw != hw))
    return d[len(h)] / len(r)


def cosine(a, b):
    a, b = np.asarray(a, float), np.asarray(b, float)
    if a.ndim != 1 or a.shape != b.shape or not np.any(a) or not np.any(b): raise ValueError("bad vectors")
    return float(a @ b / (np.linalg.norm(a) * np.linalg.norm(b)))


def judge(report, thresholds):
    s, g = report["speaker_similarity"], report["guide_similarity"]
    v = {"speaker_similarity": s >= thresholds["speaker_similarity_min"],
         "similarity_gain": s - g >= thresholds["similarity_gain_min"],
         "f0_rms_cents": report["f0_rms_cents"] <= thresholds["f0_rms_cents_max"],
         "wer": report["wer"] <= thresholds["wer_max"],
         "realtime_factor": report["realtime_factor"] <= thresholds["realtime_factor_max"]}
    return dict(v, all=all(v.values()), status=thresholds["status"])


# ---- pack
SAFE = re.compile(r"^[A-Za-z0-9._-]+$")


def pack_voice(out_dir, name, consent, guide_licence, guide_files, converter_files, *, language="en", steps=20, depth=0.4,
               converter_sample_rate=48000, speaker_id=0):
    out_dir = Path(out_dir)
    if not (name and consent and guide_licence): raise ValueError("name, consent and guide_licence are required")
    req, opt = ("acoustic", "vocoder", "phonemes"), ("speaker", "languages")
    if set(req) - set(guide_files) or set(guide_files) - set(req) - set(opt): raise ValueError("guide roles")
    if converter_files is not None and set(converter_files) != {"synth", "content"}: raise ValueError("converter roles")
    if not (isinstance(steps, int) and 1 <= steps <= 1000) or not (0 < depth <= 1): raise ValueError("steps/depth")
    if converter_sample_rate not in (48000, 32000) or speaker_id < 0: raise ValueError("converter parameters")
    if out_dir.exists() and any(out_dir.iterdir()): raise ValueError("out_dir not empty")
    plan = [("guide", r, Path(p)) for r, p in guide_files.items()] + \
           [("conv", r, Path(p)) for r, p in (converter_files or {}).items()]
    dests = [f"{d}/{p.name}" for d, _, p in plan]
    if len(set(dests)) != len(dests): raise ValueError("duplicate destination")
    for _, _, p in plan:
        if not SAFE.match(p.name) or p.name in (".", ".."): raise ValueError(f"unsafe name {p.name}")
    sha, gf, cf = {}, {}, {}
    for (d, r, p), rel in zip(plan, dests):
        (out_dir / d).mkdir(parents=True, exist_ok=True); shutil.copyfile(p, out_dir / rel)
        sha[rel] = hashlib.sha256((out_dir / rel).read_bytes()).hexdigest(); (gf if d == "guide" else cf)[r] = rel
    m = {"format": "singvoice", "format_version": 1, "name": name, "consent": consent, "guide_licence": guide_licence,
         "guide": {"type": "diffsinger", "sample_rate": 44100, "hop_size": 512, "language": language, "steps": steps,
                   "depth": depth, "files": gf},
         "converter": None if converter_files is None else {"type": "rvc-v2", "sample_rate": converter_sample_rate,
                                                            "speaker_id": speaker_id, "files": cf},
         "sha256": sha}
    (out_dir / "manifest.json").write_text(json.dumps(m, indent=1), encoding="utf-8"); return m


# ---- security
PATTERNS = (r"github_pat_[A-Za-z0-9_]{20,}", r"ghp_[A-Za-z0-9]{20,}", r"gho_[A-Za-z0-9]{20,}", r"AKIA[0-9A-Z]{16}",
            r"-----BEGIN [A-Z ]*PRIVATE KEY-----", r"hf_[A-Za-z0-9]{30,}", r"KGAT_[A-Za-z0-9]{20,}")


def scan_secrets(root, exclude_dirs=(".git",)):
    root = Path(root); rx = re.compile("|".join(PATTERNS)); hits = []
    for dp, dns, fns in os.walk(root):
        dns[:] = [d for d in dns if d not in exclude_dirs]
        for fn in fns:
            p = Path(dp) / fn; data = p.read_bytes()
            if b"\0" in data[:8192]: continue
            for n, line in enumerate(data.decode("utf-8", "replace").splitlines(), 1):
                if rx.search(line): hits.append(f"{p.relative_to(root).as_posix()}:{n}")
    return sorted(hits)


# ---- rvc_files
def write_filelist(exp_dir, rvc_root, speaker_id=0, sr_tag="48k", seed=0):
    exp_dir = Path(exp_dir); e = exp_dir.resolve().as_posix(); m = (Path(rvc_root) / "logs" / "mute").resolve().as_posix()
    stems = sorted(p.name[:-4] for p in (exp_dir / "0_gt_wavs").glob("*.wav")
                   if all((exp_dir / s / f"{p.name[:-4]}{x}").exists() for s, x in
                          (("3_feature768", ".npy"), ("2a_f0", ".wav.npy"), ("2b-f0nsf", ".wav.npy"))))
    if not stems: raise ValueError("no complete stem")
    lines = [f"{e}/0_gt_wavs/{s}.wav|{e}/3_feature768/{s}.npy|{e}/2a_f0/{s}.wav.npy|{e}/2b-f0nsf/{s}.wav.npy|{speaker_id}"
             for s in stems]
    lines += [f"{m}/0_gt_wavs/mute{sr_tag}.wav|{m}/3_feature768/mute.npy|{m}/2a_f0/mute.wav.npy|{m}/2b-f0nsf/mute.wav.npy|{speaker_id}"] * 2
    random.Random(seed).shuffle(lines)
    out = exp_dir / "filelist.txt"; out.write_text("".join(l + "\n" for l in lines), encoding="utf-8"); return out


def copy_config(exp_dir, rvc_root, sr_tag="48k"):
    if sr_tag not in ("48k", "32k"): raise ValueError(sr_tag)
    dst = Path(exp_dir) / "config.json"; shutil.copyfile(Path(rvc_root) / "configs" / "v2" / f"{sr_tag}.json", dst); return dst


def train_command(python, exp_name, sr_tag="48k", batch_size=8, total_epochs=200, save_every=10, gpus="0"):
    if total_epochs <= 0 or save_every <= 0 or total_epochs % save_every: raise ValueError("epochs")
    return [python, "train/train.py", "-e", exp_name, "-sr", sr_tag, "-f0", "1", "-bs", str(batch_size), "-g", gpus, "-te",
            str(total_epochs), "-se", str(save_every), "-pg", f"assets/pretrained_v2/f0G{sr_tag}.pth", "-pd",
            f"assets/pretrained_v2/f0D{sr_tag}.pth", "-l", "1", "-c", "0", "-sw", "1", "-v", "v2"]


def latest_weights(rvc_root, exp_name):
    w = Path(rvc_root) / "assets" / "weights"
    if (w / f"{exp_name}.pth").exists(): return w / f"{exp_name}.pth"
    rx = re.compile(rf"^{re.escape(exp_name)}_e(\d+)_s(\d+)\.pth$")
    c = [(int(m.group(1)), p) for p in w.glob("*.pth") if (m := rx.match(p.name))]
    if not c: raise FileNotFoundError(f"no weights for {exp_name}")
    return max(c)[1]


# ---- evaluate
def transpose_semitones(phrase_midi, training_median_hz):
    if not phrase_midi or training_median_hz <= 0: raise ValueError("bad input")
    k = 69 + 12 * math.log2(training_median_hz / 440) - float(np.median(phrase_midi))
    cands = sorted({math.floor(k), math.ceil(k)}, key=lambda c: (round(abs(c - k), 9), abs(c), c >= 0))
    return cands[0]


# ---- cli
COMMANDS = ("prepare", "split", "rvc-files", "rvc-train-command", "export", "make-test-weights", "pack", "evaluate",
            "provenance")


def build_parser():
    p = argparse.ArgumentParser(prog="singvst-train"); sub = p.add_subparsers(dest="command", required=True)
    for c in COMMANDS:
        s = sub.add_parser(c)
        if c == "split":
            s.add_argument("--files-dir", required=True); s.add_argument("--seed", type=int, required=True)
            s.add_argument("--fraction", type=float, default=0.1); s.add_argument("--out", required=True)
    return p


def main(argv=None):
    a = build_parser().parse_args(argv)
    if a.command == "split":
        names = sorted(p.name for p in Path(a.files_dir).glob("*.wav"))
        tr, ho = split_heldout(names, a.seed, a.fraction)
        Path(a.out).write_text(json.dumps({"train": tr, "heldout": ho}, indent=1)); return 0
    return 3
