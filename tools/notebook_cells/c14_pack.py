# (14) The guide voicebank (TIGER DiffSinger v102, G-005 `use-tiger`: personal non-commercial use, never committed or redistributed), then the voice package.
def _voicebank_and_pack():
    q = shlex.quote
    vb = Path(ROOT) / "voicebank"
    if not (vb / "tiger" / "dsacoustic" / "tiger_acou.onnx").exists():
        def download():
            vb.mkdir(parents=True, exist_ok=True)
            _sh_ok(f"curl -fL -o {q(str(vb))}/TIGER_DS_v102_PACK.zip {q(TIGER_URL)}", "/")
        archived("tiger", str(vb), ["TIGER_DS_v102_PACK.zip"], download)
        assert _sha256_file(vb / "TIGER_DS_v102_PACK.zip") == TIGER_SHA256, "TIGER pack SHA-256 mismatch"
        _sh_ok(f"python -m zipfile -e TIGER_DS_v102_PACK.zip pack && python -m zipfile -e 'pack/Voice Library/TIGER_DS_v102.zip' tiger", vb)
    run_cell(14)


guarded(14, _voicebank_and_pack)
