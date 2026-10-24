// Explicit-path loading of ONNX Runtime (D-024; C-026, C-042).
#include "singvst/ort_runtime.hpp"
#include "singvst/errors.hpp"
#include <atomic>
#include <mutex>
#include <optional>
#include <onnxruntime_cxx_api.h>
#ifdef _WIN32
 #define NOMINMAX
 #include <windows.h>
#else
 #include <dlfcn.h>
#endif

namespace singvst {
namespace {
std::mutex gMutex;
std::optional<OrtRuntimeInfo> gInfo;
std::atomic<bool> gLoaded { false };

void* openLibrary (const std::filesystem::path& p)
{
#ifdef _WIN32
    return reinterpret_cast<void*> (::LoadLibraryExW (p.wstring().c_str(), nullptr, LOAD_WITH_ALTERED_SEARCH_PATH));
#else
    return ::dlopen (p.c_str(), RTLD_NOW | RTLD_LOCAL);
#endif
}
void* findSymbol (void* lib, const char* name)
{
#ifdef _WIN32
    return reinterpret_cast<void*> (::GetProcAddress (reinterpret_cast<HMODULE> (lib), name));
#else
    return ::dlsym (lib, name);
#endif
}
void closeLibrary (void* lib)
{
#ifdef _WIN32
    ::FreeLibrary (reinterpret_cast<HMODULE> (lib));
#else
    ::dlclose (lib);
#endif
}
} // namespace

const OrtRuntimeInfo& loadOrtRuntime (const std::filesystem::path& library)
{
    namespace fs = std::filesystem;
    std::lock_guard<std::mutex> lock (gMutex);
    std::error_code ec;
    const fs::path abs = fs::absolute (library, ec);
    if (ec || ! fs::is_regular_file (abs, ec)) throw ValidationError ("ONNX Runtime library not found: " + library.string());
    if (gInfo) {
        if (fs::equivalent (gInfo->path, abs, ec) && ! ec) return *gInfo;
        throw ValidationError ("ONNX Runtime is already loaded from " + gInfo->path.string() + "; refusing " + abs.string());
    }
    void* lib = openLibrary (abs);
    if (lib == nullptr) throw ValidationError ("not a loadable ONNX Runtime library: " + abs.string());
    using GetBase = const OrtApiBase* (ORT_API_CALL*) ();
    auto getBase = reinterpret_cast<GetBase> (findSymbol (lib, "OrtGetApiBase"));
    if (getBase == nullptr) { closeLibrary (lib); throw ValidationError ("no OrtGetApiBase in " + abs.string()); }
    const OrtApiBase* base = getBase();
    const OrtApi* api = base != nullptr ? base->GetApi (ORT_API_VERSION) : nullptr;
    if (api == nullptr) { closeLibrary (lib); throw ValidationError ("ONNX Runtime library does not support API version " + std::to_string (ORT_API_VERSION)); }
    const std::string version = base->GetVersionString();
    if (version != SINGVST_ORT_VERSION) {
        closeLibrary (lib);
        throw ValidationError ("ONNX Runtime version " + version + " found, " SINGVST_ORT_VERSION " required");
    }
    Ort::InitApi (api);
    gInfo = OrtRuntimeInfo { version, abs };
    gLoaded = true;
    return *gInfo;
}

bool ortRuntimeLoaded() noexcept { return gLoaded.load(); }

std::string bundledOrtFileName()
{
#ifdef _WIN32
    return "onnxruntime.dll";
#else
    return "libonnxruntime.so.1.31.0";
#endif
}

} // namespace singvst
