---
id: K-20261024T133254Z-ort-typeinfo-view-lifetime
statement: "In the ONNX Runtime 1.31.0 C++ API, Ort::TypeInfo::GetTensorTypeAndShapeInfo() returns a non-owning ConstTensorTypeAndShapeInfo; the owning Ort::TypeInfo must stay alive while the view is used, otherwise GetShape() and GetElementType() return garbage without any sanitizer report."
status: current
supersedes: []
tags: [subject:onnxruntime-cpp-api, tech:cpp, phase:implementation]
applies_to_version: "onnxruntime 1.31.0"
source: {"url": "", "doi": "", "title": "observed in S-008 of this repository (T-042, T-043)", "locator": "core/src/ort_util.cpp loadModel", "accessed": "2026-10-24", "tier": 1}
confidence: verified
derived_from: []
discovered_by: implementer
run: gen-20261004T095012Z-singing-voice-vst-pitch-lyrics
recorded_at: 2026-10-24T13:32:52Z
---
Observed: with the view taken from a temporary, input ranks were reported as 0 for a rank-1 input; after binding the TypeInfo to a local the shapes were correct.
