---
id: L-20261021T200500Z-package-added-to-pinned-install-without-resolving
title: "An optional package was added to a pinned install list without resolving it, and its numpy floor contradicted RVC's ceiling"
status: active
supersedes: []
recurrence_of: null
occurrences: 1
severity: Medium
tags: [applies:all, domain:hosted-gpu, tech:python, kind:dependency, phase:planning]
recorded_by: planner
run: gen-20261004T095012Z-singing-voice-vst-pitch-lyrics
recorded_at: 2026-10-21T20:05:00Z
---
## Trigger
A plan adds a package, often an optional one behind a flag, to an install command that also installs a pinned requirement file.
## What went wrong
D-035 installed audio-separator 0.47.0 into the notebook venv when DEREVERB was set. Cold read pass 10 asked for its API, and the wheel showed `numpy>=2`, while RVC 81eed5e pins `numpy<2`. `uv pip compile` found no solution. The flag-gated path had never been resolved, so the planned install would have failed or broken RVC.
## Correction
audio-separator gets its own venv, which the toolkit reaches through SINGVST_SEPARATOR_PYTHON. Its exact calls are read from the wheel (spike audio-separator-047, C-066), and the path is listed as unverified.
## Prevention rule
Resolve every package of every install set together with the pins it will share an environment with, including flag-gated extras, before the plan names it. Read an API from the pinned wheel, never from memory.
## Detection check
For each install command in the plan, there is a `uv pip compile` (or equivalent) spike output covering the same packages and pins, including optional ones.
## Evidence
research/spikes/audio-separator-047/output.txt; premortem/coldread-pass-10.md S10; R-108.
