---
id: L-20261010T000103Z-brace-expansion-in-dash-again
title: "cp and mkdir with brace expansion ran in dash and created a literal '{ort,juce-lyrics,cmudict}' directory"
status: active
supersedes: []
recurrence_of: L-20261009T123009Z-dash-brace-expansion-created-literal-directory
occurrences: 1
severity: Low
tags: [tech:bash, kind:tooling, phase:planning]
recorded_by: planner
run: gen-20261004T095012Z-singing-voice-vst-pitch-lyrics
recorded_at: 2026-10-10T00:01:03Z
---
## Trigger
Any command in the sandbox Bash tool containing {a,b}, arrays, PIPESTATUS or `time`.
## What went wrong
`mkdir -p research/spikes/{ort,juce-lyrics,cmudict}` and `cp dir/{a,b}` were run in /bin/sh.
## Correction
Removed the literal directory and re-ran the commands inside `bash -c`.
## Prevention rule
Prefix every command that uses brace expansion with `bash -c` and list the created tree afterwards.
## Detection check
`find . -name '*{*'` prints nothing.
## Evidence
research/spikes literal directory on 2026-10-04.
