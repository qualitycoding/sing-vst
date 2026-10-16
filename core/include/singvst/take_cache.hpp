// Interface frozen by plan D-038 (pre-mortem round 1, R-017); file format in D-038.
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
    holds more than 900 s at its sample rate. Validates the size before allocating; never throws. */
std::optional<RenderedTake> loadTake (const std::filesystem::path& dir, std::uint64_t contentHash) noexcept;

/** A RenderFn that returns loadTake(dir, phraseHash(request)) when present; otherwise calls fn and, when the result's
    contentHash equals phraseHash(request), stores it (a failed store is ignored). Exceptions from fn propagate. */
RenderFn cachedRender (RenderFn fn, std::filesystem::path dir);

} // namespace singvst
