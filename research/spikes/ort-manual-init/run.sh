#!/usr/bin/env bash
# Usage: bash run.sh <extracted onnxruntime-linux-x64-1.31.0 dir> <python with onnx>
set -euo pipefail
ORT=${1:?ort dir}; PY=${2:?python}; HERE=$(cd "$(dirname "$0")" && pwd); W=$(mktemp -d)
"$PY" -I "$HERE/../ort/make_model.py" "$W/square.onnx"
g++ -std=c++20 -O2 -Wall -Wextra "$HERE/main.cpp" -I"$ORT/include" -ldl -o "$W/spike"   # note: no -lonnxruntime
echo "== ldd (must not list onnxruntime)"; ldd "$W/spike" | grep -c onnxruntime || true
"$W/spike" "$ORT/lib/libonnxruntime.so.1.31.0" "$W/square.onnx"
