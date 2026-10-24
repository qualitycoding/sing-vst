"""Voice package writer, format v1 (D-008). Stubs until plan step S-012."""
from __future__ import annotations

import hashlib
import json
import re
import shutil

from pathlib import Path

GUIDE_ROLES_REQUIRED = ("acoustic", "vocoder", "phonemes")
GUIDE_ROLES_OPTIONAL = ("speaker", "languages")
CONVERTER_ROLES = ("synth", "content")


_safe_name = re.compile(r"[A-Za-z0-9._-]+")


def _check_roles(files: dict, required: tuple, optional: tuple, label: str) -> None:
    unknown = sorted(set(files) - set(required) - set(optional))
    if unknown:
        raise ValueError(f"unknown {label} file role(s): {', '.join(unknown)}")
    missing = [r for r in required if r not in files]
    if missing:
        raise ValueError(f"missing {label} file role(s): {', '.join(missing)}")


def pack_voice(out_dir: Path, name: str, consent: str, guide_licence: str, guide_files: dict[str, Path],
               converter_files: dict[str, Path] | None, *, language: str = "en", steps: int = 20, depth: float = 0.4,
               converter_sample_rate: int = 48000, speaker_id: int = 0) -> dict:
    """Copy guide files to ``out_dir/guide/<basename>`` and converter files to ``out_dir/conv/<basename>``, then write
    ``out_dir/manifest.json`` exactly per D-008 (``format`` "singvoice", ``format_version`` 1, ``guide`` with
    ``type`` "diffsinger", ``sample_rate`` 44100, ``hop_size`` 512, ``language``, ``steps``, ``depth``, ``files``;
    ``converter`` null or ``type`` "rvc-v2" with ``sample_rate``, ``speaker_id``, ``files``; ``sha256`` of every copied
    file keyed by its relative path), 1-space indent, keys in that order. Returns the manifest dict.

    ``ValueError`` (nothing written) for: empty ``name``/``consent``/``guide_licence``; a missing required role or an
    unknown role; a basename that is not a safe D-008 path segment; two files with the same destination path;
    ``steps`` outside 1..1000; ``depth`` outside (0, 1]; ``converter_sample_rate`` not 48000 or 32000; negative
    ``speaker_id``; an existing non-empty ``out_dir``."""
    for label, value in (("name", name), ("consent", consent), ("guide_licence", guide_licence)):
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{label} must be a non-empty string")
    _check_roles(guide_files, GUIDE_ROLES_REQUIRED, GUIDE_ROLES_OPTIONAL, "guide")
    if converter_files is not None:
        _check_roles(converter_files, CONVERTER_ROLES, (), "converter")
    if not isinstance(steps, int) or isinstance(steps, bool) or not 1 <= steps <= 1000:
        raise ValueError(f"steps must be an integer from 1 to 1000, got {steps!r}")
    if not isinstance(depth, (int, float)) or isinstance(depth, bool) or not 0.0 < depth <= 1.0:
        raise ValueError(f"depth must be in (0, 1], got {depth!r}")
    if converter_sample_rate not in (48000, 32000):
        raise ValueError(f"converter_sample_rate must be 48000 or 32000, got {converter_sample_rate!r}")
    if not isinstance(speaker_id, int) or isinstance(speaker_id, bool) or speaker_id < 0:
        raise ValueError(f"speaker_id must be a non-negative integer, got {speaker_id!r}")
    if not isinstance(language, str) or not language.strip():
        raise ValueError("language must be a non-empty string")
    out_dir = Path(out_dir)
    if out_dir.exists() and (not out_dir.is_dir() or any(out_dir.iterdir())):
        raise ValueError(f"{out_dir} exists and is not an empty directory")

    plan: list[tuple[str, Path]] = []          # (relative destination, source)
    seen: dict[str, str] = {}

    def destination(folder: str, source: Path, role: str) -> str:
        base = Path(source).name
        if not _safe_name.fullmatch(base) or base in (".", ".."):
            raise ValueError(f"file name {base!r} (role {role}) is not a safe path segment")
        rel = f"{folder}/{base}"
        if rel in seen:
            raise ValueError(f"{role} and {seen[rel]} both map to {rel}")
        if not Path(source).is_file():
            raise FileNotFoundError(f"{role} file not found: {source}")
        seen[rel] = role
        plan.append((rel, Path(source)))
        return rel

    guide_order = [r for r in (*GUIDE_ROLES_REQUIRED, *GUIDE_ROLES_OPTIONAL) if r in guide_files]
    guide_rel = {role: destination("guide", guide_files[role], f"guide.{role}") for role in guide_order}
    converter = None
    if converter_files is not None:
        conv_rel = {role: destination("conv", converter_files[role], f"converter.{role}") for role in CONVERTER_ROLES}
        converter = {"type": "rvc-v2", "sample_rate": converter_sample_rate, "speaker_id": speaker_id, "files": conv_rel}

    sha: dict[str, str] = {}
    for rel, source in plan:
        target = out_dir / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        digest = hashlib.sha256()
        with target.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1 << 20), b""):
                digest.update(chunk)
        sha[rel] = digest.hexdigest()
    manifest = {
        "format": "singvoice",
        "format_version": 1,
        "name": name,
        "consent": consent,
        "guide_licence": guide_licence,
        "guide": {"type": "diffsinger", "sample_rate": 44100, "hop_size": 512, "language": language, "steps": steps,
                  "depth": depth, "files": guide_rel},
        "converter": converter,
        "sha256": sha,
    }
    from singvst_train.pipeline import atomic_write_text
    atomic_write_text(out_dir / "manifest.json", json.dumps(manifest, indent=1) + "\n")
    return manifest
