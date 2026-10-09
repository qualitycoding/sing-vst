---
id: L-20261010T000115Z-corroborated-label-from-one-publisher
title: "Claims were labelled corroborated from two documents by the same publisher (GitHub API metadata and the same repository's file)"
status: active
supersedes: []
recurrence_of: L-20261009T123005Z-corroborated-label-without-independent-sources
occurrences: 1
severity: Medium
tags: [applies:all, kind:verification-gap, phase:planning]
recorded_by: planner
run: gen-20261004T095012Z-singing-voice-vst-pitch-lyrics
recorded_at: 2026-10-10T00:01:15Z
---
## Trigger
A claim's sources are an API view and a file of the same upstream project.
## What went wrong
C-001 and similar claims counted the GitHub API and the repository's LICENSE as independent.
## Correction
Re-checked each code-level claim with a committed spike that clones the pinned commit and asserts the fact, which makes it verified, and recorded the publisher count on every claim.
## Prevention rule
Record independent_publishers on every claim, and label a claim corroborated only when that count is at least 2; facts in pinned source code are made verified by a spike instead.
## Detection check
tools/check_claims.py fails if a corroborated claim has independent_publishers < 2.
## Evidence
research/claims.json of 2026-10-04.
