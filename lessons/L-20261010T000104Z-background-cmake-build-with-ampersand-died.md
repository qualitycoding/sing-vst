---
id: L-20261010T000104Z-background-cmake-build-with-ampersand-died
title: 'A JUCE configure and build started with `( ... ) &` produced no log and no build tree'
status: active
supersedes: []
recurrence_of: L-20261009T120013Z-background-builds-killed-when-shell-call-ended
occurrences: 1
severity: Low
tags: [tech:cmake, tech:juce, kind:environment, phase:planning]
recorded_by: planner
run: gen-20261004T095012Z-singing-voice-vst-pitch-lyrics
recorded_at: 2026-10-10T00:01:04Z
---
## Trigger
A build expected to take longer than one tool call is started in the background.
## What went wrong
The subshell started with `&` died when the tool call ended; the empty log was mistaken for a slow configure.
## Correction
Ran configure and build in the foreground; this session uses `setsid nohup ... < /dev/null &` with a polled log.
## Prevention rule
Start every build that may exceed 250 s with `setsid nohup <cmd> > <log> 2>&1 < /dev/null &` and poll the log; never with a bare `&`.
## Detection check
`ps -eo pid,sid,cmd | grep cmake` shows the build in its own session after the starting call returns.
## Evidence
red-cfg.log was 0 bytes on 2026-10-04.
