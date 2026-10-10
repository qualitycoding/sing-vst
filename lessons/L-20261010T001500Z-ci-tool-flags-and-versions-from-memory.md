---
id: L-20261010T001500Z-ci-tool-flags-and-versions-from-memory
title: 'A recalled pluginval flag (--validate-in-process) and recalled action versions were written into the CI draft without reading the pinned tool source'
status: active
supersedes: []
recurrence_of: L-20261004T161503Z-audacity-commands-coded-from-memory
occurrences: 1
severity: Medium
tags: [tech:github-actions, tech:pluginval, kind:wrong-assumption, phase:planning]
recorded_by: planner
run: gen-20261004T095012Z-singing-voice-vst-pitch-lyrics
recorded_at: 2026-10-10T00:15:00Z
---
## Trigger
A CI workflow or script names a third-party CLI flag, release asset name or action major version.
## What went wrong
The 2026-10-04 CI draft used `pluginval --validate-in-process` (no such option in 1.0.4) and actions/checkout@v4 etc. while v7/v8 were current.
## Correction
Read the pluginval 1.0.4 CLI source and the actions' tags in the upstream-facts spike (C-015b/c) and pinned what the source shows.
## Prevention rule
Take every CLI flag, release asset name and action version for CI from the pinned tool's source or tag listing in a committed spike, never from memory.
## Detection check
`research/spikes/upstream-facts/output.txt` has a PASS line for each CLI option and action version used in .github/workflows/*.yml.
## Evidence
upstream-facts spike, checks C-015b and C-015c (first run failed, 2026-10-10).
