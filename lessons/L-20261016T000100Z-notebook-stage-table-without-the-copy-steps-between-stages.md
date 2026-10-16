---
id: L-20261016T000100Z-notebook-stage-table-without-the-copy-steps-between-stages
title: "A notebook spec listed stage outputs that no command produced (split folders, render-bin contents, voicebank folder)"
status: active
supersedes: []
recurrence_of: null
occurrences: 1
severity: High
tags: [domain:ml-training, tech:colab, kind:missing-spec, phase:planning]
recorded_by: planner
run: gen-20261004T095012Z-singing-voice-vst-pitch-lyrics
recorded_at: 2026-10-16T00:01:00Z
---
## Trigger
A plan specifies a hosted notebook as a list of commands plus a stage table of inputs and outputs.
## What went wrong
Cold read pass 4 items S1/S2: `split` writes only split.json but the table promised train/ and heldout/; out/bin/ had no copy command; the voicebank folder, cell order, interpreter spelling and uv index flags were unstated, and the owner would have paid GPU time to find out.
## Correction
D-035 gives a literal command for every table output, the cell order (19 cells), the PATH rule and the uv index flags.
## Prevention rule
For every row of a stage table, name the literal command that creates each output from each input; a row without one is a gap.
## Detection check
For each stage-table output, grep D-035 for the command that writes it.
## Evidence
premortem/coldread-pass-4.md S1, S2; plan/DECISIONS.md D-035.
