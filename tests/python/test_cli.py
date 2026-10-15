# FROZEN — DO NOT MODIFY (plan/PLAN.md, tests/FROZEN_MANIFEST.sha256). Requirement, decision and claim IDs are cited per test.
import json
import subprocess
import sys

import pytest

from singvst_train import cli


def test_P25_cli_surface_and_split_command(tmp_path, root):
    """T-P25 (D-015, D-016): the commands the notebooks call exist; split works end to end; usage errors exit 2."""
    p = cli.build_parser()
    sub = next(a for a in p._actions if a.__class__.__name__ == "_SubParsersAction")
    assert tuple(sub.choices) == cli.COMMANDS
    for c in cli.COMMANDS:
        with pytest.raises(SystemExit) as e:
            cli.main([c, "--help"])
        assert e.value.code == 0
    with pytest.raises(SystemExit) as e:
        cli.main(["no-such-command"])
    assert e.value.code == 2
    d = tmp_path / "wavs"
    d.mkdir()
    for i in range(10):
        (d / f"t{i}.wav").write_bytes(b"")
    (d / "notes.txt").write_text("x")
    out = tmp_path / "split.json"
    assert cli.main(["split", "--files-dir", str(d), "--seed", "4", "--out", str(out)]) == 0
    from singvst_train.prepare import split_heldout
    train, held = split_heldout([f"t{i}.wav" for i in range(10)], seed=4)
    assert json.loads(out.read_text()) == {"train": train, "heldout": held}
    r = subprocess.run([sys.executable, "-m", "singvst_train.cli", "--help"], capture_output=True, text=True,
                       cwd=root / "python", timeout=60)
    assert r.returncode == 0 and "split" in r.stdout
