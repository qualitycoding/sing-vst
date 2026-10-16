# Pre-mortem: round 2 (Phase 4)

**Scope.** I read the plan at branch `gen-20261004T095012Z-singing-voice-vst-pitch-lyrics` (HEAD `570c4d4`) without changing anything. Files read: HANDOFF.md, plan/*.md, eval/PROCEDURE.md, eval/thresholds.json, research/claims.json (60 claims), research/PRIOR_KNOWLEDGE.md (PK-01…PK-73), research/spikes/premortem-r1/*, premortem/round-1.md, premortem/RISK_REGISTER.md, tests/ (C++ and Python), .github/workflows/ci.yml, tools/, cmake/, CMakeLists.txt, cli/, core/include/singvst/*.hpp and python/singvst_train/*.py.

Severity follows Global Rule 4 for the `software` and `computational` profiles. Anything marked UNVERIFIED could not be checked in this offline, read-only review.

**Disclosure.** For R-057 I also read RVC 81eed5e's `i18n/i18n.py` and `i18n/locale/en_US.json:135` in a local read-only checkout outside the clone (`/home/claude/deps/rvc-src/rvc`). That is outside the stated evidence boundary, so I'm flagging it here. The finding also stands on in-repo evidence alone: research/spikes/premortem-r1/rvc_resume.txt:22 shows the log message is passed through `i18n(...)`, and the spike never captured the text that is actually written.

**Commit note.** T-P22 scans `premortem/*.md` and resolves `R-###` against premortem/RISK_REGISTER.md (tests/python/test_repo.py:107-120). This file must be committed together with register rows R-051…R-067, or T-P22 fails (the same coupling as R-049).

---

## 1. Simulation

*Values in both narratives are illustrative, not measurements, unless a source is cited.*

### 1a. [software] Six months after delivery: catastrophic failure in the DAW

| When | What the owner sees | Traced root cause |
|---|---|---|
| Merge + 0 | The owner builds the VST3 on Windows (plan/ENVIRONMENT.md:71-83) and loads `myvoice-run1` from the Google Drive for desktop folder. Recall works: reopening a project plays the stored take (T-067, T-068). | D-038 works as specified |
| + 1 month | A 4-minute song with three instances. Each completed render writes a 56 + 4n-byte file (D-038, DECISIONS.md:629-632). That is 46,080,056 bytes for 240 s at 48 kHz, written to `%APPDATA%\sing-vst\takes` on the system drive. Every lyric pause (500 ms debounce), every completed slider render and every sample-rate change adds a file. Nothing is ever pruned (DECISIONS.md:290-291). | R-058 |
| + 3 months | The owner imports an ambient part with a 70-s legato passage that has no rest ≥ 0.25 s. D-012 splits phrases only at SP ≥ 22 frames (DECISIONS.md:193-197), so the acoustic model and the vocoder run once over the whole passage. ORT's arena keeps the peak. With three instances, memory use climbs until the OS pages heavily, and one instance reports `Failed: bad_alloc`. The 900-s/5000-note limits (T-070) do not bound a phrase. | R-060 (R-027 partially mitigated) |
| + 5 months | The system drive fills. The DAW's autosave fails mid-write, and whether the project file survives depends on the host. The owner frees space by deleting `sing-vst/takes`, which README calls a forfeit of exact recall (S-018). | R-058 |
| + 6 months, **catastrophe** | The owner moves to a new laptop. They copy the projects and sync Drive, but the cache stays behind on the old machine (it is per machine, under userApplicationDataDirectory; D-010:288-289). The interface now runs at 44.1 kHz. On load, `cachedRender` misses silently (take_cache.hpp:21-23), and the sample-rate trigger (DECISIONS.md:284-285) re-keys the request anyway. Every instance renders a new performance. TIGER's noise is unseeded (C-040), so the approved lead vocals of a whole EP are replaced with different takes and no message is shown. The owner mixes and masters the replacements before noticing. | R-059 (R-017 partially mitigated) |

**Root-cause summary.** The take cache fixed recall on one machine at one sample rate. It made the cache an unbounded, unportable, silent single point of truth for approved audio. Phrase length was never bounded.

### 1b. [computational] Twelve months after completion: a claimed result is false

| When | Event | Traced root cause |
|---|---|---|
| G-004 run 1, Colab, session 1 | Cell (3) starts the 5-minute budget heartbeat, which writes `<run>/out/budget.json` (DECISIONS.md:601-604). `<run>` is on Drive (:508). Drive is mounted only in cell (4), after the installs (:506-507, :546). `atomic_write_text` raises `FileNotFoundError` in the background thread, the thread dies, and the traceback scrolls past. Every session repeats this. | R-051 |
| Sessions 1–3 | With no heartbeat, `gpu_hours` never grows. The train timeout is `min(10 h − elapsed − 0.5 h, 20 h − 0)`, and DR-13's 20-h stop never fires. Training spans three sessions of about 9 h each. `env-freeze.txt` is overwritten every session (:503-506). | R-051, R-054 |
| Session 3, cell (15) | `evaluate` runs `out/bin/singvst-render` from Drive and gets `Permission denied` (Drive FUSE has no exec permission; UNVERIFIED). Cell (4) only built the binary and never ran it. | R-052 |
| `failed: 15` | The implementer fixes the notebook so the binary is copied to local disk. D-035 says every G-004 issue has its own RUN (:511), and GATES.md:57-59 says "re-issues G-004". A new RUN would retrain everything. Under the default rule (most reversible), the implementer keeps `RUN = 1` with a new `EXPECTED_COMMIT`. Session 4 re-runs render-bin, pack and evaluate at commit Y. Split, prepare and the RVC features came from commit X. | R-053, R-054 |
| S-017 | The verification passes: the hashes match (budget.json is static because the heartbeat is dead), and both commits are on the impl branch. `gpu_hours` is labelled "lower bound", and 0.4 h is technically a lower bound. GATE-G-001 shows similarity 0.77 with spread [0.755, 0.781]. spread.json has no `similarity_gain` key, so the implementer derives a gain interval ad hoc. G-001 answers `proceed`. README says the voice was trained on a free GPU within the 20-h budget (SC-9). | R-051, R-061 |
| + 12 months | The owner trains a second voice on Kaggle with the same plan. The heartbeat works there. Training needs about 27 GPU-hours, so DR-13 stops it at 20 h, and the "start a new session" stops end versions in an error state. The restore assumption (C-019, tier-3 sources) does not hold, so sessions repeat work. Set against the archived run-1 `training.json` (epochs 200), the SC-9 claim and the committed `gpu_hours` are shown to be false. The committed `env-freeze.txt` describes session 4, not the environment that trained the model. | R-051, R-055, R-054 |

**Root-cause summary.** The round-1 changes were each correct locally but were not checked against one another:
- The mount-after-installs reorder (R-020) broke the heartbeat (R-034) and the freeze (R-019).
- Per-run roots on Drive (R-015) combined with an early build (R-023) put an executable where it cannot run.
- "Every issue is a new RUN" (R-013) has no rule for `failed:` re-issues.

---

## 2. Round-1 mitigation audit

| Round-1 risk | Verdict | Reason (file:line) |
|---|---|---|
| R-013 | adequate | Each issue gets its own run root, experiment and package (DECISIONS.md:511-517). params.json is guarded per session and is an input of every stage (:524-527, :584-586). The dry run edits params.json and re-runs every stage (PLAN.md:385-389). S-017 checks that `train` appears in `stages_run` (PLAN.md:418). Residual: code commit and session-derived parameters are outside stage identity (R-054). |
| R-014 | adequate | No experiment crosses runs (:513-517). C-061 / rvc_resume.txt:247-256, 293: resume restarts *at* the saved epoch, so a re-run of train after `run_stages` deleted `<exp>.pth` (pipeline.py:28-30) repeats epoch `total` and rewrites the final weights. The completion rule is at :569-570. |
| R-015 | adequate | Per-run roots and the `<VOICE>-run<RUN>` package name (:511-517). The status line shows manifest name and SHA prefix (:291-292). Side effects: R-052, R-063. |
| R-016 | partially | The restore rule exists (:541-543), but it rests on Kaggle output semantics that were never researched (C-019 is single-source, tier 3): file count and size limits, and whether an errored or stopped version keeps `/kaggle/working`. The dry run re-implements the restore inside `tools/notebook_dryrun.py` instead of executing the notebook's cell (3) (PLAN.md:386-389). → R-055, R-066 |
| R-017 | partially | The cache gives bit-exact recall on one machine (DECISIONS.md:628-635; T-067, T-068). But it grows without bound (:290-291), is not portable, misses silently (take_cache.hpp:21-23), is re-keyed by sample-rate changes (:284-285), cannot play without the voice loaded (:285-287), and rejects takes within about 10 ms of 900 s. → R-058, R-059, R-067 |
| R-018 | partially | Five repeats with means and spread (eval/PROCEDURE.md:19-25; test_evaluate.py:49-55). The single-draw problem is fixed, but the G-001 "indeterminate" rule (GATES.md:12-13; PLAN.md:423-424) cannot be applied to `similarity_gain`, which has no spread key. → R-061 |
| R-019 | partially | The freeze, env.json and training.json exist (DECISIONS.md:503-506, :576-577). But the freeze is overwritten every session, so only the last session's environment is committed. On Colab it is also written before Drive is mounted. → R-054, R-051 |
| R-020 | partially | Single-index installs resolve the dependency-confusion problem (:493-502; ci.yml:150-158). The reorder that mounts Drive after the installs (:506-507) conflicts with the cell (3) heartbeat and the `<run>/out` writes → R-051. No hash pinning (register residual). |
| R-021 | adequate | The visibility rule (:616-617) and the G-004 response requirement (GATES.md:47-49, :54-55). |
| R-022 | adequate | `resemblyzer --no-deps` plus webrtcvad-wheels (:498-502; C-062). Cell (6) imports and loads Whisper before any GPU stage (:553-555). |
| R-023 | partially | The build is moved before the GPU stages and prints `g++ --version` (:547-549). But the build tree and `out/bin` live under `<run>`, which is on Drive for Colab (:508, :548, :572-574), and the binary is never run before cell (15). → R-052 |
| R-024 | adequate | D-022 Protocol (:263-266). Case analysis for one reader: a reader that loaded `p` before a publish either has `inUse == BUSY` or `inUse == p` at every `collect` load (all `seq_cst`), and a reader that starts after the publish sees the new `current`. No use-after-free. T-038 remains probabilistic, but the specification is exact. |
| R-025 | adequate | 10-ms `SetTerminate` watcher (:197-200), `shared_ptr` ownership, join without detach (:239-242). The residual bound is the slowest single graph node plus non-ORT work after the last run (resample, `storeTake`). That is acceptable. |
| R-026 | partially | FIFO, atomics and mutex (:268-273). But the capture state machine is driven from processBlock (:279-282), while D-022 makes "every other piece of state" mutex-guarded, and `arm(true)` resets FIFO indices from the message thread while the audio thread may be writing. → R-064 |
| R-027 | partially | Take-level limits (:242-243, :636-637; test_limits.cpp:41-55), but phrase length is not bounded, and guide memory scales with phrase length. → R-060 |
| R-034 | **inadequate** | On Colab, the primary platform, the heartbeat starts in cell (3) (:601-604) before Drive is mounted in cell (4) (:506-507, :546). It either dies or blocks the mount. The "GPU time" definition (:532) also excludes the session overhead that platform quotas charge. → R-051, R-062 |
| R-035 | partially | The checkpoint guard handles truncated files (:563-566). The pretrained-fallback detector looks for the Chinese source literal (:568-569), but train.py logs `i18n(...)` (rvc_resume.txt:22), which is English in an en_US runtime. The silent-restart path it was meant to catch stays undetected. → R-057 |
| R-036 | partially | The SHA list, the verdict recompute and the name/commit checks exist (PLAN.md:415-419). But budget.json keeps being rewritten after cell (17) hashes it (:583, :601-604), pasted text is not byte-stable, and "ask again" has no exit. → R-056 |
| R-040 | adequate | Skipped cases are listed separately and never counted as passed (tools/ci_annotate.py:20-25). D-036 takes the summary as the criterion for multi-test steps (DECISIONS.md:649-651). No test uses SKIP (grep of tests/). |

---

## 3. Lenses

**Technical correctness.** R-051 (cell order), R-052 (executing from Drive), R-057 (log-string mismatch), R-060 (unbounded phrase), R-064 (capture state and FIFO reset), R-067 (900-s edge).

I checked the TakeSlot protocol (sound), D-038's size check before allocation (T-067), and C-061's resume-at-saved-epoch behaviour (R-014 is closed). In `run_stages`, re-running train after a missing marker is recoverable.

**Dependency and supply-chain drift.**
- RVC's cu128 ranges (C-023) are resolved again every session, and only the last session's freeze is kept (R-054).
- The uv-managed CPython patch level drifts; env.json records it (C-060).
- No hashes on the notebook installs (R-020 residual).
- CI `python-torch` still resolves Hugging Face `main` on every run (ci.yml:164; R-043 open).
- `<root>/assets-archive/` checks each asset against a SHA-256 it recorded itself on first download (:550-552). There is no independent pin for the RVC assets or the Whisper weights. Low; not raised as a separate risk.

**Invalid research assumptions.**
- *Claims not `verified`:*
  - C-010 (single-source): covered by G-005.
  - C-017 (corroborated): says Drive I/O should use archives, yet the plan now builds and executes binaries on Drive (R-052).
  - C-018 (corroborated): covered by R-001.
  - C-019 (single-source, both sources tier 3): the whole Kaggle restore design rests on it (R-055).
  - C-026 (corroborated): covered by T-041.
- *Single-source claims touched by round-1 changes:*
  - C-061: the spike read the source literal, not the emitted log text (R-057).
  - C-062: adequate as used.
  - C-040, C-047: adequate.
- *Unresearched, with no claim:*
  - Colab `drive.mount` on a non-empty mountpoint (R-051).
  - Exec permission and symlink support on Drive FUSE (R-052).
  - Kaggle output persistence and limits (R-055).
  - Vocoder memory as a function of phrase length (R-060).

**Implementer misinterpretation.**
- RUN semantics of `failed:` re-issues (R-053).
- Cell placement:
  - D-035 assigns no cell to the `params.json` write (:524-527) or to symlink creation (:515-517).
  - On Colab, both must come after the Drive mount; R-051 is the concrete case.
- Gain spread (R-061).
- Capture state atomic versus mutex (R-064).
- Stale gate text (R-065).
- The dry-run interpreter (R-066).

**Integrity (Rule 9).**
- Committed `gpu_hours` can be silently wrong (R-051).
- A run spanning commits is attributed to the evaluating commit only (R-054).
- The verification loop has no exit (R-056).
- `epochs_trained` can be false after an undetected pretrained restart (R-057).
- Not every G-001 number has a specified computation (R-061: gain interval; ceiling.json is inline notebook code with no test and no stage).
- Positives: files are never edited; gate history is kept with `git mv` (PLAN.md:421-422).

**Past lessons (PK).**
- Applied as claimed: PK-62, PK-67, PK-68, PK-69 (C-062 quotes non-comment lines).
- Partially applied:
  - PK-70: no spread for the gain (R-061).
  - PK-71: commit and batch size are not part of stage identity (R-054).
  - PK-72: recall is per machine and misses silently (R-059).
  - PK-73: only the last session's environment is kept (R-054).
  - PK-43: per-phrase memory (R-060) and Drive headroom per run (R-063).
- Recurrences:
  - PK-58 (L-20261015T180000Z): unassigned notebook actions and the cell-order interface (R-051).
  - L-20261015T180200Z (stale cross-references after renames): GATES.md was not updated for the round-1 changes (R-065).
  - PK-55 / ENVIRONMENT.md:50: a `tools/` script that needs a lock-only package (R-066).
  - The C-061 spike repeats the shape of L-20261016T040000Z (reading a literal instead of the effective value), applied to log output (R-057).

**Scale and performance.**
- R-058: cache growth.
- R-060: phrase memory.
- R-063: Drive space per run.
- Also, with no risk ID: TakeSlot `publish` takes a `unique_ptr`, while `Renderer::latest()` returns a `shared_ptr<const>`. Every take is therefore copied on the message thread, up to about 173 MB for a 900-s take at 48 kHz, and three copies per instance can be resident at once (renderer, slot, retired).

**Security.** No new exposure meets the bar.
- Cache files are size-checked before allocation (T-067).
- The checkpoint guard's `torch.load(..., weights_only=False)` (:564) can execute pickled code. On Kaggle it runs on files restored by `glob("/kaggle/input/*/run<RUN>/…")` (:541-543), so exploitation needs the owner to attach a hostile third-party input. Recommendation: use `weights_only=True` (the G/D checkpoints hold tensors and numbers) and restrict the glob to the notebook's own output slug.
- The notebook venv keeps `setuptools<81` (C-062), which carries PYSEC-2026-3447 (C-046). The notebook never uses setuptools' download paths.

**Operational realities.**
- R-055: the Kaggle fallback.
- R-058 and R-059: cache lifecycle.
- R-062: budget per voice.
- R-065: stale gate text.
- After the merge, R-053's ambiguity carries over to any owner-run retrain.

**Audio thread (PK-38).** TakeSlot is sound (section 2). processBlock under ScopedNoDenormals has no locks or allocation by specification. The open issue is R-064 (capture state and FIFO reset).

**Numerical validity.**
- R-061: the gain spread is undefined, and the ceiling computation is untested.
- R-067.
- The [min, max] of 5 repeats captures guide noise only, not training or held-out-split variance. GATES.md:12-13 states only "spread over the 5 repeats", which is accurate.
- I computed the phrase durations by parsing `eval/phrases/*.mid` in this review: 4.8–5.4 s each. Evaluation cost is negligible.

**Reproducibility.**
- R-054: multi-session provenance.
- R-057: a silent restart.
- R-051: budget numbers.
- The take cache makes plugin recall reproducible only per machine and per rate (R-059).

**Compute budget.**
- R-051: the stop never fires.
- R-053: a full retrain per notebook fix.
- R-062: the budget resets per run and excludes overhead.
- R-063: Drive quota mid-train.
- R-055: Kaggle sessions repeat work.
- T-P20 in cell (16) repeats the evaluation (test_evaluate.py:41): about 250 s of audio, minor.

---

## 4. Risk table (new risks)

| ID | Description | Lens | Severity | Likelihood | Root cause | Traces to | Proposed mitigation |
|---|---|---|---|---|---|---|---|
| R-051 | On Colab, cell (3) starts the budget heartbeat that writes `<run>/out/budget.json` on Drive. The freeze, env.json and params.json are also written under `<run>`. Drive is mounted only in cell (4), after the installs. Followed literally, the heartbeat thread dies with `FileNotFoundError` on its first write (`atomic_write_text` needs the directory), so `gpu_hours` never grows. The committed number is wrong, the train timeout uses `20 − 0`, and DR-13 never fires. If the implementer pre-creates directories instead, `drive.mount` refuses a non-empty mountpoint (UNVERIFIED). | technical; compute; integrity | Critical | medium | The R-020 reorder was not propagated to R-034, R-019 or R-013 writes; cells for some writes are unassigned (PK-58). | DECISIONS.md:503-507, :524-527, :541-546, :601-604; R-020; R-034; DR-13; A-015 | Define the cell order explicitly: (3) local paths and Kaggle restore only; (4) installs → mount → params.json guard → freeze and env.json → start the heartbeat. The heartbeat logs and re-raises into the main thread (check `thread.is_alive()` before each stage and stop if dead). Add a plausibility check to S-017 2a: `gpu_hours` ≥ the sum of `sessions[].gpu_hours` > 0 when `train` ran. |
| R-052 | On Colab, `<run>` is on Drive, so `cmake -B <run>/build-render` and `out/bin/singvst-render` live on Drive FUSE. Binaries there cannot be executed (no exec bit) and `libonnxruntime.so` cannot be `dlopen`ed, and FetchContent may fail to extract the ORT archive's library symlinks (all UNVERIFIED). Cell (4) only builds the binary, so the failure surfaces at cell (15) `evaluate`, after every GPU stage, which is what R-023 meant to prevent. | technical; operational; compute | High | medium | The per-run root (R-015) and the early build (R-023) were combined without researching Drive semantics (C-017 covers I/O only). | DECISIONS.md:508, :547-549, :572-574, :598-600; R-023; R-015; C-017 | Build in local `/content/build-render` (Kaggle: `/tmp/build-render`). The render-bin stage copies to local `out/bin` and also tars it to `<run>`. Cell (4) runs `singvst-render --check-voice tests/fixtures/voice-convert` right after the build (before GPU time). Add a claim spiking Drive exec and symlink behaviour, or document "no executables on Drive" as a rule in D-035. |
| R-053 | RUN semantics for `failed:` re-issues are contradictory. D-035 says "every G-004 issue has a run number RUN" with its own root, S-017 1a sets `RUN` = the issue number, and GATES.md says the implementer "re-issues G-004" after a `failed:`. Yet the limit "at most three per G-004 issue" only works if failed re-issues belong to the same issue. Literally, any fix after training starts a new run: a full retrain of up to 20 GPU-hours (a Kaggle weekly quota), and the three-attempt limit resets on every re-issue, so it never leads to `BLOCKED.md`. The alternative (keep RUN) produces R-054. | misinterpretation; compute | High | high | The run model of round 1 (R-013) was not reconciled with the `failed:` loop. | DECISIONS.md:511-515; PLAN.md:410-412, :420-421; GATES.md:26-27, :57-59 | Decide in D-035: a `failed:` re-issue keeps `RUN` (and the experiment) and only updates `EXPECTED_COMMIT`. A new RUN comes only from G-001 `retrain`. The three-attempt counter is per RUN. Combine with R-054's commit identity so that kept stages are re-validated. |
| R-054 | Multi-session provenance is incomplete. (a) Stage identity is `params.json` plus input files. The toolkit and RVC code commit and session-derived values (batch size chosen by GPU memory in cell (10a), `n_cpu`) are not part of it (PK-71), so a run that spans commits keeps outputs produced by older code. The report's `git_commit` names only the evaluating session, and S-017 2a accepts any set of impl-branch commits. (b) `env-freeze.txt` and `env.json` are overwritten every session, so the committed environment is the last session's, not the one that trained most epochs (PK-73). | reproducibility; integrity | Medium | medium | Provenance and stage identity were designed per session, not per stage. | DECISIONS.md:503-506, :525-531, :584-586, :588-600; PLAN.md:417-418; R-013; R-019 | Write the commit, batch size and `n_cpu` into a per-stage parameters file listed among that stage's inputs. Save `out/env/<session>.freeze.txt` and `.json` per session and list them in `training.json`. S-017 2a reports in GATE-G-001 which stage ran under which commit, and that table is committed. |
| R-055 | The Kaggle restore relies on unresearched platform behaviour (C-019 rests on two tier-3 sources): (i) limits on output file count and size, while the run holds thousands of RVC per-segment files plus GB-size G/D checkpoints and their `.bak` copies; (ii) whether a "Save & Run All" version that errors keeps `/kaggle/working`, which matters because the plan's own "start a new session" stop and the train timeout end versions with an exception; (iii) the mount path of notebook outputs. If outputs are not kept, every Kaggle session restarts and the fallback can never finish. `tools/notebook_dryrun.py` tests its own copy of the restore rule, not Kaggle. | invalid research assumption; operational; compute | High | medium | The copy-step lesson (L-20261016T000100Z) was applied at the layout level without researching the persistence layer. | DECISIONS.md:535-543, :605-607; PLAN.md:385-389; C-019; R-016 | Research and add claims for Kaggle output limits and errored-version semantics. End sessions gracefully: set a flag and skip the remaining cells instead of raising. Persist through one `tar` of `<run>`, `logs/<exp>` and `weights` (the D-016 archive rule) with a SHA-256 manifest, and restore by verifying it. |
| R-056 | The S-017 2a verification has unstable inputs and no exit. (i) The heartbeat thread keeps rewriting `budget.json` (session `end`, `gpu_hours`) after cell (17) has hashed and tarred it, so the copy the owner takes from Drive or the Kaggle output may not match the printed hash. (ii) Pasted text is not byte-stable (trailing newline, whitespace). (iii) "A failed check → ask the owner for the files again" has no attempt limit and no `BLOCKED.md` exit, so the implementer is stuck in a loop. | integrity; operational | High | medium | The R-036 checks were added without a stable artefact to check. | PLAN.md:413-419; DECISIONS.md:583, :601-604, :612-614; R-036 | Stop the heartbeat and write the final `budget.json` before cell (17). Cell (17) writes `upload.tar` plus `upload.sha256`, and the owner attaches the tar (pasting is allowed only for the hash file). After two mismatches, write `BLOCKED.md`. |
| R-057 | The R-035 pretrained-fallback detector never fires in practice. D-035 searches `train.log` for the Chinese literal "已加载生成器预训练模型", but train.py logs `i18n("已加载生成器预训练模型：%s")` (rvc_resume.txt:22). RVC's I18nAuto picks the locale and falls back to en_US, so Colab and Kaggle runtimes log "Loaded generator pretrained model: …" (see the Disclosure). Any resume where `torch.load(weights_only=False)` in the guard succeeds but RVC's own load raises (for example under torch 2.7.1's `weights_only=True` default; UNVERIFIED whether RVC passes the flag) restarts silently from the pretrained model. `training.json` `epochs_trained` (taken from the newest weight file name) and the G-001 epoch figure are then false. | technical; reproducibility; integrity | Critical | low | The spike verified the source literal, not the emitted text. The guard and RVC load checkpoints differently. | DECISIONS.md:563-570; C-061; research/spikes/premortem-r1/rvc_resume.txt:22, :246-265; R-035; PK-69 | Detect a restart by value, not by message: before train, read `torch.load(G)["iteration"]` = e. Fail the cell if the first epoch line logged in this session is below e, or if the log lacks the resume line in any locale (match both `已恢复判别器检查点` and its en_US translation). Run the guard with the same `weights_only` setting RVC uses. |
| R-058 | The take cache grows without bound on the system drive. Each completed render stores 56 + 4n bytes (46 MB for a 240-s take at 48 kHz). Edits, completed slider renders, sample-rate changes and multiple instances all add files, and D-010 forbids pruning. Over months this reaches tens of GB under `userApplicationDataDirectory`, and a full disk makes host saves fail (host-dependent). | scale; operational | Medium | high | "Never prune" was chosen to protect recall, with no size policy. | DECISIONS.md:288-291, :629-635; S-018 | Keep referenced takes. Each instance's state records the hashes it uses, written on `getStateInformation`. Evict unreferenced takes older than N days or beyond a size cap. Show the cache size in the status line. README documents the cap. |
| R-059 | Recall is still lost silently, in narrower conditions. The cache is per machine and per rate: moving a project or restoring a backup on another computer, deleting the cache, or a host sample-rate change (which re-keys the request) makes `cachedRender` miss without any message. The approved take is replaced by a new performance (C-040). A cached take also cannot play until the voice package is found and validated, because the render is blocked by "Load a voice" first. Copying the cache folder would work, but README does not say so, and the miss is silent. | operational; reproducibility | High | medium | PK-72 was applied to storage but not to detecting a miss. | DECISIONS.md:283-291, :285-287; take_cache.hpp:21-23; R-017; PK-72 | When a restored state's request misses the cache, show a warning ("approved take not found; a new performance was rendered") and keep the previous hash in state. Render at the stored `outputSampleRate` and let `renderBlock` resample on playback, so a rate change never re-keys the take. Allow cache playback without the voice when the take exists. README: "copy `sing-vst/takes` with your projects". |
| R-060 | Guide phrase length is unbounded. Phrases split only at SP ≥ 22 frames, so a long legato span (up to the whole 900-s take) is one acoustic run and one vocoder run. Vocoder activations scale with output samples (UNVERIFIED for TIGER's HiFiGAN; likely several GB for minutes of audio), and ORT's CPU arena retains its peak. The result is `bad_alloc` or an OS out-of-memory kill of the DAW. The take limits (T-070) do not bound a phrase. | scale; security (DoS); technical | High | low | R-027 bounded takes, not model runs. | DECISIONS.md:193-197, :242-243, :636-637; tests/cpp/test_limits.cpp:50-55; R-027; PK-43 | Cap a phrase at, for example, 30 s (split at the longest SP, else at a note boundary with 8-frame padding, as D-012 does). Run the vocoder in overlapped chunks as the converter does. Disable the ORT arena or shrink it after each run. Add a test with a long-phrase fixture under ASan. |
| R-061 | Some G-001 evidence numbers have no specified computation. (a) `spread.json` holds per-repeat values for `speaker_similarity` and `guide_similarity` but not `similarity_gain`, which is one of the five thresholds. GATES and S-017 require "indeterminate" per threshold metric, so the implementer must invent the interval (paired differences, or min − max) at the gate (PK-70). (b) `ceiling.json` is inline notebook code with no test, written into the evaluate stage's output directory after the stage. | numerical validity; integrity | Medium | high | spread.json is keyed by report keys, and the gain is a derived key. | eval/PROCEDURE.md:24-25; python/singvst_train/metrics.py:85-90; GATES.md:12-14; PLAN.md:423-424; DECISIONS.md:580-581 | D-017: the gain interval is the min and max of the paired per-repeat differences `speaker_similarity[r] − guide_similarity[r]`, computed by a toolkit function with a test. Move the ceiling into a toolkit function with a known-answer test and make it its own stage. |
| R-062 | A-015's "≤ 20 GPU-hours per voice" is enforced per run. `budget.json` lives under `<run>`, G-001 `retrain` is allowed while the *latest* run's `gpu_hours` < 20, and DR-13 uses the run's own total. Cumulative spend per voice is therefore unbounded. "GPU time" also excludes installs, the build, preprocess, prepare, the T-P19 check and idle time, while platform quotas charge the whole GPU session. | compute | Medium | medium | Per-run roots (R-015) split the budget ledger. | plan/ASSUMPTIONS.md:76-78; GATES.md:26-27; DECISIONS.md:532, :601-609 | Keep `<root>/budget-voice.json` summing all runs. Gate `retrain` on the per-voice total. Record session wall-clock with a GPU attached alongside stage time, and report both at G-001. |
| R-063 | Drive space per run is underestimated. Runs never delete each other's data. Each run adds `raw_wav/` (PCM_24), copies in `train/` and `heldout/`, `prepared/`, the RVC per-segment files, G/D checkpoints plus their new `.bak` copies, and 20 weight snapshots (several GB with 60 min of data; UNVERIFIED). The free-space check (3 × `raw/` + 2 GiB) does not count these, so a second run on a 15-GB free Drive can fill it mid-training. `torch.save` then fails and the session's progress is lost (the `.bak` dates from session start). | operational; compute | Medium | medium | Per-run retention (R-015), `.bak` (R-035) and the R-033 check were sized independently. | DECISIONS.md:513-517, :529-531, :563-566; R-033 | Estimate the need from the dataset (features, checkpoints ×2, snapshots) in cell (10a). After `pack`, a run may delete its own `raw_wav/`, `train/`, `prepared/` and checkpoints (keep weights and `out/`). Document "archive or delete old runs' `logs/<exp>`" in the stop message. |
| R-064 | The plugin threading specification is contradictory. D-022 lists only host bpm, sample rate and transport as atomics and puts "every other piece of state" behind the message mutex that processBlock never takes. But the capture state machine (`Armed` → `Capturing` → stop) is advanced inside processBlock. `arm(true)` "only resets [the FIFO] indices" from the message thread while the audio thread may still be writing, and `juce::AbstractFifo::reset` is not safe against a concurrent writer. No plugin code runs under TSan. | audio thread; misinterpretation | Medium | medium | R-026's mitigation named the FIFO but not the state machine or the reset handshake. | DECISIONS.md:268-273, :279-282, :293-295; ci.yml:103, :110; PK-38 | D-022: the capture state is a `std::atomic<int>` written by processBlock (the Armed→Capturing and Capturing→Stopped transitions) and by the message thread (arm, disarm) with compare-and-swap. Reset the FIFO only when the audio thread has acknowledged `Idle` through an atomic epoch. Add a plugin TSan job for T-055 and T-057. |
| R-065 | GATES.md was not updated for the round-1 changes. The G-004 evidence still gives a `blob/<impl>/` branch URL, while S-016 and S-017 require commit-pinned links. G-001 points renders at `out/eval/renders/` without the `<run>` root. The implementer writing GATE-G-004.md from GATES.md may give the branch link. This is a recurrence of L-20261015T180200Z. | misinterpretation | Low | medium | Cross-references were not regenerated after renames. | GATES.md:16, :44; PLAN.md:390-392, :410-412; R-029 | Update GATES.md to the pinned URLs and `<root>/run<RUN>/out/eval/renders/`. Add a generator check that GATES.md and PLAN.md name the same URL template. |
| R-066 | `tools/notebook_dryrun.py` cannot pass as written, and it tests the wrong code. S-016's Done when runs it with `python3.12` and it "loads each notebook with nbformat", but `tools/` scripts are standard-library only and nbformat exists only in the lock venv (requirements-lock.txt). It also copies `<tmp>/a` to `<tmp>/b` with its own implementation of the restore rule instead of executing the notebook's cell (3), so it cannot catch R-051 or R-055. | misinterpretation; past lessons | Low | high | PK-55 / ENVIRONMENT.md:50 conflicts with PLAN.md S-016. | PLAN.md:385-389, :395; plan/ENVIRONMENT.md:50; R-016 | Run it with `../venv-lock/bin/python`, or parse the `.ipynb` JSON with the standard library. Exec the notebook's own cell (3) with `/kaggle` paths remapped to the temporary directory. |
| R-067 | A take that renderTake accepts (ending ≤ 900 s after its first note) can produce up to about 10 ms more audio: frame rounding gives `floor(lastEnd·fr + 0.5)` guide frames, and the converter uses `T·hop`. `loadTake` rejects `n > 900 × sampleRate`. Such takes are stored but never loadable, so their recall is silently lost. | technical | Low | low | The two limits were written independently. | DECISIONS.md:125-127, :207-213, :242-243, :632-634; take_cache.hpp:17-19 | `loadTake` accepts `n ≤ (900 + 1) × sampleRate`, or renderTake trims to the limit. Add a boundary case to T-067 through the amendment process. |

---

COUNTS (new + inadequately mitigated round-1 risks): Critical=3 High=6 Medium=6 Low=3

*The count covers new risks R-051…R-067 (Critical 2, High 6, Medium 6, Low 3) plus R-034, the only round-1 risk judged inadequate, at its register severity (Critical). Round-1 risks judged "partially" are not counted again; their new failure modes have the IDs above.*
