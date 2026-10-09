---
id: L-20261010T000108Z-scripted-replace-inserted-comment-into-an-expression
title: "A scripted str.replace appended a '#' comment inside a list literal and broke the fixture generator's syntax"
status: active
supersedes: []
recurrence_of: L-20261004T150700Z-scripted-str-replace-silently-no-opped
occurrences: 1
severity: Low
tags: [tech:python, kind:tooling, phase:planning]
recorded_by: planner
run: gen-20261004T095012Z-singing-voice-vst-pitch-lyrics
recorded_at: 2026-10-10T00:01:08Z
---
## Trigger
Editing Python source with a script that splices text into the middle of a line.
## What went wrong
The replacement added '  # opset 17: axes is an attribute' before a closing comma, so the rest of the line became a comment.
## Correction
Removed the comment and re-ran the generator.
## Prevention rule
After any scripted edit of source code, run the file (or py_compile it) in the same command, and never splice comments into the middle of a line.
## Detection check
`python -m py_compile <file>` after each scripted edit.
## Evidence
SyntaxError in make_onnx_fixtures.py on 2026-10-04.
