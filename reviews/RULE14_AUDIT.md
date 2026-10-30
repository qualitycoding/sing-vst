# Rule 14 audit (Amendment 01, AM-04)

Run 2026-10-30T23:32:52Z on the impl branch after the Amendment 01 merge. Rule 14 (protocol v3.6): a check that cannot fail is not a check.

## 1. Failure-swallowing idioms
Scan: `grep -rnE '\|\| *(true|:)\b|continue-on-error|set \+e'` over `.github tools python cmake CMakeLists.txt cli core plugin notebooks`;
C++ `catch (...)` and empty catch blocks in `core/src cli plugin`; Python `except`, `except Exception`, `except BaseException` in
`python/singvst_train tools`; CMake `ERROR_QUIET`/`OUTPUT_QUIET`.

| Location | Idiom | Load-bearing? | Outcome |
|---|---|---|---|
| notebook cell (4), `tools/notebook_cells/c04_setup.py` | `uv pip uninstall … onnxruntime-gpu onnxruntime \|\| true` | yes: a failed uninstall left two providers of `onnxruntime` | **fixed**: lists the venv with `uv pip list --format json` and uninstalls only the installed ones; any failure stops the cell (spike AM-06) |
| `plugin/PluginProcessor.cpp` resample worker | `catch (...) { continue; }` | yes: a failed playback copy was never published and the status stayed "rendering" | **fixed**: the failure is posted to the message thread; `renderStatus()` becomes Failed and `lastError()` names it; plugin tests 67/67 |
| `core/src/render.cpp` | `catch (const Cancelled&) {}` | no: D-013 discards a cancelled job by design and the newer request runs | kept (contract) |
| `core/src/render.cpp` | `catch (...) { failed = true; … }` | records Failed + lastError | kept |
| `core/src/take_cache.cpp` | `catch (...) { return false; }` / `nullopt` | no: the frozen interface (take_cache.hpp) says the functions never throw and report failure by value; `cachedRender` ignores a failed store by D-038 | kept (frozen contract) |
| `cli/main.cpp` number parsing | `catch (...) {}` then `throw UsageError` | no: the failure is re-raised as exit 2 | kept |
| `plugin/PluginProcessor.cpp` state restore | `catch (const ParseError&) {}` around the cache lookup | no: unparsable lyrics only skip the lookup; the restore warning is still set and the render reports `Lyrics: …` | kept |
| `python/singvst_train/pipeline.py` atomic write | `except BaseException:` | re-raises after cleanup | kept |
| `python/singvst_train/cli.py` | `except Exception` | prints `singvst-train: <cmd>: <msg>` and exits 3 | kept |
| notebook cell (3) `guarded`, heartbeat | `except Exception` | records `STOP_REASON` / `HEARTBEAT_ERROR`; every later check fails on it (R-069, R-051) | kept (by design, printed) |
| notebook cell (4f) | `except BaseException:` | closes the session entry and re-raises | kept |
| `tools/notebook_dryrun.py` | `except Exception` | records the scenario as a failure; exit 1 | kept |
| `cli/git_commit.cmake` | `ERROR_QUIET` on `git rev-parse` | no: a build outside a git checkout stamps `unknown`, visibly in every provenance file | kept |

## 2. Numeric thresholds gate the build
Every frozen test runs in a CI step without `continue-on-error`; a failing test fails its job. Tests with numeric thresholds
(found by scanning the frozen suites for tolerances and bounds):

| Test | File | Gating CI step (a failure fails the job; no continue-on-error) |
|---|---|---|
| T-043 | test_engine.cpp | cpp job, step "C++ tests (T-001..T-058, T-063..T-071)" (ubuntu-24.04 and windows-2022) and sanitizers job |
| T-044 | test_engine.cpp | cpp job, step "C++ tests (T-001..T-058, T-063..T-071)" (ubuntu-24.04 and windows-2022) and sanitizers job |
| T-046 | test_engine.cpp | cpp job, step "C++ tests (T-001..T-058, T-063..T-071)" (ubuntu-24.04 and windows-2022) and sanitizers job |
| T-070 | test_limits.cpp | cpp job, step "C++ tests (T-001..T-058, T-063..T-071)" (ubuntu-24.04 and windows-2022) and sanitizers job |
| T-002 | test_lyrics.cpp | cpp job, step "C++ tests (T-001..T-058, T-063..T-071)" (ubuntu-24.04 and windows-2022) and sanitizers job |
| T-065 | test_midifile.cpp | cpp job, step "C++ tests (T-001..T-058, T-063..T-071)" (ubuntu-24.04 and windows-2022) and sanitizers job |
| T-066 | test_midifile.cpp | cpp job, step "C++ tests (T-001..T-058, T-063..T-071)" (ubuntu-24.04 and windows-2022) and sanitizers job |
| T-033 | test_playback.cpp | cpp job, step "C++ tests (T-001..T-058, T-063..T-071)" (ubuntu-24.04 and windows-2022) and sanitizers job |
| T-038 | test_playback.cpp | cpp job, step "C++ tests (T-001..T-058, T-063..T-071)" (ubuntu-24.04 and windows-2022) and sanitizers job |
| T-053 | test_plugin.cpp | cpp job, step "C++ tests" (plugin tests under xvfb on Linux) |
| T-054 | test_plugin.cpp | cpp job, step "C++ tests" (plugin tests under xvfb on Linux) |
| T-055 | test_plugin.cpp | cpp job, step "C++ tests" (plugin tests under xvfb on Linux) |
| T-057 | test_plugin.cpp | cpp job, step "C++ tests" (plugin tests under xvfb on Linux) |
| T-058 | test_plugin.cpp | cpp job, step "C++ tests" (plugin tests under xvfb on Linux) |
| T-048 | test_render.cpp | cpp job, step "C++ tests (T-001..T-058, T-063..T-071)" (ubuntu-24.04 and windows-2022) and sanitizers job |
| T-051 | test_render.cpp | cpp job, step "C++ tests (T-001..T-058, T-063..T-071)" (ubuntu-24.04 and windows-2022) and sanitizers job |
| T-071 | test_resample_take.cpp | cpp job, step "C++ tests (T-001..T-058, T-063..T-071)" (ubuntu-24.04 and windows-2022) and sanitizers job |
| T-039 | test_runtime.cpp | cpp job, step "C++ tests (T-001..T-058, T-063..T-071)" (ubuntu-24.04 and windows-2022) and sanitizers job |
| T-040 | test_runtime.cpp | cpp job, step "C++ tests (T-001..T-058, T-063..T-071)" (ubuntu-24.04 and windows-2022) and sanitizers job |
| T-019 | test_synthesis.cpp | cpp job, step "C++ tests (T-001..T-058, T-063..T-071)" (ubuntu-24.04 and windows-2022) and sanitizers job |
| T-022 | test_synthesis.cpp | cpp job, step "C++ tests (T-001..T-058, T-063..T-071)" (ubuntu-24.04 and windows-2022) and sanitizers job |
| T-023 | test_synthesis.cpp | cpp job, step "C++ tests (T-001..T-058, T-063..T-071)" (ubuntu-24.04 and windows-2022) and sanitizers job |
| T-024 | test_synthesis.cpp | cpp job, step "C++ tests (T-001..T-058, T-063..T-071)" (ubuntu-24.04 and windows-2022) and sanitizers job |
| T-025 | test_synthesis.cpp | cpp job, step "C++ tests (T-001..T-058, T-063..T-071)" (ubuntu-24.04 and windows-2022) and sanitizers job |
| T-026 | test_synthesis.cpp | cpp job, step "C++ tests (T-001..T-058, T-063..T-071)" (ubuntu-24.04 and windows-2022) and sanitizers job |
| T-027 | test_synthesis.cpp | cpp job, step "C++ tests (T-001..T-058, T-063..T-071)" (ubuntu-24.04 and windows-2022) and sanitizers job |
| T-063 | test_voice.cpp | cpp job, step "C++ tests (T-001..T-058, T-063..T-071)" (ubuntu-24.04 and windows-2022) and sanitizers job |
| T-P18 | test_cli_binary.py | python job, step "Toolkit tests and CLI integration" |
| T-P26 | test_evaluate.py | python job, step "Toolkit tests and CLI integration" |
| T-P20 | test_evaluate.py | python job, step "Toolkit tests and CLI integration" |
| T-P19 | test_export_rvc.py | python-torch job, step "Export parity (T-P19)" |
| T-P09 | test_metrics.py | python job, step "Toolkit tests and CLI integration" |
| T-P10 | test_metrics.py | python job, step "Toolkit tests and CLI integration" |
| T-P11 | test_metrics.py | python job, step "Toolkit tests and CLI integration" |
| T-P12 | test_metrics.py | python job, step "Toolkit tests and CLI integration" |
| T-P03 | test_prepare.py | python job, step "Toolkit tests and CLI integration" |

The unknown-outcome thresholds SC-4…SC-7 (`eval/thresholds.json`) are deliberately not gated in CI: the frozen procedure records
them and gate G-001 decides (2B.4, PK-29). Their environments and miss rules are pre-decided in D-041 §Targets.

## 3. CI artifact assertions
`ci.yml` has one upload step (`cli-linux`, `if-no-files-found: error`) and one download step (`actions/download-artifact@v8`,
which fails when the artifact is missing). The `if: always()` steps are annotation/summary steps that run after a failure and
cannot turn a failed job green; the `python` job's job-level `if: always()` still fails at the download when `cpp` produced no artifact.

## Re-checks after the fixes
`tools/notebook_dryrun.py` 57/57 ok, T-P16/T-P17 pass, `ctest` in the full tree 67/67 (xvfb), frozen manifest OK.
