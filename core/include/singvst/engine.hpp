// Interface frozen by plan D-003; ONNX I/O contracts in D-012.
#pragma once
#include <atomic>
#include <cstdint>
#include <filesystem>
#include <memory>
#include <vector>
#include "singvst/errors.hpp"
#include "singvst/synthesis.hpp"
#include "singvst/voice.hpp"

namespace singvst {

class GuideEngine {
public:
    virtual ~GuideEngine() = default;
    /** Loads the DiffSinger acoustic + vocoder ONNX models, the phoneme list and the optional speaker embedding named in the
        manifest (D-012). Requires loadOrtRuntime() first. Throws ValidationError for a missing/corrupt file, an unsupported
        model input (energy, breathiness, voicing, tension), a speaker-embedding size mismatch, or no runtime. Does not re-hash files. */
    static std::unique_ptr<GuideEngine> load (const VoiceManifest& m, const std::filesystem::path& dir);
    /** Renders mono audio at sampleRate(). f0FramesHz has one value per frame and its length must equal
        sum(spansToFrameDurations(spans, sampleRate()/hopSize())); unvoiced (0) frames take the nearest voiced value.
        "SP" spans of >= 22 frames split the take into phrases and are output as exact zeros; each phrase is rendered with 8
        "SP" frames before and after (C-038), which are trimmed, so output length == frames * hopSize() (D-012).
        Not bit-reproducible: the acoustic model samples its own noise (C-040). Throws ValidationError (bad input, unknown
        phoneme, no voiced frame), Cancelled. */
    virtual std::vector<float> render (const std::vector<PhonemeSpan>& spans, const std::vector<float>& f0FramesHz,
                                       const std::atomic<bool>& cancel) = 0;
    virtual int sampleRate() const = 0;
    virtual int hopSize() const = 0;
};

class ConverterEngine {
public:
    virtual ~ConverterEngine() = default;
    /** Loads the RVC v2 synthesiser + content encoder ONNX models (D-012). Requires loadOrtRuntime() first. Throws ValidationError. */
    static std::unique_ptr<ConverterEngine> load (const VoiceManifest& m, const std::filesystem::path& dir);
    /** Converts guide audio. f0Hz100fps is the target pitch at 100 frames/s. Output mono at sampleRate(), length
        T * sampleRate()/100 where T = min(f0 frames, floor(guide samples at 16 kHz / 160)). Processed in chunks of <= 1500
        frames with <= 100 frames of context per side; the prior noise is standardNormal(seed, 192*T) for the whole take
        (D-012), so output is deterministic for a given seed on one platform and independent of chunking. */
    virtual std::vector<float> convert (const std::vector<float>& guide, int guideSampleRate, const std::vector<float>& f0Hz100fps,
                                        std::uint64_t seed, const std::atomic<bool>& cancel) = 0;
    virtual int sampleRate() const = 0;
};

/** D-012 prior noise: SplitMix64 stream from seed, Box-Muller pairs (z0 = r cos, z1 = r sin), n values, computed in double. */
std::vector<float> standardNormal (std::uint64_t seed, std::size_t n);

/** Windowed-sinc resampler (D-011). Output length = round(in.size() * toRate / fromRate); identity when the rates match. */
std::vector<float> resample (const std::vector<float>& in, int fromRate, int toRate);

} // namespace singvst
