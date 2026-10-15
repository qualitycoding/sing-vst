# Human gates (Rule 10, 3.3)

At a gate the implementer halts, writes `GATE-<id>.md` at the repository root (evidence bundle below, every number generated
by a command — PK-05), saves it, and ends its turn with a message to the owner that names the gate, links the file and lists
the allowed responses. The owner answers in the conversation; the implementer copies the answer verbatim into the
`## Response` section of the same file before acting on it. While halted it may continue steps that do not depend on the gate's outcome, never an external or irreversible
action. Responses other than those listed are treated as `stop`. **`stop`** at any gate means: do not continue delivery steps;
run the closing steps S-RETRO and S-KNOW (S-KNOW still asks G-003), then end.

### G-001 Result gate (after S-017)
- **Trigger:** S-017 has produced `report.json` and the renders for the owner's first voice.
- **Evidence:** report.json and its provenance; `metrics.judge` verdicts against the unmeasured defaults; guide-only baseline
  (similarity, WER); octave-error fraction; RTF on the hosted CPU; `budget.json` (GPU-hours used); the five converted and five
  guide renders, which stay on the owner's Drive (`out/eval/renders/`, D-035) and are listened to there; the
  "implemented, unverified" checklist (`docs/UNVERIFIED.md` from S-011: editor behaviour, file dialogs, host compatibility);
  instructions to **build the plugin from source** on the owner's computer (plan/ENVIRONMENT.md §Owner build, for their OS; no plugin binaries are published — A-013, D-026), copy the VST3 bundle to the user VST3 folder, load the
  voice package from their Drive, and render the five phrases with `singvst-render` (RTF there).
- **Questions:** (1) Do the converted renders sound like the target singer, and are the lyrics understandable? (2) Which
  thresholds should bind (keep defaults / set values)? (3) Does the plugin load and play in your DAW?
- **Responses:** `proceed` (defaults bind; continue to S-018) · `proceed-with-thresholds: <json>` (planning amendment updates
  eval/thresholds.json via 2E.4, then continue) · `retrain: <data/epochs/de-reverb change>` (repeat S-017 while `budget.json` `gpu_hours` < 20, A-015; otherwise ask again) ·
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
- **Evidence:** the notebook to open (Colab or Kaggle), the Drive/dataset layout it expects, the budget (A-015), and the
  consent and platform-terms statements (A-011, C-018).
- **Questions:** (1) Are the recordings your own voice or used with the singer's consent, and is this use within the
  platform's terms? (2) De-reverb: use the audio-separator model (licence unstated, C-043) or supply dry recordings (D-025)?
  (3) Colab or Kaggle?
- **Responses:** `run: colab|kaggle, dereverb: yes|no[, epochs: <N>]` (the owner runs the notebook per D-035 and attaches `report.json`,
  `report.json.provenance.json` and `verdict.json` to the conversation) · `stop`. Recordings, renders and voice packages are
  never uploaded to the repository (A-011, T-062).

### G-005 Guide voicebank (before S-016)
- **Trigger:** S-015 is done; S-015's last action writes `GATE-G-005.md` and halts.
- **Evidence:** TIGER DiffSinger v102 facts (C-036), its licence (C-037: personal, non-commercial, no redistribution), the
  fact that it is never committed or bundled (D-026), and the alternative (any DiffSinger voicebank meeting D-012).
- **Responses:** `use-tiger` · `use-voicebank: <URL, licence>` (planning amendment checks it against D-012) · `stop`.
