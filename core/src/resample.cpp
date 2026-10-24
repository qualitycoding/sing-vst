// Windowed-sinc resampler (D-011): Kaiser beta 8.6, cutoff 0.95*min(from,to)/2, 32 zero crossings of the cutoff sinc.
#include "singvst/engine.hpp"
#include <cmath>
#include <numeric>

namespace singvst {
namespace {
const double kPi = std::acos (-1.0);

double besselI0 (double x)
{
    double sum = 1.0, term = 1.0;
    const double q = x * x / 4.0;
    for (int k = 1; k < 200; ++k) {
        term *= q / (static_cast<double> (k) * k);
        sum += term;
        if (term < sum * 1e-17) break;
    }
    return sum;
}

struct Kernel {
    double fc, ratio, width, i0beta;
    explicit Kernel (int from, int to)
        : fc (0.95 * std::min (from, to) / 2.0), ratio (2.0 * fc / from), width (32.0 * from / (2.0 * fc)), i0beta (besselI0 (8.6)) {}
    double operator() (double d) const
    {
        if (std::abs (d) > width) return 0.0;
        const double x = ratio * d;
        const double sinc = std::abs (x) < 1e-12 ? 1.0 : std::sin (kPi * x) / (kPi * x);
        const double u = 1.0 - (d / width) * (d / width);
        return ratio * sinc * besselI0 (8.6 * std::sqrt (u > 0.0 ? u : 0.0)) / i0beta;
    }
};
} // namespace

std::vector<float> resample (const std::vector<float>& in, int fromRate, int toRate)
{
    if (fromRate == toRate) return in;
    const std::int64_t n = static_cast<std::int64_t> (in.size());
    const std::int64_t m = (2 * n * toRate + fromRate) / (2 * static_cast<std::int64_t> (fromRate));   // round half away from zero
    std::vector<float> out (static_cast<std::size_t> (m), 0.0f);
    if (n == 0 || m == 0) return out;

    const Kernel kernel (fromRate, toRate);
    const std::int64_t g = std::gcd<std::int64_t, std::int64_t> (fromRate, toRate);
    const std::int64_t qStep = fromRate / g, phases = toRate / g;   // t(k) = k*qStep/phases input samples
    const std::int64_t reach = static_cast<std::int64_t> (std::ceil (kernel.width)) + 1;
    const std::int64_t taps = 2 * reach + 2;                         // offsets -reach .. reach+1 around floor(t)

    // Polyphase table: weights for input index floor(t) + o, o in [-reach, reach+1].
    std::vector<double> table;
    const bool tabled = phases <= 4096;
    if (tabled) {
        table.resize (static_cast<std::size_t> (phases * taps));
        for (std::int64_t p = 0; p < phases; ++p)
            for (std::int64_t o = -reach; o <= reach + 1; ++o)
                table[static_cast<std::size_t> (p * taps + (o + reach))] = kernel (static_cast<double> (p) / static_cast<double> (phases) - static_cast<double> (o));
    }

    std::vector<double> local (static_cast<std::size_t> (taps));
    for (std::int64_t k = 0; k < m; ++k) {
        const std::int64_t num = k * qStep;
        const std::int64_t base = num / phases, p = num % phases;
        const double* w;
        if (tabled) w = &table[static_cast<std::size_t> (p * taps)];
        else {
            for (std::int64_t o = -reach; o <= reach + 1; ++o)
                local[static_cast<std::size_t> (o + reach)] = kernel (static_cast<double> (p) / static_cast<double> (phases) - static_cast<double> (o));
            w = local.data();
        }
        double acc = 0.0;
        const std::int64_t lo = std::max<std::int64_t> (-reach, -base), hi = std::min<std::int64_t> (reach + 1, n - 1 - base);
        for (std::int64_t o = lo; o <= hi; ++o) acc += static_cast<double> (in[static_cast<std::size_t> (base + o)]) * w[o + reach];
        out[static_cast<std::size_t> (k)] = static_cast<float> (acc);
    }
    return out;
}

} // namespace singvst
