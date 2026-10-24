// Private helpers shared by the guide and converter engines (D-012): model loading from bytes, the external-data
// rejection walk, and a model run with the 10 ms terminate watcher.
#pragma once
#include <atomic>
#include <chrono>
#include <filesystem>
#include <memory>
#include <string>
#include <thread>
#include <vector>
#include <onnxruntime_cxx_api.h>
#include "singvst/errors.hpp"

namespace singvst::ortutil {

/** Reads a file named by the manifest. The path must be relative with no '..' component. Throws ValidationError. */
std::string readManifestFile (const std::filesystem::path& dir, const std::string& rel, std::uintmax_t maxBytes = (std::uintmax_t) 2 << 30);

/** Throws ValidationError for malformed model bytes or initialisers that use external data (ModelProto.graph(7) ->
    GraphProto.initializer(5) -> TensorProto.data_location(14) == EXTERNAL(1) or any external_data(13)). */
void rejectExternalData (const std::string& modelBytes, const std::string& what);

struct Model {
    std::unique_ptr<Ort::Session> session;
    std::vector<std::string> inputNames;
    std::vector<std::string> outputNames;
    std::vector<ONNXTensorElementDataType> inputTypes;
    std::vector<std::vector<std::int64_t>> inputShapes;   // -1 = dynamic
    int indexOfInput (const std::string& name) const;     // -1 when absent
};

/** Loads a model from the manifest file `rel` under `dir`. Requires the runtime (ValidationError otherwise). */
Model loadModel (Ort::Env& env, const std::filesystem::path& dir, const std::string& rel, const std::string& what);

/** Runs `session` with a watcher thread that polls `cancel` every 10 ms and calls SetTerminate on this run's options.
    Throws Cancelled when cancel is set before the run or when the run is terminated; other ONNX Runtime errors are
    rethrown as std::runtime_error. */
std::vector<Ort::Value> runWatched (Model& m, const std::atomic<bool>& cancel, const std::vector<const char*>& inNames,
                                    std::vector<Ort::Value>& inputs);

} // namespace singvst::ortutil
