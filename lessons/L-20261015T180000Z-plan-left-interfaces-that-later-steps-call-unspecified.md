---
id: L-20261015T180000Z-plan-left-interfaces-that-later-steps-call-unspecified
title: 'The plan froze tests for the toolkit CLI and notebooks but never specified the CLI options, the notebook layout, the RVC invocations or the voicebank file mapping that S-012…S-017 must produce'
status: active
supersedes: []
recurrence_of: null
occurrences: 3
severity: High
tags: [applies:all, kind:verification-gap, domain:ml-training, phase:planning]
recorded_by: planner
run: gen-20261004T095012Z-singing-voice-vst-pitch-lyrics
recorded_at: 2026-10-15T18:00:00Z
---
## Trigger
A plan has steps that write glue (CLI commands, notebooks, scripts calling third-party tools) whose exact shape is only implied by tests and claims.
## What went wrong
Cold read pass 1 items S9, S10, S12, S27: the implementer would have had to invent options, paths and file mappings.
## Correction
Added D-035 (per-command options, notebook cells, RVC command lines from the pinned source, voicebank roles, upload set).
## Prevention rule
Before the cold read, write an explicit specification (options, files, exit codes, exact third-party command lines) for every interface a later step or a human-run artefact calls.
## Detection check
Each S-### that produces glue cites a D-### that lists its interface; the cold read reports no 'undefined option/layout' item.
## Evidence
premortem/coldread-pass-1.md S9, S10, S12, S27.
Occurrence 2 (cold read pass 2): stage inputs/outputs, the time and budget controls, exit codes per error type, the notebook ref and the transposition mechanics were still unspecified (premortem/coldread-pass-2.md S3, S5-S7, S20, S23, S24).
Recurrence 2026-10-15 (cold read pass 3 Sonnet items 4, 12, 14, 20): RVC extract argv unverified, provenance root/lockfile source unspecified, Resemblyzer call shape unstated, CLI exit codes not mechanical; resolved by C-057, D-015/D-033 editable install, PROCEDURE file paths, D-014.
