# HANDOFF — sing-vst implementation

## Purpose
Build **sing-vst**: a VST3/Standalone instrument (Windows x64, Linux x64) that sings typed or MIDI-imported lyrics on MIDI
notes in a voice trained from the owner's recordings. A DiffSinger guide renders pitch + lyrics; an RVC v2 model trained on a
free hosted GPU converts the timbre (D-020). Plus the CLI `singvst-render` and the Python toolkit `singvst_train` with the
Colab/Kaggle notebooks.

**Active profiles:** `software`, `computational` (plan/PROFILE.md). `software.deploys = false`.
**Protocol:** planning protocol v3.3 (external repository qualitycoding/skills, commit `9636a79`, D-034); every
section the implementer needs is copied verbatim in `plan/PROTOCOL_EXCERPTS.md`.

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
cmake --build ../build-core --parallel 2 && ctest --test-dir ../build-core --output-on-failure            # T-001…T-052, T-063…T-070
cmake --build ../build-full --parallel 2 --target singvst_plugin_tests && (cd ../build-full/tests/cpp && xvfb-run -a ./singvst_plugin_tests)  # T-053…T-058
export SINGVST_RENDER_BIN=$PWD/../build-core/cli/singvst-render                               # after S-010
../venv-lock/bin/python -I -m pytest -q -m "not torch and not voice and not network"         # T-P01…T-P27, T-060…T-062
```
T-059 (pluginval) and T-P19 (`torch`) run in CI (`.github/workflows/ci.yml`); T-P20 (`voice`) runs in the owner's notebook
at S-017. Read CI results through the REST API (jobs, steps, check-run annotations), never the log host (D-018, PK-14).

## Verifying the freeze
`sha256sum -c tests/FROZEN_MANIFEST.sha256` must print OK for every line (also T-060 and the CI `repo` job).

## Immutability
Frozen files (everything listed in `tests/FROZEN_MANIFEST.sha256`: tests, fixtures, public headers, `eval/thresholds.json`,
`eval/PROCEDURE.md`, `eval/phrases/*`, `tests/python/interfaces.json`) are never modified, skipped, marked expected-failure or weakened. Python
signatures and docstrings never change (T-P27). If a frozen test is wrong: write `TEST_CHALLENGE.md` (item ID, evidence,
proposed fix) and halt (2E.4, DR-04, PK-24). Never regenerate the manifest.

## Steps at a glance
| Step | What | Tests | Gate |
|---|---|---|---|
| S-000 | Environment & access verification | none | none |
| S-001 | CI baseline on both platforms | T-059 (stub), Q-E7 answer | none |
| S-002 | Lyrics, pronunciation and alignment | T-001…T-018 | none |
| S-003 | Timing, pitch, gain and noise | T-019…T-027 | none |
| S-004 | Voice package and SHA-256 | T-028…T-031, T-063 | none |
| S-005 | Playback, phrase hash, capture and plugin state | T-032…T-038 | none |
| S-006 | Standard MIDI File import | T-064…T-066, T-069 | none |
| S-007 | Resampler and runtime loading | T-039…T-041 | none |
| S-008 | Guide and converter engines | T-042…T-047 | none |
| S-009 | Render pipeline and background renderer | T-048…T-052, T-067, T-068, T-070 | none |
| S-010 | CLI `singvst-render` | T-P18 | none |
| S-011 | Plugin processor and editor | T-053…T-058, T-059 | none |
| S-012 | Python toolkit core | T-P01…T-P15 (T-P13 including its binary part `test_P13b_…`), T-P25 | none |
| S-013 | RVC → ONNX export | T-P19 (both functions, incl. the content-encoder part `test_P19b_…`) | none |
| S-014 | RVC training files | T-P24 | none |
| S-015 | Evaluation procedure | T-P26 | G-005 |
| S-016 | Training notebooks | T-P16, T-P17; `tools/notebook_dryrun.py` output in EXECUTION_LOG.md | G-005 must be answered before this step starts. |
| S-017 | Owner's training run and evaluation | T-P20 (run by the owner); G-001 record | G-004, then G-001 |
| S-018 | Documentation and notices | T-P23 | none |
| S-019 | Final verification and pull request | all tests | none (merging is the owner's action, G-002) |
| S-RETRO | Retrospective | none | none |
| S-KNOW | Lessons and knowledge push | none | G-003 |

The plan begins with **S-000** and ends with the closing steps **S-RETRO** and **S-KNOW**. A step may start as soon as every
step in its `Depends on` has passed, and steps run one at a time in ID order (they share one branch and checkpoint). While
halted at a gate, continue any later step that does not depend on that gate's outcome, in ID order — never an external or
irreversible action.

## Human gates
G-001 result (after S-017) · G-002 any external/irreversible action (none scheduled; merging the PR is the owner's) · G-003
lessons/knowledge push (S-KNOW) · G-004 the owner's hosted-GPU training run (S-017) · G-005 guide voicebank (before S-016).
Details, evidence bundles, allowed responses and how a gate is announced and answered: `plan/GATES.md` (the gate file is
saved, the turn ends with a message naming the gate, and the owner's answer is copied verbatim into the file).

## Tiers
Each step names a model tier (Haiku < Sonnet < Opus < Fable; Fable is the Mythos tier of protocol 0.2). Your own tier is the
model your session reports. Run the step yourself when you are at or above that tier, or delegate it to a subagent of that
tier when your environment offers subagents (plan/PROTOCOL_EXCERPTS.md, Global Rule 5). If neither is possible, run it
yourself and record the substitution: `python3.12 tools/checkpoint.py --append 'tier_substitutions={"step": "S-###",
"wanted": "<tier>", "used": "<model>"}'` plus a DEVIATIONS.md row.
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
Every session begins with the S-000 preamble (recreate missing out-of-tree artefacts, including `.git/singvst-trailers`,
before the first save — `tools/save.sh` refuses to commit without trailers). `*.src.md` files are generator inputs
(`tools/gen/`); do not read or edit them. No step edits `.github/workflows/`; a change there is a planning amendment
(pushing it also needs the credential's workflow permission).
This procedure applies once S-000 has set `phase` to `impl`. A first implementation session (state.json `phase` is not
`impl`) starts at S-000 and ignores the planner's `active_step_id` and `in_flight_operation`.
1. Read `.checkpoints/state.json` (or the highest `.checkpoints/snapshots/*-seq-<N>.json`). 2. Verify every artifact hash;
re-run the generating step of any mismatch. 3. Rehydrate `active_variables` and `execution_context`. 4. If
`in_flight_operation` is not null, reconcile its side effects (git log, CI run, files) before repeating anything. 5. Continue
from `active_step_id` / `step_pointer.sub_action`. Checkpoints: `python3.12 tools/checkpoint.py --active-step S-### --objective
… --pointer '{…}' --scratchpad …` before every high-latency action (build, CI wait, gate) and via every save.

## Working rules (from the prevention checklist; follow every rule marked `both` in research/PRIOR_KNOWLEDGE.md)
After a scripted edit, check the result in the same command (PK-10). If a tool result is empty or says NOT RUN, re-run it
before writing about it (PK-11). Every number in a report or log is produced by a command (PK-05). Every behaviour claim
cites a test, a spike or a source opened in this run, or says UNVERIFIED (PK-04); nothing is said about how the voice sounds
without the G-001 listening record (PK-46). After a push by any non-git mechanism, fetch and reset to the remote tip (PK-49).

## Integrity (Rule 9, verbatim)
9. **Integrity** `[All]`: No step may fabricate, cherry-pick without disclosure, or manually alter data, test results, benchmarks, or figures. In addition:
   * `[computational, publication]` Every reported number is generated from committed results, not transcribed by hand.
   * `[publication]` Generative-AI images are never used as data figures. AI assistance is disclosed according to the venue's policy, as recorded in `plan/ASSUMPTIONS.md`.

## Lessons, knowledge and the store (Rules 11, 12, 13, verbatim)
11. **Lessons** `[All]`: Whenever the executing agent corrects its own execution, it records a lesson before continuing. The *executing agent* is the planning agent while it runs this protocol, and the implementing agent while it runs the plan. A *correction* is any of:
    * redoing or reverting something the agent did;
    * a command, assumption, or edit that failed and was fixed by taking a different approach;
    * a check (test, cold read, proof review, pre-mortem, CI) that caught the agent's own mistake;
    * a correction from the human.

    Retrying the same action after a transient failure is not a correction, and neither is a failure the protocol plans for (such as tests failing red against stubs).
    * Each lesson is one file, `lessons/L-<YYYYMMDDTHHMMSSZ>-<slug>.md`, on the working branch, using the template in Appendix A. It is committed before work continues.
    * A lesson carries the *identifying information* that lets a future agent recognise the situation before repeating the mistake: the trigger (the circumstances and observable signals), the mistake, the correction, a prevention rule written as one imperative, checkable instruction, and a detection check.
    * Every lesson is classified with tags from the store taxonomy (Appendix C), so lessons can be read as a group: for example, all `tech:java` lessons, or all `domain:audio` lessons.
    * If the mistake repeats a lesson loaded in R0, the new lesson names it in `recurrence_of` and strengthens its prevention rule; a recurrence means the earlier rule did not work.
    * If the same mistake recurs within the run, increase `occurrences` on the run's existing lesson and add the new evidence, instead of writing a second file.

12. **Knowledge Base** `[All]`: All supporting research and derived knowledge is recorded as knowledge items, so later work can reuse it instead of researching it again. Whenever either agent discovers a new fact about the task's Subject (its technologies, formats, APIs, platforms, tools, mathematical objects, or venues), it adds an item before continuing.
    * Each item is one file, `knowledge/K-<YYYYMMDDTHHMMSSZ>-<slug>.md`, on the working branch, using the template in Appendix B. It records the fact, its source and locator, the version it applies to, its confidence, and the claim it derives from (`C-###`), if any.
    * Every item is classified with tags from the store taxonomy (Appendix C), including at least one `subject:` tag, so it can be found again.
    * A fact that turns out wrong or outdated is never edited away: a new item `supersedes` it, so the history remains.

13. **Knowledge Store** `[All]`: Lessons and knowledge items persist across tasks in the knowledge store recorded at intake (`A-###`; layout in Appendix C). The store is read at the start of research (R0) and written only at the end of implementation, after gate `G-003` (3.7.2). During a run, new lessons and items accumulate on the working branch. Lessons and items must never contain credentials, tokens, secrets, or personal data; redact them (for example, `github_pat_***`).

During this run lessons go to `lessons/L-<UTC>-<slug>.md` and knowledge items to `knowledge/K-<UTC>-<slug>.md` on the impl
branch (templates: protocol Appendices A and B; check with `python3.12 tools/check_schema.py`). They reach the store only at
S-KNOW after G-003.

## Figures and publication
None: no deliverable figures (D-032); no manuscript (profile `publication` inactive).
