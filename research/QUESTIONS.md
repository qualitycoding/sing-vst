# Research question tree (R1)

Profiles: `software`, `computational` (plan/PROFILE.md). Each leaf names the claim that answers it and what it informs.
Status: **A** answered (claim at `verified`/`corroborated`), **R** answered but below the bar (logged as a risk), **O** open (carried to a plan step or gate).

## E — Engineering (`software`)

- **E1 Which conversion engine?**
  - E1.1 Licence and maintenance of RVC vs so-vits-svc → C-001, C-002 → D-020. **A**
  - E1.2 Can RVC v2 inference run without Python, deterministically? Noise is drawn inside `infer` (C-003); no exporter upstream (C-004) → D-012 (noise as input), S-013, T-039, T-P19. **A**
  - E1.3 Content features and frame rates → C-020, C-021 → D-012, T-021, T-039. **A**
- **E2 How do pitch + lyrics become a sung guide for the converter?**
  - E2.1 Is there a ready singing synthesiser with ONNX deployment? DiffSinger → C-006, C-009, C-033, C-034, C-035. **A**
  - E2.2 Is there an English DiffSinger voicebank the owner may use? TIGER v102 → C-010, C-036, C-037 → G-005, D-026. **A** (licence: personal non-commercial only, R-004)
  - E2.3 Exact input conventions (padding, gender/velocity, speaker embedding, depth/speedup) → C-034, C-038, C-041 → D-012, T-037, T-038. **A**
  - E2.4 Is the guide reproducible? No: C-040 → D-012, D-017, R-005. **A**
  - E2.5 Guide speed on CPU → C-039 (measured RTF 1.10 on 2 threads) → D-017 expectation. **A**
- **E3 Plugin framework and host integration**
  - E3.1 JUCE version, licence, build requirements → C-012 → D-001, D-026. **A**
  - E3.2 Can lyrics arrive from the host? No (C-011) → D-010 (text box + MIDI-file lyric events, C-013), A-005. **A**
  - E3.3 Plugin validation tool and its real CLI → C-015 → T-059, D-018. **A**
  - E3.4 Does JUCE 9.0.3 build a VST3 on the CI runners (Linux 24.04, Windows 2022)? → Windows: **yes** — CI run 38699430452 built the plugin, CLI and tests on `windows-2022` in 9 min 25 s (tests red on stubs, as expected). Linux: the first run was killed by an unbounded `make -j` (C-055); with `--parallel 4` it builds (run 38733038059), and pluginval 1.0.4 strictness 5 (T-059) passes on the stub on both OSes. **A**
- **E4 Native inference runtime**
  - E4.1 ORT version, assets, checksums, C++20 → C-014 → D-002. **A**
  - E4.2 Windows DLL conflicts → C-026 → D-024. **A**
  - E4.3 Explicit-path loading with manual API init → C-042 (Linux verified; Windows in CI at S-007) → D-024, T-041. **A/O**
- **E5 Lyrics → phonemes**
  - E5.1 Dictionary, licence, coverage → C-016 → D-005, T-007. **A**
  - E5.2 Does the guide's phoneme set cover CMUdict? Yes for TIGER (C-036) → D-012. **A**
- **E6 Training on free hosted GPUs (A-009)**
  - E6.1 Colab free-tier limits and rules → C-017, C-018 → D-016, G-004, T-P17. **A**
  - E6.2 Kaggle limits → C-019 → D-016, R-008. **R** (no Tier-1 source reachable)
  - E6.3 RVC training entry points, filelist, configs, assets → C-022, C-029, C-030, C-032 → D-016, S-014. **A**
  - E6.4 Dependency pins and package indexes → C-023 → D-019. **A**
  - E6.5 De-reverb before training → C-043 → D-025, R-009. **A** (model licence unknown)
- **E7 Planning-environment reachability** → C-044, C-045 → D-018, plan/ENVIRONMENT.md. **A**

## N — Computational (`computational`)

- **N1 Pitch mapping and quantisation**
  - N1.1 MIDI → Hz (A4 = 440 Hz, MIDI 69) → D-007, T-017. **A** (standard; PK-32)
  - N1.2 RVC coarse-pitch bins → C-021 → T-021. **A**
- **N2 Timing**
  - N2.1 Frame rates and rounding: DiffSinger 44100/512 frames, RVC 100 fps → C-009, C-020 → D-007 (cumulative rounding), T-022. **A**
  - N2.2 Host PPQ → take sample mapping → D-009, T-025, T-030. **A** (derivation in D-009)
- **N3 Quality measurement (unknown outcomes, Rule 8)**
  - N3.1 Speaker similarity → C-028 (Resemblyzer weights in package) → D-017, T-P20. **A**
  - N3.2 F0 accuracy → C-027 (pyworld harvest; needs setuptools < 81) → D-017, T-P10. **A**
  - N3.3 Intelligibility → Whisper (`openai-whisper` 20250625, D-017) → T-P20. **O**: runs only on the hosted GPU at S-017.
  - N3.4 Acceptance thresholds: unmeasured defaults until G-001 (PK-29) → A-012, eval/thresholds.json. **O** (by design)
- **N4 Gain staging** → D-021 (soft clip at 0.98, unclipped peak reported), T-023, T-030. **A**

## Pruned
- so-vits-svc training details (E1.1 excludes it). SOME note extraction (not used). openvpi vocoder fine-tuning (TIGER ships its own vocoder; C-007 kept only as the fallback-vocoder licence fact).
