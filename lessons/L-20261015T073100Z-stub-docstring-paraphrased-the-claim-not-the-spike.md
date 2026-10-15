---
id: L-20261015T073100Z-stub-docstring-paraphrased-the-claim-not-the-spike
title: "load_pyworld's frozen docstring said importlib.import_module('pyworld.pyworld'), which still runs the package __init__ that C-046 says fails"
status: active
supersedes: []
recurrence_of: null
occurrences: 1
severity: Medium
tags: [tech:python, domain:audio, kind:wrong-assumption, phase:planning]
recorded_by: planner
run: gen-20261004T095012Z-singing-voice-vst-pitch-lyrics
recorded_at: 2026-10-15T07:31:00Z
---
## Trigger
An interface docstring is written from a claim's one-line summary while the spike that verified the claim contains the exact working code.
## What went wrong
The stub promised a loading method the spike had not used; the clean-room venv showed it raising ModuleNotFoundError: pkg_resources.
## Correction
Rewrote the docstring from research/spikes/pyworld-direct/run.sh (ExtensionFileLoader on the file listed in the distribution metadata) and ran the sketch implementation of it (T-P10 passes).
## Prevention rule
When a frozen docstring describes a mechanism a spike verified, copy the mechanism from the spike's code, then run it once in the pinned environment before committing.
## Detection check
research/spikes/sketch-py/output.txt shows T-P10 passing with the documented loader.
## Evidence
venv-lock.log 2026-10-15: importlib.import_module('pyworld.pyworld') -> ModuleNotFoundError: No module named 'pkg_resources'.
