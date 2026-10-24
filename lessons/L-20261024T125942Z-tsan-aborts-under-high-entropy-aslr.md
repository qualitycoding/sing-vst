---
id: L-20261024T125942Z-tsan-aborts-under-high-entropy-aslr
title: "ThreadSanitizer aborted at startup on this kernel until ASLR was disabled for the test process"
status: active
supersedes: []
recurrence_of: null
occurrences: 1
severity: Low
tags: [applies:all, tech:cpp, domain:audio, kind:environment, phase:verification]
recorded_by: implementer
run: gen-20261004T095012Z-singing-voice-vst-pitch-lyrics
recorded_at: 2026-10-24T12:59:42Z
---
## Trigger
A TSan-instrumented test binary is run on a recent Linux kernel (7.0.0-38 here) and ctest reports the test as Failed within milliseconds.
## What went wrong
`ctest -R T-038` in ../build-tsan failed with no test output. Running the binary directly printed `FATAL: ThreadSanitizer: unexpected memory mapping 0x5f...`. That is TSan's address-space check failing under the kernel's high-entropy ASLR; the code under test was not involved. The first reading, a defect in TakeSlot, was wrong.
## Correction
Run the instrumented binary with ASLR disabled: `TSAN_OPTIONS="suppressions=$PWD/tools/tsan.supp halt_on_error=1" setarch "$(uname -m)" -R ctest --test-dir ../build-tsan --output-on-failure -R T-038`. T-038 then passed three times in a row. No source or test changed.
## Prevention rule
When a TSan or ASan binary dies before printing any test output, run it directly and read the first sanitizer line before suspecting the code; for "unexpected memory mapping" re-run under `setarch $(uname -m) -R`.
## Detection check
The EXECUTION_LOG row of every step that runs T-038, T-050, T-051 or T-068 under ../build-tsan records the exact command (with `setarch -R` when the host needs it) and its exit status.
## Evidence
S-005 attempt 1: tsan run failed with the FATAL line above; with setarch -R, three consecutive passes of T-038 (3 assertions each).
