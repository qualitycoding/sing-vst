# GATE G-004 — your hosted-GPU training run (RUN 1)

Raised 2026-10-24T18:46:20Z by S-017. Nothing after this point can run without you: the training happens on a free GPU you control, on your
recordings. Every value below is generated from the repository state (PK-05).

## What you will do
Run one notebook on **Google Colab** (this first issue is pinned to Colab, because you asked for a Google GPU), let it train an RVC
voice from your recordings, build the voice package, run the held-out evaluation, then send me one small file: `upload-run1.tar`.
The notebook downloads the guide voicebank (TIGER DiffSinger v102, personal non-commercial use only, never committed or shared).
Your recordings, the renders and the voice package stay on your Drive.

## 1. Open the notebook (pinned to one commit)
- Colab: https://colab.research.google.com/github/qualitycoding/sing-vst/blob/6cffb4c5c06a1e0fcf362be0186b6c1eb19cccb7/notebooks/train_voice_colab.ipynb
- The commit is `6cffb4c5c06a1e0fcf362be0186b6c1eb19cccb7`. The notebook checks that the code it clones is exactly this commit and stops otherwise.
- Kaggle (only if you answer `switch-platform: kaggle` first, see below): *File -> Import notebook -> GitHub*, this commit and path
  `notebooks/train_voice_kaggle.ipynb`.

## 2. Put your recordings on Drive
`MyDrive/singvst/<VOICE>/raw/` with your own singing or speech as `.wav` or `.flac` files. You need **at least 10 recordings**; the notebook sets
about a tenth aside by file as a held-out test set and stops before training if that part is under 30 s or the rest under 10 minutes.
Dry, close-miked, one voice per file works best. Do not share the Drive folder.

## 3. Edit two cells only
**Cell (2) consent.** Set `CONSENT_CONFIRMED = True` and `ATTESTATION` to exactly:

> I confirm these recordings are my own voice, or are used with the singer's consent, and that this use is within the platform's terms.

**Cell (2a) parameters.** Enter these values (the notebook checks the commit, the platform and that nothing changes within a run):

| Name | Value for this issue |
|---|---|
| `VOICE` | `myvoice` (or your own name: lower-case letters, digits and `-`; tell me in the response) |
| `RUN` | `1` |
| `EXPECTED_COMMIT` | `6cffb4c5c06a1e0fcf362be0186b6c1eb19cccb7` |
| `RESUME` | `False` (Colab keeps its state on Drive; Kaggle rule below) |
| `PLATFORM_EXPECTED` | `"colab"` |
| `PRIOR_VOICE_GPU_HOURS` | `0.0` (no earlier hours: there is no ledger yet) |
| `KILLED_HOURS` | `0.0` (must stay 0.0 on Colab) |
| `PRUNE` | `""` |
| `DEREVERB` | `False` (see question 2) |
| `EPOCHS` | `200` (a multiple of 10) |
| `SPEAKER_ID` | `0` |
| `GUIDE` | `"tiger"` (your G-005 answer) |

The ledger's current figure for Colab is **0.0 GPU hours**. The whole voice has a budget of **20 GPU hours** (A-015); each session is
limited to about 10 hours; the notebook reserves 1 hour for export and evaluation.

## 4. Run it
Choose a **GPU runtime** (a T4 is enough; a High-RAM runtime if it asks for one), then *Run all*. If a session ends with "start a new session",
reopen the same notebook and *Run all* again: training resumes from its checkpoints on Drive. Do not edit any other cell.

If the notebook prints a line starting with `owner:`, fix what it says and answer `owner-fixed: <cell>` (below). If it prints `failed: <cell> ...`,
send me that line.

## 5. Hand over the result
Cell (17) writes `upload-run1.tar` next to your voice folder on Drive and prints a `sha256sum` line. Send me:
1. the **line** it printed (paste it as text), and
2. the file `upload-run1.tar` **attached** to the conversation. It holds only numbers and logs (no audio). If I cannot find the attachment I will ask you
   to upload it instead through GitHub's web interface (*Add file -> Upload files*) to a new branch `upload-<VOICE>-run1-<n>`.
3. the hours: download `MyDrive/singvst/<VOICE>/budget-voice.json` from Google Drive (no runtime needed), attach it, and write `hours-used: drive`
   (or `budget-voice: none` if that file does not exist).

## Privacy (R-021, A-011)
Recordings, renders and the voice package are never uploaded to this repository. Keep the Drive folder unshared. On Kaggle, the dataset and notebook must be
**Private** and no version may be published.

## Kaggle instead of Colab (only if you prefer it)
Answer `switch-platform: kaggle` with `budget-voice: none` **before running anything**; I then issue a Kaggle version of this gate as RUN 2. Kaggle needs a phone-verified
account, a private dataset `singvst-<VOICE>` holding your recordings, *Save & Run All* on a T4 with **Internet: On**, and after each "start a new session"
you attach the newest version's output that has a `state.tar` (*Add Input -> Your Work*), set `RESUME = True`, add the run time of any version you will report as
`killed` to `KILLED_HOURS` (per version: (h*3600 + m*60 + s) / 3600 rounded up to 4 decimals, e.g. 3h 20m 0s -> 3.3334; 12.0 for `killed ?`), and run again.

## Questions
1. Are the recordings your own voice or used with the singer's consent, and is this use within the platform's terms?
2. De-reverb: use the audio-separator model (its licence is unstated, C-043) or supply dry recordings (D-025)? The default above is **no de-reverb**: supply dry recordings.
3. This issue is pinned to Colab. To use Kaggle, answer `switch-platform:` instead of running.

## Allowed responses
- `consent: yes, visibility: private, voice: <VOICE>, platform: colab, dereverb: no, epochs: <N>` + hours (`hours-used: drive`) + the `sha256sum` line + the attached `upload-run1.tar`.
  Without `consent: yes` and `visibility: private` the response is treated as `stop`. If `voice`, `dereverb` or `epochs` differ from the values above, I ask once for a corrected response or a re-run.
- `owner-fixed: <cell from the owner: line, or params>` + hours — you fixed what an `owner:` line said; I re-issue this gate with the same commit (at most two of these and `prune:` per run).
- `prune: <exp>` + hours — Kaggle only, after the unreadable-checkpoint `owner:` line.
- `budget-exhausted` + hours — the notebook printed `budget: no checkpoint`; no upload exists.
- `switch-platform: colab|kaggle` + hours — a new run on the other platform.
- `failed: <cell number> <error text>` + hours — I fix the notebook (one attempt per report, at most three per run).
- `stop`, optionally + hours.

Any other text is treated as `stop`. Hours, for Colab: attach `budget-voice.json` and write `hours-used: drive`.

## Response
(awaiting the owner's answer; it is copied here verbatim before the implementer acts on it)
