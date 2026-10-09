"""Rewrites .checkpoints/state.json: updates phase/subphase and lists, regenerates the artifact hash map from `git ls-files`
(plus staged new files) and updated_at. Usage: python tools/checkpoint.py --phase 1 --subphase 1.3 [--complete X] [--pending X] [--note TEXT]
Used by the planner and by the implementer after every step (lessons L-20261009T232009Z, L-20261009T152201Z)."""
import argparse, datetime, hashlib, json, pathlib, subprocess
ROOT = pathlib.Path(__file__).resolve().parents[1]
S = ROOT / ".checkpoints" / "state.json"
ap = argparse.ArgumentParser()
ap.add_argument("--phase"); ap.add_argument("--subphase")
ap.add_argument("--complete", action="append", default=[]); ap.add_argument("--pending", action="append", default=[])
ap.add_argument("--done-pending", action="append", default=[], help="remove from pending")
ap.add_argument("--note", action="append", default=[])
ap.add_argument("--set", action="append", default=[], help="key=json value at top level")
a = ap.parse_args()
st = json.loads(S.read_text()) if S.exists() else {}
if a.phase: st["phase"] = a.phase
if a.subphase: st["subphase"] = a.subphase
for c in a.complete:
    if c not in st.setdefault("completed", []): st["completed"].append(c)
st["pending"] = [p for p in st.get("pending", []) if p not in a.done_pending and p not in a.complete] + [p for p in a.pending if p not in st.get("pending", [])]
st.setdefault("notes", []).extend(a.note)
for kv in a.set:
    k, v = kv.split("=", 1); st[k] = json.loads(v)
files = subprocess.run(["git", "ls-files", "--cached", "--others", "--exclude-standard"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.split()
st["artifacts"] = {f: hashlib.sha256((ROOT / f).read_bytes()).hexdigest() for f in sorted(set(files)) if (ROOT / f).is_file() and not f.startswith(".checkpoints/")}
st["lessons_recorded"] = sorted(p.stem for p in (ROOT / "lessons").glob("L-*.md"))
st["knowledge_added"] = sorted(p.stem for p in (ROOT / "knowledge").glob("K-*.md"))
st["updated_at"] = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
S.parent.mkdir(exist_ok=True)
tmp = S.with_suffix(".tmp"); tmp.write_text(json.dumps(st, indent=2) + "\n"); tmp.replace(S)
print("checkpoint", st.get("phase"), st.get("subphase"), len(st["artifacts"]), "artifacts")
