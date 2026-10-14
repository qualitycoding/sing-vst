#!/usr/bin/env bash
# Spike (C-044, PK-13): reachability of every external host the plan, CI, notebooks or gates name, from the planning sandbox.
# Prints HTTP status (000 = no connection). Run: bash run.sh > output.txt 2>&1
set -u
echo "== probed $(date -u +%Y-%m-%dT%H:%M:%SZ) from the planning sandbox (egress via agent proxy)"
while read -r role url; do
  [ -z "$role" ] && continue
  code=$(curl -sS -o /dev/null -m 15 -w '%{http_code}' "$url" 2>/dev/null); code=${code:-000}
  printf '%-34s %-80s %s\n' "$role" "$url" "$code"
done <<'HOSTS'
pypi-index                https://pypi.org/simple/pyworld/
pypi-files                https://files.pythonhosted.org/
github-web                https://github.com/qualitycoding/sing-vst
github-git                https://github.com/juce-framework/JUCE.git/info/refs?service=git-upload-pack
github-releases-ort       https://github.com/microsoft/onnxruntime/releases/download/v1.31.0/onnxruntime-linux-x64-1.31.0.tgz
github-releases-pluginval https://github.com/Tracktion/pluginval/releases/download/v1.0.4/pluginval_Linux.zip
github-raw                https://raw.githubusercontent.com/cmusphinx/cmudict/master/cmudict.dict
github-api                https://api.github.com/repos/qualitycoding/sing-vst
huggingface-rvc-assets    https://huggingface.co/lj1995/VoiceConversionWebUI/resolve/main/hubert_base.pt
pytorch-index             https://download.pytorch.org/whl/cpu/
colab                     https://colab.research.google.com/
kaggle                    https://www.kaggle.com/
actions-results           https://results-receiver.actions.githubusercontent.com/
HOSTS
