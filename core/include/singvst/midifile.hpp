// Interface frozen by plan D-003; Standard MIDI File import rules in D-031.
#pragma once
#include <string>
#include <string_view>
#include <vector>
#include "singvst/align.hpp"

namespace singvst {

struct MidiImport {
    std::vector<Note> notes;            // all tracks and channels, beats = ticks / PPQ, sorted by (start, pitch)
    std::string lyrics;                 // lyric meta events (0x05) in time order, each trimmed, joined with one space
    double bpm = 120.0;                 // first tempo event, else 120
    std::vector<std::string> warnings;  // e.g. later tempo changes ignored
};

/** Parses a Standard MIDI File (format 0 or 1, PPQ timing) per D-031. The bytes are untrusted (PK-42): any malformed
    structure, format 2, or SMPTE timing throws ValidationError naming the problem; never reads out of bounds. */
MidiImport importMidi (std::string_view bytes);

} // namespace singvst
