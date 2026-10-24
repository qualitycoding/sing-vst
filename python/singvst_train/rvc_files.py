"""RVC 81eed5e training inputs and commands (C-022, C-029, C-030, C-047). Stubs until plan step S-014."""
from __future__ import annotations

import random
import re
import shutil
from pathlib import Path


def write_filelist(exp_dir: Path, rvc_root: Path, speaker_id: int = 0, sr_tag: str = "48k", seed: int = 0) -> Path:
    """Write ``exp_dir/filelist.txt`` in RVC's f0 format (C-029): one line per stem present in all four of
    ``0_gt_wavs/<stem>.wav``, ``3_feature768/<stem>.npy``, ``2a_f0/<stem>.wav.npy``, ``2b-f0nsf/<stem>.wav.npy`` —
    ``gt|feature|f0|f0nsf|speaker_id`` with absolute POSIX paths — plus two mute lines pointing at
    ``rvc_root/logs/mute/`` files for ``sr_tag`` (``0_gt_wavs/mute<sr_tag>.wav``, ``3_feature768/mute.npy``,
    ``2a_f0/mute.wav.npy``, ``2b-f0nsf/mute.wav.npy``). The list (stem lines in sorted stem order, then the two mute
    lines) is shuffled in place with ``random.Random(seed).shuffle`` and written with ``\\n`` after every line.
    No complete stem → ``ValueError``. Returns the path."""
    exp_dir = Path(exp_dir)
    stems = []
    for wav in sorted((exp_dir / "0_gt_wavs").glob("*.wav")):
        stem = wav.name[: -len(".wav")]
        if (exp_dir / "3_feature768" / f"{stem}.npy").is_file() and (exp_dir / "2a_f0" / f"{stem}.wav.npy").is_file() \
                and (exp_dir / "2b-f0nsf" / f"{stem}.wav.npy").is_file():
            stems.append(stem)
    if not stems:
        raise ValueError(f"no complete stem (wav, feature, f0, f0nsf) in {exp_dir}")
    root = exp_dir.resolve().as_posix()
    lines = [f"{root}/0_gt_wavs/{s}.wav|{root}/3_feature768/{s}.npy|{root}/2a_f0/{s}.wav.npy|{root}/2b-f0nsf/{s}.wav.npy|{speaker_id}"
             for s in stems]
    mute = (Path(rvc_root) / "logs" / "mute").resolve().as_posix()
    mute_line = (f"{mute}/0_gt_wavs/mute{sr_tag}.wav|{mute}/3_feature768/mute.npy|{mute}/2a_f0/mute.wav.npy|"
                 f"{mute}/2b-f0nsf/mute.wav.npy|{speaker_id}")
    lines += [mute_line, mute_line]
    random.Random(seed).shuffle(lines)
    path = exp_dir / "filelist.txt"
    path.write_text("".join(line + "\n" for line in lines), encoding="utf-8", newline="")
    return path


def copy_config(exp_dir: Path, rvc_root: Path, sr_tag: str = "48k") -> Path:
    """Copy ``rvc_root/configs/v2/<sr_tag>.json`` to ``exp_dir/config.json`` (C-030); ``sr_tag`` must be "48k" or
    "32k" (``ValueError``). Returns the destination."""
    if sr_tag not in ("48k", "32k"):
        raise ValueError(f"sr_tag must be '48k' or '32k', got {sr_tag!r}")
    destination = Path(exp_dir) / "config.json"
    shutil.copyfile(Path(rvc_root) / "configs" / "v2" / f"{sr_tag}.json", destination)
    return destination


def train_command(python: str, exp_name: str, sr_tag: str = "48k", batch_size: int = 8, total_epochs: int = 200,
                  save_every: int = 10, gpus: str = "0") -> list[str]:
    """argv for ``train/train.py`` (C-022, C-047): ``[python, "train/train.py", "-e", exp_name, "-sr", sr_tag, "-f0",
    "1", "-bs", str(batch_size), "-g", gpus, "-te", str(total_epochs), "-se", str(save_every), "-pg",
    "assets/pretrained_v2/f0G<sr_tag>.pth", "-pd", "assets/pretrained_v2/f0D<sr_tag>.pth", "-l", "1", "-c", "0", "-sw",
    "1", "-v", "v2"]``. ``save_every`` must divide ``total_epochs`` and both be positive (``ValueError``)."""
    if total_epochs <= 0 or save_every <= 0 or total_epochs % save_every != 0:
        raise ValueError(f"save_every ({save_every}) must be positive and divide total_epochs ({total_epochs})")
    return [python, "train/train.py", "-e", exp_name, "-sr", sr_tag, "-f0", "1", "-bs", str(batch_size), "-g", gpus,
            "-te", str(total_epochs), "-se", str(save_every), "-pg", f"assets/pretrained_v2/f0G{sr_tag}.pth",
            "-pd", f"assets/pretrained_v2/f0D{sr_tag}.pth", "-l", "1", "-c", "0", "-sw", "1", "-v", "v2"]


def latest_weights(rvc_root: Path, exp_name: str) -> Path:
    """The inference weights to export (C-048): ``rvc_root/assets/weights/<exp_name>.pth`` if it exists, else the
    newest ``<exp_name>_e<epoch>_s<step>.pth`` by epoch number. None → ``FileNotFoundError``."""
    weights = Path(rvc_root) / "assets" / "weights"
    final = weights / f"{exp_name}.pth"
    if final.is_file():
        return final
    pattern = re.compile(rf"^{re.escape(exp_name)}_e(\d+)_s\d+\.pth$")
    found = [(int(m.group(1)), f) for f in weights.glob("*.pth") if (m := pattern.match(f.name))] if weights.is_dir() else []
    if not found:
        raise FileNotFoundError(f"no inference weights for {exp_name!r} in {weights}")
    return max(found, key=lambda item: item[0])[1]
