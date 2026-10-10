// Spike R6 round 3 (D-024, C-042): ONNX Runtime 1.31.0 used with ORT_API_MANUAL_INIT and no link-time dependency;
// the library is loaded by explicit path, OrtGetApiBase is resolved by name, and the API version and loaded path are checked.
#define ORT_API_MANUAL_INIT
#include <onnxruntime_cxx_api.h>
#include <array>
#include <cstdio>
#include <dlfcn.h>
#include <link.h>
#include <string>
#include <vector>

int main (int argc, char** argv) {
    if (argc < 3) return 2;
    void* h = dlopen (argv[1], RTLD_NOW | RTLD_LOCAL);
    if (h == nullptr) { std::printf ("dlopen failed: %s\n", dlerror()); return 3; }
    using GetBase = const OrtApiBase* (*)();
    auto getBase = reinterpret_cast<GetBase> (dlsym (h, "OrtGetApiBase"));
    if (getBase == nullptr) { std::printf ("OrtGetApiBase not found\n"); return 4; }
    const OrtApi* api = getBase()->GetApi (ORT_API_VERSION);
    std::printf ("version string %s; GetApi(%d) %s\n", getBase()->GetVersionString(), ORT_API_VERSION, api ? "ok" : "null");
    if (api == nullptr) return 5;
    char path[4096] = {}; dlinfo (h, RTLD_DI_ORIGIN, path);
    std::printf ("loaded from directory %s\n", path);
    Ort::InitApi (api);
    Ort::Env env { ORT_LOGGING_LEVEL_WARNING, "spike" };
    Ort::SessionOptions so; so.SetIntraOpNumThreads (1);
    Ort::Session s { env, argv[2], so };
    std::vector<float> in (4 * 768, 3.0f);
    std::array<int64_t, 3> shape { 1, 4, 768 };
    auto mem = Ort::MemoryInfo::CreateCpu (OrtArenaAllocator, OrtMemTypeDefault);
    auto t = Ort::Value::CreateTensor<float> (mem, in.data(), in.size(), shape.data(), shape.size());
    const char* inN[] = { "phone" }; const char* outN[] = { "out" };
    auto out = s.Run (Ort::RunOptions { nullptr }, inN, &t, 1, outN, 1);
    std::printf ("out[0]=%g\n", (double) out[0].GetTensorData<float>()[0]);
    void* bad = dlopen ("/nonexistent/libonnxruntime.so", RTLD_NOW | RTLD_LOCAL);
    std::printf ("bad path -> %s\n", bad ? "loaded?!" : "null (expected)");
    return 0;
}
