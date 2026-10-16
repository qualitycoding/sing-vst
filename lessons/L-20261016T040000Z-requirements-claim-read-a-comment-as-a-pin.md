---
id: L-20261016T040000Z-requirements-claim-read-a-comment-as-a-pin
title: "A claim said RVC's cu128 requirements file pins torch, but torch appears there only in a comment"
status: active
supersedes: []
recurrence_of: null
occurrences: 1
severity: High
tags: [applies:all, tech:python, kind:wrong-assumption, phase:planning]
recorded_by: planner
run: gen-20261004T095012Z-singing-voice-vst-pitch-lyrics
recorded_at: 2026-10-16T04:00:00Z
---
## Trigger
A claim summarises what a requirements, lock or config file installs.
## What went wrong
C-023 said the cu128 file pins torch 2.7.1+cu128; the line is a comment describing a separate first install stage, so the notebook as planned would have installed no torch at all — found by pre-mortem round 1 while hardening R-020.
## Correction
C-023 corrected, C-062 added from grep of non-comment lines; D-035 installs the torch pair as its own stage from the PyTorch index.
## Prevention rule
Verify every 'file X installs/pins Y' claim with a grep that excludes comment lines, and quote the matching line in the spike.
## Detection check
grep -v '^#' <file> | grep <package> returns the pin the claim names.
## Evidence
premortem/round-1.md R-020; research/spikes/premortem-r1/notebook_deps.txt.
