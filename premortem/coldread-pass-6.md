# Cold read pass 6 (3.6 re-run after Phase 4 round-1 hardening) — 2026-10-16, fresh clone at 570c4d4

Phase 4 item 4 requires the cold read to re-run after plan changes; this is that re-run (new agents).

## Haiku (mechanical) — 6 items
| ID | Item | Resolution |
|---|---|---|
| H1, H2 | bare `state.json` in the Save definition and S-000 Outputs | `.checkpoints/state.json` |
| H3–H5 | PK-07, PK-50, PK-71 applied via files that later steps create | cells name the producing steps |
| H6 | GATES.md cites protocol 3.3, not excerpted | 3.3 (human gates) added to plan/PROTOCOL_EXCERPTS.md |

## Sonnet (dry run) — 16 items
| ID | Item | Resolution |
|---|---|---|
| S1 | notebook dry run needs nbformat (not stdlib) | run with `../venv-lock/bin/python -I` |
| S2 | G-004 Colab link on a branch | commit-pinned URLs in GATES.md |
| S3 | params.json / heartbeat written before the Colab mount | both at the end of cell (4), after the mount |
| S4 | invalid report vs `metrics.judge` and exit code | D-035: ValueError/failed render → invalid report; verdict `{"all": false, "status": …}`; exit 0 when report written |
| S5 | which cell holds `make_stages`; injected globals | cell (3), locator `def make_stages`; globals listed in S-016 |
| S6 | D-010 `arm(true)` allocates vs D-022 | D-010 defers to D-022 |
| S7 | external-data detection method | D-012: bounded protobuf walk (fields 7 → 5 → 14/13); S-008 unit test |
| S8 | results path, N vs RUN, gate-file collisions, VOICE field | `results/<VOICE>/run<RUN>/`; `.fail<k>` suffix; `voice:` in the G-004 response |
| S9 | similarity_gain spread; bound inclusivity | per-repeat differences; inclusive |
| S10 | "controls listed in round-*.md" undefined | register Mitigation cells cover every round R-### |
| S11 | private headers in a frozen directory | D-033: private headers in `core/src/` |
| S12 | T-068 under TSan not in the regex | local and CI TSan sets include T-068 |
| S13 | stale suite ranges | T-063…T-070 in HANDOFF and ci.yml |
| S14 | g++ other than 13; repository root | ≥ 13 accepted (others logged), < 13 BLOCKED; checkout is the root |
| S15 | EPOCHS not a multiple of 10 | asserted in (2a); GATE says so |
| S16 | dry-run held-out files; which files count | `h1.wav`, `h2.wav` at 48 kHz; sorted `*.wav` |
