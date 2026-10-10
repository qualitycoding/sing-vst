#!/usr/bin/env bash
# Spike R6 round 3 (C-028, C-043): inspects pinned wheels without installing them. Usage: bash run.sh <empty dir> <pip>
set -euo pipefail
W=${1:?dir}; PIP=${2:?pip}; mkdir -p "$W"
"$PIP" download -q --no-deps resemblyzer==0.1.4 audio-separator==0.47.0 -d "$W"
python3 -I - "$W" <<'PY'
import glob, json, re, sys, zipfile
w = sys.argv[1]
z = zipfile.ZipFile(glob.glob(f"{w}/[Rr]esemblyzer-0.1.4*.whl")[0])
print("resemblyzer wheel listing:", [(i.filename, i.file_size) for i in z.infolist() if i.filename.endswith((".pt", ".pth", ".bin"))])
print("resemblyzer requires:", [l for l in z.read([n for n in z.namelist() if n.endswith("METADATA")][0]).decode().splitlines() if l.startswith("Requires-Dist")])
z = zipfile.ZipFile(glob.glob(f"{w}/audio_separator-0.47.0*.whl")[0])
meta = z.read([n for n in z.namelist() if n.endswith("METADATA")][0]).decode().splitlines()
print("audio-separator wheel inspection:", [l for l in meta if l.startswith(("License:", "Requires-Python"))])
m = json.loads(z.read("audio_separator/models.json"))
print("roformer entry:", m["roformer_download_list"]["Roformer Model: MelBand Roformer | De-Reverb by anvuew"])
s = json.loads(z.read("audio_separator/models-scores.json"))["dereverb_mel_band_roformer_anvuew_sdr_19.1729.ckpt"]
print("score entry stems:", s["stems"], "target:", s["target_stem"])
src = "\n".join(z.read(n).decode(errors="replace") for n in z.namelist() if n.endswith(".py"))
print("download hosts:", sorted(set(re.findall(r"https://github\.com/[A-Za-z0-9_-]+/[A-Za-z0-9_-]+/releases/download/[A-Za-z0-9_.-]+", src))))
PY
