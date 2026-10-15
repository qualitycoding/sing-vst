# FROZEN — DO NOT MODIFY (plan/PLAN.md, tests/FROZEN_MANIFEST.sha256). Requirement, decision and claim IDs are cited per test.
import hashlib
import json
import subprocess

import pytest

from conftest import need_env
from singvst_train.pack import pack_voice


def _fixture_files(root):
    fx = root / "tests" / "fixtures" / "onnx"
    guide = {"acoustic": fx / "acoustic_legacy.onnx", "vocoder": fx / "vocoder.onnx", "phonemes": fx / "phonemes.txt",
             "speaker": fx / "speaker.emb"}
    conv = {"synth": fx / "rvc_synth.onnx", "content": fx / "content.onnx"}
    return guide, conv


def test_P13_pack_voice_writes_the_d008_manifest(tmp_path, root):
    """T-P13 (D-008 voice package v1)."""
    guide, conv = _fixture_files(root)
    m = pack_voice(tmp_path / "v", "Me", "my own voice", "test licence", guide, conv, speaker_id=2)
    raw = (tmp_path / "v" / "manifest.json").read_text(encoding="utf-8")
    assert json.loads(raw) == m
    assert list(m) == ["format", "format_version", "name", "consent", "guide_licence", "guide", "converter", "sha256"]
    assert m["guide"] == {"type": "diffsinger", "sample_rate": 44100, "hop_size": 512, "language": "en", "steps": 20,
                          "depth": 0.4, "files": {"acoustic": "guide/acoustic_legacy.onnx", "vocoder": "guide/vocoder.onnx",
                                                  "phonemes": "guide/phonemes.txt", "speaker": "guide/speaker.emb"}}
    assert m["converter"] == {"type": "rvc-v2", "sample_rate": 48000, "speaker_id": 2,
                              "files": {"synth": "conv/rvc_synth.onnx", "content": "conv/content.onnx"}}
    assert set(m["sha256"]) == set(m["guide"]["files"].values()) | set(m["converter"]["files"].values())
    for rel, digest in m["sha256"].items():
        assert hashlib.sha256((tmp_path / "v" / rel).read_bytes()).hexdigest() == digest
    assert pack_voice(tmp_path / "g", "G", "c", "l", {k: guide[k] for k in ("acoustic", "vocoder", "phonemes")},
                      None)["converter"] is None


@pytest.mark.binary
def test_P13b_cpp_parser_accepts_what_pack_voice_writes(tmp_path, root):
    """T-P13 (D-008, D-014): singvst-render --check-voice prints 'ok <name>' for a package written by pack_voice."""
    binary = need_env("SINGVST_RENDER_BIN", "S-009")
    guide, conv = _fixture_files(root)
    pack_voice(tmp_path / "v", "Packed", "my own voice", "test licence", guide, conv)
    r = subprocess.run([binary, "--check-voice", str(tmp_path / "v")], capture_output=True, text=True, timeout=120)
    assert r.returncode == 0, r.stderr
    assert r.stdout.strip() == "ok Packed"


def test_P14_pack_voice_rejects_invalid_input_and_writes_nothing(tmp_path, root):
    """T-P14 (D-008, A-011 consent required, PK-42)."""
    guide, conv = _fixture_files(root)
    bad_cases = [
        dict(consent=""), dict(name=""), dict(guide_licence=""),
        dict(guide_files={k: v for k, v in guide.items() if k != "vocoder"}),
        dict(guide_files=dict(guide, extra=guide["vocoder"])),
        dict(converter_files=dict(conv, other=conv["synth"])),
        dict(steps=0), dict(steps=1001), dict(depth=0.0), dict(depth=1.5),
        dict(converter_sample_rate=22050), dict(speaker_id=-1),
        dict(guide_files=dict(guide, speaker=guide["vocoder"])),          # two files map to guide/vocoder.onnx
    ]
    for i, case in enumerate(bad_cases):
        args = dict(name="Me", consent="own", guide_licence="l", guide_files=guide, converter_files=conv)
        args.update(case)
        out = tmp_path / f"o{i}"
        with pytest.raises(ValueError):
            pack_voice(out, args.pop("name"), args.pop("consent"), args.pop("guide_licence"), args.pop("guide_files"),
                       args.pop("converter_files"), **args)
        assert not out.exists() or not any(out.iterdir()), case
    odd = tmp_path / "bad name.onnx"
    odd.write_bytes(b"x")
    with pytest.raises(ValueError):
        pack_voice(tmp_path / "o-odd", "Me", "own", "l", dict(guide, acoustic=odd), None)
    (tmp_path / "full").mkdir()
    (tmp_path / "full" / "x").write_text("x")
    with pytest.raises(ValueError):
        pack_voice(tmp_path / "full", "Me", "own", "l", guide, None)
