---
id: L-20261016T040300Z-non-reproducible-render-in-a-recall-path
title: "The plugin recalled projects by re-rendering with a model that draws unseeded noise"
status: active
supersedes: []
recurrence_of: null
occurrences: 1
severity: High
tags: [domain:audio-plugins, tech:vst3, kind:wrong-assumption, phase:planning]
recorded_by: planner
run: gen-20261004T095012Z-singing-voice-vst-pitch-lyrics
recorded_at: 2026-10-16T04:03:00Z
---
## Trigger
A plugin regenerates audio from stored parameters on project load, and a stage of the generator is non-deterministic.
## What went wrong
Pre-mortem round 1 R-017: every reload produced a different performance; the approved take could not be regenerated.
## Correction
D-038 take cache keyed by the phrase hash; the plugin renders through cachedRender; T-067, T-068.
## Prevention rule
Anything a user approves and later recalls is stored, not regenerated, unless regeneration is proven bit-exact.
## Detection check
Render, reload, compare samples: bit-identical.
## Evidence
premortem/round-1.md R-017; plan/DECISIONS.md D-038.
