# FROZEN — DO NOT MODIFY (plan/PLAN.md, tests/FROZEN_MANIFEST.sha256). Requirement, decision and claim IDs are cited per test.
import hashlib
import json
import re

import pytest

from singvst_train import provenance


def test_P08_provenance_contract(tmp_path):
    """T-P08 (protocol 2B.2 provenance contract, D-015, Rule 9)."""
    lock = tmp_path / "requirements-lock.txt"
    lock.write_text("numpy==1.26.4\n")
    rec = provenance.collect({"epochs": 10}, {"numpy": 0}, repo_root=tmp_path, lockfile=lock)
    assert set(rec) == set(provenance.REQUIRED_KEYS)
    assert rec["git_commit"] == "unknown"                       # tmp_path is not a git repository
    assert rec["lockfile_sha256"] == hashlib.sha256(b"numpy==1.26.4\n").hexdigest()
    assert re.fullmatch(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(\.\d+)?Z", rec["utc_timestamp"])
    assert rec["params"] == {"epochs": 10} and rec["seeds"] == {"numpy": 0}
    assert set(rec["hardware"]) == {"platform", "cpu", "gpu"} and isinstance(rec["threads"], int)
    result = tmp_path / "result.wav"
    result.write_bytes(b"x")
    side = provenance.write_sidecar(result, rec)
    assert side.name == "result.wav.provenance.json" and json.loads(side.read_text()) == rec
    bad = dict(rec)
    bad.pop("seeds")
    other = tmp_path / "other.wav"
    with pytest.raises(ValueError, match="seeds"):
        provenance.write_sidecar(other, bad)
    assert not (tmp_path / "other.wav.provenance.json").exists()
    with pytest.raises(FileNotFoundError):
        provenance.collect({}, {}, repo_root=tmp_path, lockfile=tmp_path / "missing.txt")


def test_P08b_collect_reads_the_repository_commit(root):
    """T-P08 (provenance names the exact code): inside this repository git_commit is 40 hex digits."""
    rec = provenance.collect({}, {}, repo_root=root, lockfile=root / "python" / "requirements-lock.txt")
    assert re.fullmatch(r"[0-9a-f]{40}", rec["git_commit"])
