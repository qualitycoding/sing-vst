---
id: L-20261030T234149Z-implementer-host-differs-from-planning-sandbox
title: "The plan assumed the implementer's host had the planning sandbox's network limits"
status: active
supersedes: []
recurrence_of: null
occurrences: 1
severity: Medium
tags: [applies:all, kind:wrong-assumption, kind:environment, phase:planning]
recorded_by: implementer
run: gen-20261004T095012Z-singing-voice-vst-pitch-lyrics
recorded_at: 2026-10-30T23:41:48Z
---
## Trigger
A plan records host reachability or tool availability probed in the planning sandbox and turns it into rules for the implementer (CI-only checks, no local installs).
## What went wrong
C-044 (probed from the planning sandbox) found download.pytorch.org, huggingface.co, Colab and Kaggle unreachable; A-016 and D-036 then stated that no torch is installed locally and that export parity runs only in CI. The implementation ran on the owner's own machine, where all of them were reachable (S-000 host probe), so the CI-only rule cost CI round trips until the implementer recorded a deviation and installed torch locally.
## Correction
S-000 re-probed the hosts and DEVIATIONS rows record local torch, the HF download and the user-space sysroot; the audit supersedes C-044's item with the implementation-host facts and D-043 makes 'CI only' conditional on the implementer's own probe.
## Prevention rule
Write environment-dependent rules as conditions on the implementer's own S-000 probe ('if the probe shows X unreachable, then ...'), never as facts carried over from the planning sandbox.
## Detection check
Every plan rule that names a host, package index or privilege is phrased as a condition and references the S-000 probe output.
## Evidence
research/spikes/hosts output vs ../hosts-now.txt (S-000); DEVIATIONS.md S-000, S-011, S-013 rows; premortem/ASSUMPTION_AUDIT.md.
