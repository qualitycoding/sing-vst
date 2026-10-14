// FROZEN — DO NOT MODIFY. Frozen by plan Phase 2E (tests/FROZEN_MANIFEST.sha256). Rules: plan/DECISIONS.md. Change only via TEST_CHALLENGE.md.
#include <catch2/catch_test_macros.hpp>
#include "helpers.hpp"
#include "singvst/errors.hpp"
#include "singvst/lyrics.hpp"
using namespace singvst;
using testutil::text; using testutil::phon; using testutil::extend;
using Tokens = std::vector<LyricToken>;

TEST_CASE ("T-001 words split into hyphenated syllables (D-004)", "[lyrics]") {
    CHECK (parseLyrics ("Hel-lo world") == Tokens { text ("hel", true), text ("lo"), text ("world") });
    CHECK (parseLyrics ("to-ma-to") == Tokens { text ("to", true), text ("ma", true), text ("to") });
}

TEST_CASE ("T-002 trailing hyphen continues across whitespace; cleaning keeps ASCII alnum, apostrophe and bytes >= 0x80 (D-004)", "[lyrics]") {
    CHECK (parseLyrics ("Hel- lo, don't!\n(sing)") == Tokens { text ("hel", true), text ("lo"), text ("don't"), text ("sing") });
    CHECK (parseLyrics ("Caf\xC3\xA9 \xC3\x89T\xC3\x89 R2-D2") == Tokens { text ("caf\xC3\xA9"), text ("\xC3\x89t\xC3\x89"), text ("r2", true), text ("d2") });
}

TEST_CASE ("T-003 '+' is an Extend token; parts that clean to nothing are dropped (D-004)", "[lyrics]") {
    CHECK (parseLyrics ("la + , +") == Tokens { text ("la"), extend(), extend() });
    CHECK (parseLyrics ("la+lo") == Tokens { text ("la"), extend(), text ("lo") });
    CHECK (parseLyrics ("la- +") == Tokens { text ("la", true), extend() });
}

TEST_CASE ("T-004 bracketed phonemes: whitespace split, lower-cased, '-' after ']' continues (D-004)", "[lyrics]") {
    CHECK (parseLyrics ("[HH ah]-[l  OW] x") == Tokens { phon ({ "hh", "ah" }, true), phon ({ "l", "ow" }), text ("x") });
    CHECK (parseLyrics ("ab[sp]cd") == Tokens { text ("ab"), phon ({ "sp" }), text ("cd") });
}

TEST_CASE ("T-005 unbalanced or nested brackets throw ParseError at the byte offset (D-004, PK-42)", "[lyrics]") {
    const auto posOf = [] (const char* s) -> long {
        try { (void) parseLyrics (s); } catch (const ParseError& e) { return (long) e.position; }
        return -1;
    };
    CHECK (posOf ("ab [hh ah") == 3);        // unclosed: position of the opening '['
    CHECK (posOf ("ab ] c") == 3);           // stray ']'
    CHECK (posOf ("[a [b]]") == 3);          // nested: position of the inner '['
    CHECK (posOf ("x]") == 1);               // a word stops at ']', which is then stray
    CHECK (posOf ("\xC3\xA9 [x") == 3);      // offsets are bytes: the 2-byte character counts twice
    CHECK (posOf ("fine [ok] text") == -1);
}

TEST_CASE ("T-006 empty input, whitespace, empty groups and stray hyphens (D-004)", "[lyrics]") {
    CHECK (parseLyrics ("").empty());
    CHECK (parseLyrics (" \t\r\n ").empty());
    CHECK (parseLyrics ("[] [ \t]").empty());
    CHECK (parseLyrics ("--la") == Tokens { text ("la") });
    CHECK (parseLyrics ("la-") == Tokens { text ("la", true) });
    CHECK (parseLyrics ("- -- ,") == Tokens {});
}
