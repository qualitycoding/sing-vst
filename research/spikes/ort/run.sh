#!/usr/bin/env bash
# Spike R6-1: ONNX Runtime <ver> prebuilt C++ API from GitHub Releases, g++ / C++20. Prints package SHA-256s for plan/ENVIRONMENT.md.
# Usage: bash run.sh <scratch dir> <ort version> <python with onnx>
set -euo pipefail
W=${1:?scratch}; V=${2:?version}; PY=${3:?python}; HERE=$(cd "$(dirname "$0")" && pwd); mkdir -p "$W"; cd "$W"
for f in onnxruntime-linux-x64-$V.tgz onnxruntime-win-x64-$V.zip; do
  [ -f $f ] || curl -sfL -o $f https://github.com/microsoft/onnxruntime/releases/download/v$V/$f
  echo "sha256 $f $(sha256sum $f | cut -d' ' -f1) size $(stat -c %s $f)"
done
rm -rf ort && mkdir ort && tar xzf onnxruntime-linux-x64-$V.tgz -C ort --strip-components 1
echo "licence: $(head -1 ort/LICENSE)"; ls ort/lib
"$PY" -I "$HERE/make_model.py" square.onnx
g++ -std=c++20 -O2 -Wall -Wextra "$HERE/main.cpp" -Iort/include -Lort/lib -lonnxruntime -Wl,-rpath,"$PWD/ort/lib" -o spike
./spike square.onnx
