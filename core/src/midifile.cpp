// Standard MIDI File import (D-031). The bytes are untrusted: every read is bounds-checked.
#include "singvst/midifile.hpp"
#include "singvst/errors.hpp"
#include <algorithm>
#include <cstdint>
#include <locale>
#include <map>
#include <sstream>
#include <tuple>

namespace singvst {
namespace {
constexpr std::size_t kMaxNotes = 5000;
constexpr double kMaxSeconds = 900.0;

[[noreturn]] void bad (const std::string& what) { throw ValidationError ("MIDI file: " + what); }
void need (bool ok, const char* what) { if (! ok) bad (what); }

std::uint32_t be32 (std::string_view b, std::size_t at)
{
    return (std::uint32_t (std::uint8_t (b[at])) << 24) | (std::uint32_t (std::uint8_t (b[at + 1])) << 16)
         | (std::uint32_t (std::uint8_t (b[at + 2])) << 8) | std::uint32_t (std::uint8_t (b[at + 3]));
}

struct Lyric { std::uint64_t tick; std::size_t track; std::size_t order; std::string text; };
struct Tempo { std::uint64_t tick; std::size_t track; std::uint32_t us; };
struct RawNote { std::uint64_t start, end; int key; };

std::string trimmed (const std::string& s)
{
    const auto ws = [] (char c) { return c == ' ' || c == '\t' || c == '\r' || c == '\n'; };
    std::size_t a = 0, b = s.size();
    while (a < b && ws (s[a])) ++a;
    while (b > a && ws (s[b - 1])) --b;
    return s.substr (a, b - a);
}
} // namespace

MidiImport importMidi (std::string_view b)
{
    need (b.size() >= 14 && b.substr (0, 4) == "MThd", "missing MThd header");
    const std::uint32_t hl = be32 (b, 4);
    need (hl >= 6 && std::uint64_t (hl) + 8 <= b.size(), "bad header length");
    const unsigned fmt = (std::uint8_t (b[8]) << 8) | std::uint8_t (b[9]);
    const unsigned div = (std::uint8_t (b[12]) << 8) | std::uint8_t (b[13]);
    need (fmt == 0 || fmt == 1, "format 2 files are not supported");
    need ((div & 0x8000) == 0, "SMPTE time division is not supported");
    need (div > 0, "PPQ must be greater than 0");

    std::size_t pos = 8 + hl;
    std::vector<std::string_view> tracks;
    while (pos < b.size()) {
        need (pos + 8 <= b.size(), "truncated chunk header");
        const std::uint32_t ln = be32 (b, pos + 4);
        need (std::uint64_t (pos) + 8 + ln <= b.size(), "chunk length past the end of the file");
        if (b.substr (pos, 4) == "MTrk") tracks.push_back (b.substr (pos + 8, ln));
        pos += 8 + std::size_t (ln);
    }

    std::vector<RawNote> notes;
    std::vector<Lyric> lyrics;
    std::vector<Tempo> tempos;
    const auto addNote = [&] (std::uint64_t s, std::uint64_t e, int key) {
        if (e <= s) return;
        if (notes.size() >= kMaxNotes) bad ("more than 5000 notes (limit 5000)");
        notes.push_back ({ s, e, key });
    };

    for (std::size_t ti = 0; ti < tracks.size(); ++ti) {
        const std::string_view d = tracks[ti];
        std::size_t i = 0, order = 0;
        std::uint64_t tick = 0;
        int run = -1;
        std::map<std::pair<int, int>, std::uint64_t> held;
        const auto vlq = [&] {
            std::uint32_t v = 0;
            for (int k = 0; k < 4; ++k) {
                need (i < d.size(), "truncated variable-length quantity");
                const auto c = std::uint8_t (d[i++]);
                v = (v << 7) | (c & 0x7F);
                if (! (c & 0x80)) return v;
            }
            bad ("variable-length quantity longer than 4 bytes");
        };
        while (i < d.size()) {
            tick += vlq();
            need (i < d.size(), "truncated event");
            int s = std::uint8_t (d[i]);
            if (s >= 0x80) ++i;
            else { need (run >= 0, "data byte without running status"); s = run; }
            if (s == 0xFF) {
                need (i < d.size(), "truncated meta event");
                const int mt = std::uint8_t (d[i++]);
                const std::uint32_t ln = vlq();
                need (std::uint64_t (i) + ln <= d.size(), "meta event length past the end of the track");
                const std::string_view data = d.substr (i, ln);
                i += ln;
                if (mt == 0x05) lyrics.push_back ({ tick, ti, order++, std::string (data) });
                else if (mt == 0x51) {
                    need (ln == 3, "tempo event must have 3 data bytes");
                    const std::uint32_t us = (std::uint32_t (std::uint8_t (data[0])) << 16) | (std::uint32_t (std::uint8_t (data[1])) << 8) | std::uint8_t (data[2]);
                    need (us > 0, "tempo of 0 microseconds per quarter note");
                    tempos.push_back ({ tick, ti, us });
                } else if (mt == 0x2F) break;
            } else if (s == 0xF0 || s == 0xF7) {
                const std::uint32_t ln = vlq();
                need (std::uint64_t (i) + ln <= d.size(), "sysex length past the end of the track");
                i += ln;
            } else if (s >= 0x80 && s <= 0xEF) {
                run = s;
                const int hi = s & 0xF0;
                const std::size_t nb = (hi == 0xC0 || hi == 0xD0) ? 1 : 2;
                need (i + nb <= d.size(), "truncated channel message");
                const int d0 = std::uint8_t (d[i]), d1 = nb == 2 ? std::uint8_t (d[i + 1]) : 0;
                i += nb;
                if (hi == 0x80 || hi == 0x90) {
                    const std::pair<int, int> key { s & 0x0F, d0 };
                    const auto it = held.find (key);
                    if (it != held.end()) { addNote (it->second, tick, d0); held.erase (it); }
                    if (hi == 0x90 && d1 > 0) held[key] = tick;
                }
            } else bad ("invalid status byte");
        }
        for (const auto& h : held) addNote (h.second, tick, h.first.second);
    }

    MidiImport out;
    std::sort (notes.begin(), notes.end(), [] (const RawNote& a, const RawNote& c) {
        return std::tie (a.start, a.key) < std::tie (c.start, c.key);
    });
    for (const auto& n : notes) out.notes.push_back ({ double (n.start) / div, double (n.end) / div, n.key });

    std::stable_sort (lyrics.begin(), lyrics.end(), [] (const Lyric& a, const Lyric& c) {
        return std::tie (a.tick, a.track, a.order) < std::tie (c.tick, c.track, c.order);
    });
    for (const auto& l : lyrics) {
        const auto w = trimmed (l.text);
        if (w.empty()) continue;
        if (! out.lyrics.empty()) out.lyrics += ' ';
        out.lyrics += w;
    }

    if (! tempos.empty()) {
        const auto first = *std::min_element (tempos.begin(), tempos.end(), [] (const Tempo& a, const Tempo& c) {
            return std::tie (a.tick, a.track) < std::tie (c.tick, c.track);
        });
        out.bpm = 60e6 / double (first.us);
        bool later = false;
        std::uint64_t minTick = 0;
        for (const auto& t : tempos)
            if (t.tick > first.tick && t.us != first.us && (! later || t.tick < minTick)) { later = true; minTick = t.tick; }
        if (later) {
            std::ostringstream os;
            os.imbue (std::locale::classic());
            os << "tempo changes after beat " << double (minTick) / div << " are ignored";
            out.warnings.push_back (os.str());
        }
    }

    for (const auto& n : out.notes)
        if (n.endBeat * 60.0 / out.bpm > kMaxSeconds) bad ("a note ends more than 900 s after time 0 (limit 900 s)");
    return out;
}

} // namespace singvst
