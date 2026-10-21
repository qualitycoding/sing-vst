---
id: L-20261021T150000Z-behaviour-specified-against-an-interface-that-cannot-express-it
title: "Mitigations specified behaviour that the frozen interfaces cannot express (Renderer short-circuits identical requests; the guide engine never sees notes)"
status: active
supersedes: []
recurrence_of: null
occurrences: 1
severity: High
tags: [applies:all, kind:missing-spec, phase:planning]
recorded_by: planner
run: gen-20261004T095012Z-singing-voice-vst-pitch-lyrics
recorded_at: 2026-10-21T15:00:00Z
---
## Trigger
A hardening step adds behaviour to a component whose interface is frozen.
## What went wrong
Pre-mortem round 3 R-072 and R-077: "the worker resamples the stored take" was unreachable because Renderer never re-runs an identical request; the phrase-cap fallback needed note boundaries that GuideEngine::render does not receive.
## Correction
resampleTake (T-071) plus a plugin-owned resample worker; the split rule restated on phoneme spans.
## Prevention rule
For every behaviour added to a frozen component, name the interface call that carries it and the data that call receives; if none exists, add the interface (Phase 2) or move the behaviour to the caller.
## Detection check
Each new behaviour line in a decision cites the header function that implements it.
## Evidence
premortem/round-3.md R-072, R-077.
