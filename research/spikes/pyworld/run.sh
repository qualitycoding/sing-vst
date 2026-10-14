#!/usr/bin/env bash
# Spike R6 round 4 (C-027): pyworld 0.3.5 on Python 3.12 with numpy 1.26.4.
# Shows (a) the setuptools<81 requirement (pyworld imports pkg_resources) and (b) which known-answer signal harvest can track:
# a pure sine is NOT tracked (all frames unvoiced); a 15-partial harmonic tone is. T-P10 must therefore use a harmonic tone.
# Usage: bash run.sh <empty dir> <python3.12 binary>  > output.txt 2>&1
set -u
W=${1:?dir}; PY=${2:?python3.12}; "$PY" -m venv "$W/v"; P="$W/v/bin"
"$P/python" -m pip install -q pip==25.2 numpy==1.26.4 pyworld==0.3.5 2>&1 | grep -v -i notice
echo "== import without setuptools:"; "$P/python" -I -c "import pyworld" 2>&1 | tail -1
"$P/python" -m pip install -q setuptools==80.9.0 2>&1 | grep -v -i notice
"$P/python" -I -W ignore - <<'PY'
import sys, numpy as np, pyworld as pw
sr = 16000; n = np.arange(sr * 2)
sine = 0.5 * np.sin(2 * np.pi * 220 * n / sr)
harm = sum((0.5 / k) * np.sin(2 * np.pi * 220 * k * n / sr) for k in range(1, 16)); harm = 0.5 * harm / np.max(np.abs(harm))
print("== python", sys.version.split()[0], "numpy", np.__version__, "pyworld", pw.__version__)
for name, x in (("pure sine 220 Hz", sine), ("harmonic 220 Hz, 15 partials 1/k", harm)):
    for kw in ({}, {"f0_floor": 50, "f0_ceil": 1100}):
        f0, t = pw.harvest(x.astype(np.float64), sr, frame_period=10.0, **kw); f = pw.stonemask(x.astype(np.float64), f0, t, sr)
        inner = f[20:-20]; v = inner[inner > 0]
        rc = float(np.sqrt(np.mean((1200 * np.log2(v / 220)) ** 2))) if len(v) else float("nan")
        print(f"== {name:34s} harvest{kw}: frames {len(f)}, interior voiced {len(v)}/{len(inner)}, rms cents vs 220 Hz (A4=440) {rc:.4f}")
PY
