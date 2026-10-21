# Cold read pass 8 (3.6 re-run after Phase 4 round-3 hardening) — 2026-10-21, fresh clone at b35d8da

## Haiku (mechanical) — 1 item (+ 4 notes)
| ID | Item | Resolution |
|---|---|---|
| H1 | test_P##b sub-tests have no TRACEABILITY rows | TRACEABILITY states the sub-test convention (D-037 E-4) |
| notes | T-071 missing from suite ranges; S-009 lacks S-007 dependency; PK-02/PK-21 paths imprecise | fixed (13d7d40) |

## Sonnet (dry run) — 16 items
| ID | Item | Resolution |
|---|---|---|
| S1 | RESUME inside params.json breaks session 2 | params.json = exactly {VOICE, RUN, PLATFORM, DEREVERB, EPOCHS, SPEAKER_ID, GUIDE}, written at (4e) |
| S2 | state_tar_sha256 unrecordable | `seq` + `restored_from`; cell (17) prints `seq <n> state.tar <sha>`; owner pastes the lines (round 4 R-083) |
| S3 | RESUME dead-ends after failures in (1)–(4) | RESUME by state.tar existence; restored state.tar copied into every version's output |
| S4 | invalid evaluation blocked as failed: 16 | T-P20 assertion failures are results; only pytest exit 2–5 is failed: 16 |
| S5 | where helpers/globals are defined | cell (3) defines every helper and global |
| S6 | Kaggle-only scenarios | per-platform scenario list |
| S7 | other non-stage inputs; raw/ path | four non-stage inputs listed; raw/ exception in the path rule |
| S8 | status-line channel vs frozen header | `createEditor()` passes a status function; lastError carries "voice not found" |
| S9 | Cancelling reset without acknowledgement | `CancelAck` handshake (2-s fallback) |
| S10 | TakeSlot writers | worker hands to the message thread via callAsync; single writer kept |
| S11 | relative paths in (12), cwd of (16) | absolute paths; (16) runs from `<sing-vst>` with the test file |
| S12 | upload tar layout | exact flat member list; out tar via `tar -C <run>/out` |
| S13 | invalid-run outputs | spread.json with nulls, renders kept, report/sidecar/verdict written |
| S14 | stopped_by_budget schema | budget.json epoch-or-null; training.json bool |
| S15 | (1)–(4) "nothing written" false | (4f) failure closes the session entry; readers ignore entries without end |
| S16 | stale S-003 D-012; HANDOFF range; sketch bound | fixed |
