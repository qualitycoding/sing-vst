# FROZEN — DO NOT MODIFY (plan/PLAN.md, tests/FROZEN_MANIFEST.sha256). Requirement, decision and claim IDs are cited per test.
import hashlib
import struct
from pathlib import Path

import pytest

from singvst_train.pipeline import Stage, atomic_write_text, content_hash, run_stages


def _stages(tmp: Path, log: list, fail_b: bool = False) -> list:
    a_in, a_out, b_out = tmp / "in.txt", tmp / "a.out", tmp / "b.out"

    def run_a():
        log.append("a")
        a_out.write_text(a_in.read_text().upper())

    def run_b():
        log.append("b")
        if fail_b:
            raise RuntimeError("session died")
        b_out.write_text(a_out.read_text() + "!")

    return [Stage("a", (a_in,), (a_out,), run_a), Stage("b", (a_out,), (b_out,), run_b)]


def test_P05_stages_skip_when_done_and_cascade_on_change(tmp_path):
    """T-P05 (D-016, PK-43: operational — resume after interruption)."""
    (tmp_path / "in.txt").write_text("x")
    log = []
    assert run_stages(_stages(tmp_path, log), tmp_path / "state") == ["a", "b"]
    assert run_stages(_stages(tmp_path, log), tmp_path / "state") == []
    (tmp_path / "in.txt").write_text("y")
    assert run_stages(_stages(tmp_path, log), tmp_path / "state") == ["a", "b"]
    assert (tmp_path / "b.out").read_text() == "Y!"
    (tmp_path / "b.out").unlink()                       # a lost output re-runs that stage
    assert run_stages(_stages(tmp_path, log), tmp_path / "state") == ["b"]
    with pytest.raises(ValueError):
        run_stages(_stages(tmp_path, log) * 2, tmp_path / "state")


def test_P06_failed_stage_leaves_no_marker_and_resumes_there(tmp_path):
    """T-P06 (D-016, PK-43: operational — failure and recovery)."""
    (tmp_path / "in.txt").write_text("x")
    with pytest.raises(RuntimeError, match="session died"):
        run_stages(_stages(tmp_path, [], fail_b=True), tmp_path / "state")
    assert (tmp_path / "state" / "a.done").exists() and not (tmp_path / "state" / "b.done").exists()
    assert run_stages(_stages(tmp_path, []), tmp_path / "state") == ["b"]

    def no_output():
        pass
    with pytest.raises(RuntimeError, match="never.out"):
        run_stages([Stage("c", (tmp_path / "in.txt",), (tmp_path / "never.out",), no_output)], tmp_path / "state")


def test_P07_content_hash_definition_and_atomic_write(tmp_path):
    """T-P07 (D-016): hash matches its documented construction; atomic write leaves no temporary file."""
    d = tmp_path / "d"
    (d / "sub").mkdir(parents=True)
    (d / "1").write_bytes(b"a")
    (d / "sub" / "2").write_bytes(b"bc")
    h = hashlib.sha256()
    for rel, data in (("d/1", b"a"), ("d/sub/2", b"bc")):
        h.update(rel.encode() + b"\0" + struct.pack("<Q", len(data)) + data)
    assert content_hash((d,)) == h.hexdigest()
    (d / "sub" / "2").write_bytes(b"bd")
    assert content_hash((d,)) != h.hexdigest()
    with pytest.raises(ValueError, match="missing"):
        content_hash((tmp_path / "missing",))
    atomic_write_text(tmp_path / "m.txt", "ok")
    atomic_write_text(tmp_path / "m.txt", "ok2")
    assert (tmp_path / "m.txt").read_text() == "ok2"
    assert sorted(p.name for p in tmp_path.iterdir()) == ["d", "m.txt"]
