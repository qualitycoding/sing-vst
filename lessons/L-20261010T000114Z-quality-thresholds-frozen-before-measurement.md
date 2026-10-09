---
id: L-20261010T000114Z-quality-thresholds-frozen-before-measurement
title: 'Similarity, WER, pitch and speed thresholds were proposed at intake and frozen as pass/fail numbers with no measurement behind them'
status: active
supersedes: []
recurrence_of: L-20261009T234100Z-intake-defaults-and-draft-numbers-stated-before-measurement
occurrences: 1
severity: Medium
tags: [domain:singing-voice-synthesis, domain:audio, kind:verification-gap, phase:planning]
recorded_by: planner
run: gen-20261004T095012Z-singing-voice-vst-pitch-lyrics
recorded_at: 2026-10-10T00:01:14Z
---
## Trigger
A plan sets numeric quality targets for a model that has not been trained.
## What went wrong
eval/thresholds.json froze 0.75 / 0.15 / 25 cents / 25% / 1.0 as gates.
## Correction
Reworded them as unmeasured defaults; G-001 records the measured values and the owner confirms or amends the thresholds before any downstream step uses them.
## Prevention rule
Mark every numeric quality target 'unmeasured default' until a spike or run has measured it, and route its confirmation through the result gate.
## Detection check
eval/thresholds.json has "status": "unmeasured-default" until GATE-G-001 is signed.
## Evidence
eval/thresholds.json of 2026-10-04.
