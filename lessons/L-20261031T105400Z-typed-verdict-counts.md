---
id: L-20261031T105400Z-typed-verdict-counts
title: "Verdict counts in a report header were typed and were wrong"
status: active
supersedes: []
recurrence_of: L-20261004T102009
occurrences: 1
severity: Low
tags: [applies:all, kind:process, phase:verification]
recorded_by: implementer
run: gen-20261004T095012Z-singing-voice-vst-pitch-lyrics
recorded_at: 2026-10-31T10:54:00Z
---
## Trigger
A report written in one heredoc carries a summary line with counts of rows written further down in the same file.
## What went wrong
premortem/ASSUMPTION_AUDIT.md said "confirmed 24 · falsified 4 · unverifiable 13"; counting the table rows gave 25 / 4 / 11. The summary was written from memory while drafting, which PK-05 forbids; the earlier rule did not prevent it because the counts sat in prose, not in a status header the generator owns.
## Correction
The header line is now produced by a script that counts the table rows and asserts every row has a verdict (commit 584ec59).
## Prevention rule
Write any count in a document only by running a command over the finished document (or its source data) after the rows exist, and assert the classification covers every row; never type a count into a template.
## Detection check
`grep -nE '[0-9]+ (confirmed|falsified|unverifiable|passed|failed|items?)' <report>` — each hit is traceable to a command recorded in the commit or EXECUTION_LOG.md.
## Evidence
premortem/ASSUMPTION_AUDIT.md before/after 584ec59; PK-05 (research/PRIOR_KNOWLEDGE.md).
