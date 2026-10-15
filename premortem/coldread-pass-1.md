# Cold read pass 1 (3.6) — 2026-10-15, branch at dd45685

Agents: fresh Sonnet (dry run of HANDOFF.md + plan/PLAN.md, read-only clone) and fresh Haiku (mechanical checks 3.6.2).
Totals: Sonnet 38 items, Haiku 10 items. Each item is resolved by amending the plan (never in chat); the resolution column
names the change. Items are paraphrased; the agents' full outputs are summarised faithfully.

## Haiku (mechanical)
| ID | Item | Resolution |
|---|---|---|
| H1 | S-011 names GATE-G-001.md (created at S-017) — forward artefact | S-011 writes docs/UNVERIFIED.md; S-017 copies it into GATE-G-001.md |
| H2–H5 | BLOCKED.md / TEST_CHALLENGE.md cited as inputs but created only on halt | marked "(if present)"; HANDOFF §Files created on demand |
| H6 | rvc/assets/hubert_base exists only in the CI job's RVC checkout | S-013 wording: "in the CI python-torch job" |
| H7 | requirments_cu128_py312.txt is an upstream RVC file | S-016 names it as a file of the RVC checkout at 81eed5e (C-023) |
| H8 | protocol file is external | plan/PROTOCOL_EXCERPTS.md (verbatim excerpts, generated) |
| H9 | "T-P13b" (and T-P19b) are not IDs; docstrings say T-P13 / T-P19 | references rewritten as "T-P13 (binary part)" / "T-P19 (content encoder)" |
| H10 | S-012 Done-when needs S-010's binary | binary part of T-P13 moved to S-010 only |

## Sonnet (dry run)
| ID | Item | Resolution |
|---|---|---|
| S1 | CI `repo` runs T-P23 before S-018 writes the README; later step skipped; D-023 says S-019 | ci.yml: T-P23 in its own step, lock step `if: always()`; S-001 defines repo green except T-P23 until S-018; D-023 → S-018 |
| S2 | S-017 may commit audio, T-062 forbids it; zip banned | renders never committed; only report.json, sidecar, verdict.json |
| S3 | amendment procedure (2E.4) undefined for the implementer | HANDOFF §Amendments + PROTOCOL_EXCERPTS 2E.4 |
| S4 | HF revision cannot be read from CI | ci.yml prints `::notice title=hf-revision::<sha>` via HfApi; S-013 edits ENVIRONMENT.md pins |
| S5 | no local loop for T-P19; attempt undefined | D-036: no local torch; attempt = one CI run; local RVC clone path |
| S6 | no plugin artifact for the owner; binaries vs G-002 | G-001: owner builds from source (instructions in GATE file); no plugin binaries uploaded (D-026) |
| S7 | S-000 tag source / "newer than" / knowledge_store keys | S-000 rewritten; checkpoint.py --merge |
| S8 | protocol sections not in the repo | plan/PROTOCOL_EXCERPTS.md |
| S9 | S-012 must register all nine sub-commands for T-P25 | S-012 action says so |
| S10 | CLI options, notebook layout, RVC invocations undefined | D-035 CLI and notebook specification |
| S11 | T-P27 constraints (public names, constants, heavy imports) | D-033 extended |
| S12 | TIGER URL, nesting, role mapping, embedding, depth clamping | D-035 §Guide voicebank; errata for the clamping comment |
| S13 | onnx pin mismatch; cu128 export unverified | D-019 fixed (onnx 1.23.2); notebook runs T-P19 in its own env |
| S14 | standardNormal declared in engine.hpp, step mismatch | assigned to S-007 (core/src/random.cpp) |
| S15 | D-008 mentions juce::SHA256 | removed |
| S16 | interpreter inconsistency; network tests in local suite | python3.12 / venv everywhere; local suite excludes `network` |
| S17 | attribution hard-coded in save.sh | save.sh reads SINGVST_COMMIT_TRAILERS; PR trailer defined |
| S18 | gh auth, sudo, tool preflight | S-000 preflight list and fallbacks |
| S19 | sanitizer build commands incomplete | ENVIRONMENT.md build-asan / build-tsan lines |
| S20 | unquoted gh api URL, HEAD run selection | quoted, filtered by head_sha |
| S21 | CI waiting/pass rule undefined | D-036 CI rules |
| S22 | concurrency on one branch | steps run sequentially in ID order |
| S23 | Tier field undefined | HANDOFF §Tiers |
| S24 | oracle comparison undefined | S-008: oracle is a debugging reference; pass = frozen tests |
| S25 | stale PK "applied via" references; planner-only rules | checklist corrected; Applies-to column; HANDOFF sections renamed |
| S26 | eval/PROCEDURE.md missing | written and frozen |
| S27 | notebook final cells, uploads, verdict.json, env vars | D-035 §Evaluation and upload |
| S28 | = H10 | as H10 |
| S29 | where gate files live; channel | HANDOFF §Gates (repo root; final message of the turn; response recorded verbatim) |
| S30 | log formats | HANDOFF §Logs (table templates; commit = HEAD before the logging commit) |
| S31 | D-008 required keys / defaults | D-008 table of required keys and defaults (from T-028/T-029 fixtures) |
| S32 | m50/m1100 undefined | defined in D-007 |
| S33 | stale comments in frozen headers / pytest.ini | DECISIONS errata section; pytest.ini fixed |
| S34 | PARAMETERS.md generator unspecified | S-018: parser and table format |
| S35 | DR-08 unreachable | DR-08 uses the report's RTF (notebook) and G-001 |
| S36 | main branch unverified | S-000 checks main is the default branch |
| S37 | state.json not ready for the implementer | Phase 5 resets state.json (pending = S-000…S-KNOW) |
| S38 | turn_end_check scans all of $HOME | scan the repository and git config only |
