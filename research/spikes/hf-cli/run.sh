#!/usr/bin/env bash
# Spike (C-052..C-054): RVC's documented asset downloads, the hf CLI of huggingface_hub 2.2.0, and why it needs its own venv.
# Usage: bash run.sh <RVC checkout at 81eed5e> <empty dir> <python3.12>  > output.txt 2>&1
set -u
R=${1:?rvc}; W=${2:?dir}; PY=${3:?python3.12}
echo "== RVC $(git -C "$R" rev-parse HEAD) README.md download commands"; grep -n 'hf download' "$R/README.md"
"$PY" -m venv "$W/hfv" && "$W/hfv/bin/pip" install -q huggingface_hub==2.2.0 2>&1 | grep -vi notice
echo "== hf version: $("$W/hfv/bin/hf" --version 2>/dev/null | tail -1)"
"$W/hfv/bin/hf" download --help 2>/dev/null | grep -E 'Usage:|--revision|--include|--local-dir' | sed 's/ \{2,\}/ /g'
echo "== RVC CUDA/CPU requirement pins for transformers"; grep -n '^transformers' "$R/requirments_cpu_py312.txt" "$R/requirments_cu128_py312.txt"
echo "== PyPI metadata: transformers 4.49.0 requires_dist (huggingface-hub)"
"$PY" -I - <<'PY'
import json, urllib.request
d = json.load(urllib.request.urlopen("https://pypi.org/pypi/transformers/4.49.0/json", timeout=30))
print([r for r in d["info"]["requires_dist"] if r.lower().startswith("huggingface-hub")])
PY
