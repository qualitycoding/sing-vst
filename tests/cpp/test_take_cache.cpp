// FROZEN — DO NOT MODIFY. Frozen by plan Phase 2E (tests/FROZEN_MANIFEST.sha256). Rules: plan/DECISIONS.md. Change only via TEST_CHALLENGE.md.
// Pre-mortem round 1, R-017: an approved take must be recallable bit-for-bit (D-038).
#include <catch2/catch_test_macros.hpp>
#include <atomic>
#include <cstring>
#include <filesystem>
#include <fstream>
#include "helpers.hpp"
#include "singvst/take_cache.hpp"
using namespace singvst;
namespace fs = std::filesystem;

/** A fresh empty directory under the system temp dir. Precondition: the temp dir is writable. */
static fs::path freshDir (const char* name)
{
    const auto d = fs::temp_directory_path() / (std::string ("singvst-") + name);
    fs::remove_all (d); fs::create_directories (d); return d;
}
static RenderRequest rq (int pitch) { RenderRequest r; r.notes = { { 0, 1, pitch } }; r.tokens = { testutil::text ("la") }; r.params.voiceId = "v"; return r; }
static RenderedTake takeFor (const RenderRequest& r, float base)
{
    RenderedTake t; t.startBeat = 2.5; t.bpm = 97.25; t.sampleRate = 44100; t.contentHash = phraseHash (r.notes, r.tokens, r.params);
    for (int i = 0; i < 1000; ++i) t.samples.push_back (base + 1e-7f * (float) i);
    t.samples[7] = -1.75f; t.unclippedPeak = 1.75f; return t;
}
static bool sameTake (const RenderedTake& a, const RenderedTake& b)
{
    return a.startBeat == b.startBeat && a.bpm == b.bpm && a.sampleRate == b.sampleRate && a.unclippedPeak == b.unclippedPeak
        && a.contentHash == b.contentHash && a.samples.size() == b.samples.size()
        && std::memcmp (a.samples.data(), b.samples.data(), a.samples.size() * sizeof (float)) == 0;
}

TEST_CASE ("T-067 take cache: bit-exact round trip; absent, truncated, corrupted or mismatched files are misses; store never throws (D-038)", "[cache]") {
    const auto dir = freshDir ("t067");
    const auto t = takeFor (rq (60), 0.25f);
    CHECK (takeFileName (0x00ab'cdef'0123'4567ull) == fs::path ("00abcdef01234567.take"));
    CHECK_FALSE (loadTake (dir, t.contentHash).has_value());                       // absent
    REQUIRE (storeTake (dir, t));
    const auto file = dir / takeFileName (t.contentHash);
    REQUIRE (fs::exists (file));
    CHECK (fs::file_size (file) == 52u + 4u * 1000u);                               // D-038 layout
    const auto back = loadTake (dir, t.contentHash);
    REQUIRE (back.has_value());
    CHECK (sameTake (*back, t));
    CHECK_FALSE (loadTake (dir, t.contentHash ^ 1u).has_value());                  // other hash: no file

    const auto bytes = testutil::readFile (file);
    auto writeAs = [&] (const std::string& b) { std::ofstream f (file, std::ios::binary | std::ios::trunc); f.write (b.data(), (std::streamsize) b.size()); };
    writeAs (bytes.substr (0, bytes.size() - 1));
    CHECK_FALSE (loadTake (dir, t.contentHash).has_value());                       // truncated
    std::string flipped = bytes; flipped[60] = (char) (flipped[60] ^ 0x01);
    writeAs (flipped);
    CHECK_FALSE (loadTake (dir, t.contentHash).has_value());                       // checksum
    std::string magic = bytes; magic[0] = 'X';
    writeAs (magic);
    CHECK_FALSE (loadTake (dir, t.contentHash).has_value());                       // magic
    const auto other = takeFor (rq (62), 0.5f);
    REQUIRE (storeTake (dir, other));
    fs::rename (dir / takeFileName (other.contentHash), file);                      // right name, wrong stored hash
    CHECK_FALSE (loadTake (dir, t.contentHash).has_value());

    const auto blocker = dir / "not-a-dir";
    { std::ofstream f (blocker); f << "x"; }
    CHECK_FALSE (storeTake (blocker / "sub", t));                                   // cannot create the directory
}

TEST_CASE ("T-068 cachedRender: a later session gets the stored take without rendering; misses render and store (D-038)", "[cache]") {
    const auto dir = freshDir ("t068");
    std::atomic<int> calls { 0 };
    float base = 0.25f;
    RenderFn fn = [&] (const RenderRequest& r, const std::atomic<bool>&) { ++calls; return takeFor (r, base); };
    const std::atomic<bool> go { false };
    RenderedTake first;
    { const auto c = cachedRender (fn, dir); first = c (rq (60), go); }
    CHECK (calls.load() == 1);
    base = 0.75f;                                                                   // a re-render would now differ
    { const auto c = cachedRender (fn, dir); const auto again = c (rq (60), go);     // "next session"
      CHECK (calls.load() == 1);
      CHECK (sameTake (again, first));
      (void) c (rq (64), go);
      CHECK (calls.load() == 2); }
    RenderFn wrongHash = [&] (const RenderRequest& r, const std::atomic<bool>&) { ++calls; auto t = takeFor (r, 0.1f); t.contentHash ^= 1u; return t; };
    { const auto c = cachedRender (wrongHash, dir); (void) c (rq (66), go); (void) c (rq (66), go); }
    CHECK (calls.load() == 4);                                                      // a take whose hash does not match is not stored
    const auto blocker = dir / "file";
    { std::ofstream f (blocker); f << "x"; }
    { const auto c = cachedRender (fn, blocker / "sub"); CHECK (c (rq (68), go).samples.size() == 1000); }   // unwritable: still renders
    RenderFn boom = [] (const RenderRequest&, const std::atomic<bool>&) -> RenderedTake { throw std::runtime_error ("boom"); };
    { const auto c = cachedRender (boom, dir); CHECK_THROWS_AS (c (rq (70), go), std::runtime_error); }
}
