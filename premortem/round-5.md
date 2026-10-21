# Pre-mortem: round 5 (Phase 4, final round)

**Scope.** I reviewed branch `gen-20261004T095012Z-singing-voice-vst-pitch-lyrics` (HEAD `5efd15d`) read-only. I changed, built and ran nothing, and used no network. I read:
- HANDOFF.md
- plan/PLAN.md, DECISIONS.md, GATES.md, ASSUMPTIONS.md, ENVIRONMENT.md, PROTOCOL_EXCERPTS.md (Rule 4, Rule 9)
- eval/PROCEDURE.md
- research/claims.json (C-017, C-019, C-047, C-061, C-064, C-065 checked in full)
- research/PRIOR_KNOWLEDGE.md (PK-01…PK-77) and lessons L-20261021T150000Z and L-20261021T180000Z
- premortem/round-4.md and premortem/RISK_REGISTER.md
- tests/cpp/test_plugin.cpp, tests/python/test_evaluate.py, test_notebooks.py, conftest.py; pytest.ini
- .github/workflows/ci.yml
- core/include/singvst/{playback,render,take_cache}.hpp; plugin/PluginProcessor.h
- python/singvst_train/{rvc_files,pipeline,evaluate,metrics}.py

`sha256sum -c tests/FROZEN_MANIFEST.sha256` reports OK for all 93 entries. Severities follow Global Rule 4 for the `software` and `computational` profiles. Anything that could not be checked offline is marked UNVERIFIED.

**Commit note.** T-P22 resolves every `R-###` cited in `premortem/*.md` against the register. This file must be committed together with register rows R-095…R-107.

**PK-74 re-derivation (the basis for everything below).** I rebuilt each changed procedure, step by step, from the current text.

- **Kaggle session:**
  1. (1) → (2) → (2a): `RESUME`, `PRIOR_VOICE_GPU_HOURS`.
  2. (3) defines the helpers. Then glob, `RESUME` test, SHA check, and `restore_state`, which copies `state.tar` and `.sha256` into `/kaggle/working` (**the first write**). It then checks the members and extracts them. `restored_from` and `seq` are held for (4e) (DECISIONS.md:646-657).
  3. (4a)–(4c).
  4. (4e): mkdirs, `params.json` with `PLATFORM` (written or checked), freeze/env files, `sessions[]` entry, heartbeat. `budget-voice.json` gets `prior_gpu_hours = max(file, PRIOR)` (:576-580, :731-733).
  5. (4f): build. If it raises, the (4) handler closes the entry, stops the heartbeat and re-raises (:623-624).
  6. (5)–(16) run guarded.
  7. (17): `try` {normal: final budget write, out tar, upload tar | STOP: print reason} `finally` {stop heartbeat, write budget files, `pack_state`, print "state.tar written", then the `seq <n> state.tar <sha>` last line} (:629-633, :707-712).
- **Colab session:** the same with no restore and no `pack_state`. The mount is at (4d).
- **Ledger readers:** "readers (S-017, the budget sums) also ignore any entry without `end`" (:623-625). The heartbeat rewrites "the running session's GPU time" every 5 min, "so a killed session loses at most 5 minutes" (:733-737).
- **Plugin take path** (D-010 :305-311):
  1. The 4-Hz timer sees `Renderer::latest()` change.
  2. The worker job runs (`resampleTake`, or the original copied).
  3. `callAsync` hands the take to the message thread.
  4. The message thread publishes if the generation is newest.
  5. The destructor stops and joins the worker.
- **Capture:** `Capturing→Cancelling` (message thread), then `Cancelling→CancelAck` (next `processBlock`), then the timer drains, discards, resets and stores `Idle`. A 2-s fallback applies (D-022 :280-290).

---

## 1. Simulation

*Values are illustrative, not measured, unless a source is cited.*

### 1a. [software] Six months after delivery

I could not construct a Critical-class (catastrophic) software failure under perfect adherence to the current plan. The most severe plausible one is below. Its true severity is **Medium**: a host crash with no project data lost.

| When | What the owner sees | Traced root cause |
|---|---|---|
| Merge + 0 | The owner builds the plugin. Projects run at 44.1 kHz. Takes render at 48 kHz, and the D-010 worker resamples them for playback. | as specified |
| Before delivery (S-011) | T-058 fails: `pumpUntil(renderStatus()==Ready)` returns about 20 ms after the Renderer turns Ready, before the 4-Hz timer, the worker and `callAsync` have published the take (test_plugin.cpp:26-31, :192-196). The implementer redefines `renderStatus()` after three attempts. One attempt cycle is lost. | R-100 |
| + 6 months | The owner opens a project with a 6-minute part. Restore → cache hit (D-010 :320-323) → worker job (about 16 M samples). The owner immediately switches projects, so the host destroys the instance on the message thread. The destructor sets the stop flag and joins: the UI freezes for about 1 s because `resampleTake` cannot be cancelled. The worker has already posted its `callAsync` lambda. The destructor returns. The message loop then runs the lambda, which reads the freed `Impl` to compare generations, and the DAW crashes. | R-101 |
| + 6 months | The owner reopens the project and nothing is lost. The crash recurs whenever closing races a resample. | recoverable |

### 1b. [computational] Twelve months after completion: a claimed number is false

| When | Event | Traced root cause |
|---|---|---|
| G-004 run 1, Colab session 1 | Split → train. At 7 h the free tier reclaims the GPU (C-017; R-002, likelihood High). Cell (17) never runs. The heartbeat has written session 1's entry with `gpu_hours` 6.25 and no `end` (:733-737). | as specified |
| Session 2 | The budget sums "ignore any entry without `end`" (:623-625), so the voice total at the start is 0 and `t_budget` = 19 h (:605). RVC resumes from the checkpoint and trains 8.9 h. Session 3 runs export and evaluate (1.1 h). | R-095 |
| S-017 | The upload's `budget.json` holds three entries. `gpu_hours` = 10.0, the sum of the ended entries. Every 2a check passes, including "entries without `end` are ignored" (PLAN.md:441, :448-449). The committed value is labelled "lower bound (5-minute heartbeat)" (GATES.md:15). | R-095 |
| G-001 `retrain` | Allowed, because 10.0 < 19 − x (GATES.md:28). The owner retrains on Colab. GATE-G-004.md states `PRIOR_VOICE_GPU_HOURS` = 10.0, "the GPU hours this voice has already used on any platform" (:573). `budget-voice` = max(0, 10) + Σ runs (10 + run 2) = 20 + run 2, so `t_budget` < 0 at the first train stage. Train stops with `budget: no checkpoint` → `budget-exhausted` → G-001. Run 2 is dead after spending its f0/feature hours. | R-097 |
| Alternative implementer reading (PRIOR = 0) | Run 2 trains 8.9 h. The committed voice total is 19.9 h; the true total is 26.2 h. | R-095 |
| + 12 months | An audit sums every `sessions[]` entry of the committed `results/myvoice/run1/budget.json`, which still contains session 1's 6.25 h. The committed total, the SC-9 claim "within the budget" (ASSUMPTIONS.md:62) and A-015 are all false. The "5-minute" error bound is understated by 75×. | R-095 |

**Root-cause summary.** Round 4 added a rule that drops exactly the entries the heartbeat exists to preserve. It also added a carry-over value whose definition counts the same platform's hours twice. Neither the S-017 checks nor the dry run can see either problem.

---

## 2. Round-4 mitigation audit

| Risk | Verdict | Reason (file:line) |
|---|---|---|
| R-082 | **inadequate** | Four reasons:<br>(1) The platform binding is stored per location, which is the very PK-77 anti-pattern. `params.json` lives at `<run>` = `<root>/run<RUN>/` (DECISIONS.md:559-560), and `<root>` is the platform's own storage (:553-556). The new platform never sees the old platform's `params.json`. (4e) writes a fresh one, so the "platform change … stops with the parameters message" (:577-578) can never fire.<br>(2) GATE-G-004.md fixes `RUN` and `PRIOR` before the owner chooses a platform. The platform is answered only in the response, after the run (GATES.md:59-60). A `failed:` re-issue keeps `RUN` (PLAN.md:431; GATES.md:68), and a `failed:` line carries no platform. So "switching platform is a new `RUN`" (GATES.md:68-69) cannot be applied in advance.<br>(3) After a `failed:` there is no upload (STOP branch, :629-633), so no command can produce the abandoned platform's hours (PK-05). `PRIOR` is also missing from S-017 1a's Parameters list (PLAN.md:431-434) and from the GATES evidence list (GATES.md:49-50).<br>(4) The S-017 check `budget-voice ≥ PRIOR + run` (PLAN.md:448) passes with `PRIOR` = 0.<br>Round-4 simulation 1b replays unchanged. **Critical** remains. |
| R-083 | partially | Fixed: the hash is no longer self-referential. The seq line is printed and pasted (:655-657; GATES.md:61), and the chain is checked (PLAN.md:446-448). Not fixed:<br>• A Kaggle version killed by the platform (weekly quota, C-019) prints no line, and its ledger is in no `state.tar`. The chain stays gap-free and its hours vanish. The proposed "versions = sessions" count was not adopted → R-095.<br>• `seq` is undefined for the first session of a new `RUN`, and the check's scope across `failed:` issues and runs is undefined → R-096. |
| R-084 | partially | Fixed:<br>• Exit 1 is a result, and `t-p20.xml` is always uploaded (:625-628).<br>• T-P20 is never re-run.<br>• S-019 accepts a disclosed failure (PLAN.md:444-446, :521-522).<br>New failure modes:<br>• An invalid report now reaches S-017, but 2a recomputes `metrics.judge(report)` against `verdict.json` (PLAN.md:442). For an invalid report `verdict.json` is `{"all": false, "status"}` without `judge` (:528-529), and `judge` raises on `null` metrics → BLOCKED → R-098.<br>• Exit 1 also covers `need_env` assertions and any exception (conftest.py:13-16) → R-099. |
| R-086 | adequate | DR-13 copies the newest loadable snapshot. With none, `budget: no checkpoint` becomes the `budget-exhausted` result at G-001 (:606-609; GATES.md:66). `retrain` is allowed only below 19 − (previous run's hours per 10 epochs) (GATES.md:28). `latest_weights` prefers `<exp>.pth` (rvc_files.py docstring), so export uses the copied file. Residuals: R-104 (Low). The dead end is now reached spuriously through R-097. |
| R-088 | adequate | `RESUME` / attach is now keyed to "printed 'state.tar written'" (:572; GATES.md:54-55; PLAN.md:432), so a version that fails in cell (4) no longer dead-ends. The cell-(3) copy (:651-652) carries the same SHA. D-035:647-649 still says "has a `state.tar` in its output", which differs from the other texts exactly in the R-088 case, but both choices restore the same hash. The copy's disk cost is folded into R-102. |

**Other round-4 changes checked (not counted).**
- R-085: adequate (:705-707).
- R-087: partially → R-102.
- R-089: partially → R-107.
- R-090: adequate; the CancelAck handshake restores R-064's guarantee. Residual → R-105.
- R-091: partially → R-100, R-101, plus the registered residual that no plugin test runs at a host rate other than 48 kHz.
- R-092, R-094: adequate.
- R-093: partially → R-106.
- R-023 (g++-11): partially → R-103.

---

## 3. Lenses

**Technical correctness.**
- R-098: `judge` on an invalid report.
- R-100: `renderStatus()` reports Ready before the take is published.
- R-101: a `callAsync` lambda outlives the processor.
- R-107: dry-run scenarios (2) and (4).
- Checked and sound:
  - the restore order (SHA check before the copy);
  - `pack_state` truncating the copy;
  - the order in which the (17) normal branch writes the upload;
  - `latest_weights` combined with the DR-13 copy;
  - `torch.load` under the torch 2.7 `weights_only` default for RVC's dict/tensor/int/str checkpoints (C-063);
  - the CancelAck sequence.

**Dependency and supply-chain drift.**
- R-103: the g++-11 compile is checked once, at S-010.
- Nothing else in round 4 changed a pin.

**Invalid research assumptions.**
- C-019 (single-source) does not research what happens when the weekly quota is exhausted mid-session, yet R-095's Kaggle mechanism rests on it.
- C-064 (single-source): errored-version output and the 500-item limit. R-088 no longer depends on it.
- No claim covers the size of `/kaggle/working` or how `df` reports it (R-102).
- D-035:695's "the binary's bytes differ" after a same-commit rebuild is UNVERIFIED and probably false, because GCC builds are deterministic (R-107).

**Implementer misinterpretation.**
- R-097: what `PRIOR` means and where it comes from.
- R-096: the scope of `seq`.
- R-095: whether the heartbeat writes `end`.
- R-099: what exit 1 means.
- R-100: the semantics of `renderStatus()`.
- `owner-fixed` re-issues have no gate-file naming rule (`fail<k>` only, PLAN.md:453-455). Low, no ID.

**Integrity (Rule 9).**
- R-095 and R-082: the committed `gpu_hours` and the SC-9 claim can be false.
- R-097: the committed `budget-voice` is overstated.
- R-098: a defined invalid result cannot reach G-001 (Rule 8).
- R-099: a notebook defect is recorded as an outcome that may never be re-run.
- Positives: T-P20 is never re-run for a pass; gate history is kept; files are never edited.

**Past lessons (PK).**
- **PK-74** found:
  - R-095: the "ignore entries without `end`" rule against the heartbeat guarantee;
  - R-098: the new upload path against the 2a recompute;
  - R-102: the copy and OwnerAction against Kaggle storage.
- **PK-76** found:
  - R-100: no interface says when a take becomes playable relative to `renderStatus()`;
  - R-106: `RenderFn` and `Renderer` carry no warnings, so a cache hit has none to carry.
- **PK-77**'s detection check ("name the single place its total lives and the step that carries it"):
  - The per-voice GPU hours live in three places: Drive `budget-voice.json`, the copy inside Kaggle's `state.tar`, and the committed snapshots. The gate value has no data source after a `failed:`, and the platform binding itself is stored per location → R-082 inadequate, R-097.
  - The Kaggle weekly quota lives nowhere → R-095.
  - The three-attempt budget for G-004 became unbounded for `owner-fixed` → R-102.

**Scale and performance.**
- The destructor's `join` waits for an uncancellable `resampleTake`: about 1–3 s for a 900-s take on the message thread (folded into R-101).
- On Kaggle, the cell-(3) copy keeps a third copy of the state in `/kaggle/working` (R-102).
- No other changes.

**Security.**
- Nothing new meets the bar.
- `restore_state` accepts only regular files and directories with relative, `..`-free paths on any Python version (:652-653), which also rejects links.

**Operational realities.**
- R-102: OwnerAction remedies cannot be carried out on Kaggle, and the loop has no exit.
- R-095: Colab reclaims and Kaggle quota kills are routine (R-002, High likelihood).
- R-082: the documented Colab→Kaggle fallback.

**Audio thread (PK-38).**
- `processBlock` still never locks or allocates. CancelAck makes the FIFO reset safe.
- The 2-s fallback (:288) resets only if a block stalls for more than 2 s. Negligible.
- Residuals: R-105 (an arm click lost while the state is reported Idle) and R-101 (lifetime on the message thread, not the audio thread).

**Numerical validity.**
- R-104: `epochs_trained` disagrees with the weights DR-13 copied.
- T-P20's separate draw is now a recorded result beside cell (15)'s report. It may disagree with that report, and the disagreement is disclosed. Acceptable.

**Reproducibility.**
- R-096: the chain is ambiguous across runs.
- R-082: two lineages share one experiment name.
- `budget-exhausted` runs upload nothing, so their configuration and hours exist only on platform storage (folded into R-097's mitigation).
- R-054 is still open.

**Compute budget.**
- R-095 (undercount), R-097 (overcount and a dead retrain), R-082 (switch).
- R-103 and R-102: wasted sessions.

---

## 4. Risk table (new risks)

| ID | Description | Lens | Severity | Likelihood | Root cause | Traces to | Proposed mitigation |
|---|---|---|---|---|---|---|---|
| R-095 | **GPU hours of a session killed by the platform are dropped from both ledgers.**<br>**Colab:** the heartbeat writes the running session's GPU time but no `end` (:733-737). Round 4 then made "the budget sums … ignore any entry without `end`" (:623-625; PLAN.md:449). A reclaimed runtime's hours, up to 10 h, are excluded from `budget.json`, `budget-voice.json`, `t_budget` and the G-001 retrain rule.<br>**Kaggle:** a version killed by the weekly quota (unreadable from code, :634-635; C-019) never runs `pack_state`. The next version restores the older `state.tar`, so the killed session's ledger is gone. It printed no seq line, so the R-083 chain stays gap-free.<br>Every S-017 2a check passes. The committed `gpu_hours`, its "5-minute heartbeat" label and the SC-9 claim are false, and A-015 is silently exceeded. | integrity; compute | Critical | medium | Round 4 added a reader rule (entries without `end`, for the (4f) case) without re-deriving it against the heartbeat guarantee. On Kaggle the ledger is persisted only by a clean end. | DECISIONS.md:623-625, :634-635, :733-737; PLAN.md:441, :446-449; GATES.md:15; A-015; SC-9; R-034; R-083; C-019 | Budget sums include every entry and use its heartbeat `gpu_hours`. "Ignore without `end`" applies only to the S-017 commit check, never to sums. The heartbeat writes `last_beat`. Kaggle: GATES asks for every version from the Versions panel with its status and run time. A version with no seq line adds its run time (an upper bound) to the voice ledger and to the next `PRIOR`. S-017 checks that the number of listed versions equals the number of sessions plus the number of no-line versions. |
| R-096 | **The seq chain is undefined at a RUN boundary and across G-004 issues.** `seq` = "the previous entry's `seq` + 1" (:655-656), but entries live in the per-run `budget.json`. The first session of a new `RUN` (Kaggle retrain), and the first Kaggle session, have no previous entry. The owner pastes "every version in order" (GATES.md:61), which includes earlier runs' and earlier issues' versions, while S-017 matches the pasted lines against this run's `sessions[]` "with no gap" (PLAN.md:446-448). The implementer must guess a filter. A mismatch means asking twice, then `BLOCKED.md` (PLAN.md:449-450). | misinterpretation; reproducibility | Medium | low | R-083's chain was specified for one run and one issue. | DECISIONS.md:655-657; GATES.md:61; PLAN.md:446-450; R-083 | `seq` is voice-wide: the maximum `seq` across all restored `run*/out/budget.json`, plus 1, and 1 for the first Kaggle session. Each entry records `run`. S-017 checks the pasted lines whose `seq` ≥ this run's first `seq`; that first entry's `restored_from` must equal the hash on the preceding pasted line, taken from the committed earlier gate file. |
| R-097 | **`PRIOR_VOICE_GPU_HOURS` double-counts the same platform and has no defined source.** D-035:573-574 defines it as the hours "already used on any platform", and GATES.md:69 says "covering the hours already used". The notebook then computes `max(file, PRIOR) + Σ runs of this platform's folder` (:731-733). On a same-platform retrain, run 1 is counted twice: 12 h becomes 24 h, `t_budget` < 0, and DR-13 finds no snapshot → `budget-exhausted` at the first train stage of run 2. The documented `retrain` response fails, and the committed `budget-voice.json` is overstated. Both readings pass PLAN.md:448. `PRIOR` is absent from S-017 1a's values (PLAN.md:431-434) and from the GATES evidence list (GATES.md:49-50). | compute; misinterpretation; integrity | High | medium | The PK-77 fix defined the carried value by the subject ("this voice") but summed it with a location-keyed total. | DECISIONS.md:573-574, :605-609, :731-733; GATES.md:28, :49-50, :66, :69; PLAN.md:431-434, :448; PK-77; R-082 | Define the carried value as "Σ of `runs` recorded in the *other* platform's `budget-voice.json` (its own runs, excluding its `prior`)". Better: keep one voice ledger committed by S-017 after **every** G-004 response. Cell (17) prints `budget-voice <platform> <json>` in every branch and the owner pastes it. The notebook enforces `t_budget` from `PRIOR` (ledger total minus this platform's recorded runs). List `PRIOR` in S-017 1a and the GATES evidence. |
| R-098 | **An invalid report now reaches S-017, where check 2a cannot pass.** R-084 uploads a failed T-P20 together with its report. For an invalid report, `verdict.json` = `{"all": false, "status": …}` and "judge is not called" (:528-529). S-017 2a recomputes `metrics.judge(report, thresholds)` and requires equality (PLAN.md:442). On `null` metrics `judge` raises `TypeError` (`None >= 0.75`; metrics.py:55-59) or differs. "A failed check → ask the owner for the files again (at most twice, then `BLOCKED.md`)" (PLAN.md:449-450). The defined outcome (eval/PROCEDURE.md validity rules) never reaches G-001 under DR-10…DR-13. | integrity; technical | High | low | The upload path was widened without re-deriving the downstream check (PK-74). | DECISIONS.md:524-529, :625-628; PLAN.md:442, :449-450; eval/PROCEDURE.md "Validity checks"; metrics.py:55-59; R-084 | 2a: when `report.status` starts with `invalid:`, check `verdict.json` == `{"all": false, "status": report.status}`; otherwise recompute `judge`. GATE-G-001 shows `null` metrics as "not computed" and skips the indeterminate test for them. |
| R-099 | **Pytest exit 1 is not only an assertion about the outcome.** `need_env` asserts (conftest.py:13-16), and any exception in T-P20's own evaluation (missing path, CUDA OOM, Whisper load failure) also exits 1. D-035 classes every exit 1 as "a result … never re-run" (:625-628). A notebook defect in cell (16), which the dry run never exercises (PLAN.md:400-409), therefore becomes a permanent disclosed "T-P20 failed" with no fix path. | integrity; misinterpretation | Medium | low | Exit codes were mapped to meanings without checking the frozen test's failure sources. | DECISIONS.md:625-628, :705-707; tests/python/conftest.py:13-16; test_evaluate.py:34-40; PLAN.md:521-522 | Cell (16) asserts the three environment paths exist before running pytest (failure → `failed: 16`). S-017 classes a failure as a result only when the junit message is one of T-P20's report assertions (the `status`/keys/spread asserts). Otherwise the outcome is `failed: 16`, and the notebook is fixed and re-run. |
| R-100 | **`renderStatus()` turns Ready before the take is playable.** The D-010 hop is: 4-Hz timer notices `latest()` → worker → `callAsync` → publish (:305-311). `Renderer` has no completion callback (render.hpp:35-46). T-058 pumps until `renderStatus()==Ready` (polled at about 20 ms) and then immediately expects audio (test_plugin.cpp:192-196). If `renderStatus()` forwards `Renderer::status()`, which is the natural implementation, T-058 fails almost always. Three attempts → `BLOCKED.md`, or a mistaken `TEST_CHALLENGE.md`. No text defines `renderStatus()` (D-027 :336 only). | technical; misinterpretation; past lessons (PK-76) | Medium | medium | The asynchronous publication added in rounds 3–4 never named which interface reports "playable". | DECISIONS.md:303, :305-311, :336; render.hpp:35-46; PluginProcessor.h `renderStatus`; test_plugin.cpp:26-31, :185-197; R-091 | D-010: `renderStatus()` = `Rendering` while the Renderer is busy **or** the newest worker generation is not yet published; `Ready` only after publish. The timer may also post the worker job directly on detecting `latest()` changes. |
| R-101 | **Queued `callAsync` lambdas outlive the processor.** The destructor "sets the worker's stop flag and joins it before `TakeSlot` is destroyed" (:310-311). A lambda posted before or during the join stays in JUCE's message queue. The processor is destroyed on the message thread, and the lambda runs afterwards to compare generations and publish → use-after-free and a host crash on project close or instance removal. The join also blocks the message thread for an uncancellable `resampleTake` (seconds for long takes). Not exercised: pluginval has no take, and the plugin is not built under TSan/ASan (ci.yml:92-116). | audio thread / lifetime; technical | Medium | low | Join was specified for the thread, not for messages already posted. | DECISIONS.md:270-271, :305-311; take_cache.hpp:25-29; ci.yml:92-116; R-091 | The lambda captures a `std::shared_ptr` to a small hand-off state (generation, `TakeSlot` owner flag) or a `juce::WeakReference`. The destructor marks that state dead before the join, and the lambda does nothing when it is dead. The worker checks the stop flag between resample chunks (process `resampleTake` in ≤ 10-s slices). |
| R-102 | **OwnerAction remedies cannot be carried out on Kaggle, and the loop has no exit.** The stops say "free Drive space, naming earlier runs' `logs/<exp>/`" (:585-586) and "checkpoint unreadable; delete `logs/<exp>`" (:683). On Kaggle the state is an attached read-only `state.tar` that holds every run (:710-711), so neither fix is possible, and Kaggle disk is never researched. `owner-fixed` re-issues are "not counted as an attempt" (GATES.md:64-65), so nothing bounds the loop. The owner's only escape, `RESUME = False`, resets both ledgers (R-068 class). The R-088 copy keeps an extra full copy of the state in `/kaggle/working` all session, which moves the (10a) stop earlier. Owner-fixable stops in unguarded cell (4) (no GPU at (4c), parameters at (4e)) print a traceback, not `owner:`, and the (4e) text "set RUN = <RUN+1>" contradicts "RUN is always the number GATE-G-004.md states" (GATES.md:62). | operational; compute | Medium | low | R-087's remedies were written for Drive; the attempt bound was removed without a replacement. | DECISIONS.md:578-579, :585-586, :618-619, :651-652, :683, :710-711; GATES.md:62-66; R-087; R-088; C-064 | Kaggle-specific OwnerAction texts: "switch to Colab with a new RUN" for disk, and `prune: <exp>` for the checkpoint, which makes the notebook exclude that `logs/<exp>` from the next `pack_state`. Limit `owner-fixed` to two per issue, then `BLOCKED.md`. Cell (3) deletes the copied `state.tar` once (4e) completes. Map (4c) and (4e) stops to `owner:` lines. |
| R-103 | **The GCC 11 compatibility check runs once, at S-010.** D-033 forbids GCC-12+ features because (4f) compiles with the hosted image's compiler. Only S-010 builds with `g++-11` (PLAN.md:267-269). Core edits in S-011…S-019 and CI (GCC 13.3 only) are never re-checked, so a regression first appears as the owner's `failed: 4`. | dependency drift | Low | low | A recurring constraint was verified at a single point. | DECISIONS.md:492-494; PLAN.md:267-269; ENVIRONMENT.md pins; R-023 | Re-run the `../build-gcc11` build in S-016 (before `EXPECTED_COMMIT` is set) and S-019. |
| R-104 | **`training.json` `epochs_trained` can name a snapshot that was not used.** It is "N of the newest `<exp>_e<N>_s<M>.pth`" (:698-699). DR-13 copies the newest snapshot *that loads* (:606-607). A snapshot truncated by the budget kill makes the G-001 evidence ("`training.json` (epochs trained)", GATES.md:16) disagree with `budget.json` `stopped_by_budget`. | numerical; integrity | Low | low | The R-086 change did not propagate to training.json. | DECISIONS.md:606-607, :698-699, :730; GATES.md:16 | `epochs_trained` = `stopped_by_budget` when that is set, else `EPOCHS`. |
| R-105 | **An arm click during `Cancelling`/`CancelAck` is silently lost.** Both states are reported as `Idle` (:282). `arm(true)` CASes `Idle→Armed`, which fails, and "the loser does nothing" (:284). The window lasts up to one timer period. | audio thread; operational | Low | low | Internal states are exposed as Idle without retrying user intent. | DECISIONS.md:280-290; PluginProcessor.h `arm`; R-090 | `arm(true)` in `Cancelling`/`CancelAck` sets a pending-arm flag that the timer applies after storing `Idle`. |
| R-106 | **The capture warning has no carrier on a cache hit or a short-circuited render.** It is "carried into the warnings of the render that capture submits" (:285-286). `RenderFn` and `Renderer` expose no warnings (render.hpp:30-46). `cachedRender` returns the stored take without calling `fn` (take_cache.hpp:23), and `Renderer` skips a request whose hash equals the current take's. A capture that reproduces a cached or current request shows no warning (PK-76). | misinterpretation | Low | low | The behaviour was attached to a path the interfaces cannot express. | DECISIONS.md:245-246, :285-286, :324; render.hpp:30-46; take_cache.hpp:23; R-093 | The message thread appends capture warnings to `lastWarnings()` itself at capture finish. They are cleared at the next capture or import, not by the next render. |
| R-107 | **The S-016 dry-run expectations still need shaping.**<br>• Scenario (2) expects `["render-bin", "evaluate"]` (PLAN.md:401-402). With deterministic fakes, and probably with a deterministic same-commit rebuild (":695 the binary's bytes differ" is UNVERIFIED), evaluate's input hash is unchanged and it is skipped.<br>• Scenario (4)'s fake only raises `SessionEnd`. `STOP` is set only at raise sites (:610, :629), and cells catch `SessionEnd` before `guarded` (:614-617), so `STOP_REASON` stays unset.<br>The real-world effect is nil. | misinterpretation; past lessons | Low | high | R-089's fix wrote expectations against an unverified premise. | PLAN.md:395-409; DECISIONS.md:610, :614-617, :629, :695; R-089 | Scenario (2): the dry run writes a session-specific fake binary and expects evaluate. Otherwise expect `["render-bin"]` and drop the :695 claim. The `SessionEnd` catch sets `STOP` and `STOP_REASON = "start a new session"`. |

---

COUNTS (new + inadequately mitigated round-4 risks): Critical=2 High=2 Medium=5 Low=5

*The counts cover the new risks R-095…R-107 (Critical 1, High 2, Medium 5, Low 5) and the inadequately mitigated R-082 (Critical). R-083 and R-084 are "partially", with their new failure modes given IDs above. R-086 and R-088 are adequate.*
