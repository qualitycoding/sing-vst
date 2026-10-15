---
id: L-20261015T190100Z-resumable-stage-could-delete-its-own-checkpoints
title: "The plan ran training through a stage runner that deletes a stage's outputs before re-running it, without saying the RVC experiment directory must not be an output"
status: active
supersedes: []
recurrence_of: null
occurrences: 1
severity: High
tags: [domain:ml-training, tech:rvc, kind:wrong-assumption, phase:planning]
recorded_by: planner
run: gen-20261004T095012Z-singing-voice-vst-pitch-lyrics
recorded_at: 2026-10-15T19:01:00Z
---
## Trigger
A resumable pipeline wraps a long job that keeps its own checkpoints, and the wrapper cleans outputs before a rerun.
## What went wrong
Cold read pass 2 item S6: listing logs/<voice> as the train stage's output would wipe every checkpoint on resume.
## Correction
D-035 stage table: the train stage's only output is the final weights file; the experiment directory is never an output.
## Prevention rule
When a wrapper deletes outputs on rerun, list as outputs only artefacts that are cheap to regenerate; never a job's own checkpoint directory.
## Detection check
The D-035 stage table names no checkpoint directory in the Outputs column.
## Evidence
premortem/coldread-pass-2.md S6.
