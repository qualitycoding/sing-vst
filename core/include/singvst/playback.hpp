// Interface frozen by plan D-003; rules in D-009, D-010, D-022.
#pragma once
#include <atomic>
#include <cstddef>
#include <cstdint>
#include <memory>
#include <mutex>
#include <optional>
#include <string>
#include <string_view>
#include <utility>
#include <vector>
#include "singvst/align.hpp"
#include "singvst/lyrics.hpp"

namespace singvst {

struct RenderedTake {
    double startBeat = 0.0;     // host PPQ of sample 0 (= first note's start)
    double bpm = 120.0;         // tempo the take was rendered at
    int sampleRate = 48000;     // = RenderParams::outputSampleRate
    std::vector<float> samples; // raw (unclipped) mono audio
    float unclippedPeak = 0.0f; // peakAbs(samples)
    std::uint64_t contentHash = 0;
};

/** Sample index into the take for a host PPQ position; nullopt when outside [0, samples.size()) or when
    |hostBpm - take.bpm| > tolBpm (the take is stale for this tempo). */
std::optional<std::int64_t> takeSampleAt (const RenderedTake& take, double hostPpq, double hostBpm, double tolBpm = 0.1);

/** Fills out[0..numSamples) for one audio block (D-022): sample i is at PPQ hostPpq + i*hostBpm/(60*hostSampleRate);
    value = softClip(gainLinear * take.samples[k]) when playing, take != nullptr and takeSampleAt gives k at the take's own
    rate (nearest sample, k = floor((ppq - startBeat)*60/bpm*take.sampleRate + 0.5)); else 0. No allocation, no locks. */
void renderBlock (const RenderedTake* take, bool playing, double hostPpq, double hostBpm, double hostSampleRate,
                  float gainLinear, float* out, int numSamples) noexcept;

struct RenderParams {
    std::string voiceId;
    double bpm = 120.0;
    int outputSampleRate = 48000;
    bool conversionEnabled = true;
    double portamentoSec = 0.06;
    double vibratoCents = 0.0;
    std::uint64_t seed = 0;
    bool operator== (const RenderParams&) const = default;
};

/** Deterministic FNV-1a-64 over the canonical serialisation in D-009. */
std::uint64_t phraseHash (const std::vector<Note>& notes, const std::vector<LyricToken>& tokens, const RenderParams& params);

/** Records host MIDI during a capture pass (D-010). Positions are host PPQ. */
class CaptureRecorder {
public:
    void noteOn (double ppq, int midiNote);
    void noteOff (double ppq, int midiNote);
    /** Closes held notes at endPpq and returns all notes captured so far, sorted by (start, pitch). */
    std::vector<Note> finish (double endPpq);
    void clear();
private:
    std::vector<Note> done;
    std::vector<std::pair<int, double>> held;
};

struct PluginState {
    int version = 1;
    std::string lyrics;
    std::string voicePath;
    std::vector<Note> notes;
    RenderParams params;
    double outputGainDb = 0.0;
    bool operator== (const PluginState&) const = default;
};

std::string toJson (const PluginState& s);
/** Throws ValidationError on malformed JSON, a missing field, or version != 1. */
PluginState pluginStateFromJson (std::string_view json);

/** Single-writer / single-reader hand-off of the current take to the audio thread (D-022). acquire() and release() are
    wait-free and never allocate or free; publish() and collect() must not be called on the audio thread. */
class TakeSlot {
public:
    TakeSlot();
    ~TakeSlot();
    TakeSlot (const TakeSlot&) = delete;
    TakeSlot& operator= (const TakeSlot&) = delete;
    void publish (std::unique_ptr<RenderedTake> take);  // retires the previous current take
    const RenderedTake* acquire() noexcept;              // audio thread: pointer stays valid until release()
    void release() noexcept;                             // audio thread
    std::size_t collect();                               // frees retired takes the reader is not using; returns the number freed
    std::size_t retiredCount() const;
private:
    std::atomic<RenderedTake*> current { nullptr };
    std::atomic<RenderedTake*> inUse { nullptr };
    std::vector<RenderedTake*> retired;
    mutable std::mutex writerMutex;                      // writer side only; never taken by acquire()/release()
};

} // namespace singvst
