---
id: K-20261024T151050Z-rvc-sinegen-noise
statement: "RVC v2 (harmonic_num 0) draws randomness in two places at inference: the prior noise torch.randn_like(m_p)*0.66666 in infer(), and torch.randn_like(sine_waves) inside SineGen.forward (amplitude sine_amp/3 = 0.0333 on unvoiced frames, 0.003 on voiced ones); SineGen's rand_ini phase offset is zero for harmonic 0, so for v2 the SineGen noise is the only other source."
status: current
supersedes: []
tags: [subject:rvc-onnx-export, tech:python, domain:singing-voice-synthesis, phase:implementation]
applies_to_version: "RVC 81eed5e"
source: {"url": "", "doi": "", "title": "RVC infer/module/models.py SineGen._f02sine and SineGen.forward", "locator": "lines 309-343 of the pinned checkout", "accessed": "2026-10-24", "tier": 1}
confidence: verified
derived_from: []
discovered_by: implementer
run: gen-20261004T095012Z-singing-voice-vst-pitch-lyrics
recorded_at: 2026-10-24T15:10:49Z
---
C-003 recorded only the first. The exporter replaces the second with values read from the rnd input (frame-major, each held 2.5 samples) so one seed fixes the whole output; with every random draw forced to zero the ONNX graph equals RVC's own infer to 2e-7.
