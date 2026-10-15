---
id: L-20261015T071500Z-checkpoint-not-rewritten-after-phase-2b-commits
title: "Seventeen Phase 2B commits on 2026-10-14 left .checkpoints/state.json at 19:40Z, so the next session's resume check found 11 hash mismatches and 78 untracked artefacts"
status: active
supersedes: []
recurrence_of: L-20261010T094000Z-continuation-left-work-uncommitted-and-checkpoint-stale
occurrences: 1
severity: Medium
tags: [applies:all, tech:git, kind:process, phase:planning]
recorded_by: planner
run: gen-20261004T095012Z-singing-voice-vst-pitch-lyrics
recorded_at: 2026-10-15T07:15:00Z
---
## Trigger
A planning session commits many artefacts with tools/save.sh after the last explicit tools/checkpoint.py call; the next session applies the Resume Rule (1.2).
## What went wrong
save.sh committed and pushed each file but never rewrote state.json; the checkpoint still said phase 1.3 with 137 artefacts while the branch held 215 tracked files and the C++ test suite.
## Correction
Verified the working tree was clean and the remote tip matched HEAD (02fa6ea), so every mismatch came from committed work; treated Phase 2B as the in-progress sub-phase and changed tools/save.sh to run tools/checkpoint.py and stage state.json in every commit.
## Prevention rule
Never write the checkpoint as a separate manual step: tools/save.sh regenerates .checkpoints/state.json and commits it with every save.
## Detection check
`git show --stat HEAD` lists .checkpoints/state.json for every commit made through tools/save.sh.
## Evidence
2026-10-15 resume: state.json updated_at 2026-10-14T19:40:53Z, HEAD 02fa6ea at 2026-10-14T21:30Z; 11 mismatches, 78 artefacts missing from the map.
