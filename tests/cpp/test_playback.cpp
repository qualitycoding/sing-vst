// FROZEN — DO NOT MODIFY. Frozen by plan Phase 2E (tests/FROZEN_MANIFEST.sha256). Rules: plan/DECISIONS.md. Change only via TEST_CHALLENGE.md.
#include <catch2/catch_test_macros.hpp>
#include <catch2/matchers/catch_matchers_floating_point.hpp>
#include <atomic>
#include <chrono>
#include <clocale>
#include <cmath>
#include <thread>
#include "helpers.hpp"
#include "singvst/errors.hpp"
#include "singvst/playback.hpp"
#include "singvst/synthesis.hpp"
using namespace singvst;
using Catch::Matchers::WithinAbs;

/** A take of n samples whose sample k has value f(k). */
template <typename F> static RenderedTake makeTake (double startBeat, double bpm, int sr, int n, F f)
{
    RenderedTake t; t.startBeat = startBeat; t.bpm = bpm; t.sampleRate = sr; t.samples.resize ((size_t) n);
    for (int k = 0; k < n; ++k) t.samples[(size_t) k] = f (k);
    t.unclippedPeak = peakAbs (t.samples); return t;
}

TEST_CASE ("T-032 takeSampleAt: nearest sample, bounds, tempo staleness (D-009)", "[playback]") {
    const auto t = makeTake (4.0, 120.0, 48000, 48000, [] (int) { return 0.0f; });   // 1 s = 2 beats
    CHECK (takeSampleAt (t, 4.0, 120.0) == std::optional<std::int64_t> (0));
    CHECK (takeSampleAt (t, 5.0, 120.0) == std::optional<std::int64_t> (24000));
    CHECK (takeSampleAt (t, 4.0 + 1.2 / 48000.0, 120.0) == std::optional<std::int64_t> (1));        // 0.6 sample rounds up
    CHECK (takeSampleAt (t, 4.0 + 0.8 / 48000.0, 120.0) == std::optional<std::int64_t> (0));        // 0.4 sample rounds down
    CHECK (takeSampleAt (t, 4.0 + 2.0 * 47999.0 / 48000.0, 120.0) == std::optional<std::int64_t> (47999));   // last sample
    CHECK_FALSE (takeSampleAt (t, 3.99, 120.0).has_value());
    CHECK_FALSE (takeSampleAt (t, 6.0, 120.0).has_value());
    CHECK (takeSampleAt (t, 5.0, 120.1) == std::optional<std::int64_t> (24000));                    // within the default 0.1 bpm
    CHECK_FALSE (takeSampleAt (t, 5.0, 120.2).has_value());
    CHECK_FALSE (takeSampleAt (t, 5.0, 121.0, 0.5).has_value());
}

TEST_CASE ("T-033 renderBlock: host-time mapping at another sample rate, gain, soft clip, silence cases (D-021, D-022)", "[playback]") {
    const auto t = makeTake (2.0, 120.0, 48000, 48000, [] (int k) { return 1e-5f * (float) k; });   // ramp 0 .. 0.48
    std::vector<float> out (64);
    renderBlock (&t, true, 2.0, 120.0, 44100.0, 1.0f, out.data(), 64);
    for (int i = 0; i < 64; ++i) {
        const auto k = (int) std::floor (i / 44100.0 * 48000.0 + 0.5);
        INFO ("i=" << i); CHECK_THAT (out[(size_t) i], WithinAbs (1e-5 * k, 1e-7));
    }
    renderBlock (&t, true, 2.0 + 2.0 * 0.4, 120.0, 48000.0, 2.0f, out.data(), 4);                // k = 19200: 2 * 0.192 = 0.384
    CHECK_THAT (out[0], WithinAbs (0.384, 1e-6));
    renderBlock (&t, true, 2.0 + 2.0 * 0.45, 120.0, 48000.0, 2.0f, out.data(), 1);               // k = 21600: 2 * 0.216 = 0.432
    CHECK_THAT (out[0], WithinAbs (0.432, 1e-6));
    renderBlock (&t, true, 2.0 + 2.0 * 0.45, 120.0, 48000.0, 4.0f, out.data(), 1);               // 0.864 > knee: soft clipped
    CHECK_THAT (out[0], WithinAbs (softClip (0.864f), 1e-6));
    CHECK (out[0] < 0.864f);
    const auto filled = [&] (const RenderedTake* tk, bool playing, double ppq, double bpm) {
        std::fill (out.begin(), out.end(), 7.0f); renderBlock (tk, playing, ppq, bpm, 48000.0, 1.0f, out.data(), 64);
        for (float v : out) if (v != 0.0f) return false;
        return true;
    };
    CHECK (filled (&t, false, 2.5, 120.0));      // transport stopped
    CHECK (filled (nullptr, true, 2.5, 120.0));  // no take
    CHECK (filled (&t, true, 2.5, 130.0));       // stale tempo
    CHECK (filled (&t, true, 0.0, 120.0));       // before the take
    CHECK (filled (&t, true, 4.0, 120.0));       // after the take
    renderBlock (&t, true, 4.0 - 2.0 * 10.0 / 48000.0, 120.0, 48000.0, 1.0f, out.data(), 20);   // last 10 samples, then silence
    CHECK_THAT (out[9], WithinAbs (1e-5 * 47999, 1e-6));
    CHECK (out[10] == 0.0f);
}

TEST_CASE ("T-034 phraseHash: golden FNV-1a value, locale-independent, sensitive to every field (D-009)", "[playback]") {
    LyricToken la = testutil::text ("la");
    RenderParams p; p.voiceId = "v1"; p.bpm = 120.0; p.outputSampleRate = 48000; p.conversionEnabled = true;
    p.portamentoSec = 0.06; p.vibratoCents = 0.0; p.seed = 0;
    const std::vector<Note> n { { 0, 1, 60 } };
    const auto h0 = phraseHash (n, { la }, p);
    CHECK (h0 == 14710552853263154277ULL);
    const char* names[] = { "de_DE.UTF-8", "de_DE.utf8", "German_Germany.1252", "de-DE" };
    bool switched = false;
    for (const char* name : names) if (std::setlocale (LC_ALL, name) != nullptr) { switched = true; break; }
    REQUIRE (switched);                                     // CI installs de_DE.UTF-8 (D-018); decimal separator is ','
    CHECK (phraseHash (n, { la }, p) == h0);
    std::setlocale (LC_ALL, "C");
    auto q = p;
    q = p; q.voiceId = "v2";              CHECK (phraseHash (n, { la }, q) != h0);
    q = p; q.bpm = 120.5;                 CHECK (phraseHash (n, { la }, q) != h0);
    q = p; q.outputSampleRate = 44100;    CHECK (phraseHash (n, { la }, q) != h0);
    q = p; q.conversionEnabled = false;   CHECK (phraseHash (n, { la }, q) != h0);
    q = p; q.portamentoSec = 0.07;        CHECK (phraseHash (n, { la }, q) != h0);
    q = p; q.vibratoCents = 1.0;          CHECK (phraseHash (n, { la }, q) != h0);
    q = p; q.seed = 1;                    CHECK (phraseHash (n, { la }, q) != h0);
    CHECK (phraseHash ({ { 0, 1, 61 } }, { la }, p) != h0);
    CHECK (phraseHash ({ { 0, 1.5, 60 } }, { la }, p) != h0);
    CHECK (phraseHash ({ { 0.25, 1, 60 } }, { la }, p) != h0);
    CHECK (phraseHash (n, { testutil::text ("lo") }, p) != h0);
    CHECK (phraseHash (n, { testutil::text ("la", true) }, p) != h0);
    CHECK (phraseHash (n, { testutil::phon ({ "la" }) }, p) != h0);
    CHECK (phraseHash (n, { la, testutil::extend() }, p) != h0);
}

TEST_CASE ("T-035 CaptureRecorder pairs note-on/off, retriggers, ignores stray offs, closes held notes (D-010)", "[playback]") {
    CaptureRecorder r;
    r.noteOn (0.0, 60); r.noteOff (1.0, 60);
    r.noteOff (1.5, 61);                      // stray: ignored
    r.noteOn (2.0, 62); r.noteOn (2.5, 62);   // retrigger closes the first at 2.5
    r.noteOn (3.0, 64);
    r.noteOn (3.0, 59);
    CHECK (r.finish (4.0) == std::vector<Note> { { 0, 1, 60 }, { 2, 2.5, 62 }, { 2.5, 4, 62 }, { 3, 4, 59 }, { 3, 4, 64 } });
    r.clear();
    CHECK (r.finish (5.0).empty());
    r.noteOn (1.0, 60); r.noteOff (1.0, 60);  // zero length: dropped
    CHECK (r.finish (2.0).empty());
}

TEST_CASE ("T-036 PluginState JSON round-trips exactly; malformed input throws ValidationError (D-010, operational: restore)", "[playback]") {
    PluginState s;
    s.lyrics = "Hel-lo \"w\u00f6rld\" \xE2\x99\xAA\n+ [sp]";
    s.voicePath = "C:\\voices\\me";
    s.notes = { { 0, 1, 60 }, { 1.25, 2.5, 72 }, { 1.0 / 3.0, 0.1 + 0.2, 0 } };
    s.params.voiceId = "me"; s.params.bpm = 97.5; s.params.outputSampleRate = 44100; s.params.conversionEnabled = false;
    s.params.portamentoSec = 0.1; s.params.vibratoCents = 12.5; s.params.seed = 18446744073709551615ULL;
    s.outputGainDb = -6.02;
    const auto back = pluginStateFromJson (toJson (s));
    CHECK (back == s);                                       // doubles and the 64-bit seed survive exactly
    CHECK (pluginStateFromJson (toJson (PluginState {})) == PluginState {});
    CHECK_THROWS_AS (pluginStateFromJson (""), ValidationError);
    CHECK_THROWS_AS (pluginStateFromJson ("{not json"), ValidationError);
    CHECK_THROWS_AS (pluginStateFromJson ("[]"), ValidationError);
    CHECK_THROWS_AS (pluginStateFromJson (R"({"version": 2})"), ValidationError);
    auto j = toJson (s);
    const auto at = j.find ("\"lyrics\"");
    REQUIRE (at != std::string::npos);
    j.replace (at, 8, "\"lyricz\"");                         // a required field missing
    CHECK_THROWS_AS (pluginStateFromJson (j), ValidationError);
}

TEST_CASE ("T-037 TakeSlot: publish, acquire/release, retire and collect (D-022)", "[playback]") {
    TakeSlot slot;
    CHECK (slot.acquire() == nullptr);
    slot.release();
    auto a = std::make_unique<RenderedTake>(); a->contentHash = 1; const auto* pa = a.get();
    slot.publish (std::move (a));
    CHECK (slot.retiredCount() == 0);
    CHECK (slot.acquire() == pa);
    slot.release();
    auto b = std::make_unique<RenderedTake>(); b->contentHash = 2; const auto* pb = b.get();
    slot.publish (std::move (b));
    CHECK (slot.retiredCount() == 1);
    CHECK (slot.collect() == 1);                             // a is not in use
    CHECK (slot.retiredCount() == 0);
    CHECK (slot.acquire() == pb);                            // b in use
    auto c = std::make_unique<RenderedTake>(); c->contentHash = 3; const auto* pc = c.get();
    slot.publish (std::move (c));
    CHECK (slot.collect() == 0);                             // b is still held by the reader
    CHECK (slot.retiredCount() == 1);
    CHECK (pb->contentHash == 2);                            // and still valid
    slot.release();
    CHECK (slot.collect() == 1);
    CHECK (slot.acquire() == pc);
    slot.release();
}

TEST_CASE ("T-038 TakeSlot under concurrent publish and acquire: every acquired take is intact (D-022; run under ASan and TSan)", "[playback][concurrency]") {
    TakeSlot slot;
    std::atomic<bool> done { false };
    std::atomic<long> reads { 0 }, corrupt { 0 };
    std::thread reader ([&] {
        while (! done.load()) {
            if (const auto* t = slot.acquire()) {
                const float expect = (float) t->contentHash;
                for (float v : t->samples) if (v != expect) { ++corrupt; break; }
                ++reads;
            }
            slot.release();
        }
    });
    struct Joiner {                                          // stops and joins the reader on every exit path (no std::terminate)
        std::atomic<bool>& done; std::thread& t;
        ~Joiner() { done = true; if (t.joinable()) t.join(); }
    };
    {
        Joiner joiner { done, reader };
        for (int i = 1; i <= 2000; ++i) {
            auto t = std::make_unique<RenderedTake>(); t->contentHash = (std::uint64_t) i; t->samples.assign (256, (float) i);
            slot.publish (std::move (t));
            if (i % 7 == 0) (void) slot.collect();
        }
        const auto deadline = std::chrono::steady_clock::now() + std::chrono::seconds (10);
        while (reads.load() < 1000 && std::chrono::steady_clock::now() < deadline) std::this_thread::yield();
    }
    CHECK (reads.load() >= 1000);
    CHECK (corrupt.load() == 0);
    (void) slot.collect();
    CHECK (slot.retiredCount() == 0);
}
