// FROZEN — DO NOT MODIFY. Frozen by plan Phase 2E (tests/FROZEN_MANIFEST.sha256). Rules: plan/DECISIONS.md. Change only via TEST_CHALLENGE.md.
#include <catch2/catch_test_macros.hpp>
#include <catch2/matchers/catch_matchers_floating_point.hpp>
#include <cmath>
#include <filesystem>
#include <random>
#include "helpers.hpp"
#include "singvst/engine.hpp"
#include "singvst/errors.hpp"
#include "singvst/ort_runtime.hpp"
using namespace singvst;
using Catch::Matchers::WithinAbs;
namespace fs = std::filesystem;

TEST_CASE ("T-039 standardNormal: SplitMix64 + Box-Muller golden values, prefix property, moments (D-012, PK-34)", "[runtime]") {
    const auto a = standardNormal (0, 5);
    const double g0[] = { -0.452757740, 0.207766039, 2.650605812, -0.490422825, -0.988604125 };
    REQUIRE (a.size() == 5);
    for (int i = 0; i < 5; ++i) CHECK_THAT (a[(size_t) i], WithinAbs (g0[i], 1e-6));
    const auto b = standardNormal (42, 5);
    const double g42[] = { 0.414719750, 0.652681222, -0.891886214, 1.326833563, 1.729593088 };
    for (int i = 0; i < 5; ++i) CHECK_THAT (b[(size_t) i], WithinAbs (g42[i], 1e-6));
    CHECK (standardNormal (0, 0).empty());
    const auto c = standardNormal (0, 3);
    CHECK (std::vector<float> (a.begin(), a.begin() + 3) == c);           // odd n drops the last z1 only
    const auto z = standardNormal (7, 1000000);
    double s = 0, s2 = 0; for (float v : z) { s += v; s2 += (double) v * v; }
    const double mean = s / 1e6, sd = std::sqrt (s2 / 1e6 - mean * mean);
    CHECK (std::abs (mean) < 0.005);                                      // 5 standard errors
    CHECK (std::abs (sd - 1.0) < 0.005);
    CHECK (standardNormal (7, 1000) == standardNormal (7, 1000));
    CHECK (standardNormal (8, 1000) != standardNormal (7, 1000));
}

TEST_CASE ("T-040 resample: length rule, identity, DC gain, 1 kHz amplitude, alias rejection (D-011)", "[runtime]") {
    const std::vector<float> three { 1, 2, 3 };
    CHECK (resample (three, 44100, 44100) == three);
    CHECK (resample (std::vector<float> (44032, 0.0f), 44100, 48000).size() == 47926);
    CHECK (resample (std::vector<float> (48000, 0.0f), 48000, 16000).size() == 16000);
    CHECK (resample (std::vector<float> (44032, 0.0f), 44100, 16000).size() == 15975);
    CHECK (resample (std::vector<float> (3, 0.0f), 32000, 48000).size() == 5);        // 4.5 rounds half away from zero
    CHECK (resample (std::vector<float> (1, 0.0f), 44100, 16000).empty());
    CHECK (resample ({}, 44100, 48000).empty());
    const auto dc = resample (std::vector<float> (44100, 1.0f), 44100, 48000);
    for (size_t i = 2000; i < 46000; ++i) REQUIRE_THAT (dc[i], WithinAbs (1.0, 1e-3));
    std::vector<float> sine (48000);
    for (size_t i = 0; i < sine.size(); ++i) sine[i] = (float) std::sin (2.0 * M_PI * 1000.0 * (double) i / 48000.0);
    const auto s16 = resample (sine, 48000, 16000);
    float peak = 0; for (size_t i = 2000; i < 14000; ++i) peak = std::max (peak, std::abs (s16[i]));
    CHECK_THAT (peak, WithinAbs (1.0, 0.01));
    std::vector<float> high (44100);
    for (size_t i = 0; i < high.size(); ++i) high[i] = (float) std::sin (2.0 * M_PI * 20000.0 * (double) i / 44100.0);
    const auto h16 = resample (high, 44100, 16000);
    double e = 0; for (size_t i = 2000; i < 14000; ++i) e += (double) h16[i] * h16[i];
    CHECK (std::sqrt (e / 12000.0) < 0.00707);                             // below -40 dB of the input RMS
}

TEST_CASE ("T-041 loadOrtRuntime: explicit path only, version check, idempotent, single library (D-024, C-026, C-042)", "[runtime]") {
#ifdef _WIN32
    CHECK (bundledOrtFileName() == "onnxruntime.dll");
#else
    CHECK (bundledOrtFileName() == "libonnxruntime.so.1.31.0");
#endif
    REQUIRE_FALSE (ortRuntimeLoaded());                                   // ctest runs each case in a fresh process
    CHECK_THROWS_AS (loadOrtRuntime (fs::path { SINGVST_FIXTURES } / "does-not-exist" / bundledOrtFileName()), ValidationError);
    CHECK_THROWS_AS (loadOrtRuntime (testutil::fixture ("not_ort.bin")), ValidationError);
    CHECK_FALSE (ortRuntimeLoaded());
    const fs::path lib { SINGVST_TEST_ORT_LIB };
    const auto& info = loadOrtRuntime (lib);
    CHECK (info.version == "1.31.0");
    CHECK (fs::equivalent (info.path, lib));
    CHECK (info.path.is_absolute());
    CHECK (ortRuntimeLoaded());
    CHECK (&loadOrtRuntime (lib) == &info);               // idempotent for the same path
    std::mt19937_64 rng { std::random_device {}() };
    const auto copyDir = fs::temp_directory_path() / ("singvst-T041-" + std::to_string (rng()));
    fs::create_directories (copyDir);
    const auto copy = copyDir / bundledOrtFileName();
    fs::copy_file (lib, copy);
    CHECK_THROWS_AS (loadOrtRuntime (copy), ValidationError);             // a second, different library is refused
    std::error_code ec; fs::remove_all (copyDir, ec);
}
