// FROZEN — DO NOT MODIFY. Frozen by plan Phase 2E (tests/FROZEN_MANIFEST.sha256). Rules: plan/DECISIONS.md. Change only via TEST_CHALLENGE.md.
#include <catch2/catch_test_macros.hpp>
#include "helpers.hpp"
#include "singvst/errors.hpp"
#include "singvst/g2p.hpp"
using namespace singvst;

static Dictionary mini() { return Dictionary::fromCmuText (testutil::readFile (testutil::fixture ("cmudict-mini.dict"))); }
using Sylls = std::vector<Phones>;

TEST_CASE ("T-007 dictionary parsing: comments, ';;;' and blank lines, variants, first entry wins, normalisation (D-005)", "[g2p]") {
    const auto d = mini();
    CHECK (d.size() == 48);
    CHECK (d.lookup ("hello") == Phones { "hh", "ah", "l", "ow" });
    CHECK (d.lookup ("HeLLo") == Phones { "hh", "ah", "l", "ow" });
    CHECK (d.lookup ("world") == Phones { "w", "er", "l", "d" });            // the later 'world W AO1 R L D' line is ignored
    CHECK (d.lookup ("zzz") == Phones { "z", "iy" });                        // text after '#' ignored
    CHECK (d.lookup ("don't") == Phones { "d", "ow", "n", "t" });
    CHECK_FALSE (d.lookup ("qualitycoding").has_value());
    CHECK_FALSE (d.lookup ("hello(2)").has_value());                        // variants are not words
    CHECK (d.hasPhone ("ow"));
    CHECK (d.hasPhone ("OW1"));
    CHECK_FALSE (d.hasPhone ("zh"));                                         // only in the ignored duplicate line
    CHECK_FALSE (d.hasPhone ("zz"));
}

TEST_CASE ("T-008 isVowel: the 15 ARPAbet vowels with or without stress, any case (D-005)", "[g2p]") {
    for (const char* v : { "aa", "ae", "ah", "ao", "aw", "ay", "eh", "er", "ey", "ih", "iy", "ow", "oy", "uh", "uw", "AH0", "er1", "Ow2" })
        CHECK (isVowel (v));
    for (const char* c : { "hh", "l", "ng", "y", "w", "r", "SP", "AP", "", "a", "0" })
        CHECK_FALSE (isVowel (c));
}

TEST_CASE ("T-009 syllabify: floor(c/2) consonants to the coda, ceil(c/2) to the onset (D-005)", "[g2p]") {
    const auto d = mini();
    CHECK (syllabify (*d.lookup ("hello"), 2) == Sylls { { "hh", "ah" }, { "l", "ow" } });
    CHECK (syllabify (*d.lookup ("singing"), 2) == Sylls { { "s", "ih" }, { "ng", "ih", "ng" } });
    CHECK (syllabify (*d.lookup ("extra"), 2) == Sylls { { "eh", "k", "s" }, { "t", "r", "ah" } });
    CHECK (syllabify (*d.lookup ("birthday"), 2) == Sylls { { "b", "er", "th" }, { "d", "ey" } });
    CHECK (syllabify (*d.lookup ("tomato"), 3) == Sylls { { "t", "ah" }, { "m", "ey" }, { "t", "ow" } });
    CHECK (syllabify (*d.lookup ("strength"), 1) == Sylls { { "s", "t", "r", "eh", "ng", "k", "th" } });
}

TEST_CASE ("T-010 syllabify with fewer syllables than vowels puts the rest in the last syllable (D-005)", "[g2p]") {
    const auto d = mini();
    CHECK (syllabify (*d.lookup ("tomato"), 2) == Sylls { { "t", "ah" }, { "m", "ey", "t", "ow" } });
    CHECK (syllabify (*d.lookup ("tomato"), 1) == Sylls { { "t", "ah", "m", "ey", "t", "ow" } });
}

TEST_CASE ("T-011 syllabify rejects n == 0 and n > vowels; a vowel-less word is one syllable (D-005)", "[g2p]") {
    const auto d = mini();
    CHECK_THROWS_AS (syllabify (*d.lookup ("love"), 2), ValidationError);
    CHECK_THROWS_AS (syllabify (*d.lookup ("love"), 0), ValidationError);
    CHECK (syllabify (*d.lookup ("hmm"), 1) == Sylls { { "hh", "m" } });
    CHECK_THROWS_AS (syllabify (*d.lookup ("hmm"), 2), ValidationError);
}

TEST_CASE ("T-012 the shipped CMUdict (74790861) loads with every ARPAbet phone (C-016, D-005)", "[g2p]") {
    const auto d = Dictionary::fromCmuText (testutil::readFile (SINGVST_CMUDICT));
    CHECK (d.size() == 126052);
    CHECK (d.lookup ("singing") == Phones { "s", "ih", "ng", "ih", "ng" });
    CHECK (d.lookup ("rhythm") == Phones { "r", "ih", "dh", "ah", "m" });
    for (const char* p : { "aa", "ae", "ah", "ao", "aw", "ay", "b", "ch", "d", "dh", "eh", "er", "ey", "f", "g", "hh", "ih", "iy", "jh", "k",
                           "l", "m", "n", "ng", "ow", "oy", "p", "r", "s", "sh", "t", "th", "uh", "uw", "v", "w", "y", "z", "zh" })
        CHECK (d.hasPhone (p));
    CHECK_FALSE (d.hasPhone ("ax"));
}
