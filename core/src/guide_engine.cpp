// GuideEngine: DiffSinger acoustic + vocoder over ONNX Runtime (D-012; C-034, C-035, C-038, C-040, C-041).
#include "ort_util.hpp"
#include "singvst/engine.hpp"
#include "singvst/ort_runtime.hpp"
#include <algorithm>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <deque>
#include <map>
#include <nlohmann/json.hpp>

namespace singvst {
namespace {
constexpr double kFrameRate = 44100.0 / 512.0;
constexpr int kHop = 512;
constexpr std::int64_t kRestFrames = 22;      // an SP span of at least this many frames splits the take into phrases
constexpr std::int64_t kPadFrames = 8;
constexpr std::int64_t kMaxPartFrames = 2584; // about 30 s (R-060, R-077)

using ortutil::Model;

struct Tok { std::int64_t id = 0; std::int64_t lang = 0; };

std::map<std::string, std::int64_t> parsePhonemes (const std::string& rel, const std::string& bytes)
{
    std::map<std::string, std::int64_t> v;
    if (rel.size() >= 5 && rel.substr (rel.size() - 5) == ".json") {
        const auto j = nlohmann::json::parse (bytes, nullptr, false);
        if (j.is_discarded() || ! j.is_object()) throw ValidationError (rel + ": phonemes must be a JSON object phone -> id");
        for (auto it = j.begin(); it != j.end(); ++it) {
            if (! it.value().is_number_integer()) throw ValidationError (rel + ": phoneme ids must be integers");
            v.emplace (it.key(), it.value().get<std::int64_t>());
        }
    } else {
        std::int64_t id = 0;
        std::size_t pos = 0;
        while (pos < bytes.size()) {
            std::size_t eol = bytes.find ('\n', pos);
            const bool last = eol == std::string::npos;
            if (last) eol = bytes.size();
            std::string line = bytes.substr (pos, eol - pos);
            if (! line.empty() && line.back() == '\r') line.pop_back();
            if (! (last && line.empty())) v.emplace (line, id++);
            pos = eol + 1;
        }
    }
    return v;
}

class GuideImpl final : public GuideEngine {
public:
    GuideImpl (const VoiceManifest& m, const std::filesystem::path& dir)
        : env (ORT_LOGGING_LEVEL_WARNING, "singvst"), steps (m.guide.steps), depth (m.guide.depth), language (m.guide.language)
    {
        const auto& f = m.guide.files;
        for (const char* role : { "acoustic", "vocoder", "phonemes" })
            if (! f.count (role)) throw ValidationError (std::string ("guide.files.") + role + ": required file role missing");
        vocab = parsePhonemes (f.at ("phonemes"), ortutil::readManifestFile (dir, f.at ("phonemes")));
        if (! vocab.count ("SP")) throw ValidationError (f.at ("phonemes") + ": vocabulary has no SP token");
        if (f.count ("languages")) {
            const auto j = nlohmann::json::parse (ortutil::readManifestFile (dir, f.at ("languages")), nullptr, false);
            if (j.is_discarded() || ! j.is_object()) throw ValidationError (f.at ("languages") + ": languages must be a JSON object");
            for (auto it = j.begin(); it != j.end(); ++it)
                if (it.value().is_number_integer()) langs[it.key()] = it.value().get<std::int64_t>();
        }
        if (f.count ("speaker")) {
            const auto b = ortutil::readManifestFile (dir, f.at ("speaker"));
            if (b.empty() || b.size() % 4 != 0) throw ValidationError (f.at ("speaker") + ": speaker embedding must be raw float32");
            speaker.resize (b.size() / 4);
            std::memcpy (speaker.data(), b.data(), b.size());   // little-endian host (x86-64)
        }
        acoustic = ortutil::loadModel (env, dir, f.at ("acoustic"), "acoustic");
        vocoder = ortutil::loadModel (env, dir, f.at ("vocoder"), "vocoder");

        static const char* const allowed[] = { "tokens", "durations", "f0", "gender", "velocity", "spk_embed", "languages", "steps", "depth", "speedup" };
        for (const auto& n : acoustic.inputNames)
            if (std::find_if (std::begin (allowed), std::end (allowed), [&] (const char* a) { return n == a; }) == std::end (allowed))
                throw ValidationError ("acoustic model input '" + n + "' is not supported");
        for (const char* req : { "tokens", "durations", "f0" })
            if (acoustic.indexOfInput (req) < 0) throw ValidationError (std::string ("acoustic model has no '") + req + "' input");
        if (const int si = acoustic.indexOfInput ("spk_embed"); si >= 0) {
            if (speaker.empty()) throw ValidationError ("acoustic model needs a speaker embedding but the voice has none");
            const auto& sh = acoustic.inputShapes[static_cast<std::size_t> (si)];
            if (sh.size() >= 3 && sh.back() > 0 && static_cast<std::size_t> (sh.back()) != speaker.size())
                throw ValidationError ("speaker embedding has " + std::to_string (speaker.size()) + " values, the model expects " + std::to_string (sh.back()));
        }
        for (const auto& n : vocoder.inputNames)
            if (n != "mel" && n != "f0") throw ValidationError ("vocoder input '" + n + "' is not supported");
        if (vocoder.indexOfInput ("mel") < 0) throw ValidationError ("vocoder model has no 'mel' input");
    }

    int sampleRate() const override { return 44100; }
    int hopSize() const override { return kHop; }

    std::vector<float> render (const std::vector<PhonemeSpan>& spans, const std::vector<float>& f0In, const std::atomic<bool>& cancel) override
    {
        const auto dur = spansToFrameDurations (spans, kFrameRate);
        std::int64_t total = 0;
        for (auto d : dur) total += d;
        if (static_cast<std::int64_t> (f0In.size()) != total)
            throw ValidationError ("f0 has " + std::to_string (f0In.size()) + " frames, the spans need " + std::to_string (total));
        const std::size_t ns = spans.size();

        // Unvoiced frames take the nearest voiced value (ties: the earlier frame).
        std::vector<float> f0 (f0In);
        {
            std::vector<std::int64_t> prev (f0.size(), -1), next (f0.size(), -1);
            std::int64_t last = -1;
            for (std::size_t i = 0; i < f0.size(); ++i) { if (f0In[i] > 0.0f) last = static_cast<std::int64_t> (i); prev[i] = last; }
            last = -1;
            for (std::size_t i = f0.size(); i-- > 0;) { if (f0In[i] > 0.0f) last = static_cast<std::int64_t> (i); next[i] = last; }
            if (f0.empty() || (prev.back() < 0)) throw ValidationError ("no voiced frame in f0");
            for (std::size_t i = 0; i < f0.size(); ++i) {
                if (f0In[i] > 0.0f) continue;
                const auto p = prev[i], n = next[i];
                const auto ii = static_cast<std::int64_t> (i);
                std::int64_t pick;
                if (p < 0) pick = n; else if (n < 0) pick = p; else pick = (ii - p <= n - ii) ? p : n;
                f0[i] = f0In[static_cast<std::size_t> (pick)];
            }
        }

        std::vector<std::int64_t> b (ns + 1, 0);
        for (std::size_t k = 0; k < ns; ++k) b[k + 1] = b[k] + dur[k];

        // Token ids (validated up front); long rests are not tokenised.
        std::vector<bool> longRest (ns, false);
        std::vector<Tok> tok (ns);
        for (std::size_t k = 0; k < ns; ++k) {
            if (spans[k].phoneme == "SP" && dur[k] >= kRestFrames) { longRest[k] = true; continue; }
            tok[k] = lookup (spans[k].phoneme);
        }

        std::vector<std::pair<std::size_t, std::size_t>> runs;
        std::size_t start = 0;
        bool open = false;
        for (std::size_t k = 0; k < ns; ++k) {
            if (longRest[k]) { if (open) { runs.emplace_back (start, k - 1); open = false; } }
            else if (! open) { start = k; open = true; }
        }
        if (open) runs.emplace_back (start, ns - 1);

        std::vector<std::pair<std::size_t, std::size_t>> parts;
        for (const auto& r : runs) split (spans, b, r.first, r.second, parts);

        std::vector<float> out (static_cast<std::size_t> (total) * kHop, 0.0f);
        const bool debug = [] { const char* e = std::getenv ("SINGVST_DEBUG_RUNS"); return e != nullptr && std::string (e) == "1"; }();
        int partNo = 0;
        for (const auto& p : parts) {
            renderPart (spans, dur, b, tok, f0, p.first, p.second, out, cancel);
            if (debug) std::fprintf (stderr, "guide part %d: frames %lld\n", partNo, static_cast<long long> (b[p.second + 1] - b[p.first]));
            ++partNo;
        }
        return out;
    }

private:
    Tok lookup (const std::string& p) const
    {
        if (const auto it = vocab.find (p); it != vocab.end()) return { it->second, 0 };
        if (const auto it = vocab.find (language + "/" + p); it != vocab.end()) {
            const auto l = langs.find (language);
            return { it->second, l == langs.end() ? 0 : l->second };
        }
        throw ValidationError ("unknown phoneme '" + p + "'");
    }

    static void split (const std::vector<PhonemeSpan>& spans, const std::vector<std::int64_t>& b, std::size_t r0, std::size_t r1,
                       std::vector<std::pair<std::size_t, std::size_t>>& parts)
    {
        if (b[r1 + 1] - b[r0] <= kMaxPartFrames || r0 == r1) { parts.emplace_back (r0, r1); return; }
        std::size_t cut = 0;   // first span of the later part
        std::int64_t bestDur = -1;
        for (std::size_t k = r0 + 1; k < r1; ++k)   // longest internal SP; it stays whole in the earlier part
            if (spans[k].phoneme == "SP" && b[k + 1] - b[k] > bestDur) { bestDur = b[k + 1] - b[k]; cut = k + 1; }
        if (bestDur < 0) {
            const double mid = (static_cast<double> (b[r0]) + static_cast<double> (b[r1 + 1])) / 2.0;
            double best = 1e300, bestAny = 1e300;
            std::size_t anyCut = r0 + 1;
            for (std::size_t j = r0 + 1; j <= r1; ++j) {
                const double dist = std::abs (static_cast<double> (b[j]) - mid);
                if (dist < bestAny) { bestAny = dist; anyCut = j; }
                if (! isVowel (spans[j].phoneme) && dist < best) { best = dist; cut = j; }
            }
            if (cut == 0) cut = anyCut;
        }
        split (spans, b, r0, cut - 1, parts);
        split (spans, b, cut, r1, parts);
    }

    void renderPart (const std::vector<PhonemeSpan>& spans, const std::vector<std::int64_t>& dur, const std::vector<std::int64_t>& b,
                     const std::vector<Tok>& tok, const std::vector<float>& f0, std::size_t r0, std::size_t r1, std::vector<float>& out,
                     const std::atomic<bool>& cancel)
    {
        (void) spans;
        const std::int64_t a = b[r0], z = b[r1 + 1];
        const std::int64_t sp = vocab.at ("SP");
        std::vector<std::int64_t> tokens { sp }, durs { kPadFrames }, lang { 0 };
        for (std::size_t k = r0; k <= r1; ++k) { tokens.push_back (tok[k].id); durs.push_back (dur[k]); lang.push_back (tok[k].lang); }
        tokens.push_back (sp); durs.push_back (kPadFrames); lang.push_back (0);
        std::vector<float> pf;
        pf.reserve (static_cast<std::size_t> (z - a + 2 * kPadFrames));
        pf.insert (pf.end(), static_cast<std::size_t> (kPadFrames), f0[static_cast<std::size_t> (a)]);
        pf.insert (pf.end(), f0.begin() + a, f0.begin() + z);
        pf.insert (pf.end(), static_cast<std::size_t> (kPadFrames), f0[static_cast<std::size_t> (z - 1)]);
        const std::int64_t T = static_cast<std::int64_t> (pf.size()), n = static_cast<std::int64_t> (tokens.size());

        Ort::MemoryInfo mem = Ort::MemoryInfo::CreateCpu (OrtArenaAllocator, OrtMemTypeDefault);
        std::deque<std::vector<float>> fstore;
        std::deque<std::vector<std::int64_t>> istore;
        std::vector<Ort::Value> inputs;
        std::vector<const char*> names;
        const auto addF = [&] (const std::string& name, std::vector<float>&& data, std::vector<std::int64_t> shape) {
            fstore.push_back (std::move (data));
            names.push_back (name.c_str());
            inputs.push_back (Ort::Value::CreateTensor<float> (mem, fstore.back().data(), fstore.back().size(), shape.data(), shape.size()));
        };
        const auto addI = [&] (const std::string& name, std::vector<std::int64_t>&& data, std::vector<std::int64_t> shape) {
            istore.push_back (std::move (data));
            names.push_back (name.c_str());
            inputs.push_back (Ort::Value::CreateTensor<std::int64_t> (mem, istore.back().data(), istore.back().size(), shape.data(), shape.size()));
        };
        // A scalar at the rank (0 or 1) and element type the model declares (C-041).
        const auto addScalar = [&] (std::size_t idx, const std::string& name, double v) {
            const auto& sh = acoustic.inputShapes[idx];
            std::vector<std::int64_t> shape;
            if (! sh.empty()) shape.push_back (1);
            if (acoustic.inputTypes[idx] == ONNX_TENSOR_ELEMENT_DATA_TYPE_FLOAT) addF (name, { static_cast<float> (v) }, shape);
            else addI (name, { static_cast<std::int64_t> (std::llround (v)) }, shape);
        };

        bool hasSpeedup = acoustic.indexOfInput ("speedup") >= 0;
        for (std::size_t i = 0; i < acoustic.inputNames.size(); ++i) {
            const std::string& nm = acoustic.inputNames[i];
            if (nm == "tokens") addI (nm, std::vector<std::int64_t> (tokens), { 1, n });
            else if (nm == "durations") addI (nm, std::vector<std::int64_t> (durs), { 1, n });
            else if (nm == "f0") addF (nm, std::vector<float> (pf), { 1, T });
            else if (nm == "gender") addF (nm, std::vector<float> (static_cast<std::size_t> (T), 0.0f), { 1, T });
            else if (nm == "velocity") addF (nm, std::vector<float> (static_cast<std::size_t> (T), 1.0f), { 1, T });
            else if (nm == "spk_embed") {
                std::vector<float> e;
                e.reserve (static_cast<std::size_t> (T) * speaker.size());
                for (std::int64_t t = 0; t < T; ++t) e.insert (e.end(), speaker.begin(), speaker.end());
                addF (nm, std::move (e), { 1, T, static_cast<std::int64_t> (speaker.size()) });
            } else if (nm == "languages") addI (nm, std::vector<std::int64_t> (lang), { 1, n });
            else if (nm == "steps") addScalar (i, nm, steps);
            else if (nm == "depth") {
                if (! hasSpeedup) addScalar (i, nm, acoustic.inputTypes[i] == ONNX_TENSOR_ELEMENT_DATA_TYPE_FLOAT ? depth : depth * 1000.0);
                else {
                    std::int64_t d = std::llround (depth * 1000.0);
                    const std::int64_t su = std::max<std::int64_t> (1, d / steps);
                    d = d / su * su;
                    addScalar (i, nm, static_cast<double> (d));
                }
            } else if (nm == "speedup") {
                std::int64_t su;
                if (acoustic.indexOfInput ("depth") >= 0) {
                    std::int64_t d = std::llround (depth * 1000.0);
                    su = std::max<std::int64_t> (1, d / steps);
                } else {
                    su = 1;
                    for (std::int64_t x = 1; x <= 1000; ++x) if (1000 % x == 0 && x <= 1000 / steps) su = x;
                }
                addScalar (i, nm, static_cast<double> (su));
            }
        }
        auto melOut = ortutil::runWatched (acoustic, cancel, names, inputs);

        // Vocoder: mel straight from the acoustic output, plus the padded f0.
        std::vector<Ort::Value> vin;
        std::vector<const char*> vnames;
        std::vector<float> vf0 (pf);
        const std::vector<std::int64_t> f0shape { 1, T };
        for (const auto& nm : vocoder.inputNames) {
            vnames.push_back (nm.c_str());
            if (nm == "mel") vin.push_back (std::move (melOut.front()));
            else vin.push_back (Ort::Value::CreateTensor<float> (mem, vf0.data(), vf0.size(), f0shape.data(), f0shape.size()));
        }
        auto wavOut = ortutil::runWatched (vocoder, cancel, vnames, vin);
        const auto count = wavOut.front().GetTensorTypeAndShapeInfo().GetElementCount();
        const std::size_t want = static_cast<std::size_t> (T) * kHop;
        if (count != want) throw ValidationError ("vocoder returned " + std::to_string (count) + " samples, expected " + std::to_string (want));
        const float* wav = wavOut.front().GetTensorData<float>();
        std::copy (wav + kPadFrames * kHop, wav + count - kPadFrames * kHop, out.begin() + a * kHop);
    }

    Ort::Env env;
    Model acoustic, vocoder;
    std::map<std::string, std::int64_t> vocab, langs;
    std::vector<float> speaker;
    int steps;
    double depth;
    std::string language;
};
} // namespace

std::unique_ptr<GuideEngine> GuideEngine::load (const VoiceManifest& m, const std::filesystem::path& dir)
{
    if (! ortRuntimeLoaded()) throw ValidationError ("ONNX Runtime is not loaded; call loadOrtRuntime first");
    return std::make_unique<GuideImpl> (m, dir);
}

} // namespace singvst
