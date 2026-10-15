"""Writes the planning run's lessons (Rule 11, Appendix A). Re-runnable: existing files are left untouched."""
import pathlib
RUN = "gen-20261004T095012Z-singing-voice-vst-pitch-lyrics"
OUT = pathlib.Path(__file__).resolve().parents[2] / "lessons"
L = []
def lesson(ts, slug, title, sev, tags, trigger, wrong, corr, rule, detect, evidence, recurrence=None, occ=1, phase="phase:planning"):
    L.append(dict(id=f"L-{ts}-{slug}", title=title, severity=sev, tags=tags + [phase], trigger=trigger, wrong=wrong, corr=corr,
                  rule=rule, detect=detect, evidence=evidence, recurrence=recurrence, occ=occ, ts=ts))

lesson("20261010T000100Z", "unpushed-generation-branch-lost-in-sandbox-reset",
       "The whole generation branch existed only in the sandbox and was lost when the sandbox was reset between turns", "Medium",
       ["applies:all", "tech:git", "kind:environment"],
       "A planning run spans more than one turn; the target repository is pushable; work is committed locally but `git log origin/<branch>..HEAD` is non-empty when a turn ends.",
       "Research, spikes, frozen tests, CI and 28 claims were committed only locally; the turn ended asking the human to say 'continue', and the next turn found /home/claude empty.",
       "Rebuilt the branch from the conversation record, re-opened every source in the new run, and pushed after the first commit.",
       "Push the generation branch after every commit that ends a sub-phase, and never end a turn while `git log --oneline origin/<branch>..HEAD` prints anything.",
       "`git -C <repo> log --oneline origin/$(git branch --show-current)..HEAD | wc -l` prints 0 at the end of every turn.",
       "Turn of 2026-10-04 ended with an unpushed branch; on 2026-10-10 `ls /home/claude/sing-vst` failed.",
       recurrence="L-20261004T102007Z-sandbox-reset-lost-working-tree")
lesson("20261010T000101Z", "pasted-token-written-to-disk-before-add-repo",
       "A token pasted in chat was written to a file and a git credential helper instead of attaching the repository with add_repo", "Medium",
       ["tech:github", "tech:git", "kind:security"],
       "The human pastes a GitHub token in chat; an add_repo tool exists or may exist in the session.",
       "The token was stored in ~/.tok and wired into a global credential.helper; add_repo was never tried. In the next session the proxy rejected the token for unattached repositories anyway.",
       "Deleted the file, attached sing-vst, knowledge and lessons with add_repo (access push), and pushed through the session proxy. Advised the human to revoke the token.",
       "Call add_repo with access push for every repository the task names before reading or using any pasted token, and never write a pasted token to disk.",
       "`grep -rIl 'github_pat_\\|ghp_' ~ 2>/dev/null` and `git config --global --get-regexp credential` print nothing.",
       "Bash history of 2026-10-04 (`printf ... > .tok`); add_repo results of 2026-10-10.",
       recurrence="L-20261009T160400Z-pasted-token-rejected-401-add-repo-not-tried-first")
lesson("20261010T000102Z", "store-probe-used-only-the-default-name",
       "The knowledge-store probe checked only `agent-knowledge`, so R0 loaded nothing although qualitycoding/Lessons and qualitycoding/knowledge exist", "Medium",
       ["applies:all", "tech:github", "kind:process"],
       "Phase 0.1/0.3.7 with no store named in the request; the owner has other runs on record.",
       "Only qualitycoding/agent-knowledge was probed; it returned Not Found and research started with no prior lessons.",
       "Attached and cloned qualitycoding/Lessons and qualitycoding/knowledge and redid R0 (179 lessons, 139 items matched).",
       "Before research, probe the owner's Lessons, lessons, knowledge and agent-knowledge repositories and any store named in memory, and record every probe result in state.json.",
       "`.checkpoints/state.json` knowledge_store lists each probed location with its result.",
       "state of 2026-10-04: 'agent-knowledge doesn't exist yet, so no past lessons were loaded'.",
       recurrence="L-20261009T160500Z-lessons-addendum-adopted-after-implementation-again")
lesson("20261010T000103Z", "brace-expansion-in-dash-again",
       "cp and mkdir with brace expansion ran in dash and created a literal '{ort,juce-lyrics,cmudict}' directory", "Low",
       ["tech:bash", "kind:tooling"],
       "Any command in the sandbox Bash tool containing {a,b}, arrays, PIPESTATUS or `time`.",
       "`mkdir -p research/spikes/{ort,juce-lyrics,cmudict}` and `cp dir/{a,b}` were run in /bin/sh.",
       "Removed the literal directory and re-ran the commands inside `bash -c`.",
       "Prefix every command that uses brace expansion with `bash -c` and list the created tree afterwards.",
       "`find . -name '*{*'` prints nothing.",
       "research/spikes literal directory on 2026-10-04.",
       recurrence="L-20261009T123009Z-dash-brace-expansion-created-literal-directory")
lesson("20261010T000104Z", "background-cmake-build-with-ampersand-died",
       "A JUCE configure and build started with `( ... ) &` produced no log and no build tree", "Low",
       ["tech:cmake", "tech:juce", "kind:environment"],
       "A build expected to take longer than one tool call is started in the background.",
       "The subshell started with `&` died when the tool call ended; the empty log was mistaken for a slow configure.",
       "Ran configure and build in the foreground; this session uses `setsid nohup ... < /dev/null &` with a polled log.",
       "Start every build that may exceed 250 s with `setsid nohup <cmd> > <log> 2>&1 < /dev/null &` and poll the log; never with a bare `&`.",
       "`ps -eo pid,sid,cmd | grep cmake` shows the build in its own session after the starting call returns.",
       "red-cfg.log was 0 bytes on 2026-10-04.",
       recurrence="L-20261009T120013Z-background-builds-killed-when-shell-call-ended")
lesson("20261010T000105Z", "juce-cmake-needs-c-language-enabled",
       "Configuring a project that adds JUCE failed because `project()` enabled only CXX", "Low",
       ["tech:juce", "tech:cmake", "kind:wrong-assumption"],
       "A new CMake project calls add_subdirectory or FetchContent on JUCE 9.0.3 with `project(... LANGUAGES CXX)`.",
       "Configure stopped at JUCE/CMakeLists.txt:40: 'A C compiler is required to build targets that depend on JUCE'.",
       "Changed the project to `LANGUAGES C CXX`.",
       "Declare `LANGUAGES C CXX` in any CMake project that consumes JUCE.",
       "`grep -n 'LANGUAGES C CXX' CMakeLists.txt` matches.",
       "red-cfg.log of 2026-10-04; K-20261010T001405Z-juce-cmake-requires-c.")
lesson("20261010T000106Z", "onnx-reducemean-axes-is-an-attribute-in-opset-17",
       "An ONNX fixture passed ReduceMean axes as an input, which opset 17 rejects", "Low",
       ["tech:onnx", "kind:wrong-assumption"],
       "Hand-built ONNX graphs with onnx.helper at opset <= 17 using Reduce* operators.",
       "`make_node('ReduceMean', ['fr', 'ax2'], ...)` failed the checker: input size 2 not in range [1, 1].",
       "Passed `axes=[2]` as an attribute.",
       "Check each operator's signature for the target opset (onnx.defs.get_schema(op, opset)) before building a fixture graph, and run onnx.checker on every fixture.",
       "tests/fixtures/make_onnx_fixtures.py calls onnx.checker.check_model for every model it writes.",
       "make_onnx_fixtures.py traceback of 2026-10-04.")
lesson("20261010T000107Z", "most-vexing-parse-in-a-spike",
       "A spike declared `juce::FileInputStream in (juce::File (argv[1]))`, which C++ parses as a function declaration", "Low",
       ["tech:cpp", "kind:tooling"],
       "Writing a one-off C++ spike that constructs an object from a temporary.",
       "The build failed: cannot convert 'juce::FileInputStream(juce::File*)' to 'juce::InputStream&'.",
       "Used brace initialisation.",
       "Use brace initialisation for every object constructed from a temporary in C++ code.",
       "The spike compiles with -Wvexing-parse enabled and no warnings.",
       "research/spikes/juce-lyrics/README.md.")
lesson("20261010T000108Z", "scripted-replace-inserted-comment-into-an-expression",
       "A scripted str.replace appended a '#' comment inside a list literal and broke the fixture generator's syntax", "Low",
       ["tech:python", "kind:tooling"],
       "Editing Python source with a script that splices text into the middle of a line.",
       "The replacement added '  # opset 17: axes is an attribute' before a closing comma, so the rest of the line became a comment.",
       "Removed the comment and re-ran the generator.",
       "After any scripted edit of source code, run the file (or py_compile it) in the same command, and never splice comments into the middle of a line.",
       "`python -m py_compile <file>` after each scripted edit.",
       "SyntaxError in make_onnx_fixtures.py on 2026-10-04.",
       recurrence="L-20261004T150700Z-scripted-str-replace-silently-no-opped")
lesson("20261010T000109Z", "tests-cited-claim-ids-before-the-register-was-numbered",
       "Frozen-test docstrings cited claim IDs (C-017, C-019, C-027, C-028) that pointed at the wrong claims once the register was written", "Low",
       ["tech:cpp", "tech:pytest", "kind:process"],
       "Tests are written before research/claims.json is final and cite C-### IDs from memory.",
       "Four test citations named claims about other subjects.",
       "Renumbered the citations after generating the register.",
       "Generate claims.json before writing test docstrings, and run a check that every C-### a test cites exists and shares a subject tag with the test's topic.",
       "tools/check_refs.py reports 0 dangling or mismatched IDs.",
       "sed fixes to test_synthesis.cpp, test_g2p.cpp, test_metrics.py, test_notebooks.py on 2026-10-04.")
lesson("20261010T000110Z", "fixture-entry-count-typed-instead-of-computed",
       "T-007 expected 23 dictionary words for a fixture that has 22, because a variant line was counted as a word", "Low",
       ["tech:cpp", "kind:verification-gap"],
       "A test asserts a count derived from a fixture file.",
       "The expected size was counted by eye from `wc -l` (24 lines, 2 variants) and written as 23.",
       "Computed it from the file with the same rule the parser uses (22).",
       "Compute every expected count in a test from the fixture with a committed script, and paste the script's output.",
       "research/spikes/fixture-counts.txt lists the computation for every count asserted in tests.",
       "test_g2p.cpp edit on 2026-10-04.",
       recurrence="L-20261009T192611Z-tracked-file-count-typed-in-a-prompt-was-wrong")
lesson("20261010T000111Z", "env-dependent-tests-failed-red-with-keyerror",
       "Two environment-dependent tests failed red with KeyError instead of a clean assertion", "Low",
       ["tech:pytest", "kind:verification-gap"],
       "Tests read os.environ for paths that only exist in CI or after training.",
       "os.environ['SINGVST_RVC_ROOT'] raised KeyError, which red verification treats as broken test code.",
       "Added explicit `assert os.environ.get(k), ...` before use.",
       "Read every environment variable in a test through an assertion that names the variable and the plan step that sets it.",
       "Red run shows only NotImplementedError or AssertionError causes.",
       "pytest output of 2026-10-04.")
lesson("20261010T000112Z", "json-backslash-test-needed-two-attempts",
       "A C++ test meant to send a JSON path containing one backslash sent an invalid JSON escape, then needed a second fix", "Low",
       ["tech:cpp", "kind:verification-gap"],
       "A test builds JSON text inside a C++ string literal and needs a literal backslash in the JSON value.",
       "The literal had two backslashes (one in the JSON), which is an invalid escape, so the test would pass for the wrong reason.",
       "Used four backslashes so the JSON contains an escaped backslash; added a parse-check of the fixture text.",
       "Write JSON test inputs as raw string literals R\"(...)\" and assert in the test that the input is valid JSON before asserting the rejection reason.",
       "grep shows no JSON with backslashes outside raw string literals in tests/cpp.",
       "test_voice.cpp edits on 2026-10-04.")
lesson("20261010T000113Z", "intake-assumed-a-local-gpu-for-training",
       "Intake proposed training on the owner's local NVIDIA GPU; the owner needs a free hosted GPU", "Medium",
       ["domain:singing-voice-synthesis", "domain:audio", "kind:wrong-assumption"],
       "A plan includes model training and the request does not say where compute comes from.",
       "Intake item 9 defaulted to a local GPU and asked for its VRAM; the human corrected this to a free online GPU (Colab).",
       "Re-planned training as resumable notebook-driven stages for Colab free tier with a Kaggle fallback, under the hosted platforms' usage policies.",
       "At intake, ask where training compute runs (local GPU, free hosted notebook, paid cloud) and propose a free hosted default with its session limits, instead of assuming local hardware.",
       "plan/ASSUMPTIONS.md has an assumption naming the compute platform and its limits.",
       "Human message on 2026-10-04: 'we would have to use a free online gpu'.", phase="phase:intake")
lesson("20261010T000114Z", "quality-thresholds-frozen-before-measurement",
       "Similarity, WER, pitch and speed thresholds were proposed at intake and frozen as pass/fail numbers with no measurement behind them", "Medium",
       ["domain:singing-voice-synthesis", "domain:audio", "kind:verification-gap"],
       "A plan sets numeric quality targets for a model that has not been trained.",
       "eval/thresholds.json froze 0.75 / 0.15 / 25 cents / 25% / 1.0 as gates.",
       "Reworded them as unmeasured defaults; G-001 records the measured values and the owner confirms or amends the thresholds before any downstream step uses them.",
       "Mark every numeric quality target 'unmeasured default' until a spike or run has measured it, and route its confirmation through the result gate.",
       "eval/thresholds.json has \"status\": \"unmeasured-default\" until GATE-G-001 is signed.",
       "eval/thresholds.json of 2026-10-04.",
       recurrence="L-20261009T234100Z-intake-defaults-and-draft-numbers-stated-before-measurement")
lesson("20261010T000115Z", "corroborated-label-from-one-publisher",
       "Claims were labelled corroborated from two documents by the same publisher (GitHub API metadata and the same repository's file)", "Medium",
       ["applies:all", "kind:verification-gap"],
       "A claim's sources are an API view and a file of the same upstream project.",
       "C-001 and similar claims counted the GitHub API and the repository's LICENSE as independent.",
       "Re-checked each code-level claim with a committed spike that clones the pinned commit and asserts the fact, which makes it verified, and recorded the publisher count on every claim.",
       "Record independent_publishers on every claim, and label a claim corroborated only when that count is at least 2; facts in pinned source code are made verified by a spike instead.",
       "tools/check_claims.py fails if a corroborated claim has independent_publishers < 2.",
       "research/claims.json of 2026-10-04.",
       recurrence="L-20261009T123005Z-corroborated-label-without-independent-sources")

lesson("20261010T001500Z", "ci-tool-flags-and-versions-from-memory",
       "A recalled pluginval flag (--validate-in-process) and recalled action versions were written into the CI draft without reading the pinned tool source", "Medium",
       ["tech:github-actions", "tech:pluginval", "kind:wrong-assumption"],
       "A CI workflow or script names a third-party CLI flag, release asset name or action major version.",
       "The 2026-10-04 CI draft used `pluginval --validate-in-process` (no such option in 1.0.4) and actions/checkout@v4 etc. while v7/v8 were current.",
       "Read the pluginval 1.0.4 CLI source and the actions' tags in the upstream-facts spike (C-015b/c) and pinned what the source shows.",
       "Take every CLI flag, release asset name and action version for CI from the pinned tool's source or tag listing in a committed spike, never from memory.",
       "`research/spikes/upstream-facts/output.txt` has a PASS line for each CLI option and action version used in .github/workflows/*.yml.",
       "upstream-facts spike, checks C-015b and C-015c (first run failed, 2026-10-10).",
       recurrence="L-20261004T161503Z-audacity-commands-coded-from-memory")
lesson("20261010T094000Z", "continuation-left-work-uncommitted-and-checkpoint-stale",
       "A continuation attempt committed research round 2 but left the revised interfaces and the oracle untracked, never wrote a lesson it cited, and left state.json at 0.3.7", "Medium",
       ["applies:all", "tech:git", "kind:process"],
       "A long planning turn produces artefacts across several sub-phases and may end (or be cut off) before its last commit.",
       "On 2026-10-10 the next turn found core/ and research/spikes/oracle/ untracked, a README citing lesson L-20261010T001500Z that did not exist, and state.json still at subphase 0.3.7 although research round 2 had been committed.",
       "Verified the checkpoint hashes, wrote the missing lesson, reviewed and committed the untracked files with the next sub-phase, and moved state.json forward in that commit.",
       "Commit and push every artefact the moment a sub-phase produces it, write a lesson file before any text cites its ID, and advance state.json in the same commit as the work it records.",
       "`git status --short` is empty and `grep -rhoE 'L-2026[0-9T]+Z-[a-z0-9-]+' research plan | sort -u` names only files that exist, at the end of every turn.",
       "git status of 2026-10-10 09:30 (`?? core/`, `?? research/spikes/oracle/`); .checkpoints/state.json subphase 0.3.7.",
       recurrence="L-20261009T234122Z-checkpoint-state-stale-after-implementation-and-main-not-default")
lesson("20261014T195500Z", "session-cut-off-left-spike-and-tool-edit-uncommitted-again",
       "A continuation session wrote a spike, a dependency lock and a bootstrap-script fix after its last commit and ended without committing them", "High",
       ["applies:all", "tech:git", "kind:process"],
       "A planning session writes files after its last commit, and the session can end between tool calls (usage limit, cut-off, reset) before any turn-end check runs.",
       "At 15:38 the 2026-10-14 session committed round 4; by 15:43 it had written research/spikes/pyworld-direct/, python/requirements.in, python/requirements-lock.txt and a stricter clone check in tools/bootstrap_test_env.sh, then stopped. The 20:35 session found them untracked or modified, and the bootstrap edit failed the checkpoint hash check. This repeats L-20261010T094000Z, whose rule ('git status is empty at the end of every turn') cannot work when the turn never reaches its end.",
       "Re-ran the pyworld-direct spike to completion (identical output), verified its PYSEC-2026-3447 premise with a committed pip-audit spike, ran the bootstrap check on the pinned deps and on a wrong JUCE tag (exit 3), then committed all of it with claim C-046 through tools/save.sh.",
       "Commit and push in the same tool call that writes a file: every command that creates or edits a path in the repository ends with `bash tools/save.sh \"<msg>\" <those paths>`; run `bash tools/turn_end_check.sh` as the last call of every turn as a second line of defence.",
       "`git status --porcelain` is empty after every tool call that wrote into the repository (the call's own output shows `saved <sha> ... unpushed commits: 0`).",
       "state.json hash mismatch on tools/bootstrap_test_env.sh at 2026-10-14T19:40Z; `git status` showed ?? python/requirements*.txt, ?? research/spikes/pyworld-direct/.",
       recurrence="L-20261010T094000Z-continuation-left-work-uncommitted-and-checkpoint-stale")
lesson("20261014T195600Z", "claims-generator-hard-coded-knowledge-item-date",
       "The claims generator stamped every new knowledge item 2026-10-10T11:00:<index>Z regardless of when the claim was added", "Low",
       ["applies:all", "tech:python", "kind:verification-gap"],
       "A generator writes dated records (knowledge items, lessons) and is re-run in later sessions to add new entries.",
       "tools/gen/claims.py built the item timestamp from a fixed prefix plus the claim's list index and accepted but ignored a kstamp argument, so C-046 (found 2026-10-14) would have been recorded as discovered on 2026-10-10.",
       "Stored kstamp on each claim, used it for the item ID and recorded_at when given, and gave C-046 its real time (2026-10-14T19:50:00Z).",
       "Generators of dated records take the timestamp from the record's own field or the clock, never from a constant; a claim added after the first generation run carries kstamp.",
       "`grep -L 'recorded_at: 2026-10-10' knowledge/K-20261014*.md` lists every item stamped 20261014.",
       "tools/gen/claims.py lines 18-21 and 150 before and after this commit.")
lesson("20261014T203000Z", "oracle-had-three-rule-defects-and-no-checks-of-its-own",
       "The independent oracle written to validate frozen expectations encoded three defective rules and had no tests of its own", "High",
       ["applies:all", "tech:python", "domain:singing-voice-synthesis", "kind:verification-gap"],
       "A reference implementation ('oracle') is written to check expected values in tests that are about to be frozen, before any decision text exists and without its own invariant checks.",
       "research/spikes/oracle/oracle.py (2026-10-10) dropped the next syllable's onset after a vowel-less syllable ('hmm hello' lost 'hh'), let frame durations overshoot their own stated total (sum 55 for a total of 50), and let a zero-length note with an equal start delete the real note. Every expected value checked against it would have inherited these errors into the frozen suite.",
       "Fixed the three rules in the oracle and in plan/DECISIONS.md (D-006, D-007), added research/spikes/oracle/properties.py (randomised invariants: one note per distinct start, highest pitch kept, phones conserved in order with one SP per gap, exact frame totals, f0 frame count), and showed it fails on the unpatched oracle (4 invariant failures) and passes on the patched one (0 of 6000 cases).",
       "Before an oracle checks any frozen expectation, give it randomised invariant checks derived from the decisions, and show those checks fail on a deliberately broken copy.",
       "`python -I research/spikes/oracle/properties.py 3000` exits 0 and research/spikes/oracle/properties-output.txt shows 0 failures; the mutation run is recorded in research/rounds/round-5.md.",
       "research/spikes/oracle/properties-output.txt; mutation run against `git show 6fe0e5d:research/spikes/oracle/oracle.py` (4 failures).")
lesson("20261014T220000Z", "hand-derived-test-expectations-wrong-at-boundaries",
       "Three expected values written by hand into tests were wrong; the oracle cross-check caught all three before the freeze", "Medium",
       ["applies:all", "tech:cpp", "kind:verification-gap"],
       "Writing expected values for tests about rounding, indexing or set membership by mental arithmetic, before running them through an independent oracle.",
       "test_g2p.cpp asserted 'ao' was absent from the mini dictionary (it occurs in 'song'); test_playback.cpp expected sample 1 at exactly half a sample (binary rounding of 4 + x - 4 gives 0.4999...) and sample 47999 at ppq 5.99998 (that is sample 47999.52, which rounds out of range).",
       "Re-derived each expectation with research/spikes/oracle/check_expectations.py, changed the fixture duplicate line to a phone no other word uses (zh), and moved the rounding cases off exact .5 boundaries (0.6 / 0.4 sample) and onto the exact last-sample position.",
       "Compute every expected value with the oracle before writing it into a test, and keep inputs away from exact rounding boundaries unless the boundary is the subject (then build the input so the boundary is exact in binary).",
       "`python -I research/spikes/oracle/check_expectations.py` reports 0 mismatches and is run before every test-file commit.",
       "check_expectations output: 'MISMATCH T-007 hasPhone ao', 'MISMATCH T-032 ppq 4.000020833333333', 'MISMATCH T-032 ppq 5.99998'.", occ=2)

def render(x):
    rec = x["recurrence"] or "null"
    return f"""---
id: {x['id']}
title: {x['title']!r}
status: active
supersedes: []
recurrence_of: {rec}
occurrences: {x['occ']}
severity: {x['severity']}
tags: [{', '.join(x['tags'])}]
recorded_by: planner
run: {RUN}
recorded_at: {x['ts'][:4]}-{x['ts'][4:6]}-{x['ts'][6:8]}T{x['ts'][9:11]}:{x['ts'][11:13]}:{x['ts'][13:15]}Z
---
## Trigger
{x['trigger']}
## What went wrong
{x['wrong']}
## Correction
{x['corr']}
## Prevention rule
{x['rule']}
## Detection check
{x['detect']}
## Evidence
{x['evidence']}
"""
lesson("20261015T071500Z", "checkpoint-not-rewritten-after-phase-2b-commits",
       "Seventeen Phase 2B commits on 2026-10-14 left .checkpoints/state.json at 19:40Z, so the next session's resume check found 11 hash mismatches and 78 untracked artefacts", "Medium",
       ["applies:all", "tech:git", "kind:process"],
       "A planning session commits many artefacts with tools/save.sh after the last explicit tools/checkpoint.py call; the next session applies the Resume Rule (1.2).",
       "save.sh committed and pushed each file but never rewrote state.json; the checkpoint still said phase 1.3 with 137 artefacts while the branch held 215 tracked files and the C++ test suite.",
       "Verified the working tree was clean and the remote tip matched HEAD (02fa6ea), so every mismatch came from committed work; treated Phase 2B as the in-progress sub-phase and changed tools/save.sh to run tools/checkpoint.py and stage state.json in every commit.",
       "Never write the checkpoint as a separate manual step: tools/save.sh regenerates .checkpoints/state.json and commits it with every save.",
       "`git show --stat HEAD` lists .checkpoints/state.json for every commit made through tools/save.sh.",
       "2026-10-15 resume: state.json updated_at 2026-10-14T19:40:53Z, HEAD 02fa6ea at 2026-10-14T21:30Z; 11 mismatches, 78 artefacts missing from the map.",
       recurrence="L-20261010T094000Z-continuation-left-work-uncommitted-and-checkpoint-stale")
lesson("20261015T073000Z", "default-python3-changed-between-sessions",
       "/usr/bin/python3 became 3.13 between sessions, so a clean venv built with `python3 -m venv` could not install the 3.12 lock", "Medium",
       ["applies:all", "tech:python", "kind:environment"],
       "A run resumes after days in a sandbox it does not control; a lock pins packages for one Python minor version (here 3.12).",
       "`python3 -m venv` picked Python 3.13.16; pip found no cp313 wheel for scipy 1.13.1 and tried to build it from source (meson: no Fortran compiler), so the clean-room install failed.",
       "Rebuilt the venv with /usr/bin/python3.12 explicitly; the lock then reproduced exactly and pyworld's extension loaded.",
       "Name the interpreter by its full minor version (python3.12) in every venv, script and CI step; never rely on `python3`.",
       "`grep -rn 'python3 -m venv' tools research/spikes .github` prints nothing; plan/ENVIRONMENT.md names /usr/bin/python3.12.",
       "venv-lock.install.log: 'ERROR: Unknown compiler(s): [[gfortran] ...' under /usr/lib/python3.13.")
lesson("20261015T073100Z", "stub-docstring-paraphrased-the-claim-not-the-spike",
       "load_pyworld's frozen docstring said importlib.import_module('pyworld.pyworld'), which still runs the package __init__ that C-046 says fails", "Medium",
       ["tech:python", "domain:audio", "kind:wrong-assumption"],
       "An interface docstring is written from a claim's one-line summary while the spike that verified the claim contains the exact working code.",
       "The stub promised a loading method the spike had not used; the clean-room venv showed it raising ModuleNotFoundError: pkg_resources.",
       "Rewrote the docstring from research/spikes/pyworld-direct/run.sh (ExtensionFileLoader on the file listed in the distribution metadata) and ran the sketch implementation of it (T-P10 passes).",
       "When a frozen docstring describes a mechanism a spike verified, copy the mechanism from the spike's code, then run it once in the pinned environment before committing.",
       "research/spikes/sketch-py/output.txt shows T-P10 passing with the documented loader.",
       "venv-lock.log 2026-10-15: importlib.import_module('pyworld.pyworld') -> ModuleNotFoundError: No module named 'pkg_resources'.")
lesson("20261015T073200Z", "secret-scan-test-contained-a-literal-it-scans-for",
       "The secret-scan test planted a private-key marker as a literal, so its own whole-repository scan would have reported the test file", "Low",
       ["tech:python", "kind:verification-gap"],
       "A test plants strings that a scanner must detect and also asserts that the scanned repository (which contains the test) is clean.",
       "test_security.py contained the RSA private-key header (BEGIN ... PRIVATE KEY between five dashes) as a literal while asserting scan_secrets(root) == [].",
       "Assembled the marker from two parts at run time ('...PRIV' + 'ATE KEY-----'), like the token strings in the same test.",
       "Build every planted secret from concatenated parts at run time; grep the repository with the scanner's own patterns before committing.",
       "`python tools/check_schema.py` and the scan_secrets patterns report nothing anywhere in the repository (T-P15).",
       "Commit f6ee132.")
lesson("20261015T073300Z", "script-resolved-its-own-directory-after-cd",
       "The sketch harness looked up a helper with $(dirname \"$0\") after changing directory, so the helper silently never ran", "Low",
       ["tech:bash", "kind:tooling"],
       "A shell script invoked with a relative path changes directory and later refers to files next to itself.",
       "sketch_docs.py was never executed; the notebook tests still failed with 'missing notebooks' and the output looked like a test defect.",
       "Resolve the script's own directory once at the top (D=$(cd \"$(dirname \"$0\")\" && pwd)) and report a failed helper explicitly.",
       "Resolve the script directory to an absolute path before any cd, and make helper failures print a FAILED line.",
       "`grep -n 'dirname \"\\$0\"' research/spikes/*/run.sh` shows uses only in the first lines.",
       "research/spikes/sketch-py/run.sh before and after commit 5365bb3.")
lesson("20261015T073400Z", "main-guard-ran-before-the-test-overlay",
       "Appending an overlay to a module whose __main__ guard calls main() left `python -m` running the stub", "Low",
       ["tech:python", "kind:tooling"],
       "A harness patches a module by appending code, and the module is also run as a script (`python -m`).",
       "T-P25 failed in the sketch run with NotImplementedError: main, which looked like a test defect.",
       "Moved the __main__ guard after the overlay in the harness copy; T-P25 then passed.",
       "When overlaying a module by appending code, move its `if __name__ == \"__main__\"` block to the end first.",
       "research/spikes/sketch-py/output.txt: test_cli.py passes.",
       "Sketch run 2026-10-15, first attempt: 'raise NotImplementedError(\"main\")' from python -m singvst_train.cli --help.")
lesson("20261015T073500Z", "syllable-split-assumed-instead-of-read-from-the-dictionary",
       "An evaluation phrase split 'every' into two syllables, but CMUdict gives it three vowels (eh v er iy)", "Low",
       ["domain:singing-voice-synthesis", "tech:g2p", "kind:wrong-assumption"],
       "Writing lyric fixtures with hyphenated syllables for a pipeline that syllabifies by dictionary vowels (D-005).",
       "The phrase 'ev- ery morn- ing ...' would have produced an alignment warning in every evaluation render.",
       "The generator's dictionary check stopped it; split as 'ev- er- y' and added a note.",
       "Generate lyric fixtures with a check that each word's hyphen count + 1 equals its CMUdict vowel count.",
       "`python -I tools/gen/phrases.py` exits 0.",
       "AssertionError: every: 2 syllables but 3 vowels ['eh', 'v', 'er', 'iy'].")
OUT.mkdir(exist_ok=True)
for x in L:
    p = OUT / f"{x['id']}.md"
    if not p.exists():
        p.write_text(render(x), encoding="utf-8")
print(len(L), "lessons")
