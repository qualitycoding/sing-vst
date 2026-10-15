---
id: L-20261015T180400Z-protocol-procedures-cited-but-not-shipped
title: 'The plan cited protocol sections (2E.4, 3.7.1, 3.7.2, Appendix C) that exist only in an external repository the implementer may not have'
status: active
supersedes: []
recurrence_of: null
occurrences: 1
severity: Medium
tags: [applies:all, kind:process, phase:planning]
recorded_by: planner
run: gen-20261004T095012Z-singing-voice-vst-pitch-lyrics
recorded_at: 2026-10-15T18:04:00Z
---
## Trigger
A handoff refers to procedures defined in a document outside the repository.
## What went wrong
Cold read items S3, S8, H8.
## Correction
Generated plan/PROTOCOL_EXCERPTS.md verbatim from the pinned protocol and added HANDOFF §Amendments.
## Prevention rule
Ship verbatim excerpts of every external procedure the implementer must follow, generated from the pinned source.
## Detection check
Every protocol section cited in PLAN.md or HANDOFF.md appears in plan/PROTOCOL_EXCERPTS.md.
## Evidence
premortem/coldread-pass-1.md S3, S8, H8.
