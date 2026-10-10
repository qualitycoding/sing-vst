// Interface frozen by plan D-003; rules in D-005.
#pragma once
#include <cstddef>
#include <optional>
#include <set>
#include <string>
#include <string_view>
#include <unordered_map>
#include <vector>

namespace singvst {

using Phones = std::vector<std::string>;

/** CMUdict-format pronunciation dictionary (D-005). Words and phones are stored lower-case with stress digits removed;
    the first pronunciation of a word wins; "word(2)" variant lines and text after '#' are ignored; blank lines and
    lines starting with ";;;" are skipped. */
class Dictionary {
public:
    static Dictionary fromCmuText (std::string_view text);
    std::optional<Phones> lookup (std::string_view word) const;   // case-insensitive
    std::size_t size() const;                                     // number of distinct words
    bool hasPhone (std::string_view phone) const;                 // phone occurs in any entry (case-insensitive, stress ignored)
private:
    std::unordered_map<std::string, Phones> entries;
    std::set<std::string> phoneSet;
};

/** True for the 15 ARPAbet vowels (aa ae ah ao aw ay eh er ey ih iy ow oy uh uw), with or without a stress digit, any case. */
bool isVowel (std::string_view phone);

/** Splits phones into n syllables by D-005. Throws ValidationError when n == 0, or n exceeds the vowel count
    (a vowel-less word is one syllable). */
std::vector<Phones> syllabify (const Phones& phones, std::size_t n);

} // namespace singvst
