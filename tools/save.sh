#!/usr/bin/env bash
# Commit and push explicit paths in one step (lessons L-20261014T195500Z, L-20261010T094000Z; PK-01, PK-08).
# Usage: bash tools/save.sh "<commit message>" <path> [<path> ...]
# Run it in the SAME tool call that creates or edits those paths, so a session cut off between calls loses nothing.
set -euo pipefail
msg=${1:?usage: save.sh "<message>" <paths...>}; shift; [ $# -gt 0 ] || { echo "save.sh: name the paths to commit" >&2; exit 2; }
cd "$(git rev-parse --show-toplevel)"
# Refresh the checkpoint hash map in every commit, so state.json can never lag the branch (L-20261015T071500Z).
python3.12 tools/checkpoint.py >/dev/null   # interpreter by minor version (PK-55)
git add -- "$@" .checkpoints/state.json .checkpoints/snapshots
git diff --cached --stat
if git diff --cached --quiet; then echo "save.sh: nothing staged"; else
  # Commit trailers (newline-separated) of the session that commits: $SINGVST_COMMIT_TRAILERS, else the untracked file
  # .git/singvst-trailers (written by S-000 in every session). None → refuse, so no commit carries another session's trailers.
  tf="$(git rev-parse --git-dir)/singvst-trailers"
  if [ -n "${SINGVST_COMMIT_TRAILERS:-}" ]; then trailers=$SINGVST_COMMIT_TRAILERS
  elif [ -s "$tf" ]; then trailers=$(cat "$tf")
  else echo "save.sh: no commit trailers; write .git/singvst-trailers (S-000)" >&2; exit 2; fi
  git commit -q -m "$msg" -m "$trailers"
fi
b=$(git branch --show-current)
# Push cadence (Rule 6, protocol v3.6): retry transient failures with exponential backoff, then verify with ls-remote.
pushed=0
for wait in 2 4 8 16 0; do
  if git push -q -u origin "$b"; then pushed=1; break; fi
  [ "$wait" -gt 0 ] && { echo "push failed; retrying in ${wait}s" >&2; sleep "$wait"; }
done
[ "$pushed" -eq 1 ] || { echo "save.sh: push to origin/$b failed after 5 attempts" >&2; exit 1; }
# Refresh the remote-tracking ref explicitly: a clone with a narrow fetch refspec has no origin/<branch> otherwise.
git fetch -q origin "$b:refs/remotes/origin/$b" || { echo "save.sh: cannot fetch origin/$b" >&2; exit 1; }
left=$(git rev-list --count "origin/$b..HEAD")
remote=$(git ls-remote origin "refs/heads/$b" | cut -f1); local_head=$(git rev-parse HEAD)
echo "saved $(git rev-parse --short HEAD) on $b; unpushed commits: $left; remote ${remote:0:7}"
[ "$left" -eq 0 ] && [ "$remote" = "$local_head" ] || { echo "save.sh: remote $remote != local $local_head" >&2; exit 1; }
