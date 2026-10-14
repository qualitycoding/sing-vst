---
id: L-20261014T203000Z-oracle-had-three-rule-defects-and-no-checks-of-its-own
title: 'The independent oracle written to validate frozen expectations encoded three defective rules and had no tests of its own'
status: active
supersedes: []
recurrence_of: null
occurrences: 1
severity: High
tags: [applies:all, tech:python, domain:singing-voice-synthesis, kind:verification-gap, phase:planning]
recorded_by: planner
run: gen-20261004T095012Z-singing-voice-vst-pitch-lyrics
recorded_at: 2026-10-14T20:30:00Z
---
## Trigger
A reference implementation ('oracle') is written to check expected values in tests that are about to be frozen, before any decision text exists and without its own invariant checks.
## What went wrong
research/spikes/oracle/oracle.py (2026-10-10) dropped the next syllable's onset after a vowel-less syllable ('hmm hello' lost 'hh'), let frame durations overshoot their own stated total (sum 55 for a total of 50), and let a zero-length note with an equal start delete the real note. Every expected value checked against it would have inherited these errors into the frozen suite.
## Correction
Fixed the three rules in the oracle and in plan/DECISIONS.md (D-006, D-007), added research/spikes/oracle/properties.py (randomised invariants: one note per distinct start, highest pitch kept, phones conserved in order with one SP per gap, exact frame totals, f0 frame count), and showed it fails on the unpatched oracle (4 invariant failures) and passes on the patched one (0 of 6000 cases).
## Prevention rule
Before an oracle checks any frozen expectation, give it randomised invariant checks derived from the decisions, and show those checks fail on a deliberately broken copy.
## Detection check
`python -I research/spikes/oracle/properties.py 3000` exits 0 and research/spikes/oracle/properties-output.txt shows 0 failures; the mutation run is recorded in research/rounds/round-5.md.
## Evidence
research/spikes/oracle/properties-output.txt; mutation run against `git show 6fe0e5d:research/spikes/oracle/oracle.py` (4 failures).
