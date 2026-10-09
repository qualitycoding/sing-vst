---
id: L-20261010T000102Z-store-probe-used-only-the-default-name
title: 'The knowledge-store probe checked only `agent-knowledge`, so R0 loaded nothing although qualitycoding/Lessons and qualitycoding/knowledge exist'
status: active
supersedes: []
recurrence_of: L-20261009T160500Z-lessons-addendum-adopted-after-implementation-again
occurrences: 1
severity: Medium
tags: [applies:all, tech:github, kind:process, phase:planning]
recorded_by: planner
run: gen-20261004T095012Z-singing-voice-vst-pitch-lyrics
recorded_at: 2026-10-10T00:01:02Z
---
## Trigger
Phase 0.1/0.3.7 with no store named in the request; the owner has other runs on record.
## What went wrong
Only qualitycoding/agent-knowledge was probed; it returned Not Found and research started with no prior lessons.
## Correction
Attached and cloned qualitycoding/Lessons and qualitycoding/knowledge and redid R0 (179 lessons, 139 items matched).
## Prevention rule
Before research, probe the owner's Lessons, lessons, knowledge and agent-knowledge repositories and any store named in memory, and record every probe result in state.json.
## Detection check
`.checkpoints/state.json` knowledge_store lists each probed location with its result.
## Evidence
state of 2026-10-04: 'agent-knowledge doesn't exist yet, so no past lessons were loaded'.
