# Cold read pass 10 (3.6 re-run after Phase 4 round-5 hardening) — 2026-10-21, fresh clone at cee95ae

## Haiku (mechanical) — 0 items
All eleven checks pass (93/93 frozen files verify; every cited ID and path resolves). Observation acted on: the `network`
marker text in pytest.ini named S-012; T-P21 runs at S-000.

## Sonnet (dry run) — 22 items
| ID | Item | Resolution |
|---|---|---|
| S1 | `h10` needs per-stage hours; retrain `gpu_hours` from one platform only | `sessions[].stage_hours`; `h10` from Σ train-stage hours; `gpu_hours` = ledger `total`; bound `BUDGET_HOURS` − 1 (GATES G-001) |
| S2 | ledger derivation, labels, set vs add, killed conversion, prune, missing file, stop | D-035 §Voice ledger: per-issue records set (never added), platform figures set from the newest record, `unlogged` = Σ killed hours, `h/m/s` conversion, missing = 0, `stop` changes nothing; printed line `hours: platform <p> voice <v>`, every `hours-used:` quotes `p`; `prune:` carries `hours-used` |
| S3 | `prior` missing from schema; which issue; Colab `seq` | `prior` in `sessions[]` and in ledger records; check against this RUN's records, newest session = this issue; `seq` = 1 + max over `<root>/run*/out/budget.json` on both platforms |
| S4 | `PLATFORM_EXPECTED`/`PRUNE` absent from Parameters cell and presets | both in the Parameters cell (`""` defaults, mismatch incl. empty → `OwnerAction`); dry-run presets set them |
| S5 | `restore_state` signature conflict; globals; `guarded` type; slicing; session-start helper; `/kaggle` paths | one signature; `WORKING`, `STOP_REASON`, `BUDGET_HOURS` globals; `guarded(cell, Callable)`; `run_cell`; `start_session()`; every absolute path via `PATH_ROOTS` |
| S6 | fake directory/file rule; byte-stable inputs | empty `Path.suffix` = directory holding `fake.bin`; pre-created inputs have fixed bytes; dry run calls `write_params`/`start_session` |
| S7 | `switch-platform` missing from RUN rule; archive names | RUN + 1 for retrain and switch-platform (numbers never reused); `GATE-G-00<g>.run<RUN>.<k>.md` for every response type |
| S8 | version lines per response or cumulative; first `restored_from`; RESUME wording; STOP-branch prints | per issue, after every Kaggle response; chain check over all ledger lines by `seq − 1`; one RESUME wording; `pack_state` prints `state.tar written`, `end_session` prints `STOP_REASON` then the `seq` line on both branches |
| S9 | provenance `repo_root` | repository holding the `singvst_train` package, never the cwd |
| S10 | audio-separator 0.47.0 API unknown | spike research/spikes/audio-separator-047 (C-066) — **found numpy ≥ 2 vs RVC numpy < 2** (R-108): separate `<LOCAL>/sep` venv, exact calls in D-025, `docs/UNVERIFIED.md` bullet (S-016) |
| S11 | GATES evidence lacks new parameters; first platform choice | evidence lists `RESUME`, `PLATFORM_EXPECTED`, `PRIOR_VOICE_GPU_HOURS`, `PRUNE`; question (3) says the issue is pinned (Colab first) and a switch is answered before running |
| S12 | `budget-exhausted` string; which cells print `owner:` | owner answers `budget-exhausted, hours-used:` on seeing `budget: no checkpoint`; cells (3)–(4) print `owner:` before re-raising `OwnerAction` |
| S13 | `raise-budget` amendment path | HANDOFF §Amendments: `BUDGET_HOURS` in cell (3), dry run, same RUN, new commit, PRIOR from ledger |
| S14 | second verdict file/step | `verdict.bound.json`, S-017 action 5, exact command; Done when and Outputs updated |
| S15 | "model run" undefined | one guide part (acoustic + vocoder `Run`), line `guide part <i>: frames <n>`; exactly two lines |
| S16 | `hf download` targets truncated | exact commands of RVC README 170-180 written into D-035 cell (5) with resulting paths |
| S17 | `lastWarnings` replace vs append | render/import warnings replace; held capture warning appended while held |
| S18 | garbled publish sentence; host rate before `prepareToPlay`; state count | sentence fixed; unknown rate 0 counts as matching; three public + three internal values |
| S19 | checkpoint-only Save has no path | name `.checkpoints/state.json` |
| S20 | junit classification judgment | mechanical rule on the `<failure>` text's last line; spike research/spikes/junit-classify (C-067) |
| S21 | spread `min`/`max` with nulls; who converts invalid | `null` when any value is `null`; `evaluate_voice` itself converts |
| S22 | uploads folder unnamed; only fallback BLOCKED | `find` by name + SHA-256 match; second channel: owner uploads to branch `upload-<VOICE>-run<RUN>`, read with `git show`; BLOCKED only if both fail |

Pass limit: 3.6 allows five passes per trigger; this is the re-run triggered by the round-5 changes. These fixes were not
re-verified by a further cold read or pre-mortem round (rounds exhausted); they are listed in premortem/RESIDUAL.md.
