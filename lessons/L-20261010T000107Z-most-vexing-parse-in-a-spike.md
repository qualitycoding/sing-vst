---
id: L-20261010T000107Z-most-vexing-parse-in-a-spike
title: 'A spike declared `juce::FileInputStream in (juce::File (argv[1]))`, which C++ parses as a function declaration'
status: active
supersedes: []
recurrence_of: null
occurrences: 1
severity: Low
tags: [tech:cpp, kind:tooling, phase:planning]
recorded_by: planner
run: gen-20261004T095012Z-singing-voice-vst-pitch-lyrics
recorded_at: 2026-10-10T00:01:07Z
---
## Trigger
Writing a one-off C++ spike that constructs an object from a temporary.
## What went wrong
The build failed: cannot convert 'juce::FileInputStream(juce::File*)' to 'juce::InputStream&'.
## Correction
Used brace initialisation.
## Prevention rule
Use brace initialisation for every object constructed from a temporary in C++ code.
## Detection check
The spike compiles with -Wvexing-parse enabled and no warnings.
## Evidence
research/spikes/juce-lyrics/README.md.
