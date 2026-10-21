---
id: L-20261021T180000Z-budget-ledger-keyed-by-storage-not-by-subject
title: "The per-voice GPU budget ledger lived in each platform's storage, so switching platform reset it"
status: active
supersedes: []
recurrence_of: null
occurrences: 1
severity: High
tags: [applies:all, domain:hosted-gpu, kind:integrity, phase:planning]
recorded_by: planner
run: gen-20261004T095012Z-singing-voice-vst-pitch-lyrics
recorded_at: 2026-10-21T18:00:00Z
---
## Trigger
A budget or quota is enforced per subject (a voice, a user, a project) while its ledger is stored per execution location (a platform, a machine, a folder).
## What went wrong
Pre-mortem round 4 R-082: a Colab-to-Kaggle switch started an empty Kaggle folder whose budget-voice.json began at 0 h, so the committed GPU hours and the 20-h cap were silently wrong.
## Correction
PLATFORM is part of the run identity; GATE-G-004.md carries PRIOR_VOICE_GPU_HOURS, which seeds the ledger; S-017 checks the total covers it.
## Prevention rule
Key every ledger by the subject the limit applies to, and carry its total across every location change through the gate that authorises the change.
## Detection check
For each budgeted quantity, name the single place its total lives and the step that carries it when the execution location changes.
## Evidence
premortem/round-4.md R-082.
