<!-- STATUS HEADER: written by the planning agent's final consistency check (protocol Phase 5) with tools/gen/status.py -->

# Execution plan — sing-vst

Read `HANDOFF.md` first. Every step uses the template of protocol 3.1. Steps run **one at a time, in ID order** (they share
one branch, `.checkpoints/state.json`, `core/src/stubs.cpp` and `python/singvst_train/cli.py`); a later step may start only
when every step in its `Depends on` has passed. "Full suite" means: `ctest` in the core and full build trees, plugin tests
under `xvfb-run -a`, and `../venv-lock/bin/python -I -m pytest -q -m "not torch and not voice and not network"` with
`SINGVST_RENDER_BIN` set once S-010 is done — all green except tests whose step has not been reached (listed in
`EXECUTION_LOG.md` per attempt). On the no-root path of S-000 action 3, "locally" is waived for T-034 and the plugin
tests T-053…T-059 (the full tree is not built): the CI `test-summary` notice of D-036 is their evidence. Whenever a
`Done when` names a CI result ("in CI", or a test that is CI-only on the current path), the step's last action is: Save
(which pushes), then wait for and read that commit's CI run as D-036 says. "Save" means `bash tools/save.sh "<S-### …>" <paths>` (commit + push + `.checkpoints/state.json`, D-029).
Defaults for every step unless the step says otherwise:
- **On failure (default):** fix the implementation, never a frozen test (DR-04); re-run the full suite after any fix to
  shared code (PK-51); after three failed attempts on the same test write `BLOCKED.md` (test, logs, hypotheses) and halt.
- **Checkpoint (default):** `python3.12 tools/checkpoint.py --phase impl --subphase <S-###> --active-step <next step> --complete <S-###>
  --done-pending <S-###>`, append one row to `EXECUTION_LOG.md` (HANDOFF §Logs), then Save. Before any high-latency action
  (long build, CI wait, gate) set `--in-flight '{"op": "…"}'` and Save, and after it set `--in-flight null` and Save, so
  the pushed checkpoint always shows what was in flight (D-034).
- **Exclusive resources (default):** the workspace CPU for builds — one heavy build at a time (PK-43).

### S-000 Environment & access verification
- Tier: Haiku
- Profile: software
- Depends on: none
- Inputs: generation branch `gen-20261004T095012Z-singing-voice-vst-pitch-lyrics`; plan/ENVIRONMENT.md; plan/ASSUMPTIONS.md A-014; research/PRIOR_KNOWLEDGE.md (task tags, line 3)
- Actions: (every session first: if `origin/impl-gen-20261004T095012Z-singing-voice-vst-pitch-lyrics` exists, check it
  out instead of creating it, keep the existing logs, and re-run only the actions whose out-of-tree results are missing —
  `.git/singvst-trailers`, `../build-*`, `../venv-lock`, `../rvc`, `../store-*`, `$HOME/deps` — then follow HANDOFF §Resume).
  The repository root is this session's checkout of `qualitycoding/sing-vst` (every relative path in this plan starts
  there); its parent directory must be writable (all `../` paths live there); if it is not, write `BLOCKED.md`.
  1. Attach `qualitycoding/sing-vst`, `qualitycoding/Lessons` and `qualitycoding/knowledge` with push access through the
     session's repository tool and clone the stores with the clone command it returns, into `../store-lessons` and
     `../store-knowledge` (never a pasted token — PK-12). `gh` uses the session's preconfigured GitHub credential. Read-only
     probes (PK-17), each must succeed: `gh api repos/qualitycoding/<repo> --jq .permissions.push`
     prints `true` for all three; `gh api repos/qualitycoding/sing-vst --jq .default_branch` prints `main`;
     `gh api "repos/qualitycoding/sing-vst/actions/runs?per_page=1"` (Actions readable); `gh api
     "repos/qualitycoding/sing-vst/pulls?per_page=1"` (pull requests readable). Write access for `gh run rerun` and
     `gh pr create` cannot be probed read-only: if either fails later, record it and use the fallback of D-036 (re-run) or S-019 (pull request).
  2. Branch (`<impl>` = `impl-gen-20261004T095012Z-singing-voice-vst-pitch-lyrics`): `git config --add remote.origin.fetch
     '+refs/heads/*:refs/remotes/origin/*'`; `git fetch origin` (`git fetch --unshallow origin` first if `git rev-parse
     --is-shallow-repository` prints `true`); `git switch -c <impl> origin/gen-20261004T095012Z-singing-voice-vst-pitch-lyrics`;
     `git push -u origin <impl>`; check `git rev-parse origin/<impl>` succeeds. Git identity: keep the environment's
     `user.name`/`user.email`; if either is empty, set `git config user.name "sing-vst implementer"` and `git config
     user.email noreply@anthropic.com`. Trailers: write to `.git/singvst-trailers` (untracked, read by `tools/save.sh`) the
     commit-message trailer lines your session's instructions prescribe, one per line; if they prescribe none, write
     `Co-Authored-By: <your model name> <noreply@anthropic.com>`.
  3. Tools: `cmake --version` ≥ 3.22, `ninja`, `g++ --version` major version ≥ 13 (CI uses 13.3; another major ≥ 13 is recorded in `DEVIATIONS.md`, < 13 →
     `BLOCKED.md`), `python3.12`,
     `curl`, `unzip` exist (else `BLOCKED.md`). With root or sudo: `sudo apt-get update && sudo apt-get install -y` the
     package list of the `cpp` job's apt step in `.github/workflows/ci.yml` (it includes `xvfb`) plus `python3.12-venv
     locales` (an install failure is the no-root path below), and generate the German
     locale T-034 needs (`localedef -i de_DE -f UTF-8 de_DE.UTF-8` as root, else `sudo locale-gen de_DE.UTF-8`; C-056).
     Without root/sudo or apt mirrors: record it in `DEVIATIONS.md`; the plugin build, plugin tests, pluginval and T-034 are
     then checked in CI only (D-036) — not a halt.
  4. Stores: record their HEADs with `python3.12 tools/checkpoint.py --merge 'knowledge_store={"commit_at_impl":
     {"lessons": "<sha>", "knowledge": "<sha>"}}'`; list files **added** after the R0 commits
     (first `git -C <clone> fetch --unshallow` when `git -C <clone> rev-parse --is-shallow-repository` prints `true`; then
     `git -C ../store-lessons log --diff-filter=A --name-only --format= ac028c7..HEAD`, and in `../store-knowledge` from
     `09f3458`) that are active (lessons `status: active`, knowledge items `status: current`) and whose tags include a task
     tag of research/PRIOR_KNOWLEDGE.md line 3 or `applies:all` (protocol Appendix C). Record each in
     `DEVIATIONS.md` (`Plan says` = the store rule or fact, `Done instead` = "followed" or "not followed: conflicts with
     <plan item or frozen file>"); the plan and frozen files win over a new store rule (PK-02).
  5. `bash research/spikes/hosts/run.sh > ../hosts-now.txt`; compare every row with plan/ENVIRONMENT.md §Hosts (its "run.sh roles" column maps the rows; 000 = unreachable, any
     HTTP status = reachable); a changed row
     is recorded in `DEVIATIONS.md` with the table's alternative channel; rows already marked unreachable are expected (PK-13).
  6. `bash tools/bootstrap_test_env.sh "$HOME/deps"`; configure **and build** the trees of plan/ENVIRONMENT.md (core, full,
     asan, tsan; long builds in the background, PK-18); create `../venv-lock`; clone RVC for reading:
     `git clone https://github.com/RVC-Project/Retrieval-based-Voice-Conversion-WebUI.git ../rvc && git -C ../rvc checkout 81eed5e8f68b6bed1789f682fe78cdd324495afc` (D-036) (PK-20, PK-55).
  7. `sha256sum -c tests/FROZEN_MANIFEST.sha256`; `../venv-lock/bin/python -I -m pytest -q tests/python/test_repo.py -m "not network" -k "not P23"`
     (T-060, T-061, T-062, T-P22, T-P27) and `../venv-lock/bin/python -I -m pytest -q tests/python/test_repo.py -m network` (T-P21).
  8. Start `EXECUTION_LOG.md` and `DEVIATIONS.md` with the HANDOFF §Logs templates **before** actions 3–5 write rows (create
     them right after action 2), and seed the checkpoint: `python3.12 tools/checkpoint.py --phase impl --subphase S-000
     --active-step S-001 --set 'completed=["S-000"]' --set 'pending=["S-001", "S-002", "S-003", "S-004", "S-005", "S-006", "S-007", "S-008", "S-009", "S-010", "S-011", "S-012", "S-013", "S-014", "S-015", "S-016", "S-017", "S-018", "S-019", "S-RETRO", "S-KNOW"]' --in-flight null`.
- Outputs: impl branch; .git/singvst-trailers (untracked); EXECUTION_LOG.md; DEVIATIONS.md; .checkpoints/state.json (knowledge_store.commit_at_impl, pending); ../store-lessons, ../store-knowledge, ../rvc, $HOME/deps, ../build-core, ../build-full, ../build-asan, ../build-tsan, ../venv-lock, ../hosts-now.txt
- Evidence produced: none
- Done when: every action succeeded (or recorded its documented fallback); the action 7 commands pass.
- Checkpoint: default
- On failure: halt and write `BLOCKED.md` naming what is missing (credential, host, package) before any delivery work —
  except a T-P21 (pip-audit) finding: apply DR-07 once (regenerate the lock, update the Toolkit lock row of
  plan/ENVIRONMENT.md with the new line count, record it in `DEVIATIONS.md`); a second finding or an incompatible fix →
  `BLOCKED.md`.
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
  side, implementing exactly the D-022 **Protocol** sequence for `acquire`/`release`/`publish`/`collect`; R-024); run the full suite; run T-038 in `../build-tsan` with the plan/ENVIRONMENT.md sanitizer lines.
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
- Actions: implement `importMidi` in `core/src/midifile.cpp` with bounds-checked reads, the D-031 limits and running-status rule;
  run the full suite, then T-064…T-066 and T-069 in `../build-asan` with the plan/ENVIRONMENT.md sanitizer lines.
- Outputs: core/src/midifile.cpp, core/src/stubs.cpp
- Evidence produced: T-064…T-066, T-069
- Done when: T-064…T-066 and T-069 pass, clean under ASan+UBSan.
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
- Actions: implement `standardNormal` (golden values of D-012) in `core/src/random.cpp`, `loadOrtRuntime`,
  `ortRuntimeLoaded` (moved out of `core/src/stubs.cpp`) and `bundledOrtFileName` in `core/src/ort_runtime.cpp`, and `resample` in `core/src/resample.cpp`; push; read the CI `cpp` job
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
  100-frame context, `standardNormal` noise, the 10-ms `SetTerminate` cancel watcher, rejection of external-data models);
  run the full suite. `research/spikes/oracle/engines.py` (an independent
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
- Actions: implement render.hpp in `core/src/render.cpp` (with the D-013 limits and engine ownership) and take_cache.hpp in
  `core/src/take_cache.cpp` exactly as D-038 (research/spikes/premortem-r1/take_cache_sketch.cpp is a debugging reference
  only); run the full suite; T-050, T-051 and T-068 in `../build-tsan` (`ctest -R "T-050|T-051|T-068"`; CI's TSan step runs the same set), T-067 and T-070 in `../build-asan` (plan/ENVIRONMENT.md).
- Outputs: core/src/render.cpp, core/src/take_cache.cpp, core/src/stubs.cpp (now empty of definitions; delete it if nothing remains)
- Evidence produced: T-048…T-052, T-067, T-068, T-070
- Done when: all core tests T-001…T-052, T-063…T-070 pass; T-050/T-051 clean under TSan; CI `sanitizers` green.
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
  `seeds = {"converter": <seed>}` and the D-014 shapes; `git_commit` from a header generated at build time by a custom
  command in `cli/CMakeLists.txt` that runs on every build, R-047); set `SINGVST_RENDER_BIN` to the built binary for every later run of the suite.
- Outputs: cli/main.cpp, cli/CMakeLists.txt
- Evidence produced: T-P18
- Done when: T-P18 passes locally and in CI job `python`. (The binary part of T-P13 needs `pack_voice` and is checked at S-012.)
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
  every API used before using it (PK-37); follow D-022 **Plugin threading**, D-010's take cache and status line and D-027's
  `launchAsync` dialogs (no modal loop; R-048); build `build-full`; run plugin tests under `xvfb-run -a`; run pluginval 1.0.4
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
- Depends on: S-000, S-010
- Inputs: python/singvst_train/{prepare,pipeline,provenance,metrics,pack,security,cli}.py; D-015, D-016, D-017, D-019
- Actions: implement the bodies (signatures and docstrings unchanged, T-P27; conventions of D-033), register **all nine**
  sub-commands of `cli.COMMANDS` (T-P25 needs every `--help`; later steps add the options and bodies of theirs), and implement
  `split`, `prepare`, `pack`, `provenance` exactly as D-035; close every resource with context managers (PK-41).
- Outputs: those modules
- Evidence produced: T-P01…T-P15 (T-P13 including its binary part `test_P13b_…`), T-P25
- Done when: T-P01…T-P15 (T-P13 with `SINGVST_RENDER_BIN` set to the S-010 binary), T-P25 and T-P27 pass; `(cd python && ../../venv-lock/bin/python -m singvst_train.cli prepare --help)` exits 0.
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
  `make-test-weights` (D-035); `export --exp-name` delegates to `rvc_files.latest_weights`, which S-014 implements (no
  test before S-014 uses `--exp-name`); push and read the CI `python-torch` job (D-036: one attempt = one CI run of a new commit; no
  local torch); read the `hf-revision` notice annotation of that job and replace "`--revision main` (S-013 records the
  resolved revision here)" in the plan/ENVIRONMENT.md pins table with the printed SHA (the job's RVC checkout and its
  `rvc/assets/hubert_base` exist only on the CI runner).
- Outputs: python/singvst_train/export_rvc.py, python/singvst_train/cli.py, plan/ENVIRONMENT.md (Hugging Face revision row)
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
  (D-033). Dry run (the real run is the owner's at S-017): put two stand-in modules on `PYTHONPATH` in a temporary directory —
  `resemblyzer.py` with `preprocess_wav(fpath_or_wav, source_sr=None)` returning a 1-second zero array and a `VoiceEncoder`
  whose `embed_utterance` returns a fixed 256-value unit vector (the real API, C-058), and `whisper.py` with `load_model(name)` returning an object whose `transcribe(path, **kw)` returns
  `{"text": ""}` (the real `load_model`/`transcribe` names, C-059); the stand-in `VoiceEncoder.__init__(self, *a, **k)`
  accepts any arguments. Write a temporary held-out folder `<tmp>/heldout` holding two 2-second 220 Hz 15-partial harmonic
  tones as `<tmp>/heldout/h1.wav` and `h2.wav` (48000 Hz, soundfile), then run, from `python/` without `-I` (so `PYTHONPATH` applies): `PYTHONPATH=<tmp>/stubs
  ../../venv-lock/bin/python -m singvst_train.cli evaluate --voice ../tests/fixtures/voice-convert --heldout <tmp>/heldout
  --phrases ../eval/phrases --render-bin ../../build-core/cli/singvst-render --out <tmp>/eval --thresholds
  ../eval/thresholds.json`, and check the output files (all `evaluate.REPEATS` renders per phrase, `spread.json`) and keys of
  eval/PROCEDURE.md exist (values are meaningless; a `status` of "invalid: …" is acceptable for the dry run). Finally write `GATE-G-005.md` (plan/GATES.md), save, and halt.
- Outputs: python/singvst_train/evaluate.py, python/singvst_train/cli.py, GATE-G-005.md
- Evidence produced: T-P26
- Done when: T-P26 and T-P25 pass.
- Checkpoint: default
- On failure: default
- Gate: G-005
- Relevant decisions/claims: D-017, C-028
- Lessons applied: PK-29 (L-20261009T234100, L-20261009T120011, L-20261010T000114); PK-31 (L-20261009T120008, L-20261009T120002, L-20261004T162219); PK-33 (L-20261004T162217, L-20261007T150832); PK-35 (L-20261009T120003)
- Exclusive resources: none

### S-016 Training notebooks
- Tier: Sonnet
- Profile: software
- Depends on: S-013, S-014, S-015, G-005 answered
- Inputs: D-016, D-019, D-025, D-035; plan/GATES.md G-004; the G-005 answer; ../rvc (RVC 81eed5e checkout)
- Actions: write `notebooks/train_voice_colab.ipynb` and `notebooks/train_voice_kaggle.ipynb` (nbformat 4, no outputs)
  with exactly the cells of D-035 §Notebook layout and §Notebook environment (installs split by index, C-062; RVC's own
  `requirments_cu128_py312.txt` from the RVC checkout at 81eed5e), and the guide voicebank cells of D-035 §Guide voicebank for the G-005 answer. Before writing
  the RVC cells, `grep -n sys.argv ../rvc/train/preprocess.py ../rvc/train/dataset/extract_f0.py
  ../rvc/train/dataset/extract_hubert_feature.py` and check the D-035 command lines against it (C-057); the voicebank is
  downloaded by the owner inside the notebook and never stored in the repository. The stage table is built by one code
  cell defining `make_stages(run, rvc, sh)` (`sh` runs one shell command); write `tools/notebook_dryrun.py` (run with `../venv-lock/bin/python -I`; it puts `python/` on `sys.path` itself), which
  loads each notebook with nbformat, finds the cell containing `def make_stages` (D-035 cell (3)), execs it with the
  globals `VOICE="dry"`, `RUN=1`, `EPOCHS=10`, `DEREVERB=False`, `SPEAKER_ID=0`, `GUIDE="tiger"` and with a fake `sh` that creates each stage's declared outputs, runs the stages
  in `<tmp>/a`, packs `<tmp>/a` with the notebook's own cell-(17) `state.tar` code and restores it into `<tmp>/b` by
  executing the notebook's own cell-(3) restore code with `/kaggle/input` and `/kaggle/working` remapped to `<tmp>/in` and
  `<tmp>/b` (R-066), runs them again (no stage may run),
  then edits `params.json` and runs again (every stage must run); it must exit 0 for both notebooks (R-016, R-013).
  GATE-G-004.md (S-017) gives the owner opening links pinned to a commit (R-029): Colab
  `https://colab.research.google.com/github/qualitycoding/sing-vst/blob/<EXPECTED_COMMIT>/notebooks/train_voice_colab.ipynb`;
  Kaggle: *File → Import notebook → GitHub* with that commit and path `notebooks/train_voice_kaggle.ipynb`.
- Outputs: notebooks/train_voice_colab.ipynb, notebooks/train_voice_kaggle.ipynb, tools/notebook_dryrun.py
- Evidence produced: T-P16, T-P17; `tools/notebook_dryrun.py` output in EXECUTION_LOG.md
- Done when: T-P16, T-P17, T-P22 pass; `../venv-lock/bin/python -I tools/notebook_dryrun.py` exits 0.
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
  1a. `GATE-G-004.md` gives the commit-pinned notebook URLs, the attestation sentence of D-035 and the Parameters-cell
     values (`VOICE` = `myvoice` unless the owner names one, `RUN` = the issue number, `EXPECTED_COMMIT` = `git rev-parse
     HEAD` after S-016's last save, `DEREVERB`/`EPOCHS` defaults of D-035); the response reports the values used.
  2. After the owner runs the notebook, they attach `upload-run<RUN>.tar` and paste its `sha256sum` line (D-035); a
     `failed: …` response is handled as plan/GATES.md G-004 says; the notebook's last test cell is T-P20.
  2a. Verify before committing (R-036, R-056; log every check in EXECUTION_LOG.md): the tar's SHA-256 equals the pasted
     line (two mismatches → `BLOCKED.md`), then extract it outside the repository;
     `budget.json` `gpu_hours` equals the sum of its `sessions[].gpu_hours` and is > 0 when `train` ran (R-051);
     `metrics.judge(report, eval/thresholds.json)` recomputed locally equals `verdict.json`; the report provenance
     `params.voice_name` = `training.json` `voice_name` = `<VOICE>-run<RUN>`; every `budget.json` `sessions[].commit` is
     on the impl branch; `train` appears in some session's `stages_run` (or `stopped_by_budget` is set). A failed check →
     ask the owner for the files again (at most twice, then `BLOCKED.md`); files are never edited. GATE-G-001.md gets the
     `training.json` `stage_commits` table (which stage ran under which commit, R-054).
  3. Commit the extracted files to `results/<VOICE>/run<RUN>/` (`VOICE` and `RUN` of the response and GATE-G-004.md; the
     package name `<VOICE>-run<RUN>` is checked in action 2a); before re-issuing a gate, `git mv` the previous gate file:
     after `failed:` to `GATE-G-004.run<RUN>.fail<k>.md` (k = 1, 2, 3), after `retrain` to `GATE-G-004.run<RUN>.md` and
     `GATE-G-001.run<RUN>.md` (history kept, Rule 9); never commit audio, recordings or voice packages (T-062).
  4. Write `GATE-G-001.md` with the G-001 evidence (including `docs/UNVERIFIED.md`; per threshold metric the verdict and
     "indeterminate" when min ≤ threshold ≤ max of `spread.json`, the `similarity_gain` spread being the per-repeat
     differences, D-017) and halt.
- Outputs: results/<VOICE>/run<RUN>/ (report.json, report.json.provenance.json, verdict.json, spread.json, ceiling.json, budget.json, budget-voice.json, training.json, env/), GATE-G-004.md, GATE-G-001.md (earlier issues as GATE-G-00<k>.run<RUN>[.fail<k>].md)
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
  notebooks on `main` (R-029) with the privacy rule of D-035 (R-021); a `## Limits and care` section: where the take cache
  lives and that deleting it forfeits exact recall (R-017), short sections at constant tempo and one render per edit per
  instance (R-028), what a red T-P21 means and the owner's DR-07 procedure (R-041), and — when G-001 set thresholds — both
  verdicts and the statement that the thresholds were set after the measurement (R-037); `docs/PARAMETERS.md` generated by `tools/gen/parameters.py`, which reads `core/include/singvst/params.hpp`
  with the regex `\{\s*"(\w+)",\s*"([^"]+)",\s*([-0-9.]+)f,\s*([-0-9.]+)f,\s*([-0-9.]+)f,\s*([-0-9.]+)f,\s*"([^"]*)"\s*\}`
  and writes a table `| ID | Name | Minimum | Maximum | Default | Step | Unit |` under a line naming the source file
  (5 rows; fail if the count differs from `kParams`' declared size); `THIRD_PARTY_NOTICES.md` (JUCE, ONNX Runtime,
  nlohmann/json, CMUdict, RVC, TIGER/other voicebank terms, openvpi vocoder only if the G-005 answer or the packed voice uses one:
  one `## <component> <version or commit>` section each, with licence name, source URL at the pin and the full licence text
  copied from `$HOME/deps/JUCE/LICENSE.md`, `$HOME/deps/ort/LICENSE`, `../build-core/_deps/json-src/LICENSE.MIT`,
  `third_party/cmudict/LICENSE`, `../rvc/LICENSE`; the voicebank section gives licence name, URL and the personal
  non-commercial restriction only (C-037; never redistributed); check `grep -c '^## ' THIRD_PARTY_NOTICES.md` equals the
  number of components); sound descriptions only with the G-001
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
- Actions: run the full suite locally; read the final CI run of all jobs through the API (D-036); check `git diff --stat
  <report git_commit>..HEAD -- core cli python/singvst_train eval` for the committed results: when it is not empty, list the
  changes in `DEVIATIONS.md` and the pull request body and ask the owner there whether to re-run `evaluate` (R-038, PK-67); write
  `plan/IMPLEMENTATION_MAP.md` — a table `| Item | Delivered by (file or test) | Status |` with one row per plan step, per
  `Mitigation` cell of `premortem/RISK_REGISTER.md` (which holds every R-### of the planning pre-mortem rounds
  `premortem/round-*.md`), unmapped items listed
  in `DEVIATIONS.md` (PK-07); open a pull request impl → `main`
  (`gh pr create --base main --head <impl> --title "sing-vst implementation" --body-file ../PR_BODY.md`, the body written outside the repository; if `gh pr create` is refused, put the body and the compare URL
  `https://github.com/qualitycoding/sing-vst/compare/main...<impl>` in `EXECUTION_LOG.md` and ask the owner to open the pull
  request from that URL in the final message — not a halt), the body summarising the
  results and ending with the line `🤖 Generated with [Claude Code](https://claude.com/claude-code)` and the executing
  session's link if it has one; after creating it, check `gh pr view <n> --json isDraft --jq .isDraft` prints `false`
  (PK-68); do **not** merge (G-002).
- Outputs: plan/IMPLEMENTATION_MAP.md; pull request URL in EXECUTION_LOG.md
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
  each missing fact; run `python3.12 tools/check_schema.py`.
- Outputs: RETROSPECTIVE.md, lessons/L-*.md, knowledge/K-*.md
- Evidence produced: none
- Done when: every finding links to an L- or K- file; `python3.12 tools/check_schema.py` prints "all entries valid".
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
- Actions: plan/PROTOCOL_EXCERPTS.md §3.7 (3.7.2) — write `GATE-G-003.md` and halt. On `push-to-proposed`: copy each lesson to
  `../store-lessons/lessons/<facet>-<value>/` named by its first `tech:` or `domain:` tag (e.g. `tech:git` → `tech-git/`; no
  such tag → `general/`) and each knowledge item to `../store-knowledge/knowledge/<value>/` named by its first `subject:` tag
  (the stores' existing layout); append to each store's `TAXONOMY.md` every tag of this repository's `TAXONOMY.md` it lacks;
  in each store run `python3.12 scripts/check_knowledge_schema.py` (must pass) and `python3.12 scripts/build_index.py`
  (regenerates `lessons/INDEX.md` and `knowledge/INDEX.md`); commit and push (3 retries with pull + `build_index.py`).
  On `push-to: <target>`: attach the target with push access through the session's repository tool, check
  `gh api repos/<target> --jq .permissions.push` is `true`, clone it with the returned command, create any missing
  `lessons/`, `knowledge/`, `scripts/` (copied from `../store-lessons/scripts/`) and `TAXONOMY.md` (copied from this
  repository), and do the same.
  If the push still fails, or the owner's next message does not answer G-003 after it has been asked twice, write
  `git bundle create ../knowledge-<run_id>.bundle HEAD` (`<run_id>` = `run_id` in `.checkpoints/state.json`) (the bundle carries `lessons/` and `knowledge/`) and report its path.
- Outputs: pushes to the stores, or the bundle path
- Evidence produced: none
- Done when: protocol 3.7.2 item 4.
- Checkpoint: default
- On failure: bundle fallback (3.7.2 item 3).
- Gate: G-003
- Relevant decisions/claims: Rule 13, A-014
- Lessons applied: PK-02 (L-20261010T000102, L-20261009T234124, L-20261009T232008); PK-12 (L-20261009T193602, L-20261010T000101, L-20261009T234112)
- Exclusive resources: none
