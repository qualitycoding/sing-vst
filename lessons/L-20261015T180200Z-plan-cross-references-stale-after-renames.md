---
id: L-20261015T180200Z-plan-cross-references-stale-after-renames
title: "Checklist 'applied via' cells, header comments and step texts named tests, files and sections by old names (T-054 for T-062, make_onnx_fixtures.py, T-P13b, §Sandbox rules)"
status: active
supersedes: []
recurrence_of: null
occurrences: 2
severity: Medium
tags: [applies:all, kind:verification-gap, phase:planning]
recorded_by: planner
run: gen-20261004T095012Z-singing-voice-vst-pitch-lyrics
recorded_at: 2026-10-15T18:02:00Z
---
## Trigger
Tests, files or sections are renumbered or renamed after other documents cite them; the ID-existence check (T-P22) passes because the old IDs still exist with another meaning.
## What went wrong
Cold read items S25, S33, H9: fourteen references pointed at the wrong test or a missing file.
## Correction
Corrected the checklist, added the errata section D-037 for frozen comments, and rewrote sub-test labels as parts of their test IDs.
## Prevention rule
After any renumbering, grep every document for the old IDs and names and check each citation's meaning, not only its existence.
## Detection check
The cold read reports no wrong-reference item; `grep -rn T-P13b plan HANDOFF.md` is empty.
## Evidence
premortem/coldread-pass-1.md S25, S33, H9.
Recurrence 2026-10-21 (pre-mortem round 3 R-053): S-017 1a kept 'RUN = the issue number' after D-035 changed the RUN rule.
