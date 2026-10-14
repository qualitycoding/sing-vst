#!/usr/bin/env bash
# Spike (C-049, C-050): SHA-256 / commit pins for every download the build and CI make. Usage: bash run.sh <empty dir> > output.txt
set -euo pipefail
W=${1:?dir}; cd "$W"
get() { curl -sSfL -o "$2" "$1"; printf '%s  %s  size %s  <%s>\n' "$(sha256sum "$2" | cut -d' ' -f1)" "$2" "$(stat -c %s "$2")" "$1"; }
echo "== downloads (sha256, file, size, url)"
get https://github.com/nlohmann/json/releases/download/v3.12.0/json.tar.xz json.tar.xz
get https://raw.githubusercontent.com/cmusphinx/cmudict/74790861f652b15e4ac49015a90074ad62a27690/cmudict.dict cmudict.dict
get https://raw.githubusercontent.com/cmusphinx/cmudict/74790861f652b15e4ac49015a90074ad62a27690/LICENSE cmudict-LICENSE
get https://github.com/Tracktion/pluginval/releases/download/v1.0.4/pluginval_Linux.zip pluginval_Linux.zip
get https://github.com/Tracktion/pluginval/releases/download/v1.0.4/pluginval_Windows.zip pluginval_Windows.zip
get https://github.com/microsoft/onnxruntime/releases/download/v1.31.0/onnxruntime-linux-x64-1.31.0.tgz ort-linux.tgz
echo "== licences"
tar xJf json.tar.xz json/LICENSE.MIT && head -1 json/LICENSE.MIT
head -3 cmudict-LICENSE
echo "== tag commits (peeled)"
for spec in "JUCE https://github.com/juce-framework/JUCE.git 9.0.3" "Catch2 https://github.com/catchorg/Catch2.git v3.16.1" "json https://github.com/nlohmann/json.git v3.12.0"; do
  set -- $spec; c=$(git ls-remote "$2" "refs/tags/$3^{}" | cut -f1); [ -n "$c" ] || c=$(git ls-remote "$2" "refs/tags/$3" | cut -f1); echo "$1 $3 $c"
done
echo "== cmudict word count"; python3 -c "
import re; w=set()
for l in open('cmudict.dict',encoding='utf-8'):
    l=l.split('#',1)[0].strip()
    if l and not l.startswith(';;;'):
        x=l.split()[0]
        if not re.search(r'\(\d+\)$',x): w.add(x.lower())
print(len(w),'words')"
