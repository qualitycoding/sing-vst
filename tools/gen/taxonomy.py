"""Adds this run's new tags to the staged TAXONOMY.md (Appendix C: new tags added in the same commit). Idempotent; fails loudly."""
import pathlib, re, sys
P = pathlib.Path(__file__).resolve().parents[2] / "TAXONOMY.md"
NEW = {
 "domain:": [("domain:singing-voice-synthesis", "singing voice synthesis and conversion: generating sung audio from notes and lyrics, voice cloning (aliases: svs, svc, voice conversion)")],
 "tech:": [("tech:diffsinger", "the openvpi DiffSinger singing synthesiser, its configs and ONNX exports"),
           ("tech:google-colab", "Google Colaboratory notebooks and their free-tier runtime limits (alias: colab)"),
           ("tech:kaggle", "Kaggle Notebooks and their GPU quota and background sessions"),
           ("tech:onnx", "the ONNX model format, operator sets and onnx Python package (graph building, checker)"),
           ("tech:onnxruntime", "native ONNX Runtime (C/C++ API and Python package), as opposed to onnxruntime-web"),
           ("tech:pluginval", "Tracktion pluginval plug-in validator"),
           ("tech:pytorch", "PyTorch, including torch.onnx export"),
           ("tech:rvc", "RVC-Project Retrieval-based-Voice-Conversion-WebUI: training scripts, models and inference pipeline"),
           ("tech:so-vits-svc", "svc-develop-team so-vits-svc singing voice conversion")],
 "kind:": [("kind:security", "security or secret-handling mistake")],
}
text = P.read_text(encoding="utf-8")
for facet, items in NEW.items():
    for tag, desc in items:
        if f"`{tag}`" in text:
            continue
        m = re.search(rf"^## {re.escape(facet)}\s*\n", text, re.M)
        if not m:
            sys.exit(f"facet section {facet} not found")
        nxt = re.search(r"^## ", text[m.end():], re.M)
        end = m.end() + (nxt.start() if nxt else len(text) - m.end())
        block = text[m.end():end].rstrip("\n").split("\n")
        lines = [l for l in block if l.startswith("- `")] + [f"- `{tag}`: {desc}"]
        head = [l for l in block if not l.startswith("- `")]
        body = "\n".join([*(h for h in head if h.strip()), "", *sorted(lines)]) if any(h.strip() for h in head) else "\n".join(["", *sorted(lines)])
        text = text[:m.end()] + body.lstrip("\n") + "\n\n" + text[end:].lstrip("\n")
P.write_text(text, encoding="utf-8")
for items in NEW.values():
    for tag, _ in items:
        assert f"`{tag}`" in text, tag
print("taxonomy ok")
