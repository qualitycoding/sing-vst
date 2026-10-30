"""Post-condition audit of the completed steps (Rule 14, protocol v3.6; plan/AMENDMENT-01.md AM-05).

Usage: python3.12 tools/check_postconditions.py        (standard library only; exit 0 when every artifact passes)

For every artifact a completed step lists under `Outputs` in plan/PLAN.md this checks that it exists, is non-empty and passes a
sanity check (parses, holds the expected fields or sections). One line per artifact: `ok` or `FAIL` with the reason.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PARENT = ROOT.parent
HOME = Path.home()
results = []


def check(step, label, ok, why=""):
    results.append(ok)
    print(f"{'ok  ' if ok else 'FAIL'} {step:<6} {label}" + ("" if ok else f"  -- {why}"))


def nonempty(p):
    return p.exists() and (p.is_dir() and any(p.iterdir()) or p.is_file() and p.stat().st_size > 0)


def text(p):
    return p.read_text(encoding="utf-8", errors="replace") if p.is_file() else ""


def file_with(step, rel, *needles, base=ROOT):
    p = base / rel
    missing = [n for n in needles if n not in text(p)]
    check(step, rel, nonempty(p) and not missing, "missing or empty" if not nonempty(p) else f"lacks {missing}")


def implemented(step, rel, names):
    src = text(ROOT / rel)
    left = [n for n in names if f'NotImplementedError("{n}")' in src]
    check(step, f"{rel} bodies implemented ({len(names)})", nonempty(ROOT / rel) and not left, f"still stubbed: {left}")


def log_row(step):
    rows = [ln for ln in text(ROOT / "EXECUTION_LOG.md").splitlines() if re.match(rf"^\| [^|]+ \| {re.escape(step)} \| \d+ \| pass \|", ln)]
    check(step, f"EXECUTION_LOG.md has a pass row for {step}", bool(rows), "no pass row")


# ---- S-000 environment and records
state = json.loads(text(ROOT / ".checkpoints" / "state.json") or "{}")
check("S-000", ".checkpoints/state.json phase impl, stores recorded", state.get("phase") == "impl" and "commit_at_impl" in state.get("knowledge_store", {}), "phase or knowledge_store.commit_at_impl missing")
check("S-000", ".git/singvst-trailers", nonempty(ROOT / ".git" / "singvst-trailers") and "Co-Authored-By:" in text(ROOT / ".git" / "singvst-trailers"), "empty")
file_with("S-000", "EXECUTION_LOG.md", "| UTC time | Step | Attempt | Result (pass/fail/blocked) | Commit before this row | Note |")
file_with("S-000", "DEVIATIONS.md", "| UTC time | Step | Plan says | Done instead | Why (rule applied) |")
for rel in ("store-lessons/.git", "store-knowledge/.git", "rvc/.git", "hosts-now.txt"):
    check("S-000", f"../{rel}", nonempty(PARENT / rel), "missing")
rvc_head = subprocess.run(["git", "-C", str(PARENT / "rvc"), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
check("S-000", "../rvc at 81eed5e", rvc_head == "81eed5e8f68b6bed1789f682fe78cdd324495afc", rvc_head)
for rel in ("JUCE/modules", "Catch2/src", "ort/lib/libonnxruntime.so.1.31.0"):
    check("S-000", f"$HOME/deps/{rel}", nonempty(HOME / "deps" / rel), "missing")
for tree, exe in (("build-core", "tests/cpp/singvst_tests"), ("build-asan", "tests/cpp/singvst_tests"), ("build-tsan", "tests/cpp/singvst_tests"),
                  ("build-full", "tests/cpp/singvst_plugin_tests")):
    check("S-000", f"../{tree}/{exe}", nonempty(PARENT / tree / exe), "not built")
check("S-000", "../venv-lock/bin/python", (PARENT / "venv-lock" / "bin" / "python").exists(), "missing")
for s in ("S-000", "S-001", "S-002", "S-003", "S-004", "S-005", "S-006", "S-007", "S-008", "S-009", "S-010", "S-011", "S-012", "S-013", "S-014", "S-015", "S-016"):
    log_row(s)

# ---- S-002 ... S-009 core sources (D-033: each step adds its module; stubs.cpp deleted at S-009)
for step, files in (("S-002", ["lyrics.cpp", "g2p.cpp", "align.cpp"]), ("S-003", ["synthesis.cpp"]), ("S-004", ["voice.cpp", "sha256.cpp"]),
                    ("S-005", ["playback.cpp"]), ("S-006", ["midifile.cpp"]), ("S-007", ["random.cpp", "ort_runtime.cpp", "resample.cpp"]),
                    ("S-008", ["guide_engine.cpp", "converter_engine.cpp"]), ("S-009", ["render.cpp", "take_cache.cpp"])):
    for f in files:
        check(step, f"core/src/{f}", nonempty(ROOT / "core" / "src" / f) and "NotImplemented (" not in text(ROOT / "core" / "src" / f), "missing or stubbed")
check("S-009", "core/src/stubs.cpp deleted", not (ROOT / "core" / "src" / "stubs.cpp").exists(), "still present")
file_with("S-008", "research/spikes/s008-external-data/output.txt", "external data", "guide part 0", "guide part 1", "exit: 0")
file_with("S-008", "research/spikes/s008-external-data/run.sh", "SINGVST_DEBUG_RUNS=1")

# ---- S-010 CLI
file_with("S-010", "cli/main.cpp", "--check-voice", "provenance.json")
file_with("S-010", "cli/CMakeLists.txt", "singvst_git_commit")
file_with("S-010", "cli/git_commit.cmake", "rev-parse HEAD")
binary = PARENT / "build-core" / "cli" / "singvst-render"
usage = subprocess.run([str(binary)], capture_output=True, text=True) if binary.exists() else None
check("S-010", "singvst-render without arguments exits 2 with usage", usage is not None and usage.returncode == 2 and "usage:" in usage.stderr, "binary missing or wrong exit")

# ---- S-011 plugin
file_with("S-011", "plugin/PluginProcessor.cpp", "TakeSlot", "kCancelAck", "cachedRender")
file_with("S-011", "plugin/PluginEditor.h", "struct EditorStatus")
file_with("S-011", "plugin/PluginEditor.cpp", "launchAsync")
file_with("S-011", "docs/UNVERIFIED.md", "## Editor", "## Converter", "## Training notebooks", "De-reverb path")

# ---- S-012 ... S-015 toolkit
implemented("S-012", "python/singvst_train/prepare.py", ["split_heldout", "slice_on_silence", "normalise", "build_dataset_manifest", "dereverb"])
implemented("S-012", "python/singvst_train/pipeline.py", ["content_hash", "run_stages", "atomic_write_text"])
implemented("S-012", "python/singvst_train/provenance.py", ["collect", "write_sidecar"])
implemented("S-012", "python/singvst_train/metrics.py", ["load_pyworld", "extract_f0", "cents", "score_f0", "normalise_text", "wer", "cosine", "judge"])
implemented("S-012", "python/singvst_train/pack.py", ["pack_voice"])
implemented("S-012", "python/singvst_train/security.py", ["scan_secrets"])
implemented("S-012", "python/singvst_train/cli.py", ["build_parser", "main"])
implemented("S-013", "python/singvst_train/export_rvc.py", ["export_synth", "export_content", "make_test_weights", "parity"])
check("S-013", "plan/ENVIRONMENT.md records the Hugging Face revision", re.search(r"revision `[0-9a-f]{40}`", text(ROOT / "plan" / "ENVIRONMENT.md")) is not None, "no 40-hex revision")
implemented("S-014", "python/singvst_train/rvc_files.py", ["write_filelist", "copy_config", "train_command", "latest_weights"])
implemented("S-015", "python/singvst_train/evaluate.py", ["transpose_semitones", "evaluate_voice"])
g5 = text(ROOT / "GATE-G-005.md")
check("S-015", "GATE-G-005.md answered", "## Response" in g5 and g5.split("## Response", 1)[1].strip().startswith("use-tiger"), "no recorded response")

# ---- S-016 notebooks
for name in ("train_voice_colab.ipynb", "train_voice_kaggle.ipynb"):
    nb = json.loads(text(ROOT / "notebooks" / name) or "{}")
    code = [c for c in nb.get("cells", []) if c.get("cell_type") == "code"]
    ok = nb.get("nbformat") == 4 and len(code) == 19 and all(c.get("outputs") == [] and c.get("execution_count") is None for c in code)
    check("S-016", f"notebooks/{name}: nbformat 4, 19 code cells, no outputs", ok, f"nbformat {nb.get('nbformat')}, {len(code)} code cells")
file_with("S-016", "tools/notebook_dryrun.py", "def s10_owner_stops")
file_with("S-016", "EXECUTION_LOG.md", "### S-016 `tools/notebook_dryrun.py` output", "0 failure(s)")

# ---- S-017 (in progress): the open gate
g4 = text(ROOT / "GATE-G-004.md")
m = re.search(r"EXPECTED_COMMIT` \| `([0-9a-f]{40})`", g4)
check("S-017", "GATE-G-004.md pins a 40-hex EXPECTED_COMMIT and the Colab link", bool(m) and f"/blob/{m.group(1)}/notebooks/train_voice_colab.ipynb" in g4 if m else False, "no pinned commit")

# ---- lessons and knowledge items (Rules 11, 12)
schema = subprocess.run([sys.executable, str(ROOT / "tools" / "check_schema.py")], capture_output=True, text=True, cwd=ROOT)
check("all", "lessons/ and knowledge/ pass tools/check_schema.py", schema.returncode == 0, schema.stdout.strip()[-200:])

print(f"\n{sum(results)}/{len(results)} post-conditions hold")
sys.exit(0 if all(results) else 1)
