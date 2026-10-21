# Human gates (Rule 10, 3.3)

At a gate the implementer halts, writes `GATE-<id>.md` at the repository root (evidence bundle below, every number generated
by a command — PK-05), saves it, and ends its turn with a message to the owner that names the gate, links the file and lists
the allowed responses. The owner answers in the conversation; the implementer copies the answer verbatim into the
`## Response` section of the same file before acting on it. While halted it may continue steps that do not depend on the gate's outcome, never an external or irreversible
action. Responses other than those listed are treated as `stop`. **`stop`** at any gate means: do not continue delivery steps;
run the closing steps S-RETRO and S-KNOW (S-KNOW still asks G-003), then end.

### G-001 Result gate (after S-017)
- **Trigger:** S-017 has produced `report.json` and the renders for the owner's first voice.
- **Evidence:** report.json and its provenance; `metrics.judge` verdicts against the unmeasured defaults, with each metric's
  `spread.json` [min, max] over the 5 repeats and **indeterminate** wherever a threshold lies inside it (D-017, R-018);
  guide-only baseline (similarity, WER); `ceiling.json` (same-singer similarity ceiling, R-032); octave-error fraction; RTF
  on the hosted CPU; `budget.json` GPU-hours, labelled "lower bound (5-minute heartbeat)" (R-034); `training.json`
  (epochs trained); the converted and guide renders, which stay with the owner — Colab: `<root>/run<RUN>/out/eval/renders/` on Drive; Kaggle: inside `out-run<RUN>.tar` in the
  notebook version's output (`tar -xf out-run<RUN>.tar eval/renders`) — D-035 and are listened to there; the
  "implemented, unverified" checklist (`docs/UNVERIFIED.md` from S-011: editor behaviour, file dialogs, host compatibility);
  instructions to **build the plugin from source** on the owner's computer (plan/ENVIRONMENT.md §Owner build, for their OS; no plugin binaries are published — A-013, D-026), copy the VST3 bundle to the user VST3 folder, load the
  voice package from their Drive, and render the five phrases with `singvst-render` (RTF there): for k in 1…5,
  `singvst-render --voice <voice folder> --midi out/eval/phrases/p<k>.mid --out p<k>.wav` — the transposed phrases that
  `evaluate` wrote, lyrics from their MIDI lyric events (R-030) — (seed 0, defaults of D-014); RTF = Σ `render_seconds` / Σ `audio_seconds` of the five `p<k>.wav.provenance.json`.
- **Questions:** (1) Do the converted renders sound like the target singer, and are the lyrics understandable? (2) Which
  thresholds should bind (keep defaults / set values)? (3) Does the plugin load and play in your DAW?
- **Responses:** `proceed` (defaults bind; continue to S-018) · `proceed-with-thresholds: <json>` (planning amendment updates
  eval/thresholds.json via 2E.4, then continue; the verdict against the defaults stays committed beside the new one,
  `results/<VOICE>/run<RUN>/verdict.bound.json`, which S-017 action 5 computes after the amendment, and
  README and the pull request quote both and say the thresholds were set after the measurement — R-037) · `retrain: <data/epochs/de-reverb change>` (repeat S-017 — a new GATE-G-004.md, all its questions, with `RUN` + 1 and
  the changed Parameters-cell values — allowed only while `gpu_hours + h10 < BUDGET_HOURS − 1` (19 at the default
  `BUDGET_HOURS` 20, D-035), with `gpu_hours` = `results/<VOICE>/ledger.json` `total` (every platform and every unlogged
  hour) and `h10` = the run's train-stage hours (Σ `sessions[].stage_hours["train"]` of its committed `budget.json`) ÷
  (`epochs_trained` ÷ 10), i.e. the hours of 10 more epochs; A-015 per voice (R-086); otherwise
  GATE-G-001.md is re-issued with only `proceed`, `proceed-with-thresholds` and `stop`) ·
  `stop`.

### G-002 External or irreversible actions
- **Trigger:** any binary release, package publication, merge into `main`, deletion of a branch, or change to repository
  settings. **This plan schedules none**: S-019 opens a pull request and stops.
- **Evidence:** what would be published, its licence position (A-013, D-026), and the exact command.
- **Responses:** `approve: <action>` · `decline`. Merging the pull request is always the owner's own action.

### G-003 Lessons and knowledge push (S-KNOW)
- **Trigger:** S-RETRO is done.
- **Evidence:** IDs, titles and tags of every lesson and knowledge item to push; the proposed targets
  `qualitycoding/Lessons` and `qualitycoding/knowledge` (A-014); `tools/check_schema.py` output (all entries valid, no secrets).
- **Responses:** `push-to-proposed` · `push-to: <target>` · `do-not-push`.

### G-004 Owner's hosted-GPU training run (S-017)
- **Trigger:** S-016 is done and G-005 has been answered.
- **Evidence:** the notebook to open, pinned to `EXPECTED_COMMIT` (R-029): Colab
  `https://colab.research.google.com/github/qualitycoding/sing-vst/blob/<EXPECTED_COMMIT>/notebooks/train_voice_colab.ipynb`;
  Kaggle: *File → Import notebook → GitHub* with that commit and path `notebooks/train_voice_kaggle.ipynb`; the Drive/dataset layout it expects, the values to enter in
  the Parameters cell (`VOICE`, `RUN`, `EXPECTED_COMMIT` = the full SHA of the impl branch head after S-016's last save,
  `RESUME` (the Kaggle rule below), `PLATFORM_EXPECTED`, `PRIOR_VOICE_GPU_HOURS` (from the voice ledger), `PRUNE`,
  `DEREVERB`, `EPOCHS` (a multiple of 10), `SPEAKER_ID`, `GUIDE`; D-035, S-017 action 1a); how to hand over
  `upload-run<RUN>.tar`: attach it to the conversation, or — when the implementer reports it cannot find the attachment —
  upload it through GitHub's web interface to a new branch `upload-<VOICE>-run<RUN>` (*Add file → Upload files*; the tar
  holds no audio; S-017 action 2); privacy: the Kaggle dataset and notebook stay **Private**, no version
  is published, the Drive folder is not shared (R-021); Kaggle: run as "Save & Run All" (background, no idle timeout) on a
  T4 GPU with **Internet: On** (clone, installs, Hugging Face), which needs a phone-verified Kaggle account (R-044);
  **resuming** after "start a new session": Colab — reopen the same notebook and *Run all*; Kaggle — in the next version add
  the previous version's output as an input (*Add Input → Your Work → this notebook*), set `RESUME = True` (True exactly when an
  earlier Kaggle version of this voice has a `state.tar` in its output; attach the most recent such version), then *Save & Run All* (cell (3) finds its `state.tar`); a version that ends with
  `failed: <cell> …` printed is reported with that line; the budget (A-015), and the consent and platform-terms statements (A-011, C-018).
- **Questions:** (1) Are the recordings your own voice or used with the singer's consent, and is this use within the
  platform's terms? (2) De-reverb: use the audio-separator model (licence unstated, C-043) or supply dry recordings (D-025)?
  (3) This issue is pinned to `PLATFORM_EXPECTED` (Colab for the voice's first issue, D-035); to use the other platform,
  answer `switch-platform: <other>, hours-used: <figure>` instead of running (0 when no session has run).
- **Responses:** every response about a run on Kaggle (`consent:`, `owner-fixed:`, `prune:`, `budget-exhausted`,
  `switch-platform:` from Kaggle, `failed:`) is followed by one line per Kaggle version the owner ran **since this
  GATE-G-004.md was issued** (per issue, never cumulative), in order from the Versions panel: its `seq <n> state.tar
  <sha256>` last line, or `killed <run time as the panel shows it, e.g. 1h 23m 45s>` for a version that printed none (its
  run time is added to the ledger's `unlogged` hours as an upper bound; R-083, R-095); every `hours-used:` figure is the
  `platform` value of the last `hours: platform <p> voice <v>` line the notebook printed (D-035 §Time and budget) ·
  `consent: yes, visibility: private, voice: <VOICE>, platform: colab|kaggle, dereverb: yes|no, epochs: <N>` (`platform`
  equals `PLATFORM_EXPECTED`)
  (the values the owner used; `RUN` is always the number GATE-G-004.md states; without `consent: yes` and `visibility: private` the response is `stop`; the owner runs the notebook per
  D-035 and attaches `upload-run<RUN>.tar` and pastes the `sha256sum` line cell (17) printed) ·
  `owner: <message>` printed by the notebook → the owner fixes the stated condition (recordings, disk, RAM, parameters)
  and answers `owner-fixed: <cell>, hours-used: <figure>` (or `prune: <exp>, hours-used: <figure>` on Kaggle); the
  implementer re-issues with the same commit, not counted as an attempt, at most twice per issue, then `BLOCKED.md` (R-087,
  R-102) ·
  `budget-exhausted, hours-used: <figure>` (answered when cell (17) printed `budget: no checkpoint`: the voice reached
  its budget before a loadable snapshot; no upload exists; S-017 writes GATE-G-001.md with only that evidence and the
  responses `stop` and `raise-budget: <hours>` — a planning amendment to A-015 run as HANDOFF §Amendments says — never
  `proceed`; R-086) ·
  `switch-platform: colab|kaggle, hours-used: <figure>` (a new RUN on the other platform, whose `PRIOR_VOICE_GPU_HOURS`
  S-017 action 1a takes from the voice ledger; R-082) ·
  `failed: <cell number> <error text>, hours-used: <figure>` (the implementer fixes the notebook — one attempt per report, at most three per G-004
  issue (a `retrain` re-issue starts a new count; a `failed:` re-issue keeps `RUN`; switching platform is a new `RUN`, with
  `PRIOR_VOICE_GPU_HOURS` covering the hours already used, R-082), then
  `BLOCKED.md`; GPU hours already used stay in `budget.json` — and re-issues G-004) · `stop` (the ledger is not changed).
  After every other response S-017 updates `results/<VOICE>/ledger.json` (D-035 §Voice ledger) before acting on it.
  Recordings, renders and voice packages are never uploaded to the repository (A-011, T-062).

### G-005 Guide voicebank (before S-016)
- **Trigger:** S-015 is done; S-015's last action writes `GATE-G-005.md` and halts.
- **Evidence:** TIGER DiffSinger v102 facts (C-036), its licence (C-037: personal, non-commercial, no redistribution), the
  fact that it is never committed or bundled (D-026), and the alternative (any DiffSinger voicebank meeting D-012).
- **Responses:** `use-tiger` · `use-voicebank: <URL, licence>` (planning amendment checks it against D-012) · `stop`.
