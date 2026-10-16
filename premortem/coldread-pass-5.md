# Cold read pass 5 (3.6, protocol maximum) — 2026-10-16, fresh clone at b0c05af

## Haiku (mechanical) — 1 item
| ID | Item | Resolution |
|---|---|---|
| H1 | PK-63 applied via "PLAN.md step template" | applied via plan/PLAN.md `Depends on` and `Done when` fields (c0be5b5) |

## Sonnet (dry run) — 17 items
| ID | Item | Resolution |
|---|---|---|
| S1 | consent cell vs "only cell the owner edits"; attestation wording; no consent field in G-004 | owner edits cells (2) and (2a); D-035 gives the attestation sentence; G-004 response starts `consent: yes` (absent → stop) |
| S2 | weights / logs / cwd layout ambiguous | D-035 §Paths: absolute `<root>`, `<rvc>`, `<sing-vst>`, `VENV` per platform; `logs/`, `assets/` under `<rvc>`; cwd rules |
| S3 | D-015 "every result file" vs D-035 sidecars | D-015 lists the sidecar files and the files without one |
| S4 | S-000 halt vs DR-07 for pip-audit | S-000 On failure: DR-07 once, ENVIRONMENT lock row updated, second finding → BLOCKED.md |
| S5 | trailer content; git identity | S-000 action 2: trailers your instructions prescribe, else `Co-Authored-By: <model> <noreply@anthropic.com>`; identity fallback |
| S6 | branch commands; writable parent; store paths | literal fetch/unshallow/switch/push; writable parent or BLOCKED.md; store clones into `../store-lessons`, `../store-knowledge` |
| S7 | JUCE/Catch2 commits not checked anywhere | bootstrap pins both commits; exit 4 on a moved tag (DR-02), verified negative |
| S8 | CI evidence inside steps | PLAN header: a Done-when naming CI ends with Save + D-036 read |
| S9 | archive of earlier G-004/G-001 rounds; `failed` counter scope | `results/<voice>/run<N>/`, `GATE-G-00<k>.run<N>.md`; three attempts per G-004 issue |
| S10 | D-009 `bpm`, `sr` | `take.bpm`, `take.sampleRate`; `hostBpm` only for staleness |
| S11 | f0Curve frame count, hasPhone header comments | errata E-7, E-8 (D-037) |
| S12 | precedence of render-blocking conditions | D-010: no voice, lyrics parse error, no notes; first reported |
| S13 | S-013 `--exp-name` needs S-014's `latest_weights` | delegation stated; no test before S-014 uses it |
| S14 | THIRD_PARTY_NOTICES format and sources | S-018: section format, licence-text paths, count check |
| S15 | apt command; g++ version range | literal apt line (ci.yml list + python3.12-venv locales); g++ major 13 |
| S16 | workflow-edit permission | HANDOFF: no step edits workflows; a change is an amendment |
| S17 | store matching by status; purpose of `gh api user` | active/current entries only (Appendix C); `/user` probe dropped |

All 18 items were resolved by amending the plan. This was the fifth pass, so no further 3.6 pass is allowed for this
round of changes; the Phase 4 pre-mortem covers "implementer misinterpretation", and the cold read re-runs after Phase 4
hardening (protocol Phase 4 item 4).

Lessons: recurrence of L-20261016T000100Z (S1, S2: notebook paths and cwd unstated).
