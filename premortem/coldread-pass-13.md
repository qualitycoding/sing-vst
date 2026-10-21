# Cold read pass 13 (3.6 re-run, D-039 scope) — 2026-10-21, fresh clone at 0050310

## Haiku (mechanical) — 1 item, fixed at de9d15b
S-017 1a now says re-issues that keep `RUN` repeat that RUN's `DEREVERB`, `EPOCHS`, `SPEAKER_ID`, `GUIDE` (so
`params.json` still matches); new RUNs take defaults or the `retrain` values.

## Sonnet (dry run) — 6 items
| ID | Resolution |
|---|---|
| S1 | `owner-fixed:`/`prune:` re-issues repeat the previous `EXPECTED_COMMIT`; `failed:`, `raise-budget-to` and new RUNs take the new head (D-035 §Runs, GATES, S-017 1a) |
| S2 | with `none`, the record's `platform_hours` = the platform's previous ledger value (0.0 if none) |
| S3 | integers only in memory; JSON files and printed figures hold decimal hours with ≤ 4 decimals |
| S4 | a RUN is pruned at most once; a second unreadable checkpoint after a prune tells the owner to `switch-platform: colab` |
| S5 | invalid `raise-budget-to` asked again at most twice, then `stop` |
| S6 | scenario (9) runs cells (7)–(11) in order after the pruned restore |
