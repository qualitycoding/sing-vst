// FROZEN — DO NOT MODIFY. Frozen by plan Phase 2E (tests/FROZEN_MANIFEST.sha256). Rules: plan/DECISIONS.md. Change only via TEST_CHALLENGE.md.
// Engine tests run real ONNX Runtime 1.31.0 on the fixture models in tests/fixtures/onnx, which echo their inputs into the
// output audio (tests/fixtures/make_fixtures.py). Expected values were derived independently by research/spikes/oracle/engines.py.
#include <catch2/catch_test_macros.hpp>
#include <catch2/matchers/catch_matchers_floating_point.hpp>
#include <catch2/matchers/catch_matchers_string.hpp>
#include <atomic>
#include "helpers.hpp"
#include "singvst/engine.hpp"
#include "singvst/errors.hpp"
#include "singvst/ort_runtime.hpp"
using namespace singvst;
using Catch::Matchers::WithinAbs;
using Catch::Matchers::ContainsSubstring;

static const std::filesystem::path OX = testutil::fixture ("onnx");
static void ensureOrt() { (void) loadOrtRuntime (SINGVST_TEST_ORT_LIB); }
static VoiceManifest legacy (int steps = 20)
{
    VoiceManifest m; m.name = "fixture"; m.consent = "fixture"; m.guideLicence = "fixture";
    m.guide.steps = steps; m.guide.depth = 0.4;
    m.guide.files = { { "acoustic", "acoustic_legacy.onnx" }, { "vocoder", "vocoder.onnx" }, { "phonemes", "phonemes.txt" }, { "speaker", "speaker.emb" } };
    return m;
}
static VoiceManifest withConverter()
{
    auto m = legacy(); ConverterSpec c; c.sampleRate = 48000; c.speakerId = 2;
    c.files = { { "synth", "rvc_synth.onnx" }, { "content", "content.onnx" } }; m.converter = c; return m;
}
/** The 10 echoed channels of guide output frame t (sample t*512 + j = mel channel j). */
static std::vector<float> gframe (const std::vector<float>& y, size_t t) { return { y.begin() + (long) (t * 512), y.begin() + (long) (t * 512 + 10) }; }
/** The 8 echoed features of converter output frame t (sample t*480 + j = feature j). */
static std::vector<float> cframe (const std::vector<float>& y, size_t t) { return { y.begin() + (long) (t * 480), y.begin() + (long) (t * 480 + 8) }; }
static const std::atomic<bool> go { false };

TEST_CASE ("T-042 GuideEngine::load: needs the runtime, validates files, inputs and the speaker embedding (D-012)", "[engine]") {
    REQUIRE_FALSE (ortRuntimeLoaded());                                   // fresh process under ctest
    CHECK_THROWS_AS (GuideEngine::load (legacy(), OX), ValidationError);
    ensureOrt();
    const auto g = GuideEngine::load (legacy(), OX);
    CHECK (g->sampleRate() == 44100);
    CHECK (g->hopSize() == 512);
    auto m = legacy(); m.guide.files["acoustic"] = "missing.onnx";       CHECK_THROWS_AS (GuideEngine::load (m, OX), ValidationError);
    m = legacy(); m.guide.files["acoustic"] = "corrupt.onnx";             CHECK_THROWS_AS (GuideEngine::load (m, OX), ValidationError);
    m = legacy(); m.guide.files["acoustic"] = "acoustic_energy.onnx";     CHECK_THROWS_WITH (GuideEngine::load (m, OX), ContainsSubstring ("energy"));
    m = legacy(); m.guide.files["speaker"] = "speaker3.emb";              CHECK_THROWS_AS (GuideEngine::load (m, OX), ValidationError);
    m = legacy(); m.guide.files.erase ("speaker");                        CHECK_THROWS_AS (GuideEngine::load (m, OX), ValidationError);
}

TEST_CASE ("T-043 GuideEngine::render feeds tokens, padding, per-frame inputs and step/depth inputs per D-012", "[engine]") {
    ensureOrt();
    const auto y = GuideEngine::load (legacy(), OX)->render ({ { "SP", 0.0, 0.1 }, { "aa", 0.1, 0.5 } }, std::vector<float> (43, 330.0f), go);
    REQUIRE (y.size() == 43 * 512);                                       // durations [9, 34], padding trimmed
    // f0, sum(tokens SP SP aa SP = 0+0+2+0), sum(durations 8+9+34+8), gender 0, velocity 1, sum(speaker) 2.5, depth 400, speedup 20, -, T 59
    const std::vector<float> e { 330, 2, 59, 0, 1, 2.5f, 400, 20, 0, 59 };
    CHECK (gframe (y, 0) == e);
    CHECK (gframe (y, 42) == e);
    const auto y3 = GuideEngine::load (legacy (3), OX)->render ({ { "aa", 0.0, 0.5 } }, std::vector<float> (43, 330.0f), go);
    CHECK (gframe (y3, 0)[6] == 399.0f);                                  // d = 400, speedup = 400/3 = 133, d = 400/133*133
    CHECK (gframe (y3, 0)[7] == 133.0f);
    VoiceManifest ca = legacy(); ca.guide.files = { { "acoustic", "acoustic_ca.onnx" }, { "vocoder", "vocoder.onnx" }, { "phonemes", "phonemes.json" }, { "languages", "languages.json" } };
    const auto yc = GuideEngine::load (ca, OX)->render ({ { "qq", 0.0, 0.5 } }, std::vector<float> (43, 220.0f), go);
    const auto f = gframe (yc, 0);
    CHECK (f[1] == 41.0f);                                                // 'qq' found as 'en/qq' (id 41)
    CHECK (f[7] == 20.0f);                                                // steps
    CHECK_THAT (f[6], WithinAbs (0.4, 1e-7));                             // depth (float)
    CHECK (f[8] == 3.0f);                                                 // languages: 'en' = 3 for the prefixed token only
}

TEST_CASE ("T-044 GuideEngine::render splits phrases at SP spans of >= 22 frames and fills unvoiced frames (D-012)", "[engine]") {
    ensureOrt();
    const auto g = GuideEngine::load (legacy(), OX);
    std::vector<float> f0 (129, 0.0f);
    for (size_t i = 21; i < 43; ++i) f0[i] = 220.0f;
    for (size_t i = 86; i < 129; ++i) f0[i] = 330.0f;
    const auto y = g->render ({ { "aa", 0.0, 0.5 }, { "SP", 0.5, 1.0 }, { "ow", 1.0, 1.5 } }, f0, go);   // durations [43, 43, 43]
    REQUIRE (y.size() == 129 * 512);
    CHECK (gframe (y, 0)[0] == 220.0f);                                   // frames 0..20 take the nearest voiced value
    CHECK (gframe (y, 0)[1] == 2.0f);                                     // phrase 1 tokens: SP aa SP
    CHECK (gframe (y, 0)[2] == 59.0f);
    for (size_t i = 43 * 512; i < 86 * 512; ++i) REQUIRE (y[i] == 0.0f);  // the long rest is exact silence
    CHECK (gframe (y, 86)[0] == 330.0f);
    CHECK (gframe (y, 86)[1] == 26.0f);                                   // phrase 2 tokens: SP ow SP
    CHECK (gframe (y, 128)[2] == 59.0f);
    const auto s = g->render ({ { "aa", 0.0, 0.2 }, { "SP", 0.2, 0.4 }, { "ow", 0.4, 0.6 } }, std::vector<float> (52, 220.0f), go);
    REQUIRE (s.size() == 52 * 512);                                       // durations [17, 17, 18]: the 17-frame SP stays inside
    CHECK (gframe (s, 0)[1] == 28.0f);                                    // SP aa SP ow SP
    CHECK (gframe (s, 0)[2] == 68.0f);
}

TEST_CASE ("T-045 GuideEngine::render rejects bad input and honours cancel (D-012)", "[engine]") {
    ensureOrt();
    const auto g = GuideEngine::load (legacy(), OX);
    CHECK_THROWS_WITH (g->render ({ { "qx", 0.0, 0.5 } }, std::vector<float> (43, 330.0f), go), ContainsSubstring ("qx"));
    CHECK_THROWS_AS (g->render ({ { "aa", 0.0, 0.5 } }, std::vector<float> (42, 330.0f), go), ValidationError);   // f0 length
    CHECK_THROWS_AS (g->render ({ { "aa", 0.0, 0.5 } }, std::vector<float> (43, 0.0f), go), ValidationError);     // nothing voiced
    const std::atomic<bool> stop { true };
    CHECK_THROWS_AS (g->render ({ { "aa", 0.0, 0.5 } }, std::vector<float> (43, 330.0f), stop), Cancelled);
}

TEST_CASE ("T-046 ConverterEngine::convert feeds content units, pitch, speaker and seeded noise per D-012", "[engine]") {
    ensureOrt();
    const auto c = ConverterEngine::load (withConverter(), OX);
    CHECK (c->sampleRate() == 48000);
    std::vector<float> f0 (100, 440.0f);
    for (size_t i = 50; i < 60; ++i) f0[i] = 0.0f;
    const std::vector<float> guide (44100, 0.25f);
    const auto y = c->convert (guide, 44100, f0, 7, go);
    REQUIRE (y.size() == 100 * 480);
    const auto n = standardNormal (7, 192 * 100);
    const auto f0f = cframe (y, 0);
    CHECK (f0f[0] == 440.0f);                                             // pitchf
    CHECK (f0f[1] == 122.0f);                                             // coarse pitch of 440 Hz
    CHECK (f0f[2] == 2.0f);                                               // ds = speaker_id
    CHECK (f0f[3] == n[0]);                                               // rnd[0][0]
    CHECK (f0f[4] == n[191 * 100]);                                       // rnd[191][0]
    CHECK (f0f[6] == 100.0f);                                             // one chunk of 100 frames
    const auto f55 = cframe (y, 55);
    CHECK (f55[0] == 0.0f);                                               // unvoiced: pitchf 0, coarse 1
    CHECK (f55[1] == 1.0f);
    CHECK (f55[3] == n[55]);
    for (size_t t = 2; t < 98; ++t) REQUIRE_THAT (cframe (y, t)[5], WithinAbs (0.25, 5e-4));   // content units: mean of the 16 kHz guide
    CHECK (c->convert (guide, 44100, std::vector<float> (80, 440.0f), 7, go).size() == 80 * 480);    // T limited by f0
    CHECK (c->convert (guide, 44100, std::vector<float> (120, 440.0f), 7, go).size() == 100 * 480);  // T limited by audio
    CHECK (c->convert (guide, 44100, f0, 7, go) == y);                    // deterministic for a seed
    CHECK (cframe (c->convert (guide, 44100, f0, 8, go), 0)[3] != n[0]);
}

TEST_CASE ("T-047 ConverterEngine: chunks of 1500 frames with 100-frame context, noise independent of chunking; errors (D-012)", "[engine]") {
    ensureOrt();
    const auto c = ConverterEngine::load (withConverter(), OX);
    const auto y = c->convert (std::vector<float> (44100 * 32, 0.25f), 44100, std::vector<float> (3200, 440.0f), 9, go);
    REQUIRE (y.size() == 3200 * 480);
    const auto n = standardNormal (9, 192 * 3200);
    for (size_t t : { 0, 1499, 1500, 2999, 3000, 3199 }) {
        INFO ("frame " << t);
        CHECK (cframe (y, t)[3] == n[t]);
        CHECK (cframe (y, t)[4] == n[191 * 3200 + t]);
        CHECK (cframe (y, t)[0] == 440.0f);
    }
    CHECK (cframe (y, 0)[6] == 1600.0f);                                  // [0,1500) + 100 right context
    CHECK (cframe (y, 1500)[6] == 1700.0f);                               // [1500,3000) + 100 + 100
    CHECK (cframe (y, 3000)[6] == 300.0f);                                // [3000,3200) + 100 left context
    auto m = withConverter(); m.converter->files["content"] = "missing.onnx"; CHECK_THROWS_AS (ConverterEngine::load (m, OX), ValidationError);
    m = withConverter(); m.converter->files["synth"] = "corrupt.onnx";        CHECK_THROWS_AS (ConverterEngine::load (m, OX), ValidationError);
    CHECK_THROWS_AS (ConverterEngine::load (legacy(), OX), ValidationError);  // no converter in the manifest
    const std::atomic<bool> stop { true };
    CHECK_THROWS_AS (c->convert (std::vector<float> (44100, 0.25f), 44100, std::vector<float> (100, 440.0f), 9, stop), Cancelled);
}
