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
audit = ROOT / "premortem" / "ASSUMPTION_AUDIT.md"          # Phase 4.7 (v3.4): counts generated from its tables
verdicts = collections.Counter()
if audit.exists():
    for row in audit.read_text(encoding="utf-8").split("## Assumptions", 1)[-1].splitlines():
        cells = [c.strip() for c in row.strip("|").split("|")] if row.startswith("| ") else []
        if not cells or cells[0] in ("Item", "Claim", "Test") or set(row) <= set("|- "):
            continue
        joined = " ".join(cells).lower()
        verdicts["falsified" if "**falsified" in joined else next((v for v in ("unverifiable", "confirmed") for c in cells if c.startswith(v)), "?")] += 1
reviews = [n for n in ("CODE_REVIEW", "ADVERSARIAL_REVIEW", "MUTATION") if (ROOT / "reviews" / f"{n}.md").exists()]
header = (f"<!-- STATUS: {status} -->\n**Status: {status}** · profiles `software`, `computational` · "
          f"claims {len(C)} ({', '.join(f'{k} {v}' for k, v in sorted(conf.items()))}) · tests: C++ core {cpp - plugin}, "
          f"C++ plugin {plugin}, Python {len(py)} IDs, CI-only {ci} (T-059) · steps {steps} · gates {gates} · risks "
          f"{sum(sev.values())} ({', '.join(f'{k} {v}' for k, v in sorted(sev.items()))}) · pre-mortem rounds {rounds} · "
          "figures 0 (D-032) · assumption audit "
          + (", ".join(f"{k} {v}" for k, v in sorted(verdicts.items())) if verdicts else "not run")
          + f" · reviews {len(reviews)}/3 done (S-REVIEW, S-ADVERSARIAL, S-MUTATE) · protocol v3.6 (D-041)"
          + (" · **decision needed: premortem/RESIDUAL.md — no step may start**" if status != "READY" else "") + "\n")
lines = plan.split("\n", 1)
assert lines[0].startswith("<!--"), "PLAN.md must start with the status comment line"
(ROOT / "plan" / "PLAN.md").write_text(header + lines[1], encoding="utf-8")
print(header)
