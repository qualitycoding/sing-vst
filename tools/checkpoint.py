"""Writes .checkpoints/state.json in the protocol v3.3 schema (1.2.1-1.2.3; D-034): phase/subphase lists, artifact hashes from
`git ls-files` (plus untracked, non-ignored files), execution_context and active_variables (kept between calls unless a flag
changes them), a sequence number, and a snapshot in .checkpoints/snapshots/checkpoint-<run_id>-seq-<N>.json. Atomic:
state.tmp.json -> state.json. Called by tools/save.sh on every save, and directly when context changes.
Examples:
  python3 tools/checkpoint.py --phase 3 --subphase 3.5 --active-step HANDOFF.md \\
     --objective "write the handoff" --pointer '{"item_index": 2, "sub_action": "rules verbatim"}' --scratchpad "..."
  python3 tools/checkpoint.py --open-question "Q-E8: HF revision" --var 'python="/usr/bin/python3.12"'
"""
import argparse, datetime, hashlib, json, pathlib, subprocess
ROOT = pathlib.Path(__file__).resolve().parents[1]
D = ROOT / ".checkpoints"; S = D / "state.json"
ap = argparse.ArgumentParser()
ap.add_argument("--phase"); ap.add_argument("--subphase"); ap.add_argument("--active-step")
ap.add_argument("--complete", action="append", default=[]); ap.add_argument("--pending", action="append", default=[])
ap.add_argument("--done-pending", action="append", default=[], help="remove from pending")
ap.add_argument("--note", action="append", default=[])
ap.add_argument("--set", action="append", default=[], help="key=json value at top level")
ap.add_argument("--objective"); ap.add_argument("--scratchpad"); ap.add_argument("--call-stack", help="json list")
ap.add_argument("--pointer", help="json object merged into execution_context.step_pointer")
ap.add_argument("--in-flight", help="json value (null when nothing is in flight)")
ap.add_argument("--var", action="append", default=[], help="key=json into active_variables.variable_store")
ap.add_argument("--open-question", action="append", default=[]); ap.add_argument("--resolve-question", action="append", default=[])
ap.add_argument("--candidate-decision", action="append", default=[]); ap.add_argument("--draft", action="append", default=[],
                help="path=description of an uncommitted draft; path= alone removes it")
a = ap.parse_args()
st = json.loads(S.read_text()) if S.exists() else {}
if a.phase: st["phase"] = a.phase
if a.subphase: st["subphase"] = a.subphase
if a.active_step: st["active_step_id"] = a.active_step
for c in a.complete:
    if c not in st.setdefault("completed", []): st["completed"].append(c)
st["pending"] = [p for p in st.get("pending", []) if p not in a.done_pending and p not in a.complete] + \
                [p for p in a.pending if p not in st.get("pending", [])]
st.setdefault("notes", []).extend(a.note)
for kv in a.set:
    k, v = kv.split("=", 1); st[k] = json.loads(v)
ec = st.setdefault("execution_context", {})
for k, v in (("current_objective", ""), ("call_stack", []), ("scratchpad", ""), ("in_flight_operation", None), ("tool_cache", {})):
    ec.setdefault(k, v)
ec.setdefault("step_pointer", {"phase": "", "subphase": "", "item_index": 0, "sub_action": "", "retry_count": 0})
if a.objective is not None: ec["current_objective"] = a.objective
if a.scratchpad is not None: ec["scratchpad"] = a.scratchpad
if a.call_stack: ec["call_stack"] = json.loads(a.call_stack)
if a.pointer: ec["step_pointer"].update(json.loads(a.pointer))
ec["step_pointer"]["phase"], ec["step_pointer"]["subphase"] = st.get("phase", ""), st.get("subphase", "")
if a.in_flight is not None: ec["in_flight_operation"] = json.loads(a.in_flight)
av = st.setdefault("active_variables", {})
for k, v in (("intake_parameters", {}), ("user_constraints", []), ("open_questions", []), ("resolved_questions", []),
             ("candidate_decisions", []), ("uncommitted_drafts", {}), ("variable_store", {})):
    av.setdefault(k, v)
for kv in a.var:
    k, v = kv.split("=", 1); av["variable_store"][k] = json.loads(v)
for q in a.open_question:
    if q not in av["open_questions"]: av["open_questions"].append(q)
for q in a.resolve_question:
    hits = [x for x in av["open_questions"] if x.startswith(q.split(":")[0])]
    av["open_questions"] = [x for x in av["open_questions"] if x not in hits]; av["resolved_questions"].append(q)
for c in a.candidate_decision:
    if c not in av["candidate_decisions"]: av["candidate_decisions"].append(c)
for d in a.draft:
    k, v = d.split("=", 1)
    if v: av["uncommitted_drafts"][k] = v
    else: av["uncommitted_drafts"].pop(k, None)
files = subprocess.run(["git", "ls-files", "--cached", "--others", "--exclude-standard"], cwd=ROOT, capture_output=True,
                       text=True, check=True).stdout.split("\n")
st["artifacts"] = {f: hashlib.sha256((ROOT / f).read_bytes()).hexdigest() for f in sorted(set(files))
                   if f and (ROOT / f).is_file() and not f.startswith(".checkpoints/")}
st["lessons_recorded"] = sorted(p.stem for p in (ROOT / "lessons").glob("L-*.md"))
st["knowledge_added"] = sorted(p.stem for p in (ROOT / "knowledge").glob("K-*.md"))
st["sequence"] = int(st.get("sequence", 0)) + 1
st["updated_at"] = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
D.mkdir(exist_ok=True); (D / "snapshots").mkdir(exist_ok=True)
text = json.dumps(st, indent=2) + "\n"
tmp = D / "state.tmp.json"; tmp.write_text(text); tmp.replace(S)
(D / "snapshots" / f"checkpoint-{st.get('run_id', 'run')}-seq-{st['sequence']}.json").write_text(text)
print("checkpoint", st.get("phase"), st.get("subphase"), "seq", st["sequence"], len(st["artifacts"]), "artifacts")
