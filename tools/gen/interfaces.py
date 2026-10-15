"""Records the frozen Python interface (D-003, PK-22): every public function/class signature, the SHA-256 of every
public docstring (documented behaviour), and the public constants of singvst_train. Output: tests/python/interfaces.json,
which T-P27 compares with the live package. Re-run only during a planning amendment (2E.4), never by the implementer.
Usage: python -I tools/gen/interfaces.py"""
import hashlib, importlib, inspect, json, pathlib, sys
ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "python"))
MODULES = ["prepare", "pipeline", "provenance", "metrics", "pack", "security", "rvc_files", "export_rvc", "evaluate", "cli"]


def record():
    out = {}
    for name in MODULES:
        m = importlib.import_module(f"singvst_train.{name}")
        entry = {}
        for k, v in sorted(vars(m).items()):
            if k.startswith("_") or getattr(v, "__module__", m.__name__) != m.__name__ and (inspect.isfunction(v) or inspect.isclass(v)):
                continue
            if inspect.isfunction(v) or inspect.isclass(v):
                sig = str(inspect.signature(v)) if inspect.isfunction(v) else [f.name + ": " + str(f.type) for f in getattr(v, "__dataclass_fields__", {}).values()]
                entry[k] = {"kind": "function" if inspect.isfunction(v) else "class", "signature": sig,
                            "doc_sha256": hashlib.sha256((inspect.getdoc(v) or "").encode()).hexdigest()}
            elif k.isupper() and isinstance(v, (tuple, str, int, float)):
                entry[k] = {"kind": "constant", "value": list(v) if isinstance(v, tuple) else v}
        out[name] = entry
    return out


if __name__ == "__main__":
    (ROOT / "tests" / "python" / "interfaces.json").write_text(json.dumps(record(), indent=1, sort_keys=True) + "\n")
    print("modules", len(MODULES))
