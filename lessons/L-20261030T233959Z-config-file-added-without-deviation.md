---
id: L-20261030T233959Z-config-file-added-without-deviation
title: "A build script added beside a planned CMake file was not logged as a deviation"
status: active
supersedes: []
recurrence_of: null
occurrences: 1
severity: Low
tags: [applies:all, tech:cmake, kind:process, phase:implementation]
recorded_by: implementer
run: gen-20261004T095012Z-singing-voice-vst-pitch-lyrics
recorded_at: 2026-10-30T23:39:59Z
---
## Trigger
A step's Outputs name one file (here cli/CMakeLists.txt), and the implementation needs a second, helper file next to it (a CMake -P script, a config file, a generator).
## What went wrong
S-010 added cli/git_commit.cmake to satisfy "a custom command that runs on every build" and logged the other S-010 departures, but not this added file. The protocol v3.6 deviation-completeness audit (3.7.1 1a) found it 20 days later by diffing the branch against the plan's Outputs.
## Correction
DEVIATIONS.md gained the S-010 row; reviews/DEVIATION_AUDIT.md lists every difference and its row.
## Prevention rule
Before each Save, compare `git diff --name-only --cached` with the step's Outputs and log every extra file, pin, timeout or config file in DEVIATIONS.md in the same commit.
## Detection check
`git diff --name-only <plan branch>...HEAD` minus the Outputs of the completed steps is empty or every remaining path appears in DEVIATIONS.md (reviews/DEVIATION_AUDIT.md method).
## Evidence
reviews/DEVIATION_AUDIT.md (AM-07); DEVIATIONS.md S-010 row recorded 2026-10-30T23:39:59Z.
