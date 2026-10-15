"""RVC 81eed5e training inputs and commands (C-022, C-029, C-030, C-047). Stubs until plan step S-014."""
from __future__ import annotations

from pathlib import Path


def write_filelist(exp_dir: Path, rvc_root: Path, speaker_id: int = 0, sr_tag: str = "48k", seed: int = 0) -> Path:
    """Write ``exp_dir/filelist.txt`` in RVC's f0 format (C-029): one line per stem present in all four of
    ``0_gt_wavs/<stem>.wav``, ``3_feature768/<stem>.npy``, ``2a_f0/<stem>.wav.npy``, ``2b-f0nsf/<stem>.wav.npy`` —
    ``gt|feature|f0|f0nsf|speaker_id`` with absolute POSIX paths — plus two mute lines pointing at
    ``rvc_root/logs/mute/`` files for ``sr_tag`` (``0_gt_wavs/mute<sr_tag>.wav``, ``3_feature768/mute.npy``,
    ``2a_f0/mute.wav.npy``, ``2b-f0nsf/mute.wav.npy``). Lines are shuffled with ``random.Random(seed)``; ``\\n`` endings.
    No complete stem → ``ValueError``. Returns the path."""
    raise NotImplementedError("write_filelist")


def copy_config(exp_dir: Path, rvc_root: Path, sr_tag: str = "48k") -> Path:
    """Copy ``rvc_root/configs/v2/<sr_tag>.json`` to ``exp_dir/config.json`` (C-030); ``sr_tag`` must be "48k" or
    "32k" (``ValueError``). Returns the destination."""
    raise NotImplementedError("copy_config")


def train_command(python: str, exp_name: str, sr_tag: str = "48k", batch_size: int = 8, total_epochs: int = 200,
                  save_every: int = 10, gpus: str = "0") -> list[str]:
    """argv for ``train/train.py`` (C-022, C-047): ``[python, "train/train.py", "-e", exp_name, "-sr", sr_tag, "-f0",
    "1", "-bs", str(batch_size), "-g", gpus, "-te", str(total_epochs), "-se", str(save_every), "-pg",
    "assets/pretrained_v2/f0G<sr_tag>.pth", "-pd", "assets/pretrained_v2/f0D<sr_tag>.pth", "-l", "1", "-c", "0", "-sw",
    "1", "-v", "v2"]``. ``save_every`` must divide ``total_epochs`` and both be positive (``ValueError``)."""
    raise NotImplementedError("train_command")


def latest_weights(rvc_root: Path, exp_name: str) -> Path:
    """The inference weights to export (C-048): ``rvc_root/assets/weights/<exp_name>.pth`` if it exists, else the
    newest ``<exp_name>_e<epoch>_s<step>.pth`` by epoch number. None → ``FileNotFoundError``."""
    raise NotImplementedError("latest_weights")
