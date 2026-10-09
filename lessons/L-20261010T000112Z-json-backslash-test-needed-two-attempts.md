---
id: L-20261010T000112Z-json-backslash-test-needed-two-attempts
title: 'A C++ test meant to send a JSON path containing one backslash sent an invalid JSON escape, then needed a second fix'
status: active
supersedes: []
recurrence_of: null
occurrences: 1
severity: Low
tags: [tech:cpp, kind:verification-gap, phase:planning]
recorded_by: planner
run: gen-20261004T095012Z-singing-voice-vst-pitch-lyrics
recorded_at: 2026-10-10T00:01:12Z
---
## Trigger
A test builds JSON text inside a C++ string literal and needs a literal backslash in the JSON value.
## What went wrong
The literal had two backslashes (one in the JSON), which is an invalid escape, so the test would pass for the wrong reason.
## Correction
Used four backslashes so the JSON contains an escaped backslash; added a parse-check of the fixture text.
## Prevention rule
Write JSON test inputs as raw string literals R"(...)" and assert in the test that the input is valid JSON before asserting the rejection reason.
## Detection check
grep shows no JSON with backslashes outside raw string literals in tests/cpp.
## Evidence
test_voice.cpp edits on 2026-10-04.
