#!/usr/bin/env bash
# S-008 evidence (D-012). Usage (from the repository root, after building ../build-core):  bash research/spikes/s008-external-data/run.sh > research/spikes/s008-external-data/output.txt 2>&1
set -eu
R=$(cd "$(dirname "$0")/../../.." && pwd); B="$R/../build-core"; ORT="${SINGVST_ORT_DIR:-$HOME/deps/ort}"
W=$(mktemp -d); trap 'rm -rf "$W"' EXIT
"$R/../venv-lock/bin/python" -I "$R/research/spikes/s008-external-data/make_external.py" "$R/tests/fixtures/onnx/acoustic_legacy.onnx" "$W/acoustic_external.onnx"
# a complete voice folder whose only difference from the fixture is the external-data acoustic model
mkdir "$W/voice" && cp "$R"/tests/fixtures/onnx/* "$W/voice/" && mv "$W"/acoustic_external.onnx* "$W/voice/"
g++ -std=c++20 -O1 -I"$R/core/include" -I"$ORT/include" -DORT_API_MANUAL_INIT "$R/research/spikes/s008-external-data/check.cpp" "$B/core/libsingvst_core.a" -lpthread -ldl -o "$W/check"
SINGVST_DEBUG_RUNS=1 "$W/check" "$ORT/lib/libonnxruntime.so.1.31.0" "$R/tests/fixtures/onnx" "$W/voice"
echo "exit: $?"
