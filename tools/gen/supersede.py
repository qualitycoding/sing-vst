"""Rule 12: a knowledge item whose fact changed is never edited away. For each claim ID given, mark the current item for it
superseded and write a new item (statement and source from research/claims.json) that names it in `supersedes`.
Usage: python tools/gen/supersede.py <UTC stamp YYYYMMDDTHHMMSSZ> C-027 [C-044 ...]  (stamps increment by one second per claim)"""
import datetime, json, pathlib, re, sys
ROOT = pathlib.Path(__file__).resolve().parents[2]
RUN = "gen-20261004T095012Z-singing-voice-vst-pitch-lyrics"
claims = {c["id"]: c for c in json.loads((ROOT / "research" / "claims.json").read_text())}
t0 = datetime.datetime.strptime(sys.argv[1], "%Y%m%dT%H%M%SZ")
for i, cid in enumerate(sys.argv[2:]):
    c = claims[cid]
    cur = [p for p in (ROOT / "knowledge").glob(f"K-*-{cid.lower()}-*.md") if re.search(r"^status: current$", p.read_text(), re.M)]
    assert len(cur) == 1, f"{cid}: expected one current item, found {cur}"
    old = cur[0]; text = old.read_text()
    head = dict(re.findall(r"^(\w+):[ \t]*(.*)$", text.split("---", 2)[1], re.M))
    old.write_text(text.replace("status: current", "status: superseded", 1))
    ts = t0 + datetime.timedelta(seconds=i); stamp = ts.strftime("%Y%m%dT%H%M%SZ")
    kid = f"K-{stamp}-{cid.lower()}-{old.stem.split(cid.lower() + '-', 1)[1]}"
    s0 = c["sources"][0]
    ver = head["applies_to_version"]
    m = re.search(r'"version": "([^"]*)"', json.dumps(s0))
    (ROOT / "knowledge" / f"{kid}.md").write_text(f"""---
id: {kid}
statement: {json.dumps(c['claim'])}
status: current
supersedes: [{old.stem}]
tags: {head['tags']}
applies_to_version: {ver}
source: {json.dumps({k: s0[k] for k in ('url', 'doi', 'title', 'locator', 'accessed', 'tier')})}
confidence: {c['confidence']}
derived_from: [{cid}]
discovered_by: planner
run: {RUN}
recorded_at: {ts.strftime('%Y-%m-%dT%H:%M:%SZ')}
---
Supersedes {old.stem}, whose statement was not supported by its cited source (see lesson L-20261014T142000Z-verified-label-cited-a-file-never-written).
Sources: {'; '.join(s['title'] + ' <' + s['url'] + '> [' + s['locator'] + ']' for s in c['sources'])}.
""", encoding="utf-8")
    print("superseded", old.stem, "->", kid)
