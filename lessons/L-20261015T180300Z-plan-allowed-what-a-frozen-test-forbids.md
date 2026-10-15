---
id: L-20261015T180300Z-plan-allowed-what-a-frozen-test-forbids
title: 'S-017 allowed committing audio renders while the frozen T-062 forbids tracked audio outside tests/fixtures'
status: active
supersedes: []
recurrence_of: null
occurrences: 1
severity: Medium
tags: [applies:all, kind:scope, phase:planning]
recorded_by: planner
run: gen-20261004T095012Z-singing-voice-vst-pitch-lyrics
recorded_at: 2026-10-15T18:03:00Z
---
## Trigger
Plan steps are written after the repository-property tests are frozen.
## What went wrong
Cold read item S2: following the step would have broken T-062 at S-019.
## Correction
S-017 now commits only the three JSON results; renders stay on the owner's Drive.
## Prevention rule
When writing a step that adds files to the repository, check them against every frozen repository-property test first.
## Detection check
The cold read reports no step-vs-frozen-test contradiction.
## Evidence
premortem/coldread-pass-1.md S2.
