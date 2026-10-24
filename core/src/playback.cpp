// Host-time mapping, phrase hash, capture recorder, plugin state, TakeSlot (D-009, D-010, D-021, D-022).
#include "singvst/playback.hpp"
#include "singvst/errors.hpp"
#include "singvst/synthesis.hpp"
#include <algorithm>
#include <charconv>
#include <cmath>
#include <nlohmann/json.hpp>

namespace singvst {

std::optional<std::int64_t> takeSampleAt (const RenderedTake& take, double hostPpq, double hostBpm, double tolBpm)
{
    if (std::abs (hostBpm - take.bpm) > tolBpm) return std::nullopt;
    const double kd = std::floor ((hostPpq - take.startBeat) * 60.0 / take.bpm * take.sampleRate + 0.5);
    if (! (kd >= 0.0 && kd < static_cast<double> (take.samples.size()))) return std::nullopt;
    return static_cast<std::int64_t> (kd);
}

void renderBlock (const RenderedTake* take, bool playing, double hostPpq, double hostBpm, double hostSampleRate,
                  float gainLinear, float* out, int numSamples) noexcept
{
    const bool active = playing && take != nullptr;
    const double ppqPerSample = hostBpm / (60.0 * hostSampleRate);
    for (int i = 0; i < numSamples; ++i) {
        float v = 0.0f;
        if (active) {
            const auto k = takeSampleAt (*take, hostPpq + i * ppqPerSample, hostBpm);
            if (k) v = softClip (gainLinear * take->samples[static_cast<std::size_t> (*k)]);
        }
        out[i] = v;
    }
}

namespace {
// Locale-independent fixed formatting with 9 decimals ('.' separator), equal to C printf("%.9f").
void appendFixed9 (std::string& s, double v)
{
    char buf[400];
    const auto r = std::to_chars (buf, buf + sizeof buf, v, std::chars_format::fixed, 9);
    s.append (buf, r.ptr);
}
} // namespace

std::uint64_t phraseHash (const std::vector<Note>& notes, const std::vector<LyricToken>& tokens, const RenderParams& p)
{
    std::string s;
    for (const auto& n : notes) {
        s += "n:"; appendFixed9 (s, n.startBeat); s += ':'; appendFixed9 (s, n.endBeat); s += ':'; s += std::to_string (n.midiNote); s += ';';
    }
    for (const auto& t : tokens) {
        s += "t:"; s += std::to_string (static_cast<int> (t.kind)); s += ':'; s += t.text; s += ':';
        for (std::size_t i = 0; i < t.phonemes.size(); ++i) { if (i) s += ' '; s += t.phonemes[i]; }
        s += ':'; s += t.continuesWord ? '1' : '0'; s += ';';
    }
    s += "p:"; s += p.voiceId; s += ':'; appendFixed9 (s, p.bpm); s += ':'; s += std::to_string (p.outputSampleRate);
    s += ':'; s += p.conversionEnabled ? '1' : '0'; s += ':'; appendFixed9 (s, p.portamentoSec); s += ':'; appendFixed9 (s, p.vibratoCents);
    s += ':'; s += std::to_string (p.seed); s += ';';
    std::uint64_t h = 14695981039346656037ULL;
    for (unsigned char c : s) { h ^= c; h *= 1099511628211ULL; }
    return h;
}

void CaptureRecorder::noteOn (double ppq, int midiNote)
{
    for (auto it = held.begin(); it != held.end(); ++it)
        if (it->first == midiNote) {
            if (ppq - it->second > 1e-9) done.push_back ({ it->second, ppq, midiNote });
            held.erase (it);
            break;
        }
    held.emplace_back (midiNote, ppq);
}

void CaptureRecorder::noteOff (double ppq, int midiNote)
{
    for (auto it = held.begin(); it != held.end(); ++it)
        if (it->first == midiNote) {
            if (ppq - it->second > 1e-9) done.push_back ({ it->second, ppq, midiNote });
            held.erase (it);
            return;
        }
}

std::vector<Note> CaptureRecorder::finish (double endPpq)
{
    for (const auto& h : held)
        if (endPpq - h.second > 1e-9) done.push_back ({ h.second, endPpq, h.first });
    held.clear();
    std::stable_sort (done.begin(), done.end(), [] (const Note& a, const Note& b) {
        return a.startBeat != b.startBeat ? a.startBeat < b.startBeat : a.midiNote < b.midiNote;
    });
    return done;
}

void CaptureRecorder::clear()
{
    done.clear();
    held.clear();
}

using json = nlohmann::json;

std::string toJson (const PluginState& s)
{
    json notes = json::array();
    for (const auto& n : s.notes) notes.push_back ({ { "startBeat", n.startBeat }, { "endBeat", n.endBeat }, { "midiNote", n.midiNote } });
    json j = { { "version", s.version },
               { "lyrics", s.lyrics },
               { "voicePath", s.voicePath },
               { "notes", notes },
               { "params", { { "voiceId", s.params.voiceId }, { "bpm", s.params.bpm }, { "outputSampleRate", s.params.outputSampleRate },
                             { "conversionEnabled", s.params.conversionEnabled }, { "portamentoSec", s.params.portamentoSec },
                             { "vibratoCents", s.params.vibratoCents }, { "seed", s.params.seed } } },
               { "outputGainDb", s.outputGainDb } };
    return j.dump (-1, ' ', false, json::error_handler_t::replace);
}

PluginState pluginStateFromJson (std::string_view text)
{
    json j = json::parse (text.begin(), text.end(), nullptr, false);
    if (j.is_discarded() || ! j.is_object()) throw ValidationError ("plugin state: not a valid JSON object");
    try {
        if (j.at ("version").get<int>() != 1) throw ValidationError ("plugin state: unsupported version");
        PluginState s;
        s.version = 1;
        s.lyrics = j.at ("lyrics").get<std::string>();
        s.voicePath = j.at ("voicePath").get<std::string>();
        for (const auto& n : j.at ("notes"))
            s.notes.push_back ({ n.at ("startBeat").get<double>(), n.at ("endBeat").get<double>(), n.at ("midiNote").get<int>() });
        const auto& p = j.at ("params");
        s.params.voiceId = p.at ("voiceId").get<std::string>();
        s.params.bpm = p.at ("bpm").get<double>();
        s.params.outputSampleRate = p.at ("outputSampleRate").get<int>();
        s.params.conversionEnabled = p.at ("conversionEnabled").get<bool>();
        s.params.portamentoSec = p.at ("portamentoSec").get<double>();
        s.params.vibratoCents = p.at ("vibratoCents").get<double>();
        s.params.seed = p.at ("seed").get<std::uint64_t>();
        s.outputGainDb = j.at ("outputGainDb").get<double>();
        return s;
    } catch (const json::exception& e) {
        throw ValidationError (std::string ("plugin state: ") + e.what());
    }
}

namespace {
RenderedTake busySentinel;   // address only; never dereferenced
RenderedTake* busy() noexcept { return &busySentinel; }
} // namespace

TakeSlot::TakeSlot() = default;

TakeSlot::~TakeSlot()
{
    delete current.load();
    for (auto* r : retired) delete r;
}

void TakeSlot::publish (std::unique_ptr<RenderedTake> take)
{
    std::lock_guard<std::mutex> lock (writerMutex);
    RenderedTake* old = current.exchange (take.release());
    if (old != nullptr) retired.push_back (old);
}

const RenderedTake* TakeSlot::acquire() noexcept
{
    inUse.store (busy());
    RenderedTake* p = current.load();
    inUse.store (p);
    return p;
}

void TakeSlot::release() noexcept { inUse.store (nullptr); }

std::size_t TakeSlot::collect()
{
    std::lock_guard<std::mutex> lock (writerMutex);
    RenderedTake* u = inUse.load();
    if (u == busy()) return 0;
    std::size_t freed = 0;
    std::vector<RenderedTake*> keep;
    for (auto* r : retired) {
        if (r == u) keep.push_back (r);
        else { delete r; ++freed; }
    }
    retired.swap (keep);
    return freed;
}

std::size_t TakeSlot::retiredCount() const
{
    std::lock_guard<std::mutex> lock (writerMutex);
    return retired.size();
}

} // namespace singvst
