# Implemented, unverified

Behaviour that has no automated test because it needs a person, a real DAW or a GPU. Each bullet names the plan item it
belongs to. S-017 copies the editor list into GATE-G-001.md as the owner's checklist (PK-39). Nothing here is claimed to work.

## Editor (D-027, implemented in `plugin/PluginEditor.*`; the processor behind it is tested by T-053…T-058)
- **Lyrics box (D-027 "lyrics text editor")**: typing updates the stored lyrics; a render starts 500 ms after the last
  keystroke (D-010). The debounce feel and caret behaviour were not exercised. Lyrics changed by MIDI import or a restored
  project appear in the box only while it has no keyboard focus.
- **Load voice… (D-027 `launchAsync` dialogs, R-048)**: the folder chooser opens asynchronously with no modal loop. Opening, cancelling
  and choosing a folder were not run; the load itself (`loadVoice`) is tested by T-058.
- **Import MIDI… (D-027, D-031)**: the file chooser with `*.mid;*.midi`. The dialog was not run; `importMidiFile` is tested by T-056.
- **Arm capture (D-027, D-010)**: a toggle button mirrors the processor's capture state, so it pops out when a capture ends. The
  button's state synchronisation and the "armed: press play" hint were not exercised. The state machine is tested by T-057.
- **Status line (D-027, D-010, R-015, R-058)**: voice name, first 8 hex digits of `voice_sha256`, render state, capture hint,
  last error and the take-cache size. Its text and refresh at 4 Hz were not looked at on screen.
- **Warnings list (D-027)**: a read-only multi-line box listing `lastWarnings()`. Layout and scrolling were not looked at.
- **Parameter controls (D-027 "five parameters generated from `kParams`")**: four sliders and one toggle with host automation
  through `AudioProcessorValueTreeState` attachments. Dragging, text entry and automation gestures in a host were not run;
  the parameter table itself is tested by T-053.
- **Resizable window (D-027)**: the layout of every control at sizes between 480x420 and 1400x1000 was not checked.
- **Keyboard focus (CMake `EDITOR_WANTS_KEYBOARD_FOCUS`)**: whether a given DAW passes typing to the lyrics box was not checked.

## Hosts and audio (D-009, D-010, D-022)
- **Real DAW loading and playback**: pluginval (T-059) loads the plug-in; playback in an actual DAW, transport jumps, loops and
  tempo changes were not run (DR-09 covers reported failures).
- **Live capture from a MIDI keyboard**: T-057 drives the capture with a fake play head and MIDI buffers only.
- **Sample-rate change while a project is open**: the resampled copy is tested by T-071 and the worker only by code review.

## Converter (D-012, S-013)
- **Unvoiced consonant noise (D-012 converter, DEVIATIONS S-013)**: the NSF source's noise is read from the seed input `rnd`, each value
  held for 2.5 samples, instead of drawn fresh at every sample as in RVC. Parity with RVC's own `infer` is exact when all noise is
  zero (2e-7) and the graph is deterministic, but whether fricatives and breaths sound natural was not listened to. Judge at G-001.
- **Real trained weights**: T-P19 uses randomly initialised test weights (`make_test_weights`); export of an actually trained
  checkpoint (float16 weights, `emb_g` size from training) is first exercised in the owner's notebook at G-004.

## Training notebooks (D-016, D-035, S-016)
- **De-reverb path (D-025)**: `prepare --dereverb` runs audio-separator 0.47.0 with the MelBand-Roformer de-reverb model in its own venv. The
  `noreverb` stem name comes from the model's YAML, which is downloaded at `load_model`, so the call sequence was read from the wheel
  (research/spikes/audio-separator-047/output.txt, C-066) but never run; CI does not run it. The model's licence is unstated (C-043).
- **Cells the dry run does not execute**: cells (4) setup and installs, (5) RVC assets, (6) library checks, (10a) memory and disk check, the
  TIGER download in (14), (16) T-P20 and the tar part of (17) need a GPU runtime or the network. Their shell commands were checked for
  syntax and their helper scripts, archive logic and result parser were run locally against the real tools, but the cells themselves
  first run on Colab or Kaggle at gate G-004. Expect `owner-fixed:` or `failed:` round trips there.
- **Platform behaviour (D-016, C-017..C-019)**: Colab Drive mounting, Kaggle's "Save & Run All", the 12-hour session limit, the
  500-item output limit and the weekly quota are as documented, not observed.
- **GPU timing and memory (D-035 cell 10a)**: batch size 8 for a GPU of 14 GiB or more (else 4), the 9.5-hour session stop and the train
  timeout were reasoned from the platforms' limits, not measured on a real T4.
