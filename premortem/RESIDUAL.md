# Residual risks and the owner's decision (protocol Phase 4.6 / Phase 5)

**Plan status: BLOCKED — HUMAN DECISION REQUIRED.** Pre-mortem rounds are exhausted (5 of 5). Critical/High risks remain
whose mitigations exist only as plan text. **Implementation (S-000 onward) must not start until the owner has answered the
decision below** and a planning session has recorded the answer as a decision `D-039` and re-run `tools/gen/status.py`.

## A. Mitigated after the final round, never re-reviewed (the reason for BLOCKED)
These mitigations were written after pre-mortem round 5. No further round or fresh review has checked them. Cold read
pass 10 checked them for executability only and resolved 22 wording and rule gaps (premortem/coldread-pass-10.md).

| Risk | Severity | What could still go wrong | Mitigation in the plan |
|---|---|---|---|
| R-082 | Critical | A Colab↔Kaggle switch restarts training and splits the voice's GPU ledger across two platforms. | `PLATFORM` in `params.json` (a switch is a new RUN); `PLATFORM_EXPECTED` pinned per issue; repository voice ledger `results/<VOICE>/ledger.json` (D-035 §Voice ledger) |
| R-095 | Critical | GPU hours of a session the platform kills are missing from both ledgers, so the A-015 budget is overrun. | heartbeat hours of sessions without `end` are counted; Kaggle versions without a `seq` line are reported as `killed <run time>` and added as `unlogged` (an upper bound) |
| R-097 | High | `PRIOR_VOICE_GPU_HOURS` double-counts or misses hours. | PRIOR = ledger `total` − the ledger's hours for this platform; per-session `prior` checked by S-017 |

All three concern **GPU-hour accounting across platforms and killed sessions**. The worst case is a voice training past
A-015's 20 GPU-hours, or stopping early, on the owner's free quota. No data is lost or exposed, and nothing is published.

## B. Open with a planned control, proven only during implementation or the owner's run
These were found in rounds 1–4 and re-examined in later rounds. Each control is specified, but its proof is a test, the
S-016 dry run or the G-004/G-001 evidence, so it cannot be `mitigated` before implementation (register definition).
Critical: R-013, R-015, R-019, R-020, R-034, R-035, R-051, R-057, R-068. High: R-007, R-014, R-016, R-022, R-024, R-025,
R-026, R-052, R-055, R-059, R-060, R-069, R-070, R-083, R-086, R-088. Rows, mitigations and traces: premortem/RISK_REGISTER.md.

## Decision needed from the owner (answer one)
1. **`accept`** — accept R-082, R-095 and R-097 with the mitigations above (register status → `accepted`). Group B
   proceeds under its planned controls. The plan becomes READY.
2. **`review`** — authorise one extra pre-mortem round plus a cold read restricted to D-035 §Time and budget, §Voice
   ledger, plan/GATES.md G-004 and S-017 (a planning amendment, HANDOFF §Amendments). Status stays BLOCKED until that round
   ends with no Critical/High finding.
3. **`colab-only`** — drop the Kaggle notebook and every Kaggle rule (switch-platform, `state.tar`, version lines,
   `unlogged` hours). PRIOR is then always 0 and R-082/R-097 no longer apply. R-095 reduces to the Colab heartbeat bound,
   at most 5 minutes per killed session. The cost: no fallback when Colab's free GPU is unavailable (R-001). This is a
   planning amendment, followed by cold read and pre-mortem on the changed items.

Medium/Low residuals (for information): see the register (status `open`); R-108 (de-reverb venv conflict) was found and
mitigated in cold read pass 10.
