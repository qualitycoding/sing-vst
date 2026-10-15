"""Writes the status header at the top of plan/PLAN.md (protocol Phase 5.2; PK-05: every count is computed here).
Usage: python3.12 tools/gen/status.py READY|"BLOCKED — HUMAN DECISION REQUIRED"   (run after tools/gen/plan.py)"""
import collections, json, pathlib, re, sys
ROOT = pathlib.Path(__file__).resolve().parents[2]
status = sys.argv[1]
C = json.loads((ROOT / "research" / "claims.json").read_text(encoding="utf-8"))
conf = collections.Counter(c["confidence"] for c in C)
cpp = sum(len(re.findall(r'TEST_CASE \("T-\d{3}', f.read_text(encoding="utf-8"))) for f in (ROOT / "tests" / "cpp").glob("test_*.cpp"))
plugin = len(re.findall(r'TEST_CASE \("T-\d{3}', (ROOT / "tests" / "cpp" / "test_plugin.cpp").read_text(encoding="utf-8")))
py = {m for f in (ROOT / "tests" / "python").glob("test_*.py") for m in re.findall(r'"""(T-P?\d{2,3}) ', f.read_text(encoding="utf-8"))}
ci = len(re.findall(r"\((T-059)\)", (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")))
plan = (ROOT / "plan" / "PLAN.md").read_text(encoding="utf-8")
steps = len(re.findall(r"^### S-", plan, re.M))
gates = len(re.findall(r"^### G-\d{3}", (ROOT / "plan" / "GATES.md").read_text(encoding="utf-8"), re.M))
reg = (ROOT / "premortem" / "RISK_REGISTER.md").read_text(encoding="utf-8")
sev = collections.Counter(r.split(" | ")[3] for r in reg.splitlines() if re.match(r"^\| R-\d{3} \|", r))
rounds = len(list((ROOT / "premortem").glob("round-*.md")))
header = (f"<!-- STATUS: {status} -->\n**Status: {status}** · profiles `software`, `computational` · "
          f"claims {len(C)} ({', '.join(f'{k} {v}' for k, v in sorted(conf.items()))}) · tests: C++ core {cpp - plugin}, "
          f"C++ plugin {plugin}, Python {len(py)} IDs, CI-only {ci} (T-059) · steps {steps} · gates {gates} · risks "
          f"{sum(sev.values())} ({', '.join(f'{k} {v}' for k, v in sorted(sev.items()))}) · pre-mortem rounds {rounds} · "
          "figures 0 (D-032)\n")
lines = plan.split("\n", 1)
assert lines[0].startswith("<!--"), "PLAN.md must start with the status comment line"
(ROOT / "plan" / "PLAN.md").write_text(header + lines[1], encoding="utf-8")
print(header)
