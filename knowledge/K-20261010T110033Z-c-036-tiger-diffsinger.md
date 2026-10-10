---
id: K-20261010T110033Z-c-036-tiger-diffsinger
statement: "TIGER DiffSinger v102 (GitHub release v102, TIGER_DS_v102_PACK.zip, sha256 925ca2ad...) is an English DiffSinger voicebank whose acoustic model takes tokens, durations, f0, gender, velocity, spk_embed[1,T,256], depth int64 and speedup int64; it bundles its own vocoder (tgm_hifigan.onnx, 44100 Hz, hop 512, 128 mel bins), 7 speaker embeddings (raw float32, 256 values), and a 68-entry phonemes.txt that contains all 39 CMUdict ARPAbet phones."
status: current
supersedes: []
tags: [subject:tiger-diffsinger, tech:diffsinger, phase:research]
applies_to_version: "TIGER v102"
source: {"url": "research/spikes/tiger-guide/output.txt", "doi": "", "title": "spike tiger-guide", "locator": "phoneme count; inputs; vocoder.yaml", "accessed": "2026-10-10", "tier": 1}
confidence: verified
derived_from: [C-036]
discovered_by: planner
run: gen-20261004T095012Z-singing-voice-vst-pitch-lyrics
recorded_at: 2026-10-10T11:00:33Z
---
Derived mechanically from research/claims.json C-036 (software, load-bearing: True, independent publishers: 1).
Sources: spike tiger-guide <research/spikes/tiger-guide/output.txt> [phoneme count; inputs; vocoder.yaml].
