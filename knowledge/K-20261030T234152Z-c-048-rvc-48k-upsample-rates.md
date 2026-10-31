---
id: K-20261030T234152Z-c-048-rvc-48k-upsample-rates
statement: "RVC 81eed5e configs/v2/48k.json sets upsample_rates [12,10,2,2] (product 480 = hop at 48 kHz), upsample_kernel_sizes [24,20,4,4] and upsample_initial_channel 512."
status: current
supersedes: [K-20261014T201001Z-c-048-rvc]
tags: [subject:rvc, tech:python, phase:implementation]
applies_to_version: "RVC 81eed5e"
source: {"url": "https://github.com/RVC-Project/Retrieval-based-Voice-Conversion-WebUI/blob/81eed5e8f68b6bed1789f682fe78cdd324495afc/configs/v2/48k.json", "doi": "", "title": "RVC configs/v2/48k.json", "locator": "model.upsample_rates", "accessed": "2026-10-30", "tier": 1}
confidence: verified
derived_from: [C-048]
discovered_by: implementer
run: gen-20261004T095012Z-singing-voice-vst-pitch-lyrics
recorded_at: 2026-10-30T23:41:48Z
---
C-048's text said 10,6,2,2,2; the product 480 it relied on is unchanged.
