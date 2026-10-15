# Cold read pass 2 (3.6) — 2026-10-15, branch at d99eb4c

## Haiku (mechanical) — 9 items
| ID | Item | Resolution |
|---|---|---|
| H1–H7 | protocol 3.1, Global Rules 4/5/9/11/12/13 and "Phase 5" cited without an excerpt | PROTOCOL_EXCERPTS now includes Global Rules 1–13 and 3.1; header comment reworded |
| H8 | HANDOFF names PK-01…PK-57 (60 exist) | range replaced by "every rule whose Applies to is both" |
| H9 | TRACEABILITY cell "T-P13b" | "S-012 (binary part: S-010)" |

## Sonnet (dry run) — 28 items
| ID | Item | Resolution |
|---|---|---|
| S1 | Linux plugin tests need a display in CI | ctest wrapped in `xvfb-run -a` on Linux |
| S2 | annotation cap makes "absent = passed" unreliable | `test-summary` notice per JUnit file on every run; D-036 pass rule uses it |
| S3 | `<voice>` name source undefined | evaluate provenance `params.voice_name` (D-035, eval/PROCEDURE.md) |
| S4 | concurrency contradiction | sequential, ID order (PLAN header, HANDOFF) |
| S5 | notebook clone ref / opening | impl branch; Colab and Kaggle opening links in S-016 |
| S6 | `run_stages` could delete RVC checkpoints | D-035 stage table; experiment dir never an output |
| S7 | time/quota/epochs/Kaggle resume | D-035 §Time and budget, epochs, Kaggle restore |
| S8 | `../deps` vs `$HOME/deps` | `$HOME/deps` everywhere |
| S9 | store repo permissions, trailers persistence, sudo | S-000 preflight; `.git/singvst-trailers`; no sudo → CI-only plugin checks |
| S10 | `applies:all`, knowledge diff | S-000 action 3 |
| S11 | probe/clone/build commands | S-000 actions 4–5 |
| S12 | stale PK actions, status.py, E-2, immutability list | checklist fixed; tools/gen/status.py; D-037 E-2; HANDOFF list |
| S13 | bare python3 | python3.12 everywhere (tools usage lines too) |
| S14 | unbounded builds in HANDOFF | `--parallel 2` |
| S15 | S-019 mapping target | plan/IMPLEMENTATION_MAP.md |
| S16 | tiers: rule text, Fable, fallback, entry format | excerpts include Global Rules; HANDOFF §Tiers |
| S17 | S-KNOW index/layout/taxonomy/timeout/push-to | store scripts and layout; G-003 asked twice → bundle |
| S18 | G-001 renders / owner build lines | renders on Drive; ENVIRONMENT §Owner build |
| S19 | `stop` semantics; budget tracking | GATES preamble; budget.json |
| S20 | exit codes by error, --check-voice, voiceId, plugin errors | D-014, D-010 |
| S21 | S-012 command cwd | `(cd python && …)` |
| S22 | onnxruntime-gpu conflict | uninstall then pin (D-035 cell 4) |
| S23 | transposition writing, time zero, no dry run | eval/PROCEDURE.md; S-015 dry run with stand-in modules |
| S24 | prepare segment fields / params | D-035 prepare row |
| S25 | in-flight not pushed; pending not seeded | Save after setting/clearing; S-000 seeds pending |
| S26 | recorded HF revision unused | notebook cell 5 uses it |
| S27 | nobody writes GATE-G-005.md | S-015 last action |
| S28 | sanitizer build vs test indistinguishable | separate CI steps |
