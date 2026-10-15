"""Provenance contract (protocol 2B.2, D-015). Stubs until plan step S-012."""
from __future__ import annotations

from pathlib import Path

REQUIRED_KEYS = ("git_commit", "lockfile_sha256", "seeds", "params", "utc_timestamp", "hardware", "threads")


def collect(params: dict, seeds: dict, repo_root: Path, lockfile: Path) -> dict:
    """Return a dict with exactly REQUIRED_KEYS.

    ``git_commit``: ``git -C repo_root rev-parse HEAD`` (40 hex), or ``"unknown"`` when that fails. ``lockfile_sha256``:
    SHA-256 hex of ``lockfile`` (missing → ``FileNotFoundError``). ``utc_timestamp``: ISO-8601 with a ``Z`` suffix.
    ``hardware``: ``{"platform", "cpu", "gpu"}`` with ``gpu`` the first line of ``nvidia-smi --query-gpu=name
    --format=csv,noheader`` or ``"none"``. ``threads``: ``os.cpu_count()``. ``params``/``seeds`` are copied."""
    raise NotImplementedError("collect")


def write_sidecar(result_file: Path, record: dict) -> Path:
    """Write ``<result_file>.provenance.json`` (keys sorted, 1-space indent) atomically and return its path. A record
    missing any REQUIRED_KEYS raises ``ValueError`` naming the missing keys; nothing is written."""
    raise NotImplementedError("write_sidecar")
