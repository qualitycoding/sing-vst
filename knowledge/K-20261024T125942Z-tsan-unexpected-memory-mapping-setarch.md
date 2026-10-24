---
id: K-20261024T125942Z-tsan-unexpected-memory-mapping-setarch
statement: "On Linux kernel 7.0.0-38 with GCC 13.3, a -fsanitize=thread binary exits at startup with 'FATAL: ThreadSanitizer: unexpected memory mapping' under the default ASLR; running it through 'setarch $(uname -m) -R' lets it run normally."
status: current
supersedes: []
tags: [subject:sandbox-environment, tech:cpp, phase:verification]
applies_to_version: "Linux 7.0.0-38, GCC 13.3.0 (ubuntu 24.04)"
source: {"url": "", "doi": "", "title": "observed in the S-005 TSan run of this repository", "locator": "EXECUTION_LOG.md S-005", "accessed": "2026-10-24", "tier": 1}
confidence: verified
derived_from: []
discovered_by: implementer
run: gen-20261004T095012Z-singing-voice-vst-pitch-lyrics
recorded_at: 2026-10-24T12:59:42Z
---
Observed directly: the same binary failed without setarch and passed T-038 three times with it. Cause (kernel mmap entropy versus TSan's shadow-memory layout) is the commonly reported one but was not separately verified here.
