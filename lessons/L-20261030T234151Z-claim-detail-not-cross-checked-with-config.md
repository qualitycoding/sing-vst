---
id: L-20261030T234151Z-claim-detail-not-cross-checked-with-config
title: "A claim gave the right product but the wrong factor list for a model config"
status: active
supersedes: []
recurrence_of: null
occurrences: 1
severity: Low
tags: [applies:all, tech:python, domain:singing-voice-synthesis, kind:verification-gap, phase:research]
recorded_by: implementer
run: gen-20261004T095012Z-singing-voice-vst-pitch-lyrics
recorded_at: 2026-10-30T23:41:48Z
---
## Trigger
A claim summarises a config file (layer sizes, rates, factors) from a source other than the pinned config itself.
## What went wrong
C-048 said RVC's 48k upsample rates are 10,6,2,2,2 (= 480); configs/v2/48k.json at 81eed5e has [12,10,2,2] (= 480). Only the product was load-bearing (hop 480, C-048 T·hop), so nothing broke, but the claim was 'verified' with a wrong detail.
## Correction
The audit supersedes C-048's knowledge item with the pinned config's values.
## Prevention rule
When a claim quotes config values, copy them from the pinned file with its path and line, not from documentation or memory.
## Detection check
Each numeric detail in a claim has a file:line locator at the pinned commit.
## Evidence
../rvc/configs/v2/48k.json upsample_rates [12,10,2,2]; research/claims.json C-048.
