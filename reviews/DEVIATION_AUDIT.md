# Deviation completeness audit (protocol v3.6 3.7.1 1a; Amendment 01 AM-07)

Run 2026-10-30T23:39:59Z: `git diff --name-status origin/gen-20261004T095012Z-singing-voice-vst-pitch-lyrics...HEAD` on the impl branch (87 files outside
`lessons/`, `knowledge/`, `.checkpoints/`), each matched against the `Outputs` of the step that produced it (plan/PLAN.md,
plan/AMENDMENT-01.md) and against DEVIATIONS.md. Pins: `python/requirements*.txt` and `python/pyproject.toml` differ from
plan/ENVIRONMENT.md only in setuptools 84.0.0 → 84.1.0 (DR-07, logged); `.github/workflows/ci.yml` is unchanged; no timeout in
CI or a manifest changed.

| Difference | Planned by | DEVIATIONS.md row |
|---|---|---|
| `.gitattributes` (new config file) | — | S-004 row (fixtures -text for T-031 on Windows) |
| `python/requirements.in`, `requirements-lock.txt`, `pyproject.toml` (setuptools 84.1.0) | — | S-000 DR-07 row |
| `core/src/ort_threads.hpp`, `SINGVST_ORT_THREADS` (new config variable) | — | S-010 threads row |
| `core/src/ort_util.cpp`, `ort_util.hpp`, `sha256.hpp` (private helpers) | D-033 ("private helpers and private headers live in core/src/") | not a deviation |
| `tools/make_notebooks.py`, `tools/notebook_cells/*.py` (21 files) | — | S-016 generator row |
| `cli/git_commit.cmake` (new build script read by `cli/CMakeLists.txt`) | S-010 asks for a custom command in `cli/CMakeLists.txt` | **missing → added now** (lesson L-20261030T233959Z) |
| plugin resample-worker fix, notebook uninstall, nvidia-smi/torch queries | Amendment 01 AM-04, AM-06 | AM-04, AM-06 rows |
| local `../venv-torch`, `~/sysroot`, `../hfv`-style venvs (out of tree) | — | S-013 and S-000/S-011 rows |
| every other file in the diff | the producing step's `Outputs` (S-000…S-016) or Amendment 01 | n/a |

Result: one missing entry, now recorded; no unexplained pin, workflow, timeout or config difference remains.
