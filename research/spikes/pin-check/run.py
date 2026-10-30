"""1.3.6 pin-existence check (plan/AMENDMENT-01.md AM-06). Usage: python3.12 research/spikes/pin-check/run.py > research/spikes/pin-check/output.txt
Looks every pin up in its registry: PyPI JSON API, the PyTorch wheel indexes, GitHub tags/releases (commit recorded for git tags), Hugging Face.
Exit 1 when any pin does not exist. Standard library plus the `gh` CLI (for GitHub, authenticated)."""
import json, re, subprocess, sys, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
fails = []


def say(kind, pin, ok, detail):
    print(f"{'exists ' if ok else 'MISSING'} {kind:<9} {pin:<58} {detail}")
    if not ok:
        fails.append(pin)


def http(url, method="GET"):
    req = urllib.request.Request(url, method=method, headers={"User-Agent": "sing-vst-pin-check"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, (r.read() if method == "GET" else b"")
    except urllib.error.HTTPError as e:
        return e.code, b""


def pypi(name, version, why):
    code, body = http(f"https://pypi.org/pypi/{name}/{version}/json")
    if code == 200:
        info = json.loads(body)
        files = len(info.get("urls", []))
        yanked = any(u.get("yanked") for u in info.get("urls", []))
        say("pypi", f"{name}=={version}", files > 0 and not yanked, f"{files} files{' YANKED' if yanked else ''}; {why}")
    else:
        say("pypi", f"{name}=={version}", False, f"HTTP {code}; {why}")


def torch_index(index, name, version, why):
    code, body = http(f"https://download.pytorch.org/whl/{index}/{name}/")
    tag = version.replace("+", "%2B")
    hits = sorted(set(re.findall(rf"{name}-{re.escape(tag)}-cp312-cp312-(manylinux[^\"#]*?|linux[^\"#]*?)\.whl", body.decode("utf-8", "replace"))))
    say("pytorch", f"{name}=={version} ({index})", code == 200 and bool(hits), f"cp312 Linux wheels: {len(hits)}; {why}")


def gh_tag(repo, tag, want=None, why=""):
    r = subprocess.run(["gh", "api", f"repos/{repo}/git/ref/tags/{tag}"], capture_output=True, text=True)
    if r.returncode != 0:
        say("git tag", f"{repo}@{tag}", False, f"no such tag; {why}")
        return
    obj = json.loads(r.stdout)["object"]
    sha = obj["sha"]
    if obj["type"] == "tag":   # annotated: dereference to the commit
        sha = json.loads(subprocess.run(["gh", "api", f"repos/{repo}/git/tags/{sha}"], capture_output=True, text=True).stdout)["object"]["sha"]
    ok = want is None or sha.startswith(want)
    say("git tag", f"{repo}@{tag}", ok, f"commit {sha}{'' if ok else ' != pinned ' + want}; {why}")


def gh_commit(repo, sha, why):
    r = subprocess.run(["gh", "api", f"repos/{repo}/commits/{sha}", "--jq", ".sha"], capture_output=True, text=True)
    say("git sha", f"{repo}@{sha[:12]}", r.returncode == 0 and r.stdout.strip().startswith(sha), why)


def asset(url, why):
    code, _ = http(url, method="HEAD")
    say("release", url.split("/download/")[-1] if "/download/" in url else url, code == 200, f"HTTP {code}; {why}")


# ---- plan/ENVIRONMENT.md
gh_tag("juce-framework/JUCE", "9.0.3", "be29c81492b6151c8ea8d14c840e1311963b3a83", "JUCE (C-012)")
gh_tag("catchorg/Catch2", "v3.16.1", "08092139210881f01a34e60c5f2fd6afa0ea4024", "Catch2 (C-045)")
asset("https://github.com/nlohmann/json/releases/download/v3.12.0/json.tar.xz", "nlohmann/json (C-049)")
asset("https://github.com/microsoft/onnxruntime/releases/download/v1.31.0/onnxruntime-linux-x64-1.31.0.tgz", "ONNX Runtime Linux (D-002)")
asset("https://github.com/microsoft/onnxruntime/releases/download/v1.31.0/onnxruntime-win-x64-1.31.0.zip", "ONNX Runtime Windows (D-002)")
asset("https://github.com/Tracktion/pluginval/releases/download/v1.0.4/pluginval_Linux.zip", "pluginval (C-015)")
asset("https://github.com/Tracktion/pluginval/releases/download/v1.0.4/pluginval_Windows.zip", "pluginval (C-015)")
gh_commit("cmusphinx/cmudict", "74790861f652b15e4ac49015a90074ad62a27690", "CMUdict (C-016)")
gh_commit("RVC-Project/Retrieval-based-Voice-Conversion-WebUI", "81eed5e8f68b6bed1789f682fe78cdd324495afc", "RVC (C-001, C-022)")
code, body = http("https://huggingface.co/api/models/lj1995/VoiceConversionWebUI/revision/e6d0c1a17da07c33557852f9dfa2bd44cc75737d")
say("hf", "lj1995/VoiceConversionWebUI@e6d0c1a1", code == 200, f"HTTP {code}; RVC assets (C-032, S-013)")
for action, tag in (("actions/checkout", "v7"), ("actions/setup-python", "v7"), ("actions/upload-artifact", "v7"), ("actions/download-artifact", "v8")):
    gh_tag(action, tag, why="GitHub Action (C-045)")
for line in (ROOT / "python" / "requirements-lock.txt").read_text().splitlines():
    if line and not line.startswith("#"):
        name, version = line.split("==")
        pypi(name, version, "toolkit lock (D-019)")
pypi("huggingface_hub", "2.2.0", "download venv (C-054)")
# ---- notebook installs (D-035 §Notebook environment)
pypi("uv", "0.13.1", "notebook (C-060)")
torch_index("cu128", "torch", "2.7.1+cu128", "notebook (C-062)")
torch_index("cu128", "torchaudio", "2.7.1+cu128", "notebook (C-062)")
for name, version in (("onnx", "1.23.2"), ("onnxruntime", "1.31.0"), ("pyworld", "0.3.5"), ("mido", "1.3.3"), ("pytest", "9.1.1"),
                      ("nbformat", "5.10.4"), ("PyYAML", "6.0.3"), ("openai-whisper", "20250625"), ("webrtcvad-wheels", "2.0.14"),
                      ("resemblyzer", "0.1.4"), ("audio-separator", "0.47.0")):
    pypi(name, version, "notebook (D-035)")
asset("https://github.com/spicytigermeat/tiger_diffsinger/releases/download/v102/TIGER_DS_v102_PACK.zip", "TIGER guide (C-036, G-005)")
# ---- CI python-torch job: RVC's CPU requirement file
for name, version in (("torch", "2.4.1+cpu"), ("torchaudio", "2.4.1+cpu"), ("torchvision", "0.19.1+cpu")):
    torch_index("cpu", name, version, "CI python-torch (D-019)")

print(f"\n{len(fails)} missing")
sys.exit(1 if fails else 0)
