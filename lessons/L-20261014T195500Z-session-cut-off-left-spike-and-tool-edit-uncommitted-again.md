---
id: L-20261014T195500Z-session-cut-off-left-spike-and-tool-edit-uncommitted-again
title: 'A continuation session wrote a spike, a dependency lock and a bootstrap-script fix after its last commit and ended without committing them'
status: active
supersedes: []
recurrence_of: L-20261010T094000Z-continuation-left-work-uncommitted-and-checkpoint-stale
occurrences: 2
severity: High
tags: [applies:all, tech:git, kind:process, phase:planning]
recorded_by: planner
run: gen-20261004T095012Z-singing-voice-vst-pitch-lyrics
recorded_at: 2026-10-14T19:55:00Z
---
## Trigger
A planning session writes files after its last commit, and the session can end between tool calls (usage limit, cut-off, reset) before any turn-end check runs.
## What went wrong
At 15:38 the 2026-10-14 session committed round 4; by 15:43 it had written research/spikes/pyworld-direct/, python/requirements.in, python/requirements-lock.txt and a stricter clone check in tools/bootstrap_test_env.sh, then stopped. The 20:35 session found them untracked or modified, and the bootstrap edit failed the checkpoint hash check. This repeats L-20261010T094000Z, whose rule ('git status is empty at the end of every turn') cannot work when the turn never reaches its end.
## Correction
Re-ran the pyworld-direct spike to completion (identical output), verified its PYSEC-2026-3447 premise with a committed pip-audit spike, ran the bootstrap check on the pinned deps and on a wrong JUCE tag (exit 3), then committed all of it with claim C-046 through tools/save.sh.
## Prevention rule
Commit and push in the same tool call that writes a file: every command that creates or edits a path in the repository ends with `bash tools/save.sh "<msg>" <those paths>`; run `bash tools/turn_end_check.sh` as the last call of every turn as a second line of defence.
## Detection check
`git status --porcelain` is empty after every tool call that wrote into the repository (the call's own output shows `saved <sha> ... unpushed commits: 0`).
## Evidence
state.json hash mismatch on tools/bootstrap_test_env.sh at 2026-10-14T19:40Z; `git status` showed ?? python/requirements*.txt, ?? research/spikes/pyworld-direct/.
Recurrence 2026-10-15: after a session break the locale-de and eval-apis spikes were found uncommitted and were committed at 2953990; the rule now also requires a turn-end check before any long-running agent launch.
