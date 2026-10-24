---
id: L-20261024T133253Z-spike-passed-for-the-wrong-reason
title: "A rejection check passed because the test fixture was incomplete, not because the feature worked"
status: active
supersedes: []
recurrence_of: null
occurrences: 1
severity: Medium
tags: [applies:all, tech:cpp, kind:verification-gap, phase:verification]
recorded_by: implementer
run: gen-20261004T095012Z-singing-voice-vst-pitch-lyrics
recorded_at: 2026-10-24T13:32:52Z
---
## Trigger
A throw-away check asserts "the bad input is rejected" by expecting an exception of one type.
## What went wrong
The S-008 external-data check put the external-data model in an otherwise empty folder. The engine threw ValidationError ("phonemes.txt: missing"), the check printed PASS, and output.txt would have been committed as evidence that external data is rejected. It was rejected for an unrelated reason.
## Correction
The check now builds a complete voice folder whose only difference from the accepted fixture is the external-data model, and asserts the message contains "external data". Both the accepting and the rejecting run use the same folder shape.
## Prevention rule
For every "X is rejected" check, assert the exception's message names X and run the same scenario with X fixed to show it is accepted.
## Detection check
In the evidence file, the line before each PASS for a rejection prints the exception text, and that text names the feature under test.
## Evidence
research/spikes/s008-external-data/output.txt (second version); first version printed "ValidationError: phonemes.txt: missing or not a regular file" next to PASS.
