---
id: K-20261010T110023Z-c-026-windows-dll-loading
statement: "Some Windows installations carry C:\\Windows\\System32\\onnxruntime.dll (placed by Windows), and programs that load onnxruntime.dll by name can bind to it instead of their own copy; ONNX Runtime collaborators advise loading by explicit path and resolving OrtGetApiBase."
status: current
supersedes: []
tags: [subject:windows-dll-loading, tech:onnxruntime, phase:research]
applies_to_version: "version-independent"
source: {"url": "https://github.com/microsoft/onnxruntime/issues/11799", "doi": "", "title": "onnxruntime issue 11799", "locator": "maintainer: 'By Windows team'", "accessed": "2026-10-10", "tier": 2}
confidence: corroborated
derived_from: [C-026]
discovered_by: planner
run: gen-20261004T095012Z-singing-voice-vst-pitch-lyrics
recorded_at: 2026-10-10T11:00:23Z
---
Derived mechanically from research/claims.json C-026 (software, load-bearing: True, independent publishers: 3).
Sources: onnxruntime issue 11799 <https://github.com/microsoft/onnxruntime/issues/11799> [maintainer: 'By Windows team']; onnxruntime discussion 23239 <https://github.com/microsoft/onnxruntime/discussions/23239> [fdwr 2025-02-27]; sherpa-onnx issue 3059 <https://github.com/k2-fsa/sherpa-onnx/issues/3059> [API version [23] not available, 1.17.1 loaded]; Dynamic-link library search order <https://learn.microsoft.com/en-us/windows/win32/dlls/dynamic-link-library-search-order> [standard search order].
