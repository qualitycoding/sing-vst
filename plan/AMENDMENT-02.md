# Amendment 02 — new v3.4–v3.6 phases for the remaining steps (D-042, D-043, D-044)

**Requested by:** the owner, 2026-10-30 ("enhance the pre-existing plan with any new phases from the revised protocol").
**Baseline:** the plan as amended by Amendment 01 (protocol v3.6, D-041), implementation halted at G-004.
**Scope:** forward changes only, to steps that have not run yet (S-017 onward). Amendment 01 repaired the steps already completed
(S-000…S-016). No frozen file changes; `sha256sum -c tests/FROZEN_MANIFEST.sha256` stays OK.

## What changes

| Protocol section | Change in this plan | Where |
|---|---|---|
| 3.8.1 traditional review | new step **S-REVIEW**: fresh-context review of core, plugin, toolkit and notebooks, with C++ (gcov) and Python (coverage.py) coverage; Critical/High findings fixed before any later delivery step | PLAN S-REVIEW; D-042; spike research/spikes/coverage |
| 3.8.2 adversarial review | new step **S-ADVERSARIAL**: one probe script per boundary (lyrics, SMF, voice packages, ONNX, take cache, plugin state, CLIs, `state.tar` restore, resource exhaustion, dependency failure, `A-###` premises) | PLAN S-ADVERSARIAL; D-042 |
| 3.8.3 mutation testing | new step **S-MUTATE** on the seven library modules and `cli.py` with mutmut 3.8.1; **C++ opt-out** (no Clang/Mull on the pinned toolchain or the host) | PLAN S-MUTATE; D-044; spike research/spikes/mutmut |
| Rule 14 post-conditions | every remaining `Done when` names its artifacts' checks; each step extends `tools/check_postconditions.py` | S-017, S-018, S-019, S-RETRO, S-KNOW |
| Rule 14 budgets gate | D-044's target is fixed before S-MUTATE runs, from a measured baseline, with its miss rule | D-044 |
| 3.7.1 (1a) | S-RETRO verifies DEVIATIONS.md against the diff (the AM-07 method) | PLAN S-RETRO |
| Rule 6 push cadence | S-KNOW verifies its store pushes with `git ls-remote` | PLAN S-KNOW |
| 4.7 assumption audit | its falsified premises are corrected in the plan text | D-043; premortem/ASSUMPTION_AUDIT.md |
| 1.3.6 command and pin verification | the new pins (`python/requirements-mutate.txt`) and the review commands were run before they entered the plan | research/spikes/mutmut, research/spikes/coverage; plan/ENVIRONMENT.md |
| Phase 5 summary | the status header counts assumption-audit verdicts and finished reviews | tools/gen/status.py |
| Phase 4 pre-mortem | round 7 on the changed steps; cold-read pass 15 | premortem/round-7.md, premortem/coldread-pass-15.md; R-119…R-121 |

## Order and halting

The three review steps come after S-016 in plan order and depend only on it (S-ADVERSARIAL and S-MUTATE on S-REVIEW), so they run
**while halted at G-004**. S-019 depends on all three; its delta review covers code changed after S-REVIEW (S-017 notebook fixes,
S-018). A Critical/High fix that changes what the notebook checks out re-issues G-004 (D-042, R-119); a response for the archived pin
follows D-042's `pre-fix` rule (R-120).

## Measured evidence (1.3.6, PK-05)

- **Mutation baseline** (research/spikes/mutmut/output.txt, impl f3ad77b): 2290 mutants; the seven library modules together 0.718,
  `cli.py` 0.234. The D-044 target (≥ 0.80 together, ≥ 0.70 each, `cli.py` ≥ 0.50) is therefore expected to halt the first S-MUTATE
  run with a "tests to add" table for a planning amendment (R-121).
- **Coverage** (research/spikes/coverage/output.txt): the 61 C++ core tests pass under `--coverage`; per-file line coverage and the
  Python toolkit's coverage.py table are in the output. Two Python tests fail at impl f3ad77b: T-P23 (README section, written at
  S-018, expected) and T-P22, because Amendment 01's files cite D-042 and D-043, which this amendment defines; merging this branch
  into impl clears T-P22.

## Applying it

Merge this branch into the impl branch (HANDOFF §Amendments). Then, on the impl branch, as Amendment 01 AM-09/AM-10: archive the open
GATE-G-004.md and re-issue it pinned to the new impl head (no response exists, so no limit is consumed), log the rows, and continue
with S-REVIEW, S-ADVERSARIAL and S-MUTATE while G-004 is open.
