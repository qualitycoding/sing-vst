// toMonophonic and align (D-006).
#include "singvst/align.hpp"
#include "singvst/errors.hpp"
#include <algorithm>

namespace singvst {
namespace {
constexpr double kEps = 1e-9;

struct Unit {
    Phones phones;
    bool extension = false;
    bool fromExtendToken = false;
};

std::string join (const std::vector<std::string>& v)
{
    std::string o;
    for (std::size_t i = 0; i < v.size(); ++i) { if (i) o += ' '; o += v[i]; }
    return o;
}
} // namespace

std::vector<Note> toMonophonic (std::vector<Note> notes)
{
    notes.erase (std::remove_if (notes.begin(), notes.end(), [] (const Note& n) { return n.endBeat - n.startBeat <= kEps; }), notes.end());
    std::stable_sort (notes.begin(), notes.end(), [] (const Note& a, const Note& b) { return a.startBeat < b.startBeat; });
    std::vector<Note> kept;
    std::size_t i = 0;
    while (i < notes.size()) {
        std::size_t best = i;
        std::size_t j = i + 1;
        while (j < notes.size() && notes[j].startBeat - notes[i].startBeat <= kEps) {
            if (notes[j].midiNote > notes[best].midiNote) best = j;
            ++j;
        }
        kept.push_back (notes[best]);
        i = j;
    }
    for (std::size_t k = 0; k + 1 < kept.size(); ++k)
        if (kept[k].endBeat > kept[k + 1].startBeat) kept[k].endBeat = kept[k + 1].startBeat;
    kept.erase (std::remove_if (kept.begin(), kept.end(), [] (const Note& n) { return n.endBeat - n.startBeat <= kEps; }), kept.end());
    return kept;
}

AlignmentResult align (const std::vector<Note>& notes, const std::vector<LyricToken>& tokens, const Dictionary& dict)
{
    AlignmentResult res;
    std::vector<Unit> units;
    std::size_t t = 0;
    while (t < tokens.size()) {
        const auto& tok = tokens[t];
        if (tok.kind == TokenKind::Text) {
            std::string word = tok.text;
            std::size_t g = 1;
            while (tokens[t].continuesWord && t + 1 < tokens.size() && tokens[t + 1].kind == TokenKind::Text) {
                ++t;
                word += tokens[t].text;
                ++g;
            }
            ++t;
            const auto pron = dict.lookup (word);
            if (! pron) {
                res.warnings.push_back ("unknown word '" + word + "'");
                for (std::size_t k = 0; k < g; ++k) units.push_back ({ { "ah" }, false, false });
                continue;
            }
            const std::size_t k = static_cast<std::size_t> (std::count_if (pron->begin(), pron->end(), [] (const std::string& p) { return isVowel (p); }));
            const std::size_t m = k == 0 ? 1 : std::min (g, k);
            for (auto& s : syllabify (*pron, m)) units.push_back ({ std::move (s), false, false });
            if (g > m) {
                res.warnings.push_back ("word '" + word + "' has " + std::to_string (g) + " syllables marked but "
                                        + std::to_string (std::max<std::size_t> (k, 1)) + " vowel(s)");
                for (std::size_t e = 0; e < g - m; ++e) units.push_back ({ {}, true, false });
            }
        } else if (tok.kind == TokenKind::Phonemes) {
            Phones kept, unknown;
            for (const auto& p : tok.phonemes) {
                if (p == "sp") kept.push_back ("SP");
                else if (p == "ap") kept.push_back ("AP");
                else if (dict.hasPhone (p)) kept.push_back (p);
                else unknown.push_back (p);
            }
            if (! unknown.empty()) res.warnings.push_back ("unknown phonemes " + join (unknown));
            if (kept.empty()) kept.push_back ("ah");
            units.push_back ({ std::move (kept), false, false });
            ++t;
        } else {
            units.push_back ({ {}, true, true });
            ++t;
        }
    }

    bool haveAssignment = false;
    for (std::size_t j = 0; j < notes.size(); ++j) {
        NoteAssignment a;
        a.note = notes[j];
        const bool surplus = j >= units.size();
        if (! surplus && ! units[j].extension) {
            a.phonemes = units[j].phones;
        } else {
            a.isExtension = true;
            if (! haveAssignment) {
                a.phonemes = { "ah" };
                if (! surplus && units[j].fromExtendToken) res.warnings.push_back ("melisma '+' with no preceding syllable");
            } else {
                const auto& prev = res.notes.back().phonemes;
                std::string v = prev.back();
                for (auto it = prev.rbegin(); it != prev.rend(); ++it) if (isVowel (*it)) { v = *it; break; }
                a.phonemes = { v };
            }
        }
        haveAssignment = true;
        res.notes.push_back (std::move (a));
    }
    if (notes.size() > units.size()) res.warnings.push_back (std::to_string (notes.size() - units.size()) + " note(s) have no lyric");
    if (units.size() > notes.size()) res.warnings.push_back (std::to_string (units.size() - notes.size()) + " syllable(s) have no note");
    return res;
}

} // namespace singvst
