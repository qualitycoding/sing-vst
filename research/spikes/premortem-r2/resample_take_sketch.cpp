// Planning sketch (not shipped): proves T-071 is satisfiable under D-038 (resampleTake).
#include "singvst/take_cache.hpp"
#include "singvst/engine.hpp"
#include "singvst/errors.hpp"
#include "singvst/synthesis.hpp"
#include <cmath>
namespace singvst {
std::vector<float> resample (const std::vector<float>& in, int from, int to)   // stand-in with the D-011 length rule only
{ if (from == to) return in; const auto n = (std::size_t) std::llround ((double) in.size() * to / from);
  std::vector<float> out (n); for (std::size_t i = 0; i < n; ++i) { auto j = std::min (in.size() - 1, (std::size_t) ((double) i * from / to)); out[i] = in[j]; } return out; }
float peakAbs (const std::vector<float>& x) noexcept { float p = 0; for (float v : x) p = std::max (p, std::fabs (v)); return p; }
RenderedTake resampleTake (const RenderedTake& t, int rate)
{ if (rate <= 0) throw ValidationError ("target rate must be positive"); if (rate == t.sampleRate) return t;
  RenderedTake r = t; r.samples = resample (t.samples, t.sampleRate, rate); r.sampleRate = rate; r.unclippedPeak = peakAbs (r.samples); return r; }
}
