---
id: L-20261016T140100Z-spike-checked-a-source-literal-not-the-emitted-value
title: "A detector searched logs for the source-code literal of a message that the program translates before logging"
status: active
supersedes: []
recurrence_of: null
occurrences: 1
severity: Medium
tags: [applies:all, kind:wrong-assumption, phase:planning]
recorded_by: planner
run: gen-20261004T095012Z-singing-voice-vst-pitch-lyrics
recorded_at: 2026-10-16T14:01:00Z
---
## Trigger
A check matches program output (log text, messages) against strings read from the program's source.
## What went wrong
Pre-mortem round 2 R-057: RVC logs i18n("已加载生成器预训练模型：%s"), which is English under en_US, so the planned Chinese-literal check could never fire.
## Correction
Detection by value (checkpoint iteration before/after) plus both locale strings (C-063).
## Prevention rule
Prefer value checks to message matching; when matching text, verify the emitted text (formatting, translation) not the source literal.
## Detection check
Every log-text check names where the emitted string was observed or how it is produced.
## Evidence
premortem/round-2.md R-057; research/spikes/premortem-r2/rvc_checkpoint_i18n.txt.
