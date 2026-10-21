// Interface frozen by plan D-038 (pre-mortem rounds 1 and 3, R-017, R-072); file format in D-038.
#pragma once
#include <cstdint>
#include <filesystem>
#include <optional>
#include "singvst/render.hpp"

namespace singvst {

/** File name of a cached take: 16 lower-case hex digits of contentHash + ".take". */
std::filesystem::path takeFileName (std::uint64_t contentHash);

/** Writes the take to dir/takeFileName(take.contentHash) atomically (temporary file + rename), creating dir if needed.
    Returns false on any I/O error; never throws. */
bool storeTake (const std::filesystem::path& dir, const RenderedTake& take) noexcept;

/** The take stored for contentHash, or nullopt when the file is absent, has the wrong size, magic, hash or checksum, or
    holds more than 901 s at its sample rate (900 s plus frame-rounding slack). Validates the size before allocating; never throws. */
std::optional<RenderedTake> loadTake (const std::filesystem::path& dir, std::uint64_t contentHash) noexcept;

/** A RenderFn that returns loadTake(dir, phraseHash(request)) when present; otherwise calls fn and, when the result's
    contentHash equals phraseHash(request), stores it (a failed store is ignored). Exceptions from fn propagate. */
RenderFn cachedRender (RenderFn fn, std::filesystem::path dir);

/** A copy of take at targetRate for playback at a host rate other than the render rate (D-010, R-072): samples =
    resample(take.samples, take.sampleRate, targetRate) (D-011), sampleRate = targetRate, unclippedPeak = peakAbs of the
    new samples; startBeat, bpm and contentHash unchanged. targetRate == take.sampleRate returns an identical copy;
    targetRate <= 0 throws ValidationError. Callers always resample the original take, never a resampled copy. */
RenderedTake resampleTake (const RenderedTake& take, int targetRate);

} // namespace singvst
