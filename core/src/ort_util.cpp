#include "ort_util.hpp"
#include "singvst/ort_runtime.hpp"
#include <fstream>

namespace singvst::ortutil {
namespace {
[[noreturn]] void fail (const std::string& what, const std::string& why) { throw ValidationError (what + ": " + why); }

struct Reader {
    const unsigned char* p;
    std::size_t n, i = 0;
    std::string what;
    std::uint64_t varint()
    {
        std::uint64_t v = 0;
        for (int s = 0; s < 70; s += 7) {
            if (i >= n) fail (what, "model is not valid protobuf (truncated varint)");
            const unsigned char c = p[i++];
            v |= std::uint64_t (c & 0x7F) << s;
            if (! (c & 0x80)) return v;
        }
        fail (what, "model is not valid protobuf (varint too long)");
    }
    bool more() const { return i < n; }
};

/** Calls f(field, wireType, varintValue, ptr, len) for every field of the message in [p, p+n). */
template <class F> void walk (const unsigned char* p, std::size_t n, const std::string& what, F&& f)
{
    Reader r { p, n, 0, what };
    while (r.more()) {
        const std::uint64_t key = r.varint();
        const unsigned field = static_cast<unsigned> (key >> 3), wt = static_cast<unsigned> (key & 7);
        if (field == 0) fail (what, "model is not valid protobuf (field 0)");
        std::uint64_t v = 0;
        const unsigned char* sub = nullptr;
        std::size_t len = 0;
        if (wt == 0) v = r.varint();
        else if (wt == 1) { if (r.n - r.i < 8) fail (what, "model is not valid protobuf (truncated)"); r.i += 8; }
        else if (wt == 5) { if (r.n - r.i < 4) fail (what, "model is not valid protobuf (truncated)"); r.i += 4; }
        else if (wt == 2) {
            const std::uint64_t l = r.varint();
            if (l > r.n - r.i) fail (what, "model is not valid protobuf (length past the end)");
            sub = r.p + r.i; len = static_cast<std::size_t> (l); r.i += len;
        } else fail (what, "model is not valid protobuf (unsupported wire type)");
        f (field, wt, v, sub, len);
    }
}
} // namespace

std::string readManifestFile (const std::filesystem::path& dir, const std::string& rel, std::uintmax_t maxBytes)
{
    namespace fs = std::filesystem;
    const fs::path r (rel);
    if (rel.empty() || r.is_absolute() || r.has_root_name()) fail (rel, "not a relative path");
    for (const auto& part : r) if (part == "..") fail (rel, "path escapes the voice folder");
    const fs::path file = dir / r;
    std::error_code ec;
    if (! fs::is_regular_file (file, ec)) fail (rel, "missing or not a regular file");
    if (fs::file_size (file, ec) > maxBytes) fail (rel, "file too large");
    std::ifstream in (file, std::ios::binary);
    if (! in) fail (rel, "cannot open");
    return { std::istreambuf_iterator<char> (in), std::istreambuf_iterator<char>() };
}

void rejectExternalData (const std::string& bytes, const std::string& what)
{
    const auto* data = reinterpret_cast<const unsigned char*> (bytes.data());
    walk (data, bytes.size(), what, [&] (unsigned field, unsigned wt, std::uint64_t, const unsigned char* graph, std::size_t glen) {
        if (field != 7 || wt != 2) return;
        walk (graph, glen, what, [&] (unsigned gf, unsigned gwt, std::uint64_t, const unsigned char* tensor, std::size_t tlen) {
            if (gf != 5 || gwt != 2) return;
            walk (tensor, tlen, what, [&] (unsigned tf, unsigned twt, std::uint64_t v, const unsigned char*, std::size_t) {
                if ((tf == 14 && twt == 0 && v == 1) || tf == 13)
                    fail (what, "model uses external data, which is not supported");
            });
        });
    });
}

int Model::indexOfInput (const std::string& name) const
{
    for (std::size_t i = 0; i < inputNames.size(); ++i) if (inputNames[i] == name) return static_cast<int> (i);
    return -1;
}

Model loadModel (Ort::Env& env, const std::filesystem::path& dir, const std::string& rel, const std::string& what)
{
    const std::string bytes = readManifestFile (dir, rel);
    rejectExternalData (bytes, rel);
    Model m;
    try {
        Ort::SessionOptions opts;
        opts.SetGraphOptimizationLevel (GraphOptimizationLevel::ORT_ENABLE_ALL);
        m.session = std::make_unique<Ort::Session> (env, bytes.data(), bytes.size(), opts);
        Ort::AllocatorWithDefaultOptions alloc;
        for (std::size_t i = 0; i < m.session->GetInputCount(); ++i) {
            m.inputNames.emplace_back (m.session->GetInputNameAllocated (i, alloc).get());
            const auto typeInfo = m.session->GetInputTypeInfo (i);   // must outlive the view below
            const auto info = typeInfo.GetTensorTypeAndShapeInfo();
            m.inputTypes.push_back (info.GetElementType());
            m.inputShapes.push_back (info.GetShape());
        }
        for (std::size_t i = 0; i < m.session->GetOutputCount(); ++i)
            m.outputNames.emplace_back (m.session->GetOutputNameAllocated (i, alloc).get());
    } catch (const Ort::Exception& e) {
        fail (rel, std::string (what) + " model could not be loaded: " + e.what());
    }
    if (m.outputNames.empty()) fail (rel, "model has no outputs");
    return m;
}

namespace {
struct Watcher {
    std::atomic<bool> done { false };
    std::thread t;
    Watcher (Ort::RunOptions& ro, const std::atomic<bool>& cancel)
        : t ([this, &ro, &cancel] {
              while (! done.load()) {
                  if (cancel.load()) { ro.SetTerminate(); return; }
                  std::this_thread::sleep_for (std::chrono::milliseconds (10));
              }
          }) {}
    ~Watcher() { done = true; if (t.joinable()) t.join(); }
};
} // namespace

std::vector<Ort::Value> runWatched (Model& m, const std::atomic<bool>& cancel, const std::vector<const char*>& inNames,
                                    std::vector<Ort::Value>& inputs)
{
    if (cancel.load()) throw Cancelled();
    Ort::RunOptions ro;
    std::vector<const char*> outNames { m.outputNames.front().c_str() };
    try {
        Watcher w (ro, cancel);
        return m.session->Run (ro, inNames.data(), inputs.data(), inputs.size(), outNames.data(), 1);
    } catch (const Ort::Exception& e) {
        if (cancel.load()) throw Cancelled();
        throw std::runtime_error (std::string ("ONNX Runtime: ") + e.what());
    }
}

} // namespace singvst::ortutil
