# Research round 4 (2026-10-14) — R5 adversarial pass on round-3 claims, R6 completion

Trigger: resuming at 1.3, `git status` showed research/spikes/pyworld/ untracked while C-027 cited its output as verified.

## Findings
- **C-027 contradicted.** research/spikes/pyworld/run.sh, run to completion in a fresh venv (Python 3.12.3, numpy 1.26.4,
  pyworld 0.3.5, setuptools 80.9.0): harvest+stonemask leave a pure 220 Hz sine unvoiced on 0/161 interior frames (default and
  50–1100 Hz ranges); a 15-partial harmonic tone at 220 Hz is voiced on 161/161 frames with 0.098 cents RMS (reference A4 = 440 Hz).
  C-027 rewritten to the measured fact; knowledge item superseded (K-20261014T143900Z). **Informs:** T-P10 must use a harmonic tone (PK-31).
- **C-044 cited a non-existent file** (plan/ENVIRONMENT.md). Hosts re-probed as research/spikes/hosts (2026-10-14T14:37Z): same
  results as 2026-10-10 except the GitHub REST API is now reachable for attached repositories. Knowledge item superseded (K-20261014T143901Z).
- **Control added:** tools/gen/claims.py now fails when a cited research/ or plan/ file is missing; with it, all 43 claims pass.

## Lessons
L-20261014T142000Z-verified-label-cited-a-file-never-written (High; recurrence of L-20261010T094000Z).

## Saturation
New load-bearing claims: 0. Confidence downgrades: 0 (C-027 changed content but stays verified with an existing spike).
Contradictions: 1 (C-027), resolved this round. Round 5 re-runs the existence check over every claim after Phase 2 adds
oracle-backed expectations; if it finds nothing new, research is saturated (rounds 4 and 5 both clean except this resolved item).
