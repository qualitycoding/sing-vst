"""Resumable stage runner for hosted-GPU sessions (D-016, PK-43). Stubs until plan step S-012."""
from __future__ import annotations

import hashlib
import os
import shutil
import struct
import tempfile

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
    files: list[tuple[str, Path]] = []
    for root in paths:
        if not root.exists():
            raise ValueError(f"missing path: {root}")
        found = [root] if root.is_file() else sorted(q for q in root.rglob("*") if q.is_file())
        files.extend((q.relative_to(root.parent).as_posix(), q) for q in found)
    digest = hashlib.sha256()
    for rel, q in sorted(files, key=lambda item: item[0]):
        digest.update(rel.encode("utf-8") + b"\0" + struct.pack("<Q", q.stat().st_size))
        with q.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1 << 20), b""):
                digest.update(chunk)
    return digest.hexdigest()


def run_stages(stages: list[Stage], state_dir: Path) -> list[str]:
    """Run stages in order and return the names that ran.

    A stage is skipped when ``state_dir/<name>.done`` exists, its text equals ``content_hash(stage.inputs)`` and every
    output exists. Otherwise: existing outputs are deleted (files and directory trees), ``run()`` is called, every
    output must then exist (else ``RuntimeError`` naming the missing output), and the marker is written with
    ``atomic_write_text``. Once a stage runs, every later stage runs too. If ``run()`` raises, no marker is written and
    the exception propagates. Stage names must be unique (``ValueError``)."""
    names = [s.name for s in stages]
    if len(set(names)) != len(names):
        raise ValueError(f"duplicate stage names: {names}")
    state_dir.mkdir(parents=True, exist_ok=True)
    ran: list[str] = []
    cascade = False
    for stage in stages:
        marker = state_dir / f"{stage.name}.done"
        if not cascade and marker.is_file() and all(o.exists() for o in stage.outputs):
            try:
                if marker.read_text(encoding="utf-8") == content_hash(stage.inputs):
                    continue
            except ValueError:
                pass            # an input is missing: run() will fail loudly or recreate it
        cascade = True
        for out in stage.outputs:
            if out.is_dir() and not out.is_symlink():
                shutil.rmtree(out)
            elif out.exists() or out.is_symlink():
                out.unlink()
        wanted = content_hash(stage.inputs)
        stage.run()
        for out in stage.outputs:
            if not out.exists():
                raise RuntimeError(f"stage {stage.name!r} did not produce {out}")
        atomic_write_text(marker, wanted)
        ran.append(stage.name)
    return ran


def atomic_write_text(path: Path, text: str) -> None:
    """Write UTF-8 text to a temporary file in the same directory, flush and fsync it, then ``os.replace`` it onto
    ``path``. On any error the temporary file is removed and the target is unchanged."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(dir=path.parent, prefix=path.name + ".", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_name, path)
    except BaseException:
        try:
            os.unlink(tmp_name)
        except FileNotFoundError:
            pass
        raise
