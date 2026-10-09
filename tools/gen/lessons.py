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
OUT.mkdir(exist_ok=True)
for x in L:
    p = OUT / f"{x['id']}.md"
    if not p.exists():
        p.write_text(render(x), encoding="utf-8")
print(len(L), "lessons")
