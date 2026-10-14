// FROZEN — DO NOT MODIFY. Frozen by plan Phase 2E (tests/FROZEN_MANIFEST.sha256). Rules: plan/DECISIONS.md. Change only via TEST_CHALLENGE.md.
#include <catch2/catch_test_macros.hpp>
#include "helpers.hpp"
#include "singvst/align.hpp"
using namespace singvst;
using Strings = std::vector<std::string>;

static Dictionary mini() { return Dictionary::fromCmuText (testutil::readFile (testutil::fixture ("cmudict-mini.dict"))); }
/** n consecutive one-beat notes starting at beat 0, pitches 60, 61, ... */
static std::vector<Note> beats (int n) { std::vector<Note> v; for (int i = 0; i < n; ++i) v.push_back ({ double (i), double (i + 1), 60 + i }); return v; }

TEST_CASE ("T-013 toMonophonic: drop empty notes, keep the highest of simultaneous notes, truncate overlaps (D-006)", "[align]") {
    CHECK (toMonophonic ({ { 2, 3, 64 }, { 0, 1.5, 60 }, { 1, 2, 62 }, { 1, 2, 67 }, { 4, 4, 70 }, { 1, 1, 90 } })
           == std::vector<Note> { { 0, 1, 60 }, { 1, 2, 67 }, { 2, 3, 64 } });
    CHECK (toMonophonic ({ { 5, 6, 50 }, { 5 + 5e-10, 6, 55 } }) == std::vector<Note> { { 5 + 5e-10, 6, 55 } });
    CHECK (toMonophonic ({ { 0, 2, 60 }, { 0, 2, 60 } }) == std::vector<Note> { { 0, 2, 60 } });
    CHECK (toMonophonic ({}).empty());
}

TEST_CASE ("T-014 align maps syllables to notes in order (D-006)", "[align]") {
    const auto r = align (beats (3), parseLyrics ("hel-lo world"), mini());
    REQUIRE (r.notes.size() == 3);
    CHECK (r.notes[0].phonemes == Phones { "hh", "ah" });
    CHECK (r.notes[1].phonemes == Phones { "l", "ow" });
    CHECK (r.notes[2].phonemes == Phones { "w", "er", "l", "d" });
    CHECK (r.notes[2].note == Note { 2, 3, 62 });
    CHECK_FALSE (r.notes[1].isExtension);
    CHECK (r.warnings.empty());
}

TEST_CASE ("T-015 extensions and surplus notes hold the previous syllable's last vowel (D-006)", "[align]") {
    const auto d = mini();
    const auto a = align (beats (2), parseLyrics ("love +"), d);
    CHECK (a.notes[1].phonemes == Phones { "ah" });
    CHECK (a.notes[1].isExtension);
    CHECK (a.warnings.empty());
    const auto b = align (beats (3), parseLyrics ("la"), d);
    CHECK (b.notes[1].phonemes == Phones { "aa" });
    CHECK (b.notes[2].phonemes == Phones { "aa" });
    CHECK (b.notes[2].isExtension);
    CHECK (b.warnings == Strings { "2 note(s) have no lyric" });
    const auto c = align (beats (2), parseLyrics ("hello"), d);              // no hyphen: one syllable, the last vowel is held
    CHECK (c.notes[0].phonemes == Phones { "hh", "ah", "l", "ow" });
    CHECK (c.notes[1].phonemes == Phones { "ow" });
    const auto e = align (beats (1), parseLyrics ("+"), d);
    CHECK (e.notes[0].phonemes == Phones { "ah" });
    CHECK (e.notes[0].isExtension);
    CHECK (e.warnings == Strings { "melisma '+' with no preceding syllable" });
}

TEST_CASE ("T-016 content problems become warnings with the exact D-006 texts, never exceptions (D-006, PK-42)", "[align]") {
    const auto d = mini();
    const auto a = align (beats (1), parseLyrics ("qualitycoding"), d);
    CHECK (a.notes[0].phonemes == Phones { "ah" });
    CHECK (a.warnings == Strings { "unknown word 'qualitycoding'" });
    const auto b = align (beats (1), parseLyrics ("la la la"), d);
    CHECK (b.notes.size() == 1);
    CHECK (b.warnings == Strings { "2 syllable(s) have no note" });
    const auto c = align (beats (2), parseLyrics ("lo-ve"), d);
    CHECK (c.notes[0].phonemes == Phones { "l", "ah", "v" });
    CHECK (c.notes[1].phonemes == Phones { "ah" });
    CHECK (c.notes[1].isExtension);
    CHECK (c.warnings == Strings { "word 'love' has 2 syllables marked but 1 vowel(s)" });
    const auto e = align (beats (2), parseLyrics ("qual-ity"), d);           // unknown hyphenated word: one 'ah' per syllable
    CHECK (e.notes[0].phonemes == Phones { "ah" });
    CHECK (e.notes[1].phonemes == Phones { "ah" });
    CHECK_FALSE (e.notes[1].isExtension);
    CHECK (e.warnings == Strings { "unknown word 'quality'" });
}

TEST_CASE ("T-017 empty notes or lyrics (D-006)", "[align]") {
    const auto d = mini();
    const auto a = align ({}, parseLyrics ("la"), d);
    CHECK (a.notes.empty());
    CHECK (a.warnings == Strings { "1 syllable(s) have no note" });
    CHECK (align ({}, {}, d).warnings.empty());
    const auto b = align (beats (2), {}, d);
    REQUIRE (b.notes.size() == 2);
    CHECK (b.notes[0].phonemes == Phones { "ah" });
    CHECK (b.notes[0].isExtension);
    CHECK (b.notes[1].phonemes == Phones { "ah" });
    CHECK (b.warnings == Strings { "2 note(s) have no lyric" });
}

TEST_CASE ("T-018 phoneme tokens keep known phones, map sp/ap to SP/AP, warn about the rest (D-006)", "[align]") {
    const auto d = mini();
    const auto a = align (beats (1), parseLyrics ("[sp hh ah ap]"), d);
    CHECK (a.notes[0].phonemes == Phones { "SP", "hh", "ah", "AP" });
    CHECK (a.warnings.empty());
    const auto b = align (beats (2), parseLyrics ("[zz qq] [hh zz ow]"), d);
    CHECK (b.notes[0].phonemes == Phones { "ah" });
    CHECK (b.notes[1].phonemes == Phones { "hh", "ow" });
    CHECK (b.warnings == Strings { "unknown phonemes zz qq", "unknown phonemes zz" });
}
