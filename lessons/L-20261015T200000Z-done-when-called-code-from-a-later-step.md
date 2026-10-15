---
id: L-20261015T200000Z-done-when-called-code-from-a-later-step
title: "A step's Done-when ran a frozen test that calls a function delivered only by a later step"
status: active
supersedes: []
recurrence_of: null
occurrences: 1
severity: High
tags: [applies:all, kind:plan-structure, phase:planning]
recorded_by: planner
run: gen-20261004T095012Z-singing-voice-vst-pitch-lyrics
recorded_at: 2026-10-15T20:00:00Z
---
## Trigger
A plan assigns frozen tests to steps and steps run in ID order.
## What went wrong
Cold read pass 3 item H3: S-010's Done-when included the binary part of T-P13, which calls pack_voice, delivered by S-012; S-010 could never pass.
## Correction
Moved the binary part of T-P13 to S-012 and made S-012 depend on S-010.
## Prevention rule
For every test named in a Done-when, every function it calls is delivered by that step or by a step in its Depends on chain.
## Detection check
For each Done-when test, list the symbols it imports and map each to its delivering step; none is later than the step.
## Evidence
premortem/coldread-pass-3.md H3.
