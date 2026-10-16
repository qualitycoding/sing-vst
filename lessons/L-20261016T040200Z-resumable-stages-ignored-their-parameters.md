---
id: L-20261016T040200Z-resumable-stages-ignored-their-parameters
title: "Resumable pipeline stages were keyed on input files only, so a parameter change re-used stale outputs"
status: active
supersedes: []
recurrence_of: null
occurrences: 1
severity: High
tags: [applies:all, domain:ml-training, kind:missing-spec, phase:planning]
recorded_by: planner
run: gen-20261004T095012Z-singing-voice-vst-pitch-lyrics
recorded_at: 2026-10-16T04:02:00Z
---
## Trigger
A resumable stage runner skips a stage whose marker matches the hash of its inputs.
## What went wrong
Pre-mortem round 1 R-013: a retrain with new EPOCHS/DEREVERB would skip prepare and train (their file inputs unchanged) and report the old model as the new run.
## Correction
D-035: each run has its own root and experiment; params.json is an input of every stage and is guarded per session; S-016 dry run checks a params change re-runs every stage.
## Prevention rule
Every parameter a stage uses is part of that stage's identity (an input file or the marker key).
## Detection check
Change one parameter in a dry run; every stage that uses it re-runs.
## Evidence
premortem/round-1.md R-013; plan/DECISIONS.md D-035.
