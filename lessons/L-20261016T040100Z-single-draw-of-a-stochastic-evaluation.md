---
id: L-20261016T040100Z-single-draw-of-a-stochastic-evaluation
title: "The evaluation rendered each phrase once although the guide model draws unseeded noise, so verdicts were single draws"
status: active
supersedes: []
recurrence_of: null
occurrences: 1
severity: High
tags: [applies:all, domain:evaluation, kind:wrong-assumption, phase:planning]
recorded_by: planner
run: gen-20261004T095012Z-singing-voice-vst-pitch-lyrics
recorded_at: 2026-10-16T04:01:00Z
---
## Trigger
An evaluation measures the output of a component that is known to be non-deterministic.
## What went wrong
C-040 recorded the guide's unseeded noise, yet eval/PROCEDURE.md rendered once per phrase and judged thresholds on that draw (pre-mortem round 1 R-018).
## Correction
PROCEDURE renders REPEATS = 5 times, reports means and spread.json; G-001 marks thresholds inside the spread indeterminate.
## Prevention rule
Every metric of a stochastic system is measured over repeats and reported with its spread; a threshold inside the spread is indeterminate.
## Detection check
For each evaluation metric, the procedure names a repeat count and a spread output.
## Evidence
premortem/round-1.md R-018; eval/PROCEDURE.md step 3.
