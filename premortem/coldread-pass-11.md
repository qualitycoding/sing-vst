# Cold read pass 11 (D-039 scope: GPU-hour accounting) — 2026-10-21, fresh clone at 891eca8

Run in parallel with pre-mortem round 6 (premortem/round-6.md); fixes for both were applied together at de41850.

## Haiku (mechanical) — 5 items
| ID | Item | Resolution |
|---|---|---|
| H1 | T-059 has no TEST_CASE | by design: CI-only pluginval step (D-023, D-036); TRACEABILITY says so |
| H2 | premortem/round-6.md missing | written by round 6 (committed) |
| H3 | C-064 has no research/ source | single-source web claim, labelled so; no change |
| H4 | cell (16) asserts SINGVST_* exist without setting them | cell (16) sets the three paths, then asserts they exist (9a05b8c) |
| H5 | S-016 calls the consent globals Parameters-cell presets | "every global of cell (2) and the Parameters cell (2a)" (9a05b8c) |

## Sonnet (dry run) — 20 items
| ID | Item | Resolution |
|---|---|---|
| S1 | PRUNE restarts every version | one-shot skip with packed `pruned-<exp>` marker (R-112); dry-run scenario (9) |
| S2 | `budget: no checkpoint` had no raise path | `class BudgetStop`, mapped by `guarded`; dry-run scenario (8) |
| S3 | `hours-used` source wrong/undefined (killed versions, cells (3)/(4), Colab reclaim) | §Voice ledger: Colab = Drive `budget-voice.json` attached; Kaggle = cell-(17) line before newest `seq`; `none` keeps the previous value; never from a killed version |
| S4 | record `platform` undefined for switch | = issue's `PLATFORM_EXPECTED`; `switch_to` separate (R-111) |
| S5 | per-stage hooks had no place; dry run bypasses them | `timed(name, fn)` inside each stage's `run`; dry run replaces the global `sh`, so `timed` runs; injectable `CLOCK`, `HEARTBEAT_INTERVAL`, `heartbeat_write()` |
| S6 | no dry-run scenario exercises accounting | scenarios (7) accounting, (8) budget stop, (9) prune, (10) owner stops |
| S7 | `raise-budget` inconsistent | `raise-budget-to: <total>`, only on the budget-exhausted G-001, > total + 1 (R-114) |
| S8 | retrain bound ignores per-run overhead | `gpu_hours + r·(h_pre + h10) < BUDGET_HOURS − 1`; `raw_minutes` in training.json |
| S9 | ledger vs 2a ordering | consent record after 2a passes; others at once; `unverified` on BLOCKED |
| S10 | attempt counters undefined | per RUN, counted from archived gate files' responses |
| S11 | "parameters changed" had no response; owner lines lacked cell | `owner-fixed: params`; `owner: <cell> <message>` |
| S12 | malformed response = stop | listed keyword with a missing part is re-asked (twice, then BLOCKED); mismatch rule for voice/epochs/dereverb |
| S13 | Kaggle re-import creates a new notebook | attach the newest version with `state.tar` from any of the owner's Kaggle notebooks |
| S14 | PRIOR stale within an issue after a killed version | `KILLED_HOURS` parameter in `t_budget`, recorded per session and checked |
| S15 | which sums, rounding | equalities listed in 2a; 4-decimal round-up for every stored hour value and PRIOR |
| S16 | "newest record", version-line order | newest = last element of `issues`; lines oldest first |
| S17 | cell (3)/(4) stops reported as killed | `no-gpu` line, counted 0 |
| S18 | prepare with de-reverb not GPU time | prepare counts when `DEREVERB`; parity and ceiling inside export/evaluate stages |
| S19 | session start undefined; double `pack_state` | `SESSION_T0` in cell (1); `pack_state` only from `end_session` |
| S20 | RESUME after a cell (3)/(4) failed version | such a version's copied `state.tar` may be attached (same hash) |
