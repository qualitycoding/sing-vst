"""Writes tests/FROZEN_MANIFEST.sha256 (2E.2) for every tracked file matching the frozen globs of T-060, plus
eval/thresholds.json. Run ONLY by the planning agent at a freeze or an amendment (2E.4); never by the implementer (PK-24).
Usage: python3 tools/freeze.py"""
import fnmatch, hashlib, pathlib, subprocess
ROOT = pathlib.Path(__file__).resolve().parents[1]
GLOBS = ("tests/**/*", "core/include/singvst/*.hpp", "plugin/PluginProcessor.h", "eval/phrases/*")
ALSO = ("eval/thresholds.json", "eval/PROCEDURE.md")
tracked = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.split("\n")
files = sorted({p for p in tracked if p and any(fnmatch.fnmatch(p, g) for g in GLOBS)} | set(ALSO) - {"tests/FROZEN_MANIFEST.sha256"})
lines = [f"{hashlib.sha256((ROOT / p).read_bytes()).hexdigest()}  {p}" for p in files]
(ROOT / "tests" / "FROZEN_MANIFEST.sha256").write_text("\n".join(lines) + "\n", encoding="utf-8")
print(len(lines), "files frozen")
