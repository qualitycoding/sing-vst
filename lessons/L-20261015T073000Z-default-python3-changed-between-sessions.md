---
id: L-20261015T073000Z-default-python3-changed-between-sessions
title: '/usr/bin/python3 became 3.13 between sessions, so a clean venv built with `python3 -m venv` could not install the 3.12 lock'
status: active
supersedes: []
recurrence_of: null
occurrences: 1
severity: Medium
tags: [applies:all, tech:python, kind:environment, phase:planning]
recorded_by: planner
run: gen-20261004T095012Z-singing-voice-vst-pitch-lyrics
recorded_at: 2026-10-15T07:30:00Z
---
## Trigger
A run resumes after days in a sandbox it does not control; a lock pins packages for one Python minor version (here 3.12).
## What went wrong
`python3 -m venv` picked Python 3.13.16; pip found no cp313 wheel for scipy 1.13.1 and tried to build it from source (meson: no Fortran compiler), so the clean-room install failed.
## Correction
Rebuilt the venv with /usr/bin/python3.12 explicitly; the lock then reproduced exactly and pyworld's extension loaded.
## Prevention rule
Name the interpreter by its full minor version (python3.12) in every venv, script and CI step; never rely on `python3`.
## Detection check
`grep -rn 'python3 -m venv' tools research/spikes .github` prints nothing; plan/ENVIRONMENT.md names /usr/bin/python3.12.
## Evidence
venv-lock.install.log: 'ERROR: Unknown compiler(s): [[gfortran] ...' under /usr/lib/python3.13.
