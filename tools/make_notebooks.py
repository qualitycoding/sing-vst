"""Assembles notebooks/train_voice_colab.ipynb and notebooks/train_voice_kaggle.ipynb from tools/notebook_cells (D-016, D-035).
Usage: python3.12 tools/make_notebooks.py   (nbformat 4, no outputs). The cell order is D-035 section "Notebook layout"."""
import pathlib

import nbformat
from nbformat.v4 import new_code_cell, new_markdown_cell, new_notebook

ROOT = pathlib.Path(__file__).resolve().parents[1]
CELLS = ROOT / "tools" / "notebook_cells"
ORDER = ["01", "02", "02a", "03", "04", "05", "06", "07", "08", "09", "10", "10a", "11", "12", "13", "14", "15", "16", "17"]
FILES = {"01": "c01_{p}.py", "02": "c02_consent.py", "02a": "c02a_params.py", "03": "c03_helpers.py", "04": "c04_setup.py",
         "05": "c05_assets.py", "06": "c06_checks.py", "07": "c07_split.py", "08": "c08_prepare.py", "09": "c09_rvc.py",
         "10": "c10_files.py", "10a": "c10a_resources.py", "11": "c11_train.py", "12": "c12_export.py", "13": "c13_render-bin.py",
         "14": "c14_pack.py", "15": "c15_evaluate.py", "16": "c16_tp20.py", "17": "c17_finish.py"}
RULES = {
    "colab": {"@RESUME_RULE@": "Colab: leave False (the state lives on Drive)", "@PRUNE_RULE@": "ignored on Colab: delete the folder on Drive instead",
              "@KILLED_RULE@": "must stay 0.0 on Colab (the heartbeat covers a killed session)"},
    "kaggle": {"@RESUME_RULE@": "True exactly when an earlier Kaggle version of this voice has a state.tar in its output; attach the newest such version",
               "@PRUNE_RULE@": "the <exp> a `prune:` response named, as GATE-G-004.md states", "@KILLED_RULE@": "sum of the run times of this issue's earlier killed versions, in hours (GATE-G-004.md)"},
}
INTRO = """# sing-vst voice training ({platform})

Trains an RVC v2 voice from your own recordings on a free hosted GPU, builds the voice package and evaluates it (D-016, D-035).
Read GATE-G-004.md first. Edit **only** cell (2) (consent) and cell (2a) (parameters). Keep everything private: the recordings,
the renders and the voice package never go into the repository (A-011). The guide voicebank (TIGER DiffSinger v102) is for personal
non-commercial use only and is downloaded inside this notebook, never redistributed (G-005)."""


def build(platform):
    cells = [new_markdown_cell(INTRO.format(platform=platform.capitalize()))]
    for key in ORDER:
        src = (CELLS / FILES[key].format(p=platform)).read_text(encoding="utf-8")
        src = src.replace("@PLATFORM@", platform)
        for token, text in RULES[platform].items():
            src = src.replace(token, text)
        cells.append(new_code_cell(src.rstrip("\n")))
    nb = new_notebook(cells=cells)
    nb.metadata["kernelspec"] = {"name": "python3", "display_name": "Python 3", "language": "python"}
    nbformat.validate(nb)
    return nb


if __name__ == "__main__":
    out = ROOT / "notebooks"
    out.mkdir(exist_ok=True)
    for platform in ("colab", "kaggle"):
        nbformat.write(build(platform), out / f"train_voice_{platform}.ipynb")
        print("wrote", out / f"train_voice_{platform}.ipynb")
