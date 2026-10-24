# (3) Paths, helpers and the stage table (D-035 sections "Kernel and helpers", "Time and budget"). Nothing here needs editing.
import datetime
import glob
import hashlib
import json
import math
import os
import re
import shlex
import shutil
import signal
import subprocess
import sys
import tarfile
import threading
import time
import traceback
from collections import deque
from pathlib import Path

PLATFORM = "@PLATFORM@"                       # a constant of this notebook
PATH_ROOTS = globals().get("PATH_ROOTS", {"content": "/content", "kaggle": "/kaggle", "tmp": "/tmp"})
CLOCK = globals().get("CLOCK", time.time)     # seconds; every duration below is measured with it
HEARTBEAT_INTERVAL = globals().get("HEARTBEAT_INTERVAL", 300)
BUDGET_HOURS = 20                             # A-015; only a raise-budget-to amendment changes it
RVC_COMMIT = "81eed5e8f68b6bed1789f682fe78cdd324495afc"
RVC_ASSETS_REVISION = "e6d0c1a17da07c33557852f9dfa2bd44cc75737d"   # Hugging Face lj1995/VoiceConversionWebUI (plan/ENVIRONMENT.md)
TIGER_URL = "https://github.com/spicytigermeat/tiger_diffsinger/releases/download/v102/TIGER_DS_v102_PACK.zip"
TIGER_SHA256 = "925ca2ad44287757d26628608b2744381e75748042d0e6fae356ee8cdae19f4e"
TIGER_LICENCE = "TIGER DiffSinger v102, CC BY-NC-ND 4.0 + Commons Clause, personal non-commercial use (C-037)"
GPU_STAGES = ("rvc-f0", "rvc-features", "train", "export", "evaluate", "t-p20")


class SessionEnd(Exception):
    """The session reached its time limit; the next session resumes."""


class BudgetStop(Exception):
    """The GPU-hour budget is used up and no loadable weight snapshot exists."""


class OwnerAction(Exception):
    """A stop the owner can fix; raised as OwnerAction(cell, message)."""

    def __init__(self, cell, message):
        super().__init__(f"{cell} {message}")
        self.cell, self.message = cell, message


def owner_stop(cell, message):
    """Cells (3) and (4): print the `owner:` line the G-004 response quotes, then raise."""
    print(f"owner: {cell} {message}")
    raise OwnerAction(cell, message)


# ---- cell (3) checks and paths -------------------------------------------------------------------------------------
if PLATFORM_EXPECTED != PLATFORM:
    owner_stop(3, f"PLATFORM_EXPECTED is '{PLATFORM_EXPECTED}' but this is the {PLATFORM} notebook: use the notebook GATE-G-004.md names")
if PLATFORM == "colab" and KILLED_HOURS != 0.0:
    owner_stop(3, "KILLED_HOURS must be 0.0 on Colab (a killed Colab session is covered by the heartbeat)")

if PLATFORM == "colab":
    ROOT = f"{PATH_ROOTS['content']}/drive/MyDrive/singvst/{VOICE}"
    RVC, SINGVST = f"{PATH_ROOTS['content']}/rvc", f"{PATH_ROOTS['content']}/sing-vst"
    VENV, LOCAL = f"{PATH_ROOTS['content']}/py312", f"{PATH_ROOTS['content']}/local"
    RAW, WORKING = f"{ROOT}/raw", None
else:
    WORKING = f"{PATH_ROOTS['kaggle']}/working"
    ROOT = WORKING
    RVC, SINGVST = f"{PATH_ROOTS['tmp']}/rvc", f"{PATH_ROOTS['tmp']}/sing-vst"
    VENV, LOCAL = f"{PATH_ROOTS['tmp']}/py312", f"{PATH_ROOTS['tmp']}/local"
    RAW = f"{PATH_ROOTS['kaggle']}/input/singvst-{VOICE}"
RUNDIR = f"{ROOT}/run{RUN}"
EXP = f"{VOICE}-run{RUN}"
SESSION = datetime.datetime.fromtimestamp(SESSION_T0, datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
COMMIT = EXPECTED_COMMIT                       # step (4a) checks the checkout is exactly this commit
BATCH_SIZE = globals().get("BATCH_SIZE", 8)    # step (10a) lowers it to 4 on a small GPU

STOP, STOP_REASON = False, ""
CURRENT_STAGE, STAGE_T0 = None, 0.0
HEARTBEAT = globals().get("HEARTBEAT")         # module-level singleton, stopped and joined by step (4e) of a re-run
HEARTBEAT_ERROR = None
HEARTBEAT_STOP = globals().get("HEARTBEAT_STOP") or threading.Event()
SESSION_ENTRY, SEQ, STAGE_INT, STAGES_RUN, LAST_PGID = None, 0, {}, [], None
_BUDGET_LOCK = threading.Lock()
BUDGET_FILE = f"{RUNDIR}/out/budget.json"
VOICE_FILE = f"{ROOT}/budget-voice.json"
CELL_STAGES = {7: ["split"], 8: ["prepare"], 9: ["rvc-preprocess", "rvc-f0", "rvc-features"], 10: ["rvc-files"], 11: ["train"],
               12: ["export"], 13: ["render-bin"], 14: ["pack"], 15: ["evaluate"]}


# ---- hours are held as integer ten-thousandths of an hour, rounded up once --------------------------------------------
def _ceil4(hours):
    return math.ceil(round(hours * 10 ** 4, 6))


def _dec(units):
    return round(units / 10 ** 4, 4)


def is_gpu_stage(name):
    return name in GPU_STAGES or (name == "prepare" and DEREVERB)


def _pipeline():
    from singvst_train import pipeline
    return pipeline


def _atomic_json(path, obj):
    _pipeline().atomic_write_text(Path(path), json.dumps(obj, indent=1, sort_keys=True) + "\n")


def _read_json(path, default):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError:
        return default


def _iso(seconds):
    return datetime.datetime.fromtimestamp(seconds, datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _session_ints():
    ints = dict(STAGE_INT)
    if CURRENT_STAGE is not None and is_gpu_stage(CURRENT_STAGE):
        ints[CURRENT_STAGE] = ints.get(CURRENT_STAGE, 0) + _ceil4((CLOCK() - STAGE_T0) / 3600.0)
    return ints


def _run_total():
    """runs[RUN]: every session of this run's budget.json; the live session uses its in-memory hours."""
    live = SESSION_ENTRY["start"] if SESSION_ENTRY else None
    total = sum(_ceil4(s["gpu_hours"]) for s in _read_json(BUDGET_FILE, {"sessions": []})["sessions"] if s.get("start") != live)
    return total + sum(_session_ints().values())


def _hours():
    """(platform total, voice total) in ten-thousandths: sum of runs, then plus PRIOR_VOICE_GPU_HOURS and KILLED_HOURS."""
    others = sum(_ceil4(h) for r, h in _read_json(VOICE_FILE, {"runs": {}})["runs"].items() if r != str(RUN))
    platform_total = others + _run_total()
    return platform_total, platform_total + _ceil4(PRIOR_VOICE_GPU_HOURS) + _ceil4(KILLED_HOURS)


def print_hours():
    p, v = _hours()
    print(f"hours: platform {p / 10 ** 4:.4f} voice {v / 10 ** 4:.4f}")


def _write_budget(final=False):
    """One write of budget.json and budget-voice.json; re-reads both and updates only this session's entry (R-074)."""
    with _BUDGET_LOCK:
        ints = _session_ints()
        e = SESSION_ENTRY
        e["gpu_hours"] = _dec(sum(ints.values()))
        e["stage_hours"] = {k: _dec(v) for k, v in sorted(ints.items())}
        e["session_hours"] = _dec(_ceil4((CLOCK() - SESSION_T0) / 3600.0))
        e["stages_run"] = list(STAGES_RUN)
        if final and e["end"] is None:
            e["end"] = _iso(CLOCK())
        b = _read_json(BUDGET_FILE, {"gpu_hours": 0.0, "stopped_by_budget": None, "sessions": []})
        for i, s in enumerate(b["sessions"]):
            if s.get("start") == e["start"]:
                b["sessions"][i] = dict(e)
                break
        else:
            b["sessions"].append(dict(e))
        total = sum(_ceil4(s["gpu_hours"]) for s in b["sessions"])
        b["gpu_hours"] = _dec(total)
        Path(BUDGET_FILE).parent.mkdir(parents=True, exist_ok=True)
        _atomic_json(BUDGET_FILE, b)
        v = _read_json(VOICE_FILE, {"runs": {}})
        v["runs"][str(RUN)] = _dec(total)
        _atomic_json(VOICE_FILE, v)


def heartbeat_write():
    _write_budget()


def _set_budget_key(key, value):
    with _BUDGET_LOCK:
        b = _read_json(BUDGET_FILE, {"gpu_hours": 0.0, "stopped_by_budget": None, "sessions": []})
        b[key] = value
        _atomic_json(BUDGET_FILE, b)


def _heartbeat_loop():
    global HEARTBEAT_ERROR
    while not HEARTBEAT_STOP.wait(HEARTBEAT_INTERVAL):
        try:
            heartbeat_write()
        except Exception as exc:    # stored, never silent (R-051)
            HEARTBEAT_ERROR = exc
            return


def _stop_heartbeat():
    global HEARTBEAT
    HEARTBEAT_STOP.set()
    if HEARTBEAT is not None and HEARTBEAT.is_alive():
        HEARTBEAT.join(timeout=60)
    HEARTBEAT = None


def timed(name, fn):
    """Wrap one stage's command: heartbeat check, 9.5-h check, hours line, GPU-time accounting."""
    global CURRENT_STAGE, STAGE_T0
    if HEARTBEAT is None or not HEARTBEAT.is_alive() or HEARTBEAT_ERROR is not None:
        raise RuntimeError(f"the budget heartbeat is not running: {HEARTBEAT_ERROR!r}")
    elapsed = (CLOCK() - SESSION_T0) / 3600.0
    if elapsed >= 9.5:
        raise SessionEnd()
    print(f"session {elapsed:.2f} h; stage {name}")
    print_hours()
    if PLATFORM == "kaggle":
        print("reminder: check Kaggle's weekly GPU quota in Settings before long stages")
    CURRENT_STAGE, STAGE_T0 = name, CLOCK()
    try:
        fn()
    finally:
        if is_gpu_stage(name):
            STAGE_INT[name] = STAGE_INT.get(name, 0) + _ceil4((CLOCK() - STAGE_T0) / 3600.0)
        CURRENT_STAGE = None


# ---- the shell ---------------------------------------------------------------------------------------------------------
def sh(cmd, cwd, timeout=None):
    """Run `bash -c cmd` in its own process group with the venv first on PATH; stream and capture output; rc 124 on timeout."""
    global LAST_PGID
    env = dict(os.environ)
    env["PATH"] = f"{VENV}/bin:" + env.get("PATH", "")
    proc = subprocess.Popen(["bash", "-c", cmd], cwd=str(cwd), env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            text=True, bufsize=1, start_new_session=True)
    LAST_PGID = proc.pid
    lines = deque(maxlen=5000)

    def pump():
        for line in proc.stdout:
            print(line, end="", flush=True)
            lines.append(line)

    reader = threading.Thread(target=pump, daemon=True)
    reader.start()
    try:
        proc.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        os.killpg(proc.pid, signal.SIGTERM)
        try:
            proc.wait(timeout=60)
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid, signal.SIGKILL)
            proc.wait()
        reader.join(timeout=5)
        return 124, "".join(lines)
    reader.join(timeout=30)
    return proc.returncode, "".join(lines)


def _need(rc, cmd, out):
    if rc != 0:
        raise RuntimeError(f"command failed (rc {rc}): {cmd}\n" + "\n".join(out.splitlines()[-50:]))


def _sh_ok(cmd, cwd):
    rc, out = sh(cmd, cwd)
    _need(rc, cmd, out)
    return out


# ---- sessions, guarded cells, state ----------------------------------------------------------------------------------
def make_dirs():
    run, exp = Path(RUNDIR), EXP
    for d in (run / "state", run / "out" / "env", Path(ROOT) / "logs" / exp, Path(ROOT) / "weights", Path(RVC) / "logs", Path(RVC) / "assets"):
        d.mkdir(parents=True, exist_ok=True)
    for link, target in ((Path(RVC) / "logs" / exp, Path(ROOT) / "logs" / exp), (Path(RVC) / "assets" / "weights", Path(ROOT) / "weights")):
        if link.is_symlink():
            link.unlink()
        elif link.is_dir() and not any(link.iterdir()):
            link.rmdir()
        elif link.exists():
            raise RuntimeError(f"{link} exists and is not a symlink")
        link.symlink_to(target)


def write_params():
    want = {"VOICE": VOICE, "RUN": RUN, "PLATFORM": PLATFORM, "DEREVERB": DEREVERB, "EPOCHS": EPOCHS, "SPEAKER_ID": SPEAKER_ID, "GUIDE": GUIDE}
    path = Path(RUNDIR) / "params.json"
    if path.exists():
        have = json.loads(path.read_text(encoding="utf-8"))
        if have != want:
            owner_stop("4e", f"parameters changed within run {RUN}: answer `owner-fixed: params` and wait for a new GATE-G-004.md")
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        _atomic_json(path, want)


def start_session():
    global SESSION_ENTRY, SEQ, STAGE_INT, STAGES_RUN, HEARTBEAT, HEARTBEAT_ERROR
    _stop_heartbeat()
    seqs = [max([s.get("seq", 0) for s in _read_json(p, {"sessions": []})["sessions"]] or [0]) for p in glob.glob(f"{ROOT}/run*/out/budget.json")]
    SEQ = 1 + max(seqs or [0])
    STAGE_INT, STAGES_RUN, HEARTBEAT_ERROR = {}, [], None
    SESSION_ENTRY = {"seq": SEQ, "restored_from": RESTORED_FROM, "prior": _dec(_ceil4(PRIOR_VOICE_GPU_HOURS)), "commit": COMMIT,
                     "start": _iso(SESSION_T0), "end": None, "gpu_hours": 0.0, "session_hours": 0.0, "stage_hours": {},
                     "killed_hours": _dec(_ceil4(KILLED_HOURS)), "stages_run": []}
    _write_budget()
    HEARTBEAT_STOP.clear()
    HEARTBEAT = threading.Thread(target=_heartbeat_loop, daemon=True)
    HEARTBEAT.start()


def close_session_entry():
    """Stop the heartbeat and close this session's entry (used by end_session and by a failed step (4f))."""
    _stop_heartbeat()
    if SESSION_ENTRY is not None:
        _write_budget(final=True)


def _sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _safe_member(m):
    parts = Path(m.name).parts
    return (m.isreg() or m.isdir()) and not os.path.isabs(m.name) and ".." not in parts


def pack_state(dst_dir):
    """Kaggle: write dst_dir/state.tar and state.tar.sha256 (R-055); then drop the untarred copies and voicebank/."""
    work, dst = Path(WORKING), Path(dst_dir)
    names = sorted(p.name for p in work.glob("run*") if p.is_dir())
    names += [n for n in ("logs", "weights", "assets-archive") if (work / n).exists()]
    names += sorted(p.name for p in work.glob("pruned-*"))
    if (work / "budget-voice.json").exists():
        names.append("budget-voice.json")
    tmp = dst / "state.tar.partial"
    with tarfile.open(tmp, "w") as tf:
        for n in names:
            tf.add(work / n, arcname=n)
    os.replace(tmp, dst / "state.tar")
    digest = _sha256_file(dst / "state.tar")
    (dst / "state.tar.sha256").write_text(f"{digest}  state.tar\n", encoding="utf-8")
    print("state.tar written")
    for n in names + ["voicebank"]:
        p = work / n
        if p.is_dir() and not p.is_symlink():
            shutil.rmtree(p, ignore_errors=True)
        elif p.exists() or p.is_symlink():
            p.unlink()
    left = sorted(p.name for p in work.iterdir())
    assert len(left) <= 20, f"{WORKING} holds {len(left)} items (limit 20): {left}"
    return digest


def restore_state(input_root, resume):
    """Kaggle: restore the previous version's state.tar into WORKING (R-016, R-055, R-068); returns its SHA-256 or None."""
    prev = sorted(glob.glob(f"{input_root}/*/state.tar"))
    if len(prev) > 1:
        owner_stop(3, "more than one previous state.tar is attached (" + ", ".join(prev) + "): attach only the newest version's output")
    if resume and not prev:
        owner_stop(3, "RESUME is True but no previous output is attached: attach the previous version's output (Add Input -> Your Work)")
    if not resume and prev:
        owner_stop(3, f"a previous state.tar is attached ({prev[0]}): set RESUME = True")
    if not prev:
        return None
    tar_path = prev[0]
    want = Path(tar_path + ".sha256").read_text(encoding="utf-8").split()[0]
    got = _sha256_file(tar_path)
    if want != got:
        owner_stop(3, f"{tar_path} does not match its state.tar.sha256 ({got} != {want}): attach the version's output again")
    work = Path(WORKING)
    work.mkdir(parents=True, exist_ok=True)
    shutil.copy2(tar_path, work / "state.tar")                    # carried even if a later cell fails (R-088)
    shutil.copy2(tar_path + ".sha256", work / "state.tar.sha256")
    with tarfile.open(tar_path) as tf:
        members = tf.getmembers()
        bad = [m.name for m in members if not _safe_member(m)]
        if bad:
            raise RuntimeError(f"unsafe members in state.tar: {bad[:3]}")
        norm = lambda name: name[2:] if name.startswith("./") else name
        marker = f"pruned-{PRUNE}"
        skip = bool(PRUNE) and not any(norm(m.name) == marker for m in members)
        for m in members:
            rel = norm(m.name)
            if skip and (rel == f"logs/{PRUNE}" or rel.startswith(f"logs/{PRUNE}/") or re.fullmatch(rf"weights/{re.escape(PRUNE)}_e\d+_s\d+\.pth", rel)):
                continue
            try:
                tf.extract(m, work, filter="data")
            except TypeError:                                      # Python without extraction filters
                tf.extract(m, work)
    if skip:
        (work / marker).write_text("training of this run restarts from the pretrained model\n", encoding="utf-8")
        print(f"prune: logs/{PRUNE} and its weight snapshots were not restored")
    return got


def end_session():
    """Cell (17)'s finally body, identical for the STOP and normal branches."""
    if SESSION_ENTRY is None:
        print("no session was started" + (f"; {STOP_REASON}" if STOP_REASON else ""))
        return
    close_session_entry()
    print_hours()
    digest = pack_state(WORKING) if PLATFORM == "kaggle" else None
    if STOP_REASON:
        print(STOP_REASON)
    if PLATFORM == "kaggle":
        print(f"seq {SEQ} state.tar {digest}")


def guarded(cell, body):
    """Cells (5)-(16): nothing raises; every stop becomes STOP_REASON (R-069, R-087)."""
    global STOP, STOP_REASON
    if STOP:
        print("skipped - start a new session")
        return
    try:
        body()
    except SessionEnd:
        STOP, STOP_REASON = True, "start a new session"
    except BudgetStop:
        STOP, STOP_REASON = True, "budget: no checkpoint"
    except OwnerAction as exc:
        STOP, STOP_REASON = True, f"owner: {exc.cell} {exc.message}"
    except Exception as exc:
        traceback.print_exc()
        STOP, STOP_REASON = True, f"failed: {cell} {(str(exc).splitlines() or [type(exc).__name__])[0]}"


def run_cell(cell):
    by_name = {s.name: s for s in make_stages(RUNDIR, RVC, sh)}
    ran = _pipeline().run_stages([by_name[n] for n in CELL_STAGES[cell]], Path(RUNDIR) / "state")
    print("stages run:", ran)
    STAGES_RUN.extend(ran)
    _write_budget()
    return ran


# ---- archived downloads (D-035 step 5, R-042) ----------------------------------------------------------------------------
def archived(group, base, paths, download):
    """Take `paths` (relative to `base`) from <root>/assets-archive/<group> when SHA256SUMS matches, else download and archive."""
    arch = Path(ROOT) / "assets-archive"
    gdir, sums = arch / group, arch / "SHA256SUMS"
    lines = sums.read_text(encoding="utf-8").splitlines() if sums.exists() else []
    mine = [ln for ln in lines if ln.split(None, 1)[1:] and ln.split(None, 1)[1].startswith(group + "/")]
    Path(base).mkdir(parents=True, exist_ok=True)
    if gdir.exists() and mine:
        (arch / f".{group}.sums").write_text("\n".join(mine) + "\n", encoding="utf-8")
        rc, _ = sh(f"sha256sum -c --quiet .{group}.sums", arch)
        if rc == 0:
            _sh_ok(f"cp -a {shlex.quote(str(gdir))}/. {shlex.quote(str(base))}/", "/")
            return
        shutil.rmtree(gdir, ignore_errors=True)               # mismatch: delete and download again
    download()
    new = []
    for rel in paths:
        src = Path(base) / rel
        dst = gdir / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        if src.is_dir():
            shutil.copytree(src, dst, dirs_exist_ok=True)
        else:
            shutil.copy2(src, dst)
    for f in sorted(p for p in gdir.rglob("*") if p.is_file()):
        new.append(f"{_sha256_file(f)}  {group}/{f.relative_to(gdir).as_posix()}")
    keep = [ln for ln in lines if not (ln.split(None, 1)[1:] and ln.split(None, 1)[1].startswith(group + "/"))]
    arch.mkdir(parents=True, exist_ok=True)
    sums.write_text("\n".join(keep + new) + "\n", encoding="utf-8")


# ---- small scripts run inside the venv through sh -------------------------------------------------------------------------
_WAV_PY = """
import sys, pathlib, soundfile as sf
src, dst = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2]); dst.mkdir(exist_ok=True)
files = sorted(p for p in src.iterdir() if p.suffix.lower() in (".wav", ".flac"))
if not files: sys.exit("no .wav or .flac recordings in %s" % src)
stems = [p.stem for p in files]
if len(set(stems)) != len(stems): sys.exit("two recordings share a name: " + ", ".join(sorted(s for s in set(stems) if stems.count(s) > 1)))
for p in files:
    data, rate = sf.read(str(p)); sf.write(str(dst / (p.stem + ".wav")), data, rate, subtype="PCM_24")
print("wrote %d WAV files to %s" % (len(files), dst))
"""
_COPY_PY = """
import json, shutil, sys, pathlib, soundfile as sf
split = json.load(open("split.json")); secs = {}
for part in ("train", "heldout"):
    shutil.rmtree(part, ignore_errors=True); pathlib.Path(part).mkdir(); secs[part] = 0.0
    for name in split[part]:
        shutil.copy("raw_wav/" + name, part + "/" + name); secs[part] += sf.info("raw_wav/" + name).duration
print("train %.1f s in %d files, heldout %.1f s in %d files" % (secs["train"], len(split["train"]), secs["heldout"], len(split["heldout"])))
sys.exit(3 if (not split["heldout"] or secs["heldout"] < 30.0 or secs["train"] < 600.0) else 0)
"""
_LOAD_PY = """
import sys, torch
c = torch.load(sys.argv[1], map_location="cpu")
print("iteration=%s" % (c.get("iteration", 0) if isinstance(c, dict) else 0))
"""
_PARITY_PY = """
import sys
from pathlib import Path
from singvst_train import export_rvc
d = export_rvc.parity(Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]))
print("parity max abs difference", d)
sys.exit(0 if d <= 1e-3 else 5)
"""
_TRAINING_PY = """
import hashlib, json, pathlib, sys, soundfile as sf
exp, epochs, weights, commit = sys.argv[1], int(sys.argv[2]), sys.argv[3], sys.argv[4]
stopped = json.load(open("out/budget.json")).get("stopped_by_budget")
minutes = sum(sf.info(str(p)).duration for p in pathlib.Path("raw_wav").glob("*.wav")) / 60.0
commits = json.load(open("state/commits.json")) if pathlib.Path("state/commits.json").exists() else {}
json.dump({"voice_name": exp, "epochs_requested": epochs, "epochs_trained": stopped if stopped is not None else epochs,
           "stopped_by_budget": stopped is not None, "raw_minutes": round(minutes, 3),
           "weights_sha256": hashlib.sha256(open(weights, "rb").read()).hexdigest(),
           "env_files": sorted(p.name for p in pathlib.Path("out/env").glob("*")), "stage_commits": commits, "commit": commit},
          open("out/training.json", "w"), indent=1, sort_keys=True)
"""
_CEILING_PY = """
import json, pathlib, numpy as np
from resemblyzer import VoiceEncoder, preprocess_wav
enc = VoiceEncoder("cpu")
emb = lambda p: np.asarray(enc.embed_utterance(preprocess_wav(str(p))), dtype=np.float64)
cos = lambda a, b: float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))
train = np.mean([emb(p) for p in sorted(pathlib.Path("train").glob("*.wav"))], axis=0)
held = [emb(p) for p in sorted(pathlib.Path("heldout").glob("*.wav"))]
json.dump({"heldout_vs_train": float(np.mean([cos(h, train) for h in held]))}, open("out/eval/ceiling.json", "w"), indent=1)
"""


def _depth_from_dsconfig(voicebank):
    """depth = min(0.4, max_depth) from dsacoustic/dsconfig.yaml (divided by 1000 when > 1), 0.4 when the key is absent (C-034)."""
    try:
        text = (Path(voicebank) / "dsacoustic" / "dsconfig.yaml").read_text(encoding="utf-8")
        m = re.search(r"^max_depth\s*:\s*([0-9.]+)", text, re.M)
        if m:
            value = float(m.group(1))
            return min(0.4, value / 1000.0 if value > 1 else value)
    except OSError:
        pass
    return 0.4


# ---- the stage table (D-035) ---------------------------------------------------------------------------------------------
def make_stages(run, rvc, sh_unused=None):
    """The eleven pipeline.Stage objects; every stage's run is timed() around a body that calls the global sh (looked up at call time)."""
    from singvst_train.pipeline import Stage
    run, rvc, exp, loc, root = Path(run), Path(rvc), EXP, Path(LOCAL), Path(ROOT)
    q = shlex.quote
    params = run / "params.json"
    logs = rvc / "logs" / exp
    weights = rvc / "assets" / "weights" / f"{exp}.pth"

    def b_split():
        _sh_ok(f"python -c {q(_WAV_PY)} {q(RAW)} raw_wav", run)
        _sh_ok("python -m singvst_train.cli split --files-dir raw_wav --seed 0 --out split.json", run)
        rc, out = sh(f"python -c {q(_COPY_PY)}", run)
        if rc == 3:
            raise OwnerAction(7, "too little audio: supply at least 10 recordings (held-out at least 30 s, training at least 10 min)")
        _need(rc, "split copy", out)

    def b_prepare():
        extra = " --dereverb" if DEREVERB else ""
        _sh_ok(f"python -m singvst_train.cli prepare --in train --out prepared --lockfile out/env/{SESSION}.freeze.txt{extra}", run)

    def b_preprocess():
        _sh_ok(f"python train/preprocess.py {run}/prepared/segments 48000 {os.cpu_count() or 2} {logs} False 3.0", rvc)

    def b_f0():
        _sh_ok(f"python train/dataset/extract_f0.py cuda 1 0 0 {logs} False", rvc)

    def b_features():
        _sh_ok(f"python train/dataset/extract_hubert_feature.py cuda 1 0 0 {logs} v2 False", rvc)

    def b_files():
        _sh_ok(f"python -m singvst_train.cli rvc-files --exp-dir {logs} --rvc-root {rvc} --speaker-id {SPEAKER_ID}", run)

    def ckpt_iteration(path):
        rc, out = sh(f"python -c {q(_LOAD_PY)} {q(str(path))}", run)
        if rc != 0:
            return None
        m = re.search(r"iteration=(\d+)", out)
        return int(m.group(1)) if m else 0

    def budget_copy():
        """DR-13: the newest weight snapshot that loads becomes <exp>.pth; none -> BudgetStop (R-086)."""
        snaps = sorted(((int(m.group(1)), p) for p in weights.parent.glob(f"{exp}_e*_s*.pth")
                        if (m := re.fullmatch(rf"{re.escape(exp)}_e(\d+)_s\d+\.pth", p.name))), key=lambda t: t[0], reverse=True)
        for epoch, path in snaps:
            if ckpt_iteration(path) is not None:
                shutil.copy2(path, weights)
                _set_budget_key("stopped_by_budget", epoch)
                print(f"budget: copied {path.name} as {weights.name} (epoch {epoch})")
                return
        raise BudgetStop()

    def after_timeout():
        gone = False
        for _ in range(2):
            try:
                os.killpg(LAST_PGID, 0)
            except ProcessLookupError:
                gone = True
                break
            os.killpg(LAST_PGID, signal.SIGKILL)
            time.sleep(5)
        if not gone:
            try:
                os.killpg(LAST_PGID, 0)
            except ProcessLookupError:
                gone = True
        sh("nvidia-smi --query-compute-apps=pid,used_memory --format=csv", "/")     # information only; PIDs are never killed
        if not gone:
            raise RuntimeError("the training process group survived SIGKILL")

    def b_train():
        global STOP
        gp, dp = logs / "G_2333333.pth", logs / "D_2333333.pth"
        marker = logs / "RESTART_DETECTED"
        e0 = None
        if gp.exists() or dp.exists():                                              # checkpoint guard (R-035, R-057)
            for p in (gp, dp):
                if not p.exists():
                    continue
                it = ckpt_iteration(p)
                if it is None:
                    bak = Path(str(p) + ".bak")
                    if bak.exists() and ckpt_iteration(bak) is not None:
                        shutil.copy2(bak, p)
                        it = ckpt_iteration(p)
                    elif PLATFORM == "kaggle" and (Path(WORKING) / f"pruned-{exp}").exists():
                        raise OwnerAction(11, "checkpoint unreadable again: answer `switch-platform: colab`")
                    elif PLATFORM == "kaggle":
                        raise OwnerAction(11, f"checkpoint unreadable; answer `prune: {exp}`")
                    else:
                        raise OwnerAction(11, f"checkpoint unreadable; delete logs/{exp} to restart this run")
                if p == gp:
                    e0 = it
            if not marker.exists():
                for p in (gp, dp):
                    if p.exists():
                        shutil.copy2(p, str(p) + ".bak")
        elapsed = (CLOCK() - SESSION_T0) / 3600.0
        t_session = 10.0 - elapsed - 0.5
        t_budget = BUDGET_HOURS - 1.0 - _hours()[1] / 10 ** 4
        budget_binds = t_budget < t_session
        t = min(t_session, t_budget)
        if t <= 0:
            if budget_binds:
                budget_copy()
                return
            STOP = True
            raise SessionEnd()
        log = logs / "train.log"
        log_pos = log.stat().st_size if log.exists() else 0
        info = _sh_ok(f"python -m singvst_train.cli rvc-train-command --exp-name {q(exp)} --batch-size {BATCH_SIZE} --epochs {EPOCHS} "
                      "--save-every 10 --python python", run)
        cmd = " ".join(q(a) for a in json.loads(info.strip().splitlines()[-1]))
        rc, out = sh(cmd, rvc, timeout=t * 3600.0)
        if rc == 124:
            after_timeout()
            if budget_binds:
                budget_copy()
                return
            STOP = True
            raise SessionEnd()
        _need(rc, cmd, out)
        if e0 is not None:                                                          # restart detection (R-076, R-092)
            fresh = log.read_bytes()[log_pos:].decode("utf-8", errors="replace") if log.exists() else ""
            it = ckpt_iteration(gp)
            if it is None or it < e0 or "已加载生成器预训练模型" in fresh or "Loaded generator pretrained model" in fresh:
                for p in (gp, dp):
                    bak = Path(str(p) + ".bak")
                    if bak.exists():
                        shutil.copy2(bak, p)
                marker.write_text("training restarted from the pretrained model\n", encoding="utf-8")
                raise RuntimeError("training restarted from the pretrained model; checkpoints restored from .bak (RESTART_DETECTED written)")
            if marker.exists():
                for p in (gp, dp):
                    if p.exists():
                        shutil.copy2(p, str(p) + ".bak")
                marker.unlink()
        if not weights.exists():
            raise RuntimeError(f"train.py exited 0 but {weights.name} was not written")

    def b_export():
        _sh_ok(f"python -m singvst_train.cli export --rvc-root {rvc} --exp-name {exp} --out-dir out/conv", run)
        _sh_ok(f"python -c {q(_PARITY_PY)} {q(str(rvc))} {q(str(weights))} out/conv/rvc_synth.onnx", run)

    def b_render_bin():
        b = f"{LOCAL}/build-render/cli"
        _sh_ok(f"mkdir -p {LOCAL}/bin && cp {b}/singvst-render {b}/cmudict.dict {b}/onnxruntime-LICENSE.txt {b}/libonnxruntime.so* {LOCAL}/bin/", "/")

    def b_pack():
        if GUIDE != "tiger":
            raise OwnerAction(14, f"GUIDE = {GUIDE!r}: only 'tiger' is wired into this notebook; another voicebank needs a planning amendment (G-005)")
        v = root / "voicebank" / "tiger"
        depth = _depth_from_dsconfig(v)
        cmd = (f"python -m singvst_train.cli pack --out out/voice --name {q(exp)} --consent {q(ATTESTATION)} --guide-licence {q(TIGER_LICENCE)} "
               f"--acoustic {q(str(v / 'dsacoustic/tiger_acou.onnx'))} --vocoder {q(str(v / 'dsvocoder/tgm_hifigan.onnx'))} "
               f"--phonemes {q(str(v / 'dsacoustic/phonemes.txt'))} --speaker {q(str(v / 'dsacoustic/tiger_fresh.emb'))} "
               f"--synth out/conv/rvc_synth.onnx --content out/conv/content.onnx --language en --steps 20 --depth {depth} "
               f"--converter-sample-rate 48000 --speaker-id {SPEAKER_ID}")
        _sh_ok(cmd, run)
        _sh_ok(f"python -c {q(_TRAINING_PY)} {q(exp)} {EPOCHS} {q(str(weights))} {COMMIT}", run)

    def b_evaluate():
        _sh_ok(f"python -m singvst_train.cli evaluate --voice out/voice --heldout heldout --phrases {SINGVST}/eval/phrases "
               f"--render-bin {LOCAL}/bin/singvst-render --out out/eval --thresholds {SINGVST}/eval/thresholds.json "
               f"--lockfile out/env/{SESSION}.freeze.txt", run)
        _sh_ok(f"python -c {q(_CEILING_PY)}", run)

    def stage(name, inputs, outputs, body):
        def go():
            timed(name, body)
            commits = _read_json(run / "state" / "commits.json", {})
            commits[name] = COMMIT
            _atomic_json(run / "state" / "commits.json", commits)
        return Stage(name, tuple(inputs) + (params,), tuple(outputs), go)

    return [
        stage("split", [Path(RAW)], [run / "raw_wav", run / "split.json", run / "train", run / "heldout"], b_split),
        stage("prepare", [run / "train"], [run / "prepared"], b_prepare),
        stage("rvc-preprocess", [run / "prepared" / "segments"], [logs / "0_gt_wavs", logs / "1_16k_wavs"], b_preprocess),
        stage("rvc-f0", [logs / "1_16k_wavs"], [logs / "2a_f0", logs / "2b-f0nsf"], b_f0),
        stage("rvc-features", [logs / "1_16k_wavs"], [logs / "3_feature768"], b_features),
        stage("rvc-files", [logs / "0_gt_wavs", logs / "3_feature768", logs / "2a_f0", logs / "2b-f0nsf"],
              [logs / "filelist.txt", logs / "config.json"], b_files),
        stage("train", [logs / "filelist.txt", logs / "config.json"], [weights], b_train),
        stage("export", [weights], [run / "out" / "conv"], b_export),
        stage("render-bin", [loc / "build-render" / "cli" / "singvst-render"], [loc / "bin"], b_render_bin),
        stage("pack", [run / "out" / "conv", root / "voicebank"], [run / "out" / "voice", run / "out" / "training.json"], b_pack),
        stage("evaluate", [run / "out" / "voice", run / "heldout", loc / "bin"], [run / "out" / "eval"], b_evaluate),
    ]


# ---- Kaggle: restore the previous version (cell (3), R-016) ------------------------------------------------------------------
if PLATFORM == "kaggle":
    RESTORED_FROM = restore_state(f"{PATH_ROOTS['kaggle']}/input", RESUME)
else:
    RESTORED_FROM = None
print(f"{PLATFORM} notebook; run {RUN} of voice {VOICE}; session {SESSION}; RESTORED_FROM {RESTORED_FROM}")
