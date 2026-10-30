#!/usr/bin/env bash
# Phase 0.1 environment-class probe (protocol v3.6; AMENDMENT-01 AM-02). Two calls in different tool calls / turns:
#   bash research/spikes/env-class/run.sh start     plants markers under /tmp and ../ and starts a detached background process
#   bash research/spikes/env-class/run.sh check     reports whether all three survived, plus older evidence, and the class
# Class `ephemeral` if any marker or the process is lost, else `stable`.
set -u
S=/tmp/singvst-env-probe; P="$(cd "$(dirname "$0")/../../.." && pwd)/../.singvst-env-probe"
case "${1:-}" in
  start)
    date -u +%FT%TZ > "$S.tmp-marker"; date -u +%FT%TZ > "$P.parent-marker"
    setsid nohup sleep 86400 > /dev/null 2>&1 < /dev/null &
    echo $! > "$S.pid"; echo "started at $(cat "$S.tmp-marker"), background pid $(cat "$S.pid")";;
  check)
    echo "== probe $(date -u +%FT%TZ) on $(hostname), $(uname -sr)"
    echo "boot time: $(uptime -s) (uptime: $(uptime -p))"
    t=lost; [ -f "$S.tmp-marker" ] && t="kept (written $(cat "$S.tmp-marker"))"; echo "/tmp marker from the start call: $t"
    p=lost; [ -f "$P.parent-marker" ] && p="kept (written $(cat "$P.parent-marker"))"; echo "../ marker from the start call: $p"
    b=lost; [ -f "$S.pid" ] && kill -0 "$(cat "$S.pid")" 2>/dev/null && b="alive (pid $(cat "$S.pid"))"; echo "background process from the start call: $b"
    echo "older evidence (files this session wrote in earlier turns):"
    for f in /tmp/pv/pluginval_Linux.zip ../build-all.log ../venv-torch/bin/python ../build-full/tests/cpp/singvst_plugin_tests; do
      [ -e "$f" ] && echo "  $f  $(date -u -r "$f" +%FT%TZ)"; done
    if [ "$t" != lost ] && [ "$p" != lost ] && [ "$b" != lost ]; then echo "class: stable"; else echo "class: ephemeral"; fi;;
  *) echo "usage: run.sh start|check" >&2; exit 2;;
esac
