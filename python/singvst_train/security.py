"""Repository secret scan (Rule 13, PK-12). Stub until plan step S-012."""
from __future__ import annotations

import os
import re

from pathlib import Path

PATTERNS = (r"github_pat_[A-Za-z0-9_]{20,}", r"ghp_[A-Za-z0-9]{20,}", r"gho_[A-Za-z0-9]{20,}", r"AKIA[0-9A-Z]{16}",
            r"-----BEGIN [A-Z ]*PRIVATE KEY-----", r"hf_[A-Za-z0-9]{30,}", r"KGAT_[A-Za-z0-9]{20,}")


def scan_secrets(root: Path, exclude_dirs: tuple[str, ...] = (".git",)) -> list[str]:
    """Return sorted ``"<relative posix path>:<line number>"`` for every line of every text file under ``root``
    matching any of PATTERNS. Directories named in ``exclude_dirs`` are skipped at any depth. A file is binary (skipped)
    when its first 8192 bytes contain a NUL byte; text is decoded as UTF-8 with replacement."""
    compiled = [re.compile(pat) for pat in PATTERNS]
    hits: list[tuple[str, int]] = []
    root = Path(root)
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if d not in exclude_dirs)
        for name in sorted(filenames):
            path = Path(dirpath) / name
            try:
                with path.open("rb") as handle:
                    head = handle.read(8192)
                    if b"\0" in head:
                        continue
                    raw = head + handle.read()
            except OSError:
                continue
            rel = path.relative_to(root).as_posix()
            for number, line in enumerate(raw.decode("utf-8", errors="replace").split("\n"), start=1):
                if any(rx.search(line) for rx in compiled):
                    hits.append((rel, number))
    return [f"{rel}:{number}" for rel, number in sorted(hits)]
