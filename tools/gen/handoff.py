"""Renders HANDOFF.md from HANDOFF.src.md: {{RULE:n}} = Global Rule n copied verbatim from the protocol file, {{STEPS}} = one
row per step of plan/PLAN.md. Usage: python3.12 tools/gen/handoff.py <path to planning-protocol.md>"""
import pathlib, re, sys
ROOT = pathlib.Path(__file__).resolve().parents[2]
proto = pathlib.Path(sys.argv[1]).read_text(encoding="utf-8")
def rule(n):
    m = re.search(rf"^{n}\. \*\*.*?(?=^\d+\. \*\*|^---)", proto, re.M | re.S)
    if not m: raise SystemExit(f"rule {n} not found")
    return m.group(0).rstrip()
plan = (ROOT / "plan" / "PLAN.md").read_text(encoding="utf-8")
rows = []
for m in re.finditer(r"^### (S-[0-9A-Z]+) (.+?)\n(.*?)(?=^### |\Z)", plan, re.M | re.S):
    ev = re.search(r"^- Evidence produced: (.*)$", m.group(3), re.M); gate = re.search(r"^- Gate: (.*)$", m.group(3), re.M)
    rows.append(f"| {m.group(1)} | {m.group(2)} | {ev.group(1) if ev else ''} | {gate.group(1) if gate else ''} |")
src = (ROOT / "HANDOFF.src.md").read_text(encoding="utf-8")
out = re.sub(r"\{\{RULE:(\d+)\}\}", lambda m: rule(int(m.group(1))), src).replace("{{STEPS}}", "\n".join(rows))
(ROOT / "HANDOFF.md").write_text(out, encoding="utf-8")
print("steps", len(rows))
