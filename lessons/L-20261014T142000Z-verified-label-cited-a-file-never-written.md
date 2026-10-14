---
id: L-20261014T142000Z-verified-label-cited-a-file-never-written
title: "Claims were labelled verified against spike outputs and plan files that were never written; one of them (C-027) stated the opposite of what the spike measures"
status: active
supersedes: []
recurrence_of: L-20261010T094000Z-continuation-left-work-uncommitted-and-checkpoint-stale
occurrences: 2
severity: High
tags: [applies:all, tech:python, kind:verification-gap, phase:research]
recorded_by: planner
run: gen-20261004T095012Z-singing-voice-vst-pitch-lyrics
recorded_at: 2026-10-14T14:20:00Z
---
## Trigger
A session ends (or resets) between writing a spike script and running it, and the claim register is generated in the meantime. Signals: a claim cites `research/spikes/<name>/output.txt` or a `plan/` file; `git status` shows the spike directory untracked; the cited file is absent.
## What went wrong
C-027 said pyworld harvest tracks a clean 220 Hz sine and was labelled verified, citing research/spikes/pyworld/output.txt, which did not exist; the spike script sat uncommitted. When run, it shows harvest leaves a pure sine 0/161 voiced, so a frozen F0 test built on a sine (T-P10) could never pass. C-044 likewise cited plan/ENVIRONMENT.md, not yet written. The label check only tested that a source path looked like a spike, not that it existed.
## Correction
Ran the spike to completion in a fresh venv, added a harmonic-tone case (161/161 voiced, 0.098 cents), rewrote C-027 to the measured fact, re-probed hosts as a committed spike for C-044, superseded both knowledge items, and made tools/gen/claims.py fail when any cited research/ or plan/ file is missing.
## Prevention rule
Generate the claim register only after every cited spike has run and its output file is committed; tools/gen/claims.py must exit non-zero when a cited research/ or plan/ path does not exist.
## Detection check
`python tools/gen/claims.py` exits 0, and `git status --short research/spikes` is empty before any commit that changes research/claims.json.
## Evidence
research/spikes/pyworld/output.txt and research/spikes/hosts/output.txt (2026-10-14); knowledge/K-20261014T143900Z-c-027-pyworld.md; knowledge/K-20261014T143901Z-c-044-sandbox-environment.md.
