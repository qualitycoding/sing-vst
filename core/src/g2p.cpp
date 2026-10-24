// Dictionary, isVowel, syllabify (D-005).
#include "singvst/g2p.hpp"
#include "singvst/errors.hpp"
#include <algorithm>

namespace singvst {
namespace {
bool isSpace (char c) { return c == ' ' || c == '\t' || c == '\r' || c == '\n'; }
std::string lowerAscii (std::string_view s)
{
    std::string o (s);
    for (auto& c : o) if (c >= 'A' && c <= 'Z') c = static_cast<char> (c - 'A' + 'a');
    return o;
}
std::string normalisePhone (std::string_view p)
{
    std::string o = lowerAscii (p);
    while (! o.empty() && o.back() >= '0' && o.back() <= '9') o.pop_back();
    return o;
}
} // namespace

Dictionary Dictionary::fromCmuText (std::string_view text)
{
    Dictionary d;
    std::size_t pos = 0;
    while (pos <= text.size()) {
        std::size_t eol = text.find ('\n', pos);
        if (eol == std::string_view::npos) eol = text.size();
        std::string_view line = text.substr (pos, eol - pos);
        pos = eol + 1;
        if (const auto h = line.find ('#'); h != std::string_view::npos) line = line.substr (0, h);
        while (! line.empty() && isSpace (line.front())) line.remove_prefix (1);
        while (! line.empty() && isSpace (line.back())) line.remove_suffix (1);
        if (line.empty() || line.substr (0, 3) == ";;;") continue;
        std::vector<std::string_view> fields;
        std::size_t a = 0;
        while (a < line.size()) {
            while (a < line.size() && isSpace (line[a])) ++a;
            std::size_t b = a;
            while (b < line.size() && ! isSpace (line[b])) ++b;
            if (b > a) fields.push_back (line.substr (a, b - a));
            a = b;
        }
        if (fields.empty()) continue;
        std::string_view w = fields[0];
        if (w.size() > 2 && w.back() == ')') {
            const auto o = w.rfind ('(');
            if (o != std::string_view::npos && o + 2 < w.size()
                && std::all_of (w.begin() + static_cast<std::ptrdiff_t> (o) + 1, w.end() - 1, [] (char c) { return c >= '0' && c <= '9'; }))
                continue;
        }
        std::string word = lowerAscii (w);
        if (d.entries.count (word)) continue;
        Phones ph;
        for (std::size_t k = 1; k < fields.size(); ++k) ph.push_back (normalisePhone (fields[k]));
        for (const auto& p : ph) d.phoneSet.insert (p);
        d.entries.emplace (std::move (word), std::move (ph));
    }
    return d;
}

std::optional<Phones> Dictionary::lookup (std::string_view word) const
{
    const auto it = entries.find (lowerAscii (word));
    if (it == entries.end()) return std::nullopt;
    return it->second;
}

std::size_t Dictionary::size() const { return entries.size(); }
bool Dictionary::hasPhone (std::string_view phone) const { return phoneSet.count (normalisePhone (phone)) > 0; }

bool isVowel (std::string_view phone)
{
    static const char* const vowels[] = { "aa", "ae", "ah", "ao", "aw", "ay", "eh", "er", "ey", "ih", "iy", "ow", "oy", "uh", "uw" };
    const auto p = normalisePhone (phone);
    return std::any_of (std::begin (vowels), std::end (vowels), [&] (const char* v) { return p == v; });
}

std::vector<Phones> syllabify (const Phones& phones, std::size_t n)
{
    std::vector<std::size_t> v;
    for (std::size_t i = 0; i < phones.size(); ++i) if (isVowel (phones[i])) v.push_back (i);
    if (v.empty()) {
        if (n == 1) return { phones };
        throw ValidationError ("syllabify: no vowel and n != 1");
    }
    if (n == 0 || n > v.size()) throw ValidationError ("syllabify: n must be between 1 and the vowel count");
    std::vector<Phones> out;
    std::size_t start = 0;
    for (std::size_t j = 1; j < n; ++j) {
        const std::size_t c = v[j] - v[j - 1] - 1;
        const std::size_t cut = v[j - 1] + 1 + c / 2;
        out.emplace_back (phones.begin() + static_cast<std::ptrdiff_t> (start), phones.begin() + static_cast<std::ptrdiff_t> (cut));
        start = cut;
    }
    out.emplace_back (phones.begin() + static_cast<std::ptrdiff_t> (start), phones.end());
    return out;
}

} // namespace singvst
