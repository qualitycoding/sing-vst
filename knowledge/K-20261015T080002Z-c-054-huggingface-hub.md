---
id: K-20261015T080002Z-c-054-huggingface-hub
statement: "transformers 4.49.0 (RVC 81eed5e pins >=4.49.0,<4.50) requires huggingface-hub <1.0,>=0.26.0, so the hf 2.2.0 CLI must be installed in a separate venv from RVC's environment."
status: current
supersedes: []
tags: [subject:huggingface-hub, tech:python, tech:rvc, phase:research]
applies_to_version: "transformers 4.49.0"
source: {"url": "research/spikes/hf-cli/output.txt", "doi": "", "title": "spike hf-cli (PyPI JSON for transformers 4.49.0)", "locator": "requires_dist", "accessed": "2026-10-15", "tier": 1}
confidence: verified
derived_from: [C-054]
discovered_by: planner
run: gen-20261004T095012Z-singing-voice-vst-pitch-lyrics
recorded_at: 2026-10-15T08:00:02Z
---
Derived mechanically from research/claims.json C-054 (software, load-bearing: True, independent publishers: 1).
Sources: spike hf-cli (PyPI JSON for transformers 4.49.0) <research/spikes/hf-cli/output.txt> [requires_dist].
