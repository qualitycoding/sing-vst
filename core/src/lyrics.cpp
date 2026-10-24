// parseLyrics (D-004).
#include "singvst/lyrics.hpp"
#include "singvst/errors.hpp"

namespace singvst {
namespace {
bool isSpace (char c) { return c == ' ' || c == '\t' || c == '\r' || c == '\n'; }
char lowerAscii (char c) { return (c >= 'A' && c <= 'Z') ? static_cast<char> (c - 'A' + 'a') : c; }

std::string cleanPart (std::string_view part)
{
    std::string out;
    for (char c : part) {
        const auto u = static_cast<unsigned char> (c);
        if ((c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z') || (c >= '0' && c <= '9')) out.push_back (lowerAscii (c));
        else if (c == '\'' || u >= 0x80) out.push_back (c);
    }
    return out;
}
} // namespace

std::vector<LyricToken> parseLyrics (std::string_view s)
{
    std::vector<LyricToken> out;
    std::size_t i = 0;
    const auto n = s.size();
    while (i < n) {
        if (isSpace (s[i])) { ++i; continue; }
        if (s[i] == ']') throw ParseError ("unbalanced ']'", i);
        if (s[i] == '[') {
            const std::size_t open = i;
            std::size_t j = i + 1;
            while (j < n && s[j] != ']') {
                if (s[j] == '[') throw ParseError ("nested '['", j);
                ++j;
            }
            if (j >= n) throw ParseError ("unterminated '['", open);
            LyricToken t;
            t.kind = TokenKind::Phonemes;
            std::string cur;
            for (std::size_t k = open + 1; k < j; ++k) {
                if (isSpace (s[k])) { if (! cur.empty()) { t.phonemes.push_back (cur); cur.clear(); } }
                else cur.push_back (lowerAscii (s[k]));
            }
            if (! cur.empty()) t.phonemes.push_back (cur);
            i = j + 1;
            if (i < n && s[i] == '-') { t.continuesWord = true; ++i; }
            if (! t.phonemes.empty()) out.push_back (std::move (t));
            continue;
        }
        if (s[i] == '+') {
            LyricToken t;
            t.kind = TokenKind::Extend;
            out.push_back (std::move (t));
            ++i;
            continue;
        }
        std::size_t j = i;
        while (j < n && ! isSpace (s[j]) && s[j] != '[' && s[j] != ']' && s[j] != '+') ++j;
        const std::string_view word = s.substr (i, j - i);
        const bool endsWithDash = word.back() == '-';
        std::vector<std::string> parts;
        std::size_t a = 0;
        while (a <= word.size()) {
            std::size_t b = word.find ('-', a);
            if (b == std::string_view::npos) b = word.size();
            auto p = cleanPart (word.substr (a, b - a));
            if (! p.empty()) parts.push_back (std::move (p));
            a = b + 1;
        }
        for (std::size_t k = 0; k < parts.size(); ++k) {
            LyricToken t;
            t.kind = TokenKind::Text;
            t.text = std::move (parts[k]);
            t.continuesWord = (k + 1 < parts.size()) || endsWithDash;
            out.push_back (std::move (t));
        }
        i = j;
    }
    return out;
}

} // namespace singvst
