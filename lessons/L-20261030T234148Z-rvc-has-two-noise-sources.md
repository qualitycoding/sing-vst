---
id: L-20261030T234148Z-rvc-has-two-noise-sources
title: "A claim about where a model draws random numbers listed one of two sources"
status: active
supersedes: []
recurrence_of: null
occurrences: 1
severity: High
tags: [applies:all, tech:python, domain:singing-voice-synthesis, kind:wrong-assumption, phase:research]
recorded_by: implementer
run: gen-20261004T095012Z-singing-voice-vst-pitch-lyrics
recorded_at: 2026-10-30T23:41:48Z
---
## Trigger
A plan makes a model deterministic by turning its random draws into inputs, based on a claim that names where the model samples noise.
## What went wrong
C-003 (verified, research round) said RVC v2 infer samples its prior noise internally and concluded that a deterministic ONNX export must take that noise as an input. The NSF source's SineGen also calls torch.randn_like (amplitude 0.0333 on unvoiced frames). D-012 and the export docstring were written from C-003 alone; the S-013 export would not have been deterministic for a given rnd (T-P19's assertion) had the implementer not read SineGen.
## Correction
S-013 derives the SineGen noise from the rnd input (DEVIATIONS S-013); the assumption audit (AM-08) records the corrected contract as D-043 and K-20261024T151050Z-rvc-sinegen-noise supersedes C-003's item.
## Prevention rule
Before planning a determinism or reproducibility contract, grep the model's whole forward path (every submodule) for random calls (randn, rand, dropout in train mode, RandomNormal nodes) and list each one in the claim.
## Detection check
The claim behind any 'noise as input' decision cites a grep of the pinned source for rand/randn/dropout over every module the forward pass reaches, with the hit count.
## Evidence
rvc infer/module/models.py SineGen.forward (torch.randn_like) at 81eed5e; research/claims.json C-003; premortem/ASSUMPTION_AUDIT.md.
