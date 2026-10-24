---
id: L-20261024T133252Z-ort-typeinfo-view-dangles
title: "A view returned by Ort::TypeInfo::GetTensorTypeAndShapeInfo outlived its TypeInfo temporary and produced wrong input shapes"
status: active
supersedes: []
recurrence_of: null
occurrences: 1
severity: Medium
tags: [applies:all, tech:cpp, domain:audio, kind:wrong-assumption, phase:implementation]
recorded_by: implementer
run: gen-20261004T095012Z-singing-voice-vst-pitch-lyrics
recorded_at: 2026-10-24T13:32:52Z
---
## Trigger
C++ code reads a model input's shape or element type with `session.GetInputTypeInfo(i).GetTensorTypeAndShapeInfo()` and keeps the result in a variable.
## What went wrong
`GetInputTypeInfo(i)` returns a temporary Ort::TypeInfo. `GetTensorTypeAndShapeInfo()` on it returns a non-owning view into that object. Storing the view let the temporary die at the end of the statement. The recorded shapes were wrong: T-043 failed with "Invalid rank for input: steps Got: 0 Expected: 1" and T-042 missed a speaker-size mismatch. It compiled without warning and AddressSanitizer did not flag it.
## Correction
Bind the TypeInfo to a named local first and take the view from that local (core/src/ort_util.cpp, loadModel).
## Prevention rule
Never call a method that returns a view on an ONNX Runtime temporary and keep the result; name the owning object, or copy the data out (GetShape(), GetElementType()) in the same full expression.
## Detection check
`grep -n "GetTensorTypeAndShapeInfo" core/src` shows each call on a named object or immediately consumed (GetElementCount, GetShape).
## Evidence
S-008 attempt 1: T-042 and T-043 failed, then passed after the one-line fix; T-042..T-047 pass under ASan+UBSan.
