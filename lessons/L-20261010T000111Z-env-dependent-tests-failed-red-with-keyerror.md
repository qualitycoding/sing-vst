---
id: L-20261010T000111Z-env-dependent-tests-failed-red-with-keyerror
title: 'Two environment-dependent tests failed red with KeyError instead of a clean assertion'
status: active
supersedes: []
recurrence_of: null
occurrences: 1
severity: Low
tags: [tech:pytest, kind:verification-gap, phase:planning]
recorded_by: planner
run: gen-20261004T095012Z-singing-voice-vst-pitch-lyrics
recorded_at: 2026-10-10T00:01:11Z
---
## Trigger
Tests read os.environ for paths that only exist in CI or after training.
## What went wrong
os.environ['SINGVST_RVC_ROOT'] raised KeyError, which red verification treats as broken test code.
## Correction
Added explicit `assert os.environ.get(k), ...` before use.
## Prevention rule
Read every environment variable in a test through an assertion that names the variable and the plan step that sets it.
## Detection check
Red run shows only NotImplementedError or AssertionError causes.
## Evidence
pytest output of 2026-10-04.
