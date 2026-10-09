---
id: L-20261010T000109Z-tests-cited-claim-ids-before-the-register-was-numbered
title: 'Frozen-test docstrings cited claim IDs (C-017, C-019, C-027, C-028) that pointed at the wrong claims once the register was written'
status: active
supersedes: []
recurrence_of: null
occurrences: 1
severity: Low
tags: [tech:cpp, tech:pytest, kind:process, phase:planning]
recorded_by: planner
run: gen-20261004T095012Z-singing-voice-vst-pitch-lyrics
recorded_at: 2026-10-10T00:01:09Z
---
## Trigger
Tests are written before research/claims.json is final and cite C-### IDs from memory.
## What went wrong
Four test citations named claims about other subjects.
## Correction
Renumbered the citations after generating the register.
## Prevention rule
Generate claims.json before writing test docstrings, and run a check that every C-### a test cites exists and shares a subject tag with the test's topic.
## Detection check
tools/check_refs.py reports 0 dangling or mismatched IDs.
## Evidence
sed fixes to test_synthesis.cpp, test_g2p.cpp, test_metrics.py, test_notebooks.py on 2026-10-04.
