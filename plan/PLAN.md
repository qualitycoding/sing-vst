<!-- STATUS HEADER: written by the planning agent's final consistency check (protocol Phase 5) with tools/gen/status.py -->

# Execution plan — sing-vst

Read `HANDOFF.md` first. Every step uses the template of protocol 3.1. Steps run **one at a time, in ID order** (they share
one branch, `.checkpoints/state.json`, `core/src/stubs.cpp` and `python/singvst_train/cli.py`); a later step may start only
when every step in its `Depends on` has passed. "Full suite" means: `ctest` in the core and full build trees, plugin tests
under `xvfb-run -a`, and `../venv-lock/bin/python -I -m pytest -q -m "not torch and not voice and not network"` with
`SINGVST_RENDER_BIN` set once S-010 is done — all green except tests whose step has not been reached (listed in
`EXECUTION_LOG.md` per attempt). "Save" means `bash tools/save.sh "<S-### …>" <paths>` (commit + push + state.json, D-029).
Defaults for every step unless the step says otherwise:
- **On failure (default):** fix the implementation, never a frozen test (DR-04); re-run the full suite after any fix to
  shared code (PK-51); after three failed attempts on the same test write `BLOCKED.md` (test, logs, hypotheses) and halt.
- **Checkpoint (default):** `python3.12 tools/checkpoint.py --phase impl --subphase <S-###> --active-step <next step> --complete <S-###>
  --done-pending <S-###>`, append one row to `EXECUTION_LOG.md` (HANDOFF §Logs), then Save. Before any high-latency action
  (long build, CI wait, gate) write `--in-flight '{"op": "…"}'` first and `--in-flight null` after (D-034).
- **Exclusive resources (default):** the workspace CPU for builds — one heavy build at a time (PK-43).

### S-000 Environment & access verification
- Tier: Haiku
- Profile: software
- Depends on: none
- Inputs: generation branch `gen-20261004T095012Z-singing-voice-vst-pitch-lyrics`; plan/ENVIRONMENT.md; plan/ASSUMPTIONS.md A-014; research/PRIOR_KNOWLEDGE.md (task tags, line 3)
- Actions: 
  1. Create `impl-gen-20261004T095012Z-singing-voice-vst-pitch-lyrics` from the generation branch and push it. Set
     `SINGVST_COMMIT_TRAILERS` to your own session's commit trailers for every later save (tools/save.sh).
  2. Preflight (stop at the first failure with `BLOCKED.md`): `gh api user` succeeds (the session's GitHub connection;
     attach repositories with the session's repository tool, never a pasted token — PK-12); `gh api repos/qualitycoding/sing-vst
     --jq .default_branch` prints `main`; `git push --dry-run` succeeds; `cmake --version` ≥ 3.22, `ninja`, `g++` 13,
     `python3.12`, `curl`, `unzip`, `xvfb-run` exist; the JUCE Linux packages of the `cpp` job in `.github/workflows/ci.yml`
     are installed or installable with `sudo apt-get install -y …`.
  3. Clone `qualitycoding/Lessons` to `../store-lessons` and `qualitycoding/knowledge` to `../store-knowledge`; record their
     HEADs with `python3.12 tools/checkpoint.py --merge 'knowledge_store={"commit_at_impl": {"lessons": "<sha>", "knowledge":
     "<sha>"}}'`; list lesson files added after `ac028c7` (`git -C ../store-lessons log --name-only --format= ac028c7..HEAD`)
     whose tags include any task tag of research/PRIOR_KNOWLEDGE.md line 3, and add each one's prevention rule to
     `DEVIATIONS.md` as a rule to follow (PK-02).
  4. Re-probe the hosts table of plan/ENVIRONMENT.md and record the results in `EXECUTION_LOG.md` (PK-13).
  5. `bash tools/bootstrap_test_env.sh "$HOME/deps"`; create the build trees and the Python 3.12 venv exactly as in
     plan/ENVIRONMENT.md; clone RVC to `../rvc` at 81eed5e for reading (D-036) (PK-20, PK-55).
  6. `sha256sum -c tests/FROZEN_MANIFEST.sha256`; `git check-ignore` behaves as T-062 expects (PK-08).
  7. Start `EXECUTION_LOG.md` and `DEVIATIONS.md` with the HANDOFF §Logs templates.
- Outputs: impl branch; EXECUTION_LOG.md; DEVIATIONS.md; state.json knowledge_store.commit_at_impl; ../store-lessons, ../store-knowledge, ../rvc, ../deps, build trees, ../venv-lock
- Evidence produced: none
- Done when: every action succeeded; T-060, T-061, T-062, T-P21, T-P22, T-P27 pass.
- Checkpoint: default
- On failure: halt and write `BLOCKED.md` naming what is missing (credential, host, package) before any delivery work.
- Gate: none
- Relevant decisions/claims: D-018, D-019, D-029, C-044
- Lessons applied: PK-01 (L-20261010T094000, L-20261010T000100, L-20261009T191800); PK-02 (L-20261010T000102, L-20261009T234124, L-20261009T232008); PK-08 (L-20261009T232010, L-20261009T192610, L-20261009T191500); PK-12 (L-20261009T193602, L-20261010T000101, L-20261009T234112); PK-13 (L-20261009T193601, L-20261009T192613, L-20261004T161505); PK-20 (L-20261010T000100, L-20261009T234108, L-20261009T191800); PK-55 (L-20261015T073000)
- Exclusive resources: none

### S-001 CI baseline on both platforms
- Tier: Haiku
- Profile: software
- Depends on: S-000
- Inputs: `.github/workflows/ci.yml`; the impl branch push from S-000
- Actions: 
  1. Read the CI run of the impl branch's HEAD as D-036 says:
     `gh api "repos/qualitycoding/sing-vst/actions/runs?branch=<impl>&head_sha=$(git rev-parse HEAD)&per_page=5"`, then
     `gh api "repos/qualitycoding/sing-vst/actions/runs/<id>/jobs"` and `gh api "repos/qualitycoding/sing-vst/check-runs/<job id>/annotations"`
     (D-018, PK-14).
  2. Expected on stubs: job `repo` green except its step "README claims (T-P23)" (red until S-018); `cpp` **builds** on
     `ubuntu-24.04` and `windows-2022`, its ctest step red, pluginval (T-059) green on the silent stub; `sanitizers` builds,
     tests red; `python` red only on stub-caused tests; `python-torch` red on T-P19, with an `hf-revision` notice annotation.
  3. If the Linux build fails, compare with C-055 (bounded `--parallel`) before anything else.
- Outputs: EXECUTION_LOG.md line with run id and per-job conclusions
- Evidence produced: T-059 (stub), Q-E7 answer
- Done when: both `cpp` builds succeed and T-059 passes on both OSes; every `repo` step except "README claims (T-P23)" is green.
- Checkpoint: default
- On failure: a Windows-only build failure → fix the build files (not tests) and re-run; if the cause is a JUCE 9.0.3 or
  runner defect reproduced with a JUCE example project → `BLOCKED.md` (DR-03). pluginval failure on the stub → DR-05.
- Gate: none
- Relevant decisions/claims: D-001, D-018, D-023, C-015, C-045, C-050, C-051
- Lessons applied: PK-14 (L-20261009T191300, L-20261009T150601, L-20261009T150701); PK-15 (L-20261009T151301, L-20261009T151001, L-20261009T150901); PK-16 (L-20261015T090100, L-20261010T001500, L-20261004T161503); PK-47 (L-20261009T092005)
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
- Lessons applied: PK-21 (L-20261014T220000, L-20261009T234102, L-20261004T162212); PK-42 (L-20261009T123002, L-20261009T123001); PK-51 (L-20261004T150500, L-20261004T153000)
- Exclusive resources: default

### S-003 Timing, pitch, gain and noise
- Tier: Opus
- Profile: software, computational
- Depends on: S-002
- Inputs: core/include/singvst/synthesis.hpp; D-007, D-012 (standardNormal), D-021
- Actions: implement every function declared in synthesis.hpp (including `softClip` and `peakAbs`) in `core/src/synthesis.cpp`
  (D-033); run the full suite. (`standardNormal` is declared in engine.hpp and belongs to S-007.)
- Outputs: core/src/synthesis.cpp, core/src/stubs.cpp
- Evidence produced: T-019…T-027
- Done when: T-019…T-027 pass.
- Checkpoint: default
- On failure: default
- Gate: none
- Relevant decisions/claims: D-007, D-012, D-021, C-009, C-021
- Lessons applied: PK-27 (L-20261004T102003, L-20261009T193612, L-20261009T140010); PK-30 (L-20261009T120001, L-20261008T173530, L-20261009T090804); PK-32 (L-20261004T150300); PK-34 (L-20261009T120012); PK-36 (L-20261009T092002, L-20261009T161000)
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
- Lessons applied: PK-42 (L-20261009T123002, L-20261009T123001)
- Exclusive resources: default

### S-005 Playback, phrase hash, capture and plugin state
- Tier: Opus
- Profile: software
- Depends on: S-003
- Inputs: core/include/singvst/playback.hpp; D-009, D-010, D-022
- Actions: implement playback.hpp in `core/src/playback.cpp` (lock-free `TakeSlot` hand-off with no allocation on the reader
  side, D-022); run the full suite; run T-038 in `../build-tsan` with the plan/ENVIRONMENT.md sanitizer lines.
- Outputs: core/src/playback.cpp, core/src/stubs.cpp
- Evidence produced: T-032…T-038
- Done when: T-032…T-038 pass, and T-038 is clean under TSan.
- Checkpoint: default
- On failure: default
- Gate: none
- Relevant decisions/claims: D-009, D-010, D-022
- Lessons applied: PK-38 (L-20261009T161100)
- Exclusive resources: default

### S-006 Standard MIDI File import
- Tier: Sonnet
- Profile: software
- Depends on: S-002
- Inputs: core/include/singvst/midifile.hpp; D-031
- Actions: implement `importMidi` in `core/src/midifile.cpp` with bounds-checked reads; run the full suite, then
  T-064…T-066 in `../build-asan` with the plan/ENVIRONMENT.md sanitizer lines.
- Outputs: core/src/midifile.cpp, core/src/stubs.cpp
- Evidence produced: T-064…T-066
- Done when: T-064…T-066 pass, clean under ASan+UBSan.
- Checkpoint: default
- On failure: default
- Gate: none
- Relevant decisions/claims: D-031, C-013
- Lessons applied: PK-42 (L-20261009T123002, L-20261009T123001)
- Exclusive resources: default

### S-007 Resampler and runtime loading
- Tier: Opus
- Profile: software, computational
- Depends on: S-001
- Inputs: core/include/singvst/{ort_runtime,engine}.hpp; D-011, D-024
- Actions: implement `standardNormal` (golden values of D-012) in `core/src/random.cpp`, `loadOrtRuntime` and
  `bundledOrtFileName` in `core/src/ort_runtime.cpp`, and `resample` in `core/src/resample.cpp`; push; read the CI `cpp` job
  on **both** OSes through the API (D-036).
- Outputs: core/src/random.cpp, core/src/ort_runtime.cpp, core/src/resample.cpp, core/src/stubs.cpp
- Evidence produced: T-039…T-041
- Done when: T-039…T-041 pass locally and in CI on Linux and Windows.
- Checkpoint: default
- On failure: Windows explicit-path loading fails → DR-06.
- Gate: none
- Relevant decisions/claims: D-011, D-024, C-026, C-042
- Lessons applied: PK-14 (L-20261009T191300, L-20261009T150601, L-20261009T150701); PK-31 (L-20261009T120008, L-20261009T120002, L-20261004T162219)
- Exclusive resources: default

### S-008 Guide and converter engines
- Tier: Opus
- Profile: software, computational
- Depends on: S-003, S-004, S-007
- Inputs: core/include/singvst/engine.hpp; D-012; tests/fixtures/onnx; research/spikes/oracle/engines.py
- Actions: implement `GuideEngine` and `ConverterEngine` in `core/src/guide_engine.cpp` and `core/src/converter_engine.cpp`
  exactly as D-012 (input discovery, phrase splitting at SP ≥ 22 frames with 8-frame padding, chunked conversion with
  100-frame context, `standardNormal` noise); run the full suite. `research/spikes/oracle/engines.py` (an independent
  Python implementation that derived the frozen expected values) is a debugging reference only; the pass criterion is the
  frozen tests.
- Outputs: core/src/guide_engine.cpp, core/src/converter_engine.cpp, core/src/stubs.cpp
- Evidence produced: T-042…T-047
- Done when: T-042…T-047 pass on Linux and in CI on Windows.
- Checkpoint: default
- On failure: an input name/shape mismatch → DR-01.
- Gate: none
- Relevant decisions/claims: D-012, C-003, C-009, C-020, C-034, C-035, C-038, C-041
- Lessons applied: PK-28 (L-20261010T000106); PK-34 (L-20261009T120012)
- Exclusive resources: default

### S-009 Render pipeline and background renderer
- Tier: Opus
- Profile: software
- Depends on: S-005, S-006, S-008
- Inputs: core/include/singvst/render.hpp; D-013
- Actions: implement render.hpp in `core/src/render.cpp`; run the full suite; T-050 and T-051 in `../build-tsan` (plan/ENVIRONMENT.md).
- Outputs: core/src/render.cpp, core/src/stubs.cpp (now empty of definitions; delete it if nothing remains)
- Evidence produced: T-048…T-052
- Done when: all core tests T-001…T-052, T-063…T-066 pass; T-050/T-051 clean under TSan; CI `sanitizers` green.
- Checkpoint: default
- On failure: default
- Gate: none
- Relevant decisions/claims: D-013, D-022
- Lessons applied: PK-38 (L-20261009T161100); PK-51 (L-20261004T150500, L-20261004T153000)
- Exclusive resources: default

### S-010 CLI `singvst-render`
- Tier: Sonnet
- Profile: software, computational
- Depends on: S-009
- Inputs: cli/main.cpp (stub); D-014, D-021
- Actions: implement D-014 in `cli/main.cpp` (options, exit codes, float32 WAV writer, provenance sidecar with
  `seeds = {"converter": <seed>}`); set `SINGVST_RENDER_BIN` to the built binary for every later run of the suite.
- Outputs: cli/main.cpp
- Evidence produced: T-P13 (binary part, `test_P13b_…`), T-P18
- Done when: T-P13 (binary part) and T-P18 pass locally and in CI job `python`.
- Checkpoint: default
- On failure: default
- Gate: none
- Relevant decisions/claims: D-014, D-021, D-031
- Lessons applied: PK-30 (L-20261009T120001, L-20261008T173530, L-20261009T090804); PK-04 (L-20261009T120015, L-20261008T173532, L-20261009T234120)
- Exclusive resources: default

### S-011 Plugin processor and editor
- Tier: Opus
- Profile: software
- Depends on: S-009
- Inputs: plugin/PluginProcessor.h; D-010, D-022, D-027; core/include/singvst/params.hpp
- Actions: implement `plugin/PluginProcessor.cpp` and `plugin/PluginEditor.{h,cpp}` (D-033); grep the JUCE 9.0.3 headers for
  every API used before using it (PK-37); build `build-full`; run plugin tests under `xvfb-run -a`; run pluginval 1.0.4
  locally as in the CI step; list editor behaviour that cannot be run headless as "implemented, unverified" in
  `docs/UNVERIFIED.md` (one bullet per behaviour, with the D-027 item it belongs to); S-017 copies it into GATE-G-001.md (PK-39).
- Outputs: plugin/PluginProcessor.cpp, plugin/PluginEditor.h, plugin/PluginEditor.cpp, docs/UNVERIFIED.md
- Evidence produced: T-053…T-058, T-059
- Done when: T-053…T-059 pass locally and in CI on both OSes; the full suite is green.
- Checkpoint: default
- On failure: pluginval → DR-05; host load failures reported later → DR-09.
- Gate: none
- Relevant decisions/claims: D-010, D-022, D-027, C-011, C-050, C-051
- Lessons applied: PK-37 (L-20261008T173536, L-20261009T160900, L-20261009T092006); PK-38 (L-20261009T161100); PK-39 (L-20261009T160200); PK-40 (L-20261008T173531); PK-47 (L-20261009T092005)
- Exclusive resources: default

### S-012 Python toolkit core
- Tier: Sonnet
- Profile: software, computational
- Depends on: S-000
- Inputs: python/singvst_train/{prepare,pipeline,provenance,metrics,pack,security,cli}.py; D-015, D-016, D-017, D-019
- Actions: implement the bodies (signatures and docstrings unchanged, T-P27; conventions of D-033), register **all nine**
  sub-commands of `cli.COMMANDS` (T-P25 needs every `--help`; later steps add the options and bodies of theirs), and implement
  `split`, `prepare`, `pack`, `provenance` exactly as D-035; close every resource with context managers (PK-41).
- Outputs: those modules
- Evidence produced: T-P01…T-P15 (T-P13 without its binary part), T-P25
- Done when: T-P01…T-P15 (except the binary part of T-P13, which belongs to S-010), T-P25 and T-P27 pass; `../venv-lock/bin/python -m singvst_train.cli prepare --help` works.
- Checkpoint: default
- On failure: a pip-audit finding → DR-07.
- Gate: none
- Relevant decisions/claims: D-015, D-016, D-017, D-019, C-027, C-046
- Lessons applied: PK-31 (L-20261009T120008, L-20261009T120002, L-20261004T162219); PK-41 (L-20261009T140003, L-20261009T123010, L-20261009T123000); PK-43 (L-20261009T193613, L-20261004T102004); PK-54 (L-20261015T073100)
- Exclusive resources: none

### S-013 RVC → ONNX export
- Tier: Opus
- Profile: software, computational
- Depends on: S-012
- Inputs: python/singvst_train/export_rvc.py; RVC 81eed5e; D-012
- Actions: implement `export_synth`, `export_content`, `make_test_weights`, `parity` and the CLI commands `export`,
  `make-test-weights` (D-035); push and read the CI `python-torch` job (D-036: one attempt = one CI run of a new commit; no
  local torch); read the `hf-revision` notice annotation of that job and replace "`--revision main` (S-013 records the
  resolved revision here)" in the plan/ENVIRONMENT.md pins table with the printed SHA (the job's RVC checkout and its
  `rvc/assets/hubert_base` exist only on the CI runner).
- Outputs: python/singvst_train/export_rvc.py, python/singvst_train/cli.py
- Evidence produced: T-P19 (both functions, incl. the content-encoder part `test_P19b_…`)
- Done when: T-P19 passes in CI job `python-torch`; plan/ENVIRONMENT.md names the Hugging Face revision.
- Checkpoint: default
- On failure: parity > 1e-3 → DR-14.
- Gate: none
- Relevant decisions/claims: D-012, C-003, C-004, C-020, C-032, C-048
- Lessons applied: PK-34 (L-20261009T120012); PK-14 (L-20261009T191300, L-20261009T150601, L-20261009T150701)
- Exclusive resources: none

### S-014 RVC training files
- Tier: Sonnet
- Profile: software
- Depends on: S-012
- Inputs: python/singvst_train/rvc_files.py
- Actions: implement `write_filelist`, `copy_config`, `train_command`, `latest_weights` and the CLI commands `rvc-files`,
  `rvc-train-command` exactly as D-035.
- Outputs: python/singvst_train/rvc_files.py, python/singvst_train/cli.py
- Evidence produced: T-P24
- Done when: T-P24 and T-P25 pass.
- Checkpoint: default
- On failure: default
- Gate: none
- Relevant decisions/claims: C-022, C-029, C-030, C-047, C-048
- Lessons applied: PK-43 (L-20261009T193613, L-20261004T102004)
- Exclusive resources: none

### S-015 Evaluation procedure
- Tier: Opus
- Profile: computational
- Depends on: S-010, S-012
- Inputs: python/singvst_train/evaluate.py; eval/PROCEDURE.md; eval/phrases; eval/thresholds.json; D-017, D-035
- Actions: implement `transpose_semitones`, `evaluate_voice` and the CLI command `evaluate` exactly as
  `eval/PROCEDURE.md` (frozen) and D-035 (`verdict.json`); Resemblyzer and Whisper are imported inside `evaluate_voice` only
  (D-033). The procedure's first full run is the owner's at S-017 (T-P20); no run on fixtures is required here.
- Outputs: python/singvst_train/evaluate.py, python/singvst_train/cli.py
- Evidence produced: T-P26
- Done when: T-P26 and T-P25 pass.
- Checkpoint: default
- On failure: default
- Gate: none
- Relevant decisions/claims: D-017, C-028
- Lessons applied: PK-29 (L-20261009T234100, L-20261009T120011, L-20261010T000114); PK-31 (L-20261009T120008, L-20261009T120002, L-20261004T162219); PK-33 (L-20261004T162217, L-20261007T150832); PK-35 (L-20261009T120003)
- Exclusive resources: none

### S-016 Training notebooks
- Tier: Sonnet
- Profile: software
- Depends on: S-013, S-014, S-015, G-005 answered
- Inputs: D-016, D-019, D-025; plan/GATES.md G-004; the chosen guide voicebank (G-005)
- Actions: write `notebooks/train_voice_colab.ipynb` and `notebooks/train_voice_kaggle.ipynb` (nbformat 4, no outputs)
  with exactly the cells of D-035 §Notebook layout (RVC's own `requirments_cu128_py312.txt` from the RVC checkout at 81eed5e,
  official indexes, C-023), and the guide voicebank cells of D-035 §Guide voicebank for the G-005 answer; the voicebank is
  downloaded by the owner inside the notebook and never stored in the repository.
- Outputs: notebooks/train_voice_colab.ipynb, notebooks/train_voice_kaggle.ipynb
- Evidence produced: T-P16, T-P17
- Done when: T-P16, T-P17, T-P22 pass.
- Checkpoint: default
- On failure: default
- Gate: G-005 must be answered before this step starts.
- Relevant decisions/claims: D-016, D-019, D-025, D-026, C-017, C-018, C-019, C-023, C-032, C-036, C-037, C-047
- Lessons applied: PK-43 (L-20261009T193613, L-20261004T102004); PK-44 (L-20261010T000113)
- Exclusive resources: none

### S-017 Owner's training run and evaluation
- Tier: Sonnet
- Profile: computational
- Depends on: S-016, S-011
- Inputs: G-004 response; notebooks
- Actions: 
  1. Halt at G-004: write `GATE-G-004.md` (plan/GATES.md) and end the turn with the gate message.
  2. After the owner runs the notebook, they attach `report.json`, `report.json.provenance.json` and `verdict.json` (D-035);
     the notebook's last test cell is T-P20.
  3. Commit those three files to `results/<voice>/` (`<voice>` = the `--name` given to `pack`; check it in `report.json`'s
     provenance `params`); never commit audio, recordings or voice packages (T-062).
  4. Write `GATE-G-001.md` with the G-001 evidence (including `docs/UNVERIFIED.md`) and halt.
- Outputs: results/<voice>/report.json, results/<voice>/report.json.provenance.json, results/<voice>/verdict.json, GATE-G-004.md, GATE-G-001.md
- Evidence produced: T-P20 (run by the owner); G-001 record
- Done when: the G-001 response is recorded in `GATE-G-001.md`.
- Checkpoint: default
- On failure: result-pivot rules DR-10…DR-13 (record values, never tune the evaluation, halt at G-001).
- Gate: G-004, then G-001
- Relevant decisions/claims: D-016, D-017, A-009, A-011, A-012, A-016
- Lessons applied: PK-29 (L-20261009T234100, L-20261009T120011, L-20261010T000114); PK-35 (L-20261009T120003); PK-45 (L-20261009T160700, L-20261004T162210); PK-46 (L-20261009T090805)
- Exclusive resources: none

### S-018 Documentation and notices
- Tier: Sonnet
- Profile: software
- Depends on: S-017
- Inputs: G-001 record; D-026, D-030
- Actions: write `README.md` with a `## What it does` section whose every bullet cites a test ID; install instructions
  (copy the VST3 bundle to the user VST3 folder; COPY_PLUGIN_AFTER_BUILD is FALSE); training instructions pointing to the
  notebooks; `docs/PARAMETERS.md` generated by `tools/gen/parameters.py`, which reads `core/include/singvst/params.hpp`
  with the regex `\{\s*"(\w+)",\s*"([^"]+)",\s*([-0-9.]+)f,\s*([-0-9.]+)f,\s*([-0-9.]+)f,\s*([-0-9.]+)f,\s*"([^"]*)"\s*\}`
  and writes a table `| ID | Name | Minimum | Maximum | Default | Step | Unit |` under a line naming the source file
  (5 rows; fail if the count differs from `kParams`' declared size); `THIRD_PARTY_NOTICES.md` (JUCE, ONNX Runtime,
  nlohmann/json, CMUdict, RVC, TIGER/other voicebank terms, openvpi vocoder if used); sound descriptions only with the G-001
  record (PK-46).
- Outputs: README.md, docs/PARAMETERS.md, THIRD_PARTY_NOTICES.md, tools/gen/parameters.py
- Evidence produced: T-P23
- Done when: T-P22, T-P23 pass; the full suite is green.
- Checkpoint: default
- On failure: default
- Gate: none
- Relevant decisions/claims: D-010, D-026, D-030, C-012, C-037
- Lessons applied: PK-04 (L-20261009T120015, L-20261008T173532, L-20261009T234120); PK-40 (L-20261008T173531); PK-46 (L-20261009T090805); PK-50 (L-20261009T232011, L-20261004T161504)
- Exclusive resources: none

### S-019 Final verification and pull request
- Tier: Opus
- Profile: software, computational
- Depends on: S-018
- Inputs: everything above
- Actions: run the full suite locally; read the final CI run of all jobs through the API; map every plan step and
  pre-mortem control to a delivering file or test in `plan/TRACEABILITY.md` (PK-07); open a pull request impl → `main`
  (`gh pr create --base main --head <impl> --title "sing-vst implementation" --body-file <file>`), the body summarising the
  results and ending with the line `🤖 Generated with [Claude Code](https://claude.com/claude-code)` and the executing
  session's link if it has one; do **not** merge (G-002).
- Outputs: pull request URL in EXECUTION_LOG.md
- Evidence produced: all tests
- Done when: every frozen test passes (T-P20 from S-017's record), CI green on both OSes, the pull request exists.
- Checkpoint: default
- On failure: default
- Gate: none (merging is the owner's action, G-002)
- Relevant decisions/claims: D-018, D-029
- Lessons applied: PK-07 (L-20261009T161200, L-20261004T102010); PK-05 (L-20261004T102009, L-20261014T195600, L-20261010T000110)
- Exclusive resources: none

### S-RETRO Retrospective
- Tier: Opus
- Profile: software, computational
- Depends on: S-000…S-019
- Inputs: EXECUTION_LOG.md, commits, DEVIATIONS.md, BLOCKED.md and TEST_CHALLENGE.md (if present), GATE-*.md, CI history,
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
- Lessons applied: PK-05 (L-20261004T102009, L-20261014T195600, L-20261010T000110); PK-07 (L-20261009T161200, L-20261004T102010)
- Exclusive resources: none

### S-KNOW Lessons and knowledge push
- Tier: Haiku
- Profile: software
- Depends on: S-RETRO
- Inputs: lessons/, knowledge/, TAXONOMY.md, plan/ASSUMPTIONS.md A-014
- Actions: plan/PROTOCOL_EXCERPTS.md §3.7.2 — halt at G-003; on `push-to-proposed` copy lessons into `../store-lessons`
  and knowledge items into `../store-knowledge` in the Appendix C layout, regenerate each store's `lessons/INDEX.md` /
  `knowledge/INDEX.md` (tag → IDs, titles/statements, severity; generated, never hand-edited), merge this run's tags into
  each store's `TAXONOMY.md` (from the repository's `TAXONOMY.md`), push (3 retries with pull-and-regenerate; else
  `git bundle create knowledge-<run_id>.bundle`).
- Outputs: pushes to the stores, or the bundle path
- Evidence produced: none
- Done when: protocol 3.7.2 item 4.
- Checkpoint: default
- On failure: bundle fallback (3.7.2 item 3).
- Gate: G-003
- Relevant decisions/claims: Rule 13, A-014
- Lessons applied: PK-02 (L-20261010T000102, L-20261009T234124, L-20261009T232008); PK-12 (L-20261009T193602, L-20261010T000101, L-20261009T234112)
- Exclusive resources: none
