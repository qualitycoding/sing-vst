#!/usr/bin/env bash
# Phase 2B.5 red verification (PK-25). Usage: bash run.sh <repo> <core build dir> <full build dir> <python venv>  > output.txt 2>&1
# Builds come from tools/bootstrap_test_env.sh configure lines (core: SINGVST_BUILD_PLUGIN=OFF; full: plugin + tests).
set -u
R=${1:?repo}; C=${2:?core build}; F=${3:?full build}; PY=${4:?python}
echo "== repo $(git -C "$R" rev-parse --short HEAD)"
echo "== C++ core (singvst_tests)"; cmake --build "$C" > /dev/null 2>&1; echo "build exit $?"
T="$C/tests/cpp/singvst_tests"; "$T" --reporter compact 2>&1 | grep -E '^(test cases|assertions)'
echo "-- failure causes"; "$T" --reporter compact 2>&1 | grep -oE 'not implemented: [A-Za-z_:~=<>]+' | sort | uniq -c | sort -rn
echo "-- failures not caused by NotImplemented (expected: softClip only, a noexcept stub returning 1e9)"
"$T" --reporter compact 2>&1 | grep -E 'failed' | grep -v 'not implemented' | grep -v '^test cases' | grep -v '^assertions' | sed -E 's/:[0-9]+:.*for: .*//' | sort | uniq -c
echo "== C++ plugin (singvst_plugin_tests, xvfb)"; cmake --build "$F" --target singvst_plugin_tests > /dev/null 2>&1; echo "build exit $?"
P="$F/tests/cpp/singvst_plugin_tests"; (cd "$(dirname "$P")" && xvfb-run -a ./singvst_plugin_tests --reporter compact 2>&1 | grep -E '^(test cases|assertions)')
echo "== CLI stub"; "$C/cli/singvst-render" --check-voice "$R/tests/fixtures/voice-convert"; echo "exit $?"
echo "== Python (not torch, not voice; SINGVST_RENDER_BIN = core stub CLI)"
cd "$R" && SINGVST_RENDER_BIN="$C/cli/singvst-render" "$PY" -I -m pytest -q -m "not torch and not voice" -rA 2>&1 | grep -E '^(PASSED|FAILED)|passed|failed' | sed -E 's/ - .*//'
echo "-- failure causes"
SINGVST_RENDER_BIN="$C/cli/singvst-render" "$PY" -I -m pytest -q -m "not torch and not voice and not network" --tb=line 2>&1 | grep -E '^/.*(Error|assert)' | sed -E 's#^/[^ ]*/##; s/:[0-9]+:/:/; s/\(written by.*//' | cut -c1-110 | sort | uniq -c | sort -rn
