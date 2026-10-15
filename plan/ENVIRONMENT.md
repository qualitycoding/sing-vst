# Environment (Phase 1.4)

## Pins
| Component | Version | Identity | Source |
|---|---|---|---|
| JUCE | 9.0.3 | tag commit `be29c81492b6151c8ea8d14c840e1311963b3a83` | C-012, research/spikes/deps-pins |
| Catch2 | v3.16.1 | `08092139210881f01a34e60c5f2fd6afa0ea4024` | C-045 |
| nlohmann/json | 3.12.0 | json.tar.xz `42f6e95c…dfff7aa` | C-049 |
| ONNX Runtime | 1.31.0 | linux tgz `cc5c72ba…eb03a57`, win zip `3958d8a4…0b82195` | D-002 |
| CMUdict | `74790861f652b15e4ac49015a90074ad62a27690` | cmudict.dict `81917843…91c3d22` (vendored, third_party/cmudict) | C-016 |
| pluginval | 1.0.4 | Linux zip `c01c49d8…b55352`, Windows zip `c08e61ce…ec715ab` | C-015, C-049 |
| CMake | ≥ 3.22 (sandbox `cmake --version` 3.28.3 on 2026-10-15; CI runner default); always `--parallel <N>` (C-055) | | C-012, C-055 |
| Compilers | GCC 13.3 (ubuntu-24.04), MSVC (windows-2022) | | D-001 |
| Python | **3.12** (`/usr/bin/python3.12` in the sandbox; `python-version: "3.12"` in CI) — never bare `python3` (PK-55) | | D-019 |
| Toolkit lock | `python/requirements-lock.txt` (32 lines, incl. pip 26.2.1, setuptools 84.0.0, wheel 0.48.0) | | D-019, C-046 |
| RVC | commit `81eed5e8f68b6bed1789f682fe78cdd324495afc` | | C-001, C-022 |
| RVC assets | Hugging Face `lj1995/VoiceConversionWebUI`, `--revision main` (S-013 records the resolved revision here) | | C-032 |
| huggingface_hub (download venv only) | 2.2.0 (`hf download` flags checked 2026-10-15) | | C-032 |
| GitHub Actions | checkout v7, setup-python v7, upload-artifact v7, download-artifact v8 | | C-045 |

Full hashes are in `cmake/Dependencies.cmake`, `tools/bootstrap_test_env.sh` and `.github/workflows/ci.yml`; they are
checked at configure or download time (DR-02).

## Setup commands (verified in the planning sandbox, 2026-10-15)
```bash
# C++ (Linux): pinned JUCE/Catch2/ORT outside the repository, then the two build trees
bash tools/bootstrap_test_env.sh "$HOME/deps"
cmake -S . -B ../build-core -G Ninja -DCMAKE_BUILD_TYPE=Release -DSINGVST_BUILD_PLUGIN=OFF \
  -DFETCHCONTENT_SOURCE_DIR_JUCE="$HOME/deps/JUCE" -DFETCHCONTENT_SOURCE_DIR_CATCH2="$HOME/deps/Catch2" -DSINGVST_ORT_DIR="$HOME/deps/ort"
cmake -S . -B ../build-full -G Ninja -DCMAKE_BUILD_TYPE=Release -DSINGVST_BUILD_PLUGIN=ON -DSINGVST_BUILD_TESTS=ON \
  -DFETCHCONTENT_SOURCE_DIR_JUCE="$HOME/deps/JUCE" -DFETCHCONTENT_SOURCE_DIR_CATCH2="$HOME/deps/Catch2" -DSINGVST_ORT_DIR="$HOME/deps/ort"
setsid nohup cmake --build ../build-core > ../build-core.log 2>&1 < /dev/null &      # long builds: PK-18
# Linux packages for the plugin build (C-050): see .github/workflows/ci.yml step "JUCE Linux packages"; xvfb for plugin tests.
# Python toolkit
/usr/bin/python3.12 -m venv ../venv-lock && ../venv-lock/bin/python -m pip install --no-deps -r python/requirements-lock.txt
../venv-lock/bin/python -I -m pytest -q -m "not torch and not voice"
```
Evidence: `tools/bootstrap_test_env.sh` printed the pinned commits and ORT 1.31.0; both build trees built (BUILD_EXIT=0) and
ran red (research/spikes/red-verification/output.txt); the clean venv reproduced the lock exactly and pip-audit was clean
(T-P21 passed live, same file).

## Hosts (PK-13; research/spikes/hosts, probed 2026-10-14)
| Host | From the cloud workspace | Alternative channel |
|---|---|---|
| pypi.org, GitHub (web, git, raw, releases, REST API) | reachable | — |
| download.pytorch.org | unreachable | CI runners (`python-torch` job) and the owner's notebooks |
| huggingface.co | unreachable | CI runners (T-P19b assets) and notebooks (D-016) |
| colab.research.google.com, kaggle.com | unreachable | the owner runs the notebooks at G-004 (A-016) |
| Actions results/log host | unreachable | GitHub REST API: jobs, steps, check-run annotations (D-018, `tools/ci_annotate.py`) |

## Open environment questions
- **Q-E7** (QUESTIONS E3.4): do JUCE 9.0.3 builds succeed on the `windows-2022` runner? Answered by the CI run of S-001.
- **Q-E8**: the Hugging Face revision of `lj1995/VoiceConversionWebUI` used by T-P19b; S-013 records it in the pins table.
