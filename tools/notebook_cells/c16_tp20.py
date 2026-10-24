# (16) T-P20 in the real environment (D-017). A failure inside the test's own assertions is a result, not a stop (R-071, R-099).
def _is_result(xml_path):
    import xml.etree.ElementTree as ET
    for case in ET.parse(xml_path).getroot().iter("testcase"):
        if case.get("name") == "test_P20_evaluation_procedure_produces_a_complete_measured_report":
            kids = list(case)
            if len(kids) == 1 and kids[0].tag == "failure":
                last = [l for l in (kids[0].text or "").splitlines() if l.strip()][-1].strip()
                return re.fullmatch(r"tests/python/test_evaluate\.py:\d+: AssertionError", last) is not None
    return False


def _t_p20():
    for key, path in (("SINGVST_VOICE", f"{RUNDIR}/out/voice"), ("SINGVST_HELDOUT", f"{RUNDIR}/heldout"),
                      ("SINGVST_RENDER_BIN", f"{LOCAL}/bin/singvst-render")):
        os.environ[key] = path
        if not Path(path).exists():
            raise RuntimeError(f"{key} points to a path that does not exist: {path}")
    xml = f"{RUNDIR}/out/eval/t-p20.xml"
    box = {}
    timed("t-p20", lambda: box.update(rc=sh(f"python -m pytest -q -m voice tests/python/test_evaluate.py --junitxml={shlex.quote(xml)}", SINGVST)[0]))
    rc = box["rc"]
    if rc == 0:
        print("T-P20 passed")
    elif rc == 1 and Path(xml).exists() and _is_result(xml):
        print("T-P20 failed inside its own assertions: that is a result for gate G-001, not a stop")
    else:
        raise RuntimeError(f"the T-P20 run itself failed (pytest exit {rc})")


guarded(16, _t_p20)
