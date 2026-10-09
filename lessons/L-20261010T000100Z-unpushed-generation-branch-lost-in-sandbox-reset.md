---
id: L-20261010T000100Z-unpushed-generation-branch-lost-in-sandbox-reset
title: 'The whole generation branch existed only in the sandbox and was lost when the sandbox was reset between turns'
status: active
supersedes: []
recurrence_of: L-20261004T102007Z-sandbox-reset-lost-working-tree
occurrences: 1
severity: Medium
tags: [applies:all, tech:git, kind:environment, phase:planning]
recorded_by: planner
run: gen-20261004T095012Z-singing-voice-vst-pitch-lyrics
recorded_at: 2026-10-10T00:01:00Z
---
## Trigger
A planning run spans more than one turn; the target repository is pushable; work is committed locally but `git log origin/<branch>..HEAD` is non-empty when a turn ends.
## What went wrong
Research, spikes, frozen tests, CI and 28 claims were committed only locally; the turn ended asking the human to say 'continue', and the next turn found /home/claude empty.
## Correction
Rebuilt the branch from the conversation record, re-opened every source in the new run, and pushed after the first commit.
## Prevention rule
Push the generation branch after every commit that ends a sub-phase, and never end a turn while `git log --oneline origin/<branch>..HEAD` prints anything.
## Detection check
`git -C <repo> log --oneline origin/$(git branch --show-current)..HEAD | wc -l` prints 0 at the end of every turn.
## Evidence
Turn of 2026-10-04 ended with an unpushed branch; on 2026-10-10 `ls /home/claude/sing-vst` failed.
