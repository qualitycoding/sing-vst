# Pre-mortem: round 6 (Phase 4, extra round authorised by D-039)

**Scope.** I reviewed branch `gen-20261004T095012Z-singing-voice-vst-pitch-lyrics` (HEAD `891eca8`) read-only. I changed, built and ran nothing, and used no network. The review covers only the GPU-hour accounting (D-039, plan/DECISIONS.md:905-910). I read:
- plan/DECISIONS.md D-035 (:533-857) and D-039
- plan/GATES.md G-001 and G-004
- plan/PLAN.md S-016 (:392-443) and S-017 (:445-512)
- HANDOFF.md §Amendments (:105-116)
- premortem/RESIDUAL.md
- premortem/RISK_REGISTER.md, the named rows plus R-102 and R-104
- premortem/round-4.md and premortem/round-5.md
- plan/PROTOCOL_EXCERPTS.md Rule 4
- plan/ASSUMPTIONS.md A-015
- python/singvst_train/pipeline.py (`run_stages` docstring)
- tests/python/test_notebooks.py
- research/claims.json C-017, C-019, C-064

I did not read the coldread-pass files. Severities follow Rule 4 for the `software` and `computational` profiles. Anything that could not be checked offline is marked UNVERIFIED.

**Mechanics used in every trace (current text).**
- **Notebook enforcement.** The voice total the notebook enforces is `PRIOR_VOICE_GPU_HOURS + Σ runs` of this platform's `budget-voice.json` (DECISIONS.md:813-814). The budget term of the train timeout is `t_budget = BUDGET_HOURS − 1 − total` (:659-662). The notebook prints `hours: platform <p> voice <v>` only before each stage and in cell (17) (:814-815). The heartbeat writes files every 5 minutes but prints nothing (:828-832).
- **Owner's figure.** A response's `hours-used` is the `p` of the last line printed (GATES.md:73-74).
- **Voice ledger.** S-017 sets one record per issue (`run<RUN>.<k>`). `colab` and `kaggle` are each the `platform_hours` of the newest record on that platform (set, never summed). `unlogged` = Σ `killed_hours`; `total` = the sum of the three (DECISIONS.md:817-828).
- **PRIOR.** `PRIOR` = `total` − the ledger value for `PLATFORM_EXPECTED` (PLAN.md:458-459).
- **S-017 checks.** Only a `consent:` response has an upload, so the seq-chain, prior and budget-sum checks run only then (PLAN.md:470-485).

Notation: "true" means the GPU hours actually consumed. Values are illustrative, not measured. `BUDGET_HOURS` is 20 unless stated.

---

## 1. Scenario traces

### T1. Colab → `switch-platform` to Kaggle → killed Kaggle version → `failed:` re-issue → upload → retrain
| Step | Notebook (`t_budget`, printed lines) | Ledger after the response | Next PRIOR | S-017 |
|---|---|---|---|---|
| run1.1 Colab, PRIOR 0. S1: f0+features 0.4 h; train `t = min(8.6, 18.6)` = 8.6 → rc 124 → `SessionEnd`; (17) prints `platform 9.0000 voice 9.0000` | — | `switch-platform: kaggle, hours-used: 9.0` → run1.1 {colab, prior 0, 9.0}; colab 9.0, kaggle 0, unlogged 0, total 9.0 | Kaggle: 9.0 − 0 = 9.0 | no upload |
| run2.1 Kaggle, PRIOR 9.0. v1: `RESUME=False`, seq 1, f0+features 0.3; `t = min(8.6, 19 − 9.3 = 9.7)` = 8.6; (17) prints `platform 8.9000 voice 17.9000`, `seq 1 state.tar AAA` | | | | |
| v2: restores AAA, seq 2; `t_budget = 19 − 17.9 = 1.1`; killed by the weekly quota 0.7 h into train; panel `0h 52m 0s`; v2's heartbeat 9.6 is lost | | | | |
| v3: restores AAA (v2's R-088 copy or v1); seq 2; `t_budget` still 1.1 (**v2's 0.7 h unseen**) → binds → DR-13 copies e130 → export parity fails → guarded `failed: 12`; (17) prints `platform 10.1000 voice 19.1000`, `seq 2 state.tar BBB` | | `failed: 12 …, hours-used: 10.1` + `seq 1 AAA` / `killed 0h 52m 0s` / `seq 2 BBB` → run2.1 {kaggle, prior 9.0, 10.1, versions […, {killed_hours 0.8667}, …]}; total 9.0 + 10.1 + 0.8667 = 19.9667 | 19.9667 − 10.1 = 9.8667 | no upload |
| run2.2 (same RUN). v4: restores BBB, seq 3; export, pack, evaluate, T-P20 = 0.9 h; (17) prints `platform 11.0000 voice 20.8667`; upload; `seq 3 CCC` | | `consent:` → run2.2 {kaggle, prior 9.8667, Σ runs of upload = 11.0}; total 9.0 + 11.0 + 0.8667 = **20.8667** | — | Passes: seqs 1, 2, 3 consecutive (killed line skipped); `restored_from` null/AAA/BBB; priors 9.0 (run2.1) and 9.8667 (newest = run2.2); `gpu_hours` = Σ sessions |
| G-001 `retrain`? `h10` = (8.6 + 1.1)/13 = 0.746 → 21.6 ≥ 19 → refused | | | | |

**Result.** True ≈ 9.0 + 8.9 + 0.7 + 1.2 + 0.9 = 20.7 h. The ledger's 20.87 h is a valid upper bound and nothing is dropped. However, A-015 was exceeded by about 0.7 h because v3's `t_budget` could not see v2's killed hours, which reach `PRIOR` only at the next issue. GATE-G-001.md shows only run2's `budget.json` 11.0 h "lower bound" (GATES.md:15). The voice total and the overrun appear nowhere in the gate evidence → R-095 (b), (c).

### T2. Kaggle-first via `switch-platform` with `hours-used: 0`
- run1.1 Colab, PRIOR 0. The owner answers `switch-platform: kaggle, hours-used: 0` before running (PLAN.md:456-457).
- The record run1.1 is {colab, 0, 0}; every total is 0. RUN 1 stays unused (DECISIONS.md:586-588), and the gate file is archived as `GATE-G-004.run1.1.md`.
- run2.1 Kaggle, PRIOR 0: seq 1, `restored_from` null, `t_budget` = 19 − Σ runs. At consent, kaggle = Σ runs of the upload. The package is `myvoice-run2`, in `results/myvoice/run2/`.
- **Correct:** 0 is literally Colab's Σ runs here, because no Drive file exists.

### T3. Colab session killed between heartbeats, continued on Colab
- S1: f0+features 0.4 h; train 6.0 h. The last heartbeat comes 5.95 h into train (6.35 h recorded); the runtime is reclaimed at 6.03 h.
  - `budget.json` S1 = {`gpu_hours` 6.35, `end` null}; `budget-voice` {1: 6.35}.
- S2: Σ runs 6.35 → `t_budget` 12.65; train 5.0 h reaches 200 epochs; export, evaluate and T-P20 take 0.9 h.
- Upload `gpu_hours` = 6.35 + 5.9 = 12.25 (true 12.33). The 2a sum check passes, and S1 is listed without `end` (PLAN.md:484-485). The ledger record run1.1 is {colab, 0, 12.25}.
- **Adequate** (R-034: loss ≤ 5 min).
- But `h10` uses Σ `stage_hours["train"]`, and no text makes the heartbeat write `stage_hours` for a running stage (DECISIONS.md:811-813, :828-832). Two readings result:
  - S1's train hours are omitted: `h10` = 5.0/20 = 0.25.
  - They are included: (5.95 + 5.0)/20 = 0.55.
- At a ledger total of 18.6, `retrain` is allowed (18.85 < 19) when it should be refused (19.15) → T6 dead end → R-109.

### T4. Colab session killed *during train*, then `switch-platform` (the documented fallback)
| Step | Notebook | Ledger | Next PRIOR |
|---|---|---|---|
| run1.1 Colab. S1: f0+features 0.4 h; before train it prints `platform 0.4000 voice 0.4000`; train 7.0 h → runtime reclaimed. Drive `budget-voice` {1: 7.35} (heartbeat). S2: no GPU → (4c) `owner:` stop, **no `hours:` line** | — | `switch-platform: kaggle, hours-used: 0.4` (the last line printed, GATES.md:73-74) → run1.1 {colab, 0.4}; total 0.4 | Kaggle: 0.4 |
| run2.1 Kaggle. v1: `t_budget` = 19 − 0.7 = 18.3 → train 8.6; v2: train 6.4 to e200, plus 0.9 eval → Σ runs 16.2 | | `consent:` → kaggle 16.2; total **16.6** | |
| G-001 `retrain`: 16.6 + 0.75 < 19 → allowed. run3 Kaggle, PRIOR 0.4: `t_budget` = 19 − 0.4 − 16.5 = 2.1 → e20 → DR-13 | | total 19.9 | |

**Result.** True ≈ 7.4 + 16.2 + 3.3 = 26.9 h against a ledger total of 19.9 h, an overrun of 35 %. Every S-017 check passes: the run3 prior 0.4 equals the issued prior, the seq chain holds and the sums agree. **Silent.** Drive's correct 7.35 is read by no one, because a switch has no upload → **R-095 inadequate**.

### T5. `failed:` (or `owner-fixed:`) re-issue, then `switch-platform` "instead of running (0 when no session has run)"
- run1.1 Colab:
  - S1 is 9.0 h.
  - S2 fails at cell (12) as a guarded `failed:`; (17) prints `platform 9.1000`.
  - Response: `failed: 12 …, hours-used: 9.1` → run1.1 {colab, 9.1}; total 9.1.
- run1.2 (the re-issue, RUN 1, PRIOR 9.1 − 9.1 = 0). Colab has no GPU. The owner applies GATES.md:67-68 Q3 literally: `switch-platform: kaggle, hours-used: 0`, since no session has run in this issue. S-017 1a's "answers `switch-platform: kaggle, hours-used: 0` before running" (PLAN.md:456-457) reads the same way.
  - Record run1.2 is {colab, 0}. **colab = the newest Colab record = 0; total = 0.**
- run2.1 Kaggle, PRIOR 0 − 0 = 0. Kaggle may spend the full 20 h: true ≤ 29.1 h, ledger ≤ 20 h.
- S-017: the prior check passes (0 = issued), the chain holds, the sums agree. Silent.
- The same happens from Kaggle after a `prune:` or `owner-fixed:` re-issue: kaggle is set to 0 → **R-082 inadequate**.
- A variant: if S-017 records `platform` from the response's own platform word (`kaggle`), the 9.1 h is filed under kaggle. PRIOR for Kaggle is then 0, and the first Kaggle record overwrites it → R-111.

### T6. `budget-exhausted` → `raise-budget`
- Run 1 (Colab) is complete with total 17.5 and `h10` = 12.0/20 = 0.6. `retrain` is allowed (18.1 < 19) with twice the recordings.
- run2.1 Colab, PRIOR 17.5 − 17.5 = 0.
  - f0+features 0.8 h → `platform 18.3000`; `t_budget` = 19 − 18.3 = 0.7 → rc 124.
  - The first snapshot of `myvoice-run2` would land at about 1.2 h (twice the data), so none exists → `budget: no checkpoint` (DECISIONS.md:663-666).
  - (17) prints `platform 19.0000`. Response: `budget-exhausted, hours-used: 19.0` → run2.1 {colab, 0, 19.0}; total 19.0.
- GATE-G-001.md offers only `stop` or `raise-budget` (GATES.md:83-86). Run 1's evaluated voice cannot be accepted with `proceed`. `stop` skips S-018 and S-019, so there is no README and no pull request (GATES.md:7-8) → R-110.
- `raise-budget: 22` → amendment (HANDOFF.md:112-116) → `BUDGET_HOURS` 22 → run2.2 for the same RUN, PRIOR 19 − 19 = 0 → `t_budget` = 21 − 19 = 2.0 → e10 at 1.2 h → DR-13 → total 21.9.
  - S-017 accepts: the priors are 0 and 0, matching run2.1 and run2.2. The retrain bound 21.9 + `h10` ≥ 21 refuses another retrain.
- **The accounting is correct.** Residuals:
  - R-086 partially: the bound uses the previous run's `h10` and leaves out the new run's f0/features time.
  - R-110.
  - R-114: "raise-budget: 2" read as the new total.

### T7. A re-entered response
- run2.1 Kaggle: `failed: 11 …, hours-used: 8.9` with `seq 1 AAA` → kaggle 8.9. run2.2 is issued with PRIOR = colab 9.0.
- The owner re-enters the run2.1 response, adding a forgotten `killed 0h 52m 0s` line. S-017 **replaces** run2.1 (DECISIONS.md:819-821) → unlogged 0.8667, total 18.7667. No double count.
- Sessions already run under run2.2 record prior 9.0, which equals run2.2's issued prior, so the prior check passes. The 0.8667 h enters PRIOR only at the next issue (same in-issue gap as T1).
- A `consent:` that is re-asked after a failed 2a check also replaces its record. **Set-not-add is sound.**

### T8. `prune:` on Kaggle
- run2.1: v2 (seq 2) finds G, D and their `.bak` unreadable → `owner:` "answer `prune: myvoice-run2`" → guarded. (17) packs state and prints `platform 9.3000` and `seq 2 BBB`.
- run2.2 sets `PRUNE="myvoice-run2"` (PLAN.md:460).
- v3: `restore_state` skips `logs/myvoice-run2/`.
  - `run_stages` finds rvc-preprocess's outputs missing and reruns it and every later stage, rvc-f0 and rvc-features included (pipeline.py:27-30).
  - Train restarts from the pretrained model; `t_session` binds after 8.6 h.
  - **`pack_state` excludes `logs/myvoice-run2/`** (DECISIONS.md:608-610), so v3's restarted experiment is discarded.
- v4 has the same Parameters (`PRUNE` still set) and restarts again; so does every later version.
- After two versions `t_budget` binds → DR-13 → `stopped_by_budget` ≈ 120 < `EPOCHS` 200.
- The hours are all counted and the ledger is correct. About 9 h of budget is burned with no progress, and nothing reports it, because restart detection runs only "in a session that started with a checkpoint" (:763-767) → R-112.

---

## 2. Residual audit

| Risk | Verdict | Reason (file:line) |
|---|---|---|
| R-082 | **inadequate** (Critical) | The ledger fixes the location split: platform hours are set from cumulative per-platform figures (DECISIONS.md:817-828), and PRIOR = total − own platform (PLAN.md:458-459). T1 and T2 balance. But the departing platform's figure in a `switch-platform` response can legitimately be 0. GATES.md:67-68 Q3 says "instead of running (0 when no session has run)", and PLAN.md:456-457 says the same. In a re-issue (`failed:`, `owner-fixed:`, `prune:`) no session has run *in this issue*. Set-not-add (DECISIONS.md:825-826) then replaces the platform's whole cumulative figure with 0 (T5). That conflicts with the general rule "the last … line the notebook printed" (GATES.md:73-74). No S-017 check sees it, because there is no upload (PLAN.md:470-485). Effect: a silent undercount of everything already used on that platform, and a matching A-015 overrun. **Fix:** (1) Replace Q3's parenthesis with: "`hours-used` = the `platform` value of the last `hours:` line printed on this platform for this voice in any issue; 0 only when this platform has never printed one". GATE-G-004.md states the ledger's current figure for `PLATFORM_EXPECTED` as the value to give when nothing ran in this issue. (2) S-017 asks again (twice, then `BLOCKED.md`) when a Colab figure is below the previous Colab record, since Colab's Σ `runs` never decreases. (3) Adopt the R-095 (a) attachment and the R-111 definition. |
| R-095 | **inadequate** (Critical) | Fixed: budget sums count heartbeat hours (DECISIONS.md:684-685; PLAN.md:484-485). Kaggle `killed` lines go into `unlogged` (GATES.md:69-73; DECISIONS.md:826-827). T1 and T3 balance. Not fixed:<br>**(a)** A Colab session killed during a stage leaves its hours only in Drive's `budget-voice.json`. The last printed line predates the stage (DECISIONS.md:814-815), and a `switch-platform` has no upload. So the ledger's colab figure drops up to one session's train time (about 9.5 h) and the other platform's PRIOR is too low (T4). The kill-then-switch sequence is the most likely reason to switch (R-001, R-002; C-017).<br>**(b)** Killed Kaggle hours reach `PRIOR` only at the next issue (DECISIONS.md:610-612). Within the issue, `t_budget` ignores them (T1: +0.7 h). The overrun is bounded by the killed hours, up to about 9.5 h per killed version.<br>**(c)** G-001 evidence shows only the run's `budget.json` (GATES.md:15), never the ledger total, so an overrun is not shown to the owner.<br>**(d)** The `killed <run time>` value rests on an unresearched Versions-panel field (UNVERIFIED; C-019 and C-064 do not cover it).<br>**Fix:**<br>(a) Every Colab response without an upload (`switch-platform`, `failed:`, `owner-fixed:`, `budget-exhausted`) attaches `MyDrive/singvst/<VOICE>/budget-voice.json`, which can be downloaded without a runtime. S-017 sets `platform_hours` = Σ `runs` of that file (as for `consent:`), checks it is ≥ `hours-used`, and records its SHA-256.<br>(b) Kaggle Parameters gain `KILLED_HOURS` = Σ of this issue's `killed` run times so far, which the owner updates after each killed version. `t_budget` uses PRIOR + `KILLED_HOURS` + Σ runs. `start_session` records it, and S-017 checks each session's value against the killed lines before its seq line.<br>(c) GATE-G-001.md shows the ledger (colab, kaggle, unlogged, total) and "A-015 exceeded by x h" when total > `BUDGET_HOURS`.<br>(d) Add a claim for the panel's run-time display; where it shows none, use 12 h (Kaggle's session limit) as the upper bound. |
| R-097 | partially | Fixed: the same-platform double count is gone. In the round-5 trace, PRIOR after a Colab retrain is 12 − 12 = 0, and the notebook adds its own Σ runs once. The source is defined (PLAN.md:458-459), and S-017 checks the recorded `prior` (PLAN.md:483-484; T1 and T6 pass). Residuals:<br>(i) PRIOR is only as right as the ledger, so it inherits R-082 and R-095 (a) (T4, T5).<br>(ii) A conservative double count. When a Kaggle version is later reported `killed`, its last printed line (e.g. before export, after a 9-h train) can be the `hours-used` figure. Its hours are then in both `kaggle` and `unlogged`, so after a switch the Colab PRIOR is overstated by up to about 9 h and training stops early. This is an over-count only, so its severity is Low.<br>**Fix for (ii):** for Kaggle, `hours-used` = the cell-(17) `hours:` line of the last version that printed a `seq` line (equal to Σ runs of the `state.tar` it packed), never a line from a version reported as `killed`. |
| R-083 | adequate | `seq <n> state.tar <sha>` is printed after `pack_state` (DECISIONS.md:635-637, :725-726). The chain is checked over every Kaggle record's lines plus this response's (PLAN.md:478-483). The R-088 copy keeps `restored_from` consistent after a killed version (T1). Residual, Low, no ID: lines of non-upload responses are only checked at a later Kaggle `consent:`. A kill between `pack_state` and the final print (seconds) breaks the chain loudly (`BLOCKED.md`), not silently. |
| R-086 | partially | Fixed: DR-13 copies the newest loadable snapshot, and with none the outcome is `budget-exhausted` (DECISIONS.md:663-666; GATES.md:83-86). New failure modes:<br>• The retrain bound `gpu_hours + h10 < BUDGET_HOURS − 1` (GATES.md:28-32) leaves out the new run's rvc-f0 and rvc-features hours. It also uses the previous run's `h10` after a data change (T6).<br>• `h10` depends on undefined `stage_hours` for killed sessions → R-109.<br>• The dead end then has no `proceed` → R-110.<br>**Fix (bound):** `gpu_hours + h_pre·r + h10·r < BUDGET_HOURS − 1`, where `h_pre` = the previous run's Σ rvc-f0 + rvc-features hours and `r` = new train-set minutes ÷ old (from `split.json` of both runs; the owner states the new count in the `retrain` response). |
| R-096 | adequate | `seq` = 1 + max over `<root>/run*/out/budget.json` (DECISIONS.md:722-725) counts per platform across RUNs and issues. S-017 matches it against all records' lines (PLAN.md:478-483). T1 (one issue), a Kaggle retrain (new RUN) and a return to Kaggle after Colab (`RESUME=True`, seq continues) all check cleanly. |
| R-102 | partially | Kaggle-specific owner texts and the two-per-issue bound are present (DECISIONS.md:624-625, :760-761; GATES.md:79-82). New failure mode: `PRUNE` persists for every version of the re-issue, and `pack_state` discards the restarted experiment → R-112. |
| R-034 | adequate | A Colab kill loses ≤ 5 min in `budget.json` and `budget-voice.json` (T3; DECISIONS.md:828-833). The repository ledger's copy of those hours is R-095 (a). |

---

## 3. Lenses

**Technical correctness.**
- R-112: `PRUNE` makes every version restart, because `pack_state` drops the restarted experiment.
- R-110: a retrain that dead-ends in `budget-exhausted` leaves no path to `proceed`.
- Checked and sound:
  - the `seq` derivation on both platforms;
  - the R-088 copy keeping `restored_from` consistent after a killed or (3)/(4)-failed version;
  - the `t_budget` formula with PRIOR = total − own platform;
  - `BUDGET_HOURS` changed in both notebooks before the same-RUN re-issue;
  - `PLATFORM_EXPECTED = ""` stopping in cell (3) before anything is written. Its only cost is a `killed` line of a few minutes on Kaggle, which is an over-count.
- Archive names `GATE-G-00<g>.run<RUN>.<k>.md` are deterministic, so a record's `issue` key equals the later archive name whether the file is archived at the G-001 write or the next G-004 write.

**Implementer misinterpretation.**
- R-111: the record's `platform` is undefined for `switch-platform`.
- R-109: whether the heartbeat writes `stage_hours`.
- R-114: `raise-budget: <hours>` could mean "by" or "to".
- Owner-side: Q3's "0 when no session has run" against GATES.md:73-74 (R-082).

**Integrity (Rule 9).**
- For every response without an upload, the ledger's colab and kaggle figures are transcribed by hand from a printed line (GATES.md:73-74), not generated from a file. That is the root of R-082 and R-095 (a): Drive holds the correct number, but no step reads it. The R-095 (a) fix makes the Colab figure come from a file.
- R-113: `stop` leaves the committed ledger short.
- Positives: the ledger totals can be recomputed from the per-issue records; re-entry replaces records; gate history is archived.

**Operational realities.**
- Colab reclaim followed by no GPU, then a switch, is the expected path to Kaggle (T4, R-095).
- The Kaggle quota kill and the panel's run-time format are unresearched (R-095 (d)).
- R-115: the upload fallback branch name collides on a re-request.
- `owner:` stops in cells (3)–(4) print no `hours:` line. That matters only through R-082 and R-095.

**Compute budget.**
- R-095 (b): in-issue killed Kaggle hours are not enforced.
- R-095 (a) and R-082: silent undercounts after a switch.
- R-112: the remaining budget burned after a prune.
- R-109 and R-086: retrains are allowed that cannot fit.
- R-097 (ii): conservative over-count.

**Reproducibility.**
- Nothing new in scope beyond R-109.
- `BUDGET_HOURS` is not recorded per session, but each session's `commit` (DECISIONS.md:617) pins the cell-(3) value, and the archived gate files keep each issue's PRIOR and Parameters.
- The ledger's "newest record" depends only on the committed `issues` order.

---

## 4. Risk table (new risks)

| ID | Description | Lens | Severity | Likelihood | Root cause | Traces to | Proposed mitigation |
|---|---|---|---|---|---|---|---|
| R-109 | **`stage_hours` of a session killed mid-stage is undefined, so `h10` is understated.** `stage_hours` is "the wall-clock hours of each GPU-time stage … whose sum is the session's `gpu_hours`" (DECISIONS.md:811-813). The heartbeat writes only "the running session's GPU time" (:828-832). If `stage_hours["train"]` is written at stage end, a Colab session killed during train keeps its epochs (checkpoints on Drive) but loses its train hours from Σ `stage_hours["train"]`. `h10` (GATES.md:30-32) is then understated: 0.25 instead of 0.55 in T3. `retrain` is allowed when 10 more epochs do not fit, and the run dead-ends in `budget: no checkpoint` (R-110). S-017 never checks Σ `stage_hours` = `gpu_hours` (PLAN.md:472). | compute; misinterpretation | Medium | low | The `stage_hours` field was added without stating the heartbeat's duty for it. | DECISIONS.md:811-813, :828-832; GATES.md:28-32; PLAN.md:472; R-086 | The heartbeat writes the running stage's elapsed time into `stage_hours` on every beat. S-017 2a checks Σ `stage_hours` = `gpu_hours` per session (tolerance 1e-6). |
| R-110 | **A retrain that ends in `budget-exhausted` dead-ends the delivery.** After `budget: no checkpoint`, GATE-G-001.md offers only `stop` and `raise-budget` (GATES.md:83-86). When an earlier run of the voice was already evaluated (the G-001 `retrain` case), the owner cannot accept it. `stop` skips S-018 and S-019, so there is no README and no pull request (GATES.md:7-8), and `raise-budget` needs a full planning amendment (HANDOFF.md:107-116). Reached through R-109, or through the R-086 data-change gap (T6). | compute; operational | Medium | low | The `budget-exhausted` gate was written for the first run only. | GATES.md:7-8, :28-33, :83-86; HANDOFF.md:107-116; DECISIONS.md:663-666 | When an evaluated earlier run exists, the `budget-exhausted` GATE-G-001.md also offers `proceed` and `proceed-with-thresholds` for the newest evaluated run (named `run<R'>`), with that run's evidence and a note that run R was cut by the budget. |
| R-111 | **A ledger record's `platform` is undefined for `switch-platform`.** The record lists `"platform"` without a definition (DECISIONS.md:821-823). A `switch-platform: kaggle, hours-used: 9.0` response names the target platform, while the figure belongs to the departing one (GATES.md:73-74, :87-88). Filing it under `kaggle` gives colab 0, kaggle 9.0 and Kaggle PRIOR = total − kaggle = 0. The first real Kaggle record then overwrites 9.0, so the Colab hours vanish silently (T5 variant). | misinterpretation; compute | Medium | low | A field is named without a source while a homonymous value sits in the response. | DECISIONS.md:817-828; GATES.md:73-74, :87-88; PLAN.md:456-459; R-082 | Define `platform` = the issue's `PLATFORM_EXPECTED` (the platform whose notebook printed the figure), and record the target in a separate `switch_to` field. |
| R-112 | **`PRUNE` restarts training in every version of the re-issued issue.** `PRUNE` is a Parameters value of the whole re-issue (PLAN.md:460; DECISIONS.md:608-610). Every version's `restore_state` skips `logs/<PRUNE>/`, and every `pack_state` excludes it, so the restarted experiment is discarded at each version's end. `run_stages` then reruns rvc-preprocess through train (pipeline.py:27-30), and restart detection is skipped because no session "started with a checkpoint" (DECISIONS.md:763-767). Any run needing more than one session burns the remaining voice budget at about one session's progress (T8). Hours are fully counted and labelled `stopped_by_budget`. | technical; compute | Medium | low (conditionally high) | The exclusion was written for one `pack_state` ("the next", :760-761) but attached to a per-issue parameter. | DECISIONS.md:608-610, :760-767; PLAN.md:460; pipeline.py:27-30; R-102 | Make `PRUNE` one-shot: `restore_state` skips `logs/<PRUNE>/` only when `<run>/state/pruned-<PRUNE>` is absent, then writes that marker. `pack_state` always packs `logs/`. Add an S-016 dry-run scenario of two consecutive versions with `PRUNE` set. |
| R-113 | **`stop` at G-004 leaves the committed ledger short.** "`stop` (the ledger is not changed)" (GATES.md:92; DECISIONS.md:819-820). The hours of the stopped issue (Colab sessions since the last response, Kaggle versions of this issue) are never recorded. A first-issue `stop` after 15 h leaves no ledger file at all, which "means all four 0". | integrity | Low | low | `stop` was given no figure because it ends delivery. | GATES.md:92; DECISIONS.md:819-820 | `stop` at G-004 optionally carries `hours-used` and the version lines. S-017 records them when present; otherwise S-RETRO notes that the ledger omits the stopped issue. |
| R-114 | **`raise-budget: <hours>` does not say whether the value is a new total or an increase.** GATE-G-001.md shows `raise-budget: <hours>` (GATES.md:85). Only HANDOFF.md:112 says "to the new value". "raise-budget: 2" meant as "+2" makes `BUDGET_HOURS` 2, and the re-issue stops again with `budget: no checkpoint`. | misinterpretation | Low | low | The response syntax was not self-describing. | GATES.md:83-86; HANDOFF.md:112-116 | Rename it `raise-budget-to: <total hours>`. The amendment rejects a value ≤ ledger total + 1. |
| R-115 | **The upload fallback branch name collides on a re-request.** The owner uploads to "a new branch `upload-<VOICE>-run<RUN>`" (GATES.md:55-58; PLAN.md:465-468). A failed 2a check re-asks for the files for the same RUN (PLAN.md:486-487), and that branch already exists and is never deleted. The owner must improvise (commit to the existing branch), and a wrong guess makes the SHA check fail twice → `BLOCKED.md`, delaying the `consent:` record. | operational | Low | low | A one-shot channel was used for a retried action. | GATES.md:55-58; PLAN.md:465-468, :486-487 | A re-request names `upload-<VOICE>-run<RUN>-<n>` (n = attempt), or says "commit to the existing branch". The implementer fetches the commit whose tar matches the pasted SHA. |

---

COUNTS (new + inadequately mitigated): Critical=2 High=0 Medium=4 Low=3

*How the counts are made:*
- *Critical: R-082 and R-095, both inadequate and both silent undercounts with an A-015 overrun of up to about 9.5 h after a platform switch.*
- *Medium: R-109, R-110, R-111, R-112. Low: R-113, R-114, R-115.*
- *R-086, R-097 and R-102 are rated "partially" and are not counted. Their new failure modes carry IDs R-109, R-110 and R-112, except R-097 (ii), a conservative Low over-count that the R-097 fix in section 2 removes.*
- *R-083, R-096 and R-034 are adequate.*
- *Because Critical findings remain, D-039's condition for leaving BLOCKED is not met by this round.*
