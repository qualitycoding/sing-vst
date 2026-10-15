#!/usr/bin/env bash
# Last tool call of every turn (PK-01, PK-03, PK-12): the working tree is clean, the branch is pushed, no token is on disk.
# Exit 0 only when all three hold.
set -u
cd "$(git rev-parse --show-toplevel)"; b=$(git branch --show-current); rc=0
dirty=$(git status --porcelain); [ -z "$dirty" ] || { echo "DIRTY:"; echo "$dirty"; rc=1; }
git fetch -q origin "$b" 2>/dev/null
ahead=$(git log --oneline "origin/$b..HEAD" | wc -l); [ "$ahead" -eq 0 ] || { echo "UNPUSHED: $ahead commit(s)"; rc=1; }
tok=$( { grep -rIlE 'github_pat_[A-Za-z0-9_]{20,}|ghp_[A-Za-z0-9]{20,}' . --exclude-dir=.git 2>/dev/null; \
        git config --list 2>/dev/null | grep -lE 'github_pat_|ghp_' ; } | head -5)   # repository + git config only (cold read S38)
[ -z "$tok" ] || { echo "TOKEN ON DISK:"; echo "$tok"; rc=1; }
[ "$rc" -eq 0 ] && echo "turn-end check: clean, pushed ($(git rev-parse --short HEAD)), no tokens"
exit $rc
