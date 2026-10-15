---
id: L-20261015T073300Z-script-resolved-its-own-directory-after-cd
title: 'The sketch harness looked up a helper with $(dirname "$0") after changing directory, so the helper silently never ran'
status: active
supersedes: []
recurrence_of: null
occurrences: 1
severity: Low
tags: [tech:bash, kind:tooling, phase:planning]
recorded_by: planner
run: gen-20261004T095012Z-singing-voice-vst-pitch-lyrics
recorded_at: 2026-10-15T07:33:00Z
---
## Trigger
A shell script invoked with a relative path changes directory and later refers to files next to itself.
## What went wrong
sketch_docs.py was never executed; the notebook tests still failed with 'missing notebooks' and the output looked like a test defect.
## Correction
Resolve the script's own directory once at the top (D=$(cd "$(dirname "$0")" && pwd)) and report a failed helper explicitly.
## Prevention rule
Resolve the script directory to an absolute path before any cd, and make helper failures print a FAILED line.
## Detection check
`grep -n 'dirname "\$0"' research/spikes/*/run.sh` shows uses only in the first lines.
## Evidence
research/spikes/sketch-py/run.sh before and after commit 5365bb3.
