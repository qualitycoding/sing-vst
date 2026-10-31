#!/usr/bin/env bash
# 1.3.6 spike for S-REVIEW's coverage commands (plan/AMENDMENT-02.md, D-042).
# Usage (repository root): bash research/spikes/coverage/run.sh <impl checkout> > research/spikes/coverage/output.txt 2>&1
# C++: core built with GCC 13.3 --coverage in <impl>/../build-cov, ctest, then gcov -n per object file (summary only, no .gcov files).
# Python: coverage.py 7.17.0 from python/requirements-mutate.txt on top of the lock (pytest 9.1.1), the local suite as in HANDOFF.
set -euo pipefail
IMPL=$(cd "${1:?path to an impl-branch checkout}" && pwd); PLAN=$(cd "$(dirname "$0")/../../.." && pwd); D=$HOME/deps
echo "== C++ core with --coverage"
cmake -S "$IMPL" -B "$IMPL/../build-cov" -G Ninja -Wno-dev -DCMAKE_BUILD_TYPE=Debug -DSINGVST_BUILD_PLUGIN=OFF \
  -DFETCHCONTENT_SOURCE_DIR_CATCH2="$D/Catch2" -DSINGVST_ORT_DIR="$D/ort" -DCMAKE_CXX_FLAGS=--coverage -DCMAKE_EXE_LINKER_FLAGS=--coverage > /dev/null
cmake --build "$IMPL/../build-cov" --parallel 2 > /dev/null
LOCPATH=$HOME/locale ctest --test-dir "$IMPL/../build-cov" 2>&1 | grep 'tests passed'
O="$IMPL/../build-cov/core/CMakeFiles/singvst_core.dir/src"
(cd "$O" && gcov -n *.gcda 2>/dev/null) | awk '/^File .*core\/src\//{f=$2} /^Lines executed/{if (f) {print f, $0; f=""}}' | sed "s|'||g; s|$IMPL/||"
echo "== Python toolkit with coverage.py"
W=$(mktemp -d); trap 'rm -rf "$W"' EXIT
/usr/bin/python3.12 -m venv "$W/v"; "$W/v/bin/pip" install -q --no-deps -r "$IMPL/python/requirements-lock.txt" -r "$PLAN/python/requirements-mutate.txt"
"$W/v/bin/python" -c "import coverage, pytest; print('coverage', coverage.__version__, 'pytest', pytest.__version__)"
cd "$IMPL" && SINGVST_RENDER_BIN="$IMPL/../build-core/cli/singvst-render" "$W/v/bin/python" -m coverage run --data-file="$W/.coverage" \
  --source=python/singvst_train -m pytest -q -p no:cacheprovider -m "not torch and not voice and not network" tests/python 2>&1 | grep -E "^FAILED|passed|failed" || true   # coverage is measured whatever the outcome; failures are listed
"$W/v/bin/python" -m coverage report --data-file="$W/.coverage" | tail -14
