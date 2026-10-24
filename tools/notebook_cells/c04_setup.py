# (4) Setup, in exactly this order (R-051). Stops the owner can fix print an `owner:` line first.
q = shlex.quote
# (a) the exact commits of sing-vst and RVC
for url, path, commit in (("https://github.com/qualitycoding/sing-vst", SINGVST, EXPECTED_COMMIT),
                          ("https://github.com/RVC-Project/Retrieval-based-Voice-Conversion-WebUI.git", RVC, RVC_COMMIT)):
    if not Path(path, ".git").exists():
        _sh_ok(f"git clone -q {url} {q(path)}", "/")
    _sh_ok(f"git -C {q(path)} fetch -q origin && git -C {q(path)} checkout -q {commit}", "/")
head = _sh_ok(f"git -C {q(SINGVST)} rev-parse HEAD", "/").strip().splitlines()[-1]
if head != EXPECTED_COMMIT:
    owner_stop("4a", f"sing-vst is at {head}, not EXPECTED_COMMIT {EXPECTED_COMMIT}: fix EXPECTED_COMMIT as GATE-G-004.md states")
sys.path.insert(0, f"{SINGVST}/python")           # pipeline.py is standard-library only

# (b) the Python 3.12 venv; each package name comes from exactly one index (R-020, C-062)
Path(LOCAL).mkdir(parents=True, exist_ok=True)
_sh_ok(f"{q(sys.executable)} -m pip install -q uv==0.13.1", "/")
_sh_ok(f"{q(sys.executable)} -m uv venv --python 3.12 --python-preference only-managed {q(VENV)}", "/")
os.environ["PATH"] = f"{VENV}/bin:" + os.environ["PATH"]
UV = f"{q(sys.executable)} -m uv pip install --python {q(VENV)}/bin/python"
_sh_ok(f"{UV} --index-url https://download.pytorch.org/whl/cu128 torch==2.7.1+cu128 torchaudio==2.7.1+cu128", "/")
_sh_ok(f"grep -vE -- '--(extra-)?index-url' {q(RVC)}/requirments_cu128_py312.txt > {q(LOCAL)}/rvc-req.txt", "/")
_sh_ok(f"{UV} --index-url https://pypi.org/simple -r {q(LOCAL)}/rvc-req.txt", "/")
_sh_ok(f"{q(sys.executable)} -m uv pip uninstall --python {q(VENV)}/bin/python onnxruntime-gpu onnxruntime || true", "/")
_sh_ok(f"{UV} --index-url https://pypi.org/simple onnx==1.23.2 onnxruntime==1.31.0 pyworld==0.3.5 mido==1.3.3 pytest==9.1.1 "
       "nbformat==5.10.4 PyYAML==6.0.3 openai-whisper==20250625 webrtcvad-wheels==2.0.14", "/")
_sh_ok(f"{UV} --index-url https://pypi.org/simple resemblyzer==0.1.4 --no-deps", "/")
_sh_ok(f"{UV} -e {q(SINGVST)}/python --no-deps", "/")
if DEREVERB:                                       # its own venv: audio-separator needs numpy >= 2, RVC needs < 2 (D-025, C-066)
    SEP = f"{LOCAL}/sep"
    _sh_ok(f"{q(sys.executable)} -m uv venv --python 3.12 --python-preference only-managed {q(SEP)}", "/")
    _sh_ok(f"{q(sys.executable)} -m uv pip install --python {q(SEP)}/bin/python --index-url https://download.pytorch.org/whl/cu128 "
           "torch==2.7.1+cu128 torchaudio==2.7.1+cu128", "/")
    _sh_ok(f"{q(sys.executable)} -m uv pip install --python {q(SEP)}/bin/python --index-url https://pypi.org/simple audio-separator==0.47.0", "/")
    os.environ["SINGVST_SEPARATOR_PYTHON"] = f"{SEP}/bin/python"

# (c) the GPU's compute capability must be one this torch build supports (R-044)
rc, out = sh("python -c \"import torch; a = torch.cuda.get_arch_list(); c = torch.cuda.get_device_capability(0); "
             "s = 'sm_%d%d' % c; print('arch', a, 'device', s); raise SystemExit(0 if s in a else 7)\"", "/")
if rc != 0:
    owner_stop("4c", "this GPU's compute capability is not supported by the installed torch (see the arch line above): choose a T4 or newer")

# (d) Colab only: mount Drive. Nothing is written under /content/drive before this point.
if PLATFORM == "colab":
    from google.colab import drive
    drive.mount("/content/drive")

# (e) directories, parameters, freeze and environment files, then the session entry and the heartbeat
make_dirs()
write_params()
_sh_ok(f"{q(sys.executable)} -m uv pip freeze --python {q(VENV)}/bin/python > {q(RUNDIR)}/out/env/{SESSION}.freeze.txt", "/")
_sh_ok(f"python - <<'PY' > {q(RUNDIR)}/out/env/{SESSION}.json\n"
       "import json, platform, subprocess, torch\n"
       "drv = subprocess.run(['nvidia-smi', '--query-gpu=driver_version', '--format=csv,noheader'], capture_output=True, text=True).stdout.strip()\n"
       f"print(json.dumps({{'python': platform.python_version(), 'torch': torch.__version__, 'cuda': torch.version.cuda, "
       f"'gpu': torch.cuda.get_device_name(0), 'driver': drv, 'image': '{PLATFORM}'}}, indent=1))\nPY", "/")
start_session()

# (f) build singvst-render on local disk, never on Drive (R-052); a failure stops the run before GPU time is spent (R-023)
try:
    _sh_ok("g++ --version", "/")
    _sh_ok(f"cmake -S {q(SINGVST)} -B {q(LOCAL)}/build-render -DCMAKE_BUILD_TYPE=Release -DSINGVST_BUILD_PLUGIN=OFF -DSINGVST_BUILD_TESTS=OFF "
           f"&& cmake --build {q(LOCAL)}/build-render --target singvst-render --parallel 4", "/")
    out = _sh_ok(f"{q(LOCAL)}/build-render/cli/singvst-render --check-voice {q(SINGVST)}/tests/fixtures/voice-convert", "/")
    assert out.strip().splitlines()[-1].startswith("ok "), out
except BaseException:
    close_session_entry()
    raise
