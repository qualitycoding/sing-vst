---
id: L-20261015T200100Z-frozen-test-needed-a-locale-nobody-installed
title: "A frozen test required a German locale that neither the sandbox setup nor any CI job installed"
status: active
supersedes: []
recurrence_of: null
occurrences: 1
severity: High
tags: [applies:all, tech:ci, kind:environment, phase:planning]
recorded_by: planner
run: gen-20261004T095012Z-singing-voice-vst-pitch-lyrics
recorded_at: 2026-10-15T20:01:00Z
---
## Trigger
A frozen test depends on an environmental precondition (locale, display, font, device) rather than on code.
## What went wrong
Cold read pass 3 Sonnet item 1: T-034 REQUIREs a German locale; its comment claimed CI installs it (D-018) but no step did, and the sandbox has only C/POSIX, so S-005 and S-009 could never pass.
## Correction
D-018 corrected; S-000 action 3 generates de_DE.UTF-8 (localedef or locale-gen) with a CI-only fallback; the cpp and sanitizers jobs run locale-gen (C-056, spike locale-de).
## Prevention rule
For each frozen test, list every environmental precondition it needs and name the S-000 action and the CI step that provides it, verified by a spike.
## Detection check
grep the frozen tests for setlocale, display, font and device use; each has a provisioning line in S-000 and ci.yml.
## Evidence
premortem/coldread-pass-3.md S1; research/spikes/locale-de.
