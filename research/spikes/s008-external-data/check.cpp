// S-008 throw-away checks (D-012). Not a committed test: tests/ is frozen. Linked against ../../../../build-core/core/libsingvst_core.a.
// Usage: check <ort-lib> <fixture-onnx-dir> <copy-of-the-fixture-dir-with-acoustic_external.onnx-added>
#include <atomic>
#include <cmath>
#include <cstdio>
#include <filesystem>
#include <string>
#include "singvst/engine.hpp"
#include "singvst/errors.hpp"
#include "singvst/ort_runtime.hpp"
using namespace singvst;
namespace fs = std::filesystem;
static int failures = 0;
static void check (bool ok, const char* what) { std::printf ("%s: %s\n", ok ? "PASS" : "FAIL", what); if (! ok) ++failures; }

static VoiceManifest legacy()
{
    VoiceManifest m; m.name = "fixture"; m.consent = "fixture"; m.guideLicence = "fixture"; m.guide.steps = 20; m.guide.depth = 0.4;
    m.guide.files = { { "acoustic", "acoustic_legacy.onnx" }, { "vocoder", "vocoder.onnx" }, { "phonemes", "phonemes.txt" }, { "speaker", "speaker.emb" } };
    return m;
}
static std::vector<PhonemeSpan> spansFromFrames (const std::vector<std::pair<const char*, int>>& s)
{
    const double fr = 44100.0 / 512.0;
    std::vector<PhonemeSpan> out; long acc = 0;
    for (const auto& [p, n] : s) { out.push_back ({ p, double (acc) / fr, double (acc + n) / fr }); acc += n; }
    return out;
}

int main (int argc, char** argv)
{
    if (argc < 4) return 2;
    (void) loadOrtRuntime (argv[1]);
    const fs::path fixtures = argv[2], ext = argv[3];
    const std::atomic<bool> go { false };

    // 1. External-data check.
    try { (void) GuideEngine::load (legacy(), fixtures); check (true, "original fixture model accepted"); }
    catch (const std::exception& e) { std::printf ("%s\n", e.what()); check (false, "original fixture model accepted"); }
    auto m = legacy(); m.guide.files["acoustic"] = "acoustic_external.onnx";
    try { (void) GuideEngine::load (m, ext); check (false, "external-data model rejected"); }
    catch (const ValidationError& e) {
        std::printf ("ValidationError: %s\n", e.what());
        check (std::string (e.what()).find ("external data") != std::string::npos, "external-data model rejected with ValidationError naming external data");
    }

    // 2. A 3000-frame single phrase (no rest of >= 22 frames) is split exactly once by the 2584-frame cap: expect two 'guide part' lines.
    const auto g = GuideEngine::load (legacy(), fixtures);
    const auto big = spansFromFrames ({ { "aa", 500 }, { "t", 500 }, { "aa", 500 }, { "t", 500 }, { "aa", 500 }, { "t", 500 } });
    std::printf ("-- render 3000-frame phrase (stderr 'guide part' lines expected: 2)\n"); std::fflush (stdout);
    const auto y = g->render (big, std::vector<float> (3000, 330.0f), go);
    check (y.size() == 3000u * 512u, "output length == 3000 frames * 512");
    bool allVoiced = true;
    for (size_t t = 0; t < 3000; ++t) if (y[t * 512] != 330.0f) allVoiced = false;
    check (allVoiced, "every frame carries the f0 echo (no zeros inside the phrase)");

    // 3. Exact zeros only at SP spans of >= 22 frames.
    const auto rest = spansFromFrames ({ { "aa", 100 }, { "SP", 30 }, { "ow", 100 }, { "SP", 21 }, { "aa", 50 } });
    std::printf ("-- render with a 30-frame and a 21-frame SP (stderr: 2 parts expected, the 21-frame SP stays inside)\n"); std::fflush (stdout);
    const auto r = g->render (rest, std::vector<float> (301, 220.0f), go);
    check (r.size() == 301u * 512u, "rest render length");
    bool zerosOk = true;
    for (size_t t = 0; t < 301; ++t) {
        const bool inRest = t >= 100 && t < 130;
        bool allZero = true;
        for (size_t j = 0; j < 512; ++j) if (r[t * 512 + j] != 0.0f) { allZero = false; break; }
        if (inRest != allZero) zerosOk = false;
    }
    check (zerosOk, "frames 100..129 are exact zeros and no other frame is");
    return failures == 0 ? 0 : 1;
}
