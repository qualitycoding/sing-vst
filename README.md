# sing-vst

A VST3 and Standalone instrument (Windows x64, Linux x64) that sings typed or MIDI-imported lyrics on MIDI
notes, in a voice trained from your own recordings.

> **Status: built but not working end to end.** `main` holds only the licence, two blind-listening helper
> scripts and this file. The implementation is on the **`impl-gen-20261004T095012Z-singing-voice-vst-pitch-lyrics`**
> branch (not merged). It is waiting on you: training a voice needs a free hosted GPU (gate G-004), and no
> voice has been trained yet. No singing output has been judged by ear, and the blind listening test
> (gate G-001) is blocked.

## How it is designed to work

1. A **guide** voice (a DiffSinger voicebank) sings the pitch and lyrics you give it.
2. A **converter** (an RVC v2 model trained on your recordings) changes the guide's timbre to yours.
3. The plugin loads the resulting voice package and renders phrases on a background thread, caching takes.

The guide voicebank chosen for the first package is TIGER DiffSinger v102. Its licence forbids commercial
use and redistribution (gate G-005), so a voice built with it is for personal use.

## What exists on the implementation branch

- `core/`: the C++ engine (voice loading, lyrics-to-phoneme conversion, rendering, MIDI import, state).
- `plugin/`: the JUCE plugin with a lyrics box, voice and MIDI loaders, a capture button, a status line and
  five parameters.
- `cli/`: the `singvst-render` command-line renderer.
- `notebooks/`: Colab and Kaggle notebooks that train a voice and build the voice package.
- `tests/`: frozen C++ and Python tests, plus evaluation phrases and thresholds in `eval/`.
- `docs/UNVERIFIED.md`: a list of behaviour that has no automated test because it needs a person, a DAW
  or a GPU. Nothing on that list is claimed to work.

## Next steps

Run the training notebook (gate G-004) and send back the result. After that the blind listening test
(`scripts/make_blind_pairs.py`, `scripts/score_blind.py`) can run against real renders.

The plan and research are on `gen-20261004T095012Z-singing-voice-vst-pitch-lyrics` (start with
`HANDOFF.md`).

## Licence

Apache-2.0 (see `LICENSE`). Third-party models, voicebanks and libraries keep their own licences.
