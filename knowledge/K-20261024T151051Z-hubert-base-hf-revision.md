---
id: K-20261024T151051Z-hubert-base-hf-revision
statement: "Hugging Face lj1995/VoiceConversionWebUI main resolved to commit e6d0c1a17da07c33557852f9dfa2bd44cc75737d on 2026-10-24; its hubert_base/ folder holds config.json, preprocessor_config.json (do_normalize false, 16 kHz) and a 189 MB pytorch_model.bin, loadable by transformers HubertModel; the last_hidden_state equals RVC's v2 feature path (max abs difference 4e-5, units RMS 0.26)."
status: current
supersedes: []
tags: [subject:rvc-onnx-export, tech:python, domain:singing-voice-synthesis, phase:implementation]
applies_to_version: "huggingface_hub 2.2.0, transformers pinned by RVC requirments_cpu_py312.txt"
source: {"url": "https://huggingface.co/lj1995/VoiceConversionWebUI", "doi": "", "title": "model_info(revision='main').sha", "locator": "hubert_base/", "accessed": "2026-10-24", "tier": 1}
confidence: verified
derived_from: [C-032]
discovered_by: implementer
run: gen-20261004T095012Z-singing-voice-vst-pitch-lyrics
recorded_at: 2026-10-24T15:10:49Z
---
The CI python-torch job prints the revision it resolves as the hf-revision notice; S-013 compares it with this value before writing it to plan/ENVIRONMENT.md.
