// Interface frozen by plan D-003; grammar in D-004.
#pragma once
#include <string>
#include <string_view>
#include <vector>

namespace singvst {

enum class TokenKind { Text, Phonemes, Extend };

struct LyricToken {
    TokenKind kind = TokenKind::Text;
    std::string text;                  // lower-cased syllable text (Text only)
    std::vector<std::string> phonemes; // lower-cased phonemes (Phonemes only)
    bool continuesWord = false;        // syllable ended with '-': the next Text token belongs to the same word
    bool operator== (const LyricToken&) const = default;
};

/** Parses UTF-8 lyric text by the grammar in D-004. Throws ParseError on an unbalanced or nested '[' / ']'. */
std::vector<LyricToken> parseLyrics (std::string_view utf8);

} // namespace singvst
