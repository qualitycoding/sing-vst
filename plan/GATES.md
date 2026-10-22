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
  on the hosted CPU; `budget.json` GPU-hours, labelled "lower bound (5-minute heartbeat)" (R-034); the voice ledger
  `results/<VOICE>/ledger.json` (`colab`, `kaggle`, `unlogged`, `total`; "A-015 exceeded by <total − BUDGET_HOURS> h"
  when `total` > `BUDGET_HOURS`, R-095); `training.json`
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
  the changed Parameters-cell values — allowed only while `gpu_hours + r·(h_pre + h10) < BUDGET_HOURS − 1` (19 at the
  default `BUDGET_HOURS` 20, D-035), with `gpu_hours` = `results/<VOICE>/ledger.json` `total` (every platform and every
  unlogged hour), from the evaluated run's committed `budget.json`: `h_pre` = Σ over its sessions of `stage_hours` of
  prepare, rvc-f0 and rvc-features (a new RUN repeats them) and `h10` = Σ `stage_hours["train"]` ÷ (`epochs_trained` ÷ 10),
  the hours of 10 epochs (a new RUN trains from the pretrained model, so this is the least it needs), and `r` = 1, or —
  when the response adds, removes or replaces recordings, in which case it must state `recordings-minutes: <m>`, the
  total minutes of the new recording set (as `training.json` `raw_minutes` measures them; without it the response is asked
  for again at most twice, then treated as `stop`) — `max(1, m ÷ training.json raw_minutes)`; a response naming no
  recording change uses `r` = 1; A-015 per voice (R-086); it is a minimal-feasibility test (a retrain that enables
  de-reverb or raises `EPOCHS` needs more and may still end in `budget-exhausted`, which this gate then handles, R-110), and
  after a prune `h10` includes the discarded training's hours (conservative); otherwise GATE-G-001.md is re-issued with only `proceed`,
  `proceed-with-thresholds` and `stop`) ·
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
  `RESUME` (the Kaggle rule below), `PLATFORM_EXPECTED`, `PRIOR_VOICE_GPU_HOURS` (from the voice ledger), `KILLED_HOURS`, `PRUNE`,
  `DEREVERB`, `EPOCHS` (a multiple of 10), `SPEAKER_ID`, `GUIDE`; D-035, S-017 action 1a); how to hand over
  `upload-run<RUN>.tar`: attach it to the conversation, or — when the implementer reports it cannot find the attachment —
  upload it through GitHub's web interface to a new branch `upload-<VOICE>-run<RUN>-<n>` (`n` = 1, then 2 for a re-request;
  *Add file → Upload files*; the tar holds no audio; S-017 action 2); the ledger's current figure for `PLATFORM_EXPECTED`
  (the value the ledger keeps when this issue produced none); privacy: the Kaggle dataset and notebook stay **Private**, no version
  is published, the Drive folder is not shared (R-021); Kaggle: run as "Save & Run All" (background, no idle timeout) on a
  T4 GPU with **Internet: On** (clone, installs, Hugging Face), which needs a phone-verified Kaggle account (R-044);
  **resuming** after "start a new session": Colab — reopen the same notebook and *Run all*; Kaggle — in the next version add
  as an input the output of the newest version, in any of your Kaggle notebooks for this voice, that has a `state.tar`
  (*Add Input → Your Work*; importing a re-issued commit with *File → Import notebook* creates a new Kaggle notebook, so the
  version to attach may belong to an earlier notebook; a version that stopped in cells (3)–(4) carries a copy of the
  `state.tar` it restored and may be attached too — same hash), set `RESUME = True` (True exactly when an
  earlier Kaggle version of this voice has a `state.tar` in its output), add the run time of every version of this issue
  that you will report as `killed` to `KILLED_HOURS` — per version (h·3600 + m·60 + s) / 3600 rounded **up** to 4 decimals
  (3h 20m 0s → 3.3334), or 12.0 for `killed ?` (D-035) — then *Save & Run All* (cell (3) finds its `state.tar`); a version that ends with
  `failed: <cell> …` printed is reported with that line; the budget (A-015), and the consent and platform-terms statements (A-011, C-018).
- **Questions:** (1) Are the recordings your own voice or used with the singer's consent, and is this use within the
  platform's terms? (2) De-reverb: use the audio-separator model (licence unstated, C-043) or supply dry recordings (D-025)?
  (3) This issue is pinned to `PLATFORM_EXPECTED` (Colab for the voice's first issue, D-035); to use the other platform,
  answer `switch-platform:` (below) instead of running.
- **Hours in every response** (D-035 §Voice ledger; R-082, R-095): on **Colab**, attach
  `MyDrive/singvst/<VOICE>/budget-voice.json` downloaded from Google Drive (no runtime needed) and write `hours-used:
  drive`, or `budget-voice: none` when that file does not exist; on **Kaggle**, write `hours-used: <p>` with `p` from the
  last `hours: platform <p> voice <v>` line above the newest `seq <n> state.tar` line among this issue's versions (never
  from a version you report as `killed`), or `hours-used: none` when no version of this issue printed a `seq` line, and
  add one line per Kaggle version you ran **since this GATE-G-004.md was issued**, oldest first (the Versions panel lists
  newest first): `seq <n> state.tar <sha256>` (its last line), `no-gpu` (a version that printed no `hours:` line), or
  `killed <run time as the panel shows it, e.g. 1h 23m 45s>`, or `killed ?` when the panel shows none (any other version; its time is added to `unlogged` as an
  upper bound). In the responses below `<hours>` stands for this part.
- **Responses:** `consent: yes, visibility: private, voice: <VOICE>, platform: colab|kaggle, dereverb: yes|no, epochs: <N>`
  + `<hours>` (`platform` equals `PLATFORM_EXPECTED`; the values the owner used; `RUN` is always the number GATE-G-004.md
  states; without `consent: yes` and `visibility: private` the response is `stop`; the owner runs the notebook per D-035,
  attaches `upload-run<RUN>.tar` and pastes the `sha256sum` line cell (17) printed. When `voice:`, `dereverb:` or `epochs:`
  differ from the issued values, or `training.json` `epochs_requested` differs from the issued `EPOCHS`, S-017 asks once
  for a corrected response or a re-run; the gate file's values always name `RUN`, the paths and the ledger record) ·
  `owner-fixed: <cell from the owner: line, or params>` + `<hours>` after the notebook printed `owner: <cell> <message>`:
  the owner fixed the stated condition (recordings, disk, RAM, the notebook to open); `params` answers "parameters changed
  within run", and the re-issue repeats this RUN's original `VOICE`, `RUN`, `DEREVERB`, `EPOCHS`, `SPEAKER_ID`, `GUIDE`
  and platform, while `PRIOR_VOICE_GPU_HOURS`, `KILLED_HOURS`, `RESUME`, `PRUNE` and `EXPECTED_COMMIT` follow S-017 action 1a · `prune: <exp>` + `<hours>` (Kaggle,
  after the unreadable-checkpoint `owner:` line; at most once per RUN). For both the implementer re-issues with the same `EXPECTED_COMMIT`, not counted as
  a `failed:` attempt; at most two `owner-fixed:` and `prune:` re-issues together per RUN, then `BLOCKED.md` (R-087, R-102) ·
  `budget-exhausted` + `<hours>` (answered when cell (17) printed `budget: no checkpoint`: the voice reached its budget
  before a loadable snapshot; no upload exists; S-017 writes GATE-G-001.md with only this evidence — the voice ledger,
  the notebook's `budget: no checkpoint` line, the response's `<hours>` part and version lines, and the run's
  `EPOCHS` — and the responses `stop`,
  `raise-budget-to: <new BUDGET_HOURS total>` — valid only here, at least the ledger `total` + 2 (1 h reserve plus at
  least 1 h of training; a lower value is asked for again at most twice, then treated as `stop`), a
  planning amendment to A-015 run as HANDOFF §Amendments says — and, when an earlier run of this voice was evaluated, also
  `proceed` and `proceed-with-thresholds` for the newest such run with its evidence and a note that run <RUN> was cut by the
  budget; R-086, R-110, R-114) ·
  `switch-platform: colab|kaggle` + `<hours>` (the named platform must differ from `PLATFORM_EXPECTED`, and a `consent:`
  `platform:` must equal it — else the response is asked for again, at most twice, then `BLOCKED.md`; `<hours>` belongs to the platform being left; a new RUN on the other
  platform, whose `PRIOR_VOICE_GPU_HOURS` S-017 action 1a takes from the voice ledger; R-082, R-111) ·
  `failed: <cell number> <error text>` + `<hours>` (the implementer fixes the notebook — one attempt per report, at most
  three `failed:` re-issues per RUN, then `BLOCKED.md`; a `failed:` re-issue keeps `RUN`; a `retrain` or `switch-platform`
  is a new RUN with its own counts; `raise-budget-to` keeps the RUN and its counts — and re-issues G-004) ·
  `stop`, optionally + `<hours>` (recorded when given; R-113).
  Counts are taken from the archived `GATE-G-004.run<RUN>.*.md` files whose `## Response` starts with that keyword
  (`owner-fixed:` and `prune:` pooled); the response being handled is not archived yet, so a re-issue is allowed while the
  archived count is below the limit. A
  response that starts with a listed keyword but lacks a required part is asked for again (at most twice, then
  `BLOCKED.md`) without changing any state; any other text is `stop`. S-017 updates `results/<VOICE>/ledger.json` after
  every response as D-035 §Voice ledger says, before acting on it.
  Recordings, renders and voice packages are never uploaded to the repository (A-011, T-062).

### G-005 Guide voicebank (before S-016)
- **Trigger:** S-015 is done; S-015's last action writes `GATE-G-005.md` and halts.
- **Evidence:** TIGER DiffSinger v102 facts (C-036), its licence (C-037: personal, non-commercial, no redistribution), the
  fact that it is never committed or bundled (D-026), and the alternative (any DiffSinger voicebank meeting D-012).
- **Responses:** `use-tiger` · `use-voicebank: <URL, licence>` (planning amendment checks it against D-012) · `stop`.
