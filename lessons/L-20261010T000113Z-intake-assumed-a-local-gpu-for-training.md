---
id: L-20261010T000113Z-intake-assumed-a-local-gpu-for-training
title: "Intake proposed training on the owner's local NVIDIA GPU; the owner needs a free hosted GPU"
status: active
supersedes: []
recurrence_of: null
occurrences: 1
severity: Medium
tags: [domain:singing-voice-synthesis, domain:audio, kind:wrong-assumption, phase:intake]
recorded_by: planner
run: gen-20261004T095012Z-singing-voice-vst-pitch-lyrics
recorded_at: 2026-10-10T00:01:13Z
---
## Trigger
A plan includes model training and the request does not say where compute comes from.
## What went wrong
Intake item 9 defaulted to a local GPU and asked for its VRAM; the human corrected this to a free online GPU (Colab).
## Correction
Re-planned training as resumable notebook-driven stages for Colab free tier with a Kaggle fallback, under the hosted platforms' usage policies.
## Prevention rule
At intake, ask where training compute runs (local GPU, free hosted notebook, paid cloud) and propose a free hosted default with its session limits, instead of assuming local hardware.
## Detection check
plan/ASSUMPTIONS.md has an assumption naming the compute platform and its limits.
## Evidence
Human message on 2026-10-04: 'we would have to use a free online gpu'.
