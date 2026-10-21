---
id: K-20261021T200000Z-c-066-audio-separator
statement: "audio-separator 0.47.0 (PyPI wheel sha256 756f3b62\u2026) exports Separator(model_file_dir, output_dir, output_format='WAV', output_single_stem, \u2026), load_model(model_filename) and separate(audio_file_path, custom_output_names); custom_output_names keys are stem names matched case-insensitively and give <name>.<format> in output_dir; the de-reverb model's stems are noreverb/reverb; it requires numpy>=2 while RVC 81eed5e's cu128 file pins numpy<2, so the two cannot be resolved into one environment (uv pip compile: no solution), but audio-separator resolves on its own with torch 2.7.1."
status: current
supersedes: []
tags: [subject:audio-separator, domain:hosted-gpu, phase:research]
applies_to_version: "audio-separator 0.47.0"
source: {"url": "research/spikes/audio-separator-047/output.txt", "doi": "", "title": "spike audio-separator-047 (wheel inspection and uv resolution)", "locator": "whole file", "accessed": "2026-10-21", "tier": 1}
confidence: verified
derived_from: [C-066]
discovered_by: planner
run: gen-20261004T095012Z-singing-voice-vst-pitch-lyrics
recorded_at: 2026-10-21T20:00:00Z
---
Derived mechanically from research/claims.json C-066 (software, load-bearing: True, independent publishers: 1).
Sources: spike audio-separator-047 (wheel inspection and uv resolution) <research/spikes/audio-separator-047/output.txt> [whole file].
