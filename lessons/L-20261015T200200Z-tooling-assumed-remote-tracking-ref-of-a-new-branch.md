---
id: L-20261015T200200Z-tooling-assumed-remote-tracking-ref-of-a-new-branch
title: "The save and turn-end tools read origin/<branch>, which a single-branch clone never creates for a newly pushed branch"
status: active
supersedes: []
recurrence_of: null
occurrences: 1
severity: Medium
tags: [applies:all, tech:git, kind:wrong-assumption, phase:planning]
recorded_by: planner
run: gen-20261004T095012Z-singing-voice-vst-pitch-lyrics
recorded_at: 2026-10-15T20:02:00Z
---
## Trigger
Tooling compares HEAD with origin/<branch> in a clone made with a narrow fetch refspec, and the implementer pushes a new branch.
## What went wrong
Cold read pass 3 Sonnet item 3: save.sh would exit non-zero after a successful push and turn_end_check.sh would report 'pushed' falsely, because origin/impl-… never exists.
## Correction
save.sh and turn_end_check.sh fetch origin "$b:refs/remotes/origin/$b" explicitly; S-000 widens the fetch refspec, pushes with -u and checks git rev-parse origin/<impl>.
## Prevention rule
Tools that compare with a remote-tracking ref fetch that ref explicitly first; never assume the clone's refspec covers a new branch.
## Detection check
In a --single-branch clone, push a new branch and run the tools; they report the true ahead count.
## Evidence
premortem/coldread-pass-3.md S3; tools/save.sh; tools/turn_end_check.sh.
