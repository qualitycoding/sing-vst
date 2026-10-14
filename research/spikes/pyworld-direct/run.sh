#!/usr/bin/env bash
# Spike (C-046): pyworld 0.3.5's package __init__ imports pkg_resources only for __version__; setuptools >= 83 (needed for
# PYSEC-2026-3447) no longer ships pkg_resources. Loading the compiled extension pyworld.pyworld directly works.
# Usage: bash run.sh <empty dir> <python3.12>  > output.txt 2>&1
set -u
W=${1:?dir}; PY=${2:?python3.12}; "$PY" -m venv "$W/v"; P="$W/v/bin"
"$P/python" -m pip install -q pip==26.2.1 setuptools==84.0.0 numpy==1.26.4 pyworld==0.3.5 2>&1 | grep -vi notice
"$P/python" -I -W ignore - <<'PY'
import importlib.machinery, importlib.util, importlib.metadata, pathlib, numpy as np
try:
    import pyworld; print("== plain import: OK")
except Exception as e: print("== plain 'import pyworld':", type(e).__name__, e)
dist = importlib.metadata.distribution("pyworld")
so = [f for f in dist.files if f.name.startswith("pyworld.") and f.suffix in (".so", ".pyd")][0]
path = str(dist.locate_file(so)); loader = importlib.machinery.ExtensionFileLoader("pyworld.pyworld", path)
spec = importlib.util.spec_from_file_location("pyworld.pyworld", path, loader=loader); pw = importlib.util.module_from_spec(spec); loader.exec_module(pw)
sr = 16000; n = np.arange(sr * 2)
harm = sum((0.5 / k) * np.sin(2 * np.pi * 220 * k * n / sr) for k in range(1, 16)); harm = 0.5 * harm / np.max(np.abs(harm))
f0, t = pw.harvest(harm, sr, f0_floor=50, f0_ceil=1100, frame_period=10.0); f = pw.stonemask(harm, f0, t, sr); v = f[20:-20]
print("== setuptools", importlib.metadata.version("setuptools"), "pyworld", dist.version, "| direct load of", so,
      "| interior voiced", int((v > 0).sum()), "/", len(v), "| rms cents vs 220 Hz (A4=440)", round(float(np.sqrt(np.mean((1200 * np.log2(v / 220)) ** 2))), 4))
PY
