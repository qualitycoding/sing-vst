import sys, onnx
from onnx import helper, TensorProto
X = helper.make_tensor_value_info("phone", TensorProto.FLOAT, [1, "T", 768]); Y = helper.make_tensor_value_info("out", TensorProto.FLOAT, [1, "T", 768])
m = helper.make_model(helper.make_graph([helper.make_node("Mul", ["phone", "phone"], ["out"])], "g", [X], [Y]), opset_imports=[helper.make_opsetid("", 17)])
m.ir_version = 9; onnx.checker.check_model(m); onnx.save(m, sys.argv[1])
