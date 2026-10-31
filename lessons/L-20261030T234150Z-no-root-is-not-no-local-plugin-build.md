---
id: L-20261030T234150Z-no-root-is-not-no-local-plugin-build
title: "No root was taken to mean the plugin could only be built and tested in CI"
status: active
supersedes: []
recurrence_of: null
occurrences: 1
severity: Low
tags: [applies:all, tech:cpp, kind:wrong-assumption, kind:environment, phase:planning]
recorded_by: implementer
run: gen-20261004T095012Z-singing-voice-vst-pitch-lyrics
recorded_at: 2026-10-30T23:41:48Z
---
## Trigger
A plan needs system packages (apt -dev libraries, Xvfb) and the implementer has no root.
## What went wrong
S-000 action 3 sent every plugin check (build, plugin tests, pluginval, T-034) to CI on the no-root path. apt-get download plus dpkg -x into a user prefix, with pkg-config paths rewritten, built JUCE and ran Xvfb and pluginval locally, and a localedef into a user directory gave the German locale; CI round trips were not needed.
## Correction
S-011 built ../build-full against ~/sysroot (K-20261024T144526Z-juce-linux-build-without-root) and recorded the deviation; D-043 lists the user-space path as the first fallback.
## Prevention rule
Before declaring a check CI-only for lack of root, try a user-space install (apt-get download + dpkg -x, LOCPATH, setarch) and record the result.
## Detection check
A no-root fallback in a plan names the user-space attempt and its outcome before falling back to CI.
## Evidence
DEVIATIONS.md S-000/S-011 sysroot row; K-20261024T144526Z-juce-linux-build-without-root.
