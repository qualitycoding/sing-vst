---
id: L-20261016T040400Z-provenance-named-a-lock-the-run-never-installed
title: "Result sidecars recorded the SHA of the repository lock file although the producing notebook installed a different, unlocked environment"
status: active
supersedes: []
recurrence_of: null
occurrences: 1
severity: High
tags: [applies:all, domain:reproducibility, kind:integrity, phase:planning]
recorded_by: planner
run: gen-20261004T095012Z-singing-voice-vst-pitch-lyrics
recorded_at: 2026-10-16T04:04:00Z
---
## Trigger
Results are produced in an environment other than the one the repository lock describes (hosted notebook, owner's machine).
## What went wrong
Pre-mortem round 1 R-019: prepare/evaluate sidecars would carry lockfile_sha256 of python/requirements-lock.txt, which the notebook never installs.
## Correction
D-035: the notebook freezes its own environment (env-freeze.txt, env.json) and passes it as --lockfile; both are uploaded and committed.
## Prevention rule
Provenance records the environment that actually produced the result, captured in that environment.
## Detection check
Each result sidecar's lockfile_sha256 equals the SHA-256 of a file produced in the same run.
## Evidence
premortem/round-1.md R-019; plan/DECISIONS.md D-035.
