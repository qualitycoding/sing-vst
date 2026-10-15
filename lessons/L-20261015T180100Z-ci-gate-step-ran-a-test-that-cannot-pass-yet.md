---
id: L-20261015T180100Z-ci-gate-step-ran-a-test-that-cannot-pass-yet
title: 'The CI job required to be green at S-001 ran T-P23, which only passes after S-018, and its failure skipped the later lock-audit step'
status: active
supersedes: []
recurrence_of: null
occurrences: 1
severity: Medium
tags: [tech:github-actions, kind:process, phase:planning]
recorded_by: planner
run: gen-20261004T095012Z-singing-voice-vst-pitch-lyrics
recorded_at: 2026-10-15T18:01:00Z
---
## Trigger
A CI job mixes checks that must be green early with tests that are red by design until a later step.
## What went wrong
Cold read item S1: S-001's done criterion was unreachable, and T-P21 would never have run in CI.
## Correction
Moved T-P23 into its own `if: always()` step, made the lock step `if: always()`, and defined S-001's criterion as every repo step except the README one.
## Prevention rule
In a job whose result gates an early step, put each test that is red by design into its own `if: always()` step and name the exception in the step's done criterion.
## Detection check
`grep -n 'if: always()' .github/workflows/ci.yml` shows one per by-design-red step; S-001's Done-when names them.
## Evidence
premortem/coldread-pass-1.md S1.
