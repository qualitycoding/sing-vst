# FROZEN — DO NOT MODIFY (plan/PLAN.md, tests/FROZEN_MANIFEST.sha256). Requirement, decision and claim IDs are cited per test.
"""Repository and environment properties (D-023: exempt from red verification; they must pass from Phase 5 onward)."""
import hashlib
import json
import re
import shutil
import subprocess
import sys
import venv

import pytest
import yaml

FREEZE_ALSO = ("eval/thresholds.json",)
FREEZE_GLOBS = ("tests/**/*", "core/include/singvst/*.hpp", "plugin/PluginProcessor.h", "eval/phrases/*")


def _git(root, *args):
    return subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True, check=True).stdout


def test_T060_freeze_manifest_matches_and_covers_every_frozen_file(root):
    """T-060 (Phase 2E, PK-23, PK-24): every listed hash matches; every tracked file under the frozen globs is listed."""
    manifest = root / "tests" / "FROZEN_MANIFEST.sha256"
    listed = {}
    for line in manifest.read_text(encoding="utf-8").splitlines():
        digest, path = line.split("  ", 1)
        listed[path] = digest
    for path, digest in listed.items():
        assert hashlib.sha256((root / path).read_bytes()).hexdigest() == digest, f"{path} changed after the freeze"
    tracked = set(_git(root, "ls-files").split("\n")) - {""}
    want = {p for p in tracked if any(__import__("fnmatch").fnmatch(p, g) for g in FREEZE_GLOBS)} | set(FREEZE_ALSO)
    want -= {"tests/FROZEN_MANIFEST.sha256"}
    assert sorted(want - set(listed)) == []


def test_T061_workflow_keeps_the_required_jobs_and_checks(root):
    """T-061 (D-018, C-015, C-045, PK-15, PK-16): the CI workflow parses and still runs every frozen suite."""
    path = root / ".github" / "workflows" / "ci.yml"
    text = path.read_text(encoding="utf-8")
    wf = yaml.safe_load(text)
    on = wf.get("on", wf.get(True))
    assert "push" in on and "pull_request" in on
    assert wf.get("permissions") == {"contents": "read"}
    jobs = wf["jobs"]
    assert {"repo", "cpp", "sanitizers", "python", "python-torch"} <= set(jobs)
    assert jobs["cpp"]["strategy"]["matrix"]["os"] == ["ubuntu-24.04", "windows-2022"]
    allowed = {"actions/checkout": "v7", "actions/setup-python": "v7", "actions/upload-artifact": "v7",
               "actions/download-artifact": "v8"}
    for uses in re.findall(r"uses:\s*([^\s#]+)", text):
        name, _, tag = uses.partition("@")
        assert name in allowed and tag == allowed[name], uses
    runs = {j: "\n".join(s.get("run", "") for s in jobs[j]["steps"]) for j in jobs}
    assert "sha256sum -c tests/FROZEN_MANIFEST.sha256" in runs["repo"]
    assert "ctest" in runs["cpp"] and "ctest" in runs["sanitizers"]
    assert "--strictness-level 5" in runs["cpp"] and "--skip-gui-tests" in runs["cpp"]
    assert "--validate-in-process" not in text
    assert "-fsanitize=address" in text and "-fsanitize=thread" in text
    assert re.search(r"pytest .*-m \"not torch and not voice", runs["python"])
    assert re.search(r"pytest .*-m torch", runs["python-torch"])
    assert "pip-audit" in runs["repo"] or "network" in runs["repo"]
    if shutil.which("actionlint"):
        r = subprocess.run(["actionlint", str(path)], capture_output=True, text=True)
        assert r.returncode == 0, r.stdout + r.stderr


def test_T062_ignore_rules_and_no_private_data_tracked(root):
    """T-062 (PK-08, A-011, D-008, D-026): build output ignored, fixtures not; no voice packages, weights or recordings."""
    def ignored(p):
        return subprocess.run(["git", "-C", str(root), "check-ignore", "-q", "--no-index", p]).returncode == 0
    for p in ("build/x", "build-core/x", "python/singvst_train/__pycache__/x.pyc", "voices/a.wav", "data/a.wav", ".venv/x"):
        assert ignored(p), p
    for p in ("tests/fixtures/lyrics.mid", "tests/fixtures/onnx/vocoder.onnx", "eval/phrases/p1.mid",
              "third_party/cmudict/cmudict.dict", "tests/fixtures/voice-convert/manifest.json", "notebooks/x.ipynb"):
        assert not ignored(p), p
    assert _git(root, "ls-files", "-ci", "--exclude-standard").strip() == ""
    tracked = [p for p in _git(root, "ls-files").split("\n") if p]
    assert [p for p in tracked if p.endswith((".pth", ".ckpt", ".index", ".zip"))] == []
    assert [p for p in tracked if p.endswith((".wav", ".flac", ".mp3")) and not p.startswith("tests/fixtures/")] == []
    for p in tracked:
        if p.endswith("manifest.json") and not p.startswith("tests/fixtures/"):
            assert '"singvoice"' not in (root / p).read_text(encoding="utf-8", errors="replace"), p


@pytest.mark.network
def test_P21_lock_reinstalls_exactly_and_audits_clean(tmp_path, root):
    """T-P21 (D-019, PK-41): the lock reproduces in a clean venv, pip check passes, pip-audit 2.10.1 finds nothing
    (flags from research/spikes/pip-audit-setuptools)."""
    lock = root / "python" / "requirements-lock.txt"
    want = sorted(l for l in lock.read_text().splitlines() if l and not l.startswith("#"))
    v = tmp_path / "v"
    venv.create(v, with_pip=True)
    py = v / "bin" / "python"
    subprocess.run([str(py), "-m", "pip", "install", "-q", "--no-deps", "-r", str(lock)], check=True)
    have = sorted(subprocess.run([str(py), "-m", "pip", "freeze", "--all"], capture_output=True, text=True,
                                 check=True).stdout.split())
    assert have == want
    assert subprocess.run([str(py), "-m", "pip", "check"]).returncode == 0
    a = tmp_path / "a"
    venv.create(a, with_pip=True)
    subprocess.run([str(a / "bin" / "python"), "-m", "pip", "install", "-q", "pip-audit==2.10.1"], check=True)
    r = subprocess.run([str(a / "bin" / "pip-audit"), "-r", str(lock), "--no-deps", "--disable-pip"],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr


ID = re.compile(r"\b(?:(C|D|A|G|S|R|T)-(\d{3})|T-(P\d{2})|(DR|PK)-(\d{2})|(L|K)-(\d{8}T\d{4,6}Z?))")
SCANNED = ("tests/**/*.py", "tests/cpp/*.cpp", "plan/*.md", "HANDOFF.md", "README.md", "research/QUESTIONS.md",
           "research/PRIOR_KNOWLEDGE.md", "research/claims.json", "premortem/*.md", "eval/*", ".github/workflows/*.yml",
           "python/singvst_train/*.py", "core/include/singvst/*.hpp", "notebooks/*.ipynb")


def _registry(root):
    reg = {k: set() for k in "CDAGSRT"}
    reg["C"] = {c["id"] for c in json.loads((root / "research" / "claims.json").read_text(encoding="utf-8"))}
    dec = (root / "plan" / "DECISIONS.md").read_text(encoding="utf-8")
    reg["D"] = set(re.findall(r"^### (D-\d{3})", dec, re.M))
    reg["DR"] = set(re.findall(r"^- (DR-\d{2})", dec, re.M))
    for k, f, pat in (("A", "plan/ASSUMPTIONS.md", r"^### (A-\d{3})"), ("G", "plan/GATES.md", r"^### (G-\d{3})"),
                      ("S", "plan/PLAN.md", r"^### (S-\d{3})"), ("R", "premortem/RISK_REGISTER.md", r"^\| (R-\d{3}) \|")):
        reg[k] = set(re.findall(pat, (root / f).read_text(encoding="utf-8"), re.M))
    for f in (root / "tests" / "cpp").glob("test_*.cpp"):
        reg["T"] |= set(re.findall(r'TEST_CASE \("(T-\d{3})', f.read_text(encoding="utf-8")))
    for f in (root / "tests" / "python").glob("test_*.py"):
        reg["T"] |= set(re.findall(r'"""(T-P?\d{2,3})', f.read_text(encoding="utf-8")))
    reg["T"] |= set(re.findall(r"\((T-\d{3})\)", (root / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")))
    reg["PK"] = set(re.findall(r"^\| (PK-\d{2}) \|", (root / "research" / "PRIOR_KNOWLEDGE.md").read_text(encoding="utf-8"), re.M))
    state = json.loads((root / ".checkpoints" / "state.json").read_text(encoding="utf-8"))
    reg["L"] = {p.stem for p in (root / "lessons").glob("L-*.md")} | set(state.get("lessons_loaded", []))
    reg["K"] = {p.stem for p in (root / "knowledge").glob("K-*.md")} | set(state.get("knowledge_loaded", []))
    return reg


def test_P22_every_cited_id_exists(root):
    """T-P22 (PK-06, PK-26): every C/D/A/G/S/R/T/T-P/DR/PK/L/K identifier cited in the plan, tests, code or CI exists."""
    reg = _registry(root)
    missing = []
    for g in SCANNED:
        for f in sorted(root.glob(g)):
            if not f.is_file() or "__pycache__" in f.parts or f.name == "PROTOCOL_EXCERPTS.md":   # verbatim external text
                continue
            text = f.read_text(encoding="utf-8", errors="replace")
            if f.name == "PRIOR_KNOWLEDGE.md":   # drop the column that quotes store lessons' own summaries (other runs' IDs)
                text = "\n".join(" | ".join(l.split(" | ")[:3] + l.split(" | ")[4:]) if l.startswith("| `L-") else l
                                 for l in text.splitlines())
            for m in ID.finditer(text):
                if m.group(1):
                    ok = f"{m.group(1)}-{m.group(2)}" in reg[m.group(1)]
                elif m.group(3):
                    ok = f"T-{m.group(3)}" in reg["T"]
                elif m.group(4):
                    ok = f"{m.group(4)}-{m.group(5)}" in reg[m.group(4)]
                else:
                    ok = any(x.startswith(f"{m.group(6)}-{m.group(7)}") for x in reg[m.group(6)])
                if not ok:
                    missing.append(f"{f.relative_to(root)}: {m.group(0)}")
    assert missing == []


SOUND = re.compile(r"sounds? (just )?like|realistic|natural-sounding|indistinguishable|studio[- ]quality|lifelike", re.I)


def test_P23_readme_states_behaviour_only_with_test_ids(root):
    """T-P23 (D-030, PK-04, PK-46): each bullet under '## What it does' cites a test; claims about how the voice sounds
    appear only on lines that cite the G-001 listening record."""
    docs = [root / "README.md", *sorted((root / "docs").glob("**/*.md"))]
    readme = docs[0].read_text(encoding="utf-8")
    section = re.search(r"^## What it does\n(.*?)(?=^## |\Z)", readme, re.M | re.S)
    assert section, "README.md needs a '## What it does' section (plan step S-018)"
    bullets = [l for l in section.group(1).splitlines() if l.lstrip().startswith(("- ", "* "))]
    assert bullets and all(re.search(r"\bT-P?\d{2,3}\b", b) for b in bullets), bullets
    for d in docs:
        for n, line in enumerate(d.read_text(encoding="utf-8").splitlines(), 1):
            if SOUND.search(line):
                assert "G-001" in line, f"{d.name}:{n}: {line}"


def test_P27_python_interfaces_match_the_frozen_record(root):
    """T-P27 (D-003, PK-22): signatures, documented behaviour (docstring hashes) and constants are unchanged."""
    sys.path.insert(0, str(root / "tools" / "gen"))
    import interfaces
    assert interfaces.record() == json.loads((root / "tests" / "python" / "interfaces.json").read_text(encoding="utf-8"))
