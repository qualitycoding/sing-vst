"""Voice package writer, format v1 (D-008). Stubs until plan step S-012."""
from __future__ import annotations

from pathlib import Path

GUIDE_ROLES_REQUIRED = ("acoustic", "vocoder", "phonemes")
GUIDE_ROLES_OPTIONAL = ("speaker", "languages")
CONVERTER_ROLES = ("synth", "content")


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
    raise NotImplementedError("pack_voice")
