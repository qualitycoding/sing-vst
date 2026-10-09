---
id: L-20261010T000110Z-fixture-entry-count-typed-instead-of-computed
title: 'T-007 expected 23 dictionary words for a fixture that has 22, because a variant line was counted as a word'
status: active
supersedes: []
recurrence_of: L-20261009T192611Z-tracked-file-count-typed-in-a-prompt-was-wrong
occurrences: 1
severity: Low
tags: [tech:cpp, kind:verification-gap, phase:planning]
recorded_by: planner
run: gen-20261004T095012Z-singing-voice-vst-pitch-lyrics
recorded_at: 2026-10-10T00:01:10Z
---
## Trigger
A test asserts a count derived from a fixture file.
## What went wrong
The expected size was counted by eye from `wc -l` (24 lines, 2 variants) and written as 23.
## Correction
Computed it from the file with the same rule the parser uses (22).
## Prevention rule
Compute every expected count in a test from the fixture with a committed script, and paste the script's output.
## Detection check
research/spikes/fixture-counts.txt lists the computation for every count asserted in tests.
## Evidence
test_g2p.cpp edit on 2026-10-04.
