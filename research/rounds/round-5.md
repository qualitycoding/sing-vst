# Research round 5 (2026-10-14, from 19:35Z) — R1-R6 on the dependency lock; closing existence check after Phase 2

## Resume
Checkpoint hashes: 125/126 matched; tools/bootstrap_test_env.sh differed (an uncommitted edit from the 15:43Z session), and
python/requirements.in, python/requirements-lock.txt and research/spikes/pyworld-direct/ were untracked (lesson
L-20261014T195500Z, recurrence of L-20261010T094000Z). The store (Lessons @ ac028c7, knowledge @ 09f3458) has not moved, so R0 stands.

## Findings
- **C-046 (new, load-bearing, verified).** setuptools < 83 carries PYSEC-2026-3447 (research/spikes/pip-audit-setuptools), and with
  setuptools 84.0.0 `import pyworld` 0.3.5 fails because pkg_resources is gone; loading the extension pyworld.pyworld directly
  works and reproduces the harmonic-tone result of C-027 (research/spikes/pyworld-direct, re-run to completion: identical output).
  **Informs:** D-019 (Python pins: setuptools 84.0.0), D-017 and T-P10 (metrics load pyworld through the extension), PK-41.
- tools/bootstrap_test_env.sh now refuses an existing clone that is not on the pinned tag's commit; checked on the pinned
  deps (exit 0) and on a JUCE 9.0.2 clone (exit 3).
- tools/gen/claims.py now honours kstamp (lesson L-20261014T195600Z).

- **C-047, C-048 (new, load-bearing, verified; research/spikes/rvc-resume).** RVC training resumes from the newest G_/D_
  checkpoint in logs/<exp>, so a hosted session cut at its time limit continues if logs/<exp> persists (D-016); the
  inference weights for export are assets/weights/<name>.pth in float16 with keys config, weight, sr, f0, version (D-012, S-013).

- **Oracle defects (corrected, lesson L-20261014T203000Z).** research/spikes/oracle/oracle.py had three rule defects:
  a vowel-less syllable dropped the next onset, frame durations could overshoot their total, and a zero-length note with an
  equal start removed the real note. Fixed; research/spikes/oracle/properties.py now checks six invariants over 6000 random
  cases (0 failures, properties-output.txt). Mutation check: against the unpatched oracle (commit 6fe0e5d) it reports 4
  invariant failures, so the checks can fail.

## Saturation (provisional)
New load-bearing claims: 3 (C-046, C-047, C-048). Downgrades: 0. Contradictions: 0. Not yet saturated: round 6 runs the cited-file existence
check and the oracle over the Phase 2 expectations; if it adds nothing, research closes at round 6 (protocol maximum).
