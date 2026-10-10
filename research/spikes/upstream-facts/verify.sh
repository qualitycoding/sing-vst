#!/usr/bin/env bash
# Spike R6 (round 2): clones each pinned upstream ref and asserts the code-level facts that claims C-### rest on.
# Usage: bash verify.sh <empty scratch dir>   — prints PASS/FAIL per fact; exit 1 if any FAIL.
set -uo pipefail
W=${1:?scratch dir}; mkdir -p "$W"; cd "$W"
fail=0
check() { local id="$1" desc="$2"; shift 2; if "$@" >/dev/null 2>&1; then echo "PASS $id $desc"; else echo "FAIL $id $desc"; fail=1; fi; }
clone_at() { # dir url ref
  [ -d "$1/.git" ] && return 0
  git init -q "$1" && git -C "$1" remote add origin "$2" && git -C "$1" fetch -q --depth 1 origin "$3" && git -C "$1" checkout -q FETCH_HEAD
}
clone_at rvc https://github.com/RVC-Project/Retrieval-based-Voice-Conversion-WebUI.git 81eed5e8f68b6bed1789f682fe78cdd324495afc
clone_at ds https://github.com/openvpi/DiffSinger.git ba031f6f2f969373b49a926cf8b007e9ae48834f
clone_at ou https://github.com/openutau/OpenUtau.git a06ab28b0ae011bd0b85926f3044572be46a7a63
clone_at juce https://github.com/juce-framework/JUCE.git refs/tags/9.0.3
clone_at cmu https://github.com/cmusphinx/cmudict.git 74790861f652b15e4ac49015a90074ad62a27690
clone_at svc https://github.com/svc-develop-team/so-vits-svc.git HEAD
clone_at voc https://github.com/openvpi/vocoders.git HEAD
clone_at pv https://github.com/Tracktion/pluginval.git refs/tags/v1.0.4
echo "== pinned heads"; for d in rvc ds ou juce cmu svc voc pv; do echo "$d $(git -C $d rev-parse HEAD)"; done
echo "== upstream tips (drift check)"
git ls-remote https://github.com/RVC-Project/Retrieval-based-Voice-Conversion-WebUI.git HEAD
git ls-remote --tags https://github.com/juce-framework/JUCE.git | grep -oE 'refs/tags/9\.[0-9.]+$' | sort -V | tail -2
git ls-remote --tags https://github.com/microsoft/onnxruntime.git | grep -oE 'refs/tags/v1\.(2[89]|3[0-9])\.[0-9]+$' | sort -V | tail -4
git ls-remote --tags https://github.com/catchorg/Catch2.git | grep -oE 'refs/tags/v3\.[0-9.]+$' | sort -V | tail -1
for a in checkout setup-python upload-artifact download-artifact; do echo "actions/$a $(git ls-remote --tags https://github.com/actions/$a.git | grep -oE 'refs/tags/v[0-9]+$' | sort -V | tail -1)"; done
echo "== facts"
check C-001 "RVC licence is MIT" grep -q '^MIT License' rvc/LICENSE
check C-002a "so-vits-svc licence is AGPL-3.0" grep -q 'GNU AFFERO GENERAL PUBLIC LICENSE' svc/LICENSE
check C-003a "RVC v2 synthesiser class exists" grep -q 'class SynthesizerTrnMs768NSFsid(SynthesizerTrnMs256NSFsid)' rvc/infer/module/models.py
check C-003b "RVC infer() signature phone, phone_lengths, pitch, nsff0, sid" bash -c "grep -A8 '    def infer(' rvc/infer/module/models.py | tr -d ' \n' | grep -q 'phone,phone_lengths,pitch,nsff0,sid,'"
check C-003c "RVC infer draws noise internally (randn_like * 0.66666)" grep -q 'torch.randn_like(m_p) \* 0.66666' rvc/infer/module/models.py
check C-004 "RVC tree has no ONNX export module (only infer/rmvpe.py mentions onnx)" bash -c "[ \"\$(cd rvc && grep -rl onnx --include=*.py . | sort | tr '\n' ' ')\" = './infer/rmvpe.py ' ]"
check C-005 "RVC v2 configs are 32k and 48k only" bash -c "[ \"\$(ls rvc/configs/v2 | tr '\n' ' ')\" = '32k.json 48k.json ' ]"
check C-020a "RVC hubert input is 16 kHz" grep -q 'assert sr == 16000' rvc/train/dataset/extract_hubert_feature.py
check C-020b "RVC v2 uses final encoder layer" grep -q 'RVC v2 uses the final (12th) encoder layer' rvc/infer/hubert.py
check C-020c "RVC pipeline frame window 160 at 16 kHz" bash -c "grep -q 'self.sr = 16000' rvc/infer/vc/pipeline.py && grep -q 'self.window = 160' rvc/infer/vc/pipeline.py"
check C-021a "RVC f0 range 50..1100 Hz" bash -c "grep -q 'f0_min = 50' rvc/infer/vc/pipeline.py && grep -q 'f0_max = 1100' rvc/infer/vc/pipeline.py"
check C-021b "RVC coarse pitch formula" bash -c "grep -q 'f0_mel = 1127 \* np.log(1 + f0 / 700)' rvc/infer/vc/pipeline.py && grep -q '254 / (' rvc/infer/vc/pipeline.py && grep -q 'f0_mel\[f0_mel > 255\] = 255' rvc/infer/vc/pipeline.py && grep -q 'np.rint(f0_mel)' rvc/infer/vc/pipeline.py"
check C-022a "RVC training scripts exist" bash -c "cd rvc && ls train/preprocess.py train/dataset/extract_f0.py train/dataset/extract_hubert_feature.py train/train.py train/train_index.py"
check C-022b "RVC train.py flags -e -sr -f0 -bs [-g] -te -se -pg -pd -l -c -sw -v" grep -qF 'train/train.py -e "%s" -sr %s -f0 %s -bs %s -te %s -se %s %s %s -l %s -c %s -sw %s -v %s' rvc/webui.py
check C-022c "RVC preprocess argv: inp_root sr n_p exp_dir noparallel per [manifest]" bash -c "grep -q 'inp_root = sys.argv\[1\]' rvc/train/preprocess.py && grep -q 'per = float(sys.argv\[6\])' rvc/train/preprocess.py"
check C-022d "RVC weights come from huggingface lj1995/VoiceConversionWebUI into assets/" bash -c "grep -q 'huggingface.co/lj1995/VoiceConversionWebUI' rvc/README.md && grep -q 'assets/rmvpe/rmvpe.pt' rvc/README.md && grep -q 'assets/hubert_base/pytorch_model.bin' rvc/README.md"
check C-023a "RVC cpu py312 pins torch 2.4.1+cpu and transformers <4.50" bash -c "grep -q '^torch==2.4.1+cpu' rvc/requirments_cpu_py312.txt && grep -q '^transformers>=4.49.0,<4.50' rvc/requirments_cpu_py312.txt && grep -q '^numpy>=1.26.4,<2' rvc/requirments_cpu_py312.txt"
check C-023b "RVC cu128 file pins torch 2.7.1+cu128 and onnxruntime-gpu <1.20" bash -c "grep -q 'torch==2.7.1+cu128' rvc/requirments_cu128_py312.txt && grep -q '^onnxruntime-gpu>=1.19.2,<1.20' rvc/requirments_cu128_py312.txt"
check C-023c "RVC requirement files default to Chinese mirror indexes" bash -c "grep -q 'mirrors.pku.edu.cn' rvc/requirments_cpu_py312.txt && grep -q 'download.pytorch.org/whl/cu128' rvc/README.md"
check C-024 "RVCRealtimeVST is Windows x64 iPlug2 with a Python worker" bash -c "grep -q 'Windows x64 real-time voice conversion plug-in' rvc/RVCRealtimeVST/README.en.md && grep -q 'separate Python worker' rvc/RVCRealtimeVST/README.en.md"
check C-006a "DiffSinger licence is Apache-2.0" grep -q 'Apache License' ds/LICENSE
check C-006b "DiffSinger deploys via scripts/export.py acoustic|variance|nsf-hifigan" bash -c "grep -q 'python scripts/export.py acoustic' ds/docs/GettingStarted.md && grep -q 'python scripts/export.py nsf-hifigan' ds/docs/GettingStarted.md"
check C-009a "DiffSinger acoustic ONNX inputs tokens, durations, f0 (+variance embeds)" grep -q "input_names = \['tokens', 'durations', 'f0'\]" ds/deployment/exporters/acoustic_exporter.py
check C-009b "DiffSinger acoustic export opset 17 and output mel" bash -c "grep -q 'opset_version=17' ds/deployment/exporters/acoustic_exporter.py && grep -q \"'mel'\" ds/deployment/exporters/acoustic_exporter.py"
check C-009c "NSF-HiFiGAN ONNX inputs mel, f0" bash -c "grep -A3 'input_names=\[' ds/deployment/exporters/nsf_hifigan_exporter.py | tr -d ' \n' | grep -q \"'mel','f0'\""
check C-009d "OpenUtau feeds tokens/durations/f0 to acoustic and mel/f0 to vocoder" bash -c "grep -q 'CreateFromTensor(\"tokens\"' ou/OpenUtau.Core/DiffSinger/DiffSingerRenderer.cs && grep -q 'CreateFromTensor(\"mel\", mel)' ou/OpenUtau.Core/DiffSinger/DiffSingerRenderer.cs"
check C-009e "OpenUtau DsConfig defaults 44100 Hz, hop 512, 128 mel bins" bash -c "grep -q 'public int sample_rate = 44100;' ou/OpenUtau.Core/DiffSinger/DiffSingerConfig.cs && grep -q 'public int hop_size = 512;' ou/OpenUtau.Core/DiffSinger/DiffSingerConfig.cs && grep -q 'public int num_mel_bins = 128;' ou/OpenUtau.Core/DiffSinger/DiffSingerConfig.cs"
check C-007a "openvpi/vocoders code licence is AGPL-3.0" grep -q 'GNU AFFERO GENERAL PUBLIC LICENSE' voc/LICENSE
check C-011a "VST3 interfaces define kTextTypeID and kPhonemeTypeID note expressions" bash -c "f=\$(find juce/modules -name ivstnoteexpression.h | head -1); grep -q 'kTextTypeID' \$f && grep -q 'kPhonemeTypeID' \$f"
check C-011b "JUCE 9.0.3 VST3 wrapper drops kNoteExpressionTextEvent (returns {})" bash -c "grep -A3 'case Steinberg::Vst::Event::kNoteExpressionTextEvent:' juce/modules/juce_audio_processors_headless/format_types/juce_VST3Common.h | grep -q 'return {};'"
check C-012a "JUCE 9.0.3 modules are AGPLv3 / commercial dual-licensed" grep -q 'dual-licensed under the' juce/LICENSE.md
check C-012b "JUCE 9.0.3 needs cmake >= 3.22 and the C language" bash -c "grep -q 'cmake_minimum_required(VERSION 3.22)' juce/CMakeLists.txt && grep -q 'A C compiler is required' juce/CMakeLists.txt"
check C-016a "CMUdict licence is BSD-style (redistribution permitted with notice)" grep -q 'Redistribution and use in source and binary forms' cmu/LICENSE
check C-016b "CMUdict entry and word counts" bash -c "python3 -c \"
import re,collections
d=collections.defaultdict(list); n=0
for l in open('cmu/cmudict.dict',encoding='utf-8'):
    l=l.split('#')[0].strip()
    if not l: continue
    w,*p=l.split(); d[re.sub(r'\(\d+\)$','',w)].append(p); n+=1
assert n==135166 and len(d)==126052, (n,len(d))
\""
check C-015a "pluginval licence is GPL-3.0" grep -q 'GNU GENERAL PUBLIC LICENSE' pv/LICENSE
check C-015b "pluginval 1.0.4 CLI options --strictness-level, --skip-gui-tests, --output-dir, --validate exist" bash -c "for o in strictness-level skip-gui-tests output-dir; do grep -q \"{ \\\"--\$o\\\"\" pv/Source/CommandLine.cpp || exit 1; done; grep -q 'cli.addCommand ({ \\\"--validate\\\"' pv/Source/CommandLine.cpp"
check C-015c "pluginval 1.0.4 has no --validate-in-process option (CLI validates in-process by default)" bash -c "! grep -rq -- 'validate-in-process' pv/Source && grep -q 'ValidationType::inProcess' pv/Source/CommandLine.cpp"
check C-029 "RVC filelist f0 line: gt_wav|feature768|2a_f0|2b-f0nsf|speaker, plus 2 mute lines per speaker" bash -c "grep -qF '\"%s/%s.wav|%s/%s.npy|%s/%s.wav.npy|%s/%s.wav.npy|%s\"' rvc/webui.py && grep -qF 'mute%s.wav|%s/logs/mute/3_feature%s/mute.npy|%s/logs/mute/2a_f0/mute.wav.npy|%s/logs/mute/2b-f0nsf/mute.wav.npy|%s\"' rvc/webui.py && grep -q 'for _ in range(2):' rvc/webui.py"
check C-030 "RVC v2 48k config is copied to logs/<exp>/config.json (v1 or 40k use v1/<sr>.json)" bash -c "grep -q 'config_path = \"v2/%s.json\" % sr2' rvc/webui.py && grep -q 'config_save_path = os.path.join(exp_dir, \"config.json\")' rvc/webui.py"
check C-031 "RVC pretrained base models are trained on VCTK (README)" grep -q 'VCTK open source dataset' rvc/docs/en/README.en.md
check C-032 "RVC model download uses 'hf download lj1995/VoiceConversionWebUI' for hubert_base, rmvpe.pt, pretrained_v2, mute.zip" bash -c "grep -q 'hf download lj1995/VoiceConversionWebUI --revision main' rvc/docs/en/README.en.md && grep -q 'mute.zip' rvc/docs/en/README.en.md && grep -q 'pretrained_v2/\*' rvc/docs/en/README.en.md"
check C-033 "DiffSinger phoneme list: exporter writes <name>.phonemes.json; OpenUtau loads .json as phone->id map, else .txt line index" bash -c "grep -q \"'phonemes': f'{self.model_name}.phonemes.json'\" ds/deployment/exporters/acoustic_exporter.py && grep -q 'case \".json\":' ou/OpenUtau.Core/DiffSinger/DiffSingerUtils.cs && grep -q 'result\[lines\[i\]\] = i;' ou/OpenUtau.Core/DiffSinger/DiffSingerUtils.cs"
check C-034 "Continuous-acceleration acoustic models take depth float[1] (variable depth) and steps int64[1]; exporter sets use_continuous_acceleration True" bash -c "grep -q \"dsconfig\['use_continuous_acceleration'\] = True\" ds/deployment/exporters/acoustic_exporter.py && grep -q 'new DenseTensor<float>(new float\[\] {(float)depth}, new int\[\] { 1 }' ou/OpenUtau.Core/DiffSinger/DiffSingerRenderer.cs && grep -q 'new DenseTensor<long>(new long\[\] { steps }, new int\[\] { 1 }' ou/OpenUtau.Core/DiffSinger/DiffSingerRenderer.cs"
check C-035 "Language ids: phoneme 'lang/ph' prefix selects languages.json id; unprefixed phonemes get 0" bash -c "grep -q 'if(phoneme.Contains(\"/\")){' ou/OpenUtau.Core/DiffSinger/DiffSingerUtils.cs && grep -q 'GetValueOrDefault(' ou/OpenUtau.Core/DiffSinger/DiffSingerRenderer.cs"
echo "== sha256 cmudict.dict $(sha256sum cmu/cmudict.dict | cut -d' ' -f1)"
exit $fail
