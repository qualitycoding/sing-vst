# FROZEN — DO NOT MODIFY (plan/PLAN.md, tests/FROZEN_MANIFEST.sha256). Requirement, decision and claim IDs are cited per test.
import json
import random

import pytest

from singvst_train import rvc_files


def _exp(tmp_path, stems, incomplete=()):
    exp = tmp_path / "logs" / "me"
    for sub, suffix in (("0_gt_wavs", ".wav"), ("3_feature768", ".npy"), ("2a_f0", ".wav.npy"), ("2b-f0nsf", ".wav.npy")):
        (exp / sub).mkdir(parents=True, exist_ok=True)
        for s in stems:
            (exp / sub / f"{s}{suffix}").write_bytes(b"")
    for s in incomplete:
        (exp / "0_gt_wavs" / f"{s}.wav").write_bytes(b"")
    return exp


def test_P24_filelist_config_command_and_weights(tmp_path):
    """T-P24 (C-022, C-029, C-030, C-047, C-048): RVC 81eed5e training inputs."""
    rvc = tmp_path / "rvc"
    exp = _exp(tmp_path, ["0_0", "0_1", "1_0"], incomplete=["9_9"])
    path = rvc_files.write_filelist(exp, rvc, speaker_id=0, sr_tag="48k", seed=3)
    lines = path.read_text(encoding="utf-8").split("\n")
    assert lines[-1] == "" and len(lines) == 6                      # 3 stems + 2 mute lines, trailing newline
    body = lines[:-1]
    e, m = exp.resolve().as_posix(), (rvc / "logs" / "mute").resolve().as_posix()
    expected = [f"{e}/0_gt_wavs/{s}.wav|{e}/3_feature768/{s}.npy|{e}/2a_f0/{s}.wav.npy|{e}/2b-f0nsf/{s}.wav.npy|0"
                for s in ("0_0", "0_1", "1_0")]
    expected += [f"{m}/0_gt_wavs/mute48k.wav|{m}/3_feature768/mute.npy|{m}/2a_f0/mute.wav.npy|{m}/2b-f0nsf/mute.wav.npy|0"] * 2
    shuffled = list(expected)
    random.Random(3).shuffle(shuffled)
    assert body == shuffled
    with pytest.raises(ValueError):
        rvc_files.write_filelist(_exp(tmp_path / "empty", []), rvc)
    (rvc / "configs" / "v2").mkdir(parents=True)
    (rvc / "configs" / "v2" / "48k.json").write_text(json.dumps({"train": {"epochs": 1}}))
    cfg = rvc_files.copy_config(exp, rvc, "48k")
    assert cfg == exp / "config.json" and json.loads(cfg.read_text()) == {"train": {"epochs": 1}}
    with pytest.raises(ValueError):
        rvc_files.copy_config(exp, rvc, "40k")
    assert rvc_files.train_command("py", "me", "48k", 8, 200, 10, "0") == [
        "py", "train/train.py", "-e", "me", "-sr", "48k", "-f0", "1", "-bs", "8", "-g", "0", "-te", "200", "-se", "10",
        "-pg", "assets/pretrained_v2/f0G48k.pth", "-pd", "assets/pretrained_v2/f0D48k.pth", "-l", "1", "-c", "0", "-sw", "1",
        "-v", "v2"]
    with pytest.raises(ValueError):
        rvc_files.train_command("py", "me", save_every=7, total_epochs=200)
    w = rvc / "assets" / "weights"
    w.mkdir(parents=True)
    with pytest.raises(FileNotFoundError):
        rvc_files.latest_weights(rvc, "me")
    for n in ("me_e5_s50.pth", "me_e20_s200.pth", "me_e10_s100.pth", "other_e90_s9.pth"):
        (w / n).write_bytes(b"")
    assert rvc_files.latest_weights(rvc, "me") == w / "me_e20_s200.pth"
    (w / "me.pth").write_bytes(b"")
    assert rvc_files.latest_weights(rvc, "me") == w / "me.pth"
