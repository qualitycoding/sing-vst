#!/usr/bin/env bash
# Commit and push explicit paths in one step (lessons L-20261014T195500Z, L-20261010T094000Z; PK-01, PK-08).
# Usage: bash tools/save.sh "<commit message>" <path> [<path> ...]
# Run it in the SAME tool call that creates or edits those paths, so a session cut off between calls loses nothing.
set -euo pipefail
msg=${1:?usage: save.sh "<message>" <paths...>}; shift; [ $# -gt 0 ] || { echo "save.sh: name the paths to commit" >&2; exit 2; }
cd "$(git rev-parse --show-toplevel)"
# Refresh the checkpoint hash map in every commit, so state.json can never lag the branch (L-20261015T071500Z).
python3 tools/checkpoint.py >/dev/null
git add -- "$@" .checkpoints/state.json
git diff --cached --stat
if git diff --cached --quiet; then echo "save.sh: nothing staged"; else
  git commit -q -m "$msg" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>" -m "Claude-Session: https://claude.ai/code/session_016Ltp4MhMKiaYAbZSCVGTy8"
fi
b=$(git branch --show-current)
for i in 1 2 3; do git push -q origin "$b" && break; echo "push attempt $i failed" >&2; sleep $((i * 5)); done
left=$(git log --oneline "origin/$b..HEAD" | wc -l); echo "saved $(git rev-parse --short HEAD) on $b; unpushed commits: $left"
[ "$left" -eq 0 ]
