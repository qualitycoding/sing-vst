"""Prints a GitHub ::error:: annotation for every failed or errored test case in JUnit XML files (D-018, PK-14), so
failures are readable through the check-run annotations API. Usage: python tools/ci_annotate.py <junit.xml>..."""
import sys
import xml.etree.ElementTree as ET

n = 0
for path in sys.argv[1:]:
    try:
        root = ET.parse(path).getroot()
    except (OSError, ET.ParseError) as e:
        print(f"::error title=junit::{path}: {e}")
        n += 1
        continue
    for case in root.iter("testcase"):
        for bad in list(case.findall("failure")) + list(case.findall("error")):
            msg = (bad.get("message") or bad.text or "").strip().splitlines()
            title = (case.get("name") or "?")[:120].replace(":", " ")
            print(f"::error title={title}::{(msg[0] if msg else 'failed')[:300]}")
            n += 1
print(f"{n} failing test case(s) annotated")
