---
id: L-20261014T195600Z-claims-generator-hard-coded-knowledge-item-date
title: 'The claims generator stamped every new knowledge item 2026-10-10T11:00:<index>Z regardless of when the claim was added'
status: active
supersedes: []
recurrence_of: null
occurrences: 1
severity: Low
tags: [applies:all, tech:python, kind:verification-gap, phase:planning]
recorded_by: planner
run: gen-20261004T095012Z-singing-voice-vst-pitch-lyrics
recorded_at: 2026-10-14T19:56:00Z
---
## Trigger
A generator writes dated records (knowledge items, lessons) and is re-run in later sessions to add new entries.
## What went wrong
tools/gen/claims.py built the item timestamp from a fixed prefix plus the claim's list index and accepted but ignored a kstamp argument, so C-046 (found 2026-10-14) would have been recorded as discovered on 2026-10-10.
## Correction
Stored kstamp on each claim, used it for the item ID and recorded_at when given, and gave C-046 its real time (2026-10-14T19:50:00Z).
## Prevention rule
Generators of dated records take the timestamp from the record's own field or the clock, never from a constant; a claim added after the first generation run carries kstamp.
## Detection check
`grep -L 'recorded_at: 2026-10-10' knowledge/K-20261014*.md` lists every item stamped 20261014.
## Evidence
tools/gen/claims.py lines 18-21 and 150 before and after this commit.
