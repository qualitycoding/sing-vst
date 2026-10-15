# FROZEN — DO NOT MODIFY (plan/PLAN.md, tests/FROZEN_MANIFEST.sha256). Requirement, decision and claim IDs are cited per test.
import re

import nbformat
import pytest

NAMES = ("train_voice_colab.ipynb", "train_voice_kaggle.ipynb")
FORBIDDEN = re.compile(r"gradio|webui\.py|--share|ngrok|cloudflared|localtunnel|github_pat_|ghp_|hf_[A-Za-z0-9]{10,}|"
                       r"pku\.edu|nju\.edu|mirrors\.")
RVC_COMMIT = "81eed5e8f68b6bed1789f682fe78cdd324495afc"


def _load(root, name):
    p = root / "notebooks" / name
    assert p.exists(), f"missing notebooks/{name} (written by plan step S-016)"
    nb = nbformat.read(p, as_version=4)
    nbformat.validate(nb)
    return nb


@pytest.mark.parametrize("name", NAMES)
def test_P16_notebooks_are_valid_and_committed_without_outputs(root, name):
    """T-P16 (D-016): nbformat 4, valid, no outputs or execution counts (nothing private is committed, A-011)."""
    nb = _load(root, name)
    assert nb.nbformat == 4
    for c in nb.cells:
        if c.cell_type == "code":
            assert c.outputs == [] and c.execution_count is None


@pytest.mark.parametrize("name", NAMES)
def test_P17_notebooks_follow_the_hosted_gpu_rules(root, name):
    """T-P17 (D-016, D-019, C-017, C-018, C-023, C-047): GPU check first; consent before any data step; every training
    action is a call of the toolkit CLI; no web UI, tunnels, tokens or mirror indexes; pinned RVC; archives via tar."""
    nb = _load(root, name)
    code = [c.source for c in nb.cells if c.cell_type == "code"]
    src = "\n".join(c.source for c in nb.cells)
    assert not FORBIDDEN.search(src), FORBIDDEN.search(src).group(0)
    assert "nvidia-smi" in code[0]
    consent = next(i for i, c in enumerate(code) if "assert CONSENT_CONFIRMED" in c)
    first_data = next(i for i, c in enumerate(code) if "singvst_train.cli prepare" in c)
    assert consent < first_data
    assert re.search(r"^CONSENT_CONFIRMED\s*=\s*False\b", src, re.M), "consent must default to False"
    for cmd in ("prepare", "rvc-files", "rvc-train-command", "export", "pack", "evaluate"):
        assert f"python -m singvst_train.cli {cmd}" in src, cmd
    assert RVC_COMMIT in src
    assert "download.pytorch.org" in src
    assert re.search(r"\btar\b", src)
