---
id: L-20261010T000105Z-juce-cmake-needs-c-language-enabled
title: 'Configuring a project that adds JUCE failed because `project()` enabled only CXX'
status: active
supersedes: []
recurrence_of: null
occurrences: 1
severity: Low
tags: [tech:juce, tech:cmake, kind:wrong-assumption, phase:planning]
recorded_by: planner
run: gen-20261004T095012Z-singing-voice-vst-pitch-lyrics
recorded_at: 2026-10-10T00:01:05Z
---
## Trigger
A new CMake project calls add_subdirectory or FetchContent on JUCE 9.0.3 with `project(... LANGUAGES CXX)`.
## What went wrong
Configure stopped at JUCE/CMakeLists.txt:40: 'A C compiler is required to build targets that depend on JUCE'.
## Correction
Changed the project to `LANGUAGES C CXX`.
## Prevention rule
Declare `LANGUAGES C CXX` in any CMake project that consumes JUCE.
## Detection check
`grep -n 'LANGUAGES C CXX' CMakeLists.txt` matches.
## Evidence
red-cfg.log of 2026-10-04; K-20261010T001405Z-juce-cmake-requires-c.
