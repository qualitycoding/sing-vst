#!/usr/bin/env bash
# Usage: bash run.sh <JUCE 9.0.3 dir> <python with mido 1.3.3> <build dir>
set -euo pipefail
J=${1:?juce}; PY=${2:?python}; B=${3:?build}; HERE=$(cd "$(dirname "$0")" && pwd)
"$PY" -I "$HERE/make_mid.py" "$B.mid"
cmake -S "$HERE" -B "$B" -DCMAKE_BUILD_TYPE=Release -DJUCE_DIR="$J" > "$B.cfg.log"
cmake --build "$B" -j2 > "$B.build.log"
"$B/LyricSpike_artefacts/Release/LyricSpike" "$B.mid"
