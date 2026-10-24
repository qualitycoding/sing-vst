# (17) Finish: stop the heartbeat, write the budget a final time, build the tars. The finally block always runs end_session().
try:
    if STOP:
        print("skipped - start a new session")
    else:
        if HEARTBEAT is None or not HEARTBEAT.is_alive() or HEARTBEAT_ERROR is not None:
            raise RuntimeError(f"the budget heartbeat is not running: {HEARTBEAT_ERROR!r}")
        close_session_entry()
        run = Path(RUNDIR)
        _sh_ok(f"tar -C {shlex.quote(str(run / 'out'))} -cf {shlex.quote(ROOT)}/out-run{RUN}.tar .", "/")
        upload = Path(ROOT) / f"upload-run{RUN}.tar"
        with tarfile.open(upload, "w") as tf:
            for name in ("report.json", "report.json.provenance.json", "verdict.json", "spread.json", "ceiling.json", "t-p20.xml"):
                if (run / "out" / "eval" / name).exists():
                    tf.add(run / "out" / "eval" / name, arcname=name)
            for src, name in ((run / "out" / "budget.json", "budget.json"), (run / "out" / "training.json", "training.json"),
                              (Path(ROOT) / "budget-voice.json", "budget-voice.json"), (run / "state" / "commits.json", "commits.json"),
                              (run / "out" / "env", "env")):
                if src.exists():
                    tf.add(src, arcname=name)
        print(f"{_sha256_file(upload)}  upload-run{RUN}.tar")
        print_hours()
finally:
    end_session()
