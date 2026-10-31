# Cold read pass 15 (Amendment 02 scope) — 2026-10-31, working tree of the gen branch over 09b9a1d

## Mechanical — 4 items
| ID | Resolution |
|---|---|
| H1 | All 25 steps of plan/PLAN.md have every 3.1 template field, and every `Depends on` names an earlier step (checked by script) — no change |
| H2 | S-017, S-RETRO and S-KNOW did not require `tools/check_postconditions.py` in `Done when`, although D-042 says every remaining step extends it — added |
| H3 | Round 7 item 6 relied on per-probe timeouts that S-ADVERSARIAL did not state — S-ADVERSARIAL now runs each probe under `timeout 600` |
| H4 | T-P22 on this branch alone reports C-068…C-070, L- and K- identifiers cited by premortem/ASSUMPTION_AUDIT.md and D-043; they exist on the impl branch (Amendment 01 AM-06/AM-08), so the check holds after the merge, which is how this branch is applied (HANDOFF §Amendments) — no change; re-checked after the merge |

## Dry run — 2 items
| ID | Resolution |
|---|---|
| S1 | S-MUTATE as first written would loop: its `Done when` demanded the target, its baseline is below it and frozen tests cannot be added by the implementer — D-044 now records the baseline and S-MUTATE's `Done when` and `On failure` say the first run halts for a test amendment (R-121) |
| S2 | A review re-issue of G-004 while the owner is already training on the old pin had no rule; the S-017 upload check would have accepted it — D-042 `pre-fix` rule and S-017 action 2a (R-120) |
