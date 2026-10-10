#!/usr/bin/env bash
# Spike R6: downloads the pinned openvpi PC-NSF-HiFiGAN release, prints its licence notice and the ONNX I/O, and times 1 s of audio on CPU.
# Usage: bash run.sh <empty scratch dir> <python with onnxruntime+numpy>
set -euo pipefail
W=${1:?scratch}; PY=${2:?python}; mkdir -p "$W"
B=https://github.com/openvpi/vocoders/releases/download/pc-nsf-hifigan-44.1k-hop512-128bin-2025.02
curl -sfL -o "$W/voc.oudep" "$B/pc_nsf_hifigan_44.1k_hop512_128bin_2025.02.oudep"
echo "sha256 oudep $(sha256sum "$W/voc.oudep" | cut -d' ' -f1)"
"$PY" -I - "$W" <<'PY'
import sys, zipfile, time, numpy as np, onnxruntime as ort
w = sys.argv[1]; z = zipfile.ZipFile(f"{w}/voc.oudep")
print("files:", sorted(z.namelist()))
notice = z.read("NOTICE.txt").decode()
print("licence line:", [l for l in notice.splitlines() if "license" in l.lower() or "Attribution" in l])
print("vocoder.yaml:", z.read("vocoder.yaml").decode().replace("\n", "; "))
onnx = [n for n in z.namelist() if n.endswith(".onnx")][0]
open(f"{w}/v.onnx", "wb").write(z.read(onnx))
so = ort.SessionOptions(); so.intra_op_num_threads = 1
s = ort.InferenceSession(f"{w}/v.onnx", so, providers=["CPUExecutionProvider"])
print("inputs:", [(i.name, i.type, i.shape) for i in s.get_inputs()]); print("outputs:", [(o.name, o.type, o.shape) for o in s.get_outputs()])
T = 86; mel = np.random.RandomState(0).randn(1, T, 128).astype(np.float32) * 0.5 - 5; f0 = np.full((1, T), 220, np.float32)
s.run(None, {"mel": mel, "f0": f0})
ts = []
for _ in range(3):
    t = time.perf_counter(); y = s.run(None, {"mel": mel, "f0": f0})[0]; ts.append(time.perf_counter() - t)
print(f"output shape {y.shape}; samples/frame {y.shape[1] // T}; median {sorted(ts)[1]:.3f} s for {T*512/44100:.3f} s audio, 1 thread, onnxruntime {ort.__version__}")
PY
