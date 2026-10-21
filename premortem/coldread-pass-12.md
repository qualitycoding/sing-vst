# Cold read pass 12 (3.6 re-run after the round-6 fixes; D-039 scope) — 2026-10-21, fresh clone at de41850

## Haiku (mechanical) — 4 items, fixed at 11735a2
`killed_hours` added to the `budget.json` schema; ledger record `run` source; `{"killed_hours": h}` shape;
`hours-used: drive` named in §Voice ledger.

## Sonnet (dry run) — 22 items
| ID | Resolution |
|---|---|
| S1 | `RESTORED_FROM` global set by cell (3) (None on Colab), read by `start_session` |
| S2 | the raising helpers print `owner: <cell> …` themselves (cell (3) checks, 4c, `write_params()`) |
| S3 | formulas for `runs[RUN]`, top-level `gpu_hours`, and the live voice total (file for other runs + in-memory current run) |
| S4 | owner's killed-hours formula with round-up per version in GATE-G-004.md; checks on per-version sums |
| S5 | all hour values held as integer ten-thousandths, `ceil(round(x·10⁴, 6))` once; printed `p`/`v` rounded up |
| S6 | `owner-fixed: params` repeats only the run-identity values; PRIOR/KILLED/RESUME/PRUNE/commit follow 1a |
| S7 | fake clock advances once per `timed` run; check commands return rc 0 |
| S8 | `make_dirs()` helper (run dirs, RVC symlinks) called at (4e) and by the dry run; restore input path stated |
| S9 | `end_session()` has no parameter |
| S10 | cell (16) runs inside `timed("t-p20", …)`; not executed by the dry run; scenario (7) totals 5 h |
| S11 | `killed ?` form, counted 12 h |
| S12 | "the last `hours:` line above the newest `seq` line" |
| S13 | `unverified` in the record schema; Colab consent uses the uploaded file; baseline excludes unverified and the replaced record |
| S14 | prune also skips `weights/<PRUNE>_e*_s*.pth`; `h10` conservative after a prune |
| S15 | retrain bound stated as a minimal-feasibility test; shortfall lands in budget-exhausted (R-110) |
| S16 | switch to the same platform or consent platform mismatch → asked again, then BLOCKED |
| S17 | `owner-fixed:`/`prune:` pooled; current response counts while archived count < limit |
| S18 | `EXPECTED_COMMIT` = impl head when GATE-G-004.md is written |
| S19 | budget-exhausted G-001 evidence listed; `raise-budget-to` ≥ total + 2 |
| S20 | presets for RESUME, RESTORED_FROM, SESSION_T0; per-session resets; (9) ordering; Colab KILLED_HOURS enforced 0.0 |
| S21 | KILLED_HOURS in the gate's list; "keeps"; Kaggle consent `p` = uploaded Σ runs check |
| S22 | already fixed by the Haiku item |
