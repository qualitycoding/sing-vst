"""GitHub annotations from JUnit XML (D-018, D-036, PK-14). For each file: one `::notice title=test-summary <file>::` line
listing the test IDs (T-###, T-P##) that passed, failed and were skipped (a skipped case never counts as passed, R-040) — the pass criterion of D-036, immune to the per-step limit on
error annotations — then an `::error::` line per failing case (may be capped by GitHub). Usage: python3.12 tools/ci_annotate.py <junit.xml>..."""
import re
import sys
import xml.etree.ElementTree as ET

ID = re.compile(r"\bT-P?\d{2,3}\b")
for path in sys.argv[1:]:
    try:
        root = ET.parse(path).getroot()
    except (OSError, ET.ParseError) as e:
        print(f"::error title=junit {path}::{e}")
        continue
    passed, failed, skipped = set(), set(), set()
    for case in root.iter("testcase"):
        text = f"{case.get('name', '')} {case.get('classname', '')}"
        ids = set(ID.findall(text)) | {f"T-P{m}" for m in re.findall(r"\btest_P(\d{2})", text)} \
            | {f"T-{m}" for m in re.findall(r"\btest_T(\d{3})", text)}
        bad = list(case.findall("failure")) + list(case.findall("error"))
        skip = case.find("skipped") is not None
        (failed if bad else skipped if skip else passed).update(ids or {case.get("name", "?")[:40]})
    passed -= failed | skipped
    skipped -= failed
    print(f"::notice title=test-summary {path}::passed: {' '.join(sorted(passed)) or '-'} | failed: {' '.join(sorted(failed)) or '-'} | skipped: {' '.join(sorted(skipped)) or '-'}")
    for case in root.iter("testcase"):
        for bad in list(case.findall("failure")) + list(case.findall("error")):
            msg = (bad.get("message") or bad.text or "").strip().splitlines()
            print(f"::error title={(case.get('name') or '?')[:120].replace(':', ' ')}::{(msg[0] if msg else 'failed')[:300]}")
