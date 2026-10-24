"""Provenance contract (protocol 2B.2, D-015). Stubs until plan step S-012."""
from __future__ import annotations

import copy
import datetime
import json
import os
import platform
import re
import subprocess
from hashlib import sha256

from pathlib import Path

REQUIRED_KEYS = ("git_commit", "lockfile_sha256", "seeds", "params", "utc_timestamp", "hardware", "threads")


def _cpu_name() -> str:
    try:
        for line in Path("/proc/cpuinfo").read_text(encoding="utf-8", errors="replace").splitlines():
            if line.lower().startswith("model name"):
                return line.split(":", 1)[1].strip()
    except OSError:
        pass
    return platform.processor() or platform.machine() or "unknown"


def _gpu_name() -> str:
    try:
        out = subprocess.run(["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"], capture_output=True, text=True, timeout=30)
        if out.returncode == 0 and out.stdout.strip():
            return out.stdout.strip().splitlines()[0].strip()
    except (OSError, subprocess.SubprocessError):
        pass
    return "none"


def collect(params: dict, seeds: dict, repo_root: Path, lockfile: Path) -> dict:
    """Return a dict with exactly REQUIRED_KEYS.

    ``git_commit``: ``git -C repo_root rev-parse HEAD`` (40 hex), or ``"unknown"`` when that fails. ``lockfile_sha256``:
    SHA-256 hex of ``lockfile`` (missing → ``FileNotFoundError``). ``utc_timestamp``: ISO-8601 with a ``Z`` suffix.
    ``hardware``: ``{"platform", "cpu", "gpu"}`` with ``gpu`` the first line of ``nvidia-smi --query-gpu=name
    --format=csv,noheader`` or ``"none"``. ``threads``: ``os.cpu_count()``. ``params``/``seeds`` are copied."""
    commit = "unknown"
    try:
        out = subprocess.run(["git", "-C", str(repo_root), "rev-parse", "HEAD"], capture_output=True, text=True, timeout=30)
        if out.returncode == 0 and re.fullmatch(r"[0-9a-f]{40}", out.stdout.strip()):
            commit = out.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        pass
    lock_hash = sha256(Path(lockfile).read_bytes()).hexdigest()      # FileNotFoundError when missing
    return {
        "git_commit": commit,
        "lockfile_sha256": lock_hash,
        "seeds": copy.deepcopy(seeds),
        "params": copy.deepcopy(params),
        "utc_timestamp": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "hardware": {"platform": platform.platform(), "cpu": _cpu_name(), "gpu": _gpu_name()},
        "threads": os.cpu_count() or 1,
    }


def write_sidecar(result_file: Path, record: dict) -> Path:
    """Write ``<result_file>.provenance.json`` (keys sorted, 1-space indent) atomically and return its path. A record
    missing any REQUIRED_KEYS raises ``ValueError`` naming the missing keys; nothing is written."""
    missing = [k for k in REQUIRED_KEYS if k not in record]
    if missing:
        raise ValueError(f"provenance record is missing: {', '.join(missing)}")
    target = result_file.with_name(result_file.name + ".provenance.json")
    from singvst_train.pipeline import atomic_write_text
    atomic_write_text(target, json.dumps(record, sort_keys=True, indent=1) + "\n")
    return target
