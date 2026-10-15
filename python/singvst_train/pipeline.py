"""Resumable stage runner for hosted-GPU sessions (D-016, PK-43). Stubs until plan step S-012."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable


@dataclass(frozen=True)
class Stage:
    name: str
    inputs: tuple[Path, ...]
    outputs: tuple[Path, ...]
    run: Callable[[], None]


def content_hash(paths: tuple[Path, ...]) -> str:
    """SHA-256 hex over every regular file under ``paths`` (a path may be a file or a directory, walked recursively).
    For each file, sorted by its POSIX path relative to the given root's parent: feed ``relpath + "\\0"`` (UTF-8),
    the 8-byte little-endian length, then the bytes. A missing path raises ``ValueError`` naming it."""
    raise NotImplementedError("content_hash")


def run_stages(stages: list[Stage], state_dir: Path) -> list[str]:
    """Run stages in order and return the names that ran.

    A stage is skipped when ``state_dir/<name>.done`` exists, its text equals ``content_hash(stage.inputs)`` and every
    output exists. Otherwise: existing outputs are deleted (files and directory trees), ``run()`` is called, every
    output must then exist (else ``RuntimeError`` naming the missing output), and the marker is written with
    ``atomic_write_text``. Once a stage runs, every later stage runs too. If ``run()`` raises, no marker is written and
    the exception propagates. Stage names must be unique (``ValueError``)."""
    raise NotImplementedError("run_stages")


def atomic_write_text(path: Path, text: str) -> None:
    """Write UTF-8 text to a temporary file in the same directory, flush and fsync it, then ``os.replace`` it onto
    ``path``. On any error the temporary file is removed and the target is unchanged."""
    raise NotImplementedError("atomic_write_text")
