---
id: L-20261016T140000Z-hardening-changes-not-checked-against-each-other
title: "Round-1 mitigations were each correct alone but broke each other (mount moved after installs killed the budget heartbeat; per-run roots on Drive held an executable)"
status: active
supersedes: []
recurrence_of: null
occurrences: 1
severity: High
tags: [applies:all, kind:process, phase:planning]
recorded_by: planner
run: gen-20261004T095012Z-singing-voice-vst-pitch-lyrics
recorded_at: 2026-10-16T14:00:00Z
---
## Trigger
Several mitigations are added in one hardening pass to the same procedure (a notebook, a startup sequence).
## What went wrong
Pre-mortem round 2 R-051/R-052: R-020 moved the Drive mount after the installs while R-034 started a heartbeat writing to Drive before it; R-015 put the run root on Drive while R-023 built and ran the binary there.
## Correction
D-035 cell (4) order (a)–(f) states every write's position relative to the mount; build tree and binary on local disk.
## Prevention rule
After a hardening pass, re-derive the full ordered sequence of the changed procedure and check every write, mount and execution against it before committing.
## Detection check
For each changed procedure, a single ordered list names the step of every file write and the file system it lands on.
## Evidence
premortem/round-2.md R-051, R-052.
