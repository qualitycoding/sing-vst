// FROZEN — DO NOT MODIFY. Frozen by plan Phase 2E (tests/FROZEN_MANIFEST.sha256). Rules: plan/DECISIONS.md. Change only via TEST_CHALLENGE.md.
// Pre-mortem round 3, R-072: a take rendered at one rate plays at another host rate through a resampled copy (D-010, D-038).
#include <catch2/catch_test_macros.hpp>
#include "singvst/engine.hpp"
#include "singvst/errors.hpp"
#include "singvst/synthesis.hpp"
#include "singvst/take_cache.hpp"
using namespace singvst;

TEST_CASE ("T-071 resampleTake: resampled samples, new rate and peak; timing and hash kept; identity at the same rate (D-038)", "[cache]") {
    RenderedTake t; t.startBeat = 3.25; t.bpm = 101.5; t.sampleRate = 48000; t.contentHash = 0x1234'5678'9abc'def0ull;
    for (int i = 0; i < 48000; ++i) t.samples.push_back (i < 24000 ? 0.5f : -0.25f);
    t.unclippedPeak = 0.5f;
    const auto r = resampleTake (t, 44100);
    CHECK (r.sampleRate == 44100);
    CHECK (r.samples == resample (t.samples, 48000, 44100));
    CHECK (r.samples.size() == 44100);
    CHECK (r.unclippedPeak == peakAbs (r.samples));
    CHECK (r.startBeat == t.startBeat);
    CHECK (r.bpm == t.bpm);
    CHECK (r.contentHash == t.contentHash);
    const auto same = resampleTake (t, 48000);
    CHECK (same.samples == t.samples);
    CHECK (same.sampleRate == 48000);
    CHECK (same.unclippedPeak == t.unclippedPeak);
    CHECK_THROWS_AS (resampleTake (t, 0), ValidationError);
    CHECK_THROWS_AS (resampleTake (t, -44100), ValidationError);
}
