---
id: L-20261015T073400Z-main-guard-ran-before-the-test-overlay
title: 'Appending an overlay to a module whose __main__ guard calls main() left `python -m` running the stub'
status: active
supersedes: []
recurrence_of: null
occurrences: 1
severity: Low
tags: [tech:python, kind:tooling, phase:planning]
recorded_by: planner
run: gen-20261004T095012Z-singing-voice-vst-pitch-lyrics
recorded_at: 2026-10-15T07:34:00Z
---
## Trigger
A harness patches a module by appending code, and the module is also run as a script (`python -m`).
## What went wrong
T-P25 failed in the sketch run with NotImplementedError: main, which looked like a test defect.
## Correction
Moved the __main__ guard after the overlay in the harness copy; T-P25 then passed.
## Prevention rule
When overlaying a module by appending code, move its `if __name__ == "__main__"` block to the end first.
## Detection check
research/spikes/sketch-py/output.txt: test_cli.py passes.
## Evidence
Sketch run 2026-10-15, first attempt: 'raise NotImplementedError("main")' from python -m singvst_train.cli --help.
