"""Dry run of the training notebooks (plan S-016, D-035; R-013, R-016, R-079).

Usage: ../venv-lock/bin/python -I tools/notebook_dryrun.py        (exits 0 when every scenario of both notebooks passes)

For each notebook this loads the cells with nbformat and execs cell (3) (the cell that defines `make_stages`) with PATH_ROOTS mapped
into a temporary directory, the globals of cells (2) and (2a) preset, a fake clock and a fake `sh`. The fake `sh` runs every stage
through the notebook's own `timed`: on the first main command of a stage it advances the clock by the scenario's hours and creates
the stage's declared outputs. Cells (4), (5), (6), (10a), (14)'s download, (16) and (17)'s tar are not executed (they need a GPU and
the network); everything else - guarded, run_cell, pack_state, restore_state, end_session, the heartbeat and the budget files - is
the notebook's own code.
"""
import contextlib
import glob
import io
import json
import re
import sys
import tarfile
import tempfile
from pathlib import Path

import nbformat

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python"))

GPU = {"rvc-f0": 1.0, "rvc-features": 1.0, "train": 1.0, "export": 1.0, "evaluate": 1.0}
ALL_STAGES = ["split", "prepare", "rvc-preprocess", "rvc-f0", "rvc-features", "rvc-files", "train", "export", "render-bin", "pack", "evaluate"]
CELLS = [7, 8, 9, 10, 11, 12, 13, 14, 15]
HOURS_LINE = re.compile(r"^hours: platform (\d+\.\d{4}) voice (\d+\.\d{4})$")
failures = []


def check(cond, what):
    print(("  ok   " if cond else "  FAIL ") + what)
    if not cond:
        failures.append(what)


class Env:
    """One notebook in one temporary directory tree, driven session by session."""

    def __init__(self, notebook, **params):
        nb = nbformat.read(ROOT / "notebooks" / notebook, as_version=4)
        self.cells = [c.source for c in nb.cells if c.cell_type == "code"]
        self.cell3 = next(c for c in self.cells if "def make_stages" in c)
        self.platform = "colab" if "colab" in notebook else "kaggle"
        self.tmp = Path(tempfile.mkdtemp(prefix="nbdry-"))
        self.clock = [1_700_000_000.0]
        self.params = dict(PRIOR_VOICE_GPU_HOURS=0.0, KILLED_HOURS=0.0, PRUNE="", RESUME=False, PLATFORM_EXPECTED=self.platform, EPOCHS=10)
        self.params.update(params)
        self.ns = {}
        self.hours = dict(GPU) if params.pop("gpu_hours", False) else {}
        self.script = {}              # stage name -> exception instance or class to raise on its first main command
        self.on_main = {}             # stage name -> callable run after the clock advance
        self.invocation = 0
        self.created = False
        self.load_ok = True
        self.out = io.StringIO()

    # ---- paths of the current root
    def path(self, key):
        return Path(self.ns[key])

    # ---- a (new) session ----------------------------------------------------------------------------------------------
    def boot(self, root=None, restore_from=None, start=True, **override):
        """Exec cell (3) for a new session, then do what cell (4e) does. root=None keeps the current tree; a fresh Path starts a new one."""
        if root is not None:
            self.tmp = Path(tempfile.mkdtemp(prefix="nbdry-"))
            self.ns.pop("HEARTBEAT", None)
        params = dict(self.params, **override)
        roots = {"content": str(self.tmp / "content"), "kaggle": str(self.tmp / "kaggle"), "tmp": str(self.tmp / "tmp")}
        self.clock[0] += 60.0
        ns = self.ns
        ns.update(PATH_ROOTS=roots, CLOCK=lambda: self.clock[0], HEARTBEAT_INTERVAL=10 ** 9, CONSENT_CONFIRMED=True, ATTESTATION="dry",
                  VOICE="dry", RUN=1, EXPECTED_COMMIT="0" * 40, DEREVERB=False, SPEAKER_ID=0, GUIDE="tiger", **params)
        ns["SESSION_T0"] = self.clock[0]
        ns["STOP"], ns["STOP_REASON"] = False, ""
        if restore_from is not None:
            prev = Path(roots["kaggle"]) / "input" / "prev"
            prev.mkdir(parents=True)
            for name in ("state.tar", "state.tar.sha256"):
                (prev / name).write_bytes((Path(restore_from) / name).read_bytes())
        with contextlib.redirect_stdout(self.out):
            exec(compile(self.cell3, "cell3", "exec"), ns)
        self._install_fakes()
        self._pre_create()
        if start:
            with contextlib.redirect_stdout(self.out):
                ns["make_dirs"]()
                ns["write_params"]()
                ns["start_session"]()

    def _pre_create(self):
        raw = self.path("RAW")
        raw.mkdir(parents=True, exist_ok=True)
        (raw / "a.wav").write_bytes(b"RIFF-dry-a")
        (raw / "b.wav").write_bytes(b"RIFF-dry-b")
        vb = Path(self.ns["ROOT"]) / "voicebank"
        vb.mkdir(parents=True, exist_ok=True)
        (vb / "voice.bin").write_bytes(b"voicebank-dry")
        binary = Path(self.ns["LOCAL"]) / "build-render" / "cli" / "singvst-render"
        binary.parent.mkdir(parents=True, exist_ok=True)
        binary.write_bytes(b"singvst-render-dry")

    # ---- the fakes --------------------------------------------------------------------------------------------------
    def _install_fakes(self):
        ns = self.ns
        original_timed = ns["timed"]

        def timed(name, fn):
            self.invocation += 1
            self.created = False
            return original_timed(name, fn)

        def sh(cmd, cwd, timeout=None):
            stage = ns["CURRENT_STAGE"]
            if "torch.load" in cmd:
                return (0 if self.load_ok else 1), "iteration=10\n"
            if "rvc-train-command" in cmd:
                return 0, json.dumps(["python", "train/train.py", "-e", ns["EXP"]]) + "\n"
            if stage is None or "nvidia-smi" in cmd:
                return 0, ""
            if not self.created:
                self.created = True
                self.clock[0] += self.hours.get(stage, 0.0) * 3600.0
                hook = self.on_main.get(stage)
                if hook:
                    hook()
                failure = self.script.get(stage)
                if failure is not None:
                    raise failure
                self._create_outputs(stage)
            return 0, ""

        ns["timed"], ns["sh"] = timed, sh

    def _create_outputs(self, stage):
        ns = self.ns
        by_name = {s.name: s for s in ns["make_stages"](ns["RUNDIR"], ns["RVC"], ns["sh"])}
        for out in by_name[stage].outputs:
            self._make(out, f"{stage}-{self.invocation}")
        for other in by_name.values():                 # inputs of later stages that sit below a directory just created
            for inp in other.inputs:
                if not inp.exists() and any(parent in by_name[stage].outputs for parent in inp.parents):
                    self._make(inp, f"{stage}-{self.invocation}")
        if stage == "train":
            (Path(ns["RVC"]) / "logs" / ns["EXP"] / "fake-train-state.bin").write_bytes(f"train-{self.invocation}".encode())

    @staticmethod
    def _make(path, tag):
        if path.suffix == "":
            path.mkdir(parents=True, exist_ok=True)
            (path / "fake.bin").write_bytes(tag.encode())
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(tag.encode())

    # ---- helpers for scenarios ----------------------------------------------------------------------------------------
    def cell(self, n):
        with contextlib.redirect_stdout(self.out):
            self.ns["guarded"](n, lambda: self.ns["run_cell"](n))

    def run_cells(self, cells=CELLS):
        for n in cells:
            self.cell(n)

    def end(self):
        with contextlib.redirect_stdout(self.out):
            self.ns["end_session"]()

    def budget(self):
        return json.loads(Path(self.ns["BUDGET_FILE"]).read_text())

    def stages_run(self):
        return list(self.ns["STAGES_RUN"])

    def hours_lines(self):
        return [ln for ln in self.out.getvalue().splitlines() if ln.startswith("hours:")]

    def stop_reason(self):
        return self.ns["STOP_REASON"]


def extract_state(env, into):
    """The state.tar the session left in WORKING, copied to `into` (a stand-in for the next version's attached input)."""
    into = Path(into)
    into.mkdir(parents=True, exist_ok=True)
    for name in ("state.tar", "state.tar.sha256"):
        (into / name).write_bytes((Path(env.ns["WORKING"]) / name).read_bytes())
    return into


def tar_names(path):
    with tarfile.open(path) as tf:
        return [m.name for m in tf.getmembers()]


# ======================================================================================================================
def s1_full_session(nb):
    print(f"(1) a full session runs every stage [{nb}]")
    e = Env(nb, gpu_hours=True)
    e.boot()
    e.run_cells()
    check(e.stages_run() == ALL_STAGES, f"stages run in order: {e.stages_run()}")
    check(not e.ns["STOP"], "no stop")
    commits = json.loads((Path(e.ns["RUNDIR"]) / "state" / "commits.json").read_text())
    check(sorted(commits) == sorted(ALL_STAGES), "commits.json records every stage")
    e.end()


def s2_restore(nb):
    print(f"(2) end_session, then restore into a fresh root: only render-bin and evaluate run [{nb}]")
    e = Env(nb)
    e.boot()
    e.run_cells()
    e.end()
    keep = extract_state(e, e.tmp / "keep")
    e.boot(root=True, restore_from=keep, RESUME=True)
    e.run_cells()
    check(e.stages_run() == ["render-bin", "evaluate"], f"stages run after the restore: {e.stages_run()}")
    check(e.ns["RESTORED_FROM"] is not None, "RESTORED_FROM holds the restored tar's hash")
    e.end()


def s3_params_edit(nb):
    print(f"(3) editing params.json makes every stage run [{nb}]")
    e = Env(nb)
    e.boot()
    e.run_cells()
    p = Path(e.ns["RUNDIR"]) / "params.json"
    data = json.loads(p.read_text())
    data["EPOCHS"] = 99
    p.write_text(json.dumps(data))
    before = len(e.stages_run())
    e.run_cells()
    check(e.stages_run()[before:] == ALL_STAGES, f"second pass reran: {e.stages_run()[before:]}")
    e.end()


def s4_session_end(nb):
    print(f"(4) a train SessionEnd stops the session; the next one resumes at train [{nb}]")
    from singvst_train.pipeline import Stage  # noqa: F401  (the import path must work)
    e = Env(nb)
    e.boot()
    SessionEnd = e.ns["SessionEnd"]
    e.script["train"] = SessionEnd()
    e.run_cells()
    check(e.ns["STOP"] and e.stop_reason() == "start a new session", f"STOP set: {e.stop_reason()!r}")
    first = e.stages_run()
    check(first[-1] != "train" and "train" not in first, f"train left no marker; stages run: {first}")
    if nb.endswith("kaggle.ipynb"):
        e.end()
        keep = extract_state(e, e.tmp / "keep")
        check("state.tar" in [p.name for p in Path(e.ns["WORKING"]).iterdir()], "state.tar written by end_session")
        e.boot(root=True, restore_from=keep, RESUME=True)
        entry = [s for s in e.budget()["sessions"]][0]
        check(entry["end"] is not None and entry["seq"] == 1, f"first session entry has end and seq: {entry['seq']}")
    else:
        e.end()
        e.boot()                                     # Colab: same root, markers on Drive
    e.script.clear()
    e.run_cells()
    check(e.stages_run()[0] == "train" and "rvc-f0" not in e.stages_run(), f"resumed at train: {e.stages_run()}")


def s5_failures(nb):
    print(f"(5) failures and owner stops never escape guarded [{nb}]")
    e = Env(nb)
    e.boot()
    e.script["rvc-features"] = RuntimeError("boom")
    e.run_cells()
    check(e.ns["STOP"] and e.stop_reason().startswith("failed: 9 "), f"RuntimeError -> {e.stop_reason()!r}")
    e.end()
    if nb.endswith("kaggle.ipynb"):
        check((Path(e.ns["WORKING"]) / "state.tar").exists(), "Kaggle: state.tar written after a failure")
        rec = tar_names(Path(e.ns["WORKING"]) / "state.tar")
        check(any(n.endswith("budget.json") for n in rec), "state.tar holds the budget files")
    else:
        check(e.budget()["sessions"][-1]["end"] is not None, "Colab: budget.json has the session's end")
    o = Env(nb)
    o.boot()
    o.script["rvc-f0"] = o.ns["OwnerAction"](9, "fix the thing")
    o.run_cells()
    check(o.stop_reason().startswith("owner: 9 "), f"OwnerAction -> {o.stop_reason()!r}")
    o.end()


def s6_resume_rules(nb):
    print(f"(6) RESUME rules raise the D-035 messages [{nb}]")
    e = Env(nb)
    e.boot()
    e.run_cells()
    e.end()
    keep = extract_state(e, e.tmp / "keep")
    for label, resume, restore, text in (("RESUME with no state.tar", True, None, "attach the previous version's output"),
                                         ("no RESUME with a state.tar", False, keep, "set RESUME = True")):
        f = Env(nb)
        raised = None
        try:
            f.boot(root=True, restore_from=restore, RESUME=resume, start=False)
        except f.ns.get("OwnerAction", Exception) as exc:
            raised = str(exc)
        except Exception as exc:                      # OwnerAction is defined by the exec that raised it
            raised = str(exc)
        check(raised is not None and text in raised, f"{label}: {raised!r}")
        check(any(ln.startswith("owner: 3 ") for ln in f.out.getvalue().splitlines()), f"{label}: prints an `owner: 3 ` line")


def s7_accounting(nb):
    print(f"(7) GPU-hour accounting [{nb}]")
    kaggle = nb.endswith("kaggle.ipynb")
    e = Env(nb, gpu_hours=True, PRIOR_VOICE_GPU_HOURS=2.5, KILLED_HOURS=0.5 if kaggle else 0.0)
    e.boot()
    seen = []
    e.on_main["train"] = lambda: (e.ns["heartbeat_write"](), seen.append(e.budget()["sessions"][-1]["stage_hours"].get("train")))
    e.run_cells()
    b = e.budget()
    entry = b["sessions"][-1]
    check(entry["gpu_hours"] == 5.0 == round(sum(entry["stage_hours"].values()), 4), f"gpu_hours {entry['gpu_hours']} = sum of stage_hours {entry['stage_hours']}")
    voice = json.loads(Path(e.ns["VOICE_FILE"]).read_text())
    check(voice["runs"]["1"] == 5.0, f"budget-voice.json runs[1] = {voice['runs']['1']}")
    check(entry["prior"] == 2.5 and entry["killed_hours"] == (0.5 if kaggle else 0.0), f"prior {entry['prior']} killed_hours {entry['killed_hours']}")
    lines = e.hours_lines()
    extra = 3.0 if kaggle else 2.5
    ok = bool(lines) and all(HOURS_LINE.match(ln) and abs(float(HOURS_LINE.match(ln).group(2)) - float(HOURS_LINE.match(ln).group(1)) - extra) < 1e-9 for ln in lines)
    check(ok, f"{len(lines)} hours lines match and voice = platform + {extra}")
    check(seen == [1.0], f"a heartbeat during the train stage records its elapsed time: {seen}")
    # a session that never reached end_session is still summed with its heartbeat hours
    e.boot(PRIOR_VOICE_GPU_HOURS=2.5)
    with contextlib.redirect_stdout(e.out):
        e.ns["heartbeat_write"]()
    b2 = e.budget()
    check(len(b2["sessions"]) == 2 and b2["sessions"][0]["end"] is None and b2["gpu_hours"] == 5.0, f"unended session still counted: gpu_hours {b2['gpu_hours']}")
    e.end()


def s8_budget(nb):
    print(f"(8) budget stop in the train stage [{nb}]")
    e = Env(nb, PRIOR_VOICE_GPU_HOURS=19.0)
    e.boot()
    weights = Path(e.ns["RVC"]) / "assets" / "weights"
    (weights / f"{e.ns['EXP']}_e10_s100.pth").write_bytes(b"snapshot")
    e.run_cells(CELLS[:5])
    check(not e.ns["STOP"], f"stage completed from the snapshot (STOP_REASON {e.stop_reason()!r})")
    check(e.budget()["stopped_by_budget"] == 10, f"stopped_by_budget = {e.budget()['stopped_by_budget']}")
    check((weights / f"{e.ns['EXP']}.pth").exists(), "<exp>.pth was copied from the snapshot")
    e.end()
    n = Env(nb, PRIOR_VOICE_GPU_HOURS=19.0)
    n.boot()
    n.run_cells(CELLS[:5])
    check(n.stop_reason() == "budget: no checkpoint", f"no snapshot -> {n.stop_reason()!r}")
    n.end()


def s9_prune(nb):
    print(f"(9) prune skips logs/<exp> once and keeps it afterwards [{nb}]")
    e = Env(nb)
    e.boot()
    e.run_cells(CELLS[:5])
    e.end()
    exp = e.ns["EXP"]
    keep = extract_state(e, e.tmp / "keep")
    b = Env(nb)
    b.boot(root=True, restore_from=keep, RESUME=True, PRUNE=exp, start=False)
    work = Path(b.ns["WORKING"])
    check(not (work / "logs" / exp).exists(), "logs/<exp> not restored")
    check((work / f"pruned-{exp}").exists(), "pruned-<exp> marker written")
    with contextlib.redirect_stdout(b.out):
        b.ns["make_dirs"](); b.ns["write_params"](); b.ns["start_session"]()
    b.run_cells(CELLS[:5])
    check("rvc-preprocess" in b.stages_run() and "train" in b.stages_run(), f"restarted training: {b.stages_run()}")
    b.end()
    keep2 = extract_state(b, b.tmp / "keep")
    c = Env(nb)
    c.boot(root=True, restore_from=keep2, RESUME=True, PRUNE=exp, start=False)
    check((Path(c.ns["WORKING"]) / "logs" / exp / "fake-train-state.bin").exists(), "second restore keeps logs/<exp>")


def s10_owner_stops(nb):
    print(f"(10) owner stops in cells (3) and (4e) [{nb}]")
    e = Env(nb)
    raised = False
    try:
        e.boot(root=True, PLATFORM_EXPECTED="the-other-one", start=False)
    except Exception as exc:
        raised = type(exc).__name__ == "OwnerAction"
    check(raised and any(ln.startswith("owner: 3 ") for ln in e.out.getvalue().splitlines()), "PLATFORM_EXPECTED mismatch -> OwnerAction and `owner: 3 `")
    f = Env(nb)
    f.boot()
    f.ns["EPOCHS"] = 20
    raised = False
    try:
        with contextlib.redirect_stdout(f.out):
            f.ns["write_params"]()
    except Exception as exc:
        raised = type(exc).__name__ == "OwnerAction"
    check(raised and any(ln.startswith("owner: 4e ") for ln in f.out.getvalue().splitlines()), "changed params -> OwnerAction and `owner: 4e `")


BOTH = [s1_full_session, s3_params_edit, s5_failures, s7_accounting, s8_budget, s10_owner_stops]
KAGGLE_ONLY = [s2_restore, s6_resume_rules, s9_prune]


def main():
    for nb in ("train_voice_colab.ipynb", "train_voice_kaggle.ipynb"):
        print(f"==== {nb}")
        scenarios = BOTH + [s4_session_end] + (KAGGLE_ONLY if "kaggle" in nb else [])
        for scenario in sorted(scenarios, key=lambda f: int(re.match(r"s(\d+)_", f.__name__).group(1))):
            try:
                scenario(nb)
            except Exception as exc:
                import traceback
                traceback.print_exc()
                failures.append(f"{scenario.__name__} [{nb}] raised {exc!r}")
    print(f"\n{len(failures)} failure(s)")
    for f in failures:
        print("  -", f)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
