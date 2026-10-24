# (5) RVC assets, from Hugging Face revision RVC_ASSETS_REVISION with the huggingface_hub 2.2.0 CLI (C-052, C-054), archived on persistent storage (R-042).
def _guarded_assets():
    q = shlex.quote
    hfv = f"{LOCAL}/hfv"
    hf, rev = f"{hfv}/bin/hf", RVC_ASSETS_REVISION

    def hf_env():
        if not Path(hf).exists():
            _sh_ok(f"python3 -m venv {q(hfv)} && {q(hfv)}/bin/pip install -q huggingface_hub==2.2.0", "/")

    def dl_hubert():
        hf_env()
        _sh_ok(f'{hf} download lj1995/VoiceConversionWebUI --revision {rev} --include "hubert_base/*" --local-dir assets', RVC)

    def dl_rmvpe():
        hf_env()
        _sh_ok(f"{hf} download lj1995/VoiceConversionWebUI rmvpe.pt --revision {rev} --local-dir assets/rmvpe", RVC)

    def dl_pretrained():
        hf_env()
        _sh_ok(f'{hf} download lj1995/VoiceConversionWebUI --revision {rev} --include "pretrained/*" "pretrained_v2/*" --local-dir assets', RVC)

    def dl_mute():
        hf_env()
        _sh_ok(f"{hf} download lj1995/VoiceConversionWebUI mute.zip --revision {rev} --local-dir .model-downloads "
               "&& python -m zipfile -e .model-downloads/mute.zip logs", RVC)

    archived("hubert_base", RVC, ["assets/hubert_base"], dl_hubert)
    archived("rmvpe", RVC, ["assets/rmvpe"], dl_rmvpe)
    archived("pretrained", RVC, ["assets/pretrained", "assets/pretrained_v2"], dl_pretrained)
    archived("mute", RVC, ["logs/mute"], dl_mute)
    for rel in ("assets/hubert_base/config.json", "assets/rmvpe/rmvpe.pt", "assets/pretrained_v2/f0G48k.pth", "logs/mute"):
        assert (Path(RVC) / rel).exists(), f"missing after step (5): {rel}"
    print("RVC assets ready")


guarded(5, _guarded_assets)
