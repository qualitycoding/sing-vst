# Red verification (Phase 2B.5, PK-25) — 2026-10-15

`bash run.sh <repo> <core build> <full build> <venv>` → `output.txt` (builds configured with the lines printed by
`tools/bootstrap_test_env.sh`; venv = clean Python 3.12 install of `python/requirements-lock.txt`).

- **C++ core** `singvst_tests`: 56/56 test cases fail. Every failure is `NotImplemented` from a stub, except `softClip`
  (a `noexcept` stub that cannot throw and returns 1e9, so its value assertions fail). Assertions that pass inside failing
  cases (e.g. `isfinite` on that 1e9) do not make a case pass.
- **C++ plugin** `singvst_plugin_tests` (T-053…T-058, under xvfb): 6/6 fail on `SingVstProcessor` stubs.
- **CLI stub**: exit 99, "not implemented".
- **Python** (`-m "not torch and not voice"`): 30 fail, 4 pass. The 4 passes are exempt repository/environment checks
  (D-023): T-061, T-062, T-P21 (lock reproduced exactly and pip-audit clean, run live) and T-P27 (interface record).
  Failures: `NotImplementedError` from stubs, or an assertion that names the missing artifact and the plan step that writes
  it (notebooks, README section, freeze manifest, plan documents), or the stub CLI's message.
- Note for implementers: Python's `NotImplementedError` subclasses `RuntimeError`, so a bare `pytest.raises(RuntimeError)`
  would pass against a stub; every such assertion in the frozen suite carries `match=` (T-P06), which is why T-P06 fails on
  the pattern rather than passing.
- Not run here: T-P19 (`torch`, CI job python-torch), T-P20 (`voice`, owner's hosted-GPU run), T-059 (pluginval, CI).
