#!/usr/bin/env bash
# Spike (C-057..C-059): exact argv of RVC 81eed5e's dataset scripts; Resemblyzer 0.1.4 and openai-whisper 20250625 call
# signatures, read from their published source (no torch needed). Usage: bash run.sh <RVC checkout> <empty dir> <python3.12>
set -u
R=${1:?rvc}; W=${2:?dir}; PY=${3:?python3.12}; mkdir -p "$W"
echo "== RVC $(git -C "$R" rev-parse HEAD): sys.argv use"
for f in train/preprocess.py train/dataset/extract_f0.py train/dataset/extract_hubert_feature.py; do echo "-- $f"; grep -nE 'sys\.argv|mode ==|f0method =|elif mode' "$R/$f"; done
echo "-- RVC requirement pins relevant to the notebook"; grep -nE '^(pyworld|soundfile|scipy|numpy|librosa|transformers|onnxruntime)' "$R/requirments_cu128_py312.txt"
"$PY" -m pip download -q --no-deps --no-binary :all: openai-whisper==20250625 -d "$W/whisper" 2>&1 | tail -1
"$PY" -m pip download -q --no-deps resemblyzer==0.1.4 -d "$W/resemblyzer" 2>&1 | tail -1
cd "$W/resemblyzer" && unzip -q -o ./*.whl -d x && echo "== resemblyzer 0.1.4" && grep -nE '^def preprocess_wav|source_sr|isinstance\(fpath_or_wav|librosa.load|def embed_utterance' x/resemblyzer/audio.py x/resemblyzer/voice_encoder.py | head -12
cd "$W/whisper" && tar xzf ./*.tar.gz && echo "== openai-whisper 20250625" && grep -nE '^def load_model|^def transcribe|    temperature|    language|def load_audio' */whisper/__init__.py */whisper/transcribe.py */whisper/audio.py | head -12
