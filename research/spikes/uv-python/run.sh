#!/usr/bin/env bash
# Spike (C-060): a pinned uv creates a Python 3.12 venv independent of the host Python (for the hosted notebooks, D-035).
# Usage: bash run.sh <empty dir> <any python3> <uv version>  > output.txt 2>&1
set -u
W=${1:?dir}; PY=${2:?python}; V=${3:?uv version}; mkdir -p "$W"
"$PY" -m venv "$W/boot" && "$W/boot/bin/pip" install -q "uv==$V" 2>&1 | grep -vi notice
echo "== uv $("$W/boot/bin/uv" --version)"
UV_PYTHON_INSTALL_DIR="$W/pythons" "$W/boot/bin/uv" venv --python 3.12 --python-preference only-managed "$W/py312" 2>&1 | tail -3
"$W/py312/bin/python" -c "import sys; print('venv python', sys.version.split()[0])"
"$W/boot/bin/uv" pip install --python "$W/py312/bin/python" -q pyworld==0.3.5 numpy==1.26.4 2>&1 | tail -2
"$W/py312/bin/python" -c "import numpy; print('numpy', numpy.__version__)"
