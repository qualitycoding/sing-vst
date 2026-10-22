# Cold read pass 14 (3.6 re-run, D-039 scope) — 2026-10-22, fresh clone at 3d40cc6

## Haiku (mechanical) — 6 items
| ID | Resolution |
|---|---|
| H1–H3 | `pipeline.run_stages`, `pipeline.Stage`, `pipeline.atomic_write_text` are defined in python/singvst_train/pipeline.py, which D-035 names — no change |
| H4–H6 | G-001 `proceed`, `stop` and `retrain` handling now pointed to from S-017 action 4 (evaluate the retrain bound, new GATE-G-004.md, S-018, S-RETRO) |

## Sonnet (dry run) — 2 items
| ID | Resolution |
|---|---|
| S1 | `recordings-minutes` = total minutes of the new set; missing → asked twice, then `stop`; no recording change → `r` = 1 |
| S2 | D-035 §Runs: `owner-fixed:`/`prune:` re-issues also change `RESUME` by its rule |

Five money scenarios were worked end to end with consistent numbers (Colab kill then switch; killed Kaggle version then
upload; failed then switch; prune then two versions; budget-exhausted then raise-budget-to).
