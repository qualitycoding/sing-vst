# Amendment 01 — planning protocol v3.3 → v3.6, applied up to gate G-004 (D-041)

**Requested by:** the owner, 2026-10-30 ("compare with the planning protocol we followed and create an amendment plan up to the
current point G-004").
**Baseline:** this plan was written under planning protocol **v3.3** (`qualitycoding/skills` commit `9636a79`, D-034).
**Target:** planning protocol **v3.6** (`qualitycoding/skills` commit `b361dab`, `protocols/planning-protocol.md`).
**State at the amendment:** steps S-000…S-016 passed (EXECUTION_LOG.md), G-005 answered `use-tiger`, S-017 action 1 issued
GATE-G-004.md (RUN 1, Colab, `EXPECTED_COMMIT` `6cffb4c5…`) and no owner response has arrived. Implementation is halted at G-004.

This document has two parts. **Part 1** compares the protocols and decides, item by item, what applies to this run. **Part 2**
is the amendment's own step list (`AM-01`…`AM-10`), which brings the completed work up to v3.6 without changing any frozen
file. The forward changes to the remaining steps (S-017 onward: new review steps, Rule 14 post-conditions, retrospective
check) are a separate planning change, Amendment 02 (D-042), because they extend the plan rather than repair the past.

## Part 1 — What changed, and what it means here

| Protocol change | Version | Applies? | Already satisfied by | Gap for work done up to G-004 | Action |
|---|---|---|---|---|---|
| 0.1 environment class `stable`/`ephemeral` recorded in the checkpoint | v3.6 | yes (probe); 1.5 only if `ephemeral` | — | no class recorded; the implementation machine was never probed | AM-02 |
| 1.5 ephemeral-environment protections | v3.6 | only if AM-02 finds `ephemeral` | — | none if `stable` | AM-02 decides |
| Global Rule 6 push cadence: push after every green chunk, verify with `ls-remote`, retry with backoff | v3.6 | yes | `tools/save.sh` commits, pushes (3 attempts) and re-fetches after every step; `tools/turn_end_check.sh` | no `ls-remote` comparison of remote and local HEAD; retries are not exponential | AM-03 |
| Rule 14 no swallowed failures | v3.5 | yes | CI has none (checked: `grep -E '\|\| *true|continue-on-error|set \+e' .github`) | one load-bearing `\|\| true` in notebook cell (4) (`uv pip uninstall … \|\| true`) | AM-04 |
| Rule 14 artifact post-conditions in every Done-when; CI asserts artifacts | v3.5 | yes | many Done-when lines name tests only | the artifacts of S-000…S-016 were never checked as a set (exists, non-empty, parses) | AM-05 (past); D-042 (future) |
| Rule 14 budgets gate; per-environment targets with pre-decided miss rules | v3.5 | yes | numeric thresholds in frozen tests fail CI; SC-4…SC-7 are unknown-outcome thresholds judged at G-001 by design (2B.4, PK-29) | the RTF target (SC-7, `realtime_factor_max` 1.0) does not name its environments or a miss rule per environment | AM-04 records D-041 §Targets |
| Rule 14 substitutions are deviations, logged when made | v3.5 | yes | DEVIATIONS.md has 30+ rows | never diffed against plan/ENVIRONMENT.md | AM-07 |
| 1.3.6 pins must exist; commands verified (spike or pinned-version doc) | v3.5 | yes | research/spikes/deps-pins, hf-cli, uv-python, ort, red-verification | notebook pins (uv, torch cu128, audio-separator, whisper, webrtcvad-wheels, resemblyzer) and several notebook commands have no recorded existence check / spike | AM-06 |
| 3.7.1 (1a) retrospective verifies DEVIATIONS.md against the diff | v3.5 | yes (at S-RETRO) | — | S-RETRO text lacks it | D-042 (future); AM-07 runs it once now |
| 3.8 `S-REVIEW`, `S-ADVERSARIAL`; `S-MUTATE` or an opt-out `D-###` | v3.4 | yes (`software` profile) | — | steps missing | D-042 (future) |
| 4.7 Assumption & Premise Audit after pre-mortem convergence | v3.4 | yes | — | never run; several premises were already contradicted during implementation (see AM-08) | AM-08 |
| Phase 5 summary: audit verdicts, review findings, 1.3.6 checks | v3.4–v3.6 | yes | — | status header lacks them | AM-10, D-042 |
| HANDOFF restates Rules 6 (with push cadence), 11, 12, 13 | v3.6 | yes | Rules 9, 11, 12, 13 restated | Rule 6 and Rule 14 not restated | AM-01 |
| 0.3.1 default knowledge-store name `knowledge` | correction | no effect | A-014 already names `qualitycoding/knowledge` | — | — |

**Frozen files are not touched.** No amendment action changes a test, fixture, public header, `eval/thresholds.json`,
`eval/PROCEDURE.md`, `eval/phrases/*` or `tests/python/interfaces.json`; `tools/freeze.py` is not run;
`sha256sum -c tests/FROZEN_MANIFEST.sha256` must stay OK after every action.

## Part 2 — Amendment steps

Each step uses the protocol 3.1 template. They run on the impl branch after this branch is merged into it (HANDOFF
§Amendments), in ID order, one at a time; every one ends with `bash tools/save.sh` (push cadence, AM-03 from then on).
Tier: Opus for AM-08 (a fresh-context adversarial audit), Sonnet for the rest.

### AM-01 Adopt v3.6 in the planning artefacts
- Actions: regenerate `plan/PROTOCOL_EXCERPTS.md` from the v3.6 protocol at `b361dab` with the new sections (1.3.6, 1.5, 3.8,
  4.7; Rule 14 is part of the Global Rules excerpt); `HANDOFF.md` names v3.6 / D-041, restates Rules 6 and 14 verbatim and
  links this file; record `protocol_version` 3.6 and the commit in `.checkpoints/state.json`.
- Done when: `grep -c 'v3.6' plan/PROTOCOL_EXCERPTS.md HANDOFF.md` ≥ 1 each; `grep -n '^14\. \*\*Honest Verification'
  plan/PROTOCOL_EXCERPTS.md HANDOFF.md` finds both; state.json holds `"protocol_version": "3.6"`. Post-condition: both
  files are non-empty Markdown and `python3.12 tools/check_schema.py` passes.

### AM-02 Environment-class probe (0.1)
- Actions: `bash research/spikes/env-class/run.sh` records boot time, whether files written by this session in earlier
  turns still exist under `/tmp` and `../`, and whether a background process started in an earlier tool call is still
  alive. Class `ephemeral` if any of them is lost, else `stable`; write `environment_class` and the evidence into
  `.checkpoints/state.json`. If `ephemeral`: stop and plan 1.5 protections in a further amendment.
- Done when: `research/spikes/env-class/output.txt` exists, names the class and its three observations; state.json
  `environment_class` ∈ {`stable`, `ephemeral`}.

### AM-03 Push cadence (Rule 6)
- Actions: `tools/save.sh` retries a failed push with exponential backoff (2, 4, 8, 16 s) and then compares
  `git ls-remote origin refs/heads/<branch>` with `git rev-parse HEAD`, failing on a mismatch; `tools/turn_end_check.sh`
  makes the same comparison. Verify once now for the impl and generation branches.
- Done when: both scripts contain `ls-remote`; the verification prints equal hashes for both branches; a save after the
  change reports the remote hash.

### AM-04 Honest verification audit (Rule 14)
- Actions: scan every file the plan runs (`.github/workflows`, `tools/`, `python/`, `cmake/`, `CMakeLists.txt`,
  `notebooks/`, `tools/notebook_cells/`) for `|| true`, `continue-on-error`, `set +e` and bare `except:`/`except
  Exception: pass`; fix every load-bearing hit (cell (4)'s `uv pip uninstall … || true` becomes an explicit uninstall of
  only the installed distributions, failing visibly); list every numeric-threshold `T-###` and the CI step whose failure
  fails the build; check every CI upload step fails when it finds nothing. Record in `reviews/RULE14_AUDIT.md`.
- Done when: the scan prints no load-bearing hit; `reviews/RULE14_AUDIT.md` lists every threshold test with its gating CI
  step; T-P16, T-P17 and `tools/notebook_dryrun.py` still pass after the notebook change.

### AM-05 Post-condition audit of S-000…S-016 (Rule 14)
- Actions: `tools/check_postconditions.py` checks every artifact the completed steps produced (the step's `Outputs`
  list): exists, non-empty, parses (JSON, nbformat, ONNX header, Markdown table rows), and the expected fields; run it and
  log the output in EXECUTION_LOG.md.
- Done when: it exits 0 and prints one line per artifact; any failure is fixed in the producing step's files (never in a
  frozen file) and logged as a lesson.

### AM-06 Pin and command verification (1.3.6)
- Actions: `research/spikes/pin-check/run.sh` looks up every pin of plan/ENVIRONMENT.md, `ci.yml` and the notebook install
  cells in its registry (PyPI JSON API, `download.pytorch.org` indexes, GitHub tags and releases, Hugging Face revision) and
  records each result and, for git tags, the commit; `research/spikes/notebook-commands/run.sh` executes the notebook
  commands that run without a GPU (uv venv with `--python-preference only-managed`, `uv pip install --python` with a
  separate index per package set, the RVC requirement filter, `python -m zipfile -e`, the uninstall replacement of AM-04);
  GPU-only commands get a pinned-version documentation locator in `research/SOURCES.md` and their decision rule (the cell
  stops and the owner reports `failed:`; G-004).
- Done when: every pin line says `exists`; every runnable command exited 0 in the spike output; every GPU-only command has a
  locator; a missing pin → replaced, logged in DEVIATIONS.md and re-issued at G-004 (AM-09).

### AM-07 Deviation completeness (3.7.1 1a, run once now)
- Actions: compare the impl branch with the generation branch (`git diff --stat`) and with plan/ENVIRONMENT.md: every
  changed manifest, workflow, pin, added file outside the planned Outputs, timeout and config file must have a
  DEVIATIONS.md row; add any missing row with the reason, and record a `kind:process` lesson per missing row.
- Done when: a table in `reviews/DEVIATION_AUDIT.md` lists each difference with its DEVIATIONS.md row.

### AM-08 Assumption & Premise Audit (4.7, retroactive)
- Tier: Opus (fresh context: an agent that did not author the plan).
- Actions: give every `A-###`, the premises of the decisions the remaining steps depend on (D-008, D-010, D-012, D-013,
  D-016, D-017, D-019, D-025, D-026, D-035, D-036), the three `single-source` claims (C-010, C-019, C-064) and every premise a
  frozen test relies on exactly one verdict (`confirmed`, `falsified`, `unverifiable`) with the evidence checked; facts
  established during implementation count as evidence and are cited by EXECUTION_LOG/DEVIATIONS row or knowledge item.
  Falsified → lesson (`kind:wrong-assumption`) + knowledge item (superseding any wrong one) + trace through
  plan/TRACEABILITY.md + an amendment entry (`D-###`) for every load-bearing consequence; unverifiable → `R-###` with a
  mitigation.
- Done when: `premortem/ASSUMPTION_AUDIT.md` gives every in-scope item a verdict and links each falsified item to its
  `L-`/`K-`/`D-` IDs; `python3.12 tools/check_schema.py` passes.

### AM-09 Re-pin gate G-004
- Actions: if any action changed a notebook or anything the notebook checks out, archive the open `GATE-G-004.md` as
  `GATE-G-004.run1.1.md` (`git mv`; it has no response, so it counts toward no limit) and re-issue it with
  `EXPECTED_COMMIT` = the impl head after the last amendment save, the same RUN and values otherwise.
- Done when: `GATE-G-004.md` names the new commit, its Colab link opens that commit's notebook (HTTP 200 for the raw file),
  and the archived file exists.

### AM-10 Records
- Actions: EXECUTION_LOG.md row per AM step; DEVIATIONS.md row "plan amended to v3.6 (D-041)"; checkpoint with
  `amendment: 01` complete; the Phase 5 status line on plan/PLAN.md gains the assumption-audit verdict counts.
- Done when: `turn_end_check.sh` passes; `git ls-remote` equals HEAD for both branches.

## Cold read and pre-mortem of this amendment (2E.4)
The amendment changes process and records, not behaviour; no frozen test changes. Its cold read (plan/… pass 15) and its
pre-mortem round (round 7) are restricted to the changed items and run together with Amendment 02, whose new steps they also
cover (premortem/coldread-pass-15.md, premortem/round-7.md).
