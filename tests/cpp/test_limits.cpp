// FROZEN — DO NOT MODIFY. Frozen by plan Phase 2E (tests/FROZEN_MANIFEST.sha256). Rules: plan/DECISIONS.md. Change only via TEST_CHALLENGE.md.
// Pre-mortem round 1, R-027: untrusted MIDI files and plugin state cannot make the renderer allocate without bound (D-038).
#include <catch2/catch_test_macros.hpp>
#include <atomic>
#include <string>
#include "helpers.hpp"
#include "singvst/errors.hpp"
#include "singvst/midifile.hpp"
#include "singvst/ort_runtime.hpp"
#include "singvst/render.hpp"
#include "singvst/voice.hpp"
using namespace singvst;

static std::string be32 (std::uint32_t n) { return { (char) (n >> 24), (char) (n >> 16), (char) (n >> 8), (char) n }; }
static std::string varlen (std::uint32_t v)
{
    std::string s (1, (char) (v & 0x7F));
    while (v >>= 7) s.insert (s.begin(), (char) (0x80 | (v & 0x7F)));
    return s;
}
/** Format-0 SMF, PPQ 480, default tempo (120 bpm) with the given track body (end-of-track appended). */
static std::string smf (std::string body)
{
    body += std::string ("\x00\xFF\x2F\x00", 4);
    return std::string ("MThd\0\0\0\x06\0\0\0\x01\x01\xE0", 14) + "MTrk" + be32 ((std::uint32_t) body.size()) + body;
}
/** n notes of 48 ticks (0.1 beat) each, back to back. */
static std::string manyNotes (int n)
{
    std::string body;
    for (int i = 0; i < n; ++i) body += varlen (0) + "\x90\x3C\x40" + varlen (48) + std::string ("\x80\x3C\x00", 3);
    return smf (body);
}
/** One note of one beat that ends at beat endBeat. */
static std::string lateNote (std::uint32_t endBeat)
{
    return smf (varlen ((endBeat - 1) * 480u) + "\x90\x3E\x40" + varlen (480) + std::string ("\x80\x3E\x00", 3));
}
static bool namesLimit (const ValidationError& e, const char* limit) { return std::string (e.what()).find (limit) != std::string::npos; }

TEST_CASE ("T-069 importMidi rejects more than 5000 notes or notes ending after 900 s, naming the limit (D-038)", "[midi][limits]") {
    CHECK (importMidi (manyNotes (5000)).notes.size() == 5000);                      // 500 beats = 250 s
    try { (void) importMidi (manyNotes (5001)); FAIL ("5001 notes accepted"); }
    catch (const ValidationError& e) { CHECK (namesLimit (e, "5000")); }
    CHECK (importMidi (lateNote (1799)).notes.size() == 1);                         // ends at 899.5 s at 120 bpm
    try { (void) importMidi (lateNote (1801)); FAIL ("note ending at 900.5 s accepted"); }
    catch (const ValidationError& e) { CHECK (namesLimit (e, "900")); }
}

TEST_CASE ("T-070 renderTake rejects takes over 900 s or 5000 notes before any engine runs, naming the limit (D-038)", "[render][limits]") {
    (void) loadOrtRuntime (SINGVST_TEST_ORT_LIB);
    const auto d = Dictionary::fromCmuText (testutil::readFile (testutil::fixture ("cmudict-mini.dict")));
    const auto m = parseManifest (testutil::readFile (testutil::fixture ("voice-legacy/manifest.json")));
    const auto guide = GuideEngine::load (m, testutil::fixture ("voice-legacy"));
    const std::atomic<bool> go { false };
    RenderRequest r; r.params.voiceId = "v"; r.params.bpm = 120.0;
    r.notes = { { 0.0, 1.0, 60 }, { 1799.0, 1801.0, 62 } };                          // ends at 900.5 s
    r.tokens = parseLyrics ("la la");
    try { (void) renderTake (r, d, *guide, nullptr, go); FAIL ("900.5 s take rendered"); }
    catch (const ValidationError& e) { CHECK (namesLimit (e, "900")); }
    r.notes.clear(); r.tokens.clear();
    for (int i = 0; i < 5001; ++i) { r.notes.push_back ({ i * 0.25, i * 0.25 + 0.25, 60 }); r.tokens.push_back (testutil::text ("la")); }
    try { (void) renderTake (r, d, *guide, nullptr, go); FAIL ("5001 notes rendered"); }
    catch (const ValidationError& e) { CHECK (namesLimit (e, "5000")); }
}
