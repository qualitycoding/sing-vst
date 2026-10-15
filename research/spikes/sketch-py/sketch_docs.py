"""Writes minimal notebooks and a README section into the sketch copy, showing T-P16, T-P17 and T-P23 are satisfiable
(PK-21). Usage: python -I sketch_docs.py <sketch copy root>"""
import pathlib, sys
import nbformat
W = pathlib.Path(sys.argv[1])
cells = [
    nbformat.v4.new_code_cell("!nvidia-smi"),
    nbformat.v4.new_markdown_cell("Consent: set to True only for recordings of your own voice or with the singer's consent."),
    nbformat.v4.new_code_cell("CONSENT_CONFIRMED = False\nATTESTATION = ''"),
    nbformat.v4.new_code_cell("assert CONSENT_CONFIRMED and ATTESTATION"),
    nbformat.v4.new_code_cell("!git clone https://github.com/RVC-Project/Retrieval-based-Voice-Conversion-WebUI.git rvc && "
                              "git -C rvc checkout 81eed5e8f68b6bed1789f682fe78cdd324495afc\n"
                              "!pip install -r rvc-req.txt --extra-index-url https://download.pytorch.org/whl/cu128"),
    nbformat.v4.new_code_cell("!python -m singvst_train.cli prepare --help\n!python -m singvst_train.cli rvc-files --help\n"
                              "!python -m singvst_train.cli rvc-train-command --help\n!python -m singvst_train.cli export --help\n"
                              "!python -m singvst_train.cli pack --help\n!python -m singvst_train.cli evaluate --help\n"
                              "!tar -cf out.tar out"),
]
(W / "notebooks").mkdir(exist_ok=True)
for n in ("train_voice_colab.ipynb", "train_voice_kaggle.ipynb"):
    nbformat.write(nbformat.v4.new_notebook(cells=cells), W / "notebooks" / n)
(W / "README.md").write_text("# sing-vst\n\n## What it does\n\n- Sings typed lyrics on MIDI notes (T-058).\n"
                             "- Validates voice packages (T-028).\n\n## Licence\n\nApache-2.0.\n")
