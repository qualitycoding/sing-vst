// Interface frozen by plan D-003; loading rules in D-024 (C-026, C-042).
#pragma once
#include <filesystem>
#include <string>

namespace singvst {

struct OrtRuntimeInfo {
    std::string version;            // OrtGetApiBase()->GetVersionString(), e.g. "1.31.0"
    std::filesystem::path path;     // absolute path of the library actually loaded
};

/** Loads ONNX Runtime from an explicit file path (never by search order), resolves OrtGetApiBase, requires
    GetApi(ORT_API_VERSION) != nullptr and a version string equal to SINGVST_ORT_VERSION ("1.31.0"), and calls Ort::InitApi.
    Idempotent for the same path; a different path after a successful load, a missing file, a file that is not an ONNX Runtime
    library, or a version mismatch throw ValidationError. Thread-safe. */
const OrtRuntimeInfo& loadOrtRuntime (const std::filesystem::path& library);

/** True after a successful loadOrtRuntime. */
bool ortRuntimeLoaded() noexcept;

/** Platform file name of the bundled library: "onnxruntime.dll" on Windows, "libonnxruntime.so.1.31.0" on Linux. */
std::string bundledOrtFileName();

} // namespace singvst
