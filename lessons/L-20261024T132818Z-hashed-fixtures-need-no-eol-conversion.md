---
id: L-20261024T132818Z-hashed-fixtures-need-no-eol-conversion
title: "A test that hashes checked-in text fixtures passed on Linux and failed on Windows because git rewrote line endings"
status: active
supersedes: []
recurrence_of: null
occurrences: 1
severity: Medium
tags: [applies:all, tech:cpp, domain:audio, kind:wrong-assumption, phase:verification]
recorded_by: implementer
run: gen-20261004T095012Z-singing-voice-vst-pitch-lyrics
recorded_at: 2026-10-24T13:28:18Z
---
## Trigger
A repository holds fixture files whose SHA-256 or byte length is compared in a test (here a voice package manifest, T-031) and has no .gitattributes; the tests also run on a Windows CI runner.
## What went wrong
S-004 was accepted on Linux alone. On windows-2022 T-031 failed while every other S-004 test passed. The CI annotation gave only "Failed". The cause (git's default autocrlf converting the text fixture phonemes.txt on checkout, so its hash no longer matched the manifest) was inferred, not read from a log.
## Correction
Added .gitattributes marking tests/fixtures/** and third_party/cmudict/** as -text. The next windows-2022 run passed T-031, which confirmed the inference.
## Prevention rule
When a test compares hashes or sizes of checked-in files, add a .gitattributes with -text for those paths in the same commit, and do not call the step done until the Windows job has passed the test.
## Detection check
`git check-attr text tests/fixtures/voice-legacy/guide/phonemes.txt` prints "text: unset", and the windows-2022 test-summary lists the hash-comparing test as passed.
## Evidence
CI run on 522825e (T-031 failed on windows-2022 only); run on d0d6918 (passed).
