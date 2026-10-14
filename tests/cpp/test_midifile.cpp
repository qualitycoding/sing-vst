// FROZEN — DO NOT MODIFY. Frozen by plan Phase 2E (tests/FROZEN_MANIFEST.sha256). Rules: plan/DECISIONS.md. Change only via TEST_CHALLENGE.md.
#include <catch2/catch_test_macros.hpp>
#include <catch2/matchers/catch_matchers_floating_point.hpp>
#include <random>
#include "helpers.hpp"
#include "singvst/errors.hpp"
#include "singvst/midifile.hpp"
using namespace singvst;
using Catch::Matchers::WithinRel;
using Strings = std::vector<std::string>;

/** Bytes from a list of byte values (keeps embedded zero bytes). */
static std::string bytes (std::initializer_list<int> v) { std::string s; for (int b : v) s.push_back ((char) b); return s; }
static const std::string HDR0 = bytes ({ 'M','T','h','d', 0,0,0,6, 0,0, 0,1, 0x01,0xE0 });   // format 0, 1 track, PPQ 480
static std::string track (const std::string& body)
{
    const auto n = body.size();
    return "MTrk" + bytes ({ int (n >> 24) & 255, int (n >> 16) & 255, int (n >> 8) & 255, int (n & 255) }) + body;
}

TEST_CASE ("T-064 importMidi reads notes, lyrics and tempo from a format-0 file (D-031)", "[midi]") {
    const auto r = importMidi (testutil::readFile (testutil::fixture ("lyrics.mid")));
    CHECK (r.notes == std::vector<Note> { { 0, 1, 60 }, { 1, 2, 62 }, { 2, 3, 64 } });
    CHECK (r.lyrics == "hel- lo world");                                 // each event trimmed, joined with one space
    CHECK (r.bpm == 120.0);
    CHECK (r.warnings.empty());
}

TEST_CASE ("T-065 importMidi: format 1, running status, velocity-0 off, retrigger, held notes, sysex, unknown chunk, tempo change (D-031)", "[midi]") {
    const auto r = importMidi (testutil::readFile (testutil::fixture ("complex.mid")));
    CHECK (r.notes == std::vector<Note> { { 0, 0.5, 69 }, { 0.5, 1, 71 }, { 1, 2, 48 }, { 1, 2, 71 }, { 2, 2.5, 72 } });
    CHECK (r.lyrics == "a b c");                                         // by tick, then track
    CHECK_THAT (r.bpm, WithinRel (60e6 / 666667.0, 1e-12));              // tempo 90 bpm is stored as 666667 us
    CHECK (r.warnings == Strings { "tempo changes after beat 2 are ignored" });
    const auto empty = importMidi (HDR0 + track (bytes ({ 0x00, 0xFF, 0x2F, 0x00 })));
    CHECK (empty.notes.empty());
    CHECK (empty.lyrics.empty());
    CHECK (empty.bpm == 120.0);
}

TEST_CASE ("T-066 importMidi treats bytes as untrusted: malformed input throws ValidationError, never crashes (D-031, PK-42)", "[midi]") {
    const std::vector<std::pair<const char*, std::string>> bad {
        { "empty", "" },
        { "not MThd", "RIFF" + HDR0.substr (4) },
        { "truncated header", HDR0.substr (0, 10) },
        { "header length 5", bytes ({ 'M','T','h','d', 0,0,0,5, 0,0, 0,1, 0x01 }) },
        { "SMPTE file", testutil::readFile (testutil::fixture ("smpte.mid")) },
        { "format 2", testutil::readFile (testutil::fixture ("format2.mid")) },
        { "PPQ 0", bytes ({ 'M','T','h','d', 0,0,0,6, 0,0, 0,1, 0,0 }) + track (bytes ({ 0x00, 0xFF, 0x2F, 0x00 })) },
        { "chunk past end", HDR0 + "MTrk" + bytes ({ 0, 0, 1, 0 }) + bytes ({ 0x00, 0xFF, 0x2F, 0x00 }) },
        { "varlen of 5 bytes", HDR0 + track (bytes ({ 0x81, 0x81, 0x81, 0x81, 0x01, 0x90, 60, 64 })) },
        { "data byte without status", HDR0 + track (bytes ({ 0x00, 0x3C, 0x40 })) },
        { "tempo of 2 bytes", HDR0 + track (bytes ({ 0x00, 0xFF, 0x51, 0x02, 0x07, 0xA1, 0x00, 0xFF, 0x2F, 0x00 })) },
        { "meta past end", HDR0 + track (bytes ({ 0x00, 0xFF, 0x05, 0x10, 'a' })) },
        { "truncated note", HDR0 + track (bytes ({ 0x00, 0x90, 0x3C })) },
    };
    for (const auto& [what, b] : bad) { INFO (what); CHECK_THROWS_AS (importMidi (b), ValidationError); }

    // Deterministic mutation fuzz of both valid fixtures: every result is a value or a ValidationError.
    std::mt19937 rng { 20261014u };
    long accepted = 0, rejected = 0, other = 0;
    for (const char* name : { "lyrics.mid", "complex.mid" }) {
        const auto seed = testutil::readFile (testutil::fixture (name));
        for (int i = 0; i < 1500; ++i) {
            std::string m = seed;
            const int edits = 1 + (int) (rng() % 4);
            for (int e = 0; e < edits; ++e) m[rng() % m.size()] = (char) (rng() & 0xFF);
            if (rng() % 4 == 0) m.resize (rng() % (m.size() + 1));
            try { (void) importMidi (m); ++accepted; }
            catch (const ValidationError&) { ++rejected; }
            catch (...) { ++other; }
        }
    }
    CHECK (other == 0);
    CHECK (accepted + rejected == 3000);
}
