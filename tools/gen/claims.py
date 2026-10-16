"""Writes research/claims.json and the matching knowledge items knowledge/K-*.md (R2: items derived mechanically from claims).
Re-runnable: knowledge items are keyed by claim ID and rewritten only when missing. Every claim records independent_publishers
(lesson L-20261010T000115Z); `corroborated` requires >= 2 publishers with at least one Tier 1 source, `verified` requires a
committed spike (research/spikes/...) among the sources."""
import json, pathlib, sys
ROOT = pathlib.Path(__file__).resolve().parents[2]
RUN = "gen-20261004T095012Z-singing-voice-vst-pitch-lyrics"
GH = "https://github.com/"
RVC = "RVC-Project/Retrieval-based-Voice-Conversion-WebUI/blob/81eed5e8f68b6bed1789f682fe78cdd324495afc/"
C = []

def S(url, title, locator, tier, accessed="2026-10-10", version=""):
    return dict(url=url, doi="", title=title, version=version, locator=locator, accessed=accessed, tier=tier)

def spike(name, locator):
    return S(f"research/spikes/{name}/output.txt", f"spike {name}", locator, 1)

def claim(id, text, kind, lb, sources, conf, informs, tags, version="version-independent", pubs=None, contra=None, kstamp=None):
    C.append(dict(id=id, claim=text, kind=kind, load_bearing=lb, sources=sources, confidence=conf, evidence_class="n/a",
                  independent_publishers=pubs if pubs is not None else len({(s["url"].split("/")[2] if "://" in s["url"] else "this-run") for s in sources}),
                  contradicted_by=contra or [], informs=informs, tags=tags, applies_to_version=version, kstamp=kstamp))

UF = "upstream-facts"
claim("C-001", "RVC-Project/Retrieval-based-Voice-Conversion-WebUI is MIT-licensed; pinned commit 81eed5e8f68b6bed1789f682fe78cdd324495afc (latest release 2.3.260718, 2026-07-21).",
      "policy", True, [spike(UF, "PASS C-001"), S(GH + RVC + "LICENSE", "LICENSE", "file", 1)], "verified", ["D-020", "D-026"],
      ["subject:rvc", "tech:rvc", "domain:singing-voice-synthesis"], "RVC 81eed5e")
claim("C-002", "svc-develop-team/so-vits-svc is AGPL-3.0 and archived (last push 2023-11-11), so it is not the converter.",
      "policy", True, [spike(UF, "PASS C-002a"), S("https://api.github.com/repos/svc-develop-team/so-vits-svc", "GitHub API repository metadata", "archived, pushed_at", 1, "2026-10-04")],
      "verified", ["D-020"], ["subject:so-vits-svc", "domain:singing-voice-synthesis"])
claim("C-003", "RVC v2 SynthesizerTrnMs768NSFsid.infer(phone, phone_lengths, pitch, nsff0, sid, ...) samples its prior noise internally (torch.randn_like(m_p) * 0.66666), so a deterministic ONNX export must take that noise as an input.",
      "software", True, [spike(UF, "PASS C-003a/b/c"), S(GH + RVC + "infer/module/models.py", "infer/module/models.py", "lines 646-676", 1)], "verified",
      ["D-012", "T-039", "T-P19"], ["subject:rvc", "tech:rvc", "tech:onnx"], "RVC 81eed5e")
claim("C-004", "The pinned RVC tree has no ONNX export module (only infer/rmvpe.py mentions onnx); sing-vst provides its own exporter.",
      "software", True, [spike(UF, "PASS C-004")], "verified", ["D-012", "S-013"], ["subject:rvc", "tech:rvc", "tech:onnx"], "RVC 81eed5e")
claim("C-005", "RVC v2 ships training configs for 32 kHz and 48 kHz only (configs/v2/32k.json, 48k.json).",
      "software", True, [spike(UF, "PASS C-005")], "verified", ["D-008", "D-016"], ["subject:rvc", "tech:rvc"], "RVC 81eed5e")
claim("C-006", "openvpi/DiffSinger (Apache-2.0, pinned ba031f6f2f969373b49a926cf8b007e9ae48834f) deploys models as ONNX via scripts/export.py acoustic|variance|nsf-hifigan.",
      "software", False, [spike(UF, "PASS C-006a/b")], "verified", ["D-012"], ["subject:diffsinger", "tech:diffsinger"], "DiffSinger ba031f6")
claim("C-007", "openvpi community NSF-HiFiGAN / PC-NSF-HiFiGAN vocoder weights are CC BY-NC-SA 4.0 (code AGPL-3.0); the pc_nsf_hifigan_44.1k_hop512_128bin_2025.02 ONNX takes mel[1,T,128] and f0[1,T] and returns waveform[1,T*512].",
      "policy", False, [spike("vocoder-onnx", "licence line, inputs, outputs"), spike(UF, "PASS C-007a")], "verified", ["D-026"],
      ["subject:openvpi-vocoders", "tech:diffsinger"], "pc-nsf-hifigan 2025.02")
claim("C-009", "DiffSinger acoustic ONNX inputs are tokens[1,n] int64, durations[1,n] int64, f0[1,T] float plus optional embeds (gender, velocity, spk_embed, languages, energy, breathiness, voicing, tension) and sampling controls; output mel[1,T,bins]. The vocoder takes mel and f0. OpenUtau defaults: 44100 Hz, hop 512, 128 mel bins.",
      "software", True, [spike(UF, "PASS C-009a..e"), spike("tiger-guide", "acoustic inputs")], "verified", ["D-012", "T-042", "T-043"],
      ["subject:diffsinger", "tech:diffsinger", "tech:onnx", "subject:openutau"], "DiffSinger ba031f6 / OpenUtau a06ab28")
claim("C-010", "No OSI- or CC-BY-licensed English DiffSinger voicebank was found; the English voicebank found (TIGER v102, C-036) is free for personal non-commercial use only.",
      "policy", True, [S("https://github.com/spicytigermeat/tiger_diffsinger", "TIGER repository README and LICENSE.md", "License section", 1),
                       S("https://www.openutau.com/Voicebank-development/", "OpenUtau voicebank development", "Machine Learning voicebank development", 3)],
      "single-source", ["G-005", "D-026", "A-013"], ["subject:diffsinger-voicebanks", "tech:diffsinger"], pubs=2)
claim("C-011", "VST3 defines NoteExpressionTextEvent (kTextTypeID, kPhonemeTypeID) but JUCE 9.0.3's VST3 wrapper turns kNoteExpressionTextEvent into an empty MidiMessage, so host lyric text never reaches a JUCE plugin.",
      "software", True, [spike(UF, "PASS C-011a/b")], "verified", ["D-010", "A-005"], ["subject:vst3", "tech:juce", "tech:vst3"], "JUCE 9.0.3")
claim("C-012", "JUCE 9.0.3 modules are dual-licensed AGPLv3 / commercial JUCE 9 licence; its CMake needs cmake >= 3.22 and the C language enabled.",
      "policy", True, [spike(UF, "PASS C-012a/b")], "verified", ["D-001", "D-026"], ["subject:juce", "tech:juce", "tech:cmake"], "JUCE 9.0.3")
claim("C-013", "juce::MidiFile (JUCE 9.0.3) reads lyric meta events (type 0x05) with timestamps convertible to seconds.",
      "software", True, [spike("juce-lyrics", "output.txt")], "verified", ["D-010", "T-P18"], ["subject:juce", "tech:juce", "subject:midi-lyrics"], "JUCE 9.0.3")
claim("C-014", "ONNX Runtime 1.31.0 (MIT) publishes onnxruntime-linux-x64-1.31.0.tgz (sha256 cc5c72ba...) and onnxruntime-win-x64-1.31.0.zip (sha256 3958d8a4...) on GitHub Releases; its C++ API works with g++ 13 / C++20.",
      "software", True, [spike("ort", "sha256 lines, ORT 1.31.0 out[0]=9")], "verified", ["D-002", "plan/ENVIRONMENT.md"], ["subject:onnxruntime", "tech:onnxruntime", "tech:cpp"], "onnxruntime 1.31.0")
claim("C-015", "pluginval 1.0.4 (GPL-3.0) has CLI options --strictness-level, --skip-gui-tests, --output-dir, --validate and no --validate-in-process; level 5+ runs Steinberg's VST3 validator.",
      "software", True, [spike(UF, "PASS C-015a/b/c"), S("https://github.com/Tracktion/pluginval/releases/tag/v1.0.4", "release notes", "1.0.0 changes", 1, "2026-10-04")], "verified",
      ["T-053", "D-018"], ["subject:pluginval", "tech:pluginval"], "pluginval 1.0.4")
claim("C-016", "CMUdict at 74790861f652b15e4ac49015a90074ad62a27690 (BSD-style licence) has 135,166 entries / 126,052 words in ARPAbet with stress digits; cmudict.dict sha256 81917843...; out-of-vocabulary words exist.",
      "software", True, [spike(UF, "PASS C-016a/b; sha256 line")], "verified", ["D-005", "T-007"], ["subject:cmudict", "tech:g2p"], "cmudict 74790861")
claim("C-017", "Google Colab free tier: notebooks run at most 12 hours depending on availability, idle runtimes time out, limits are unpublished and fluctuate, GPU types vary; notebooks load from GitHub; Drive I/O should use archives, not many small files.",
      "policy", True, [S("https://research.google.com/colaboratory/faq.html", "Colab FAQ", "Resource Limits; drive.mount", 1, "2026-10-04"),
                       S("https://www.hivenet.com/post/google-colaboratory-gpu-complete-guide-to-free-cloud-gpu-access-and-limitations", "Hivenet guide", "Free tier", 3, "2026-10-04")],
      "corroborated", ["A-009", "D-016"], ["subject:google-colab", "tech:google-colab"])
claim("C-018", "Colab disallows 'creating deepfakes' on all managed runtimes (added May 2022) and, on the free tier, bypassing the notebook UI to drive a web UI; runtimes may be terminated.",
      "policy", True, [S("https://research.google.com/colaboratory/faq.html", "Colab FAQ", "Which activities are restricted in Colab?", 1, "2026-10-04"),
                       S("https://www.bleepingcomputer.com/news/google/google-quietly-bans-deepfake-training-projects-on-colab", "BleepingComputer", "article 2022-05-30", 3)],
      "corroborated", ["D-016", "G-004", "T-P17"], ["subject:google-colab", "tech:google-colab"])
claim("C-019", "Kaggle Notebooks: 12-hour CPU/GPU sessions, a floating weekly GPU quota shown in account settings (commonly about 30 h), background ('Save Version') sessions not subject to the interactive idle limit, GPU P100 or T4 x2.",
      "policy", True, [S("https://www3.nd.edu/~dchiang/teaching/nlp/2023/kaggle.html", "Notre Dame course notes", "batch sessions", 3, "2026-10-04"),
                       S("https://gpuperhour.com/blog/free-cloud-gpus-and-credits", "Free Cloud GPUs in 2026", "Kaggle", 3, "2026-10-04")],
      "single-source", ["A-009", "D-016", "R-008"], ["subject:kaggle", "tech:kaggle"], pubs=2)
claim("C-020", "RVC v2 content features: hubert_base final (12th) encoder layer on 16 kHz input, 320-sample hop (50 fps), repeated x2 to the 100 fps f0 frame rate (window 160 at 16 kHz).",
      "software", True, [spike(UF, "PASS C-020a/b/c")], "verified", ["D-012", "T-039"], ["subject:rvc", "tech:rvc"], "RVC 81eed5e")
claim("C-021", "RVC coarse pitch = rint(clip((1127 ln(1+f/700) - mel_min) * 254 / (mel_max - mel_min) + 1, 1, 255)) with f0_min 50 Hz, f0_max 1100 Hz (numpy rint: half to even).",
      "numerical", True, [spike(UF, "PASS C-021a/b"), S("research/spikes/oracle/oracle.py", "oracle rvc_coarse", "function rvc_coarse", 1)], "verified", ["T-025", "D-012"], ["subject:rvc", "tech:rvc"], "RVC 81eed5e")
claim("C-022", "RVC training runs train/preprocess.py (inp_root sr n_p exp_dir noparallel per [manifest]), train/dataset/extract_f0.py, train/dataset/extract_hubert_feature.py, train/train.py (-e -sr -f0 -bs [-g] -te -se -pg -pd -l -c -sw -v) and train/train_index.py.",
      "software", True, [spike(UF, "PASS C-022a/b/c")], "verified", ["D-016", "S-014"], ["subject:rvc", "tech:rvc", "domain:ml-training"], "RVC 81eed5e")
claim("C-023", "RVC's py3.12 requirement files pin torch 2.4.1+cpu / 2.7.1+cu128, numpy <2, transformers <4.50 and onnxruntime-gpu <1.20, and default to Chinese mirror indexes whose official equivalents are pypi.org and download.pytorch.org.",
      "software", True, [spike(UF, "PASS C-023a/b/c")], "verified", ["D-019"], ["subject:rvc", "tech:rvc", "tech:pytorch"], "RVC 81eed5e")
claim("C-024", "The RVC repository contains RVCRealtimeVST, a Windows-only iPlug2 VST2/VST3 that runs RVC in a separate Python worker (prior art, not reused).",
      "software", False, [spike(UF, "PASS C-024")], "verified", ["D-020"], ["subject:rvc", "tech:vst3"], "RVC 81eed5e")
claim("C-026", "Some Windows installations carry C:\\Windows\\System32\\onnxruntime.dll (placed by Windows), and programs that load onnxruntime.dll by name can bind to it instead of their own copy; ONNX Runtime collaborators advise loading by explicit path and resolving OrtGetApiBase.",
      "software", True, [S("https://github.com/microsoft/onnxruntime/issues/11799", "onnxruntime issue 11799", "maintainer: 'By Windows team'", 2),
                         S("https://github.com/microsoft/onnxruntime/discussions/23239", "onnxruntime discussion 23239", "fdwr 2025-02-27", 2),
                         S("https://github.com/k2-fsa/sherpa-onnx/issues/3059", "sherpa-onnx issue 3059", "API version [23] not available, 1.17.1 loaded", 2),
                         S("https://learn.microsoft.com/en-us/windows/win32/dlls/dynamic-link-library-search-order", "Dynamic-link library search order", "standard search order", 1)],
      "corroborated", ["D-024", "T-041"], ["subject:windows-dll-loading", "tech:onnxruntime"], pubs=3)
claim("C-027", "pyworld 0.3.5 on Python 3.12 / numpy 1.26.4 imports pkg_resources (needs setuptools < 81). Its harvest+stonemask leave a pure 220 Hz sine fully unvoiced (0/161 interior frames, default or 50-1100 Hz range) but track a 15-partial harmonic 220 Hz tone exactly (161/161 voiced, 0.098 cents RMS); F0 known-answer tests must use a harmonic tone.",
      "software", True, [S("research/spikes/pyworld/output.txt", "spike pyworld", "all '==' lines", 1, "2026-10-14")], "verified", ["T-P10", "D-017", "PK-31"], ["subject:pyworld", "tech:python"], "pyworld 0.3.5")
claim("C-028", "Resemblyzer 0.1.4 bundles its speaker-encoder weights (resemblyzer/pretrained.pt, 17,090,379 bytes) in the wheel and depends on torch, librosa and webrtcvad.",
      "software", True, [spike("pyfacts", "resemblyzer wheel listing")], "verified", ["D-017"], ["subject:resemblyzer", "tech:python"], "resemblyzer 0.1.4")
claim("C-029", "RVC filelist f0 line format is gt_wav|feature768|2a_f0|2b-f0nsf|speaker, plus 2 mute lines per speaker.",
      "software", True, [spike(UF, "PASS C-029")], "verified", ["D-016"], ["subject:rvc", "tech:rvc"], "RVC 81eed5e")
claim("C-030", "For RVC v2 at 48k the config copied to logs/<exp>/config.json is configs/v2/48k.json.",
      "software", True, [spike(UF, "PASS C-030")], "verified", ["D-016"], ["subject:rvc", "tech:rvc"], "RVC 81eed5e")
claim("C-031", "RVC's pretrained base models are trained on VCTK (README).", "policy", False, [spike(UF, "PASS C-031")], "verified", ["D-026"], ["subject:rvc", "tech:rvc"], "RVC 81eed5e")
claim("C-032", "RVC model assets come from Hugging Face lj1995/VoiceConversionWebUI (hubert_base, rmvpe.pt, pretrained_v2, mute.zip).",
      "software", True, [spike(UF, "PASS C-032")], "verified", ["D-016", "R-002"], ["subject:rvc", "tech:rvc"], "RVC 81eed5e")
claim("C-033", "DiffSinger phoneme vocabularies: the exporter writes <name>.phonemes.json (phone -> id); OpenUtau loads .json as a map, otherwise .txt where the token id is the line index.",
      "software", True, [spike(UF, "PASS C-033")], "verified", ["D-012", "D-008"], ["subject:diffsinger", "tech:diffsinger", "subject:openutau"], "DiffSinger ba031f6 / OpenUtau a06ab28")
claim("C-034", "Continuous-acceleration acoustic models take steps int64[1] and, with variable depth, depth float[1]; legacy models take speedup int64 and, with shallow diffusion, depth int64 (OpenUtau: depth64 = round(min(depth, max_depth/1000) * 1000), speedup = max(1, depth64 / steps), depth64 = depth64 / speedup * speedup; without shallow diffusion speedup = largest divisor of 1000 <= 1000/steps).",
      "software", True, [spike(UF, "PASS C-034"), S(GH + "openutau/OpenUtau/blob/a06ab28b0ae011bd0b85926f3044572be46a7a63/OpenUtau.Core/DiffSinger/DiffSingerRenderer.cs", "DiffSingerRenderer.cs", "lines 288-313", 1),
                         spike("tiger-guide", "rank0/rank1 scalars accepted; render")], "verified", ["D-012", "T-043"], ["subject:diffsinger", "tech:diffsinger", "subject:openutau"], "OpenUtau a06ab28")
claim("C-035", "Language ids: a phoneme 'lang/ph' prefix selects the languages.json id; unprefixed phonemes get id 0.",
      "software", False, [spike(UF, "PASS C-035")], "verified", ["D-012"], ["subject:diffsinger", "tech:diffsinger"], "OpenUtau a06ab28")
claim("C-036", "TIGER DiffSinger v102 (GitHub release v102, TIGER_DS_v102_PACK.zip, sha256 925ca2ad...) is an English DiffSinger voicebank whose acoustic model takes tokens, durations, f0, gender, velocity, spk_embed[1,T,256], depth int64 and speedup int64; it bundles its own vocoder (tgm_hifigan.onnx, 44100 Hz, hop 512, 128 mel bins), 7 speaker embeddings (raw float32, 256 values), and a 68-entry phonemes.txt that contains all 39 CMUdict ARPAbet phones.",
      "software", True, [spike("tiger-guide", "phoneme count; inputs; vocoder.yaml")], "verified", ["G-005", "D-012", "D-008"], ["subject:tiger-diffsinger", "tech:diffsinger"], "TIGER v102")
claim("C-037", "TIGER licence: the repository LICENSE.md is CC BY-NC-ND 4.0 plus a Commons Clause (no commercial use, no redistribution, no derivatives); the pack's extra/LICENSE.md is an MIT-style text that allows modification but forbids commercial use and harmful uses; the character TOS allows using the voice to represent another character with credit. Personal non-commercial use is free under both.",
      "policy", True, [S("https://github.com/spicytigermeat/tiger_diffsinger/blob/988ec2c2dd23b7b28c448e1a6db710bfa20c5583/LICENSE.md", "TIGER LICENSE.md", "file", 1),
                       S("https://github.com/spicytigermeat/tiger_diffsinger/blob/988ec2c2dd23b7b28c448e1a6db710bfa20c5583/character_usage_tos.md", "character_usage_tos.md", "allowed list", 1),
                       spike("tiger-guide", "pack extra/LICENSE.md (read 2026-10-10)")], "verified", ["D-026", "A-013", "G-005"], ["subject:tiger-diffsinger", "tech:diffsinger"], "TIGER v102",
      contra=["The two licence texts disagree on modification; the stricter (ND) one governs this plan."])
claim("C-038", "OpenUtau pads every DiffSinger phrase with 8 'SP' frames at the head and tail, feeds gender = 0 and velocity = 1 when no curve is set, and builds spk_embed per frame from the selected speaker's embedding.",
      "software", True, [S(GH + "openutau/OpenUtau/blob/a06ab28b0ae011bd0b85926f3044572be46a7a63/OpenUtau.Core/DiffSinger/DiffSingerUtils.cs", "DiffSingerUtils.cs", "lines 15-83", 1),
                         spike("tiger-guide", "frames 188 (incl. 8+8 pad), waveform 188.0 frames")], "verified", ["D-012", "T-043", "T-044"], ["subject:openutau", "subject:diffsinger", "tech:diffsinger"], "OpenUtau a06ab28")
claim("C-039", "Measured: TIGER acoustic (depth 400, speedup 20) + tgm_hifigan render 2.00 s of audio in 2.18 s on the 2-core planning sandbox with ORT 1.31.0 (guide RTF 1.10); load time 0.88 s; unclipped peak 0.540.",
      "numerical", False, [spike("tiger-guide", "acoustic/vocoder timing line")], "verified", ["D-017", "A-012"], ["subject:tiger-diffsinger", "tech:onnxruntime"], "TIGER v102; ORT 1.31.0")
claim("C-040", "TIGER's acoustic graph contains 2 RandomNormalLike nodes without a seed attribute; two identical runs differ (max |mel1-mel2| = 1.86); the ONNX Runtime 1.31.0 C/C++ API exposes no seed function (only Python has onnxruntime.set_seed).",
      "software", True, [spike("tiger-guide", "acoustic determinism line; ORT seed grep line")], "verified", ["D-012", "D-017", "R-005"], ["subject:tiger-diffsinger", "tech:onnxruntime"], "TIGER v102; ORT 1.31.0")
claim("C-041", "TIGER's acoustic model accepts the depth and speedup scalars at rank 0 and at rank 1.",
      "software", False, [spike("tiger-guide", "rank0/rank1 lines")], "verified", ["D-012"], ["subject:tiger-diffsinger", "tech:onnxruntime"], "TIGER v102; ORT 1.31.0")
claim("C-042", "With ORT_API_MANUAL_INIT, a program that does not link onnxruntime can load libonnxruntime.so.1.31.0 by explicit path, resolve OrtGetApiBase, get API version 31, call Ort::InitApi and run a model; the Windows equivalent (LoadLibraryExW + GetProcAddress) is not yet run.",
      "software", True, [spike("ort-manual-init", "output.txt")], "verified", ["D-024", "T-041"], ["subject:onnxruntime", "tech:onnxruntime", "tech:cpp"], "onnxruntime 1.31.0 (Linux)")
claim("C-043", "audio-separator 0.47.0 (MIT, Python >= 3.10) lists the de-reverb model dereverb_mel_band_roformer_anvuew_sdr_19.1729.ckpt ('MelBand Roformer | De-Reverb by anvuew', stems noreverb/reverb, target noreverb) and downloads model files from GitHub releases; the model's own licence is not stated.",
      "software", True, [spike("pyfacts", "audio-separator wheel inspection")], "verified", ["D-025", "R-009"], ["subject:audio-separator", "tech:python", "domain:audio"], "audio-separator 0.47.0")
claim("C-044", "From the planning sandbox (probed 2026-10-14): pypi.org (index and wheel downloads), GitHub web, git, raw, releases and the REST API for attached repositories are reachable; huggingface.co, download.pytorch.org, colab.research.google.com, kaggle.com and the Actions results host are not.",
      "software", True, [S("research/spikes/hosts/output.txt", "spike hosts", "all lines", 1, "2026-10-14"), spike("pyworld", "pip install lines (wheel downloads)")], "verified", ["D-018", "PK-13", "plan/ENVIRONMENT.md"], ["subject:sandbox-environment", "tech:github"], "sandbox 2026-10-14")
claim("C-045", "Current major tags: actions/checkout v7, actions/setup-python v7, actions/upload-artifact v7, actions/download-artifact v8; Catch2 latest v3.16.1.",
      "software", True, [spike(UF, "upstream tips (drift check)")], "verified", ["D-018", "plan/ENVIRONMENT.md"], ["subject:github-actions", "tech:github-actions"], "2026-10-10")
claim("C-046", "setuptools < 83 carries PYSEC-2026-3447 (fixed in 83.0.0) and setuptools >= 81 no longer ships pkg_resources, so with setuptools 84.0.0 'import pyworld' (0.3.5) fails with ModuleNotFoundError; loading the compiled extension pyworld.pyworld directly works and tracks a 15-partial 220 Hz harmonic tone on 161/161 interior frames at 0.0976 cents RMS (A4 = 440 Hz).",
      "software", True, [S("research/spikes/pyworld-direct/output.txt", "spike pyworld-direct", "all '==' lines", 1, "2026-10-14"),
                         S("research/spikes/pip-audit-setuptools/output.txt", "spike pip-audit-setuptools", "PYSEC-2026-3447 rows", 1, "2026-10-14")],
      "verified", ["D-019", "D-017", "T-P10", "PK-41"], ["subject:pyworld", "tech:python"], "pyworld 0.3.5 / setuptools 84.0.0", kstamp="20261014T195000Z")
claim("C-047", "RVC 81eed5e train/train.py resumes automatically: it loads the newest D_*.pth and G_*.pth in logs/<exp> (sorted by the digits in the name) and falls back to the pretrained models only when none load; checkpoints are written every save_every_epoch epochs, as G_/D_2333333.pth when if_latest (-l 1) is set.",
      "software", True, [S("research/spikes/rvc-resume/output.txt", "spike rvc-resume", "resume and checkpoint lines", 1, "2026-10-14")],
      "verified", ["D-016", "S-014", "T-P05"], ["subject:rvc", "tech:rvc", "domain:ml-training"], "RVC 81eed5e", kstamp="20261014T201000Z")
claim("C-048", "RVC 81eed5e writes inference weights with savee() to assets/weights/<name>.pth (relative to the RVC working directory): weights stored as float16, keys config (synthesiser constructor list; 48k upsample rates 10,6,2,2,2 = 480 samples per 100 fps frame), sr, f0, version; one file per save when -sw 1 and a final file when training completes.",
      "software", True, [S("research/spikes/rvc-resume/output.txt", "spike rvc-resume", "inference weights lines", 1, "2026-10-14")],
      "verified", ["D-012", "D-016", "S-013"], ["subject:rvc", "tech:rvc", "tech:onnx"], "RVC 81eed5e", kstamp="20261014T201001Z")
claim("C-049", "nlohmann/json v3.12.0 (MIT) is published as json.tar.xz (sha256 42f6e95cad6ec532fd372391373363b62a14af6d771056dbfc86160e6dfff7aa); tag commit 55f93686c01528224f448c19128836e7df245f72. pluginval 1.0.4 zips: Linux c01c49d8063965c4c2dea8324468336768f5c9139e0b1caebde14c2400b55352, Windows c08e61ce3b96db41636f8ec7e76f4c7e2c13ebdac7fa1b5a1f52b4f32ec715ab.",
      "software", True, [S("research/spikes/deps-pins/output.txt", "spike deps-pins", "downloads, tag commits", 1, "2026-10-14")],
      "verified", ["D-001", "D-018", "plan/ENVIRONMENT.md"], ["subject:nlohmann-json", "tech:cpp", "tech:cmake"], "json 3.12.0 / pluginval 1.0.4", kstamp="20261014T213000Z")
claim("C-050", "Building the JUCE 9.0.3 plugin on Ubuntu 24.04 needs JUCE's documented Linux packages; without libxi-dev the build fails ('X11/extensions/XInput2.h: No such file or directory'). With JUCE_USE_CURL=0 and JUCE_WEB_BROWSER=0 the list is libasound2-dev libjack-jackd2-dev libfreetype-dev libfontconfig1-dev libx11-dev libxcomposite-dev libxcursor-dev libxext-dev libxinerama-dev libxrandr-dev libxrender-dev libxi-dev libglu1-mesa-dev mesa-common-dev libegl-dev.",
      "software", True, [S("research/spikes/plugin-stub/output.txt", "spike plugin-stub", "packages, build exit", 1, "2026-10-14")],
      "verified", ["D-001", "D-018", "plan/ENVIRONMENT.md"], ["subject:juce", "tech:juce", "tech:cmake"], "JUCE 9.0.3", kstamp="20261014T213001Z")
claim("C-051", "The JUCE 9.0.3 VST3 target's TARGET_FILE_DIR is <bundle>/Contents/x86_64-linux, so a POST_BUILD copy places libonnxruntime.so.1.31.0 and cmudict.dict beside 'Sing VST.so'; pluginval 1.0.4 --strictness-level 5 --skip-gui-tests passes on the silent stub plugin under xvfb (includes its 'vst3 validator' test).",
      "software", True, [S("research/spikes/plugin-stub/output.txt", "spike plugin-stub", "bundle, pluginval lines", 1, "2026-10-14")],
      "verified", ["D-024", "D-023", "T-059"], ["subject:pluginval", "tech:pluginval", "tech:vst3", "tech:juce"], "JUCE 9.0.3 / pluginval 1.0.4", kstamp="20261014T213002Z")

claim("C-052", "RVC 81eed5e's README documents its model downloads as `hf download lj1995/VoiceConversionWebUI --revision main` with `--include \"hubert_base/*\" --local-dir assets` (content encoder), `rmvpe.pt --local-dir assets/rmvpe`, `--include \"pretrained/*\" \"pretrained_v2/*\"` and `mute.zip` unzipped into logs.",
      "software", True, [S("research/spikes/hf-cli/output.txt", "spike hf-cli (RVC README.md lines 170-190)", "README download commands", 1, "2026-10-15")],
      "verified", ["D-016", "D-018", "S-013", "S-016", "R-010"], ["subject:rvc", "tech:rvc", "domain:ml-training"], "RVC 81eed5e", kstamp="20261015T080000Z")
claim("C-053", "huggingface_hub 2.2.0 installs the `hf` CLI; `hf download [OPTIONS] REPO_ID [FILENAMES]...` accepts `--revision`, `--include` and `--local-dir`.",
      "software", True, [S("research/spikes/hf-cli/output.txt", "spike hf-cli", "hf download --help", 1, "2026-10-15")],
      "verified", ["D-018", "S-013", "S-016"], ["subject:huggingface-hub", "tech:python"], "huggingface_hub 2.2.0", kstamp="20261015T080001Z")
claim("C-054", "transformers 4.49.0 (RVC 81eed5e pins >=4.49.0,<4.50) requires huggingface-hub <1.0,>=0.26.0, so the hf 2.2.0 CLI must be installed in a separate venv from RVC's environment.",
      "software", True, [S("research/spikes/hf-cli/output.txt", "spike hf-cli (PyPI JSON for transformers 4.49.0)", "requires_dist", 1, "2026-10-15")],
      "verified", ["D-018", "S-016"], ["subject:huggingface-hub", "tech:python", "tech:rvc"], "transformers 4.49.0", kstamp="20261015T080002Z")

claim("C-055", "With the Unix Makefiles generator, `cmake --build <dir> --parallel` without a number runs `make -j` (no job limit) while `--parallel 4` runs `make -j4`; an unbounded JUCE plugin build was terminated on the ubuntu-24.04 runner (exit 143, CI run 38699430452) while Windows (MSBuild) built.",
      "software", True, [S("research/spikes/cmake-parallel/output.txt", "spike cmake-parallel (CMake 3.28.3)", "MAKE ARGS lines", 1, "2026-10-15")],
      "verified", ["D-018", "S-001"], ["subject:cmake", "tech:cmake", "tech:github-actions"], "CMake 3.28", kstamp="20261015T090000Z")

claim("C-056", "Ubuntu 24.04 images ship only the C, C.utf8 and POSIX locales; after `localedef -i de_DE -f UTF-8 de_DE.UTF-8` (root) or `sudo locale-gen de_DE.UTF-8`, setlocale(LC_ALL, \"de_DE.UTF-8\") succeeds with decimal point ',' — which T-034 requires.",
      "software", True, [S("research/spikes/locale-de/output.txt", "spike locale-de", "before/after lines", 1, "2026-10-15")],
      "verified", ["D-018", "S-000", "T-034"], ["subject:posix-locale", "tech:cpp", "tech:github-actions"], "Ubuntu 24.04 glibc 2.39", kstamp="20261015T221000Z")
claim("C-057", "RVC 81eed5e: `extract_f0.py cuda <n_part> <i_part> <i_gpu> <exp_dir> <is_half>` always uses rmvpe; `extract_hubert_feature.py <device> <n_part> <i_part> <i_gpu> <exp_dir> <version> <is_half>` (8 args) or without i_gpu (7 args); `preprocess.py <inp_root> <sr> <n_p> <exp_dir> <noparallel> <per> [manifest]`; its cu128 requirements pin no pyworld or mido.",
      "software", True, [S("research/spikes/eval-apis/output.txt", "spike eval-apis (sys.argv lines, requirements grep)", "RVC section", 1, "2026-10-15")],
      "verified", ["D-035", "S-016"], ["subject:rvc", "tech:rvc", "domain:ml-training"], "RVC 81eed5e", kstamp="20261015T221001Z")
claim("C-058", "Resemblyzer 0.1.4 `preprocess_wav(fpath_or_wav, source_sr=None)` loads a str/Path with librosa at its own rate and resamples to 16 kHz; a numpy array is resampled only when `source_sr` is given (otherwise assumed 16 kHz); `VoiceEncoder.embed_utterance(wav)` embeds the preprocessed waveform.",
      "software", True, [S("research/spikes/eval-apis/output.txt", "spike eval-apis (resemblyzer/audio.py, voice_encoder.py)", "resemblyzer section", 1, "2026-10-15")],
      "verified", ["D-017", "S-015"], ["subject:resemblyzer", "tech:python"], "resemblyzer 0.1.4", kstamp="20261015T221002Z")
claim("C-059", "openai-whisper 20250625: `whisper.load_model(name)`; `model.transcribe(audio, temperature=..., language=...)` where temperature defaults to the fallback tuple (0.0, 0.2, …, 1.0) and a file path is decoded by `load_audio` (ffmpeg) at 16 kHz.",
      "software", True, [S("research/spikes/eval-apis/output.txt", "spike eval-apis (whisper/__init__.py, transcribe.py, audio.py)", "whisper section", 1, "2026-10-15")],
      "verified", ["D-017", "S-015"], ["subject:openai-whisper", "tech:python"], "openai-whisper 20250625", kstamp="20261015T221003Z")

claim("C-060", "uv 0.13.1 (`pip install uv==0.13.1`) creates a Python 3.12 venv with `uv venv --python 3.12 --python-preference only-managed`, downloading its own CPython (3.12.15) regardless of the host Python, and installs wheels into it with `uv pip install --python <venv>/bin/python`.",
      "software", True, [S("research/spikes/uv-python/output.txt", "spike uv-python (host Python 3.13)", "all lines", 1, "2026-10-15")],
      "verified", ["D-035", "S-016"], ["subject:uv", "tech:python"], "uv 0.13.1", kstamp="20261015T222000Z")

cl = ROOT / "research" / "claims.json"
cl.write_text(json.dumps([{k: v for k, v in c.items() if k not in ("tags", "applies_to_version", "kstamp")} for c in C], indent=1) + "\n")
# Consistency rules on labels (lessons L-20261010T000115Z, L-20261009T123005Z)
bad = [c["id"] for c in C if c["confidence"] == "corroborated" and (c["independent_publishers"] < 2 or not any(s["tier"] == 1 for s in c["sources"]))]
bad += [c["id"] for c in C if c["confidence"] == "verified" and not any(s["url"].startswith("research/spikes/") or s["url"].startswith("plan/") for s in c["sources"])]
# A cited spike or plan file must exist in the tree (lesson L-20261014T142000Z: C-027 was 'verified' against an output file never written)
bad += [f"{c['id']}:{s['url']}" for c in C for s in c["sources"]
        if (s["url"].startswith("research/") or s["url"].startswith("plan/")) and not (ROOT / s["url"]).exists()]
if bad: sys.exit("label rule violated: " + ", ".join(bad))
kd = ROOT / "knowledge"; kd.mkdir(exist_ok=True)
for i, c in enumerate(C):
    if list(kd.glob(f"K-*-{c['id'].lower()}-*.md")):
        continue
    ts = c["kstamp"] or ("20261010T1100" + f"{i:02d}" + "Z")  # kstamp: real UTC time for claims added after 2026-10-10
    subj = next(t for t in c["tags"] if t.startswith("subject:")).split(":")[1]
    kid = f"K-{ts}-{c['id'].lower()}-{subj}"
    s0 = c["sources"][0]
    (kd / f"{kid}.md").write_text(f"""---
id: {kid}
statement: {json.dumps(c['claim'])}
status: current
supersedes: []
tags: [{', '.join(c['tags'] + ['phase:research'])}]
applies_to_version: {json.dumps(c['applies_to_version'])}
source: {json.dumps({k: s0[k] for k in ('url', 'doi', 'title', 'locator', 'accessed', 'tier')})}
confidence: {c['confidence']}
derived_from: [{c['id']}]
discovered_by: planner
run: {RUN}
recorded_at: {ts[:4]}-{ts[4:6]}-{ts[6:8]}T{ts[9:11]}:{ts[11:13]}:{ts[13:15]}Z
---
Derived mechanically from research/claims.json {c['id']} ({c['kind']}, load-bearing: {c['load_bearing']}, independent publishers: {c['independent_publishers']}).
Sources: {'; '.join(s['title'] + ' <' + s['url'] + '> [' + s['locator'] + ']' for s in c['sources'])}.
""", encoding="utf-8")
print(len(C), "claims;", len(list(kd.glob("K-*.md"))), "knowledge items")
