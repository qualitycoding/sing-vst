// Interface frozen by plan D-003; rules in D-006.
#pragma once
#include <string>
#include <vector>
#include "singvst/g2p.hpp"
#include "singvst/lyrics.hpp"

namespace singvst {

/** A note in quarter-note beats (PPQ) from the start of the host timeline; the note sounds on [startBeat, endBeat). */
struct Note {
    double startBeat = 0.0;
    double endBeat = 0.0;
    int midiNote = 60;
    bool operator== (const Note&) const = default;
};

/** D-006: drops notes of length <= 1e-9 beats, sorts by (start, pitch descending), keeps only the highest pitch among notes
    whose starts are within 1e-9 beats, truncates an earlier note at the next kept start, and drops notes of length <= 1e-9. */
std::vector<Note> toMonophonic (std::vector<Note> notes);

struct NoteAssignment {
    Note note;
    Phones phonemes;          // lower-case ARPAbet phones sung on this note
    bool isExtension = false; // melisma: holds the previous syllable's vowel
};

struct AlignmentResult {
    std::vector<NoteAssignment> notes;
    std::vector<std::string> warnings;
};

/** Assigns lyric syllables to monophonic notes by D-006. Never throws for content problems; reports them as warnings. */
AlignmentResult align (const std::vector<Note>& monophonic, const std::vector<LyricToken>& tokens, const Dictionary& dict);

} // namespace singvst
