"""Generates research/SOURCES.md from research/claims.json: one row per distinct source with its tier, version, the claims
it supports and their confidence (verification notes). Usage: python3.12 tools/gen/sources.py"""
import json, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[2]
C = json.loads((ROOT / "research" / "claims.json").read_text(encoding="utf-8"))
src = {}
for c in C:
    for s in c["sources"]:
        k = (s["url"], s["title"])
        e = src.setdefault(k, {"tier": s["tier"], "version": s.get("version", ""), "accessed": s["accessed"], "claims": [], "locators": set()})
        e["claims"].append(f"{c['id']} ({c['confidence']})"); e["locators"].add(s["locator"])
L = ["# Sources", "", "Generated from research/claims.json by `python3.12 tools/gen/sources.py`. Tier 1 = official docs, source code at the",
     "pinned version, specifications, or a committed spike; Tier 2 = maintainer statements, release notes, issue trackers; Tier 3",
     "= reputable secondary write-ups; Tier 4 = forums (never sufficient alone). Every source was opened in this run (PK-06).", "",
     "| Source | URL / path | Tier | Version | Accessed | Locators | Supports |", "|---|---|---|---|---|---|---|"]
for (url, title), e in sorted(src.items(), key=lambda kv: (kv[1]["tier"], kv[0][1])):
    L.append(f"| {title} | {url} | {e['tier']} | {e['version']} | {e['accessed']} | {'; '.join(sorted(e['locators']))} | {', '.join(e['claims'])} |")
L += ["", f"{len(src)} sources, {len(C)} claims."]
(ROOT / "research" / "SOURCES.md").write_text("\n".join(L) + "\n", encoding="utf-8")
print(len(src), "sources")
