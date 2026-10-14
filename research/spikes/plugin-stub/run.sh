#!/usr/bin/env bash
# Spike (C-050, C-051): JUCE 9.0.3 plugin stub builds on Ubuntu 24.04 with JUCE's documented Linux packages; the runtime files
# sit beside the binary in the VST3 bundle; pluginval 1.0.4 strictness 5 passes on the silent stub.
# Usage: bash run.sh <repo> <deps dir from tools/bootstrap_test_env.sh> <build dir> <pluginval zip dir>  > output.txt 2>&1
set -u
R=${1:?repo}; D=${2:?deps}; B=${3:?build}; P=${4:?pluginval dir}
echo "== packages (JUCE docs/Linux Dependencies.md, JUCE_USE_CURL=0, JUCE_WEB_BROWSER=0)"
for p in libasound2-dev libjack-jackd2-dev libfreetype-dev libfontconfig1-dev libx11-dev libxcomposite-dev libxcursor-dev libxext-dev libxinerama-dev libxrandr-dev libxrender-dev libxi-dev libglu1-mesa-dev mesa-common-dev libegl-dev xvfb; do
  printf '%s %s\n' "$p" "$(dpkg-query -W -f='${Version}' "$p" 2>/dev/null || echo MISSING)"; done
cmake -S "$R" -B "$B" -G Ninja -DCMAKE_BUILD_TYPE=Release -DSINGVST_BUILD_TESTS=OFF -DFETCHCONTENT_SOURCE_DIR_JUCE="$D/JUCE" -DSINGVST_ORT_DIR="$D/ort" > "$B.cfg.log" 2>&1 && cmake --build "$B" -j2 > "$B.build.log" 2>&1
echo "== build exit $?"
V="$B/plugin/SingVst_artefacts/Release/VST3/Sing VST.vst3"
echo "== bundle"; (cd "$V/.." && find "Sing VST.vst3" | sort)
echo "== pluginval $(sha256sum "$P/pluginval_Linux.zip" | cut -c1-16)…"; unzip -o -q "$P/pluginval_Linux.zip" -d "$P/pv"
xvfb-run -a "$P/pv/pluginval" --strictness-level 5 --skip-gui-tests --validate "$V" 2>&1 | grep -E "^(Starting tests|SUCCESS|FAILURE|!!!)" ; echo "== pluginval exit ${PIPESTATUS[0]}"
