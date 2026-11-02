# LISTENING AMENDMENT — G-001

**Repository:** `qualitycoding/sing-vst`  
**Branch:** `impl-gen-20261004T095012Z-singing-voice-vst-pitch-lyrics`  
**Decision:** `LISTEN-001`  
**Recorded:** 2026-11-02T14:15:19Z  
**Test type:** `singer-similarity`  
**Initial seed:** `20261102`  
**Status:** `blocked` — prerequisites are recorded below; no listening score has been manufactured.

## Purpose

Amend this repository's native plan with the cross-repository blind-listening protocol from `qualitycoding/skills` `protocols/blind-listening-test-execution-plan.md`. This file is the repository-local amendment; it does not override frozen tests and does not create a replacement implementation branch.

## Entry blockers

- G-004 hosted-GPU training/evaluation renders are the active blocker.
- Owner-approved private target-singer phrases and consent records are required.
- Only non-sensitive result metadata may enter public commits.

## Frozen comparison


### Frozen common listening settings

| Setting | Frozen value |
|---|---|
| Primary scored set | 12 matched pairs |
| Primary window | `--window start`; at least one onset set is mandatory |
| Optional diagnostic set | A separately identified `--window middle` set; never pool it with the onset score |
| Clip length | 1.0 s unless this repository later freezes a shorter percussive/effect interval before listening |
| Level | Common RMS at −23 dBFS; retain pre-match level metrics |
| Fades/output | 10 ms fades, mono conversion as implemented by the script, 44.1 kHz PCM-24 WAV unless the repository freezes its working rate |
| Numeric gate | At most 8/12 correct for the primary 12-pair set |
| Qualitative gate | No unresolved finding that contradicts the gate purpose; numeric pass cannot override an adverse demo finding |
| Rounds | Maximum three total, including the initial round |
| Iteration seed | New, previously unused seed after every disclosed round; rounds 2/3 add 1000/2000 to this repository's initial seed |
| p-value | Report exactly; it is evidence, not a substitute for ≤8/12 |
| Changes | General mechanism fixes only, never per-clip/per-note constants tuned to the test set |


## Required procedure

1. Complete every blocker above and keep all frozen metrics/results intact.
2. Build the owner-local staging tree outside the listener bundle:

```text
listening-work/G-001/round-001/
  ref/
  cand/
  blind/
  events/
  demos/
  listener-bundle/
```

3. Build pairs from the repository root:

```bash
python3 scripts/make_blind_pairs.py   --ref listening-work/G-001/round-001/ref   --cand listening-work/G-001/round-001/cand   --out listening-work/G-001/round-001/blind   --seed 20261102   --pairs 12   --window start   --seconds 1.0   --rms-db -23.0   --fade 0.010   --fs 44100
```

4. Render demos from reproducible text event files or reproducible host sessions: lyric intelligibility, sustained vowels, consonants/onsets, pitch transitions, low/high notes, soft/loud phrases, weak lyrics, and local plugin playback.
5. Deliver public evidence only through a real evidence branch with `SHA256SUMS`, or use the private-local route for `sing-vst`.
6. Lock the listener's ordered answers before scoring, then run:

```bash
python3 scripts/score_blind.py   --key listening-work/G-001/round-001/blind/key.json.b64   --answers "<12 ordered A/B answers>"
```

7. Record the exact p-value from the one-sided binomial formula; do not use it to replace the frozen ≤8/12 rule.
8. For iteration, preserve the listener's wording, measure the mechanism, make one targeted general change, rerun affected metrics/reviews, and build the next bundle with the next unused seed.
9. Stop after round 3 unless the allowed response vocabulary explicitly permits another disposition.

## Questions

Ask for one ordered `A`/`B` answer per pair. Then ask the repository-specific weak-spot and demo questions identified in the plan amendment. Verbatim answers, demo numbers, and timestamps are mandatory for adverse findings.

## Response vocabulary

`proceed`, `iterate: <notes>`, `proceed-with-rescope: <text>`, `stop`

## Resume map

- `proceed` → resume `S-017 post-G-001 step`.
- `iterate: <notes>` / `calibrate` → remain at `G-001` and record the next mechanism change, candidate commit, and seed.
- `proceed-with-rescope: <text>` → record the narrowed claim and affected files/tests/docs before moving downstream.
- `stop` / `blocked` → leave the native checkpoint at this gate with the exact missing prerequisite and next action.

## Claim guard

G-005 use-tiger remains unchanged; owner-local listening only and no public voice-audio URLs.
