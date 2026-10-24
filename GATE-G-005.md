# GATE G-005 — Guide voicebank (before S-016)

Raised 2026-10-24T15:30:59Z by S-015. Steps S-016 onward are halted until you answer. Every fact below comes from a committed spike or claim
(PK-05); none is from memory.

## What is being decided
The training notebooks build a voice package from two parts: a **guide** (a DiffSinger voicebank that sings the typed pitch and
lyrics) and a **converter** (an RVC model trained on your recordings that changes the guide's timbre to your voice). The guide
is not trained here. This gate picks which guide voicebank the notebooks and the first voice package use.

## Evidence
- **TIGER DiffSinger v102** (C-036; spike research/spikes/tiger-guide/output.txt): English; release `v102`, file
  `TIGER_DS_v102_PACK.zip`, SHA-256 `925ca2ad44287757d26628608b2744381e75748042d0e6fae356ee8cdae19f4e`.
  Its acoustic model takes tokens, durations, f0, gender, velocity, a 256-value speaker embedding, depth and speedup; it
  bundles its own vocoder (44100 Hz, hop 512, 128 mel bins), 7 speaker embeddings, and a 68-entry phoneme list that
  contains all 39 CMUdict phones. Measured on 2 threads: guide real-time factor 1.10. Its acoustic graph draws unseeded noise
  (two RandomNormalLike nodes; two identical runs differ by up to 1.86 in the mel), which is why renders are repeated 5 times and
  takes are recalled from the take cache (C-040, D-012, D-038).
- **Licence** (C-037): the repository is CC BY-NC-ND 4.0 plus a Commons Clause (no commercial use, no redistribution, no
  derivatives); the pack's extra licence is MIT-style but forbids commercial and harmful uses; the character terms allow using
  the voice to represent another character with credit. **Personal non-commercial use is free under both.**
- **Handling** (D-026, A-011): the voicebank is never committed, bundled or redistributed; a voice package containing it stays on
  your machine or private Drive. The notebooks download it at run time from its release page; the repository holds no copy.
- **Alternative**: any DiffSinger voicebank meeting D-012 (acoustic ONNX with only the supported inputs — tokens, durations, f0,
  gender, velocity, spk_embed, languages, steps/depth or speedup — and no energy, breathiness, voicing or tension input; a
  vocoder taking mel and f0; 44100 Hz, hop 512; a phoneme list covering the CMUdict phones or a language prefix map). A planning
  amendment checks the URL and licence against D-012 before S-016 starts (plan/PROTOCOL_EXCERPTS.md 2E.4).
- **Dry run of the evaluation** (S-015): the evaluation command ran end to end on the fixture voice with stand-in speaker and
  speech libraries: 100 renders (5 phrases x 5 repeats, with and without conversion), `report.json`, `spread.json`, the
  provenance sidecar and `verdict.json` were written. Its values are meaningless and its status was "invalid: f0: only 7 scored F0
  frames in phrase p2 (repeat 0)", as expected for models that echo their inputs.

## Allowed responses
- `use-tiger` — use TIGER DiffSinger v102 as the guide, for personal non-commercial use only.
- `use-voicebank: <URL, licence>` — use another voicebank; the implementer halts and you start a planning amendment that checks it
  against D-012 (re-research, re-freeze with tools/freeze.py, cold read) before S-016 resumes.
- `stop` — do not continue delivery steps; run the closing steps S-RETRO and S-KNOW, then end.

Any other text is treated as `stop`.

## Response
(awaiting the owner's answer; it is copied here verbatim before the implementer acts on it)
