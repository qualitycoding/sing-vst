---
id: L-20261015T090100Z-unbounded-parallel-build-flag-from-memory
title: 'The CI workflow used `cmake --build --parallel` without a job count, which is `make -j` with no limit on Linux; the JUCE plugin build was terminated on the runner'
status: active
supersedes: []
recurrence_of: L-20261010T001500Z-ci-tool-flags-and-versions-from-memory
occurrences: 1
severity: High
tags: [tech:github-actions, tech:cmake, kind:tooling, phase:planning]
recorded_by: planner
run: gen-20261004T095012Z-singing-voice-vst-pitch-lyrics
recorded_at: 2026-10-15T09:01:00Z
---
## Trigger
Writing build commands for CI from memory, with a generator (Unix Makefiles) whose tool treats a bare -j as unlimited, for a heavy build (JUCE plugin with LTO).
## What went wrong
cpp (ubuntu-24.04) Build step ended after 3 minutes with exit 143 in run 38699430452; the Python job then had no CLI artifact. The same flag passed on Windows (MSBuild), hiding the problem.
## Correction
Spike research/spikes/cmake-parallel showed `make -j`; every CI build now passes `--parallel 4`.
## Prevention rule
Give every parallel build an explicit job count, and check the build tool's actual command line with a wrapper spike before relying on a flag.
## Detection check
`grep -nE -- '--parallel( |$)' .github/workflows/ci.yml` shows a number after every --parallel.
## Evidence
CI run 38699430452: cpp (ubuntu-24.04) Build failure, exit code 143; research/spikes/cmake-parallel/output.txt.
