#!/usr/bin/env bash
# Spike (C-046): which setuptools versions carry a known advisory? Usage: bash run.sh <empty dir> <python3.12> > output.txt 2>&1
set -u
W=${1:?dir}; PY=${2:?python3.12}; "$PY" -m venv "$W/v"; "$W/v/bin/python" -m pip install -q pip-audit==2.10.1 2>&1 | grep -vi notice
for v in 80.9.0 84.0.0; do
  printf 'setuptools==%s\n' "$v" > "$W/req-$v.txt"
  echo "== pip-audit setuptools==$v"; "$W/v/bin/pip-audit" -r "$W/req-$v.txt" --no-deps --disable-pip 2>&1 | grep -v '^WARNING'
done
