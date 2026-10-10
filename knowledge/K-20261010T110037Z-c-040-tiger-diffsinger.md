---
id: K-20261010T110037Z-c-040-tiger-diffsinger
statement: "TIGER's acoustic graph contains 2 RandomNormalLike nodes without a seed attribute; two identical runs differ (max |mel1-mel2| = 1.86); the ONNX Runtime 1.31.0 C/C++ API exposes no seed function (only Python has onnxruntime.set_seed)."
status: current
supersedes: []
tags: [subject:tiger-diffsinger, tech:onnxruntime, phase:research]
applies_to_version: "TIGER v102; ORT 1.31.0"
source: {"url": "research/spikes/tiger-guide/output.txt", "doi": "", "title": "spike tiger-guide", "locator": "acoustic determinism line; ORT seed grep line", "accessed": "2026-10-10", "tier": 1}
confidence: verified
derived_from: [C-040]
discovered_by: planner
run: gen-20261004T095012Z-singing-voice-vst-pitch-lyrics
recorded_at: 2026-10-10T11:00:37Z
---
Derived mechanically from research/claims.json C-040 (software, load-bearing: True, independent publishers: 1).
Sources: spike tiger-guide <research/spikes/tiger-guide/output.txt> [acoustic determinism line; ORT seed grep line].
