---
id: K-20261024T151049Z-rvc-attention-trace
statement: "In RVC 81eed5e, infer/module/attentions.py MultiHeadAttention (window_size 10) computes its relative-position padding with int(length) and max(...), so torch.onnx.export (dynamo=False, opset 17) freezes the example sequence length; replacing _get_relative_embeddings, _relative_position_to_absolute_position and _absolute_position_to_relative_position with torch.arange/gather versions gives identical values (max abs difference 0.0 for lengths 1..200) and a graph valid for any length."
status: current
supersedes: []
tags: [subject:rvc-onnx-export, tech:python, domain:singing-voice-synthesis, phase:implementation]
applies_to_version: "RVC 81eed5e, torch 2.4.1+cpu, onnx 1.23.2, onnxruntime 1.31.0"
source: {"url": "", "doi": "", "title": "observed in S-013 of this repository", "locator": "python/singvst_train/export_rvc.py _make_attention_dynamic", "accessed": "2026-10-24", "tier": 1}
confidence: verified
derived_from: []
discovered_by: implementer
run: gen-20261004T095012Z-singing-voice-vst-pitch-lyrics
recorded_at: 2026-10-24T15:10:49Z
---
Verified by T-P19 (parity 3e-7 at 200 frames) and by extra runs at 1, 7 and 600 frames.
