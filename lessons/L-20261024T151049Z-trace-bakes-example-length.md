---
id: L-20261024T151049Z-trace-bakes-example-length
title: "A torch.onnx.export trace of RVC's synthesiser baked in the example length and failed for every other length"
status: active
supersedes: []
recurrence_of: null
occurrences: 1
severity: High
tags: [applies:all, tech:python, domain:singing-voice-synthesis, kind:wrong-assumption, phase:implementation]
recorded_by: implementer
run: gen-20261004T095012Z-singing-voice-vst-pitch-lyrics
recorded_at: 2026-10-24T15:10:49Z
---
## Trigger
A model is exported with torch.onnx.export (tracing) with dynamic_axes declared, and its code converts tensor sizes to Python values: `int(length)`, `max(a, length)`, or `if pad_length > 0`. The tracer prints "TracerWarning: Converting a tensor to a Python integer/boolean".
## What went wrong
The export of RVC's v2 synthesiser succeeded at 100 frames and the checker passed, so the export looked done. The first parity run at 200 frames failed inside ONNX Runtime with a Reshape error in enc_p/encoder/attn_layers.0. The windowed relative-position attention had its length frozen into constants.
## Correction
Replaced the three helpers (`_get_relative_embeddings`, `_relative_position_to_absolute_position`, `_absolute_position_to_relative_position`) with index/gather versions that keep the length dynamic. Checked first that they equal the originals exactly (difference 0.0 for lengths 1..200), then ran parity at 1, 7, 200 and 600 frames (about 3e-7).
## Prevention rule
After any tracing export, run the ONNX model at several lengths different from the example (at least one shorter and one longer than any window or kernel in the model) and treat every TracerWarning about Python conversion as a defect until such a run passes.
## Detection check
The export test or its spike runs the exported graph with at least three different dynamic sizes; `grep -c TracerWarning` of the export log is zero or each remaining warning is explained.
## Evidence
S-013 attempt 1: T-P19 failed at frames=200 before the fix and passed after; research notes in knowledge K-*-rvc-attention-trace.
