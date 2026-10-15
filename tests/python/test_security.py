# FROZEN — DO NOT MODIFY (plan/PLAN.md, tests/FROZEN_MANIFEST.sha256). Requirement, decision and claim IDs are cited per test.
from singvst_train.security import scan_secrets


def test_P15_secret_scan_finds_planted_tokens_and_the_repository_is_clean(tmp_path, root):
    """T-P15 (Rule 13, PK-12: secret handling). Token strings are assembled at run time so this file stays clean."""
    (tmp_path / "a.txt").write_text("ok\ntoken = " + "github_pat_" + "A" * 30 + "\n", encoding="utf-8")
    (tmp_path / "b.bin").write_bytes(b"\x00\x01" + ("ghp_" + "B" * 30).encode())
    (tmp_path / ".git").mkdir()
    (tmp_path / ".git" / "c").write_text("ghp_" + "C" * 30)
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "d.md").write_text("AKIA" + "D" * 16 + "\n" + "-----BEGIN RSA PRIVATE KEY-----")
    assert scan_secrets(tmp_path) == ["a.txt:2", "sub/d.md:1", "sub/d.md:2"]
    assert scan_secrets(root) == []
