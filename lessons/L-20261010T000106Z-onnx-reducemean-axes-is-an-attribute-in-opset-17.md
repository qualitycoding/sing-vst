---
id: L-20261010T000106Z-onnx-reducemean-axes-is-an-attribute-in-opset-17
title: 'An ONNX fixture passed ReduceMean axes as an input, which opset 17 rejects'
status: active
supersedes: []
recurrence_of: null
occurrences: 1
severity: Low
tags: [tech:onnx, kind:wrong-assumption, phase:planning]
recorded_by: planner
run: gen-20261004T095012Z-singing-voice-vst-pitch-lyrics
recorded_at: 2026-10-10T00:01:06Z
---
## Trigger
Hand-built ONNX graphs with onnx.helper at opset <= 17 using Reduce* operators.
## What went wrong
`make_node('ReduceMean', ['fr', 'ax2'], ...)` failed the checker: input size 2 not in range [1, 1].
## Correction
Passed `axes=[2]` as an attribute.
## Prevention rule
Check each operator's signature for the target opset (onnx.defs.get_schema(op, opset)) before building a fixture graph, and run onnx.checker on every fixture.
## Detection check
tests/fixtures/make_onnx_fixtures.py calls onnx.checker.check_model for every model it writes.
## Evidence
make_onnx_fixtures.py traceback of 2026-10-04.
