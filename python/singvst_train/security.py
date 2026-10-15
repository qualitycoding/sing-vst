"""Repository secret scan (Rule 13, PK-12). Stub until plan step S-012."""
from __future__ import annotations

from pathlib import Path

PATTERNS = (r"github_pat_[A-Za-z0-9_]{20,}", r"ghp_[A-Za-z0-9]{20,}", r"gho_[A-Za-z0-9]{20,}", r"AKIA[0-9A-Z]{16}",
            r"-----BEGIN [A-Z ]*PRIVATE KEY-----", r"hf_[A-Za-z0-9]{30,}", r"KGAT_[A-Za-z0-9]{20,}")


def scan_secrets(root: Path, exclude_dirs: tuple[str, ...] = (".git",)) -> list[str]:
    """Return sorted ``"<relative posix path>:<line number>"`` for every line of every text file under ``root``
    matching any of PATTERNS. Directories named in ``exclude_dirs`` are skipped at any depth. A file is binary (skipped)
    when its first 8192 bytes contain a NUL byte; text is decoded as UTF-8 with replacement."""
    raise NotImplementedError("scan_secrets")
