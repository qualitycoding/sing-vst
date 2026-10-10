#include <onnxruntime_cxx_api.h>
#include <array>
#include <iostream>
#include <vector>
int main (int argc, char** argv) {
    Ort::Env env { ORT_LOGGING_LEVEL_WARNING, "spike" };
    Ort::SessionOptions so; so.SetIntraOpNumThreads (1);
    Ort::Session s { env, argv[argc - 1], so };
    const int64_t T = 4; std::vector<float> in (T * 768, 3.0f);
    std::array<int64_t, 3> shape { 1, T, 768 };
    auto mem = Ort::MemoryInfo::CreateCpu (OrtArenaAllocator, OrtMemTypeDefault);
    auto t = Ort::Value::CreateTensor<float> (mem, in.data(), in.size(), shape.data(), shape.size());
    const char* inN[] { "phone" }; const char* outN[] { "out" };
    auto out = s.Run (Ort::RunOptions { nullptr }, inN, &t, 1, outN, 1);
    std::cout << "ORT " << Ort::GetVersionString() << " out[0]=" << out[0].GetTensorData<float>()[0] << "\n";
    try { Ort::Session bad { env, "does-not-exist.onnx", so }; } catch (const Ort::Exception& e) { std::cout << "missing model -> Ort::Exception code " << e.GetOrtErrorCode() << "\n"; }
    return 0;
}
