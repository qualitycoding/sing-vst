// FROZEN — DO NOT MODIFY. Frozen by plan Phase 2E (tests/FROZEN_MANIFEST.sha256). Rules: plan/DECISIONS.md. Change only via TEST_CHALLENGE.md.
#include <catch2/catch_test_macros.hpp>
#include <atomic>
#include <chrono>
#include <mutex>
#include <thread>
#include "helpers.hpp"
#include "singvst/errors.hpp"
#include "singvst/ort_runtime.hpp"
#include "singvst/render.hpp"
#include "singvst/synthesis.hpp"
#include "singvst/voice.hpp"
using namespace singvst;
using namespace std::chrono_literals;
using Strings = std::vector<std::string>;

static Dictionary mini() { return Dictionary::fromCmuText (testutil::readFile (testutil::fixture ("cmudict-mini.dict"))); }
static VoiceManifest fixtureVoice (const char* dir) { return parseManifest (testutil::readFile (testutil::fixture (std::string (dir) + "/manifest.json"))); }
static RenderRequest request (double startBeat, const char* lyrics, int outputRate = 48000, bool convert = true)
{
    RenderRequest r; r.notes = { { startBeat, startBeat + 1, 69 }, { startBeat + 1, startBeat + 2, 69 } };
    r.tokens = parseLyrics (lyrics); r.params.voiceId = "fixture"; r.params.bpm = 120.0; r.params.outputSampleRate = outputRate;
    r.params.conversionEnabled = convert; r.params.seed = 3; return r;
}
static const std::atomic<bool> go { false };

TEST_CASE ("T-048 renderTake, guide only: lengths through the chain, take metadata, unclipped peak (D-013, D-021)", "[render]") {
    (void) loadOrtRuntime (SINGVST_TEST_ORT_LIB);
    const auto d = mini();
    const auto m = fixtureVoice ("voice-legacy");
    const auto guide = GuideEngine::load (m, testutil::fixture ("voice-legacy"));
    const auto rq = request (4.0, "la la");
    const auto t = renderTake (rq, d, *guide, nullptr, go);
    CHECK (t.samples.size() == 47926);                       // 86 frames * 512 = 44032 at 44.1 kHz -> 48 kHz
    CHECK (t.sampleRate == 48000);
    CHECK (t.startBeat == 4.0);
    CHECK (t.bpm == 120.0);
    CHECK (t.contentHash == phraseHash (rq.notes, rq.tokens, rq.params));
    CHECK (t.unclippedPeak == peakAbs (t.samples));
    CHECK (t.unclippedPeak > 1.0f);                           // fixture output is far above full scale: no clipping applied
    CHECK (renderTake (request (0.0, "la la", 44100), d, *guide, nullptr, go).samples.size() == 44032);
}

TEST_CASE ("T-049 renderTake with conversion, warnings, and failure modes (D-013)", "[render]") {
    (void) loadOrtRuntime (SINGVST_TEST_ORT_LIB);
    const auto d = mini();
    const auto m = fixtureVoice ("voice-convert");
    const auto dir = testutil::fixture ("voice-convert");
    const auto guide = GuideEngine::load (m, dir);
    const auto conv = ConverterEngine::load (m, dir);
    CHECK (renderTake (request (0.0, "la la"), d, *guide, conv.get(), go).samples.size() == 47520);          // T = min(100, 99) frames * 480
    CHECK (renderTake (request (0.0, "la la", 48000, false), d, *guide, conv.get(), go).samples.size() == 47926);   // conversion off
    std::vector<std::string> warnings;
    (void) renderTake (request (0.0, "qualitycoding la"), d, *guide, conv.get(), go, &warnings);
    CHECK (warnings == Strings { "unknown word 'qualitycoding'" });
    auto empty = request (0.0, "la"); empty.notes.clear();
    CHECK_THROWS_AS (renderTake (empty, d, *guide, conv.get(), go), ValidationError);
    const std::atomic<bool> stop { true };
    CHECK_THROWS_AS (renderTake (request (0.0, "la la"), d, *guide, conv.get(), stop), Cancelled);
}

static RenderRequest req (int pitch) { RenderRequest r; r.notes = { { 0, 1, pitch } }; r.tokens = { testutil::text ("la") }; r.params.voiceId = "v"; return r; }
static std::uint64_t hashOf (const RenderRequest& r) { return phraseHash (r.notes, r.tokens, r.params); }
static RenderedTake fake (const RenderRequest& r) { RenderedTake t; t.contentHash = hashOf (r); t.samples.assign (10, 0.5f); t.unclippedPeak = 0.5f; return t; }

TEST_CASE ("T-050 Renderer: Ready, Failed keeps the previous take, cache, cancellation (D-013)", "[render][concurrency]") {
    std::atomic<int> calls { 0 };
    Renderer r ([&] (const RenderRequest& q, const std::atomic<bool>&) -> RenderedTake {
        ++calls;
        if (q.notes[0].midiNote == 99) throw std::runtime_error ("model exploded");
        return fake (q); });
    CHECK (r.status() == RenderStatus::Idle);
    CHECK (r.latest() == nullptr);
    r.submit (req (60));
    REQUIRE (r.waitIdle (5s));
    CHECK (r.status() == RenderStatus::Ready);
    REQUIRE (r.latest() != nullptr);
    CHECK (r.latest()->contentHash == hashOf (req (60)));
    r.submit (req (60));                                      // identical request: not rendered again
    REQUIRE (r.waitIdle (5s));
    CHECK (r.renderCount() == 1);
    CHECK (calls.load() == 1);
    r.submit (req (99));
    REQUIRE (r.waitIdle (5s));
    CHECK (r.status() == RenderStatus::Failed);
    CHECK (r.lastError().find ("model exploded") != std::string::npos);
    REQUIRE (r.latest() != nullptr);
    CHECK (r.latest()->contentHash == hashOf (req (60)));    // previous take kept for playback
    CHECK (r.renderCount() == 1);
}

TEST_CASE ("T-051 Renderer: submit cancels the running job; the destructor cancels and joins promptly (D-013)", "[render][concurrency]") {
    std::atomic<bool> started { false };
    {
        Renderer r ([&] (const RenderRequest& q, const std::atomic<bool>& cancel) -> RenderedTake {
            if (q.notes[0].midiNote == 60) { started = true; while (! cancel) std::this_thread::sleep_for (1ms); throw Cancelled(); }
            return fake (q); });
        r.submit (req (60));
        while (! started) std::this_thread::sleep_for (1ms);
        r.submit (req (62));
        REQUIRE (r.waitIdle (5s));
        CHECK (r.status() == RenderStatus::Ready);
        CHECK (r.latest()->contentHash == hashOf (req (62)));
        CHECK (r.renderCount() == 1);                         // the cancelled job is discarded silently
        CHECK (r.lastError().empty());
    }
    started = false;
    const auto t0 = std::chrono::steady_clock::now();
    {
        Renderer r ([&] (const RenderRequest&, const std::atomic<bool>& cancel) -> RenderedTake {
            started = true; while (! cancel) std::this_thread::sleep_for (1ms); throw Cancelled(); });
        r.submit (req (60));
        while (! started) std::this_thread::sleep_for (1ms);
    }                                                         // destructor with a job in flight
    CHECK (std::chrono::steady_clock::now() - t0 < 5s);
}

TEST_CASE ("T-052 Renderer keeps only the newest queued request (D-013)", "[render][concurrency]") {
    std::atomic<bool> release { false }, started { false };
    std::vector<int> rendered; std::mutex mu;
    Renderer r ([&] (const RenderRequest& q, const std::atomic<bool>& cancel) -> RenderedTake {
        if (q.notes[0].midiNote == 60) { started = true; while (! release && ! cancel) std::this_thread::sleep_for (1ms); if (cancel) throw Cancelled(); }
        { std::lock_guard<std::mutex> l (mu); rendered.push_back (q.notes[0].midiNote); }
        return fake (q); });
    r.submit (req (60));
    while (! started) std::this_thread::sleep_for (1ms);
    r.submit (req (61));
    r.submit (req (62));
    r.submit (req (63));
    REQUIRE (r.waitIdle (5s));
    std::lock_guard<std::mutex> l (mu);
    CHECK (rendered == std::vector<int> { 63 });              // 60 cancelled, 61 and 62 dropped
    CHECK (r.latest()->contentHash == hashOf (req (63)));
}
