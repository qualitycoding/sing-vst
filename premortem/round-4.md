# Pre-mortem: round 4 (Phase 4)

**Scope.** I reviewed branch `gen-20261004T095012Z-singing-voice-vst-pitch-lyrics` (HEAD `b35d8da`) read-only. I changed, built and ran nothing, and used no network. I read these files:
- HANDOFF.md
- plan/PLAN.md, DECISIONS.md, GATES.md, ASSUMPTIONS.md, PROTOCOL_EXCERPTS.md (Rule 4, Rule 9)
- eval/PROCEDURE.md
- research/claims.json (63 claims: 57 verified, 3 corroborated, 3 single-source)
- research/PRIOR_KNOWLEDGE.md (PK-01…PK-76)
- research/spikes/premortem-r2/*
- premortem/round-3.md and premortem/RISK_REGISTER.md
- tests/cpp/test_plugin.cpp and test_resample_take.cpp; tests/cpp/CMakeLists.txt
- tests/python/test_notebooks.py, test_evaluate.py, conftest.py; pytest.ini
- core/include/singvst/{take_cache,render,playback}.hpp; plugin/PluginProcessor.h
- python/singvst_train/{pipeline,rvc_files,evaluate}.py
- .github/workflows/ci.yml

`sha256sum -c tests/FROZEN_MANIFEST.sha256` reports OK for all 93 entries. Severity follows Global Rule 4 for the `software` and `computational` profiles. Anything that could not be checked offline is marked UNVERIFIED.

**Commit note.** T-P22 resolves every `R-###` cited in `premortem/*.md` against the register. This file must be committed together with register rows R-082…R-094.

**PK-74 / PK-76 re-derivation (basis for sections 2–4).** I rebuilt each changed procedure, step by step, from the current text.

- **Kaggle session:**
  1. (1) `nvidia-smi` → (2) consent → (2a) parameters.
  2. (3) paths, helpers, `make_stages`, `pack_state`, `restore_state`. Then the `RESUME` check, the SHA check, and `restore_state` extracts `state.tar` into `/kaggle/working`. **This is the first write** (DECISIONS.md:620-627).
  3. (4a)–(4f), each of which "may raise" (:603-604). Among them, (4e) appends `sessions[]` (with `restored_from`) and starts the heartbeat (:631-632).
  4. (5)–(16) run inside `guarded` (:597-601).
  5. (17): `try { normal branch: final budget write, out tar, upload tar, print SHA | STOP: print reason } finally { stop heartbeat, write budget files, pack_state → state.tar + .sha256, "also recorded as state_tar_sha256 in the session's sessions[] entry", delete the untarred copies and voicebank/, assert ≤ 20 items }` (:601-603, :677-683).
- **Colab session:** the same without the restore and `pack_state`, with the mount at (4d).
- **Plugin rate path** (D-010 :301-305):
  1. `prepareToPlay(rate)` → atomic host rate.
  2. The timer sees `Renderer::latest()` or the host rate change → worker job `(original, rate)` → `resampleTake` → publish.
  3. Restore: a cache hit is published by the message thread (:312-315) → the worker resamples it.
  4. Interface calls that carry this: `Renderer::latest()`, `resampleTake`, `TakeSlot::publish`. They all exist. **No frozen test runs the plugin at a rate other than 48 kHz.**
- **Capture** (D-022 :279-286):
  - Message thread: CAS `Idle→Armed`.
  - Audio thread: CAS `Armed→Capturing`; writes FIFO events while `Capturing`; CAS `Capturing→Stopping`. The timer then drains, finishes, resets and stores `Idle`.
  - Message thread: CAS `Capturing→Cancelling`. The timer then drains, discards, resets and stores `Idle`. **No audio-side acknowledgement comes before this reset.**
  - The replace warning is carried by `lastWarnings()`, whose semantics (:316) drop it when the next render completes.

---

## 1. Simulation

*Values are illustrative, not measured, unless a source is cited.*

### 1a. [software] Six months after delivery

I could not construct a Critical-class (catastrophic) software failure under perfect adherence to the current plan. The most severe plausible failure is below. Its true severity is **Medium**: no data is unrecoverable.

| When | What the owner sees | Traced root cause |
|---|---|---|
| Merge + 0 | The owner builds the plugin. Takes render at 48 kHz (`outputSampleRate` is fixed, D-010 :301-302). The resample worker serves the owner's 44.1 kHz project. | as specified |
| + 4 months | Recording a vocal part, the owner arms capture, plays, decides against it and disarms mid-pass. The message thread CASes `Capturing→Cancelling` (D-022 :280-281). The 4-Hz timer then drains, discards and resets the FIFO indices. Nothing proves the audio thread has stopped writing: it read `Capturing` at the start of the block it is still processing. `AbstractFifo` is reset under a live writer, which is the R-064 condition. The writer's `finishedWrite` leaves `validEnd` past the reset start. | R-090 |
| + 4 months, next capture | The next capture drains the stale slots of the cancelled pass together with the new events. The stored notes of an approved part are replaced by the merged set. The warning "stored notes replaced; the previous take stays in the take cache" (D-022 :284) is held in `lastWarnings()`. That is overwritten when the render submitted by the same capture completes (D-010 :316), seconds later. The editor has no note view (D-027), so the owner hears a changed melody only on playback. | R-090, R-093 |
| + 6 months | The owner notices, re-opens an older project save and gets a cache hit (D-010 :312-315). The approved take is back. Cost: rework. | recoverable |

Separately, a verification gap: the resample worker's wiring is untested at any host rate other than 48 kHz (test_plugin.cpp:102, :127, :152, :187). An implementation without a working worker passes CI and plays 48-kHz takes by nearest sample (playback.hpp:31-35). That is the R-072 defect, now undetected rather than unspecified (R-091).

### 1b. [computational] Twelve months after completion: a claimed result is false

| When | Event | Traced root cause |
|---|---|---|
| G-004 run 1, Colab | Two Colab sessions run split→train. Training reaches epoch 120, and Drive's `run1/out/budget.json` records 6.1 GPU-h. The Colab free tier then refuses a GPU for days. Cell (1)/(4c) raises, and the owner reports `failed: 4 …`. | as specified (C-017) |
| Re-issue (RUN kept) | GATE-G-004.md asks all questions again, including "(3) Colab or Kaggle?" (GATES.md:58). The owner chooses the documented fallback (D-016, DECISIONS.md:387). This is the voice's first Kaggle version, so GATE-G-004.md says `RESUME = False` (PLAN.md:427; DECISIONS.md:560). The run starts in an empty `/kaggle/working`: split…train from the pretrained model, and `budget.json` and `budget-voice.json` both start at 0. | R-082 |
| Kaggle versions 1–3 | Training completes. Each version's `state.tar` hash is to be "recorded as `state_tar_sha256` in the session's `sessions[]` entry" (:680-681). But that `budget.json` is inside the tar and its loose copy is deleted. The implementer guesses: the next session back-fills the field from `state.tar.sha256`. | R-083 |
| S-017 | Every 2a check passes (PLAN.md:433-440): Σ sessions, `train` ran, commits, t-p20.xml, and the chain check (tautological under the back-fill guess). `results/myvoice/run1/budget.json` commits 12.9 GPU-h, labelled "lower bound (5-minute heartbeat)" (GATES.md:15). | R-082, R-083 |
| G-001 `retrain` | It is allowed because the uploaded `budget-voice.json` (12.9) is under 20 (GATES.md:28). Run 2 on Kaggle spends 7 h more. The committed per-voice total is 19.9 h. The true total is 26 h, so A-015 is exceeded, and Drive still holds a second `myvoice-run1` lineage at epoch 120. | R-082 |
| + 12 months | An audit of the owner's Colab history against the committed results shows the SC-9 claim "within the 20-h budget" (ASSUMPTIONS.md:62) and the committed `gpu_hours` are false by 6.1 h. The heartbeat label understates the error by more than an order of magnitude. | R-082 |

**Root-cause summary.** Run state and both ledgers belong to the platform, but the plan lets the platform change at every G-004 issue. The R-068 chain check compares only sessions that are present, and one of its two values cannot be recorded as specified.

---

## 2. Round-3 mitigation audit

| Risk | Verdict | Reason (file:line) |
|---|---|---|
| R-053 | adequate | S-017 1a now says `RUN` = 1, +1 per `retrain`, and a `failed:` re-issue keeps `RUN` (PLAN.md:426-427). This matches D-035 (DECISIONS.md:547-548) and GATES.md:62-64. A grep for "issue number" in plan/, HANDOFF.md and eval/ finds no stale text. |
| R-068 | partially | Fixed: the forgotten-input case. `RESUME` raises on a missing or unexpected `state.tar` (DECISIONS.md:621-625), `restored_from` is recorded (:627), there is the S-017 chain check (PLAN.md:439-440) and dry-run scenario (6) (PLAN.md:403). Not fixed:<br>• `state_tar_sha256` cannot be recorded as specified (:680-683) → R-083.<br>• A version that wrote no `state.tar` (hard kill, or an error in cells (1)–(4) after the restore), or an older output attached, is absent from the restored ledger. The chain check only compares sessions that are present → R-083.<br>• `RESUME` is defined as "False only for the voice's very first Kaggle version" (GATES.md:53-54). That dead-ends when that version wrote nothing → R-088.<br>• A Colab↔Kaggle switch legitimately starts with `RESUME = False` and resets both ledgers → R-082. |
| R-069 | partially | `guarded` covers (5)–(16), sets `STOP_REASON = failed: …`, and cell (17)'s try/finally persists state (DECISIONS.md:597-609). So every failure after cell (4) reaches `pack_state`. Residual problems:<br>• "(1)–(4) may raise: nothing has been written yet" (:603-604) is false on Kaggle: cell (3) has already extracted `state.tar` into `/kaggle/working` (:625-626) → R-088.<br>• Owner-actionable stops ((7) data, (10a) disk/RAM, (4e) parameters) are now `failed:` lines that GATES treats as notebook defects → R-087.<br>• Scenario (5) calls `pack_state` itself. Cell (17)'s finally is never executed by the dry run → R-089. |
| R-070 | adequate | `sh` starts a new process group, sends SIGTERM to the group, then SIGKILL after 60 s, and returns rc 124 (DECISIONS.md:580-585). C-065 is pinned source. The group kill covers both RVC branches. C-065 omits the in-process `single_cuda` branch (rvc_process_structure.txt:3-5), which the kill also covers. Residual: the post-timeout `nvidia-smi` check (:583-585) relies on container process visibility → R-094 (Low). |
| R-071 | partially | `t-p20.xml` is written in cell (16), carried in the upload (:675-677, :716-718), and checked at S-017 (PLAN.md:438-439). But:<br>• Cell (16) runs with cwd `<run>` (:554-555), where pytest finds neither pytest.ini nor tests → exit 5 every time → R-085.<br>• A legitimate "invalid" evaluation (eval/PROCEDURE.md:37-38) becomes `failed: 16` with no upload → R-084. |
| R-072 | partially | `resampleTake` is frozen and tested (take_cache.hpp:25-29; test_resample_take.cpp:10-28). `outputSampleRate` is fixed and a worker that always resamples from the original is specified (DECISIONS.md:301-305). PK-76 holds: each behaviour names its call. But:<br>• No plugin test runs at a host rate other than 48 kHz (test_plugin.cpp:102, :127, :152, :187), so a missing or wrong worker passes CI.<br>• The worker publishing contradicts D-022's "single writer = message thread" (:270).<br>• The worker's lifetime at plugin destruction is unspecified (D-013's join rule, :248-249, covers only `Renderer`).<br>→ R-091. |

**Other round-3 changes checked (not counted).**
- **R-073:** adequate. `state.tar` now holds every `run*/` and `voicebank/` is deleted (:680-683).
- **R-074:** partially. "Module-level singleton" (:703-704), but `HEARTBEAT` is a cell-(3) global (:578). Re-running cell (3) rebinds it, which can orphan the old thread.
- **R-075:** adequate for its own failure mode. The new failure mode it creates is R-086.
- **R-076:** partially. Nothing ever deletes `RESTART_DETECTED` → R-092.
- **R-077:** partially. The rule is now computable (:196-200), but parts are spliced with no crossfade. The S-008 check is a throw-away, not a regression test, and its "two model runs" is ambiguous (two parts mean 2 acoustic + 2 vocoder runs).
- **R-078:** CAS on both sides fixes the lost-disarm race. The new failure modes are R-090 and R-093.
- **R-079:** partially → R-089.
- **R-080, R-081:** adequate.

---

## 3. Lenses

**Technical correctness.**
- R-083: an unrecordable `state_tar_sha256`.
- R-085: the cell (16) working directory.
- R-086: a budget-bound train stage with no snapshot.
- R-090: the `Cancelling` FIFO reset.
- R-089: dry-run expectations contradict D-035:665 (`<LOCAL>` is rebuilt every session).
- Checked and sound: the process-group timeout. The (17) normal branch writes the budget before the tars (:677-679), and the finally's second write is idempotent. The `.bak` naming against RVC's glob (:595). `filter="data"` extraction.

**Dependency and supply-chain drift.**
- R-023 residual, now inadequate. D-033 declares "GCC ≥ 11" (DECISIONS.md:484-485), but S-000 requires g++ ≥ 13 (PLAN.md:49-50) and CI builds only with GCC 13.3. The hosted image compiles the core at (4f) with its own compiler (GCC 11 on Ubuntu 22.04 images, UNVERIFIED).
- A GCC-12+ library feature passes CI and fails at (4f), for example `std::atomic<std::shared_ptr>`, which is a natural choice for `Renderer::latest()` and the worker hand-off. That costs a `failed: 4` round the implementer cannot reproduce.
- Same failure mode as R-023, so no new ID. Proposed: S-000 installs `g++-11`, and S-010 builds `singvst-render` with it.
- `restore_state` runs in the kernel's Python. `tarfile` `filter=` needs 3.10.12+, 3.11.4+ or 3.12. UNVERIFIED for the Kaggle image; no claim covers it.

**Invalid research assumptions.**
- C-019 and C-064 are single-source. Unresearched and load-bearing for R-083 and R-088: errored-version output semantics, and which version "Add Input → Your Work" attaches.
- C-010 (single-source) is covered by G-005.
- C-017, C-018 and C-026 are corroborated. Unchanged.
- C-065 (verified) omits the `single_cuda` in-process branch. No impact.
- No claim covers:
  - `nvidia-smi --query-compute-apps` inside Colab/Kaggle containers (R-094);
  - the hosted GCC version;
  - the duration of evaluate plus T-P20, which the fixed 1-h reserve (:588-589) assumes (PK-29).

**Implementer misinterpretation.**
- R-083: where `state_tar_sha256` is recorded.
- R-085: cell (16) working directory.
- R-087: owner-actionable `failed:` lines.
- R-088: `RESUME` after a first version that wrote nothing.
- R-089: dry-run scenarios (2) and (4), and `params.json`/`raw/` pre-creation.
- R-091: which thread publishes.
- R-092: who deletes `RESTART_DETECTED`.
- `stopped_by_budget` is `<bool>` in training.json (:669) but `<N>` in budget.json (:713). No ID; harmless to the checks.

**Integrity (Rule 9).**
- R-082: committed `gpu_hours` and the SC-9 claim are wrong after a platform switch.
- R-084: the upload is gated on a second, independent stochastic evaluation. Re-running until T-P20 passes selects validity draws, and invalid outcomes never reach G-001.
- R-083: the chain check is unsatisfiable or tautological.
- Positives: files are never edited, gate history is kept, and the verdict is recomputed.

**Past lessons (PK).**
- PK-74 applied here found R-083 (pack_state against the S-017 check), R-088 (restore against "nothing written yet") and R-090 (the `Cancelling` path skips the `Stopping` handshake).
- PK-76 found R-093 (`lastWarnings()` cannot carry a capture event).
- PK-29: the 1-h reserve is not derived from a measurement.
- PK-63 now holds for S-019, since t-p20.xml is delivered.
- PK-71: batch size is still outside stage identity (R-054, open).

**Scale and performance.**
- Resampling a 900-s take is about 40 M output samples × about 70 taps on the worker. Each instance holds the original plus the copy (about 330 MB) while both are alive.
- Acceptable on a worker thread. Folded into R-028 (open). No new ID.

**Security.**
- Nothing new meets the bar.
- Extraction uses `filter="data"` (:625).
- R-094's PID-based SIGKILL could target a non-namespace PID (UNVERIFIED); the effect is availability, not exposure.

**Operational realities.**
- R-082: platform fallback.
- R-087: owner-actionable stops.
- R-088: Kaggle "previous version" after an errored version.
- R-085: a guaranteed first-run `failed: 16` under literal adherence.

**Audio thread (PK-38).**
- R-090: FIFO reset under a live writer.
- R-091: the worker publishes from a non-message thread. This is safe under `TakeSlot`'s writer mutex (D-022 :274-275) but contradicts :270.
- `processBlock` still never locks or allocates. `TakeSlot` is unchanged and sound.

**Numerical validity.**
- R-077 residual: splice discontinuity at forced phrase splits.
- A timeout that truncates only `D_2333333.pth` restores D from `.bak` (e0) while G stays at e1 (:651-653). The lineages are mixed, but the GAN recovers. Low, no ID.
- T-P20's evaluation is a different draw from the committed report (test_evaluate.py:41-42), which is relevant to R-084.

**Reproducibility.**
- R-082: two lineages share one experiment name across platforms.
- R-092: `.bak` frozen at an old epoch.
- R-054 open.

**Compute budget.**
- R-086: a retrain near the per-voice budget dead-ends.
- R-082: the per-voice cap is bypassed across platforms.
- R-085 and R-087: wasted sessions.
- T-P20 (cell (16)) repeats all 50 renders and Whisper inside the unmeasured 1-h reserve (PK-29). Low, no ID.

---

## 4. Risk table (new risks)

| ID | Description | Lens | Severity | Likelihood | Root cause | Traces to | Proposed mitigation |
|---|---|---|---|---|---|---|---|
| R-082 | **A Colab↔Kaggle switch silently restarts training and both GPU ledgers.** Run state and `budget-voice.json` live under the platform's `<root>` (DECISIONS.md:542-546, :701-702). Every G-004 issue, including a `failed:` re-issue that keeps `RUN`, asks "Colab or Kaggle?" (GATES.md:58-59, :62-64), and Kaggle is the documented fallback (:387). The voice's first Kaggle version runs with `RESUME = False` (PLAN.md:427), so split…train restart from the pretrained model and both ledgers restart at 0. Every S-017 2a check passes (PLAN.md:433-440). The committed `gpu_hours`, the GATES.md:15 label and the SC-9 claim are false by the abandoned platform's hours. The G-001 `retrain` condition (GATES.md:28) and `t_budget` (:588-589) then let the per-voice total exceed A-015. | compute; integrity; reproducibility | Critical | medium | Ledgers and run state were designed per platform; the platform was never bound to a run or a voice. | DECISIONS.md:387, :542-548, :560, :701-702; GATES.md:15, :28, :58-64; PLAN.md:427, :433-440; A-015; SC-9; R-062; R-068 | D-035: `PLATFORM` goes into `params.json`, so a switch within a run stops with "start a new RUN". GATE-G-004.md gives a Parameters-cell value `PRIOR_VOICE_GPU_HOURS`, the sum over committed `results/<VOICE>/run*/budget.json`, plus the abandoned platform's `budget.json`, which the owner attaches. The notebook seeds `budget-voice.json` from it. S-017 2a checks that `budget-voice.json` ≥ that sum plus this run. GATES: a platform switch is a new RUN. |
| R-083 | **`state_tar_sha256` cannot be recorded where D-035 puts it, and the R-068 chain check cannot see a missing session.** `pack_state` tars `run*/` (which holds `budget.json`), deletes the untarred copies, and "also records" the tar's hash "in the session's `sessions[]` entry" (:680-683). No file can hold its own tar's hash, and the upload tar is written before `pack_state` (:678-680). Literal adherence means S-017's check "`restored_from` equal to the previous session's `state_tar_sha256`" (PLAN.md:439-440) fails for every multi-session Kaggle run: ask twice, then `BLOCKED.md`. The only workable guess (the successor back-fills from `state.tar.sha256`) makes the check tautological. A session that wrote no `state.tar`, or was skipped because an older output was attached, has no entry at all, so it can never be compared. The dry run never executes cell (17) (PLAN.md:398-403). | integrity; misinterpretation; compute | High | high | A verification was specified against an artefact whose write order makes it unrecordable (PK-74). | DECISIONS.md:625-627, :677-683, :701-702; PLAN.md:398-403, :439-442; R-068; C-064 | Drop `state_tar_sha256` from `sessions[]`. Each session records `seq` (previous + 1) and `restored_from`. Cell (17) prints `seq <n> state.tar <sha>`. GATES: for Kaggle, the owner pastes every version's final line. S-017 checks that the pasted hashes, in version order, equal the successive `restored_from` values, and that the number of versions equals the number of sessions. |
| R-084 | **Gating the upload on T-P20 turns a legitimate "invalid" evaluation into an unfixable notebook failure.** eval/PROCEDURE.md:37-38 defines an invalid report as a result: "T-P20 then fails, which is the intended outcome". D-035 makes a failing T-P20 a guarded `failed: 16` with no upload (:676-677). GATES treats `failed:` as a notebook defect to fix, three times, then `BLOCKED.md` (GATES.md:62-64). DR-10…DR-13 are unreachable for invalid outcomes. T-P20 also runs its own independent evaluation (test_evaluate.py:41-42), so it can fail when cell (15)'s report is measured, or pass when it is not. Re-running until it passes selects draws (Rule 9). | integrity; misinterpretation | High | low | The R-071 fix reused the `failed:` path for a test whose failure is a defined outcome. | DECISIONS.md:597-601, :672-677, :716-718; eval/PROCEDURE.md:37-38; GATES.md:62-64; tests/python/test_evaluate.py:34-42; PLAN.md:438-439, :512; Rule 8 | Cell (16): a pytest exit 1 (assertion) does not set `STOP`. The upload always carries `t-p20.xml`. Only exit 2–5 (error or collection) is `failed: 16`. S-017: a T-P20 failure is recorded and shown at G-001 with the report status (DR-10…DR-13). S-019's Done-when accepts "T-P20 failed: <reason>, disclosed". Re-runs to make it pass are forbidden. |
| R-085 | **Cell (16) runs pytest where there are no tests.** "Every other command runs with cwd `<run>`" (:554-555), and cell (16)'s `--junitxml=out/eval/t-p20.xml` assumes it (:675-676). Unlike cell (6), it does not say "from the sing-vst checkout". From `<run>`, pytest finds no pytest.ini (`testpaths = tests/python`, pytest.ini:2) and collects nothing, so it exits 5, which is a guarded failure. Every first owner run therefore ends with `failed: 16`. The re-issue rebuilds the binary and re-runs evaluate and T-P20. The dry run does not exercise cell (16). | misinterpretation; compute | Medium | medium | The cwd default was not checked against a command that needs the checkout's config. | DECISIONS.md:554-555, :641-642, :675-677; pytest.ini:2; R-071 | Spell cell (16) as `python -m pytest -q -m voice -c <sing-vst>/pytest.ini --rootdir <sing-vst> <sing-vst>/tests/python --junitxml=<run>/out/eval/t-p20.xml`, with absolute `SINGVST_*` paths. Exit 5 → `failed: 16 no tests collected`. |
| R-086 | **A retrain near the per-voice budget dead-ends in the train stage.** G-001 allows `retrain` while `budget-voice.json` < 20 (GATES.md:28), but `t_budget = 20 − 1 − gpu_hours` (:588-589). With 19 ≤ gpu_hours < 20, or `t_budget` binding before the new experiment's first `-se 10` snapshot, the DR-13 branch copies `latest_weights` of a run with no `<exp>_e<N>` → `FileNotFoundError` (rvc_files.py:33-36) → `failed: 11`. Nothing in the notebook can fix it, and each re-issue spends rvc-f0/features GPU time → `BLOCKED.md`. Likewise, a budget kill during a snapshot save leaves a truncated newest `<exp>_e<N>`. DR-13 copies it and export fails in every later session. | compute; technical | High | low | The 1-h reserve (R-075) was not propagated to the G-001 retrain rule or to DR-13's preconditions. | DECISIONS.md:587-592, :711-713; GATES.md:27-28; rvc_files.py:33-36; DR-13; A-015; R-075 | GATES: `retrain` only while `budget-voice` < 19 − (run 1's measured hours per 10 epochs). The DR-13 branch copies the newest snapshot that loads (`torch.load` via `sh`). With none, it sets `STOP_REASON = "budget: no checkpoint"`, reported as a G-001 result under DR-13, not `failed:`. |
| R-087 | **Owner-actionable stops are reported as notebook failures.** `guarded` maps every stop to `failed: <cell> …` (:598-601). That includes: too few recordings (7) (:644-646), RAM or disk (10a) (:568-572), "parameters changed within run" (:565-566), and unreadable checkpoint "delete logs/<exp>" (:653). GATES' only `failed:` handling is "the implementer fixes the notebook … at most three per issue, then `BLOCKED.md`" (GATES.md:62-64). The implementer must guess whether to re-issue with an unchanged commit, and owner fixes use up the three attempts. | operational; misinterpretation | Medium | medium | `failed:` was given one meaning for two kinds of cause. | DECISIONS.md:565-572, :597-601, :644-646, :653; GATES.md:62-64; R-069 | `guarded` maps an `OwnerAction` exception to `STOP_REASON = owner: <message>`. GATES adds the response `owner-fixed: <cell>`: re-run with the same commit, not counted toward the three attempts. |
| R-088 | **On Kaggle, an error in cells (1)–(4) after the cell-(3) restore leaves a version with no `state.tar`, and `RESUME` then dead-ends.** "Cells (1)–(4) may raise: nothing has been written yet" (:603-604), but cell (3) has already extracted `state.tar` into `/kaggle/working` (:625-626). Any (4) failure errors the version without `pack_state`: install outage, arch (4c), build (4f), params (4e). Following GATES ("add the previous version's output", GATES.md:52-54), the next version finds no `state.tar` and raises "attach the previous version's output" in a loop. Worse: when the voice's first Kaggle version fails in cell (4), every later version has `RESUME = True` (PLAN.md:427) and no `state.tar` exists anywhere, so it raises forever. The plan's only exit is a guess. A wrong guess (`RESUME = False` while an older `state.tar` exists) is R-068's silent reset. Which version "Add Input" attaches is unresearched (C-064). | operational; compute; misinterpretation | High | medium | The restore was placed before steps that may raise, and `RESUME` was defined by version count, not by state existence. | DECISIONS.md:560, :603-604, :620-627; GATES.md:52-55; PLAN.md:427; C-064; R-068 | Cell (3) first copies the verified `state.tar` and `.sha256` into `/kaggle/working`, so every version's output carries one from the start. `RESUME` = "a version of this voice has printed `state.tar <sha>`". GATES names "the most recent version that printed `state.tar <sha>`". |
| R-089 | **The S-016 dry-run scenarios cannot pass as written, and they skip cell (17).** (a) `params.json` (written at (4e)) is an input of every stage (:684-685) and `raw/` is split's input. Neither is among the "two non-stage inputs" pre-created (PLAN.md:396-397), so `content_hash` raises. (b) Scenario (2) says a restore leads to "no stage runs" (PLAN.md:399-400), which contradicts D-035:665: `<LOCAL>` is rebuilt every session, so render-bin re-runs and, through the binary, so does evaluate. The scenario passes only if the dry run keeps `<LOCAL>`, which is not a real session. (c) In scenario (4), the fake only raises `SessionEnd`, yet `STOP` is expected to be set. (d) The Colab notebook needs `pack_state`/`restore_state` for scenarios (2), (4) and (5). (e) Cell (17)'s ordering is never executed, so R-083 passes. The implementer shapes the expectations, and any shaping exits 0. | misinterpretation; past lessons | Medium | high | The dry-run expectations were written without re-deriving the session sequence (PK-74). | PLAN.md:393-404, :410; DECISIONS.md:620-621, :663-666, :677-685; R-079 | S-016 states per-scenario expected `stages_run`, including `render-bin` after a resume with a fresh `<LOCAL>`. Cell (3) factors `write_params()` (4e) and `end_session(stop)` (17). The dry run calls both, runs scenarios (4) and (5) through `end_session`, and asserts the recorded ledger fields. |
| R-090 | **`Cancelling` resets the FIFO while the audio thread may still write.** The message thread's CAS `Capturing→Cancelling` is asynchronous to `processBlock`, which reads `Capturing` once per block and then writes events. The timer drains and "resets the FIFO indices" in `Cancelling` (D-022 :283-286) with no audio-side acknowledgement. With `Stopping`, the audio thread's own CAS proves it stopped writing; with `Cancelling`, nothing does. This is exactly the condition R-064 forbade. Inconsistent `AbstractFifo` indices make the next capture replay the cancelled pass's slots, so stored notes are replaced with a merged set. Not exercised: T-057 is single-threaded and the plugin is not built under TSan (ci.yml:110). | audio thread; technical | Medium | low | The R-078 fix added a message-side transition without the handshake the R-064 fix relied on. | DECISIONS.md:279-286; test_plugin.cpp:150-183; ci.yml:110; PK-38; R-064; R-078 | D-022: the message thread CASes `Capturing→Cancelling`. `processBlock`, at its next block start, CASes `Cancelling→Discarding` and writes nothing more. The timer drains and resets only in `Discarding` (and `Stopping`). |
| R-091 | **The plugin resample worker is untested and under-specified.** No plugin test prepares at a rate other than 48000 (test_plugin.cpp:102, :127, :152, :187). T-071 checks only the function. A missing worker or wrong wiring therefore passes CI and silently restores R-072's nearest-sample playback (playback.hpp:31-35). D-010 makes the worker publish (:303-305), but D-022 says "single writer = message thread" (:270). The worker's cancellation and join at destruction are unspecified: `resampleTake` has no cancel, and D-013's join rule covers only `Renderer` (:248-249). A late publish into a destroyed `TakeSlot` crashes the host on close. | audio thread; technical; misinterpretation | Medium | medium | R-072's mitigation froze the function but not the behaviour around it (PK-76 satisfied for naming, not for verification). | DECISIONS.md:270, :248-249, :301-305; take_cache.hpp:25-29; test_plugin.cpp:102, :127, :152, :187; R-072 | D-010/D-022: the worker is a second `TakeSlot` writer under `writerMutex`. Jobs carry a generation number and publish only if still current. The destructor sets a stop flag and joins before the `TakeSlot` is destroyed. Amendment: a plugin test with `prepareToPlay(44100)` and `publishTakeForTesting(48 kHz)` that pumps until the played block matches `resampleTake`. |
| R-092 | **`RESTART_DETECTED` is never cleared.** No step deletes it (:593-595). For the rest of the run the guard never refreshes `.bak`. A later timeout that truncates G or D restores the old e0 and loses every epoch since detection, on every such occurrence. | reproducibility; compute | Low | low | Recovery path added without an exit. | DECISIONS.md:593-595, :651-654; R-076 | The first session whose post-train check passes refreshes `.bak` and deletes the marker. |
| R-093 | **The capture-replace warning is carried by an interface that drops it.** D-022 adds "stored notes replaced; the previous take stays in the take cache" (:284). `lastWarnings()` is "the warnings of the most recent import or completed render" (D-010 :316). The render submitted by the same capture overwrites the warning within seconds (PK-76). | misinterpretation; operational | Low | medium | A behaviour was added to an interface whose semantics cannot hold it. | DECISIONS.md:284, :316; PluginProcessor.h:55; PK-76; R-078 | Append capture warnings to the next render's warnings, or show them in the status line until the next capture or import. |
| R-094 | **The post-timeout GPU check depends on unresearched container behaviour.** `nvidia-smi --query-compute-apps=pid` (:583-585) inside Colab or Kaggle containers may list nothing, which makes the check vacuous, or host-namespace PIDs. SIGKILL then hits no process or the wrong one, and the outcome of a still-non-empty re-check is unspecified (UNVERIFIED; no claim). | technical; operational | Low | low | A verification step was added without a claim. | DECISIONS.md:583-585; C-065; R-070 | Verify termination with `os.killpg(pgid, 0)` (expect `ProcessLookupError`). Print the `nvidia-smi` output for information only; never kill PIDs taken from it. |

---

COUNTS (new + inadequately mitigated round-3 risks): Critical=1 High=4 Medium=5 Low=3

*The counts cover the new risks R-082…R-094. None of the six audited round-3 risks is "inadequate": R-053 and R-070 are adequate, and R-068, R-069, R-071 and R-072 are "partially", with their new failure modes given the IDs above.*
