---
id: L-20261015T073200Z-secret-scan-test-contained-a-literal-it-scans-for
title: 'The secret-scan test planted a private-key marker as a literal, so its own whole-repository scan would have reported the test file'
status: active
supersedes: []
recurrence_of: null
occurrences: 1
severity: Low
tags: [tech:python, kind:verification-gap, phase:planning]
recorded_by: planner
run: gen-20261004T095012Z-singing-voice-vst-pitch-lyrics
recorded_at: 2026-10-15T07:32:00Z
---
## Trigger
A test plants strings that a scanner must detect and also asserts that the scanned repository (which contains the test) is clean.
## What went wrong
test_security.py contained the literal '-----BEGIN RSA PRIVATE KEY-----' while asserting scan_secrets(root) == [].
## Correction
Assembled the marker from two parts at run time ('...PRIV' + 'ATE KEY-----'), like the token strings in the same test.
## Prevention rule
Build every planted secret from concatenated parts at run time; grep the repository with the scanner's own patterns before committing.
## Detection check
`grep -rnE 'BEGIN [A-Z ]*PRIVATE KEY-----|github_pat_[A-Za-z0-9_]{20,}' --exclude-dir=.git .` prints nothing.
## Evidence
Commit f6ee132.
