# EXECUTION_LOG

| UTC time | Step | Attempt | Result (pass/fail/blocked) | Commit before this row | Note |
|---|---|---|---|---|---|
| 2026-10-24T12:39:43Z | S-000 | 1 | pass | 7f05d4e | no-root path (full tree skipped, CI-only plugin tests); host rows changed (see DEVIATIONS); T-060,T-061,T-062,T-P22,T-P27 pass; T-P21 passes after DR-07; core/asan/tsan trees built |
| 2026-10-24T12:54:32Z | S-001 | 1 | pass | 696e76a | run 40094856682 on 696e76a: cpp ubuntu-24.04 + windows-2022 build OK, ctest red (stubs), pluginval T-059 success on both; repo green except README claims (T-P23); sanitizers build, tests red; python-torch red (T-P19); python job still running at read time. Q-E7 re-check: JUCE 9.0.3 builds on both OSes on the impl branch |
| 2026-10-24T12:55:38Z | S-002 | 1 | pass | b319890 | T-001..T-018 pass; 43 other core tests still red (stubs) |
| 2026-10-24T12:56:21Z | S-003 | 1 | pass | a00f149 | T-019..T-027 pass; 34 core tests still red (later steps) |
| 2026-10-24T12:57:20Z | S-004 | 1 | pass | 09a02f6 | T-028..T-031, T-063 pass; 29 core tests still red (later steps) |
| 2026-10-24T12:59:51Z | S-005 | 1 | pass | fb6c152 | T-032..T-038 pass (core); T-034 with LOCPATH de_DE; T-038 TSan clean x3 with setarch -R and ASan clean; 23 core tests still red (later steps) |
| 2026-10-24T13:00:48Z | S-006 | 1 | pass | 06f0f43 | T-064..T-066, T-069 pass; clean under ASan+UBSan (4/4); 19 core tests still red (later steps). Running status persists across meta/sysex per D-031 (the oracle clears it; D-031 text followed, T-065 passes) |
| 2026-10-24T13:28:18Z | S-004 | 2 | pass | d0d6918 | T-031 fixed on windows-2022 by .gitattributes (CI run on d0d6918: T-001..T-041, T-063..T-066, T-069 pass on windows-2022; same on ubuntu) |
| 2026-10-24T13:28:18Z | S-007 | 1 | pass | d0d6918 | T-039..T-041 pass locally and in CI on ubuntu-24.04 and windows-2022 (explicit-path loading of onnxruntime.dll worked; DR-06 not needed) |
| 2026-10-24T13:47:00Z | S-008 | 1 | pass | c1aecb2 | T-042..T-047 pass locally (also under ASan+UBSan) and in CI on ubuntu-24.04 and windows-2022 (run 40098618880); research/spikes/s008-external-data/output.txt: external-data model rejected naming 'external data', original accepted, 3000-frame phrase = 2 guide parts, zeros only at SP >= 22 frames. Mid-step fixes: dangling Ort::TypeInfo view; spike that passed for the wrong reason (lessons recorded) |
