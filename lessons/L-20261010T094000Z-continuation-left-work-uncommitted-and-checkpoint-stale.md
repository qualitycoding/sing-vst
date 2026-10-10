---
id: L-20261010T094000Z-continuation-left-work-uncommitted-and-checkpoint-stale
title: 'A continuation attempt committed research round 2 but left the revised interfaces and the oracle untracked, never wrote a lesson it cited, and left state.json at 0.3.7'
status: active
supersedes: []
recurrence_of: L-20261009T234122Z-checkpoint-state-stale-after-implementation-and-main-not-default
occurrences: 1
severity: Medium
tags: [applies:all, tech:git, kind:process, phase:planning]
recorded_by: planner
run: gen-20261004T095012Z-singing-voice-vst-pitch-lyrics
recorded_at: 2026-10-10T09:40:00Z
---
## Trigger
A long planning turn produces artefacts across several sub-phases and may end (or be cut off) before its last commit.
## What went wrong
On 2026-10-10 the next turn found core/ and research/spikes/oracle/ untracked, a README citing lesson L-20261010T001500Z that did not exist, and state.json still at subphase 0.3.7 although research round 2 had been committed.
## Correction
Verified the checkpoint hashes, wrote the missing lesson, reviewed and committed the untracked files with the next sub-phase, and moved state.json forward in that commit.
## Prevention rule
Commit and push every artefact the moment a sub-phase produces it, write a lesson file before any text cites its ID, and advance state.json in the same commit as the work it records.
## Detection check
`git status --short` is empty and `grep -rhoE 'L-2026[0-9T]+Z-[a-z0-9-]+' research plan | sort -u` names only files that exist, at the end of every turn.
## Evidence
git status of 2026-10-10 09:30 (`?? core/`, `?? research/spikes/oracle/`); .checkpoints/state.json subphase 0.3.7.
