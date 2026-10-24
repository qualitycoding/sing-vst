// Phoneme layout, pitch curve, RVC pitch bins, frame durations, output soft clip (D-007, D-021).
#include "singvst/synthesis.hpp"
#include "singvst/errors.hpp"
#include <algorithm>
#include <cmath>

namespace singvst {
namespace {
constexpr double kEpsBeat = 1e-9;
const double kPi = std::acos (-1.0);

struct Seg {
    bool isNote = false;
    double s = 0.0, e = 0.0;
    const NoteAssignment* a = nullptr;
};
using Timed = std::vector<std::pair<std::string, double>>;   // phone, duration
} // namespace

double midiToHz (double m) { return 440.0 * std::pow (2.0, (m - 69.0) / 12.0); }

std::vector<PhonemeSpan> layoutPhonemes (const std::vector<NoteAssignment>& notes, double bpm, double c)
{
    if (notes.empty()) return {};
    const double t0 = notes.front().note.startBeat;
    const auto sec = [&] (double b) { return (b - t0) * 60.0 / bpm; };
    std::vector<Seg> segs;
    for (std::size_t k = 0; k < notes.size(); ++k) {
        const auto& a = notes[k];
        const double s = sec (a.note.startBeat), e = sec (a.note.endBeat);
        if (e - s <= 0.0 || (k > 0 && a.note.startBeat < notes[k - 1].note.endBeat - kEpsBeat) || a.phonemes.empty())
            throw ValidationError ("layoutPhonemes needs sorted, non-overlapping notes of positive length with phonemes");
        if (! segs.empty() && s > segs.back().e + 1e-12) segs.push_back ({ false, segs.back().e, s, nullptr });
        segs.push_back ({ true, s, e, &a });
    }
    std::vector<Timed> head (segs.size()), tail (segs.size());
    std::vector<bool> equal (segs.size(), false);
    for (std::size_t k = 0; k < segs.size(); ++k) {
        if (! segs[k].isNote) continue;
        const auto& ph = segs[k].a->phonemes;
        std::size_t fv = ph.size();
        for (std::size_t i = 0; i < ph.size(); ++i) if (isVowel (ph[i])) { fv = i; break; }
        const double dur = segs[k].e - segs[k].s;
        if (fv == ph.size()) { equal[k] = true; continue; }
        const std::size_t onset = fv, coda = ph.size() - fv - 1;
        if (coda > 0) {
            const double tot = std::min (static_cast<double> (coda) * c, 0.4 * dur);
            for (std::size_t i = fv + 1; i < ph.size(); ++i) tail[k].push_back ({ ph[i], tot / static_cast<double> (coda) });
        }
        if (onset > 0) {
            if (k > 0) {
                const double pd = segs[k - 1].e - segs[k - 1].s;
                const double tot = std::min (static_cast<double> (onset) * c, 0.4 * pd);
                for (std::size_t i = 0; i < fv; ++i) tail[k - 1].push_back ({ ph[i], tot / static_cast<double> (onset) });
            } else {
                const double tot = std::min (static_cast<double> (onset) * c, 0.4 * dur);
                for (std::size_t i = 0; i < fv; ++i) head[k].push_back ({ ph[i], tot / static_cast<double> (onset) });
            }
        }
    }
    std::vector<PhonemeSpan> spans;
    for (std::size_t k = 0; k < segs.size(); ++k) {
        const double s = segs[k].s, e = segs[k].e, dur = e - s;
        double hsum = 0.0, tsum = 0.0;
        for (const auto& x : head[k]) hsum += x.second;
        for (const auto& x : tail[k]) tsum += x.second;
        if (segs[k].isNote && hsum + tsum > 0.8 * dur) {
            const double f = 0.8 * dur / (hsum + tsum);
            for (auto& x : head[k]) x.second *= f;
            for (auto& x : tail[k]) x.second *= f;
            hsum *= f;
            tsum *= f;
        }
        double t = s;
        for (const auto& x : head[k]) { spans.push_back ({ x.first, t, t + x.second }); t += x.second; }
        if (segs[k].isNote && equal[k]) {
            const auto& ph = segs[k].a->phonemes;
            const double step = (e - tsum - t) / static_cast<double> (ph.size());
            for (std::size_t i = 0; i < ph.size(); ++i)
                spans.push_back ({ ph[i], t + static_cast<double> (i) * step, t + static_cast<double> (i + 1) * step });
        } else {
            std::string nuc = "SP";
            if (segs[k].isNote) for (const auto& p : segs[k].a->phonemes) if (isVowel (p)) { nuc = p; break; }
            spans.push_back ({ nuc, t, e - tsum });
        }
        t = e - tsum;
        for (const auto& x : tail[k]) { spans.push_back ({ x.first, t, t + x.second }); t += x.second; }
        spans.back().endSec = e;
    }
    return spans;
}

std::vector<float> f0Curve (const std::vector<NoteAssignment>& notes, double bpm, double fr, double total,
                            double port, double vib, double vhz)
{
    const double nd = std::ceil (total * fr - 1e-9);
    const std::int64_t n = nd > 0.0 ? static_cast<std::int64_t> (nd) : 0;
    std::vector<float> out (static_cast<std::size_t> (n), 0.0f);
    if (notes.empty()) return out;
    const double t0 = notes.front().note.startBeat;
    const auto sec = [&] (double b) { return (b - t0) * 60.0 / bpm; };
    for (std::size_t k = 0; k < notes.size(); ++k) {
        const auto& a = notes[k];
        const double s = sec (a.note.startBeat), e = sec (a.note.endBeat), f = midiToHz (a.note.midiNote);
        const bool legato = k > 0 && std::abs (notes[k - 1].note.endBeat - a.note.startBeat) < kEpsBeat;
        const double fp = legato ? midiToHz (notes[k - 1].note.midiNote) : f;
        const double pw = std::min (port, e - s);
        const std::int64_t lo = std::max<std::int64_t> (0, static_cast<std::int64_t> (std::ceil (s * fr - 1e-9)));
        const std::int64_t hi = std::min<std::int64_t> (n, static_cast<std::int64_t> (std::ceil (e * fr - 1e-9)));
        for (std::int64_t i = lo; i < hi; ++i) {
            const double t = static_cast<double> (i) / fr;
            if (! (s - 1e-12 <= t && t < e - 1e-12)) continue;
            const double u = (legato && pw > 0.0) ? (t - s) / pw : 1.0;
            double hz = f;
            if (u < 1.0) hz = std::exp (std::log (fp) + (std::log (f) - std::log (fp)) * (1.0 - std::cos (kPi * u)) / 2.0);
            if (vib != 0.0) hz *= std::pow (2.0, vib * std::sin (2.0 * kPi * vhz * (t - s)) / 1200.0);
            out[static_cast<std::size_t> (i)] = static_cast<float> (hz);
        }
    }
    return out;
}

int rvcCoarsePitch (double hz)
{
    const double mmin = 1127.0 * std::log (1.0 + 50.0 / 700.0), mmax = 1127.0 * std::log (1.0 + 1100.0 / 700.0);
    double m = 1127.0 * std::log (1.0 + hz / 700.0);
    if (m > 0.0) m = (m - mmin) * 254.0 / (mmax - mmin) + 1.0;
    m = m <= 1.0 ? 1.0 : std::min (m, 255.0);
    return static_cast<int> (std::nearbyint (m));   // round half to even, as numpy rint
}

std::vector<std::int64_t> spansToFrameDurations (const std::vector<PhonemeSpan>& spans, double fr)
{
    const std::int64_t n = static_cast<std::int64_t> (spans.size());
    if (n == 0) throw ValidationError ("spansToFrameDurations: no spans");
    const std::int64_t total = static_cast<std::int64_t> (std::floor (spans.back().endSec * fr + 0.5));
    if (total < n) throw ValidationError ("spansToFrameDurations: too short for the number of spans");
    std::vector<std::int64_t> out;
    std::int64_t b = 0;
    for (std::int64_t k = 0; k < n; ++k) {
        std::int64_t nb = total;
        if (k < n - 1) {
            const auto r = static_cast<std::int64_t> (std::floor (spans[static_cast<std::size_t> (k)].endSec * fr + 0.5));
            nb = std::min (std::max (r, b + 1), total - (n - 1 - k));
        }
        out.push_back (nb - b);
        b = nb;
    }
    return out;
}

float softClip (float x, float ceiling) noexcept
{
    if (! std::isfinite (x)) return 0.0f;
    const double c = ceiling, knee = 0.8 * c, ax = std::abs (static_cast<double> (x));
    if (ax <= knee) return x;
    const double y = std::min (knee + (c - knee) * std::tanh ((ax - knee) / (c - knee)), c);
    return static_cast<float> (std::copysign (y, static_cast<double> (x)));
}

float peakAbs (const std::vector<float>& x) noexcept
{
    float p = 0.0f;
    for (float v : x) p = std::max (p, std::abs (v));
    return p;
}

} // namespace singvst
