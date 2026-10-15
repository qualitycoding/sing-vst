<!-- STATUS HEADER (generated at Phase 5 by tools/gen/status.py) -->

# Execution plan — sing-vst

Read `HANDOFF.md` first. Every step uses the template of protocol 3.1. "Full suite" means: `ctest` in the core and full
build trees, plugin tests under `xvfb-run -a`, and `python3.12 -m pytest -q -m "not torch and not voice"` with
`SINGVST_RENDER_BIN` set once S-010 is done — all green except tests whose step has not been reached (listed in
`EXECUTION_LOG.md` per attempt). "Save" means `bash tools/save.sh "<S-### …>" <paths>` (commit + push + state.json, D-029).
Defaults for every step unless the step says otherwise:
- **On failure (default):** fix the implementation, never a frozen test (DR-04); re-run the full suite after any fix to
  shared code (PK-51); after three failed attempts on the same test write `BLOCKED.md` (test, logs, hypotheses) and halt.
- **Checkpoint (default):** `python3 tools/checkpoint.py --phase impl --subphase <S-###> --complete <S-###>`, append one line to
  `EXECUTION_LOG.md` (UTC time, step, attempt, pass|fail|blocked, commit, note), then Save.
- **Exclusive resources (default):** the workspace CPU for builds — one heavy build at a time (PK-43).

### S-000 Environment & access verification
- Tier: Haiku
- Profile: software
- Depends on: none
- Inputs: generation branch `gen-20261004T095012Z-singing-voice-vst-pitch-lyrics`; plan/ENVIRONMENT.md; plan/ASSUMPTIONS.md A-014
- Actions:
  1. Create `impl-gen-20261004T095012Z-singing-voice-vst-pitch-lyrics` from the generation branch and push it.
  2. Clone `qualitycoding/Lessons` and `qualitycoding/knowledge`; record their HEAD commits in `.checkpoints/state.json`
     (`knowledge_store`); list lessons whose tags match plan/ENVIRONMENT.md's task tags that are newer than `ac028c7`
     and add any new prevention rule to `DEVIATIONS.md` (PK-02).
  3. Attach repositories through the session's GitHub connection (never a token on disk); `git config --get-regexp credential`
     shows no token; `bash tools/turn_end_check.sh` passes (PK-12).
  4. Re-probe the hosts table of plan/ENVIRONMENT.md and record results in `EXECUTION_LOG.md` (PK-13).
  5. `bash tools/bootstrap_test_env.sh "$HOME/deps"`; create both build trees and the Python 3.12 venv exactly as in
     plan/ENVIRONMENT.md (PK-20, PK-55).
  6. `sha256sum -c tests/FROZEN_MANIFEST.sha256`; `git check-ignore` behaves as T-062 expects (PK-08).
  7. Start `EXECUTION_LOG.md` and `DEVIATIONS.md` (empty table).
- Outputs: impl branch; EXECUTION_LOG.md; DEVIATIONS.md; state.json knowledge_store
- Evidence produced: none
- Done when: every action succeeded; T-060, T-061, T-062, T-P21, T-P22, T-P27 pass.
- Checkpoint: default
- On failure: halt and write `BLOCKED.md` naming what is missing (credential, host, package) before any delivery work.
- Gate: none
- Relevant decisions/claims: D-018, D-019, D-029, C-044
- Lessons applied: {{L:PK-01,PK-02,PK-08,PK-12,PK-13,PK-20,PK-55}}
- Exclusive resources: none

### S-001 CI baseline on both platforms
- Tier: Haiku
- Profile: software
- Depends on: S-000
- Inputs: `.github/workflows/ci.yml`; the impl branch push from S-000
- Actions:
  1. Read the CI run for the impl branch's HEAD through the REST API:
     `gh api repos/qualitycoding/sing-vst/actions/runs?branch=<impl>&per_page=1`, then `…/runs/<id>/jobs` and
     `…/check-runs/<job id>/annotations` (D-018, PK-14).
  2. Expected on stubs: jobs `repo` green; `cpp` builds on `ubuntu-24.04` **and** `windows-2022`, ctest red, pluginval
     (T-059) green on the silent stub; `sanitizers` builds; `python` red only on stub-caused tests; `python-torch` red on
     T-P19 (stubs).
  3. Record the Windows build result as the answer to Q-E7 in plan/ENVIRONMENT.md via `DEVIATIONS.md` if it differs.
- Outputs: EXECUTION_LOG.md line with run id and per-job conclusions
- Evidence produced: T-059 (stub), Q-E7 answer
- Done when: both `cpp` builds succeed and T-059 passes on both platforms; `repo` is green.
- Checkpoint: default
- On failure: a Windows-only build failure → fix the build files (not tests) and re-run; if the cause is a JUCE 9.0.3 or
  runner defect reproduced with a JUCE example project → `BLOCKED.md` (DR-03). pluginval failure on the stub → DR-05.
- Gate: none
- Relevant decisions/claims: D-001, D-018, D-023, C-015, C-045, C-050, C-051
- Lessons applied: {{L:PK-14,PK-15,PK-16,PK-47}}
- Exclusive resources: none

### S-002 Lyrics, pronunciation and alignment
- Tier: Opus
- Profile: software
- Depends on: S-000
- Inputs: core/include/singvst/{lyrics,g2p,align,errors}.hpp; D-004, D-005, D-006; third_party/cmudict
- Actions: implement `parseLyrics`, `Dictionary`, `isVowel`, `syllabify`, `toMonophonic`, `align` in
  `core/src/lyrics.cpp`, `core/src/g2p.cpp`, `core/src/align.cpp` per D-033; build `build-core`; run the full suite.
- Outputs: core/src/lyrics.cpp, core/src/g2p.cpp, core/src/align.cpp, core/src/stubs.cpp (definitions removed)
- Evidence produced: T-001…T-018
- Done when: T-001…T-018 pass; no previously passing test fails.
- Checkpoint: default
- On failure: default
- Gate: none
- Relevant decisions/claims: D-004, D-005, D-006, C-016
- Lessons applied: {{L:PK-21,PK-42,PK-51}}
- Exclusive resources: default

### S-003 Timing, pitch, gain and noise
- Tier: Opus
- Profile: software, computational
- Depends on: S-002
- Inputs: core/include/singvst/synthesis.hpp; D-007, D-012 (standardNormal), D-021
- Actions: implement every function declared in synthesis.hpp in `core/src/synthesis.cpp` (D-033), including `softClip`
  and `standardNormal` with the golden values of D-012; run the full suite.
- Outputs: core/src/synthesis.cpp, core/src/stubs.cpp
- Evidence produced: T-019…T-027
- Done when: T-019…T-027 pass.
- Checkpoint: default
- On failure: default
- Gate: none
- Relevant decisions/claims: D-007, D-012, D-021, C-009, C-021
- Lessons applied: {{L:PK-27,PK-30,PK-32,PK-34,PK-36}}
- Exclusive resources: default

### S-004 Voice package and SHA-256
- Tier: Sonnet
- Profile: software
- Depends on: S-000
- Inputs: core/include/singvst/voice.hpp; D-008
- Actions: implement `parseManifest`, `validatePackage`, `sha256Hex` in `core/src/voice.cpp` and `core/src/sha256.cpp`
  (FIPS 180-4; no JUCE, D-001); every violation raises `ValidationError` naming the field; run the full suite.
- Outputs: core/src/voice.cpp, core/src/sha256.cpp, core/src/stubs.cpp
- Evidence produced: T-028…T-031, T-063
- Done when: T-028…T-031 and T-063 pass.
- Checkpoint: default
- On failure: default
- Gate: none
- Relevant decisions/claims: D-008, C-049
- Lessons applied: {{L:PK-42}}
- Exclusive resources: default

### S-005 Playback, phrase hash, capture and plugin state
- Tier: Opus
- Profile: software
- Depends on: S-003
- Inputs: core/include/singvst/playback.hpp; D-009, D-010, D-022
- Actions: implement playback.hpp in `core/src/playback.cpp` (lock-free `TakeSlot` hand-off with no allocation on the reader
  side, D-022); run the full suite; run T-038 under TSan locally
  (`-DCMAKE_CXX_FLAGS=-fsanitize=thread`, `TSAN_OPTIONS=suppressions=tools/tsan.supp`).
- Outputs: core/src/playback.cpp, core/src/stubs.cpp
- Evidence produced: T-032…T-038
- Done when: T-032…T-038 pass, and T-038 is clean under TSan.
- Checkpoint: default
- On failure: default
- Gate: none
- Relevant decisions/claims: D-009, D-010, D-022
- Lessons applied: {{L:PK-38}}
- Exclusive resources: default

### S-006 Standard MIDI File import
- Tier: Sonnet
- Profile: software
- Depends on: S-002
- Inputs: core/include/singvst/midifile.hpp; D-031
- Actions: implement `importMidi` in `core/src/midifile.cpp` with bounds-checked reads; run the full suite, then T-066
  under ASan+UBSan locally.
- Outputs: core/src/midifile.cpp, core/src/stubs.cpp
- Evidence produced: T-064…T-066
- Done when: T-064…T-066 pass, clean under ASan+UBSan.
- Checkpoint: default
- On failure: default
- Gate: none
- Relevant decisions/claims: D-031, C-013
- Lessons applied: {{L:PK-42}}
- Exclusive resources: default

### S-007 Resampler and runtime loading
- Tier: Opus
- Profile: software, computational
- Depends on: S-001
- Inputs: core/include/singvst/{ort_runtime,engine}.hpp; D-011, D-024
- Actions: implement `loadOrtRuntime`, `bundledOrtFileName` and `resample` in `core/src/ort_runtime.cpp` and
  `core/src/resample.cpp`; push; read the CI `cpp` job on **both** OSes through the API.
- Outputs: core/src/ort_runtime.cpp, core/src/resample.cpp, core/src/stubs.cpp
- Evidence produced: T-039…T-041
- Done when: T-039…T-041 pass locally and in CI on Linux and Windows.
- Checkpoint: default
- On failure: Windows explicit-path loading fails → DR-06.
- Gate: none
- Relevant decisions/claims: D-011, D-024, C-026, C-042
- Lessons applied: {{L:PK-14,PK-31}}
- Exclusive resources: default

### S-008 Guide and converter engines
- Tier: Opus
- Profile: software, computational
- Depends on: S-003, S-004, S-007
- Inputs: core/include/singvst/engine.hpp; D-012; tests/fixtures/onnx; research/spikes/oracle/engines.py
- Actions: implement `GuideEngine` and `ConverterEngine` in `core/src/guide_engine.cpp` and `core/src/converter_engine.cpp`
  exactly as D-012 (input discovery, phrase splitting at SP ≥ 22 frames with 8-frame padding, chunked conversion with
  100-frame context, `standardNormal` noise); run the full suite; compare a fixture render against
  `research/spikes/oracle/engines.py`.
- Outputs: core/src/guide_engine.cpp, core/src/converter_engine.cpp, core/src/stubs.cpp
- Evidence produced: T-042…T-047
- Done when: T-042…T-047 pass on Linux and in CI on Windows.
- Checkpoint: default
- On failure: an input name/shape mismatch → DR-01.
- Gate: none
- Relevant decisions/claims: D-012, C-003, C-009, C-020, C-034, C-035, C-038, C-041
- Lessons applied: {{L:PK-28,PK-34}}
- Exclusive resources: default

### S-009 Render pipeline and background renderer
- Tier: Opus
- Profile: software
- Depends on: S-005, S-006, S-008
- Inputs: core/include/singvst/render.hpp; D-013
- Actions: implement render.hpp in `core/src/render.cpp`; run the full suite; T-050 and T-051 under TSan locally.
- Outputs: core/src/render.cpp, core/src/stubs.cpp (now empty of definitions; delete it if nothing remains)
- Evidence produced: T-048…T-052
- Done when: all core tests T-001…T-052, T-063…T-066 pass; T-050/T-051 clean under TSan; CI `sanitizers` green.
- Checkpoint: default
- On failure: default
- Gate: none
- Relevant decisions/claims: D-013, D-022
- Lessons applied: {{L:PK-38,PK-51}}
- Exclusive resources: default

### S-010 CLI `singvst-render`
- Tier: Sonnet
- Profile: software, computational
- Depends on: S-009
- Inputs: cli/main.cpp (stub); D-014, D-021
- Actions: implement D-014 in `cli/main.cpp` (options, exit codes, float32 WAV writer, provenance sidecar with
  `seeds = {"converter": <seed>}`); set `SINGVST_RENDER_BIN` to the built binary for every later run of the suite.
- Outputs: cli/main.cpp
- Evidence produced: T-P13b, T-P18
- Done when: T-P13b and T-P18 pass locally and in CI job `python`.
- Checkpoint: default
- On failure: default
- Gate: none
- Relevant decisions/claims: D-014, D-021, D-031
- Lessons applied: {{L:PK-30,PK-04}}
- Exclusive resources: default

### S-011 Plugin processor and editor
- Tier: Opus
- Profile: software
- Depends on: S-009
- Inputs: plugin/PluginProcessor.h; D-010, D-022, D-027; core/include/singvst/params.hpp
- Actions: implement `plugin/PluginProcessor.cpp` and `plugin/PluginEditor.{h,cpp}` (D-033); grep the JUCE 9.0.3 headers for
  every API used before using it (PK-37); build `build-full`; run plugin tests under `xvfb-run -a`; run pluginval 1.0.4
  locally as in the CI step; list editor behaviour that cannot be run headless as "implemented, unverified" in
  `GATE-G-001.md` material (PK-39).
- Outputs: plugin/PluginProcessor.cpp, plugin/PluginEditor.h, plugin/PluginEditor.cpp
- Evidence produced: T-053…T-058, T-059
- Done when: T-053…T-059 pass locally and in CI on both OSes; the full suite is green.
- Checkpoint: default
- On failure: pluginval → DR-05; host load failures reported later → DR-09.
- Gate: none
- Relevant decisions/claims: D-010, D-022, D-027, C-011, C-050, C-051
- Lessons applied: {{L:PK-37,PK-38,PK-39,PK-40,PK-47}}
- Exclusive resources: default

### S-012 Python toolkit core
- Tier: Sonnet
- Profile: software, computational
- Depends on: S-000
- Inputs: python/singvst_train/{prepare,pipeline,provenance,metrics,pack,security,cli}.py; D-015, D-016, D-017, D-019
- Actions: implement the bodies (signatures and docstrings unchanged, T-P27), including the CLI commands `prepare`, `split`,
  `pack`, `provenance`; close every resource with context managers (PK-41).
- Outputs: those modules
- Evidence produced: T-P01…T-P15, T-P25
- Done when: T-P01…T-P15 (T-P13b after S-010), T-P25, T-P27 pass; `python -m singvst_train.cli prepare --help` works.
- Checkpoint: default
- On failure: a pip-audit finding → DR-07.
- Gate: none
- Relevant decisions/claims: D-015, D-016, D-017, D-019, C-027, C-046
- Lessons applied: {{L:PK-31,PK-41,PK-43,PK-54}}
- Exclusive resources: none

### S-013 RVC → ONNX export
- Tier: Opus
- Profile: software, computational
- Depends on: S-012
- Inputs: python/singvst_train/export_rvc.py; RVC 81eed5e; D-012
- Actions: implement `export_synth`, `export_content`, `make_test_weights`, `parity` and the CLI commands `export`,
  `make-test-weights`; push and read the CI `python-torch` job through the API; record the Hugging Face revision that
  `hf download` resolved (job log line printed by `ls -l rvc/assets/hubert_base` and `hf download` output, read via the
  annotations or step summary) in plan/ENVIRONMENT.md pins via `DEVIATIONS.md`.
- Outputs: python/singvst_train/export_rvc.py, python/singvst_train/cli.py
- Evidence produced: T-P19
- Done when: T-P19 (both functions) passes in CI job `python-torch`.
- Checkpoint: default
- On failure: parity > 1e-3 → DR-14.
- Gate: none
- Relevant decisions/claims: D-012, C-003, C-004, C-020, C-032, C-048
- Lessons applied: {{L:PK-34,PK-14}}
- Exclusive resources: none

### S-014 RVC training files
- Tier: Sonnet
- Profile: software
- Depends on: S-012
- Inputs: python/singvst_train/rvc_files.py
- Actions: implement `write_filelist`, `copy_config`, `train_command`, `latest_weights` and the CLI commands `rvc-files`,
  `rvc-train-command`.
- Outputs: python/singvst_train/rvc_files.py, python/singvst_train/cli.py
- Evidence produced: T-P24
- Done when: T-P24 and T-P25 pass.
- Checkpoint: default
- On failure: default
- Gate: none
- Relevant decisions/claims: C-022, C-029, C-030, C-047, C-048
- Lessons applied: {{L:PK-43}}
- Exclusive resources: none

### S-015 Evaluation procedure
- Tier: Opus
- Profile: computational
- Depends on: S-010, S-012
- Inputs: python/singvst_train/evaluate.py; eval/phrases; eval/thresholds.json; D-017
- Actions: implement `transpose_semitones` and `evaluate_voice` and the CLI command `evaluate`; Resemblyzer and Whisper are
  imported inside `evaluate_voice` only (they are not in the toolkit lock; the notebooks install them, D-019). The
  procedure's first full run is the owner's at S-017 (T-P20); no run on fixtures is required here.
- Outputs: python/singvst_train/evaluate.py, python/singvst_train/cli.py
- Evidence produced: T-P26
- Done when: T-P26 and T-P25 pass.
- Checkpoint: default
- On failure: default
- Gate: none
- Relevant decisions/claims: D-017, C-028
- Lessons applied: {{L:PK-29,PK-31,PK-33,PK-35}}
- Exclusive resources: none

### S-016 Training notebooks
- Tier: Sonnet
- Profile: software
- Depends on: S-013, S-014, S-015, G-005 answered
- Inputs: D-016, D-019, D-025; plan/GATES.md G-004; the chosen guide voicebank (G-005)
- Actions: write `notebooks/train_voice_colab.ipynb` and `notebooks/train_voice_kaggle.ipynb` (nbformat 4, no outputs):
  cell 1 `!nvidia-smi`; consent cells (`CONSENT_CONFIRMED = False`, attestation, `assert CONSENT_CONFIRMED and …`); install
  RVC 81eed5e with `requirments_cu128_py312.txt` from the official indexes and the toolkit `--no-deps`; download RVC assets
  with `hf download` (C-032); then cells calling `python -m singvst_train.cli prepare | split | rvc-files |
  rvc-train-command | export | pack | evaluate`, each wrapped by `pipeline.run_stages` markers on Drive / the Kaggle output;
  build `singvst-render` (core only) in the notebook; `tar` archives in and out; the guide voicebank is downloaded by the
  owner inside the notebook from its release URL and never stored in the repository.
- Outputs: notebooks/train_voice_colab.ipynb, notebooks/train_voice_kaggle.ipynb
- Evidence produced: T-P16, T-P17
- Done when: T-P16, T-P17, T-P22 pass.
- Checkpoint: default
- On failure: default
- Gate: G-005 must be answered before this step starts.
- Relevant decisions/claims: D-016, D-019, D-025, D-026, C-017, C-018, C-019, C-023, C-032, C-036, C-037, C-047
- Lessons applied: {{L:PK-43,PK-44}}
- Exclusive resources: none

### S-017 Owner's training run and evaluation
- Tier: Sonnet
- Profile: computational
- Depends on: S-016, S-011
- Inputs: G-004 response; notebooks
- Actions:
  1. Halt at G-004 and write `GATE-G-004.md` (plan/GATES.md).
  2. After the owner's response, wait for `report.json`, its provenance sidecar and the renders archive (the owner runs the
     notebook, which runs `pytest -m voice` (T-P20) as its last cell).
  3. Commit `results/<voice name>/report.json`, `report.json.provenance.json`, `verdict.json` (never audio of the owner's
     voice unless the owner says so in the G-004 response).
  4. Halt at G-001 with `GATE-G-001.md`.
- Outputs: results/<voice>/report.json, report.json.provenance.json, verdict.json, GATE-G-004.md, GATE-G-001.md
- Evidence produced: T-P20 (run by the owner); G-001 record
- Done when: the G-001 response is recorded in `GATE-G-001.md`.
- Checkpoint: default
- On failure: result-pivot rules DR-10…DR-13 (record values, never tune the evaluation, halt at G-001).
- Gate: G-004, then G-001
- Relevant decisions/claims: D-016, D-017, A-009, A-011, A-012, A-016
- Lessons applied: {{L:PK-29,PK-35,PK-45,PK-46}}
- Exclusive resources: none

### S-018 Documentation and notices
- Tier: Sonnet
- Profile: software
- Depends on: S-017
- Inputs: G-001 record; D-026, D-030
- Actions: write `README.md` with a `## What it does` section whose every bullet cites a test ID; install instructions
  (copy the VST3 bundle to the user VST3 folder; COPY_PLUGIN_AFTER_BUILD is FALSE); training instructions pointing to the
  notebooks; `docs/PARAMETERS.md` generated from `kParams` by a script; `THIRD_PARTY_NOTICES.md` (JUCE, ONNX Runtime,
  nlohmann/json, CMUdict, RVC, TIGER/other voicebank terms, openvpi vocoder if used); sound descriptions only with the G-001
  record (PK-46).
- Outputs: README.md, docs/PARAMETERS.md, THIRD_PARTY_NOTICES.md, tools/gen/parameters.py
- Evidence produced: T-P23
- Done when: T-P22, T-P23 pass; the full suite is green.
- Checkpoint: default
- On failure: default
- Gate: none
- Relevant decisions/claims: D-010, D-026, D-030, C-012, C-037
- Lessons applied: {{L:PK-04,PK-40,PK-46,PK-50}}
- Exclusive resources: none

### S-019 Final verification and pull request
- Tier: Opus
- Profile: software, computational
- Depends on: S-018
- Inputs: everything above
- Actions: run the full suite locally; read the final CI run of all jobs through the API; map every plan step and
  pre-mortem control to a delivering file or test in `plan/TRACEABILITY.md` (PK-07); open a pull request impl → `main`
  (`gh pr create --base main --head <impl>`), body ending with the attribution lines; do **not** merge (G-002).
- Outputs: pull request URL in EXECUTION_LOG.md
- Evidence produced: all tests
- Done when: every frozen test passes (T-P20 from S-017's record), CI green on both OSes, the pull request exists.
- Checkpoint: default
- On failure: default
- Gate: none (merging is the owner's action, G-002)
- Relevant decisions/claims: D-018, D-029
- Lessons applied: {{L:PK-07,PK-05}}
- Exclusive resources: none

### S-RETRO Retrospective
- Tier: Opus
- Profile: software, computational
- Depends on: S-000…S-019
- Inputs: EXECUTION_LOG.md, commits, DEVIATIONS.md, BLOCKED.md, TEST_CHALLENGE.md, GATE-*.md, CI history,
  research/PRIOR_KNOWLEDGE.md, lessons/, knowledge/
- Actions: a Haiku agent collects the inputs into one digest; a fresh Opus agent answers the four questions of protocol
  3.7.1 and writes `RETROSPECTIVE.md`, a lesson for each unrecorded correction or overlooked step, and a knowledge item for
  each missing fact; run `python3 tools/check_schema.py`.
- Outputs: RETROSPECTIVE.md, lessons/L-*.md, knowledge/K-*.md
- Evidence produced: none
- Done when: every finding links to an L- or K- file; `tools/check_schema.py` prints "all entries valid".
- Checkpoint: default
- On failure: default
- Gate: none
- Relevant decisions/claims: Rule 11, Rule 12
- Lessons applied: {{L:PK-05,PK-07}}
- Exclusive resources: none

### S-KNOW Lessons and knowledge push
- Tier: Haiku
- Profile: software
- Depends on: S-RETRO
- Inputs: lessons/, knowledge/, TAXONOMY.md, plan/ASSUMPTIONS.md A-014
- Actions: protocol 3.7.2 — halt at G-003; on `push-to-proposed` copy lessons into `qualitycoding/Lessons` and knowledge
  items into `qualitycoding/knowledge` in the Appendix C layout, regenerate both indexes, merge the run's tags into
  `TAXONOMY.md`, push (3 retries with pull-and-regenerate; else `git bundle create knowledge-<run_id>.bundle`).
- Outputs: pushes to the stores, or the bundle path
- Evidence produced: none
- Done when: protocol 3.7.2 item 4.
- Checkpoint: default
- On failure: bundle fallback (3.7.2 item 3).
- Gate: G-003
- Relevant decisions/claims: Rule 13, A-014
- Lessons applied: {{L:PK-02,PK-12}}
- Exclusive resources: none
