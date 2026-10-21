# Cold read pass 7 (3.6 re-run after Phase 4 round-2 hardening) — 2026-10-21, fresh clone at ee13c20

## Haiku (mechanical) — 1 item
| ID | Item | Resolution |
|---|---|---|
| H1 | "Q-E7" is an alias, not a defined ID | cited as "Q-E7 (research/QUESTIONS.md E3.4)" |

## Sonnet (dry run) — 16 items
| ID | Item | Resolution |
|---|---|---|
| S1 | S-008 external-data test has no legal location (tests/ frozen) | throw-away check under research/spikes/s008-external-data/, in S-008 Outputs and Done when |
| S2 | `sh` contract, train timeout ≤ 0, timeout vs "missing output", STOP paths, dry-run fake | D-035 §Kernel and helpers: `sh(cmd, cwd, timeout)`, `SessionEnd`, train-stage outcome table; dry run wraps `Stage.run` and tests a SessionEnd |
| S3 | which interpreter runs orchestration; imports; shared globals; dry-run remap | kernel orchestrates, `sys.path` insert after (4a), lazy imports; fixed global names; `PATH_ROOTS` override |
| S4 | Kaggle resume via previous output; Internet On | G-004 evidence: resuming instructions per platform, Internet On |
| S5 | where the attached tar appears | S-017: session uploads folder → `../uploads/`; unreadable → DEVIATIONS + BLOCKED.md |
| S6 | build-full on the no-root path | skipped and recorded |
| S7 | stage_commits written before evaluate | upload carries `state/commits.json`; GATE-G-001 uses it |
| S8 | `run:` field means platform | renamed `platform:`; RUN always from GATE-G-004.md |
| S9 | Kaggle renders location | inside `out-run<RUN>.tar`; extraction command in G-001 |
| S10 | TSan regex at S-005 includes later tests | staged: T-038 at S-005, full set from S-009 |
| S11 | S-016 inputs lack hf-cli flags and claims | added |
| S12 | UNVERIFIED.md vs D-030 | exempted in D-030 |
| S13 | segment index base | 0-based, slice order |
| S14 | which keys spread.json holds | the seven metrics (D-017) |
| S15 | which report S-019 diffs | the highest accepted run |
| S16 | where the Q-E7 re-check is recorded | EXECUTION_LOG.md note |
