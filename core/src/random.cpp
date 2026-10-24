// standardNormal: SplitMix64 + Box-Muller (D-012).
#include "singvst/engine.hpp"
#include <cmath>

namespace singvst {
namespace {
std::uint64_t splitmix64 (std::uint64_t& state)
{
    state += 0x9E3779B97F4A7C15ULL;
    std::uint64_t z = state;
    z = (z ^ (z >> 30)) * 0xBF58476D1CE4E5B9ULL;
    z = (z ^ (z >> 27)) * 0x94D049BB133111EBULL;
    return z ^ (z >> 31);
}
} // namespace

std::vector<float> standardNormal (std::uint64_t seed, std::size_t n)
{
    std::vector<float> out;
    out.reserve (n);
    std::uint64_t s = seed;
    const double twoPi = 2.0 * std::acos (-1.0);
    while (out.size() < n) {
        const std::uint64_t x1 = splitmix64 (s), x2 = splitmix64 (s);
        const double u1 = static_cast<double> ((x1 >> 11) + 1) * 0x1.0p-53;
        const double u2 = static_cast<double> (x2 >> 11) * 0x1.0p-53;
        const double r = std::sqrt (-2.0 * std::log (u1));
        out.push_back (static_cast<float> (r * std::cos (twoPi * u2)));
        if (out.size() < n) out.push_back (static_cast<float> (r * std::sin (twoPi * u2)));
    }
    return out;
}

} // namespace singvst
