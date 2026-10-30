#!/usr/bin/env bash
# 1.3.6 command verification for the notebook cells that run without a GPU (plan/AMENDMENT-01.md AM-06).
# Usage (repository root): bash research/spikes/notebook-commands/run.sh > research/spikes/notebook-commands/output.txt 2>&1
# Runs the literal commands of cells (4a), (4b), (5) and (14) with the pinned versions in a scratch directory. The two CUDA package
# sets are resolved with `uv pip install --dry-run` (same flags and index); everything else is executed. Exit 1 on the first failure.
set -euo pipefail
R=$(cd "$(dirname "$0")/../../.." && pwd); W=$(mktemp -d); trap 'rm -rf "$W"' EXIT
step() { echo; echo "== $*"; }
step "kernel python and uv 0.13.1 (cell 4b)"
/usr/bin/python3.12 -m venv "$W/kernel"; K="$W/kernel/bin/python"
"$K" -m pip install -q uv==0.13.1 && "$K" -m uv --version
step "uv venv --python 3.12 --python-preference only-managed (cell 4b)"
"$K" -m uv venv --python 3.12 --python-preference only-managed "$W/py312" 2>&1 | tail -2
"$W/py312/bin/python" -c "import sys; print('venv python', sys.version.split()[0], sys.executable)"
UV="$K -m uv pip install --python $W/py312/bin/python"
step "(i) torch cu128 from the PyTorch index only (dry run)"
$UV --dry-run --index-url https://download.pytorch.org/whl/cu128 torch==2.7.1+cu128 torchaudio==2.7.1+cu128 2>&1 | grep -E 'Would install|torch' | head -4
step "(ii) RVC's cu128 requirement file without its index lines (cell 4b filter; C-062: it lists no torch)"
grep -vE -- '--(extra-)?index-url' "$R/../rvc/requirments_cu128_py312.txt" > "$W/rvc-req.txt"
count() { awk -v re="$1" '$0 ~ re {n++} END {print n + 0}' "$2"; }
echo "lines kept: $(count '^[^#[:space:]]' "$W/rvc-req.txt"); index lines left: $(count 'index-url' "$W/rvc-req.txt")"
echo "torch lines in the file: $(count '^torch(audio|vision)?==' "$W/rvc-req.txt")"
[ "$(count 'index-url' "$W/rvc-req.txt")" -eq 0 ] && [ "$(count '^torch(audio|vision)?==' "$W/rvc-req.txt")" -eq 0 ]
$UV --dry-run --index-url https://pypi.org/simple -r "$W/rvc-req.txt" 2>&1 | grep -E '^Would install|Resolved' | head -2
step "(iii) uninstall whichever onnxruntime provider is installed (cell 4b after AM-04)"
$UV --index-url https://pypi.org/simple onnxruntime==1.31.0 2>&1 | tail -1
"$K" -m uv pip list --python "$W/py312/bin/python" --format json > "$W/list.json"
present=$("$K" -c "import json; print(' '.join(d['name'] for d in json.load(open('$W/list.json')) if d['name'].lower() in ('onnxruntime-gpu', 'onnxruntime')))")
echo "installed providers: $present"
"$K" -m uv pip uninstall --python "$W/py312/bin/python" $present 2>&1 | tail -1
step "(iv) evaluation and export packages from PyPI (dry run, --no-deps for the pins alone)"
$UV --dry-run --no-deps --index-url https://pypi.org/simple onnx==1.23.2 onnxruntime==1.31.0 pyworld==0.3.5 mido==1.3.3 pytest==9.1.1 \
    nbformat==5.10.4 PyYAML==6.0.3 openai-whisper==20250625 webrtcvad-wheels==2.0.14 2>&1 | grep -E 'Would install' | head -1
$UV --dry-run --index-url https://pypi.org/simple resemblyzer==0.1.4 --no-deps 2>&1 | grep -E 'Would install' | head -1
step "(v) the toolkit, editable, without dependencies"
$UV -e "$R/python" --no-deps 2>&1 | tail -1
"$W/py312/bin/python" -c "import singvst_train.cli as c; print('toolkit commands', len(c.COMMANDS))"
step "freeze file (cell 4e)"
"$K" -m uv pip freeze --python "$W/py312/bin/python" > "$W/freeze.txt"; echo "freeze lines: $(wc -l < "$W/freeze.txt")"
step "git clone + checkout of a pinned commit, then rev-parse (cell 4a)"
git clone -q "$R" "$W/sv" && git -C "$W/sv" checkout -q "$(git -C "$R" rev-parse HEAD)" && git -C "$W/sv" rev-parse HEAD
step "python -m zipfile -e, two levels, inner path with a space (cell 14: pack -> 'pack/Voice Library/TIGER_DS_v102.zip' -> tiger)"
PY="$W/py312/bin/python"; Z="$W/vb"; mkdir -p "$Z/src/dsacoustic" "$Z/build/Voice Library"
echo acoustic > "$Z/src/dsacoustic/tiger_acou.onnx"
(cd "$Z/src" && "$PY" -m zipfile -c "../build/Voice Library/TIGER_DS_v102.zip" dsacoustic)
(cd "$Z/build" && "$PY" -m zipfile -c ../TIGER_DS_v102_PACK.zip "Voice Library")
(cd "$Z" && "$PY" -m zipfile -e TIGER_DS_v102_PACK.zip pack && "$PY" -m zipfile -e 'pack/Voice Library/TIGER_DS_v102.zip' tiger)
test -s "$Z/tiger/dsacoustic/tiger_acou.onnx" && echo "extracted: tiger/dsacoustic/tiger_acou.onnx"
step "separate venv for huggingface_hub 2.2.0 and its hf CLI (cell 5)"
/usr/bin/python3.12 -m venv "$W/hfv" && "$W/hfv/bin/pip" install -q huggingface_hub==2.2.0 && "$W/hfv/bin/hf" download --help | grep -E -- '--revision|--include|--local-dir' | head -3
echo; echo "ALL COMMANDS OK"
