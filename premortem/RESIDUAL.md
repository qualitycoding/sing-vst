# Residual risks and the owner's decision (protocol Phase 4.6 / Phase 5)

**Plan status: READY.** The owner answered "Accept" on 2026-10-22 (plan/DECISIONS.md D-040): R-082, R-095 and R-097 are
accepted with the mitigations below; section B proceeds under its planned controls. The record below is kept as the
history of the decision.

## History
- After pre-mortem round 5 (the protocol's last), R-082, R-095 and R-097 had mitigations nobody had reviewed. The owner
  chose `review` (D-039).
- **Round 6** (premortem/round-6.md) traced eight GPU-hour scenarios with numbers. It rated R-082 and R-095 **inadequate
  (Critical)**: a switch after a re-issue could report 0 h and wipe a platform's figure; a Colab session killed during
  training and then switched lost up to ~9.5 h; killed Kaggle hours were not enforced within an issue. It rated R-097
  partially adequate and added R-109…R-115 (Medium/Low). D-039's condition ("no Critical or High finding") was therefore
  **not met**.
- All round-6 findings were fixed (D-035 §Time and budget, §Voice ledger; GATES G-001/G-004; S-016 scenarios (7)–(10);
  S-017). The main changes:
  - Ledger figures come from a file or a fixed notebook line, never from memory. On Colab that file is Drive's
    `budget-voice.json`, which includes the heartbeats of a killed session.
  - A platform's figure can never decrease or be overwritten by 0.
  - `KILLED_HOURS` enters the notebook's budget stop within an issue.
  - The voice ledger and any overrun are shown at G-001.
  - The budget stop has its own path (`BudgetStop`).
  - `PRUNE` is one-shot.
  - The retrain bound includes per-run overhead.
- Four cold-read passes (11–14; premortem/coldread-pass-11…14.md) checked the rewritten rules. Each pass found fewer
  items: 25, 26, 7, then 8 (3 of those false positives; the rest fixed). Pass 14 worked five scenarios end to end and found
  the numbers consistent:
  - Colab killed mid-train, then a switch to Kaggle.
  - A killed Kaggle version followed by an upload.
  - `failed:` followed by a switch.
  - A prune followed by two versions.
  - `budget-exhausted` followed by `raise-budget-to`.

  Cold reads check that the plan can be executed. They are not a pre-mortem, so no adversarial review has checked the
  round-6 fixes.

## A. Residual Critical/High risks (accepted by the owner, D-040)
| Risk | Severity | What could still go wrong | Mitigation now in the plan |
|---|---|---|---|
| R-082 | Critical | A Colab↔Kaggle switch splits or resets the voice's GPU-hour ledger, so A-015's 20 h is silently exceeded. | per-issue ledger records set from file-sourced, never-decreasing figures; record `platform` = the issue's platform; `PRIOR` = ledger total − own platform |
| R-095 | Critical | Hours of killed sessions are missing from the ledger. | Colab: Drive `budget-voice.json` (≤ 5 min lost); Kaggle: `killed` lines as upper bounds, `KILLED_HOURS` enforced in-issue, 12 h when the run time is unknown; overrun shown at G-001 |
| R-097 | High | `PRIOR_VOICE_GPU_HOURS` is wrong. | derived from the ledger above, with 4-decimal round-up held as integers; checked per session by S-017 |

All three concern **GPU-hour accounting on the owner's free quotas**. The worst remaining case is that A-015's 20-hour
budget is over- or under-run. No data is lost or exposed, and nothing is published.

## B. Open with a planned control, proven only during implementation or the owner's run
Unchanged by round 6. Critical: R-013, R-015, R-019, R-020, R-034, R-035, R-051, R-057, R-068. High: R-007, R-014,
R-016, R-022, R-024, R-025, R-026, R-052, R-055, R-059, R-060, R-069, R-070, R-083, R-086, R-088. See
premortem/RISK_REGISTER.md.

## Decision offered to the owner (answered `accept`, D-040)
1. **`accept`**: accept R-082, R-095 and R-097 with the round-6 fixes; the register status becomes `accepted`, and the
   plan becomes READY.
2. **`review`**: authorise pre-mortem round 7 on the round-6 fixes only (same scope as D-039). Status stays BLOCKED until
   a round ends with no Critical or High finding.
3. **`colab-only`**: drop the Kaggle notebook and every Kaggle rule (switch-platform, `state.tar`, version lines,
   `KILLED_HOURS`, `PRUNE`). This removes every scenario in which round 6 found a Critical problem. Colab's
   killed-session case was already adequate in round 6 (trace T3). The cost is that there is no fallback when Colab's free
   GPU is unavailable (R-001). It is a planning amendment, followed by a cold read on the removal.

Medium/Low residuals: premortem/RISK_REGISTER.md (status `open`); R-108…R-115 are mitigated in the text.
