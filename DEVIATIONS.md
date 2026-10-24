# DEVIATIONS

| UTC time | Step | Plan says | Done instead | Why (rule applied) |
|---|---|---|---|---|
| 2026-10-24T12:32:11Z | S-000 | action 3: apt-get install the CI package list, python3.12-venv, locales, g++-11; generate de_DE locale | not done (no root: id -u=1000, sudo needs a password) | No-root path of action 3: plugin build, plugin tests, pluginval and T-034 are checked in CI only (D-036); build-full tree skipped |
| 2026-10-24T12:32:11Z | S-000 | action 1: attach repos through the session repository tool and clone with the command it returns | cloned with git clone --depth 1 to ../store-lessons and ../store-knowledge (repo names are lowercase: qualitycoding/lessons, qualitycoding/knowledge) | Same clone commands as returned by the tool; directory names per plan |
| 2026-10-24T12:32:11Z | S-000 | action 4: list store files added after R0 commits | none: store HEADs equal the R0 commits (lessons ac028c7, knowledge 09f3458) | No active items added since R0 |
| 2026-10-24T12:32:47Z | S-000 | action 5: hosts table expects pytorch-index, huggingface-rvc-assets, colab, kaggle, actions-results unreachable | now reachable (200/302/404) from this local machine | Changed rows recorded; alternative channels (CI, notebooks) remain the plan's evidence path (PK-13); Actions results still read via REST API (D-018) |
| 2026-10-24T12:32:47Z | S-000 | action 6: configure and build core, full, asan, tsan | full tree skipped (no-root path of action 3, see row above) | D-036 |
| 2026-10-24T12:39:43Z | S-000 | action 7 / On failure: T-P21 pip-audit finding GHSA-xmj3-9gf7-h52w in setuptools 84.0.0 | applied DR-07 once: setuptools 84.1.0 in python/requirements.in, requirements-lock.txt, pyproject.toml; plan/ENVIRONMENT.md Toolkit lock row updated (still 32 lines); T-P21 re-run passes | DR-07 (first and only use) |
| 2026-10-24T12:39:48Z | S-000 | action 2: keep environment identity | environment had no user.name/user.email; set repo-local sing-vst implementer / noreply@anthropic.com | plan's stated fallback |
| 2026-10-24T12:55:38Z | S-002 | Tier: Opus | run by claude-sonnet-5-5 (no Opus subagent used) | HANDOFF §Tiers: neither possible/chosen, substitution recorded |
| 2026-10-24T12:56:21Z | S-003 | Tier: Opus | run by claude-sonnet-5-5 | HANDOFF §Tiers substitution |
