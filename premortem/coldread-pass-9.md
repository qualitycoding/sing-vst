# Cold read pass 9 (3.6 re-run after Phase 4 round-4 hardening) — 2026-10-21, fresh clone at 3921e23

## Haiku (mechanical) — 0 items
All eleven checks pass (93/93 frozen files verify; every cited ID and path resolves).

## Sonnet (dry run) — 18 items
| ID | Item | Resolution |
|---|---|---|
| S1 | scenario (2) expectations unreachable with naive fakes | fakes write invocation-unique bytes, create nested input paths; `CELL_STAGES` slice map, one `run_stages` call per cell |
| S2 | `guarded` did not set STOP for SessionEnd/OwnerAction | STOP set in every branch |
| S3 | scenario (5) asserted state.tar on Colab | split per platform |
| S4 | helper signatures undefined; `sh(<command>)` vs 3-parameter `sh` | signatures of `end_session`, `pack_state`, `restore_state`; stages pass cwd and timeout |
| S5 | PRIOR_VOICE_GPU_HOURS source and double counting | other-platform hours only; from the `switch-platform` response; in S-017 1a |
| S6 | retrain budget formula | `gpu_hours + h10 < 19`, h10 defined; else re-issue without retrain |
| S7 | budget-exhausted path to G-001 | evidence = the response; responses `stop` / `raise-budget` only |
| S8 | session schema (seq, restored_from, end, tolerance) | schema extended; seq across RUNs; end set before the upload tar; tolerance 1e-6 |
| S9 | two RESUME definitions; how S-017 learns it | one definition (state.tar in output); the owner applies it per GATE-G-004.md |
| S10 | cell-local SessionEnd catch vs guarded | removed; guarded handles it |
| S11 | dry-run globals incomplete | every Parameters-cell global preset; PLATFORM from cell (3) |
| S12 | verdict check for invalid reports | invalid verdict shape checked instead |
| S13 | how the S-008 check counts model runs | `SINGVST_DEBUG_RUNS=1` private hook |
| S14 | assets archive hash storage | `assets-archive/SHA256SUMS` |
| S15 | stereo held-out files | averaged to mono for extract_f0 |
| S16 | annotations permission probe; no repo tool | annotations probe; `gh repo clone` fallback, else BLOCKED |
| S17 | queued callAsync after destruction | shared `alive` flag checked with the generation |
| S18 | knowledge-store scripts | existence checked at S-000; copy rule at S-KNOW |
