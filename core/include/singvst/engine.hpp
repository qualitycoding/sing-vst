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
        The engine adds 8 "SP" frames before and after (C-038) and trims them, so output length == frames * hopSize().
        Not bit-reproducible: the acoustic model samples its own noise (C-040). Throws ValidationError (bad input, unknown
        phoneme), Cancelled. */
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
        T * sampleRate()/100 where T = min(f0 frames, 2 * content frames). The synthesiser's prior noise is generated from seed
        by D-012 (SplitMix64 + Box-Muller), so output is deterministic for a given seed on one platform. */
    virtual std::vector<float> convert (const std::vector<float>& guide, int guideSampleRate, const std::vector<float>& f0Hz100fps,
                                        std::uint64_t seed, const std::atomic<bool>& cancel) = 0;
    virtual int sampleRate() const = 0;
};

/** Windowed-sinc resampler (D-011). Output length = round(in.size() * toRate / fromRate); identity when the rates match. */
std::vector<float> resample (const std::vector<float>& in, int fromRate, int toRate);

} // namespace singvst
