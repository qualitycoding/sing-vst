# Research round 6 (2026-10-15) — closing round (protocol maximum)

## R0 re-check
Store tips unchanged: `qualitycoding/Lessons` @ ac028c7, `qualitycoding/knowledge` @ 09f3458 (`git ls-remote`, 2026-10-15),
so R0 stands. research/PRIOR_KNOWLEDGE.md regenerated with this run's newer lessons (PK-52…PK-57 added; every lesson mapped).

## Findings
- **C-052, C-053, C-054 (new, load-bearing, verified; research/spikes/hf-cli).** RVC's README gives the official
  `hf download` commands for its assets; huggingface_hub 2.2.0's `hf download` takes `--revision/--include/--local-dir`;
  transformers 4.49.0 (RVC's pin) requires huggingface-hub < 1.0, so the CLI lives in its own venv (CI `python-torch`, S-016).
  **Informs:** D-018, S-013, S-016, R-010.
- Protocol v3.3 published upstream (skills 9636a79): adopted as D-034 (checkpoint schema; resumption).
- Environment drift: `/usr/bin/python3` is now 3.13 (lesson L-20261015T073000Z) — ENVIRONMENT.md names python3.12.
- Oracle re-run over the frozen C++ expectations:  research/spikes/oracle/check_expectations-output.txt (275 checked,
  0 mismatches); properties.py: 0 invariant failures over 2 × 3000 cases. Python expectations: research/spikes/sketch-py
  (every test whose inputs exist passes against the sketch; notebook/README tests satisfiable).
- Cited-file existence: `tools/gen/claims.py` fails if a claim cites a research/ or plan/ path that does not exist; it passed.

## Termination (1.3)
Rounds run: 6 (maximum). Claims: 52 — corroborated 3, single-source 2, verified 47; load-bearing:
corroborated 3, single-source 2, verified 40. Load-bearing claims below `corroborated`: C-010, C-019 —
each is in premortem/RISK_REGISTER.md. Round 6 added 3 verified load-bearing claims and no downgrades or contradictions;
research closes at the maximum, with the residual open questions Q-E7 and Q-E8 assigned to S-001 and S-013.
