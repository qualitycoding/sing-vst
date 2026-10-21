#!/usr/bin/env bash
# Spike (C-066, pass-10 cold read item 10): the audio-separator 0.47.0 API used by prepare.dereverb, read from the
# PyPI wheel, and whether it can share the notebook venv with RVC's requirements.
# Usage: bash run.sh <RVC checkout at 81eed5e> <empty dir> <python3.12> <uv>  > output.txt 2>&1
set -u
R=${1:?rvc}; W=${2:?dir}; PY=${3:?python3.12}; UV=${4:?uv}
"$PY" -m pip download -q --no-deps audio-separator==0.47.0 -d "$W" 2>&1 | grep -vi notice
echo "== wheel"; (cd "$W" && sha256sum audio_separator-0.47.0-py3-none-any.whl)
mkdir -p "$W/x" && (cd "$W/x" && "$PY" -I -m zipfile -e ../audio_separator-0.47.0-py3-none-any.whl .)
S="$W/x/audio_separator/separator"
echo "== package exports"; cat "$S/__init__.py"
echo "== Separator.__init__ parameters"; sed -n '/    def __init__(/,/    ):/p' "$S/separator.py" | head -25
echo "== load_model / separate signatures"; grep -n 'def load_model(\|def separate(' "$S/separator.py"
echo "== output file naming (custom_output_names keys are stem names, case-insensitive)"; sed -n '/def get_stem_output_path/,/return os.path.join(filename)/p' "$S/common_separator.py"
echo "== single-stem selection (case-insensitive)"; grep -n 'output_single_stem.lower()' "$S/architectures/mdxc_separator.py"
echo "== stems of the de-reverb model"; "$PY" -I -c "import json,sys; d=json.load(open(sys.argv[1]))['dereverb_mel_band_roformer_anvuew_sdr_19.1729.ckpt']; print(d['stems'], d['target_stem'])" "$W/x/audio_separator/models-scores.json"
echo "== Requires-Dist (numpy, onnx, torch)"; grep -E '^Requires-Dist: (numpy|onnx|torch) ' "$W/x/audio_separator-0.47.0.dist-info/METADATA"
echo "== RVC 81eed5e numpy pin"; grep -n '^numpy' "$R/requirments_cu128_py312.txt"
echo "== can both share one environment? (uv pip compile, Linux, Python 3.12)"
printf 'audio-separator==0.47.0\nnumpy>=1.26.4,<2\n' > "$W/both.in"
"$UV" pip compile -q --python-version 3.12 --python-platform x86_64-unknown-linux-gnu "$W/both.in" -o /dev/null 2>&1 | head -6; echo "rc=${PIPESTATUS[0]}"
echo "== in its own environment with the notebook's torch pin? (uv pip compile, Linux, Python 3.12)"
printf 'audio-separator==0.47.0\ntorch==2.7.1\n' > "$W/own.in"
"$UV" pip compile -q --python-version 3.12 --python-platform x86_64-unknown-linux-gnu "$W/own.in" -o "$W/own.txt" 2>&1 | head -6; echo "rc=${PIPESTATUS[0]}"
grep -E '^(numpy|onnx-weekly|torch|audio-separator)==' "$W/own.txt"
