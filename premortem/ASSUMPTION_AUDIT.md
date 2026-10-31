# Assumption & Premise Audit (protocol v3.6 Phase 4.7; Amendment 01 AM-08)

Run 2026-10-31T10:53:28Z, retroactively, with S-000…S-016 done and the plan halted at G-004. **Auditor:** the implementing agent (claude-opus-5-5), which did
not author the plan but is not fresh context for the implementation; no subagent was used (recorded in DEVIATIONS.md). Stance:
each item was assumed wrong and checked against evidence; facts established during implementation count as evidence and are cited.

Verdicts (counted from the tables below): **confirmed** 25 · **falsified** 4 · **unverifiable** 11 (each unverifiable item maps to a risk, gate or in-notebook check).

## Assumptions (plan/ASSUMPTIONS.md)
| Item | Premise in one sentence | Falsifying evidence would be | Checked | Verdict | IDs |
|---|---|---|---|---|---|
| A-001 | Planning ran in Claude's cloud workspace with subagents. | planning records showing otherwise | premortem/ and state.json history | confirmed | — |
| A-002 | Target repo is github.com/qualitycoding/sing-vst, public, Apache-2.0. | API says private / other licence | `gh api`: private=false, Apache-2.0 | confirmed | — |
| A-003 | DiffSinger guide + RVC converter produce the voice. | a contract the engines cannot meet | T-042…T-049 pass with real ONNX Runtime on both OSes; sound quality only at G-001 | confirmed (structure); quality → G-001 | SC-10 |
| A-004 | RVC is MIT and maintained; so-vits-svc archived AGPL. | licence/archived flags differ | `gh api`: RVC MIT, not archived; so-vits-svc archived, AGPL-3.0 | confirmed | — |
| A-005 | Lyrics come from the text box or MIDI lyric events; hosts cannot send lyric text to a VST3. | a JUCE/VST3 lyric API | C-011 (verified); T-056 imports lyric events | confirmed | — |
| A-006 | Lookahead rendering synced to the host position. | host position not available | T-032, T-033, T-055, T-057 (fake host); real DAWs unverified | confirmed (tested); DAW → docs/UNVERIFIED.md | R-014 |
| A-007 | English via CMUdict. | dictionary unusable | T-012: 126052 words, all 39 phones | confirmed | — |
| A-008 | C++20, JUCE 9.0.3, VST3+Standalone on Windows and Linux, ORT 1.31.0 CPU. | build or load fails on a platform | CI cpp jobs green on ubuntu-24.04 and windows-2022 incl. pluginval (run 40103923321) | confirmed | — |
| A-009 | The owner can train on a free Colab GPU (Kaggle fallback). | no free GPU available to the owner | only the owner can check, at G-004 | unverifiable | R-001, R-002, G-004 |
| A-010 | 10–60 min of the owner's mono singing per voice. | fewer recordings | owner data; cell (7) stops below 10 min / 30 s (R-031) | unverifiable | R-031 |
| A-011 | Recordings are the owner's or used with consent; use within platform terms. | — | owner attestation at G-004 (cell (2), question 1) | unverifiable (by design: owner's statement) | G-004 |
| A-012 | SC-1…SC-10 as listed; SC-4…SC-7 unmeasured defaults. | — | eval/thresholds.json status unmeasured-default; D-041 §Targets names environments and miss rules | confirmed | D-041 |
| A-013 | JUCE is AGPLv3 or commercial, so only source is published. | JUCE 9 licence text differs | ~/deps/JUCE/LICENSE.md: "dual-licensed under the AGPLv3 and the commercial JUCE licence" | confirmed | — |
| A-014 | Stores are qualitycoding/Lessons and qualitycoding/knowledge, private. | different names or public | `gh api`: both private=true; v3.6's default-name correction does not affect this run | confirmed | — |
| A-015 | ≤ 20 GPU-hours per voice, ≤ 10 h per session. | — | a budget choice (owner default), enforced by cell (11) and tested by the dry run (scenarios 7, 8) | confirmed (as a decision) | — |
| A-016 | The implementer works in the cloud workspace and cannot reach Colab/Kaggle/PyTorch/HF (C-044). | the implementer reaches those hosts | S-000 host probe on the owner's machine: all reachable; local torch and HF downloads worked (S-013) | **falsified** | L-20261030T234149Z-implementer-host-differs-from-planning-sandbox, K-20261030T234151Z-c-044-implementation-host-reachability, D-043 |

## Decision premises the remaining steps rely on
| Item | Premise | Checked | Verdict | IDs |
|---|---|---|---|---|
| D-008 | TIGER's files fill the four guide roles. | C-036 spike tiger-guide; pack stage run for real with stand-ins (S-016) | confirmed | — |
| D-010 | JUCE's PositionInfo gives ppq/bpm/isPlaying each block. | T-055, T-057 | confirmed | — |
| D-012 | The prior noise is RVC's only random draw, so `rnd` alone makes the converter deterministic (C-003). | ../rvc infer/module/models.py SineGen.forward calls torch.randn_like | **falsified** (handled in S-013; contract text corrected by D-043) | L-20261030T234148Z-rvc-has-two-noise-sources, K-20261024T151050Z-rvc-sinegen-noise, D-043 |
| D-012 | 48k RVC synth hop is 480 from upsample rates 10,6,2,2,2 (C-048). | configs/v2/48k.json [12,10,2,2] | **falsified** in detail (product 480 holds) | L-20261030T234151Z-claim-detail-not-cross-checked-with-config, K-20261030T234152Z-c-048-rvc-48k-upsample-rates |
| D-013 | Limits 5000 notes / 900 s before any engine runs. | T-069, T-070 | confirmed | — |
| D-016 | Colab/Kaggle sessions last ≤ 12 h with unpublished limits (C-017, C-019). | C-017 corroborated; C-019 single-source | unverifiable (owner's platform) | R-002, R-008 |
| D-017 | Resemblyzer/Whisper APIs as named; procedure computable. | S-015 dry run with stand-ins of the real names (C-058, C-059); real models only in the notebook | confirmed (API names); values → G-001 | T-P20 |
| D-019 | RVC's cu128 file + toolkit resolve in one venv; torch pair from its own index. | AM-06 spike: cu128 torch resolves; RVC file (no torch lines) resolves 139 packages from PyPI | confirmed | C-070 |
| D-019 | The lock is pip-audit clean. | S-000: setuptools 84.0.0 advisory → DR-07 (84.1.0) | confirmed after DR-07 (a dated fact, not an assumption error) | — |
| D-025 | audio-separator must live in its own venv; stem `noreverb`. | C-066 (wheel); stem name from the model YAML at load time | confirmed (venv); stem name unverifiable | docs/UNVERIFIED.md |
| D-026 | TIGER is personal non-commercial; never redistributed. | C-037 licence texts; G-005 answered use-tiger | confirmed | — |
| D-035 | nvidia-smi query fields name, driver_version, pid, used_memory exist. | NVIDIA docs defer field names to --help-query-* (C-068) | unverifiable → checked first in cell (4c) | C-068 |
| D-035 | Kaggle output holds ≤ 500 items (C-064); state.tar keeps it small. | single source | unverifiable | R-016, R-055 |
| D-036 | No torch locally; plugin checks CI-only without root. | local torch (S-013) and user-space sysroot build + Xvfb + pluginval (S-011) | **falsified** (same root cause as A-016, plus the no-root premise) | L-20261030T234149Z-implementer-host-differs-from-planning-sandbox, L-20261030T234150Z-no-root-is-not-no-local-plugin-build, D-043 |

## Single-source and inferred claims
| Claim | Verdict | Mitigation |
|---|---|---|
| C-010 (no OSI/CC-BY English DiffSinger voicebank found) | unverifiable (absence claim) | G-005 answered; D-026 licence handling |
| C-019 (Kaggle session and quota facts) | unverifiable | R-008; Colab is the first platform |
| C-064 (Kaggle 500-item output limit) | unverifiable | state.tar design (≤ 20 items asserted by pack_state) |
| C-068 (nvidia-smi documentation) | unverifiable for field names | cell (4c) check, decision rule `failed: 4` |

## Premises frozen tests rely on
| Test | Premise | Verdict |
|---|---|---|
| T-034 | CI installs de_DE.UTF-8 | confirmed (passes in CI) |
| T-041 | explicit-path ORT loading works on Windows | confirmed (CI windows-2022) |
| T-P10 | pyworld via its extension gives < 1 cent on the known tone | confirmed |
| T-P19 | an export with `rnd` as the only noise input is deterministic | confirmed only with SineGen noise taken from `rnd` (D-043) |
| T-059 | pluginval strictness 5 passes on the real plugin | confirmed (both OSes) |
| T-P20 | owner runs evaluation on real voice | unverifiable until G-004/G-001 |

## Consequences (2E.4)
Every falsified item was already corrected in the implementation (S-011, S-013, S-000) and logged; what remained was the plan text.
D-043 (Amendment 02, generation branch) records the corrected D-012 converter contract, the conditional D-036 / S-000 rules and C-048's
values, and runs with Amendment 02's cold read and pre-mortem round. No frozen test changes; no re-freeze.
