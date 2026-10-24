"""Writes a copy of the fixture acoustic model whose initialisers are saved as external data (D-012 external-data check)."""
import sys, pathlib, onnx
src, dst = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
m = onnx.load(str(src))
onnx.save_model(m, str(dst), save_as_external_data=True, all_tensors_to_one_file=True, location=dst.name + ".data", size_threshold=0)
ext = sum(1 for t in onnx.load(str(dst), load_external_data=False).graph.initializer if t.data_location == onnx.TensorProto.EXTERNAL)
print(f"external initialisers written: {ext}")
assert ext > 0
