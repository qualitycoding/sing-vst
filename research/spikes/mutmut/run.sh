#!/usr/bin/env bash
# 1.3.6 spike for S-MUTATE (plan/AMENDMENT-02.md, D-044): mutmut 3.8.1 on the toolkit, with its configuration.
# Usage (repository root): bash research/spikes/mutmut/run.sh <impl checkout>   (pins from this checkout: python/requirements-mutate.txt) > research/spikes/mutmut/output.txt 2>&1
# mutmut 3 maps mutants by module name and needs the package at ./, src/ or source/; the frozen conftest adds python/ to sys.path,
# so the run uses a generated workspace: src/singvst_train (copy), tests/python and tests/fixtures (copies, unchanged), eval/,
# and a `python` -> `src` link for T-P25's subprocess. Scope = D-044.
set -euo pipefail
IMPL=${1:?path to an impl-branch checkout}; PLAN=$(cd "$(dirname "$0")/../../.." && pwd); W=$(mktemp -d); trap 'rm -rf "$W"' EXIT
/usr/bin/python3.12 -m venv "$W/v"
"$W/v/bin/pip" install -q --no-deps -r "$IMPL/python/requirements-lock.txt"
"$W/v/bin/pip" install -q --no-deps -r "$PLAN/python/requirements-mutate.txt"   # pinned closure; keeps the lock's pytest
"$W/v/bin/pip" check
"$W/v/bin/python" -c "import pytest; print('pytest', pytest.__version__)"
"$W/v/bin/python" -m pip show mutmut | grep -E '^(Name|Version)'
mkdir -p "$W/work/src" "$W/work/tests"
cp -r "$IMPL/python/singvst_train" "$W/work/src/"; cp -r "$IMPL/tests/python" "$IMPL/tests/fixtures" "$W/work/tests/"; cp -r "$IMPL/eval" "$W/work/"
# The frozen conftest inserts <root>/python first: keep it a package-free directory holding only what tests read there (the lock,
# T-P08b) and mutmut's config (a T-P25 child process runs from it and the mutated code loads the config from its cwd); the child
# finds the mutated package through a .pth file pointing at mutants/src; T-P08b also needs a git commit at the root.
mkdir -p "$W/work/python"; cp "$IMPL/python/requirements-lock.txt" "$W/work/python/"; cp "$IMPL/pytest.ini" "$W/work/"
echo "$W/work/mutants/src" > "$("$W/v/bin/python" -c 'import site; print(site.getsitepackages()[0])')/singvst-mutants.pth"
git -C "$W/work" init -q && git -C "$W/work" -c user.name=mutate -c user.email=mutate@localhost commit -q --allow-empty -m workspace
cat > "$W/work/setup.cfg" <<'CFG'
[mutmut]
source_paths=
    src/singvst_train/pipeline.py
    src/singvst_train/prepare.py
    src/singvst_train/metrics.py
    src/singvst_train/pack.py
    src/singvst_train/rvc_files.py
    src/singvst_train/security.py
    src/singvst_train/provenance.py
    src/singvst_train/cli.py
pytest_add_cli_args_test_selection=
    tests/python/test_pipeline.py
    tests/python/test_prepare.py
    tests/python/test_metrics.py
    tests/python/test_pack.py
    tests/python/test_rvc_files.py
    tests/python/test_security.py
    tests/python/test_provenance.py
    tests/python/test_cli.py
also_copy=
    pytest.ini
    tests/python
    tests/fixtures
    eval
    python
pytest_add_cli_args=
    -m
    not torch and not voice and not network and not binary
    -p
    no:cacheprovider
CFG
cp "$W/work/setup.cfg" "$W/work/python/"
echo "== setup.cfg"; cat "$W/work/setup.cfg"
cd "$W/work"
"$W/v/bin/mutmut" run > run.log 2>&1
echo "== mutmut run exit 0; last line:"; tail -1 run.log | tr '\r' '\n' | tail -1
echo "== results by status, all modules"
"$W/v/bin/mutmut" results --all true > results.txt
sed -E 's/^.*: //' results.txt | sort | uniq -c
echo "== per module (score = (killed + timeout) / total; 'no tests' = mutated code no selected test reaches)"
printf "%-11s %5s %6s %7s %8s %8s %6s\n" module total killed timeout survived no_tests score
sed -E 's/^ *singvst_train\.([a-z_]+)\..*: (.*)$/\1|\2/' results.txt | awk -F'|' '{t[$1]++; s[$1"|"$2]++} END {for (m in t) {k=s[m"|killed"]+0; to=s[m"|timeout"]+0; sv=s[m"|survived"]+0; nt=s[m"|no tests"]+0; printf "%-11s %5d %6d %7d %8d %8d %6.3f\n", m, t[m], k, to, sv, nt, (k+to)/t[m]}}' | sort
echo "== D-044 gate scope: the seven library modules (cli.py is scored on its own)"
grep -v '^ *singvst_train\.cli\.' results.txt | awk '{n++; if ($NF=="killed" || $NF=="timeout") k++} END {printf "mutants %d, killed+timeout %d, score %.3f\n", n, k, k/n}'
