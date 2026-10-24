---
id: K-20261024T144526Z-juce-linux-build-without-root
statement: "Without root, a JUCE 9.0.3 Linux plugin and its tests can be built and run: 'apt-get download' (works unprivileged once the apt lists exist) each package from 'apt-get -s install <CI package list>', unpack with 'dpkg -x' into a prefix, rewrite prefix=/includedir=/libdir= and -I/-L paths in the .pc files to that prefix, repoint dangling .so symlinks at the host's runtime libraries, then export PKG_CONFIG_PATH, CPATH, LIBRARY_PATH, LD_LIBRARY_PATH and PATH; the unpacked Xvfb then runs the plugin tests and pluginval 1.0.4 strictness 5."
status: current
supersedes: []
tags: [subject:juce-linux-dependencies, subject:sandbox-environment, tech:cpp, phase:implementation]
applies_to_version: "Ubuntu 24.04, JUCE 9.0.3, pluginval 1.0.4"
source: {"url": "", "doi": "", "title": "observed in S-011 of this repository", "locator": "DEVIATIONS.md S-011 row", "accessed": "2026-10-24", "tier": 1}
confidence: verified
derived_from: []
discovered_by: implementer
run: gen-20261004T095012Z-singing-voice-vst-pitch-lyrics
recorded_at: 2026-10-24T14:45:26Z
---
Observed: 38 packages (about 12 MB of .deb files, 32 MB unpacked) were enough; the plugin tests (6 test cases, 98 assertions) and pluginval passed under the unpacked Xvfb. The same commands did not need sudo. S-000's no-root path had assumed these checks were CI-only.
