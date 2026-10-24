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
| 2026-10-24T14:03:36Z | S-009 | 1 | pass | c27f619 | CI run 40099771798: T-001..T-052, T-063..T-071 pass on ubuntu-24.04 and windows-2022; sanitizers job green (ASan all core tests, TSan T-038/T-050/T-051/T-068); locally 61/61, ASan 61/61, TSan x3, T-050..T-052 x30 stable. T-053..T-058 (plugin) still red until S-011. core/src/stubs.cpp deleted |
| 2026-10-24T14:21:46Z | S-010 | 1 | pass | f299eb3 | T-P18 passes locally and in CI python job (run 40100954890: T-060 T-061 T-062 T-P18 T-P22 T-P27 pass; other toolkit tests red until S-012+); cpp both OSes 61 core tests green; sanitizers green; commit stamp re-stamps on incremental rebuild (verified); g++-11 build skipped (no-root, DEVIATIONS) |
| 2026-10-24T14:59:18Z | S-011 | 1 | pass | 981cba2 | CI run 40103923321: cpp ubuntu-24.04 and windows-2022 jobs succeeded in full (T-001..T-058 and T-063..T-071 pass, pluginval strictness 5 step green = T-059); sanitizers green; locally 67/67 in build-full under Xvfb, pluginval SUCCESS. docs/UNVERIFIED.md written |
| 2026-10-24T15:02:03Z | S-012 | 1 | pass | d875261 | T-P01..T-P15 (P13b with SINGVST_RENDER_BIN set), T-P25, T-P27 pass locally; prepare --help exits 0; prepare/provenance end-to-end smoke on synthetic audio ok. Still red (later steps): T-P16/P17 (S-016), T-P23 (S-018), T-P24 (S-014), T-P26 (S-015) |
| 2026-10-24T15:27:32Z | S-012 | 2 | pass | 41b2636 | CI run 40105798141 python job: T-P01..T-P15, T-P18, T-P22, T-P25, T-P27 and T-060..T-062 pass; T-P16 T-P17 T-P23 T-P24 T-P26 red (steps S-016, S-018, S-014, S-015) |
| 2026-10-24T15:27:32Z | S-013 | 1 | pass | 41b2636 | T-P19 (both functions) passes locally and in CI python-torch (run 40105798141); parity 3e-7 at 1/7/200/600 frames, 2e-7 vs RVC infer with noise zeroed; hf-revision e6d0c1a17da07c33557852f9dfa2bd44cc75737d recorded in plan/ENVIRONMENT.md. Mid-step correction: trace baked in the example length (lesson recorded) |
| 2026-10-24T15:28:04Z | S-014 | 1 | pass | a03d227 | T-P24 and T-P25 pass locally (27 passed in the lock venv; still red: T-P16/P17 S-016, T-P23 S-018, T-P26 S-015). rvc-files and rvc-train-command run; export --exp-name now delegates to latest_weights |
| 2026-10-24T15:30:59Z | S-015 | 1 | pass | 9911c31 | T-P26 and T-P25 pass locally. Dry run with stand-in resemblyzer/whisper on the fixture voice: 100 renders, report.json (exactly REPORT_KEYS), spread.json (5 values per metric), sidecar (params/seeds per D-035), verdict.json; status 'invalid: f0: only 7 scored F0 frames in phrase p2 (repeat 0)' as accepted for the dry run. GATE-G-005.md written; HALTED at G-005 (S-016 onward wait) |


### S-016 `tools/notebook_dryrun.py` output ($N)

```text
==== train_voice_colab.ipynb
(1) a full session runs every stage [train_voice_colab.ipynb]
  ok   stages run in order: ['split', 'prepare', 'rvc-preprocess', 'rvc-f0', 'rvc-features', 'rvc-files', 'train', 'export', 'render-bin', 'pack', 'evaluate']
  ok   no stop
  ok   commits.json records every stage
(3) editing params.json makes every stage run [train_voice_colab.ipynb]
  ok   second pass reran: ['split', 'prepare', 'rvc-preprocess', 'rvc-f0', 'rvc-features', 'rvc-files', 'train', 'export', 'render-bin', 'pack', 'evaluate']
(4) a train SessionEnd stops the session; the next one resumes at train [train_voice_colab.ipynb]
  ok   STOP set: 'start a new session'
  ok   train left no marker; stages run: ['split', 'prepare', 'rvc-preprocess', 'rvc-f0', 'rvc-features', 'rvc-files']
  ok   resumed at train: ['train', 'export', 'render-bin', 'pack', 'evaluate']
(5) failures and owner stops never escape guarded [train_voice_colab.ipynb]
  ok   RuntimeError -> 'failed: 9 boom'
  ok   Colab: budget.json has the session's end
  ok   OwnerAction -> 'owner: 9 fix the thing'
(7) GPU-hour accounting [train_voice_colab.ipynb]
  ok   gpu_hours 5.0 = sum of stage_hours {'evaluate': 1.0, 'export': 1.0, 'rvc-f0': 1.0, 'rvc-features': 1.0, 'train': 1.0}
  ok   budget-voice.json runs[1] = 5.0
  ok   prior 2.5 killed_hours 0.0
  ok   11 hours lines match and voice = platform + 2.5
  ok   a heartbeat during the train stage records its elapsed time: [1.0]
  ok   unended session still counted: gpu_hours 5.0
(8) budget stop in the train stage [train_voice_colab.ipynb]
  ok   stage completed from the snapshot (STOP_REASON '')
  ok   stopped_by_budget = 10
  ok   <exp>.pth was copied from the snapshot
  ok   no snapshot -> 'budget: no checkpoint'
(10) owner stops in cells (3) and (4e) [train_voice_colab.ipynb]
  ok   PLATFORM_EXPECTED mismatch -> OwnerAction and `owner: 3 `
  ok   changed params -> OwnerAction and `owner: 4e `
==== train_voice_kaggle.ipynb
(1) a full session runs every stage [train_voice_kaggle.ipynb]
  ok   stages run in order: ['split', 'prepare', 'rvc-preprocess', 'rvc-f0', 'rvc-features', 'rvc-files', 'train', 'export', 'render-bin', 'pack', 'evaluate']
  ok   no stop
  ok   commits.json records every stage
(2) end_session, then restore into a fresh root: only render-bin and evaluate run [train_voice_kaggle.ipynb]
  ok   stages run after the restore: ['render-bin', 'evaluate']
  ok   RESTORED_FROM holds the restored tar's hash
(3) editing params.json makes every stage run [train_voice_kaggle.ipynb]
  ok   second pass reran: ['split', 'prepare', 'rvc-preprocess', 'rvc-f0', 'rvc-features', 'rvc-files', 'train', 'export', 'render-bin', 'pack', 'evaluate']
(4) a train SessionEnd stops the session; the next one resumes at train [train_voice_kaggle.ipynb]
  ok   STOP set: 'start a new session'
  ok   train left no marker; stages run: ['split', 'prepare', 'rvc-preprocess', 'rvc-f0', 'rvc-features', 'rvc-files']
  ok   state.tar written by end_session
  ok   first session entry has end and seq: 1
  ok   resumed at train: ['train', 'export', 'render-bin', 'pack', 'evaluate']
(5) failures and owner stops never escape guarded [train_voice_kaggle.ipynb]
  ok   RuntimeError -> 'failed: 9 boom'
  ok   Kaggle: state.tar written after a failure
  ok   state.tar holds the budget files
  ok   OwnerAction -> 'owner: 9 fix the thing'
(6) RESUME rules raise the D-035 messages [train_voice_kaggle.ipynb]
  ok   RESUME with no state.tar: "3 RESUME is True but no previous output is attached: attach the previous version's output (Add Input -> Your Work)"
  ok   RESUME with no state.tar: prints an `owner: 3 ` line
  ok   no RESUME with a state.tar: '3 a previous state.tar is attached (/tmp/nbdry-y311hnds/kaggle/input/prev/state.tar): set RESUME = True'
  ok   no RESUME with a state.tar: prints an `owner: 3 ` line
(7) GPU-hour accounting [train_voice_kaggle.ipynb]
  ok   gpu_hours 5.0 = sum of stage_hours {'evaluate': 1.0, 'export': 1.0, 'rvc-f0': 1.0, 'rvc-features': 1.0, 'train': 1.0}
  ok   budget-voice.json runs[1] = 5.0
  ok   prior 2.5 killed_hours 0.5
  ok   11 hours lines match and voice = platform + 3.0
  ok   a heartbeat during the train stage records its elapsed time: [1.0]
  ok   unended session still counted: gpu_hours 5.0
(8) budget stop in the train stage [train_voice_kaggle.ipynb]
  ok   stage completed from the snapshot (STOP_REASON '')
  ok   stopped_by_budget = 10
  ok   <exp>.pth was copied from the snapshot
  ok   no snapshot -> 'budget: no checkpoint'
(9) prune skips logs/<exp> once and keeps it afterwards [train_voice_kaggle.ipynb]
  ok   logs/<exp> not restored
  ok   pruned-<exp> marker written
  ok   restarted training: ['rvc-preprocess', 'rvc-f0', 'rvc-features', 'rvc-files', 'train']
  ok   second restore keeps logs/<exp>
(10) owner stops in cells (3) and (4e) [train_voice_kaggle.ipynb]
  ok   PLATFORM_EXPECTED mismatch -> OwnerAction and `owner: 3 `
  ok   changed params -> OwnerAction and `owner: 4e `

0 failure(s)
```
| 2026-10-24T18:45:21Z | S-016 | 1 | pass | 1312749 | T-P16, T-P17, T-P22 pass locally and in CI (run 40121078176: python job passes every T-P test except T-P23 = S-018; repo job passes T-060..T-062, T-P21, T-P22, T-P27); tools/notebook_dryrun.py 57/57 ok for both notebooks (output above); real split/prepare/pack stages and helper scripts also run locally; g++-11 build skipped (no root) |
| 2026-10-24T18:46:20Z | S-017 | 1 | blocked-on-gate | 6cffb4c | GATE-G-004.md raised for RUN 1 (Colab, EXPECTED_COMMIT 6cffb4c5c06a1e0fcf362be0186b6c1eb19cccb7, EPOCHS 200, VOICE myvoice, ledger 0.0 h); halted at G-004 |
