// FROZEN — DO NOT MODIFY. Frozen by plan Phase 2E (tests/FROZEN_MANIFEST.sha256). Rules: plan/DECISIONS.md. Change only via TEST_CHALLENGE.md.
#include <catch2/catch_test_macros.hpp>
#include <catch2/matchers/catch_matchers_string.hpp>
#include <filesystem>
#include <fstream>
#include <random>
#include "helpers.hpp"
#include "singvst/errors.hpp"
#include "singvst/voice.hpp"
using namespace singvst;
namespace fs = std::filesystem;

static const std::string H64 = std::string (64, 'a');
/** Base manifest (valid). Every path appears exactly once in 'files' and once in 'sha256'. */
static const std::string BASE = R"({"format": "singvoice", "format_version": 1, "name": "Me", "consent": "my own voice",
 "guide_licence": "TIGER v102, personal non-commercial",
 "guide": {"type": "diffsinger", "sample_rate": 44100, "hop_size": 512, "language": "en", "steps": 20, "depth": 0.4,
           "files": {"acoustic": "guide/acoustic.onnx", "vocoder": "guide/vocoder.onnx", "phonemes": "guide/phonemes.txt"}},
 "converter": {"type": "rvc-v2", "sample_rate": 48000, "speaker_id": 0, "files": {"synth": "conv/rvc.onnx", "content": "conv/content.onnx"}},
 "sha256": {"guide/acoustic.onnx": "HASH", "guide/vocoder.onnx": "HASH", "guide/phonemes.txt": "HASH", "conv/rvc.onnx": "HASH", "conv/content.onnx": "HASH"}})";

/** Replaces every occurrence of 'from' in s. Precondition: 'from' occurs at least once (else throws). */
static std::string replaceAll (std::string s, const std::string& from, const std::string& to)
{
    if (s.find (from) == std::string::npos) throw std::logic_error ("test helper: '" + from + "' not in manifest");
    for (size_t p = 0; (p = s.find (from, p)) != std::string::npos; p += to.size()) s.replace (p, from.size(), to);
    return s;
}
static std::string base() { return replaceAll (BASE, "HASH", H64); }

TEST_CASE ("T-028 parseManifest reads the fixture packages and applies defaults (D-008)", "[voice]") {
    const auto legacy = parseManifest (testutil::readFile (testutil::fixture ("voice-legacy/manifest.json")));
    CHECK (legacy.formatVersion == 1);
    CHECK (legacy.name == "voice-legacy");
    CHECK_FALSE (legacy.consent.empty());
    CHECK_FALSE (legacy.guideLicence.empty());
    CHECK (legacy.guide.sampleRate == 44100);
    CHECK (legacy.guide.hopSize == 512);
    CHECK (legacy.guide.language == "en");
    CHECK (legacy.guide.steps == 20);
    CHECK (legacy.guide.depth == 0.4);
    CHECK (legacy.guide.files.at ("speaker") == "guide/speaker.emb");
    CHECK_FALSE (legacy.converter.has_value());
    CHECK (legacy.sha256.size() == 4);
    const auto conv = parseManifest (testutil::readFile (testutil::fixture ("voice-convert/manifest.json")));
    REQUIRE (conv.converter.has_value());
    CHECK (conv.converter->sampleRate == 48000);
    CHECK (conv.converter->speakerId == 2);
    CHECK (conv.converter->files.at ("synth") == "conv/rvc_synth.onnx");
    CHECK (conv.sha256.size() == 6);
    const auto m = parseManifest (replaceAll (replaceAll (base(), R"("language": "en", )", ""), R"("speaker_id": 0, )", ""));
    CHECK (m.guide.language == "en");
    CHECK (m.converter->speakerId == 0);
    const auto noConv = parseManifest (replaceAll (replaceAll (replaceAll (base(),
        R"("converter": {"type": "rvc-v2", "sample_rate": 48000, "speaker_id": 0, "files": {"synth": "conv/rvc.onnx", "content": "conv/content.onnx"}},)", ""),
        R"(, "conv/rvc.onnx": ")" + H64 + "\"", ""), R"(, "conv/content.onnx": ")" + H64 + "\"", ""));
    CHECK_FALSE (noConv.converter.has_value());
    CHECK (parseManifest (replaceAll (base(), R"("format": "singvoice",)", R"("format": "singvoice", "comment": "unknown top-level keys are ignored",)")).name == "Me");
}

TEST_CASE ("T-029 parseManifest rejects every schema violation with ValidationError (D-008, PK-42)", "[voice]") {
    REQUIRE_NOTHROW (parseManifest (base()));
    const std::vector<std::pair<const char*, std::string>> bad {
        { "not JSON", "{not json" }, { "array", "[]" }, { "empty", "" },
        { "format", replaceAll (base(), "\"singvoice\"", "\"voice\"") },
        { "format_version", replaceAll (base(), "\"format_version\": 1", "\"format_version\": 2") },
        { "name empty", replaceAll (base(), "\"name\": \"Me\"", "\"name\": \"\"") },
        { "consent missing", replaceAll (base(), "\"consent\": \"my own voice\",", "") },
        { "guide_licence empty", replaceAll (base(), "\"TIGER v102, personal non-commercial\"", "\"\"") },
        { "guide type", replaceAll (base(), "\"diffsinger\"", "\"nnsvs\"") },
        { "guide sample_rate", replaceAll (base(), "\"sample_rate\": 44100", "\"sample_rate\": 48000") },
        { "hop_size", replaceAll (base(), "\"hop_size\": 512", "\"hop_size\": 256") },
        { "steps 0", replaceAll (base(), "\"steps\": 20", "\"steps\": 0") },
        { "steps 1001", replaceAll (base(), "\"steps\": 20", "\"steps\": 1001") },
        { "steps fractional", replaceAll (base(), "\"steps\": 20", "\"steps\": 2.5") },
        { "depth 0", replaceAll (base(), "\"depth\": 0.4", "\"depth\": 0") },
        { "depth 1.5", replaceAll (base(), "\"depth\": 0.4", "\"depth\": 1.5") },
        { "language empty", replaceAll (base(), "\"language\": \"en\"", "\"language\": \"\"") },
        { "acoustic role missing", replaceAll (replaceAll (base(), "\"acoustic\": \"guide/acoustic.onnx\", ", ""), "\"guide/acoustic.onnx\": \"" + H64 + "\", ", "") },
        { "unknown guide role", replaceAll (base(), "\"phonemes\": \"guide/phonemes.txt\"}", "\"phonemes\": \"guide/phonemes.txt\", \"pitch\": \"guide/phonemes.txt\"}") },
        { "converter type", replaceAll (base(), "\"rvc-v2\"", "\"so-vits\"") },
        { "converter sample_rate", replaceAll (base(), "\"sample_rate\": 48000", "\"sample_rate\": 22050") },
        { "speaker_id negative", replaceAll (base(), "\"speaker_id\": 0", "\"speaker_id\": -1") },
        { "unknown converter role", replaceAll (base(), "\"content\": \"conv/content.onnx\"}", "\"content\": \"conv/content.onnx\", \"index\": \"conv/rvc.onnx\"}") },
        { "sha256 missing a file", replaceAll (base(), "\"conv/content.onnx\": \"" + H64 + "\"", "\"conv/other.onnx\": \"" + H64 + "\"") },
        { "sha256 extra key", replaceAll (base(), "\"conv/content.onnx\": \"" + H64 + "\"", "\"conv/content.onnx\": \"" + H64 + "\", \"extra.bin\": \"" + H64 + "\"") },
        { "sha256 upper case", replaceAll (base(), "\"conv/rvc.onnx\": \"" + H64 + "\"", "\"conv/rvc.onnx\": \"" + std::string (64, 'A') + "\"") },
        { "sha256 63 digits", replaceAll (base(), "\"conv/rvc.onnx\": \"" + H64 + "\"", "\"conv/rvc.onnx\": \"" + std::string (63, 'a') + "\"") },
    };
    for (const auto& [what, json] : bad) { INFO (what); CHECK_THROWS_AS (parseManifest (json), ValidationError); }
}

TEST_CASE ("T-030 file paths must be safe relative paths (D-008, security: path traversal)", "[voice]") {
    const auto withPath = [] (const std::string& p) { return replaceAll (base(), "guide/acoustic.onnx", p); };
    REQUIRE_NOTHROW (parseManifest (withPath ("guide/a-b_c.1.onnx")));
    for (const char* p : { "../acoustic.onnx", "guide/../../acoustic.onnx", "/etc/acoustic.onnx", "C:/acoustic.onnx", "guide\\\\acoustic.onnx",
                           "guide//acoustic.onnx", "./acoustic.onnx", "guide/./acoustic.onnx", "guide/", "guide/a b.onnx", "guide/caf\xC3\xA9.onnx", ".." }) {
        INFO (p); CHECK_THROWS_AS (parseManifest (withPath (p)), ValidationError);
    }
}

TEST_CASE ("T-031 validatePackage checks presence, type, size and SHA-256 of every file (D-008, security: integrity)", "[voice]") {
    const auto src = testutil::fixture ("voice-legacy");
    const auto m = parseManifest (testutil::readFile (src / "manifest.json"));
    std::mt19937_64 rng { std::random_device {}() };
    const auto dir = fs::temp_directory_path() / ("singvst-T031-" + std::to_string (rng()));
    fs::copy (src, dir, fs::copy_options::recursive);
    CHECK_NOTHROW (validatePackage (dir, m));
    CHECK_THROWS_AS (validatePackage (dir, m, 15), ValidationError);          // speaker.emb is 16 bytes
    { std::fstream f (dir / "guide/speaker.emb", std::ios::in | std::ios::out | std::ios::binary); f.seekp (0); f.put ('\x01'); }
    CHECK_THROWS_WITH (validatePackage (dir, m), Catch::Matchers::ContainsSubstring ("guide/speaker.emb"));
    fs::copy_file (src / "guide/speaker.emb", dir / "guide/speaker.emb", fs::copy_options::overwrite_existing);
    CHECK_NOTHROW (validatePackage (dir, m));
    fs::remove (dir / "guide/vocoder.onnx");
    CHECK_THROWS_AS (validatePackage (dir, m), ValidationError);
    fs::create_directory (dir / "guide/vocoder.onnx");                       // a directory is not a regular file
    CHECK_THROWS_AS (validatePackage (dir, m), ValidationError);
    fs::remove_all (dir);
}

TEST_CASE ("T-063 sha256Hex matches FIPS 180-4 vectors and block-boundary lengths (D-008)", "[voice]") {
    CHECK (sha256Hex ("") == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855");
    CHECK (sha256Hex ("abc") == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad");
    CHECK (sha256Hex ("abcdbcdecdefdefgefghfghighijhijkijkljklmklmnlmnomnopnopq") == "248d6a61d20638b8e5c026930c3e6039a33ce45964ff2167f6ecedd419db06c1");
    CHECK (sha256Hex (std::string (1000000, 'a')) == "cdc76e5c9914fb9281a1c7e284d73e67f1809a48a497200e046d39ccc7112cd0");
    CHECK (sha256Hex (std::string (55, 'x')) == "d5e285683cd4efc02d021a5c62014694958901005d6f71e89e0989fac77e4072");
    CHECK (sha256Hex (std::string (56, 'x')) == "04c26261370ee7541549d16dee320c723e3fd14671e66a099afe0a377c16888e");
    CHECK (sha256Hex (std::string (64, 'x')) == "7ce100971f64e7001e8fe5a51973ecdfe1ced42befe7ee8d5fd6219506b5393c");
    std::string all; for (int i = 0; i < 256; ++i) all.push_back ((char) i);
    CHECK (sha256Hex (all) == "40aff2e9d2d8922e47afd4648e6967497158785fbd1da870e7110266bf944880");
}
