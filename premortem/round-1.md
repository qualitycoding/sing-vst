# Pre-mortem — round 1 (Phase 4)

**Scope.** I read the plan at branch `gen-20261004T095012Z-singing-voice-vst-pitch-lyrics` without changing anything: HANDOFF.md, plan/*.md, eval/PROCEDURE.md, eval/thresholds.json, research/claims.json (all 58 claims), research/PRIOR_KNOWLEDGE.md (PK-01…PK-66 and the per-lesson table), premortem/RISK_REGISTER.md, tests/ (C++ and Python), .github/workflows/ci.yml, tools/, cmake/, core/include/singvst/*.hpp, plugin/, cli/ and python/singvst_train/*.py.

Severity follows Global Rule 4 for the `software` and `computational` profiles. Statements marked UNVERIFIED could not be checked in this read-only, offline review.

**Commit note:** T-P22 scans `premortem/*.md` (tests/python/test_repo.py:108-109), and its R registry comes from premortem/RISK_REGISTER.md (test_repo.py:120). Commit this file together with register rows R-013…R-050, or T-P22 fails (R-049).

---

## 1. Simulation

### 1a. [software] Six months after the merge: the plugin fails catastrophically in the DAW

*Values in this narrative are illustrative, not measurements.*

| When | What the owner sees | Traced root cause |
|---|---|---|
| Merge + 0 | The owner builds the VST3 from source on Windows (plan/ENVIRONMENT.md §Owner build). The voice `myvoice` from run 1 is on Drive, synced locally. | — |
| + 3 weeks | The song is 3:40 long, with one lead and two harmony instances. Every lyric edit or Portamento slider move re-renders the whole take in every affected instance. Each instance runs its own ONNX Runtime sessions with up to 4 intra-op threads, and the DAW drops out during playback. A tempo ramp in the bridge (> 0.1 bpm) leaves the takes stale, so the track is silent while it re-renders continuously. | R-028 (D-010 DECISIONS.md:264-266; D-002 :25-26; C-039 measured a 2-s phrase only) |
| + 2 months | The owner approves the lead take, mixes, and closes the project. The next day the project loads: `setStateInformation` restores notes and lyrics and submits a render (D-010). TIGER draws unseeded noise (C-040), so every instance sings a different performance, with different breaths and vowel colour. The approved take was never stored and cannot be regenerated. | R-017 (C-040, D-010 :274-276; R-005 covers only evaluation) |
| + 4 months | The owner retrains with more recordings. Cell (4) cannot clone `impl-gen-…` because the head branch was deleted at merge, so the owner edits the cell to `main` (R-029). The run reuses `VOICE = myvoice`. The pack stage deletes and rewrites `out/voice/`, Drive sync replaces the local folder, and every older project now silently loads the new voice. The run-1 renders judged at G-001 are gone because `out/eval/` was deleted. | R-015 (pipeline.py:28-30; DECISIONS.md:490-532); R-029 (DECISIONS.md:497-498) |
| + 6 months, **catastrophe** | The owner closes the project while instance 2 renders a 25-s phrase. That phrase is one ONNX Runtime `Run`, and `cancel` is checked only between runs (DECISIONS.md:197). The implementer met D-013's "destructor cancels and joins within 5 s" (DECISIONS.md:234) and T-051, which uses a cooperative fake, with a timed join followed by detach. The worker returns into a freed `GuideEngine`, the DAW crashes on close, and the host's autosave of the project is left half-written. Earlier, intermittent crashes during playback while re-renders were frequent came from the `TakeSlot` acquire window that T-038 cannot reliably expose. | R-025 (D-012/D-013; no engine-lifetime rule); R-024 (playback.hpp:78-96; T-038) |

**Root-cause summary.** Three things fail together:
- The plan assumes that re-rendering is free and repeatable, but it is neither: C-040 makes renders non-reproducible, and D-013 renders the whole take.
- D-012/D-013 specify cancellation and teardown that ONNX Runtime cannot provide.
- Fixed artefact paths (`out/voice`, a branch name) are overwritten or deleted in place.

### 1b. [computational] Twelve months after completion: claimed results do not reproduce

| When | Event | Traced root cause |
|---|---|---|
| G-004 run 1 | Colab, EPOCHS 200. Similarity 0.71, gain 0.13, WER 0.31; below the defaults. The owner answers G-001 `retrain: epochs 400, de-reverb yes` (DR-10). | — |
| G-004 run 2 | The owner sets `EPOCHS = 400` and `DEREVERB = True` in cell (2a). `run_stages` finds the markers and outputs for split … export. Their inputs are files only, and the parameters belong to no stage, so all of them are **skipped**. render-bin re-runs because the fresh clone changes the checkout hash, and that cascades into pack + evaluate. The *same model* is re-evaluated with fresh guide noise: similarity 0.76, gain 0.16. budget.json grows by 0.4 h, which nobody checks. The response "epochs: 400, dereverb: yes" and the results are committed as run 2. G-001 `proceed`; README cites the G-001 record. | R-013 (DECISIONS.md:520-532, :539-540; pipeline.py:24-31) |
| + 12 months | A collaborator (or the owner, on a newer Colab image) tries to reproduce run 2 for a second voice and fails at three layers. (1) The environment: RVC's requirement ranges and the unpinned transitive dependencies resolve differently. The provenance `lockfile_sha256` names python/requirements-lock.txt, which was never installed in the notebook, and budget.json keeps one `commit`. (2) The metric: five re-evaluations of the archived run-2 voice package give similarity between 0.70 and 0.76, so the "pass" was one draw of the noise. (3) The claim itself: `dataset.json` says `dereverb: false` (prepare was skipped). The weights carry no provenance (D-015), so the epoch count cannot be checked, and the RVC logs on Drive were overwritten by later runs. | R-019 (DECISIONS.md:459-471; D-015 :326-330); R-018 (eval/PROCEDURE.md:19; C-040); R-015 |
| RTF claim | The hosted RTF ran with 1 intra-op thread (2 vCPU → `min(4, max(1, 2/2))`, D-002). The owner's G-001 RTF renders used plain-word lyrics on untransposed phrases (GATES.md:18), so they measure a different input from the one evaluated. | R-030 |

**Root-cause summary.**
- Stage identity in the stage runner ignores parameters (R-013).
- The evaluation takes a single sample of a stochastic measurement (R-018, which R-005 does not mitigate).
- The provenance contract is applied to the CI environment, not to the environment that produced the result, and the trained artefacts get no provenance at all (R-019).

---

## 2. Lenses

**Technical correctness.** R-013, R-014, R-017, R-024, R-025, R-026, R-035, R-046, R-050. I checked the frozen numeric expectations of T-048/T-049 (47926 and 47520 samples) and the T-040 length rules by hand against D-007/D-011/D-012; they are consistent. I found no defect in D-004…D-009 beyond those listed.

**Dependency and supply-chain drift.** R-019 (unlocked notebook environment), R-020, R-039, R-041, R-042, R-043. JUCE, ORT, nlohmann/json, pluginval and CMUdict are SHA-checked at download (cmake/Dependencies.cmake:6-29; ci.yml:69-71). Their tags are the residual exposure (R-043).

**Invalid research assumptions.**
- *Claims not `verified`:* C-010 (single-source), C-017 (corroborated), C-018 (corroborated), C-019 (single-source), C-026 (corroborated).
- *Claims with one entry in `sources`:* C-004, C-005, C-006, C-011, C-012, C-013, C-014, C-016, C-020, C-022, C-023, C-024, C-027, C-028, C-029, C-030, C-031, C-032, C-033, C-035, C-036, C-039, C-040, C-041, C-042, C-043, C-045, C-047, C-048, C-049, C-050, C-051, C-052, C-053, C-054, C-055, C-056, C-057, C-058, C-059, C-060.

Review of those claims:
- **Adequate as used:**
  - Spike-of-pinned-code facts, which hold at the pin and are covered by tests: C-004, C-005, C-011, C-012, C-014, C-016, C-020, C-022, C-029, C-030, C-033, C-035, C-036, C-041, C-049, C-050, C-051, C-055, C-056, C-057.
  - Not load-bearing: C-006, C-024, C-031, C-039.
  - C-010 is covered by R-003/G-005. C-018 is covered by R-001. C-026 is covered by R-007, which is adequate: explicit-path loading, a version check, and T-041 on Windows CI.
  - C-027 is effectively superseded by C-046.
  - C-043 is covered by R-009.
- **Needing action:**
  - C-017 conflicts with D-035's Drive symlinks (R-033).
  - C-019 rests on tier-3 sources only, and the run mode and GPU are unaddressed (R-044).
  - C-023's version ranges make the training environment unlocked (R-019), and its index replacement creates R-020.
  - C-028, C-058, C-059 and C-060 were verified by reading source or on another host, never by importing in the notebook environment (R-022).
  - C-032, C-052, C-053 and C-054 leave asset availability and the CI revision exposed (R-042, R-043).
  - C-040 drives R-017 and R-018.
  - C-047 covers resume in the middle of a run, but not resume after completion or a corrupt checkpoint (R-014, R-035).
  - C-048: parity is tested only on random weights (R-050).
- **Labels and stale data (no risk ID):** C-042 is labelled verified, yet its statement says the Windows half "is not yet run". T-041 on Windows CI (S-007, DR-06) closes that gap. C-013's `informs` field is stale: the core uses its own `importMidi` (D-031), not `juce::MidiFile`.
- **Unresearched assumptions with no claim:**
  - That Resemblyzer is valid for singing (R-032).
  - The hosted compiler version (R-023).
  - Drive FUSE throughput and free quota (R-033).
  - Support for the GPU's compute capability in the cu128 wheel (R-044).
  - The Whisper weight host (R-042).
  - webrtcvad's dependency on pkg_resources (R-022).

**Implementer misinterpretation.**
- D-016 "single tar archives" against D-035's Drive symlinks (R-033).
- The Kaggle previous-output path is unspecified (R-016).
- `TakeSlot` protocol (R-024).
- The 5-s join bound against uncancellable runs (R-025).
- The plugin threading model (R-026).
- D-031 running status (R-046).
- G-001 owner render command (R-030).
- One `commit` key in budget.json across sessions (R-029).

**Integrity (Rule 9).**
- Silently re-labelled no-op retrain (R-013).
- Overwritten run evidence (R-015).
- Provenance that names the wrong lock (R-019).
- Unauthenticated transfer of results (R-036).
- Post-hoc thresholds without a disclosure rule (R-037).
- A lesson exemption resting on a non-existent re-evaluation (R-038).

S-017's `git mv` of gate files and the `results/<voice>/run<N>/` layout do keep the gate history.

**Past lessons.** Every PK rule marked `both` was checked against its "Applied via" target.
- *Applied as claimed:* PK-01…PK-30, PK-32, PK-33, PK-36, PK-37, PK-39…PK-42, PK-44…PK-54, PK-56, PK-57, PK-59, PK-60, PK-62, PK-63 (every `Done when` chain S-002…S-019 traced), PK-64 and PK-65.
- *Gaps:*
  - PK-31: speaker similarity has no known-answer validation (R-032).
  - PK-34: the guide's noise is not reproducible (R-017, R-018).
  - PK-38: R-024, R-026.
  - PK-43: disk headroom (R-033) and a checkpoint corrupted when rotated in place, a recurrence of L-20261004T102004Z (R-035).
  - PK-55: CI uses bare `python3` (R-039).
  - PK-58 / PK-66: Kaggle copy steps, a recurrence of L-20261016T000100Z (R-016).
  - PK-61: skipped cases are counted as passed (R-040).
  - PK-13: the Whisper host (R-042).
- *Exemptions:* Of the 33 "not applicable" lessons, 31 are correctly exempt (CFD, percussion, Web Audio, OBD, manuscript, archives). L-20261009T193614Z and L-20261009T151401Z are not (R-038).

**Scale and performance.**
- Whole-take re-rendering, the cost of multiple instances, tempo automation, the per-sample resampler, and re-hashing packages on the message thread (R-028).
- Kaggle re-running the GPU stages every session (R-016).
- Drive I/O during training (R-033).
- Denormals (R-045).

**Security.**
- Dependency confusion during installs with Drive mounted (R-020).
- Visibility of the owner's recordings and voice model (R-021).
- Unbounded take size from untrusted MIDI or state, and ONNX external data (R-027).

On credentials: none are needed (Hugging Face downloads are anonymous, Drive OAuth is the owner's). T-P17 forbids tokens in notebooks and T-P15 runs a secret scan, so no further risk. The notebooks are executed from a mutable branch (R-029).

**Operational realities.**
- Branch-name references break after the merge (R-029).
- CI will go red as new advisories are published, and there is no maintenance procedure (R-041).
- Upstream assets could disappear (R-042).
- Voice packages cannot be rolled back (R-015).
- There is no workaround for a lost approved take (R-017).
- When something breaks after the merge, DR-09 (collect the host log) applies only during implementation, and the plugin writes no log file (folded into R-025's mitigation through the status line).

**Audio thread (PK-38).**
- *Locks and waiting:* `TakeSlot` is wait-free only if the re-validation protocol is specified (R-024). The capture FIFO, the bpm hand-off and state access are unspecified (R-026).
- *Allocation:* processBlock needs no scratch buffer if it renders into channel 0 and copies (mitigation in R-026).
- *Priority inversion:* none, provided `Renderer::latest()`/`status()` are never called from processBlock (D-022 routes playback through `TakeSlot`).
- *Denormals:* R-045.
- *Other:* T-055 forbids gain smoothing, so block-wise gain steps under automation are possible. That is cosmetic and not a separate risk.

**Numerical validity.**
- Lyric and transposition mismatch in the G-001 evidence (R-030).
- Held-out split with few files (R-031).
- Validity of the similarity metric (R-032).
- Single-draw verdicts (R-018).

Checked with no failure mode found:
- The f0/guide/converter frame arithmetic (D-007 E-7, D-012 `T = min(…)`).
- The portamento overlap with the 50-ms F0 scoring edge: at most about 7 % of the interval in frames 50–60 ms, a negligible effect on RMS.
- Double-precision PPQ mapping.
- The A4 = 440 Hz reference.

**Reproducibility.**
- Unlocked notebook environment and wrong-lock provenance (R-019).
- Guide noise (R-017, R-018).
- Mutable branch and per-session commit (R-029).
- Tags and the CI Hugging Face revision (R-043).
- Configure-time git commit (R-047).

Bitwise reproducibility of GPU training is neither claimed nor needed.

**Compute budget.**
- Under-counted GPU hours (R-034).
- Kaggle re-runs (R-016).
- Failures that surface only after the GPU stages (R-022, R-023, R-031).
- Run mode and GPU arch (R-044).
- Silent restart from pretrained weights (R-035).

### Adequacy of existing register entries

| Entry | Verdict |
|---|---|
| R-002 | Inadequate for Kaggle (R-016) and for budget accounting (R-034). |
| R-005 | Inadequate: it covers evaluation as "one recorded run", which fails the computational headline (R-018), and it ignores plugin recall (R-017). |
| R-008 | Under-scoped (R-044). |
| R-010 | Mitigated for notebooks only; the CI job resolves `main` every time (R-043). |
| R-011 | Its DR-10 path is undermined by R-013 and R-018. |
| R-012 | Extended by R-028. |
| R-001, R-003, R-004, R-006, R-007, R-009 | Adequate. |

---

## 3. Risk table

| ID | Description | Lens | Severity | Likelihood | Root cause | Traces to | Proposed mitigation |
|---|---|---|---|---|---|---|---|
| R-013 | A G-001 `retrain` that changes EPOCHS, DEREVERB or SPEAKER_ID silently retrains nothing. `run_stages` skips a stage when its marker equals the hash of its **file** inputs and every output exists. No Parameters-cell value is a stage input (train: `filelist.txt` + `config.json`; prepare: `train/`), so split…export are skipped. render-bin re-runs (a fresh clone changes the checkout hash) and cascades into pack + evaluate, so a new report of the **old** model is committed as run N+1 under the owner's response "epochs: N, dereverb: yes". | technical correctness; integrity | Critical | medium | Stage identity excludes the parameters the stage uses. | DECISIONS.md:520-532, :539-540; python/singvst_train/pipeline.py:24-31; GATES.md:23; DR-10; S-017 | Cell (2a) writes `state/params-<stage>.json` holding the parameters each stage uses, listed among that stage's inputs, so any change re-runs it and everything after it. The notebook prints `run_stages`' return value and stores it in budget.json `sessions[].stages_run`. S-017 refuses a run whose stages_run lacks `train` when the response changed EPOCHS or DEREVERB. |
| R-014 | Retraining reuses the previous run's RVC experiment, because `logs/<voice>/G_2333333.pth`/`D_…` and `assets/weights/<voice>_e*_s*.pth` survive every stage re-run (deliberately, PK-62). (a) A data-change retrain resumes from run 1's checkpoint instead of training afresh. (b) With an unchanged `-te`, train.py resumed at epoch ≥ total runs no epoch and (UNVERIFIED: C-047 does not cover this case) writes no `assets/weights/<voice>.pth`, so the stage raises "missing output" on every retry. Under DR-13, `latest_weights` may pick run-1 weights. | technical correctness | High | medium | Run boundaries are not modelled; the C-047 spike covered resume in mid-run only. | DECISIONS.md:517-519, :536-539; C-047; python/singvst_train/rvc_files.py:33; GATES.md:23 | A `retrain` re-issue uses the experiment and package name `<VOICE>-run<N>` (RVC experiment, weights and out/ subfolders), so no state crosses runs. Spike RVC 81eed5e resume at epoch = total. Treat "exit 0, no final weights, latest checkpoint epoch ≥ EPOCHS" as complete by copying `latest_weights` (as DR-13 does). |
| R-015 | Re-running in the same `<VOICE>` folder deletes the previous run's outputs: pack rewrites `out/voice/`, and evaluate deletes `out/eval/` (the renders the owner listened to at G-001). DAW projects store the voice path (D-010) and silently load the new voice after Drive sync. The earlier package and renders are unrecoverable, so run N's G-001 record loses its audio evidence. | integrity (history); operational | Critical | medium | Outputs live at fixed paths and are deleted before a re-run. | pipeline.py:28-30; DECISIONS.md:490-532, :541-543, :274-276; S-017 action 3; Rule 9 | Per-run roots `out/run<N>/{conv,bin,voice,eval}` and `pack --name <VOICE>-run<N>`; never delete an earlier run's package. GATE-G-004.md names each run's path. The plugin status line shows the loaded manifest name and SHA prefix. |
| R-016 | The Kaggle multi-session flow is incomplete. Cell (3) copies only `state/`, `logs/<voice>/` and `out/budget.json`, so raw_wav/, train/, heldout/, prepared/, weights/, out/conv, out/bin and voicebank/ are missing in the next session. Split therefore re-runs and cascades through the RVC preprocess/f0/feature stages every session, charging GPU time to the 20-h budget. A session that ends after train completed re-runs train, which (R-014b) yields no final weights, a permanent failure. The mount path of "the previous run's output, attached as an input dataset" is unspecified (PK-58). | operational; compute; past lessons | High | medium | Recurrence of L-20261016T000100Z for the Kaggle variant; L-20261015T180000Z. | DECISIONS.md:475-476, :496-497, :520-532; R-002; PK-58; PK-66 | Copy the whole previous `/kaggle/working` except venv and build trees, from `/kaggle/input/<slug>/` found by a glob with an assertion that names it. Add to S-016 a two-session dry run of cells (3) and (7)–(12) against a temporary mock layout with stub stage functions. |
| R-017 | Every plugin render is a new performance. TIGER draws unseeded noise (C-040) and the plugin state persists only notes, lyrics and parameters (D-010). A project reload (the restore submits a render), a host sample-rate change or a voice reload therefore replaces the user's approved vocal with a different one, without warning, and the approved take cannot be regenerated. | technical; reproducibility; operational | Critical | high | A non-reproducible stage sits in a project-recall path; PK-34 cannot apply to the guide. | C-040; D-010 (DECISIONS.md:264-266, :274-276); D-013; R-005; PK-34; L-20261009T120012Z | Persist each Ready take to a cache file keyed by phraseHash and the voice SHA (outside `PluginState`, so frozen interfaces are untouched) and load it on restore instead of re-rendering. Alternatively, an amendment makes the guide noise an ONNX input as D-012 did for RVC, after checking that the pack licence allows private modification (C-037). At minimum, S-018 README documents "freeze or bounce the track". |
| R-018 | Evaluation verdicts rest on one draw of the unseeded guide. Each phrase is rendered once (eval/PROCEDURE.md:19). Similarity, WER and F0 vary between identical runs (C-040: max mel difference 1.86) and no spread is measured, so a verdict near a threshold flips on re-run, and a run-to-run comparison cannot separate improvement from noise. R-005's mitigation is inadequate. | numerical validity; reproducibility | Critical | medium | A stochastic measurement is sampled once. | C-040; D-017; eval/PROCEDURE.md:19-30; R-005; T-P20 | Amendment: render each phrase K ≥ 5 times (converter seed fixed) and report the mean with min/max per metric; G-001 judges with the spread shown. Until then GATE-G-001.md carries a second `evaluate` run of the same package (CPU only) and calls verdicts inside the observed spread indeterminate. |
| R-019 | The training and evaluation environment is unlocked, and the provenance names the wrong lock. The notebook resolves RVC's version ranges (C-023) and all transitive dependencies at run time on a drifting hosted image. Yet the `prepare`/`evaluate` sidecars record `lockfile_sha256` of python/requirements-lock.txt, which the notebook never installs. Trained weights, ONNX exports and voice packages have no provenance (D-015), and budget.json holds a single `commit`. | reproducibility; integrity | Critical | high | The provenance contract was bound to the CI environment, not to the environment that produced the result. | DECISIONS.md:459-471 (esp. :469-471), :326-330, :533; D-019 item 2; C-023 | Cell (4) writes `uv pip freeze --python $VENV/bin/python` to `out/env-freeze.txt`, and driver/CUDA/GPU/image details to `out/env.json`. Sidecars use `--lockfile out/env-freeze.txt`. Pack writes `out/voice/training.json` (epochs trained, commit, env-freeze SHA); unlisted files are ignored by D-008. Per-session commits go in `sessions[]`. Both files are added to the G-004 upload. |
| R-020 | Dependency confusion in the notebook install. `--index-url pypi --extra-index-url download.pytorch.org/whl/cu128 --index-strategy unsafe-best-match` takes the highest version of any name across both indexes (the resolution exploited in the 2022 torchtriton incident), with no hash checking. The code then runs in a Colab runtime with the owner's entire Drive mounted. The CI python-torch job uses the pip equivalent. | security; supply chain | Critical | low | Multi-index resolution without per-package index pinning or hashes. | DECISIONS.md:463-467; ci.yml:149; C-023 | Install torch, torchaudio, triton and the nvidia-* packages from the pytorch index in a separate explicit step (or pin them to that index with uv's explicit index mapping); install everything else from PyPI only, from a hash-locked file generated once and committed beside the notebooks. Mount Drive after the installs (reorder cells (3)/(4)). |
| R-021 | Exposure of the owner's biometric data. Nothing states the visibility of the Kaggle input dataset `singvst-<VOICE>` (raw recordings), of the Kaggle notebook versions (trained weights, voice package, held-out audio in the output) or of the Drive folder. A public dataset or notebook version publishes the owner's voice and a model that clones it. | security | Critical | low | Privacy controls are absent from G-004. | DECISIONS.md:474-476, :490; GATES.md:39-53; A-011; C-018 | GATE-G-004.md requires "Private" for the dataset and notebook and forbids publishing a version. The G-004 response adds `visibility: private`, otherwise `stop`. The Kaggle notebook's first cell prints the reminder, and README repeats it. |
| R-022 | The evaluation stack never runs in the notebook environment before the owner's GPU run. S-015's dry run substitutes Resemblyzer and Whisper, CI installs neither, and C-058/C-059 were read from source only. Resemblyzer imports webrtcvad, whose module imports `pkg_resources` (UNVERIFIED for the resolved version). setuptools ≥ 81 lacks `pkg_resources`, and every setuptools that still ships it carries PYSEC-2026-3447 (C-046). The failure appears at cell (15) after training, and its only quick fix touches security, so the default rule leads to BLOCKED.md. | invalid research assumption; compute | High | medium | API facts were verified by reading, not by importing in the target environment. | PLAN.md:349-359; C-028; C-046; C-058; C-059; C-060; D-019 item 2 | Cell (6) adds `python -c "import resemblyzer, whisper; whisper.load_model('small.en')"` so a failure happens before training. Decide now, in a decision record, the webrtcvad source and the setuptools pin, rather than at G-004. |
| R-023 | `singvst-render` is compiled in the notebook (cell (13)) with the hosted image's compiler and CMake, which have not been checked (C-044). Every verified build uses GCC 13.3 or MSVC (D-001). A C++20 library feature that first appears in GCC 13 (e.g. `<format>`) passes CI and fails on the runtime after the GPU stages. | technical; reproducibility | Medium | medium | The evaluation build's toolchain is neither pinned nor tested. | DECISIONS.md:508-512; D-001; D-033; C-044 | D-033 adds a GCC 11 floor (no `<format>`, `<print>` or `std::expected`). The CLI is built and `g++ --version` printed right after cell (4), before any GPU stage. |
| R-024 | `TakeSlot` is specified by outcome only. The obvious "load `current`, then store `inUse`" leaves a window in which the writer publishes, `collect()` frees the old take, and the audio thread then reads freed memory. T-038's interleaving is probabilistic, also under TSan, so this frozen test cannot reject that implementation. | audio thread; technical | High | low | Protocol unspecified; the test is insufficient. | core/include/singvst/playback.hpp:78-96; DECISIONS.md:249-254; tests/cpp/test_playback.cpp:160-192; PK-38 | Specify a wait-free protocol in D-022. The reader does `inUse.store(BUSY)`, then `p = current.load()`, then `inUse.store(p)`, all seq_cst. `collect()` frees nothing while `inUse == BUSY` and otherwise frees retired takes that differ from `inUse`. The cold read of S-005 checks this sequence. |
| R-025 | `cancel` is checked only before each ONNX run, and one acoustic run covers a whole phrase (seconds to tens of seconds on a desktop CPU, given C-039's 2-s data point). D-013 nevertheless promises a join "within 5 s", and no rule says who owns the engines while a job runs. Detaching to meet 5 s lets the worker use freed engines after the plugin closes or a voice reloads, which crashes the host. Joining instead blocks the message thread for the whole run. T-051's cooperative fake cannot tell the two apart. | technical; operational | High | medium | D-013's bound cannot be met with D-012's cancellation; engine lifetime is unspecified. | DECISIONS.md:197, :230-234; render.hpp:32-48; test_render.cpp T-051; C-039 | Each job captures the engines in a `shared_ptr`. Cancel also calls `Ort::RunOptions::SetTerminate()` on the in-flight run, so ORT stops between graph nodes. Join without detaching. Add a plugin test that destroys the processor during a fixture render. Failures are logged to a file beside the voice. |
| R-026 | The plugin's cross-thread state is unspecified. The 4096-event capture buffer is written on the audio thread, drained by the 4 Hz timer and re-armed by `arm(true)`. Host bpm and sample rate reach the timer from processBlock. `get/setStateInformation` touch lyrics, notes and voice that the editor and timer also mutate, and some hosts call them off the message thread. No plugin code runs under TSan (sanitizer builds use `SINGVST_BUILD_PLUGIN=OFF`), and T-057 is single-threaded. | audio thread; technical | High | low | The plugin threading model is missing from D-010/D-022. | DECISIONS.md:269-273; ci.yml:97, :104; test_plugin.cpp T-057; PK-38 | D-022 amendment: a preallocated SPSC FIFO (e.g. `juce::AbstractFifo`) allocated once in the constructor, with `arm` resetting only indices; bpm and sample rate as atomics; all non-audio state behind one message-side mutex that processBlock never takes; processBlock writes `renderBlock` into channel 0 and copies it, with no allocation for oversized blocks. |
| R-027 | Untrusted MIDI files and DAW state are parsed safely byte by byte (D-031, T-066), but nothing bounds what they make the renderer allocate. One note at tick 2^28 with PPQ 1, or tens of thousands of notes, yields a take of hours, and therefore f0, guide, 16-kHz and `rnd` (192·T) buffers of several GB on the worker inside the DAW. At best that ends in `bad_alloc`; at worst the OS kills the host for running out of memory. ONNX files in a voice package may also reference external data outside the SHA-listed set. | security (DoS); scale | High | low | Validation stops at syntax. | DECISIONS.md:284-297; D-013; voice.hpp:44-46; PK-42 | Amendment: `renderTake`/`importMidi` reject takes over 15 min and more than 5000 notes with a `ValidationError` naming the limit, plus tests. Engine load rejects ONNX models with external-data initializers. |
| R-028 | Whole-take rendering does not scale to songs. Every lyric edit, slider move (at 4 Hz), tempo change > 0.1 bpm or sample-rate change re-renders the entire take. C-039 measured a 2-s phrase only. Each instance opens its own sessions (hubert_base alone is about 95 M parameters, about 0.38 GB in fp32; UNVERIFIED for the export) with up to 4 intra-op threads, so several instances oversubscribe CPU and RAM. Tempo automation keeps takes stale and silent. D-011 specifies the sinc per output sample. `validatePackage` re-hashes the package on the message thread at every load or restore. | scale and performance | Medium | high | Phrase-scoped design (A-006) with no limits or guidance. | DECISIONS.md:25-26, :171-176, :264-266; C-039; R-012; A-006 | Cache renders per phrase (D-012 already splits at SP ≥ 22 frames) so an edit re-renders only changed phrases; one process-wide intra-op thread pool shared by instances; a polyphase table for the resampler; hash on a background thread; README documents short sections at constant tempo. |
| R-029 | Branch names instead of commits. Notebooks clone `impl-gen-…` at HEAD (cell (4)), and the Colab/Kaggle links and the owner build name the same branch. After the merge, and GitHub's head-branch deletion, the links return 404 and cell (4) fails. Before the merge, a `failed:` fix pushed in the middle of a run changes the code between sessions while budget.json keeps one `commit`. | operational; reproducibility | Medium | high | Code is identified by branch name. | DECISIONS.md:497-498, :533; PLAN.md:381-382; plan/ENVIRONMENT.md:74 | GATE-G-004.md gives a commit SHA; cell (4) checks it out and asserts it equals `EXPECTED_COMMIT` from cell (2a). `sessions[]` records each session's commit. S-018 README points the training and build instructions at `main`. |
| R-030 | The G-001 evidence is not the evaluated condition. GATES.md:18 has the owner render `--lyrics-file eval/phrases/p<k>.txt` (plain words: "copper kettles hum at dawn" is 5 words for 7 notes) on the untransposed phrases. eval/PROCEDURE.md:19 renders the transposed MIDI with hyphenated lyric events ("cop- per ket- tles …"). With plain words each two-syllable word sits on one note (D-006: m = min(g, k) with g = 1), and two notes per phrase get the warning "2 note(s) have no lyric". The owner's own renders are garbled, so they judge intelligibility and the plugin on a different input. | numerical validity; misinterpretation | Medium | high | The gate text was written independently of the procedure. | plan/GATES.md:18; eval/PROCEDURE.md:15-19; D-006; D-014; eval/phrases/p1.txt | Drop `--lyrics-file` (the lyrics come from the MIDI events) and render the transposed phrases that evaluate wrote (`out/eval/phrases/<p>.mid`). |
| R-031 | The held-out split is by file: k = max(1, round(0.1·n)) for n ≥ 2, and k = 0 for n < 2. An owner who records one long file gets no held-out set, and evaluation fails at cell (15), after the GPU stages. With 2–4 files, 25–50 % of the recordings are withheld from training. Nothing checks this before training. | numerical validity; compute | Medium | medium | The rule assumes many files (A-010). | python/singvst_train/prepare.py:9-16; eval/PROCEDURE.md:9; A-010; D-017 | Cell (7) stops before training if heldout is empty or under 30 s, or if train is under 10 min, and tells the owner to cut the recordings into at least 10 files. |
| R-032 | "Resembles the target singer" rests on a measure that has not been validated. Resemblyzer 0.1.4 is a speech speaker encoder, and no claim shows that its cosine separates singers. There is no same-singer ceiling (held-out against the training recordings), and the guide baseline is the only floor. The thresholds are defaults (PK-29). | invalid research assumption; numerical validity | Medium | medium | PK-31 was applied to F0 and WER but not to similarity. | DECISIONS.md:354-356; eval/PROCEDURE.md:21-23; C-028; PK-31; PK-35; A-012 SC-4 | A separate script (REPORT_KEYS is frozen) reports the ceiling (held-out against the mean embedding of the training files) in GATE-G-001.md. README calls similarity a proxy confirmed only by the G-001 listening record. |
| R-033 | Colab training I/O and storage. D-035 symlinks `logs/<VOICE>` and `assets/weights` into Drive, so RVC (`-c 0`, rvc_files.py:28) reads thousands of small files per epoch through Drive FUSE, against D-016's "single tar archives" and C-017. The Drive folder also holds raw/, raw_wav/ (PCM_24), copies in train/ and heldout/, prepared/, the RVC features, the G/D checkpoints, about 20 `-sw` weight files, the TIGER pack unzipped twice, and out/ plus its tar. That is several GB against a 15-GB free Drive, with no free-space check (PK-43 checks RAM and GPU only). The implementer has to pick which rule wins. | operational; compute; misinterpretation | Medium | medium | D-016 contradicts D-035; no disk-headroom check. | DECISIONS.md:340-341, :476-479, :486-487; C-017; PK-43; L-20261009T193613Z | Keep the experiment on local disk during a session; restore and sync it as one tar at session start, after each checkpoint save and at session end. Cell (10a) checks Drive free space against an estimate from the dataset size. Remove the raw_wav/ and train/ copies after prepare. State in D-035 which rule wins. |
| R-034 | GPU hours are under-counted. Time is added when a stage "ends (or is interrupted)", but a Colab disconnect or Kaggle hard stop kills the kernel without running any handler, so those hours are never written. budget.json `gpu_hours` (a committed result, G-001 evidence and SC-9's proof) is silently low, and the train timeout and DR-13's 20-h stop are computed from it. T-P20 in cell (16) repeats the whole evaluation outside any stage and is not counted. | compute; integrity | Critical | medium | Accounting depends on the process ending normally. | DECISIONS.md:488, :533-540; A-015; A-012 SC-9; DR-13; R-002 | Every stage, and cell (16), rewrites `out/budget.json` with `atomic_write_text` every 5 min with the running session's GPU time, so a killed session loses at most 5 min. GATE-G-001.md labels `gpu_hours` "lower bound, 5-min heartbeat". |
| R-035 | Training progress can be lost silently. With `-l 1`, RVC overwrites its only `G_2333333.pth`/`D_2333333.pth` in place (C-047). The train stage's own timeout (DECISIONS.md:536), or a VM kill during `torch.save`, can leave a truncated file, and on resume RVC falls back to the pretrained models when none load (C-047). Training restarts from scratch with no error while the budget and the reported epoch count carry on. | technical; data integrity; past lessons | Critical | low | Recurrence of L-20261004T102004Z (checkpoint rotated into a corrupt file); training is killed without a graceful stop. | C-047; DECISIONS.md:342-343, :536; PK-43 | Before launching train.py, load the existing G/D checkpoints and stop if they exist but fail to load, restoring a `.bak` taken after each verified save. Fail a resumed session if RVC's pretrained-load log line appears (spike its exact text at 81eed5e). End the timeout just after a save boundary. |
| R-036 | The transfer of results is unauthenticated. The four files arrive by attachment or paste, are written by the implementer and committed with no check that they come from one notebook run. There is no SHA-256 list from the notebook, no check that verdict.json equals `metrics.judge(report, thresholds)`, and no check that the provenance `voice_sha256`/`git_commit` match budget.json. | integrity (Rule 9) | Critical | low | No end-to-end check on results transferred by a person. | DECISIONS.md:541-543; PLAN.md:402-407; Rule 9 | Cell (17) prints `sha256sum` of the four files, and the G-004 response includes those hashes. S-017 verifies the hashes, recomputes the verdict with `metrics.judge`, checks name and commit consistency and logs the check. A mismatch means requesting the files again, never editing them. |
| R-037 | Thresholds can be set after the results: `proceed-with-thresholds` comes after the owner has read the report. The README or the pull request body could then say the voice "meets the thresholds" without disclosing that they were chosen after measurement. | integrity | Medium | medium | No disclosure rule for post-hoc criteria. | GATES.md:22-23; eval/thresholds.json; D-017; D-030; S-018; S-019; PK-29 | Keep the verdict against the default thresholds committed beside the new one. S-018 and S-019 quote both verdicts and say that the thresholds were set after the measurement. |
| R-038 | Two lesson exemptions rest on controls that do not exist. L-20261009T193614Z is exempt because "G-001 re-runs evaluation after any core change", but no step re-evaluates after S-017, so fixes at S-018 or S-019 leave the committed report describing code that is not merged. L-20261009T151401Z is exempt because "the plan opens no pull requests", but S-019 opens one. | past lessons; integrity | Medium | medium | Stale exemption justifications. | research/PRIOR_KNOWLEDGE.md (rows for both lessons); S-017; S-018; S-019 | S-019 checks that `git diff --stat <report git_commit>..HEAD -- core cli python/singvst_train eval` is empty; if not, it lists the changes in DEVIATIONS.md and the pull request, and asks the owner whether to re-run evaluate. Correct both exemption cells. |
| R-039 | PK-55 is not applied in CI. The `cpp` and `sanitizers` annotate steps call bare `python3` (ci.yml:88, :113), and the implementer may not edit workflows. If the runner's `python3` changes or disappears, no test-summary notice is written, and D-036 ends in BLOCKED.md. | past lessons; drift | Medium | low | Recurrence of L-20261015T073000Z. | ci.yml:88, :113; PK-55; D-036 | Planning amendment: `actions/setup-python@v7` with 3.12 in both jobs (T-061 allows it), then call `python`. |
| R-040 | `tools/ci_annotate.py` counts any testcase without `<failure>` or `<error>` as passed. A skipped or not-run case (`<skipped>`: ctest "Not Run" or "Disabled", Catch2 `SKIP`) is therefore listed under `passed:`, which is exactly the evidence D-036 accepts. | past lessons; technical | High | low | Recurrence of L-20261015T190000Z: a pass inferred from the absence of a failure. | tools/ci_annotate.py:20-21; D-036; PK-61 | List skipped cases separately and never count them as passed. S-001 checks that every expected ID appears under `passed:`. |
| R-041 | T-P21 runs pip-audit live on every CI run. After the merge, any new advisory against the lock (numpy 1.26.4, scipy 1.13.1, protobuf, onnx …) turns the `repo` job red, and DR-07 exists only during implementation. | operational; drift | Medium | high | A time-dependent frozen test with no maintenance owner. | test_repo.py T-P21; ci.yml:33-35; D-019; DR-07 | S-018 README documents the owner's DR-07 procedure and explains that a red T-P21 means an advisory was published, not a regression. |
| R-042 | Single points of upstream availability, with no archive kept by the owner: the TIGER v102 release asset (a personal repository), Hugging Face `lj1995/VoiceConversionWebUI` at the S-013 revision, RVC at 81eed5e, and Whisper's weight host (hard-coded in openai-whisper and absent from plan/ENVIRONMENT.md §Hosts, PK-13). Losing any of them blocks training or evaluating a new voice. | drift; operational | Medium | low | Assets are downloaded only at run time. | DECISIONS.md:499, :545-552; C-032; C-036; C-052; C-059; PK-13; R-010 | On the first run, archive the TIGER zip, the RVC assets and the Whisper `small.en` weights with their SHA-256 under `<root>/assets-archive/`; cells (5), (14) and (15) prefer the archive. The owner keeps a fork of RVC. |
| R-043 | Some pins are only tags or branches. Dependencies.cmake fetches JUCE `GIT_TAG 9.0.3` and Catch2 `v3.16.1`, and the check for a moved tag runs only in the sandbox bootstrap, not in CI or the owner's build. CI's python-torch job resolves Hugging Face `main` on every run, so R-010 is mitigated for the notebooks only. | drift; reproducibility | Low | low | Tag and branch references in files the implementer cannot change. | cmake/Dependencies.cmake:49, :53; ci.yml:156; R-010; DR-02 | Use the commit SHAs from plan/ENVIRONMENT.md as `GIT_TAG`, without shallow fetch. Planning amendment: pin `REV` in ci.yml to the revision S-013 records. |
| R-044 | The Kaggle assumptions rest on tier-3 sources (C-019). The plan does not say whether to run interactively (idle timeout) or as a background "Save Version"; it does not mention the phone verification Kaggle requires for GPU and internet; and it does not check that the allocated GPU (P100 sm_60 or T4 sm_75) is in the cu128 torch 2.7.1 arch list (sm_60 support UNVERIFIED). | invalid research assumption; compute | Medium | medium | Kaggle facts are unverified (C-044). | C-019; R-008; D-016; DECISIONS.md:488-489 | GATE-G-004.md (Kaggle) prescribes "Save & Run All", a T4 GPU and phone verification. Cell (1) asserts that the device's compute capability is in `torch.cuda.get_arch_list()`. |
| R-045 | There is no denormal protection: D-002 sets no `session.set_denormal_as_zero`, and processBlock is not required to use `ScopedNoDenormals`. Diffusion and vocoder tails can produce subnormal values that slow inference on x86. | audio thread; performance | Low | low | Omission. | DECISIONS.md:25-26; D-022; PK-38 | Set the ORT session option `session.set_denormal_as_zero = 1`; wrap processBlock in `juce::ScopedNoDenormals`. |
| R-046 | D-031 does not say whether meta and sysex events cancel running status. The SMF spec says they do, many real files rely on the status continuing, and D-031 makes "a data byte with no running status" an error. T-065's fixture uses an explicit status after its meta event, so the implementer must guess. | misinterpretation; technical | Medium | medium | Specification gap. | DECISIONS.md:288-290; tests/fixtures/make_fixtures.py:148-152; T-065 | Decide it in D-031: meta and sysex do not clear running status, as common readers behave. Until amended, record the choice in DEVIATIONS.md under the default rule. |
| R-047 | The CLI's `git_commit` provenance is captured at configure time (`execute_process(git rev-parse HEAD)`). Incremental rebuilds after new commits (the sandbox trees are configured once at S-000; an owner runs `git pull` then `cmake --build`) stamp renders with an old commit. | reproducibility | Low | medium | Commit captured at configure time. | cli/CMakeLists.txt:2-6; D-014 | Generate the commit header in a custom command on every build, or make configure depend on `.git/HEAD` and the ref file. |
| R-048 | `JUCE_MODAL_LOOPS_PERMITTED=1` is a PUBLIC definition of the shipped plugin, added for the tests' message pumping. It permits synchronous file choosers and alerts in the editor, which hang some VST3 hosts on Linux; the file dialogs are "implemented, unverified" (D-027). | technical; operational | Low | low | A test convenience leaks into the product build. | plugin/CMakeLists.txt:19; D-027; PK-39 | D-027 requires `FileChooser::launchAsync` and no modal loops in the editor; S-011's cold read checks this. |
| R-049 | T-P22 scans `premortem/*.md`, so the IDs R-013…R-050 cited in this file fail T-P22 unless premortem/RISK_REGISTER.md gains their rows in the same commit. | process | Low | medium | The scan and the registry are coupled. | tests/python/test_repo.py:108-120 | Commit this round together with the register rows. |
| R-050 | Export parity is tested only on random weights (`make_test_weights`; T-P19 in CI and in cell (6)). The trained fp16 weights exported at cell (12) are never compared with RVC's torch output, so an export defect specific to trained weights reaches evaluation unnoticed. | technical; numerical validity | Low | low | The parity check is not run on the artefact that ships. | D-012; DECISIONS.md:500, :508; tests/python/test_export_rvc.py; C-048; DR-14 | The export stage runs `export_rvc.parity(<rvc>, assets/weights/<voice>.pth, out/conv/rvc_synth.onnx)` and stops above 1e-3 (DR-14). |

COUNTS: Critical=10 High=8 Medium=14 Low=6
