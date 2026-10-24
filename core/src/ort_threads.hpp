// Private: the intra-op thread count used by every ONNX Runtime session, so the CLI can report exactly what the engines used (D-014).
#pragma once
#include <algorithm>
#include <cstdlib>
#include <string>
#include <thread>

namespace singvst {
/** SINGVST_ORT_THREADS (1..64) when set and valid, else hardware_concurrency clamped to [1, 8]. */
inline int ortIntraOpThreads()
{
    if (const char* e = std::getenv ("SINGVST_ORT_THREADS")) {
        char* end = nullptr;
        const long v = std::strtol (e, &end, 10);
        if (end != e && *end == '\0' && v >= 1 && v <= 64) return static_cast<int> (v);
    }
    return static_cast<int> (std::clamp (std::thread::hardware_concurrency(), 1u, 8u));
}
} // namespace singvst
