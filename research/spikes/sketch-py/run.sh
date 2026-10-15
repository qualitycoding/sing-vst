#!/usr/bin/env bash
# Spike PK-21/PK-22: overlay sketch_impl.py onto a copy of the repository (stub docstrings kept, so T-P27 still applies)
# and run the frozen Python suite there. Usage: bash run.sh <repo> <python3.12 venv with the lock> <work dir>  > output.txt
set -u
R=${1:?repo}; PY=${2:?python}; W=${3:?work dir}; D=$(cd "$(dirname "$0")" && pwd)
rm -rf "$W"; mkdir -p "$W"; git -C "$R" archive HEAD | tar -x -C "$W"; cp -r "$R/.git" "$W/.git"
cp "$D/sketch_impl.py" "$W/python/singvst_train/_sketch_impl.py"
for m in prepare pipeline provenance metrics pack security rvc_files evaluate cli; do
  cat >> "$W/python/singvst_train/$m.py" <<PY

# ---- sketch overlay (research/spikes/sketch-py) ----
from singvst_train import _sketch_impl as _s
for _n, _v in list(globals().items()):
    if callable(_v) and getattr(_v, "__module__", "") == __name__ and hasattr(_s, _n) and not isinstance(_v, type):
        _f = getattr(_s, _n); _f.__doc__ = _v.__doc__; _f.__module__ = __name__; _f.__qualname__ = _v.__qualname__
        _f.__signature__ = __import__("inspect").signature(_v); globals()[_n] = _f
PY
done
# cli.py: the __main__ guard must run after the overlay (python -m singvst_train.cli)
sed -i '/^if __name__ == "__main__":$/,+1d' "$W/python/singvst_train/cli.py"
printf '\nif __name__ == "__main__":\n    raise SystemExit(main())\n' >> "$W/python/singvst_train/cli.py"
cd "$W" && "$PY" -I -m pytest -q -m "not torch and not voice and not binary and not network" -rfE -p no:randomly 2>&1 | tail -40
echo "== with sketch notebooks and README section (T-P16, T-P17, T-P23 satisfiable)"
"$PY" -I "$D/sketch_docs.py" "$W" || echo "sketch_docs FAILED"
cd "$W" && "$PY" -I -m pytest -q tests/python/test_notebooks.py "tests/python/test_repo.py::test_P23_readme_states_behaviour_only_with_test_ids" 2>&1 | tail -3
