# Assumptions (Phase 0.3.6)

The intake batch (2026-10-04) offered 15 numbered defaults. The owner answered two of them — the repository and the training
compute — and supplied a credential; every other item adopted its proposed default (protocol 0.3.6.3). The owner's
standing choice of knowledge store (qualitycoding/Lessons and qualitycoding/knowledge) was applied at R0.

### A-001 Planning environment
Planning ran in Claude's cloud workspace with the repositories attached through the session's GitHub connection (the pasted
token was removed from disk; lesson L-20261010T000101Z). Subagents are available from 2026-10-15 and are used for the cold
read (3.6) and the pre-mortem (Phase 4). **Source:** owner (repository + credential); planner (environment).

### A-002 Target repository
`github.com/qualitycoding/sing-vst` (public, Apache-2.0). **Source:** owner, 2026-10-04.

### A-003 Architecture
A guide singer (DiffSinger ONNX acoustic model + vocoder) renders pitch and lyrics; an RVC v2 model trained on the owner's
recordings converts its timbre (D-020). **Source:** default.

### A-004 Conversion engine
RVC (MIT, maintained; C-001) — "so-vits-rvc" in the request is read as the RVC / so-vits-svc family; so-vits-svc is archived
and AGPL-3.0 (C-002) and is not used. **Source:** default.

### A-005 Lyrics input
Lyrics are typed into the plugin's text box (grammar D-004: `-` splits a word, `+` holds a syllable over the next note,
`[ph ph]` gives phonemes) or imported from MIDI-file lyric events (D-031). Hosts cannot send lyric text to a JUCE VST3
(C-011). **Source:** default.

### A-006 Rendering mode
Lookahead rendering: notes are captured from the host or imported, rendered on a background thread, and played back in sync
with the host's position (D-009, D-013). Live low-latency singing from a keyboard is out of scope. **Source:** default.

### A-007 Language
English only (CMUdict, D-005). **Source:** default.

### A-008 Platforms and stack
C++20, JUCE 9.0.3, VST3 + Standalone, Windows x64 and Linux x64; ONNX Runtime 1.31.0 on CPU in the plugin (D-001, D-002).
macOS/AU out of scope. **Source:** default (JUCE pinned by research, C-012).

### A-009 Training compute
Training runs on a **free hosted GPU** — Google Colab free tier (primary) or Kaggle (fallback) — driven by notebooks the
owner runs (D-016). **Source:** owner, 2026-10-04 ("use a free online GPU, like google ai audio", read as Google Colab).

### A-010 Source recordings
10–60 minutes of mono singing per voice, WAV/FLAC; several files from one singer make one voice; a held-out 10 % by file is
never trained on (D-017). Reverberant material is de-reverbed only if the owner chooses it at G-004 (D-025). **Source:** default.

### A-011 Rights and consent
Supplied voices are the owner's own or used with the singer's explicit consent. The notebooks require
`CONSENT_CONFIRMED = True` plus a one-line attestation before any data step; recordings, voice packages and trained weights
are never committed to any repository (T-062). Colab forbids "creating deepfakes" (C-018): the owner confirms at G-004 that
the use complies with the platform terms. **Source:** default.

### A-012 Success criteria
SC-1 build: the plugin builds as VST3 + Standalone on Windows x64 and Linux x64 (CI `cpp`).
SC-2 lyrics and pitch: typed or imported lyrics are sung on the given notes (T-001…T-031, T-048…T-058, T-P18).
SC-3 host integration: playback follows the host position and tempo; state saves and restores (T-032…T-038, T-053…T-057).
SC-4 similarity: speaker similarity ≥ 0.75 and ≥ 0.15 above the guide baseline (T-P20, values at G-001).
SC-5 pitch: F0 error ≤ 25 cents RMS on interior voiced frames (T-P09, T-P10, T-P20).
SC-6 intelligibility: Whisper WER ≤ 0.25 on the evaluation phrases (T-P11, T-P20).
SC-7 speed: rendering at or faster than real time on the owner's CPU (T-P20 RTF; G-001).
SC-8 plugin validity: pluginval strictness 5 passes on both platforms (T-059).
SC-9 training on a free hosted GPU within the budget, resumable across sessions (T-P05, T-P06, T-P16, T-P17, T-P24).
SC-10 listening sign-off by the owner at G-001.
SC-4…SC-7 thresholds are **unmeasured defaults** (eval/thresholds.json `"status": "unmeasured-default"`); G-001 decides
which bind (PK-29). **Source:** default.

### A-013 Licence and release
sing-vst code is Apache-2.0. JUCE is AGPLv3 or commercial (C-012), so any distributed plugin binary is AGPLv3 unless the
owner holds a JUCE licence; this plan publishes **source only** — any binary release is gate G-002. The TIGER guide voicebank
(personal, non-commercial; C-037) is never committed or redistributed (D-026). **Source:** default.

### A-014 Knowledge store
Lessons: `qualitycoding/Lessons`; knowledge items: `qualitycoding/knowledge` (both private). Read at R0 (`ac028c7`,
`09f3458`); written only at S-KNOW after G-003. **Source:** owner's standing choice.

### A-015 Compute budget
≤ 20 GPU-hours of training per voice; each hosted session plans ≤ 10 h of work (under the 12 h limits, C-017, C-019).
**Source:** default.

### A-016 Who runs what
The implementing agent (cloud workspace, CI) builds and tests everything that runs without a GPU or the owner's data. The
**owner** runs the training notebook on Colab/Kaggle at G-004 (the agent cannot reach those hosts, C-044) and does the
listening check at G-001 on their own computer. **Source:** planner (follows A-009 and C-044).
