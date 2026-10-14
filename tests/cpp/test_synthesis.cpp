// FROZEN — DO NOT MODIFY. Frozen by plan Phase 2E (tests/FROZEN_MANIFEST.sha256). Rules: plan/DECISIONS.md. Change only via TEST_CHALLENGE.md.
#include <catch2/catch_test_macros.hpp>
#include <catch2/matchers/catch_matchers_floating_point.hpp>
#include <cmath>
#include <limits>
#include "singvst/errors.hpp"
#include "singvst/synthesis.hpp"
using namespace singvst;
using Catch::Matchers::WithinAbs;
using Catch::Matchers::WithinRel;

static NoteAssignment na (double s, double e, int midi, Phones p, bool ext = false) { return { { s, e, midi }, std::move (p), ext }; }
struct Exp { const char* ph; double start, end; };
/** Checks spans against an expected list (absolute tolerance 1e-9 s) and that they are contiguous. */
static void checkSpans (const std::vector<PhonemeSpan>& got, const std::vector<Exp>& exp)
{
    REQUIRE (got.size() == exp.size());
    for (size_t i = 0; i < exp.size(); ++i) {
        INFO ("span " << i);
        CHECK (got[i].phoneme == exp[i].ph);
        CHECK_THAT (got[i].startSec, WithinAbs (exp[i].start, 1e-9));
        CHECK_THAT (got[i].endSec, WithinAbs (exp[i].end, 1e-9));
        if (i > 0) CHECK (got[i].startSec == got[i - 1].endSec);
    }
}

TEST_CASE ("T-019 midiToHz: A4 = MIDI 69 = 440 Hz, 0 cents from 12-TET across the MIDI range (D-007, PK-32, PK-36)", "[synthesis]") {
    CHECK_THAT (midiToHz (69), WithinRel (440.0, 1e-15));
    CHECK_THAT (midiToHz (57), WithinRel (220.0, 1e-15));
    CHECK_THAT (midiToHz (81), WithinRel (880.0, 1e-15));
    CHECK_THAT (midiToHz (60), WithinRel (261.6255653005986, 1e-13));
    for (int m = 0; m <= 127; ++m) {
        INFO ("MIDI " << m << " -> " << midiToHz (m) << " Hz");
        CHECK_THAT (1200.0 * std::log2 (midiToHz (m) / 440.0) - 100.0 * (m - 69), WithinAbs (0.0, 1e-9));
    }
}

TEST_CASE ("T-020 layout: the next onset is taken from the end of the previous note (D-007)", "[synthesis]") {
    checkSpans (layoutPhonemes ({ na (0, 1, 60, { "hh", "ah" }), na (1, 2, 62, { "l", "ow" }) }, 120.0, 0.06),
                { { "hh", 0, 0.06 }, { "ah", 0.06, 0.44 }, { "l", 0.44, 0.5 }, { "ow", 0.5, 1.0 } });
}

TEST_CASE ("T-021 layout: onsets and codas clamp to 40 % of a segment; a rest becomes one SP span (D-007)", "[synthesis]") {
    checkSpans (layoutPhonemes ({ na (0, 0.2, 60, { "l", "aa" }), na (0.2, 1, 62, { "s", "t", "r", "ah", "ng", "k", "th" }), na (2, 3, 64, { "aa" }) }, 120.0),
                { { "l", 0, 0.04 }, { "aa", 0.04, 0.06 }, { "s", 0.06, 0.06 + 0.04 / 3 }, { "t", 0.06 + 0.04 / 3, 0.06 + 0.08 / 3 }, { "r", 0.06 + 0.08 / 3, 0.1 },
                  { "ah", 0.1, 0.34 }, { "ng", 0.34, 0.34 + 0.16 / 3 }, { "k", 0.34 + 0.16 / 3, 0.34 + 0.32 / 3 }, { "th", 0.34 + 0.32 / 3, 0.5 },
                  { "SP", 0.5, 1.0 }, { "aa", 1.0, 1.5 } });
}

TEST_CASE ("T-022 layout: a vowel-less syllable keeps the next onset; head + tail scale to 80 %; preconditions (D-007)", "[synthesis]") {
    checkSpans (layoutPhonemes ({ na (0, 1, 60, { "hh", "m" }), na (1, 2, 62, { "hh", "ah" }) }, 120.0),
                { { "hh", 0, 0.22 }, { "m", 0.22, 0.44 }, { "hh", 0.44, 0.5 }, { "ah", 0.5, 1.0 } });
    // note 1 (0.1 s): head 0.04 + coda 0.04 + next onset 0.04 = 0.12 > 0.08 -> all scaled by 2/3
    checkSpans (layoutPhonemes ({ na (0, 0.2, 60, { "s", "t", "r", "eh", "ng", "k", "th" }), na (0.2, 1.0, 62, { "s", "t", "ah" }) }, 120.0),
                { { "s", 0, 0.08 / 9 }, { "t", 0.08 / 9, 0.16 / 9 }, { "r", 0.16 / 9, 0.24 / 9 }, { "eh", 0.24 / 9, 0.24 / 9 + 0.02 },
                  { "ng", 0.24 / 9 + 0.02, 0.32 / 9 + 0.02 }, { "k", 0.32 / 9 + 0.02, 0.40 / 9 + 0.02 }, { "th", 0.40 / 9 + 0.02, 0.48 / 9 + 0.02 },
                  { "s", 0.48 / 9 + 0.02, 0.48 / 9 + 0.02 + 0.04 / 3 }, { "t", 0.48 / 9 + 0.02 + 0.04 / 3, 0.1 }, { "ah", 0.1, 0.5 } });
    CHECK (layoutPhonemes ({}, 120.0).empty());
    CHECK_THROWS_AS (layoutPhonemes ({ na (0, 2, 60, { "aa" }), na (1, 3, 62, { "aa" }) }, 120.0), ValidationError);   // overlap
    CHECK_THROWS_AS (layoutPhonemes ({ na (1, 1, 60, { "aa" }) }, 120.0), ValidationError);                             // zero length
    CHECK_THROWS_AS (layoutPhonemes ({ na (0, 1, 60, {}) }, 120.0), ValidationError);                                   // no phones
}

TEST_CASE ("T-023 f0Curve: steady pitch, unvoiced rests, cosine portamento in log frequency for legato notes (D-007)", "[synthesis]") {
    const auto f = f0Curve ({ na (0, 1, 69, { "aa" }), na (1, 2, 81, { "aa" }), na (3, 4, 69, { "aa" }) }, 60.0, 100.0, 4.0, 0.1, 0.0);
    REQUIRE (f.size() == 400);
    CHECK_THAT (f[50], WithinRel (440.0f, 1e-6f));
    CHECK_THAT (f[100], WithinRel (440.0f, 1e-6f));          // portamento starts at the previous pitch
    CHECK_THAT (f[105], WithinRel (622.2539674f, 1e-6f));    // halfway: geometric mean of 440 and 880
    CHECK_THAT (f[110], WithinRel (880.0f, 1e-6f));
    CHECK_THAT (f[150], WithinRel (880.0f, 1e-6f));
    CHECK (f[250] == 0.0f);                                  // rest
    CHECK_THAT (f[300], WithinRel (440.0f, 1e-6f));          // after a rest: no portamento
}

TEST_CASE ("T-024 f0Curve: frame count is ceil(total*fr - 1e-9); vibrato depth in cents, phase 0 at the note start (D-007, PK-27)", "[synthesis]") {
    const std::vector<NoteAssignment> one { na (0, 1, 69, { "aa" }) };
    CHECK (f0Curve (one, 120.0, 100.0, 0.5).size() == 50);
    CHECK (f0Curve (one, 120.0, 100.0, 0.501).size() == 51);
    CHECK (f0Curve (one, 120.0, 100.0, 0.5 + 1e-12).size() == 50);
    const auto v = f0Curve ({ na (0, 4, 69, { "aa" }) }, 60.0, 1000.0, 4.0, 0.0, 100.0, 5.0);
    double hi = -1e9, lo = 1e9;
    for (float x : v) { REQUIRE (x > 0.0f); const double c = 1200.0 * std::log2 (x / 440.0); hi = std::max (hi, c); lo = std::min (lo, c); }
    CHECK_THAT (hi, WithinAbs (100.0, 0.01));
    CHECK_THAT (lo, WithinAbs (-100.0, 0.01));
    CHECK_THAT (v[0], WithinRel (440.0f, 1e-6f));
    CHECK_THAT (v[50], WithinRel (466.1637615f, 1e-6f));    // t = 0.05 s: sin(pi/2) = 1 -> +100 cents
}

TEST_CASE ("T-025 rvcCoarsePitch matches RVC get_f0 bins (C-021, D-007)", "[synthesis]") {
    const std::vector<std::pair<double, int>> table { { 0, 1 }, { -5, 1 }, { 50, 1 }, { 100, 20 }, { 220, 60 }, { 261.6255653005986, 73 }, { 330, 93 },
        { 440, 122 }, { 523.25, 143 }, { 660, 174 }, { 880, 217 }, { 1046.5, 246 }, { 1100, 255 }, { 2000, 255 } };
    for (const auto& [hz, bin] : table) { INFO (hz << " Hz"); CHECK (rvcCoarsePitch (hz) == bin); }
    int prev = 1;
    for (double hz = 50.0; hz <= 1100.0; hz += 0.5) { const int b = rvcCoarsePitch (hz); CHECK (b >= prev); prev = b; }
}

TEST_CASE ("T-026 spansToFrameDurations: bounded cumulative rounding, exact total, every phoneme >= 1 frame (D-007)", "[synthesis]") {
    CHECK (spansToFrameDurations ({ { "SP", 0, 0.0101 }, { "hh", 0.0101, 0.0102 }, { "ah", 0.0102, 1.0 } }, 44100.0 / 512.0)
           == std::vector<std::int64_t> { 1, 1, 84 });
    std::vector<PhonemeSpan> tail { { "a", 0, 0.5 } };
    for (int i = 0; i < 5; ++i) tail.push_back ({ "x", 0.5 + i * 1e-4, 0.5 + (i + 1) * 1e-4 });
    CHECK (spansToFrameDurations (tail, 100.0) == std::vector<std::int64_t> { 45, 1, 1, 1, 1, 1 });   // total 50, not 55
    CHECK_THROWS_AS (spansToFrameDurations ({ { "a", 0, 0.01 }, { "b", 0.01, 0.015 }, { "c", 0.015, 0.02 } }, 100.0), ValidationError);
    CHECK_THROWS_AS (spansToFrameDurations ({}, 100.0), ValidationError);
}

TEST_CASE ("T-027 softClip and peakAbs (D-021, PK-30)", "[synthesis]") {
    CHECK (softClip (0.5f) == 0.5f);
    CHECK (softClip (-0.784f) == -0.784f);
    CHECK_THAT (softClip (1.0f), WithinAbs (0.9410412542, 1e-6));
    CHECK_THAT (softClip (-1.0f), WithinAbs (-0.9410412542, 1e-6));
    CHECK_THAT (softClip (2.0f), WithinAbs (0.9799983986, 1e-6));
    CHECK (softClip (100.0f) <= 0.98f);
    CHECK (softClip (100.0f) > 0.979f);
    CHECK_THAT (softClip (1.0f, 0.5f), WithinAbs (0.4999987712, 1e-6));
    CHECK (softClip (std::numeric_limits<float>::quiet_NaN()) == 0.0f);
    CHECK (softClip (std::numeric_limits<float>::infinity()) == 0.0f);
    float prev = -1.0f;
    for (float x = -4.0f; x <= 4.0f; x += 0.001f) { const float y = softClip (x); CHECK (y >= prev); CHECK (std::abs (y) <= 0.98f); prev = y; }
    CHECK (peakAbs ({}) == 0.0f);
    CHECK (peakAbs ({ -0.7f, 0.3f }) == 0.7f);
}
