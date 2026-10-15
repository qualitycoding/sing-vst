"""Renders plan/PLAN.md from plan/PLAN.src.md: each {{L:PK-xx,...}} becomes the PK rules with the source-lesson IDs listed
for them in research/PRIOR_KNOWLEDGE.md (IDs generated, never typed — PK-05). Usage: python3 tools/gen/plan.py"""
import pathlib, re
ROOT = pathlib.Path(__file__).resolve().parents[2]
pk = {}
for line in (ROOT / "research" / "PRIOR_KNOWLEDGE.md").read_text(encoding="utf-8").splitlines():
    m = re.match(r"^\| (PK-\d{2}) \|.*\| ([^|]*) \|\s*$", line)
    if m:
        pk[m.group(1)] = [x.strip() for x in m.group(2).split(",") if x.strip().startswith("L-")]
def render(m):
    out = []
    for p in m.group(1).split(","):
        p = p.strip()
        if p not in pk:
            raise SystemExit(f"unknown {p}")
        out.append(f"{p} ({', '.join(pk[p][:3]) or 'this run'})")
    return "; ".join(out)
src = (ROOT / "plan" / "PLAN.src.md").read_text(encoding="utf-8")
text = re.sub(r"\{\{L:([^}]*)\}\}", render, src)
(ROOT / "plan" / "PLAN.md").write_text(text, encoding="utf-8")
print("steps", len(re.findall(r"^### S-", text, re.M)))
