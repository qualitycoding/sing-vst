// ConverterEngine: RVC v2 content encoder + synthesiser over ONNX Runtime (D-012; C-003, C-020, C-021, C-048).
#include "ort_util.hpp"
#include "singvst/engine.hpp"
#include "singvst/ort_runtime.hpp"
#include "singvst/synthesis.hpp"
#include <algorithm>

namespace singvst {
namespace {
constexpr std::int64_t kChunk = 1500;    // core frames per chunk
constexpr std::int64_t kContext = 100;   // context frames per side
using ortutil::Model;

class ConverterImpl final : public ConverterEngine {
public:
    ConverterImpl (const VoiceManifest& m, const std::filesystem::path& dir)
        : env (ORT_LOGGING_LEVEL_WARNING, "singvst"), sr (m.converter->sampleRate), speakerId (m.converter->speakerId)
    {
        const auto& f = m.converter->files;
        for (const char* role : { "synth", "content" })
            if (! f.count (role)) throw ValidationError (std::string ("converter.files.") + role + ": required file role missing");
        content = ortutil::loadModel (env, dir, f.at ("content"), "content encoder");
        synth = ortutil::loadModel (env, dir, f.at ("synth"), "synthesiser");
        if (content.indexOfInput ("source") < 0) throw ValidationError ("content model has no 'source' input");
        for (const char* req : { "phone", "phone_lengths", "pitch", "pitchf", "ds", "rnd" })
            if (synth.indexOfInput (req) < 0) throw ValidationError (std::string ("synthesiser model has no '") + req + "' input");
    }

    int sampleRate() const override { return sr; }

    std::vector<float> convert (const std::vector<float>& guide, int guideSampleRate, const std::vector<float>& f0, std::uint64_t seed,
                                const std::atomic<bool>& cancel) override
    {
        const auto g16 = resample (guide, guideSampleRate, 16000);
        const std::int64_t hop = sr / 100;
        const std::int64_t T = std::min<std::int64_t> (static_cast<std::int64_t> (f0.size()), static_cast<std::int64_t> (g16.size()) / 160);
        std::vector<float> out (static_cast<std::size_t> (T * hop), 0.0f);
        if (T == 0) { if (cancel.load()) throw Cancelled(); return out; }

        const auto noise = standardNormal (seed, static_cast<std::size_t> (192 * T));   // [192][T] for the whole take
        std::vector<std::int64_t> pitch (static_cast<std::size_t> (T));
        for (std::int64_t t = 0; t < T; ++t) pitch[static_cast<std::size_t> (t)] = rvcCoarsePitch (f0[static_cast<std::size_t> (t)]);

        Ort::MemoryInfo mem = Ort::MemoryInfo::CreateCpu (OrtArenaAllocator, OrtMemTypeDefault);
        for (std::int64_t a = 0; a < T; a += kChunk) {
            const std::int64_t bnd = std::min (a + kChunk, T), lo = std::max<std::int64_t> (0, a - kContext), hi = std::min (T, bnd + kContext);
            const std::int64_t n = hi - lo;

            // Content units of the chunk's 16 kHz slice; each unit repeated twice (50 -> 100 fps), cut or extended to n frames.
            std::vector<float> slice (g16.begin() + lo * 160, g16.begin() + hi * 160);
            const std::vector<std::int64_t> sshape { 1, static_cast<std::int64_t> (slice.size()) };
            std::vector<Ort::Value> cin;
            cin.push_back (Ort::Value::CreateTensor<float> (mem, slice.data(), slice.size(), sshape.data(), sshape.size()));
            const std::vector<const char*> cnames { "source" };
            auto cout_ = ortutil::runWatched (content, cancel, cnames, cin);
            const auto cinfo = cout_.front().GetTensorTypeAndShapeInfo();
            const auto cshape = cinfo.GetShape();
            if (cshape.size() != 3 || cshape[2] != 768) throw ValidationError ("content model must output units of shape [1, T, 768]");
            const std::int64_t tc = cshape[1];
            const float* units = cout_.front().GetTensorData<float>();
            std::vector<float> phone (static_cast<std::size_t> (n * 768));
            for (std::int64_t t = 0; t < n; ++t) {
                const std::int64_t src = tc == 0 ? 0 : std::min (t / 2, tc - 1);
                if (tc > 0) std::copy (units + src * 768, units + (src + 1) * 768, phone.begin() + t * 768);
            }

            std::vector<std::int64_t> plen { n }, ds { speakerId };
            std::vector<std::int64_t> p (pitch.begin() + lo, pitch.begin() + hi);
            std::vector<float> pf (f0.begin() + lo, f0.begin() + hi);
            std::vector<float> rnd (static_cast<std::size_t> (192 * n));
            for (std::int64_t c = 0; c < 192; ++c)
                std::copy (noise.begin() + c * T + lo, noise.begin() + c * T + hi, rnd.begin() + c * n);
            const std::vector<std::int64_t> s_phone { 1, n, 768 }, s_one { 1 }, s_n { 1, n }, s_rnd { 1, 192, n };
            std::vector<Ort::Value> sin;
            std::vector<const char*> snames;
            for (const auto& nm : synth.inputNames) {
                snames.push_back (nm.c_str());
                if (nm == "phone") sin.push_back (Ort::Value::CreateTensor<float> (mem, phone.data(), phone.size(), s_phone.data(), s_phone.size()));
                else if (nm == "phone_lengths") sin.push_back (Ort::Value::CreateTensor<std::int64_t> (mem, plen.data(), 1, s_one.data(), s_one.size()));
                else if (nm == "pitch") sin.push_back (Ort::Value::CreateTensor<std::int64_t> (mem, p.data(), p.size(), s_n.data(), s_n.size()));
                else if (nm == "pitchf") sin.push_back (Ort::Value::CreateTensor<float> (mem, pf.data(), pf.size(), s_n.data(), s_n.size()));
                else if (nm == "ds") sin.push_back (Ort::Value::CreateTensor<std::int64_t> (mem, ds.data(), 1, s_one.data(), s_one.size()));
                else if (nm == "rnd") sin.push_back (Ort::Value::CreateTensor<float> (mem, rnd.data(), rnd.size(), s_rnd.data(), s_rnd.size()));
                else throw ValidationError ("synthesiser input '" + nm + "' is not supported");
            }
            auto audio = ortutil::runWatched (synth, cancel, snames, sin);
            const auto count = audio.front().GetTensorTypeAndShapeInfo().GetElementCount();
            if (count < static_cast<std::size_t> (n * hop)) throw ValidationError ("synthesiser returned fewer samples than frames * hop");
            const float* y = audio.front().GetTensorData<float>();
            std::copy (y + (a - lo) * hop, y + (bnd - lo) * hop, out.begin() + a * hop);
        }
        return out;
    }

private:
    Ort::Env env;
    Model content, synth;
    int sr, speakerId;
};
} // namespace

std::unique_ptr<ConverterEngine> ConverterEngine::load (const VoiceManifest& m, const std::filesystem::path& dir)
{
    if (! ortRuntimeLoaded()) throw ValidationError ("ONNX Runtime is not loaded; call loadOrtRuntime first");
    if (! m.converter) throw ValidationError ("the voice has no converter");
    return std::make_unique<ConverterImpl> (m, dir);
}

} // namespace singvst
