---
id: L-20261014T220000Z-hand-derived-test-expectations-wrong-at-boundaries
title: 'Three expected values written by hand into tests were wrong; the oracle cross-check caught all three before the freeze'
status: active
supersedes: []
recurrence_of: null
occurrences: 1
severity: Medium
tags: [applies:all, tech:cpp, kind:verification-gap, phase:planning]
recorded_by: planner
run: gen-20261004T095012Z-singing-voice-vst-pitch-lyrics
recorded_at: 2026-10-14T22:00:00Z
---
## Trigger
Writing expected values for tests about rounding, indexing or set membership by mental arithmetic, before running them through an independent oracle.
## What went wrong
test_g2p.cpp asserted 'ao' was absent from the mini dictionary (it occurs in 'song'); test_playback.cpp expected sample 1 at exactly half a sample (binary rounding of 4 + x - 4 gives 0.4999...) and sample 47999 at ppq 5.99998 (that is sample 47999.52, which rounds out of range).
## Correction
Re-derived each expectation with research/spikes/oracle/check_expectations.py, changed the fixture duplicate line to a phone no other word uses (zh), and moved the rounding cases off exact .5 boundaries (0.6 / 0.4 sample) and onto the exact last-sample position.
## Prevention rule
Compute every expected value with the oracle before writing it into a test, and keep inputs away from exact rounding boundaries unless the boundary is the subject (then build the input so the boundary is exact in binary).
## Detection check
`python -I research/spikes/oracle/check_expectations.py` reports 0 mismatches and is run before every test-file commit.
## Evidence
check_expectations output: 'MISMATCH T-007 hasPhone ao', 'MISMATCH T-032 ppq 4.000020833333333', 'MISMATCH T-032 ppq 5.99998'.
