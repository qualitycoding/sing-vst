# Pre-mortem: round 3 (Phase 4)

**Scope.** I reviewed branch `gen-20261004T095012Z-singing-voice-vst-pitch-lyrics` (HEAD `ee13c20`) in read-only mode. I changed, built and ran nothing, and used no network. Files read: HANDOFF.md, plan/PLAN.md, plan/DECISIONS.md, plan/GATES.md, plan/ASSUMPTIONS.md, plan/ENVIRONMENT.md, plan/PROFILE.md, plan/PROTOCOL_EXCERPTS.md, eval/PROCEDURE.md, research/claims.json (62 claims), research/PRIOR_KNOWLEDGE.md (PK-01…PK-75), research/spikes/premortem-r1/rvc_resume.txt, research/spikes/premortem-r2/*, research/spikes/rvc-resume/output.txt, premortem/round-2.md, premortem/RISK_REGISTER.md, tests/cpp/test_plugin.cpp, tests/cpp/test_engine.cpp (test names), tests/python/test_notebooks.py, test_pipeline.py and test_evaluate.py, core/include/singvst/{engine,render,playback,take_cache,params,synthesis}.hpp, plugin/PluginProcessor.h, python/singvst_train/{pipeline,rvc_files}.py, CMakeLists.txt, cmake/Dependencies.cmake, cli/CMakeLists.txt and core/CMakeLists.txt.

Severity follows Global Rule 4 for the `software` and `computational` profiles (plan/PROTOCOL_EXCERPTS.md:19-35). Anything that could not be checked offline is marked UNVERIFIED.

**Commit note.** T-P22 resolves every `R-###` cited in `premortem/*.md` against premortem/RISK_REGISTER.md. This file must be committed together with register rows R-068…R-081.

**PK-74 re-derivation (basis for sections 2–4).** I rebuilt each procedure step by step from the plan text.

- **Notebook session (Colab):**
  - (1) `nvidia-smi`, session start → (2) consent → (2a) parameters → (3) paths and `make_stages`.
  - (4a) clone and commit check → (4b) venv and installs → (4c) GPU arch check → (4d) **mount** → (4e) `<run>/` dirs, symlinks, params.json, freeze/env files, `sessions[]` append, **heartbeat start** → (4f) local build and `--check-voice`.
  - (5) assets → (6) T-P19 and Whisper check → (7)–(15) `run_stages` slices → (16) T-P20 → (17) final writes and tars.
  - Sources: DECISIONS.md:572-631.
- **Notebook session (Kaggle):** the same, with the `state.tar` restore inside (3) (DECISIONS.md:576-578) and `state.tar` creation, followed by deletion of the untarred copies, at the end of (17) (:629-631).
- **Plugin restore:** state parse → cache lookup by the restored request → publish a hit → voice load → `submit` (D-010, DECISIONS.md:303-307, :313-315).
- **Capture:** message CAS Idle→Armed → audio Armed→Capturing → audio Capturing→Stopping → timer drains the FIFO, finishes, resets the FIFO and stores Idle (D-022, DECISIONS.md:274-279).

---

## 1. Simulation

*Values are illustrative, not measured, unless a source is cited.*

### 1a. [software] Six months after delivery: catastrophic failure

| When | What the owner sees | Traced root cause |
|---|---|---|
| Merge + 0 | The owner builds the plugin (ENVIRONMENT.md:71-83). Takes render at the state's `outputSampleRate` (48 kHz) and are cached (D-038). | as specified |
| + 1 month | The owner switches the audio interface to 44.1 kHz. D-010 says "the worker resamples the stored take … and publishes that copy" (DECISIONS.md:294-296). The request and its hash are unchanged, so `Renderer::submit` short-circuits ("a request whose phraseHash equals the current Ready take's is not re-rendered", render.hpp:57-59; D-013 :241-242). The only path left to the worker never runs. As specified, renderBlock reads the 48-kHz take by nearest sample (playback.hpp:106-108). The vocals now carry zero-order-hold aliasing, which goes unnoticed on monitors. | R-072 |
| + 2 months | A 40-s sustained ambient line exceeds the 2584-frame phrase cap (DECISIONS.md:196-197). The cap says to split "at the note boundary nearest its middle", but `GuideEngine::render` receives only phoneme spans (engine.hpp:27; synthesis.hpp:10-14). The implementer had guessed "the span boundary nearest the middle", which falls inside the vowel. Both halves get 8 SP frames of padding, so the vowel has an audible seam. The owner approves the take with the seam, and the cache now preserves it bit for bit. | R-077 |
| + 5 months | The owner disarms capture during the same block in which the transport starts. The message thread's CAS Armed→Idle succeeds, but the audio thread had already read `Armed`. It does a plain store to `Capturing`, because D-022 prescribes CAS only for the message thread (:276-277). The capture proceeds, and on stop the timer replaces the stored notes of an approved part (D-010 :290-291). | R-078 |
| + 6 months, **catastrophe** | The replaced notes trigger a new render, which is a new performance (C-040). The state now holds the new notes' hash. The approved take is still in the cache, but no state references it, so no restore can reach it. The miss warning fires only on restore (:305-307), not after a capture. The owner discovers the loss after mastering. | R-078, with R-059 partially mitigated |

**Root-cause summary.** The round-2 recall fixes (resample on rate change, cache-first restore) and the phrase cap were written against behaviour that the frozen interfaces cannot express: an unchanged request is never re-run, and the engine sees no notes. The capture handshake made only one side's transitions atomic.

### 1b. [computational] Twelve months after completion: a claimed result is false

| When | Event | Traced root cause |
|---|---|---|
| G-004 run 1, Kaggle (Colab quota exhausted), version 1 | Train starts from pretrained weights. At 9.5 h the train timeout fires. The implementer implemented the timeout as `subprocess.run(argv, timeout=t)`, because the plan does not say how. That kills only the launcher. RVC's training worker, a `run(rank, …)` child process (rvc_resume.txt:646 `rank == 0`; the `mp.Process` launcher itself is UNVERIFIED from the clone), keeps training. Cell (17) tars `logs/` while the worker overwrites `G_2333333.pth`. | R-070 |
| Version 2 | The checkpoint guard finds the G checkpoint truncated. There is no `.bak`, because version 1 started without a checkpoint. The cell "stops" (DECISIONS.md:603-604). That stop is not one of the three `STOP` conditions (:561), so the cell raises. The version errors, cell (17) never runs and no `state.tar` is written. | R-069 |
| Version 3 | The owner deletes `logs/<exp>` as the message says. When re-running, they forget to attach version 2's output (which holds no `state.tar` anyway). Restore finds none and goes to "first session" (:577). `budget.json` and `budget-voice.json` start again at 0 h. | R-068 |
| Versions 3–5 | Training completes. `budget.json` says 14.2 h. About 9.5 GPU-hours of version 1 and the errored version 2 are absent from every ledger. | R-068, R-034 (partially) |
| S-017 | Every 2a check passes: hashes, Σ sessions, `train` in `stages_run`, commits on the impl branch (PLAN.md:420-427). T-P20's outcome was printed in cell (16) and never transferred (DECISIONS.md:663-666). S-019 records "T-P20 from S-017's record" (PLAN.md:496), but no such record exists. | R-071 |
| + 12 months | A re-run from the same data and notebook is audited against Kaggle's usage history. The SC-9 claim "within the 20-h budget" (ASSUMPTIONS.md:64) and the committed `gpu_hours` turn out false, and the "lower bound (5-minute heartbeat)" label (GATES.md:15) understates the error by hours. T-P20 cannot be shown to have passed. | R-068, R-071 |

**Root-cause summary.** Kaggle persistence depends on cell (17) running. Only three stop paths guarantee that it runs, and a missing input is treated as a legitimate first session. The training process's lifetime is not bounded by the stage that starts it.

---

## 2. Round-2 mitigation audit

| Risk | Verdict | Reason (file:line) |
|---|---|---|
| R-034 | partially | **Colab:** fixed. The heartbeat starts after the mount (DECISIONS.md:580-583), stores its exceptions and is checked before every stage (:651-655). **Kaggle:** the heartbeat's writes persist only through `state.tar` written in cell (17) (:629-631). A hard kill (12-h limit, kernel OOM) or any exception before (17) loses the whole session's accounting, not 5 minutes. The GATES.md:15 label is then false → R-068, R-069. **Colab:** a second heartbeat thread from re-running cells survives (R-074). |
| R-051 | adequate | The cell (4) order (a)–(f) puts the mount at (d) before every Drive write at (e) (:579-583). The text "no cell writes under /content/drive before this point" (:581) is explicit. Liveness is checked before every stage and in (17) (:654-655). The S-017 2a plausibility check is in place (PLAN.md:422). |
| R-052 | adequate | `<LOCAL>` is local disk (:533-535). The build and `--check-voice` run on the fixture at (4f) before GPU stages (:584-588). The render-bin `cp` file names match what the build produces: `libonnxruntime.so.1.31.0`, `cmudict.dict` and `onnxruntime-LICENSE.txt` (cmake/Dependencies.cmake:29, :50-55; DECISIONS.md:613-615). Residual: the hosted compiler is unpinned (R-023, Medium, open). The (13) premise "because the binary's bytes differ, evaluate" re-runs (:616-617) holds only across commits (git_commit is compiled in). It is harmless. |
| R-053 | **inadequate** | D-035 now says a `failed:` re-issue keeps `RUN` (:535-536), and GATES.md:58-60 agrees. But PLAN.md:416 (S-017 1a) still says "`RUN` = the issue number". An implementer following the step text gives a `failed:` re-issue a new `RUN`, which is a full retrain. This is the original failure mode (L-20261015T180200Z recurrence). Severity High, as registered. |
| R-055 | partially | The graceful `STOP` and one `state.tar` with SHA-256 address the 500-item limit (C-064, single-source). But only "9.5 h, budget, train timeout" set `STOP` (:561). Every other "stop" — (4a)/(4c)/(6)/(7) checks, the checkpoint guard (:604), the restart detector (:610), parity (:612-613), a dead heartbeat (:654-655) — and every unexpected exception errors the version before (17) → R-069. A missing input silently becomes "first session" (:577) → R-068. After a G-001 retrain, the restored earlier `run<k>/` and the extracted `voicebank/` are left loose in the output → R-073. The dry run's fake `sh` never exercises a stop path (PLAN.md:388-394). |
| R-056 | adequate | The heartbeat is stopped and `budget.json` written before the tars (:627-629). One attached `upload-run<RUN>.tar` is used, and only its hash line is pasted (:663-666). Two mismatches → `BLOCKED.md`, and a failed check is asked again at most twice (PLAN.md:420-426). Residual: T-P20's result is not in the tar (R-071). |
| R-057 | partially | The value check (`iteration` ≥ `e0`) plus both log strings (:607-610; C-063) is sound. The guard loads exactly as RVC does (C-063: no `weights_only` argument). But detection only stops the cell. RVC has already overwritten `G_2333333.pth` with the restarted model, and the next session's guard copies that model over the good `.bak` (:604-605) → R-076. |
| R-059 | partially | Cache-first restore and the miss warning are specified (D-010 :303-307). The resample-on-rate-change cannot be reached through the frozen `Renderer`, because an unchanged request is short-circuited (render.hpp:57-59). The plan does not say which take is resampled or what initially sets `outputSampleRate` → R-072. A notes replacement by capture loses recall with no warning (R-078). |
| R-060 | partially | The arena is disabled (D-002 :27-28) and a 30-s cap is stated (D-012 :196-197). But the cap's fallback "note boundary nearest its middle" uses information `GuideEngine::render` does not receive (engine.hpp:27; synthesis.hpp:10-14). The assignment of a split SP span's frames is unspecified, and no test covers the cap (test_engine.cpp T-042…T-047; S-008 adds only the external-data test) → R-077. |

---

## 3. Lenses

**Technical correctness.**
- R-070: the train timeout does not end training.
- R-072: the rate-change resample is unreachable.
- R-077: the phrase cap needs notes the engine does not have.
- R-078: capture transitions.
- R-075: budget stop versus DR-13.
- R-076: restart recovery.
- Checked and sound:
  - `run_stages` (pipeline.py:24-31) never deletes `logs/<exp>` (PK-62 holds).
  - `latest_checkpoint_path` sorts by every digit in the full path (rvc-resume/output.txt:222-225). The prefix is shared and `.pth.bak` does not match `G_*.pth`, so `.bak` copies are not picked up, provided they are named `<file>.pth.bak`, not `*.bak.pth` (D-035 says only "copied to `.bak`"; noted, no ID).

**Dependency and supply-chain drift.**
- The notebook compiler is unpinned. CI builds with GCC 13.3 only (ENVIRONMENT.md:13). The R-023 "GCC 11 floor" from round 1 never reached D-033 (DECISIONS.md:472-482), so a hosted image's older GCC fails at (4f): early, but blocking (R-023 open, Medium; not re-raised).
- RVC cu128 ranges re-resolve every session; per-session freezes now record them (R-054).
- No new drift beyond the register.

**Invalid research assumptions.**
- C-019 (single-source, tier 3) and C-064 (single-source) carry R-068, R-069 and R-073. The behaviour of more than 500 output items is unknown (truncate? drop? fail?), as are errored-version semantics and whether a notebook can take its own output as input. All UNVERIFIED.
- C-010 (single-source): covered by G-005.
- C-017, C-018 (corroborated): unchanged.
- No claim covers RVC's training process structure (launcher plus worker); R-070 rests on the `rank` evidence in rvc_resume.txt:646 only.
- C-061 and C-063 are adequate as used.

**Implementer misinterpretation.**
- PLAN.md:416 versus D-035 on `RUN` (R-053, inadequate).
- Which "stop" sets `STOP` (R-069).
- "Budget" listed as a STOP condition versus DR-13's "export it, evaluate" (R-075).
- "The worker resamples" (R-072).
- "Note boundary" (R-077).
- Audio-side CAS, and D-010:308-309 "`arm(true)` only resets its indices" versus D-022:278-279 "the timer … resets the FIFO indices" (R-078).
- Executing fragments of cells (3) and (17) in the dry run (R-079).

**Integrity (Rule 9).**
- R-068: a silently reset ledger produces a committed `gpu_hours` that is wrong by whole sessions.
- R-071: S-019 claims T-P20 passed with no record.
- R-080: `training.json` `stage_commits` never includes the evaluate stage.
- Positives: files are never edited; gate history is kept with `git mv` (PLAN.md:428-431); the verdict is recomputed (PLAN.md:423).

**Past lessons (PK).**
- PK-74 applied here found R-069, R-070, R-073, R-074 and R-076.
- PK-58 recurrence: the "stop" semantics and the timeout mechanism are unspecified notebook interfaces (R-069, R-070).
- L-20261015T180200Z recurrence: stale PLAN.md:416 (R-053).
- PK-63: S-019's Done-when needs a T-P20 record that no step produces (R-071).
- PK-72: approved takes become unreachable after a capture replace (R-078).
- PK-75 applied correctly in C-063.
- PK-71: the batch size is still outside stage identity (R-054, open).

**Scale and performance.**
- On Kaggle, `state.tar` is written while the untarred copies still exist, roughly doubling `/kaggle/working` usage: G/D checkpoints with `.bak`, 20 weight snapshots, features, the out tar and the upload tar. The cell (10a) check (:556-558) does not count this (UNVERIFIED size; folded into R-073).
- A cache-first restore reads up to 173 MB per instance synchronously in `setStateInformation` under the message mutex (D-022 :281-282; D-038 size 56 + 4n). This slows project load. Medium-free; noted.
- If the implementer does a rate-change resample on the message thread, a 900-s take freezes the UI for seconds: about 40 M output samples × about 147 taps for 48 k→44.1 k (D-011). This is part of R-072.

**Security.**
- Nothing new meets the bar.
- Kaggle restore extracts a tar from `/kaggle/input/*` (:576-578). Extraction should use `tarfile` `filter="data"` so a hostile attached input cannot write outside `/kaggle/working`. Exploitation needs the owner to attach third-party data. Low, no ID.
- With no `weights_only` argument, torch 2.7.1's default `weights_only=True` makes the guard's `torch.load` safe.

**Operational realities.**
- R-068: a forgotten Kaggle input.
- R-073: Kaggle retrain leftovers.
- R-074: re-running Colab cells in the same runtime.
- R-081: G-001 tells a Kaggle owner to listen "on their Drive" (GATES.md:16), but on Kaggle the renders exist only inside tars in the version output.

**Audio thread (PK-38).**
- R-078: capture CAS.
- `TakeSlot` is unchanged and sound (round 2).
- The cache-first restore publishes through `TakeSlot::publish` (writer mutex), not on the audio thread. That is sound.

**Numerical validity.**
- R-072: nearest-sample playback when the resample never happens.
- R-077: seams at forced phrase splits.
- T-P20 in cell (16) runs a second, independent evaluation into `tmp_path` (test_evaluate.py:41), whose values differ from cell (15)'s because of guide noise. That is acceptable only because neither is asserted, but it is another reason R-071 needs the T-P20 record itself.

**Reproducibility.**
- R-070: a torn checkpoint in `state.tar`.
- R-076: `.bak` overwrite.
- R-080: stage-commit table incomplete.
- R-054 (open).

**Compute budget.**
- R-068: ledger reset.
- R-069: an errored Kaggle version loses the session.
- R-070: an orphaned trainer consumes GPU uncounted and can make `evaluate` (Whisper on CUDA) run out of memory.
- R-075: the stale 5-minute heartbeat value decides "budget reached". Export, evaluate and cell (16) add GPU time after the 20-h stop.
- R-053: a full retrain per notebook fix.

---

## 4. Risk table (new risks)

| ID | Description | Lens | Severity | Likelihood | Root cause | Traces to | Proposed mitigation |
|---|---|---|---|---|---|---|---|
| R-068 | **Kaggle restore treats a missing input as a legitimate first session.** `glob("/kaggle/input/*/state.tar")` with no match → "first session" (DECISIONS.md:577). This happens when the owner forgets to attach the previous version's output, or when the previous version wrote no `state.tar` (R-069). Training then restarts from the pretrained model, and `budget.json` / `budget-voice.json` restart at 0. Nothing flags it. S-017 2a's checks (PLAN.md:420-427) all pass on the post-reset ledger. The committed per-voice `gpu_hours`, labelled "lower bound (5-minute heartbeat)" (GATES.md:15), is silently wrong by whole sessions, and A-015 can be exceeded. | compute; integrity; operational | Critical | low | The restore distinguishes "no state" from "first session" only by absence. | DECISIONS.md:576-578, :649-653; GATES.md:15; A-015; R-034; R-062; C-064 | Add Parameters-cell value `NEW_RUN = True` for the first session of a run (GATE-G-004.md says to set it to `False` afterwards). With `NEW_RUN = False` and no `state.tar` → stop (graceful `STOP`) with "attach the previous version's output". With `NEW_RUN = True` and `run<RUN>/` already present in a restored tar → stop. Record `NEW_RUN` and the restored tar's SHA-256 in `sessions[]`. S-017 2a checks that every session after the first names the previous session's tar hash. |
| R-069 | **Only three stop conditions use `STOP`.** Every other "stop" in D-035 raises an error in Save & Run All: commit check, GPU arch, T-P19/Whisper, split size, checkpoint guard, restart detector, parity, dead heartbeat. So does any unexpected exception (OOM, download failure, a bug). The Kaggle version then never runs cell (17), so no `state.tar` is written. Whether an errored version keeps `/kaggle/working` is unresearched (C-064). If not, every Kaggle session that fails after training loses up to 9.5 GPU-hours of checkpoints, and the next restore falls into R-068. The dry run cannot catch this: its fake `sh` never fails (PLAN.md:388-394). | technical; compute; operational | High | medium | The R-055 mitigation listed `STOP` triggers instead of making persistence unconditional. | DECISIONS.md:561-565, :579-588, :594-597, :603-613, :654-655; C-064; R-055 | Make every "stop" in D-035 a `STOP` with a message. Wrap cells (5)–(16) so any exception sets `STOP` and is printed. On Kaggle, write `state.tar` in a `try/finally` path of cell (17) that runs even after an error (or `%%capture`-style guard per cell). Add a dry-run case where one stage's `sh` raises, and assert `state.tar` is still written and restorable. |
| R-070 | **The train timeout does not end training.** D-035 gives the timeout (:657-658) but not how training is terminated. RVC's `train.py` runs training in a per-rank worker (`run(rank, …)`, rvc_resume.txt:646; `mp.Process` launcher UNVERIFIED from the clone). `subprocess.run(timeout=…)` kills only the launcher, so the worker keeps training on the GPU. Consequences: <br>• Cell (17)'s Kaggle `state.tar` captures a `G_2333333.pth` being rewritten. <br>• On the budget path, export and evaluate run beside it (Whisper GPU OOM → "invalid" report). <br>• Its GPU time is uncounted. <br>• At `total_epoch` it can overwrite the `<exp>.pth` copied by the budget stop after export. | technical; compute; reproducibility | High | medium | The interface for stopping a third-party trainer was not specified (PK-58). | DECISIONS.md:561, :601-611, :657-660; C-061; rvc_resume.txt:646-662; R-035 | D-035: start `train.py` with `start_new_session=True`. On timeout, send `SIGTERM` to the process group, wait 60 s, then `SIGKILL` the group, and assert with `nvidia-smi --query-compute-apps` that no process holds the GPU before the next stage. Spike RVC 81eed5e `train.py` `main()` for its process structure (new claim). |
| R-071 | **T-P20's outcome is never transferred.** Cell (16) runs `pytest -m voice` in the notebook (:626-627). The upload tar (:663-666) and the G-004 response (GATES.md:55-57) carry no test result. S-019's Done-when needs "T-P20 from S-017's record" (PLAN.md:496), so the implementer must either assert a pass without evidence (Rule 9) or guess. T-P20 also fails by design on an "invalid" report (eval/PROCEDURE.md:37-38), and a `!pytest` failure does not stop the notebook. | integrity; misinterpretation | High | high | The upload was designed for result files, not test records (PK-63). | PLAN.md:419, :436, :496; DECISIONS.md:626-627, :663-666; GATES.md:55-57; tests/python/test_evaluate.py:34-62 | Cell (16) runs `python -m pytest -m voice --junitxml=out/eval/t-p20.xml`; the XML goes into the upload tar. S-017 2a checks it reports 1 test, 0 failures, 0 errors, and GATE-G-001.md quotes it. A failure sets `STOP` before the upload and is reported as `failed: 16`. |
| R-072 | **The rate-change resample (R-059) has no reachable implementation.** D-010 says "the worker resamples the stored take to the host rate and publishes that copy, while the request … keeps the state's `outputSampleRate`" (:294-296). But the `Renderer`'s worker runs only `RenderFn(request)`, and an identical request is short-circuited (render.hpp:57-59; D-013 :241-242). The plan also does not say: <br>• which take is resampled (the cached original, or an already resampled copy, which compounds errors); <br>• what first sets `outputSampleRate` in the state; <br>• which thread does the work. <br>The implementer must guess. If nothing resamples, renderBlock plays the take by nearest sample (playback.hpp:106-108), an audible aliasing defect. A message-thread resample of a long take freezes the UI for seconds. | technical; audio thread; misinterpretation | High | high | A behaviour was specified against a frozen interface without checking that interface's semantics (PK-74). | DECISIONS.md:294-296, :241-242; render.hpp:57-66; playback.hpp:93-108, :112-121; D-011; R-059 | D-010: (1) `outputSampleRate` = 48000 always (state default); (2) the plugin owns a second, private worker (one `std::thread`, newest-wins) that resamples `renderer.latest()` or the cache hit from its original rate to the current host rate whenever either changes, and publishes the copy; (3) never resample a resampled copy. Add a plugin test with `prepareToPlay(44100)` and a 48-kHz take that checks the published take's `sampleRate` (amendment). |
| R-073 | **Kaggle outputs leak loose files that `state.tar` does not cover.** <br>• `state.tar` holds only `run<RUN>/` (:629-631). After a G-001 retrain the restored `run<k>/` of earlier runs stays untarred: thousands of segment, render and state files that are never deleted. Run 1's package also drops out of every later `state.tar`, contradicting "earlier runs' voice packages stay where they are" (:538-539). <br>• `<root>/voicebank/pack/` and `tiger/` (cell (14), :617-618) are never tarred or deleted. <br>Either can push the output past the 500-item limit (C-064, single-source), whose effect on `state.tar` is unknown. Writing the tar beside the originals also doubles disk use, which cell (10a) does not count. | operational; compute | Medium | low | The tar list was derived from one run's layout. | DECISIONS.md:538-539, :556-558, :576-578, :617-618, :629-631; C-064; R-055; R-063 | `state.tar` holds every `run*/` directory. Cell (17) deletes `voicebank/` (re-extracted from `assets-archive/` each session), and before finishing asserts that `/kaggle/working` holds ≤ 20 items. Cell (10a) adds the size of the tar inputs to the Kaggle free-space requirement. |
| R-074 | **A second heartbeat thread survives re-running cells in one Colab runtime.** "Run all" after an error, or re-running from cell (1), starts a new heartbeat at (4e). The old thread keeps writing its in-memory `budget.json` / `budget-voice.json`, overwriting the new session's `sessions[]` entry and totals, including after cell (17) has stopped only the new thread. The liveness check sees only the current handle (:654-655). Drive's ledgers then lose or double sessions. A-015 enforcement and later runs read the corrupted `budget-voice.json`. | compute; integrity | Medium | medium | The heartbeat is a per-cell object, not a per-process singleton. | DECISIONS.md:582-583, :649-655, :627-628; R-034; R-051 | Keep the heartbeat in a module-level singleton. (4e) stops and joins any existing one before starting. The heartbeat re-reads the file and updates only its own session's entry, keyed by `<session>`, under `atomic_write_text`. |
| R-075 | **Budget-stop semantics are contradictory.** D-035 lists "budget" among the conditions that set `STOP` (:561), so export and evaluate are skipped. DR-13 and :658-660 say the train stage completes and the run continues to export and evaluate. "Reaches 20" is not tied to a value either: the heartbeat's file is up to 5 min stale. A budget-bound timeout read at 19.92 h is taken as a session timeout (`STOP`), and the next session spends its setup to train for about 5 minutes. Export, evaluate and cell (16) then add GPU time beyond 20 h. | compute; misinterpretation | Medium | medium | Two round-2 edits (STOP, per-voice budget) were not reconciled with DR-13. | DECISIONS.md:561, :649-660; DR-13; A-015; R-062 | D-035: remove "budget" from the `STOP` list. Decide the branch by which term of `min()` was binding, computed by the main thread's exact counter, not the file. Reserve a fixed margin (for example 1 h) for export, evaluate and T-P20 in the train timeout (`20 − 1 − gpu_hours`). |
| R-076 | **Detecting a pretrained restart destroys the good checkpoint at the next session.** When the restart detector fires (:607-610), RVC has already overwritten `G_/D_2333333.pth` with the restarted model, which loads cleanly. The cell only stops. The next session's guard loads those files, sets `e0` from them and copies them over the good `.bak` (:604-605), so progress before the restart is lost. GPU time is spent again, and with a budget stop the reported `epochs_trained` mixes two lineages (`latest_weights` picks the highest `_e<N>`, rvc_files.py:71-73). | reproducibility; compute | Medium | low | The detector was added without a recovery path. | DECISIONS.md:601-611; rvc_files.py:71-73; C-061; C-063; R-057 | On detection, restore G/D from `.bak` (still holding `e0`) before stopping, and write `logs/<exp>/RESTART_DETECTED`. The guard refuses to overwrite `.bak` when that marker exists. The message tells the owner to report `failed: 11`. |
| R-077 | **The 30-s phrase cap cannot be computed as written.** "Else at the note boundary nearest its middle" (:196-197) needs note boundaries, but `GuideEngine::render` receives only phoneme spans (engine.hpp:27; synthesis.hpp:10-14). The plan does not say which sub-phrase receives an internal SP span shorter than 22 frames, and the output length must stay exactly `sum(durations)·512`. No test covers the cap. Any guess passes CI. A split inside a legato line is rendered as two padded phrases, an audible seam that the cache then preserves. | technical; numerical validity; misinterpretation | Medium | medium | The cap was specified at the take level but implemented at the engine interface. | DECISIONS.md:192-199; engine.hpp:21-28; synthesis.hpp:10-14; R-060 | D-012: split at the span boundary nearest the middle whose next span starts with a consonant (else any span boundary). An internal SP span belongs whole to the earlier part. S-008 adds a unit test with a 3000-frame phrase that checks two model runs, exact output length and zeros only at the ≥ 22-frame SP spans. README `## Limits and care` says long legato lines are split. |
| R-078 | **The capture handshake is only half atomic.** D-022 gives CAS to the message thread only (:276-277). processBlock's Armed→Capturing and Capturing→Stopping are not required to be CAS, so a concurrent disarm is lost. The capture then replaces the stored notes the user meant to keep (D-010 :290-291). That triggers a new performance, and the state no longer references the approved cached take: recall is lost silently (the miss warning is restore-only, :305-307). Disarm during `Capturing` has no defined transition. D-010:308-309 ("`arm(true)` only resets its indices") conflicts with D-022:278-279 ("the timer … resets the FIFO indices"). | audio thread; misinterpretation | Medium | low | The R-064 fix specified one side of the state machine. | DECISIONS.md:274-279, :288-291, :305-311; PluginProcessor.h:15-17; T-057; PK-38; PK-72 | D-022: every transition is a CAS on both threads. Disarm from `Capturing` CASes to a new internal `Cancelling` value that the timer drains and discards (stored notes kept). Delete the D-010 "`arm(true)` only resets" clause. A notes replacement by capture adds the warning "stored notes replaced; previous take kept in the cache". |
| R-079 | **The S-016 dry run must execute fragments of cells (3) and (17) that the plan does not factor out.** Cell (3) also sets absolute `/content` or `/kaggle` paths and `<LOCAL>`, which the dry run does not remap (only `/kaggle/input` and `/kaggle/working`). Cell (17) also stops the heartbeat and writes budget and upload tars. The stage inputs `<LOCAL>/build-render/cli/singvst-render` and `<root>/voicebank/` come from (4f) and (14), not from any stage. The implementer must guess the factoring. | misinterpretation | Low | high | R-066's fix named code to execute without an interface for it (PK-58). | PLAN.md:388-394; DECISIONS.md:574-578, :584-588, :617-618, :627-631 | D-035: cell (3) defines `PATHS` from one `BASE` mapping, plus `pack_state(dst)` and `restore_state(src)` functions. Cells (3)/(17) call them. The dry run calls the same functions with `BASE` remapped and pre-creates the two non-stage inputs. |
| R-080 | **`training.json` never records the evaluate stage.** `training.json` (`stage_commits`, `env_files`) is written by the pack stage (14), which always runs before evaluate (15) (:618-622). Its `stage_commits` therefore never includes evaluate, and a later evaluate-only session's env files are missing. The GATE-G-001 table copied from it (PLAN.md:426-427) is incomplete. `out/env/` and the report provenance hold the missing data. | reproducibility; integrity | Low | high | The summary is written mid-pipeline. | DECISIONS.md:618-622; PLAN.md:426-427; R-054 | Cell (17) (non-`STOP`) rewrites `out/stage_commits.json` from `<run>/state/commits.json` and includes it in the upload tar. S-017 builds the table from it. |
| R-081 | **G-001 assumes the renders are on Drive.** It tells the owner to listen to renders "on the owner's Drive (`<root>/run<RUN>/out/eval/renders/`)" and to render `out/eval/phrases/p<k>.mid` (GATES.md:16-21). On Kaggle these exist only inside the version's out tar and `state.tar`, and the untarred copies are deleted (:629-631). | operational | Low | medium | G-001 text written for Colab only. | GATES.md:16-21; DECISIONS.md:629-631 | GATE-G-001.md gives the Kaggle path: download the version output and extract the out tar. |

---

COUNTS (new + inadequately mitigated round-2 risks): Critical=1 High=5 Medium=6 Low=3

*The count covers the new risks R-068…R-081 (Critical 1, High 4, Medium 6, Low 3) plus R-053, the only round-2 risk judged inadequate, at its register severity (High). Round-2 risks judged "partially" (R-034, R-055, R-057, R-059, R-060) are not counted again; their new failure modes have the IDs above.*
