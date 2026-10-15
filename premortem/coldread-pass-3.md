# Cold read pass 3 (3.6) — 2026-10-15, branch at f807e57

## Haiku (mechanical) — 8 items
| ID | Item | Resolution |
|---|---|---|
| H1 | S-019 cites premortem/round-*.md | written by the planning pre-mortem (Phase 4) before the push; wording says so |
| H2 | external protocol path | HANDOFF names it as external; excerpts are local |
| H3 | S-010 Done-when needs `pack_voice` (S-012) | binary part of T-P13 moved to S-012, which now depends on S-010 |
| H4, H5 | Phase 5 and 0.2 cited without excerpts | added to plan/PROTOCOL_EXCERPTS.md |
| H6 | PK-38 cites a pre-mortem lens not yet written | the Phase 4 rounds include the "audio thread" lens |
| H7 | PK-16 cites C-015b/c | C-015 |
| H8 | PK-03 heading spelling | "§Halt / deviation protocol" |

## Sonnet (dry run) — 21 items
| ID | Item | Resolution |
|---|---|---|
| S1 | T-034 needs a German locale nobody installs | D-018 corrected; S-000 action 3 generates it (localedef / locale-gen, else CI-only); cpp and sanitizers jobs run locale-gen (C-056) |
| S2 | impl branch pushed before push access is established | S-000 action 1 attaches all three repositories and probes permissions before action 2 pushes |
| S3 | narrow fetch refspec: origin/<impl> never exists | S-000 widens the refspec, pushes with -u and checks `git rev-parse origin/<impl>`; save.sh and turn_end_check.sh fetch the ref explicitly |
| S4 | RVC extract argv unverified; ../rvc not an S-016 input | C-057 (argv read at 81eed5e); S-016 Inputs add ../rvc and an action greps `sys.argv` |
| S5 | notebook environment incomplete | D-035 §Environment: uv-managed Python 3.12 venv (C-060) with every pin; literal render build line |
| S6 | no parameters cell; Drive/RVC mapping; memory check | D-035 cells (2) parameters, symlink mapping, memory headroom check (PK-43) |
| S7 | no rule for an owner-reported notebook failure | GATES G-004 `failed: <cell> <error>` response: fix and re-issue, 3 attempts, hours counted |
| S8 | Python 3.12 on hosted runtimes | uv installs 3.12 regardless of the runtime's Python (C-060) |
| S9 | quota unreadable; GPU time undefined | D-035 §Time and budget: GPU time = wall-clock of the cuda stages; quota is a printed reminder the owner confirms |
| S10 | three vs four result files | four files everywhere (S-017, G-004), attached or pasted |
| S11 | training vs held-out median reference | D-017 says the held-out median (PROCEDURE wins) |
| S12 | provenance root and lockfile source | editable install mandated; root = `Path(__file__).resolve().parents[2]`; lockfile python/requirements-lock.txt |
| S13 | values in an invalid report | PROCEDURE: uncomputable metrics are `null`; the S-015 dry run may end "invalid" |
| S14 | Resemblyzer stand-in hides the sample-rate trap | PROCEDURE passes file paths; stand-in `preprocess_wav(fpath_or_wav, source_sr=None)` (C-058) |
| S15 | PR body path | `--body-file ../PR_BODY.md`, outside the repository; round files: see H1 |
| S16 | S-013 Outputs omit ENVIRONMENT.md | added |
| S17 | store clones: credential, record location, precedence, added-only | repo tool's clone command; DEVIATIONS rows "followed / not followed"; plan and frozen files win; `--diff-filter=A` |
| S18 | gh scopes; Done-when commands; literal ellipsis | read probes of actions/runs and pulls, write fallbacks named; exact pytest commands; full pending list |
| S19 | Resume would misroute a first implementer | HANDOFF: Resume applies once `phase` is `impl`; a first session starts at S-000 (state.json also reset at Phase 5) |
| S20 | exit 2 vs 3 not mechanical | D-014: CLI pre-checks before `renderTake` exit 2; any exception from `renderTake` exits 3 |
| S21 | S-KNOW push-to and `<run_id>` | attach via repo tool, create-if-missing layout, `<run_id>` = state.json `run_id` |

Lessons: L-20261015T200000Z (H3), L-20261015T200100Z (S1), L-20261015T200200Z (S3); recurrences L-20261014T195500Z (occurrence 2), L-20261015T180000Z (occurrence 3; S4, S12, S14, S20).
