# (6) Checks before any GPU stage (R-022): the exporter against the real RVC checkout (T-P19), and the evaluation libraries.
def _checks():
    q = shlex.quote
    _sh_ok(f"SINGVST_RVC_ROOT={q(RVC)} python -m pytest -q -m torch", SINGVST)
    whisper_home = os.path.expanduser("~/.cache/whisper")
    archived("whisper", whisper_home, ["small.en.pt"],
             lambda: _sh_ok("python -c \"import whisper; whisper.load_model('small.en')\"", "/"))
    _sh_ok("python -c \"import resemblyzer, whisper; whisper.load_model('small.en'); print('evaluation libraries ok')\"", "/")


guarded(6, _checks)
