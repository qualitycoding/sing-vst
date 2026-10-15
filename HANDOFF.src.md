# HANDOFF — sing-vst implementation

## Purpose
Build **sing-vst**: a VST3/Standalone instrument (Windows x64, Linux x64) that sings typed or MIDI-imported lyrics on MIDI
notes in a voice trained from the owner's recordings. A DiffSinger guide renders pitch + lyrics; an RVC v2 model trained on a
free hosted GPU converts the timbre (D-020). Plus the CLI `singvst-render` and the Python toolkit `singvst_train` with the
Colab/Kaggle notebooks.

**Active profiles:** `software`, `computational` (plan/PROFILE.md). `software.deploys = false`.
**Protocol:** qualitycoding/skills `protocols/planning-protocol.md` v3.3 (`9636a79`, D-034).

## Reading order
1. This file. 2. `plan/PLAN.md` (steps). 3. `plan/DECISIONS.md` (interfaces, behaviour, decision rules DR-01…DR-14).
4. `plan/GATES.md`. 5. `plan/ASSUMPTIONS.md` (A-001…A-016, success criteria SC-1…SC-10). 6. `plan/ENVIRONMENT.md`.
7. `plan/TRACEABILITY.md`. 8. `research/PRIOR_KNOWLEDGE.md` (prevention-rule checklist — follow every rule whose `Applies to` is `both`).
9. `premortem/RISK_REGISTER.md`. Background: `research/claims.json`, `research/QUESTIONS.md`, `research/rounds/`.

## Sandbox rules
Environment exactly as `plan/ENVIRONMENT.md` (verified setup commands). Interpreters: `python3.12` for `tools/`,
`../venv-lock/bin/python` for tests and the toolkit; never bare `python3` (PK-55). Long builds: `setsid nohup <cmd> > <log> 2>&1 < /dev/null &`, then poll (PK-18). The shell
may be dash: wrap brace expansion, arrays and `[[ ]]` in `bash -c` (PK-19). Resolve a script's own directory before any `cd`
(PK-57).

## Running the frozen suites
```bash
cmake --build ../build-core && ctest --test-dir ../build-core --output-on-failure            # T-001…T-052, T-063…T-066
cmake --build ../build-full --target singvst_plugin_tests && (cd ../build-full/tests/cpp && xvfb-run -a ./singvst_plugin_tests)  # T-053…T-058
export SINGVST_RENDER_BIN=$PWD/../build-core/cli/singvst-render                               # after S-010
../venv-lock/bin/python -I -m pytest -q -m "not torch and not voice and not network"         # T-P01…T-P27, T-060…T-062
```
T-059 (pluginval) and T-P19 (`torch`) run in CI (`.github/workflows/ci.yml`); T-P20 (`voice`) runs in the owner's notebook
at S-017. Read CI results through the REST API (jobs, steps, check-run annotations), never the log host (D-018, PK-14).

## Verifying the freeze
`sha256sum -c tests/FROZEN_MANIFEST.sha256` must print OK for every line (also T-060 and the CI `repo` job).

## Immutability
Frozen files (everything listed in `tests/FROZEN_MANIFEST.sha256`: tests, fixtures, public headers, `eval/thresholds.json`,
`eval/phrases/*`, `tests/python/interfaces.json`) are never modified, skipped, marked expected-failure or weakened. Python
signatures and docstrings never change (T-P27). If a frozen test is wrong: write `TEST_CHALLENGE.md` (item ID, evidence,
proposed fix) and halt (2E.4, DR-04, PK-24). Never regenerate the manifest.

## Steps at a glance
| Step | What | Tests | Gate |
|---|---|---|---|
{{STEPS}}

The plan begins with **S-000** and ends with the closing steps **S-RETRO** and **S-KNOW**. A step may start as soon as every
step in its `Depends on` has passed; independent steps may run concurrently unless they share an exclusive resource. While
halted at a gate, continue any step that does not depend on that gate's outcome — never an external or irreversible action.

## Human gates
G-001 result (after S-017) · G-002 any external/irreversible action (none scheduled; merging the PR is the owner's) · G-003
lessons/knowledge push (S-KNOW) · G-004 the owner's hosted-GPU training run (S-017) · G-005 guide voicebank (before S-016).
Details, evidence bundles, allowed responses and how a gate is announced and answered: `plan/GATES.md` (the gate file is
saved, the turn ends with a message naming the gate, and the owner's answer is copied verbatim into the file).

## Tiers
Each step names a model tier (Haiku < Sonnet < Opus < Fable). Run the step yourself when you are at or above that tier, or
delegate it to a subagent of that tier when your environment offers subagents; otherwise use the next higher available tier
and record the substitution with `python3.12 tools/checkpoint.py --set 'tier_substitutions=[…]'` (protocol Global Rule 5).
S-RETRO's "fresh Opus agent" means a subagent that has not seen the run; without subagents, write the retrospective from the
digest alone and say so in RETROSPECTIVE.md.

## Git rules
Every command that writes into the repository ends with `bash tools/save.sh "<msg>" <paths>` — commit, push and checkpoint
in one call (PK-52); stage only the named paths (PK-08). After a push by any non-git mechanism, fetch and reset to the remote
tip; never rewrite published history (PK-49). The last call of every turn is `bash tools/turn_end_check.sh` (clean, pushed,
no tokens in the repository or git config).

## Logs
`EXECUTION_LOG.md` — one row per step attempt:
`| UTC time | Step | Attempt | Result (pass/fail/blocked) | Commit before this row | Note |` (the commit is HEAD before the
save that adds the row). `DEVIATIONS.md` — `| UTC time | Step | Plan says | Done instead | Why (rule applied) |`.

## Files created on demand
`BLOCKED.md` (on a halt), `TEST_CHALLENGE.md` (on a frozen-test challenge), `GATE-<id>.md` (at a gate), `RETROSPECTIVE.md`
(S-RETRO) — all at the repository root. They do not exist until their event happens.

## Amendments (planning changes during implementation)
The implementer never edits frozen files, `eval/thresholds.json`, `tests/python/interfaces.json` or the manifest, and never
runs `tools/freeze.py` or `tools/gen/interfaces.py`. When a gate response or a test challenge needs a planning change
(G-001 `proceed-with-thresholds`, G-005 `use-voicebank`, TEST_CHALLENGE.md), the implementer halts and says so; the owner
starts a planning session that runs the amendment of plan/PROTOCOL_EXCERPTS.md §2E.4 (re-research, re-freeze with
`tools/freeze.py`, cold read and pre-mortem on the changed items) and pushes to the generation branch; the implementer then
merges the generation branch into the impl branch and resumes.

## Halt / deviation protocol
- Work on `impl-gen-20261004T095012Z-singing-voice-vst-pitch-lyrics`. Every command that writes into the repository ends with
  `bash tools/save.sh "<msg>" <paths>` (commit, push and checkpoint in one call; PK-52). The last call of every turn is
  `bash tools/turn_end_check.sh` (clean, pushed, no tokens).
- `EXECUTION_LOG.md`: one line per step attempt — UTC time, step ID, attempt, `pass|fail|blocked`, commit, note.
- `DEVIATIONS.md`: open it at the first departure from the plan; log every default-rule choice with its rationale.
- `BLOCKED.md`: write it and halt when a decision rule says so, when the default rule touches frozen tests, security, data
  integrity, a public interface, research integrity, licences or consent, or after three failed attempts on one test.
- Default rule: choose the most reversible option that does not expand scope, log it in DEVIATIONS.md, and continue.

## Resume (zero-context, protocol v3.3 1.2.3)
1. Read `.checkpoints/state.json` (or the highest `.checkpoints/snapshots/*-seq-<N>.json`). 2. Verify every artifact hash;
re-run the generating step of any mismatch. 3. Rehydrate `active_variables` and `execution_context`. 4. If
`in_flight_operation` is not null, reconcile its side effects (git log, CI run, files) before repeating anything. 5. Continue
from `active_step_id` / `step_pointer.sub_action`. Checkpoints: `python3 tools/checkpoint.py --active-step S-### --objective
… --pointer '{…}' --scratchpad …` before every high-latency action (build, CI wait, gate) and via every save.

## Working rules (from the prevention checklist; follow every rule marked `both` in research/PRIOR_KNOWLEDGE.md)
After a scripted edit, check the result in the same command (PK-10). If a tool result is empty or says NOT RUN, re-run it
before writing about it (PK-11). Every number in a report or log is produced by a command (PK-05). Every behaviour claim
cites a test, a spike or a source opened in this run, or says UNVERIFIED (PK-04); nothing is said about how the voice sounds
without the G-001 listening record (PK-46). After a push by any non-git mechanism, fetch and reset to the remote tip (PK-49).

## Integrity (Rule 9, verbatim)
{{RULE:9}}

## Lessons, knowledge and the store (Rules 11, 12, 13, verbatim)
{{RULE:11}}

{{RULE:12}}

{{RULE:13}}

During this run lessons go to `lessons/L-<UTC>-<slug>.md` and knowledge items to `knowledge/K-<UTC>-<slug>.md` on the impl
branch (templates: protocol Appendices A and B; check with `python3 tools/check_schema.py`). They reach the store only at
S-KNOW after G-003.

## Figures and publication
None: no deliverable figures (D-032); no manuscript (profile `publication` inactive).
