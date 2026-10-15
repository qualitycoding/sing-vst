---
id: L-20261015T190000Z-ci-pass-criterion-relied-on-absent-error-annotations
title: 'D-036 counted a test as passed when no error annotation named it, but GitHub caps error annotations per step, so a failing test could be invisible'
status: active
supersedes: []
recurrence_of: null
occurrences: 1
severity: High
tags: [tech:github-actions, kind:verification-gap, phase:planning]
recorded_by: planner
run: gen-20261004T095012Z-singing-voice-vst-pitch-lyrics
recorded_at: 2026-10-15T19:00:00Z
---
## Trigger
CI results can only be read through check-run annotations, and a step runs many tests of which many fail by design.
## What went wrong
Cold read pass 2 item S2: with 10-60 stub failures per step, the cap would hide failures and a test would look passed.
## Correction
tools/ci_annotate.py now writes one test-summary notice per JUnit file listing passed and failed IDs on every run; D-036 uses it.
## Prevention rule
Define a CI pass by a positive record (a summary listing the test as passed), never by the absence of a failure annotation.
## Detection check
Every annotate step runs `if: always()` and its output contains a `test-summary` notice.
## Evidence
premortem/coldread-pass-2.md S2.
