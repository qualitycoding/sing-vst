#!/usr/bin/env bash
# Spike (C-067, pass-10 cold read item 20): what pytest's junit XML records for T-P20's own assertion failures versus
# need_env assertions and exceptions, so D-035 §Evaluation outcome can classify t-p20.xml mechanically.
# Usage: bash run.sh <python with pytest 9.1.1> <empty dir>  > output.txt 2>&1
set -u
PY=${1:?python}; W=${2:?dir}; HERE=$(cd "$(dirname "$0")" && pwd)
cp -r "$HERE/case/tests" "$W/"
echo "== $("$PY" -m pytest --version 2>&1)"
(cd "$W" && "$PY" -m pytest -q -p no:cacheprovider tests/python/test_evaluate.py --junitxml=o.xml >/dev/null)
"$PY" -I - "$W/o.xml" <<'PY'
import re, sys, xml.etree.ElementTree as ET
rule = re.compile(r"^tests/python/test_evaluate\.py:\d+: AssertionError$")
for tc in ET.parse(sys.argv[1]).iter("testcase"):
    for f in tc:
        last = [l for l in (f.text or "").splitlines() if l.strip()][-1].strip()
        print(f"{tc.get('name')}: <{f.tag}> message={f.get('message').splitlines()[0]!r} last={last!r} result={bool(f.tag == 'failure' and rule.match(last))}")
PY
