# Cold read pass 4 (3.6) — 2026-10-15, fresh clone at de16976

## Haiku (mechanical) — 3 items
| ID | Item | Resolution |
|---|---|---|
| H1 | S-019 cites premortem/round-*.md, absent | Phase 4 output, committed before the planning push (as pass 3 H1) |
| H2 | PK-38 cites the "audio thread" lens, absent | Phase 4 rounds include that lens (as pass 3 H6) |
| H3 | PK-01 applied via "S-000 (resume check)" | applied via HANDOFF §Resume (2b58a4c) |

## Sonnet (dry run) — 16 items
| ID | Item | Resolution |
|---|---|---|
| S1 | notebook data plumbing: split copies, FLAC→WAV, voicebank folder, render-bin contents | D-035: `raw_wav/`, split copy rule, `<root>/voicebank/{pack,tiger}`, literal `cp` of binary + runtime files into `out/bin/`, literal pack/evaluate arguments |
| S2 | cell order, `n_cpu`, `SINGVST_RVC_ROOT`, interpreter spelling, uv index flags | cells (2a) parameters and (10a) memory check, 19 cells; `os.cpu_count()`; cell (6) env; venv `bin` first on PATH so `python -m singvst_train.cli <cmd>`; `--index-url pypi --extra-index-url cu128 --index-strategy unsafe-best-match` |
| S3 | fallbacks for `gh run rerun` / `gh pr create` undefined | D-036: new commit instead of rerun; S-019: compare URL + body in EXECUTION_LOG, owner opens the PR |
| S4 | CLI provenance shapes, `render_seconds`, `--seed` default, owner's render command | D-014 shapes; `render_seconds` = `renderTake` wall-clock; seed 0; G-001 literal loop and RTF formula |
| S5 | S-000 not idempotent; out-of-tree artefacts lost on reset; save.sh fell back to the planner's trailers | S-000 session preamble; HANDOFF §Resume points to it; save.sh refuses to commit without trailers |
| S6 | S-015 dry run not literal | literal command from `python/` without `-I`, `PYTHONPATH=<tmp>/stubs`; stand-in `VoiceEncoder.__init__(*a, **k)` |
| S7 | recipient of epochs/dereverb values; retrain vs G-004 | GATE-G-004.md states the Parameters-cell values; the response reports the values used; `retrain` re-issues G-004 in full |
| S8 | no-root path vs "locally" in Done-when | PLAN header waiver for T-034 and T-053…T-059; D-036 lists them as CI-only on that path |
| S9 | `ortRuntimeLoaded` left in stubs.cpp | S-007 implements it |
| S10 | `gh api user` may 403; shallow store clones | `/user` advisory; `fetch --unshallow` before range logs |
| S11 | apt mirrors not in run.sh; row mapping | run.sh apt rows (probed: reachable); hosts table "run.sh roles" column |
| S12 | stale test IDs in QUESTIONS, claims `informs`, D-013 | renumbered (T-025, T-042…T-044, T-019, T-026, T-032/T-033, T-027); D-013 T-048…T-052 |
| S13 | requirements.in says S-012 generates the lock | regenerated only under DR-07 |
| S14 | `*.src.md` beside the real files | HANDOFF: generator inputs, do not read or edit |
| S15 | round-*.md absent | Phase 4 output (H1) |
| S16 | "openvpi vocoder if used" | listed only if the G-005 answer or the packed voice uses one |

Lessons: L-20261016T000000Z (S5), L-20261016T000100Z (S1, S2); recurrence L-20261015T180000Z (occurrence 4; S4).
