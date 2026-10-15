# Sources

Generated from research/claims.json by `python3 tools/gen/sources.py`. Tier 1 = official docs, source code at the
pinned version, specifications, or a committed spike; Tier 2 = maintainer statements, release notes, issue trackers; Tier 3
= reputable secondary write-ups; Tier 4 = forums (never sufficient alone). Every source was opened in this run (PK-06).

| Source | URL / path | Tier | Version | Accessed | Locators | Supports |
|---|---|---|---|---|---|---|
| Colab FAQ | https://research.google.com/colaboratory/faq.html | 1 |  | 2026-10-04 | Resource Limits; drive.mount; Which activities are restricted in Colab? | C-017 (corroborated), C-018 (corroborated) |
| DiffSingerRenderer.cs | https://github.com/openutau/OpenUtau/blob/a06ab28b0ae011bd0b85926f3044572be46a7a63/OpenUtau.Core/DiffSinger/DiffSingerRenderer.cs | 1 |  | 2026-10-10 | lines 288-313 | C-034 (verified) |
| DiffSingerUtils.cs | https://github.com/openutau/OpenUtau/blob/a06ab28b0ae011bd0b85926f3044572be46a7a63/OpenUtau.Core/DiffSinger/DiffSingerUtils.cs | 1 |  | 2026-10-10 | lines 15-83 | C-038 (verified) |
| Dynamic-link library search order | https://learn.microsoft.com/en-us/windows/win32/dlls/dynamic-link-library-search-order | 1 |  | 2026-10-10 | standard search order | C-026 (corroborated) |
| GitHub API repository metadata | https://api.github.com/repos/svc-develop-team/so-vits-svc | 1 |  | 2026-10-04 | archived, pushed_at | C-002 (verified) |
| LICENSE | https://github.com/RVC-Project/Retrieval-based-Voice-Conversion-WebUI/blob/81eed5e8f68b6bed1789f682fe78cdd324495afc/LICENSE | 1 |  | 2026-10-10 | file | C-001 (verified) |
| TIGER LICENSE.md | https://github.com/spicytigermeat/tiger_diffsinger/blob/988ec2c2dd23b7b28c448e1a6db710bfa20c5583/LICENSE.md | 1 |  | 2026-10-10 | file | C-037 (verified) |
| TIGER repository README and LICENSE.md | https://github.com/spicytigermeat/tiger_diffsinger | 1 |  | 2026-10-10 | License section | C-010 (single-source) |
| character_usage_tos.md | https://github.com/spicytigermeat/tiger_diffsinger/blob/988ec2c2dd23b7b28c448e1a6db710bfa20c5583/character_usage_tos.md | 1 |  | 2026-10-10 | allowed list | C-037 (verified) |
| infer/module/models.py | https://github.com/RVC-Project/Retrieval-based-Voice-Conversion-WebUI/blob/81eed5e8f68b6bed1789f682fe78cdd324495afc/infer/module/models.py | 1 |  | 2026-10-10 | lines 646-676 | C-003 (verified) |
| oracle rvc_coarse | research/spikes/oracle/oracle.py | 1 |  | 2026-10-10 | function rvc_coarse | C-021 (verified) |
| release notes | https://github.com/Tracktion/pluginval/releases/tag/v1.0.4 | 1 |  | 2026-10-04 | 1.0.0 changes | C-015 (verified) |
| spike deps-pins | research/spikes/deps-pins/output.txt | 1 |  | 2026-10-14 | downloads, tag commits | C-049 (verified) |
| spike hf-cli | research/spikes/hf-cli/output.txt | 1 |  | 2026-10-15 | hf download --help | C-053 (verified) |
| spike hf-cli (PyPI JSON for transformers 4.49.0) | research/spikes/hf-cli/output.txt | 1 |  | 2026-10-15 | requires_dist | C-054 (verified) |
| spike hf-cli (RVC README.md lines 170-190) | research/spikes/hf-cli/output.txt | 1 |  | 2026-10-15 | README download commands | C-052 (verified) |
| spike hosts | research/spikes/hosts/output.txt | 1 |  | 2026-10-14 | all lines | C-044 (verified) |
| spike juce-lyrics | research/spikes/juce-lyrics/output.txt | 1 |  | 2026-10-10 | output.txt | C-013 (verified) |
| spike ort | research/spikes/ort/output.txt | 1 |  | 2026-10-10 | sha256 lines, ORT 1.31.0 out[0]=9 | C-014 (verified) |
| spike ort-manual-init | research/spikes/ort-manual-init/output.txt | 1 |  | 2026-10-10 | output.txt | C-042 (verified) |
| spike pip-audit-setuptools | research/spikes/pip-audit-setuptools/output.txt | 1 |  | 2026-10-14 | PYSEC-2026-3447 rows | C-046 (verified) |
| spike plugin-stub | research/spikes/plugin-stub/output.txt | 1 |  | 2026-10-14 | bundle, pluginval lines; packages, build exit | C-050 (verified), C-051 (verified) |
| spike pyfacts | research/spikes/pyfacts/output.txt | 1 |  | 2026-10-10 | audio-separator wheel inspection; resemblyzer wheel listing | C-028 (verified), C-043 (verified) |
| spike pyworld | research/spikes/pyworld/output.txt | 1 |  | 2026-10-14 | all '==' lines; pip install lines (wheel downloads) | C-027 (verified), C-044 (verified) |
| spike pyworld-direct | research/spikes/pyworld-direct/output.txt | 1 |  | 2026-10-14 | all '==' lines | C-046 (verified) |
| spike rvc-resume | research/spikes/rvc-resume/output.txt | 1 |  | 2026-10-14 | inference weights lines; resume and checkpoint lines | C-047 (verified), C-048 (verified) |
| spike tiger-guide | research/spikes/tiger-guide/output.txt | 1 |  | 2026-10-10 | acoustic determinism line; ORT seed grep line; acoustic inputs; acoustic/vocoder timing line; frames 188 (incl. 8+8 pad), waveform 188.0 frames; pack extra/LICENSE.md (read 2026-10-10); phoneme count; inputs; vocoder.yaml; rank0/rank1 lines; rank0/rank1 scalars accepted; render | C-009 (verified), C-034 (verified), C-036 (verified), C-037 (verified), C-038 (verified), C-039 (verified), C-040 (verified), C-041 (verified) |
| spike upstream-facts | research/spikes/upstream-facts/output.txt | 1 |  | 2026-10-10 | PASS C-001; PASS C-002a; PASS C-003a/b/c; PASS C-004; PASS C-005; PASS C-006a/b; PASS C-007a; PASS C-009a..e; PASS C-011a/b; PASS C-012a/b; PASS C-015a/b/c; PASS C-016a/b; sha256 line; PASS C-020a/b/c; PASS C-021a/b; PASS C-022a/b/c; PASS C-023a/b/c; PASS C-024; PASS C-029; PASS C-030; PASS C-031; PASS C-032; PASS C-033; PASS C-034; PASS C-035; upstream tips (drift check) | C-001 (verified), C-002 (verified), C-003 (verified), C-004 (verified), C-005 (verified), C-006 (verified), C-007 (verified), C-009 (verified), C-011 (verified), C-012 (verified), C-015 (verified), C-016 (verified), C-020 (verified), C-021 (verified), C-022 (verified), C-023 (verified), C-024 (verified), C-029 (verified), C-030 (verified), C-031 (verified), C-032 (verified), C-033 (verified), C-034 (verified), C-035 (verified), C-045 (verified) |
| spike vocoder-onnx | research/spikes/vocoder-onnx/output.txt | 1 |  | 2026-10-10 | licence line, inputs, outputs | C-007 (verified) |
| onnxruntime discussion 23239 | https://github.com/microsoft/onnxruntime/discussions/23239 | 2 |  | 2026-10-10 | fdwr 2025-02-27 | C-026 (corroborated) |
| onnxruntime issue 11799 | https://github.com/microsoft/onnxruntime/issues/11799 | 2 |  | 2026-10-10 | maintainer: 'By Windows team' | C-026 (corroborated) |
| sherpa-onnx issue 3059 | https://github.com/k2-fsa/sherpa-onnx/issues/3059 | 2 |  | 2026-10-10 | API version [23] not available, 1.17.1 loaded | C-026 (corroborated) |
| BleepingComputer | https://www.bleepingcomputer.com/news/google/google-quietly-bans-deepfake-training-projects-on-colab | 3 |  | 2026-10-10 | article 2022-05-30 | C-018 (corroborated) |
| Free Cloud GPUs in 2026 | https://gpuperhour.com/blog/free-cloud-gpus-and-credits | 3 |  | 2026-10-04 | Kaggle | C-019 (single-source) |
| Hivenet guide | https://www.hivenet.com/post/google-colaboratory-gpu-complete-guide-to-free-cloud-gpu-access-and-limitations | 3 |  | 2026-10-04 | Free tier | C-017 (corroborated) |
| Notre Dame course notes | https://www3.nd.edu/~dchiang/teaching/nlp/2023/kaggle.html | 3 |  | 2026-10-04 | batch sessions | C-019 (single-source) |
| OpenUtau voicebank development | https://www.openutau.com/Voicebank-development/ | 3 |  | 2026-10-10 | Machine Learning voicebank development | C-010 (single-source) |

37 sources, 52 claims.
