// Interface frozen by plan D-003; rules in D-007 and D-021.
#pragma once
#include <cstdint>
#include <string>
#include <vector>
#include "singvst/align.hpp"

namespace singvst {

struct PhonemeSpan {
    std::string phoneme;   // lower-case ARPAbet, or "SP" for silence
    double startSec = 0.0;
    double endSec = 0.0;
};

/** Equal temperament, A4 (MIDI 69) = 440 Hz. */
double midiToHz (double midiNote);

/** Contiguous phoneme spans covering [0, end of the last note] with note times taken relative to the first note's start;
    gaps become "SP". Onset/coda placement and clamping by D-007. */
std::vector<PhonemeSpan> layoutPhonemes (const std::vector<NoteAssignment>& notes, double bpm, double consonantSec = 0.06);

/** f0 in Hz per frame (0 = unvoiced) for times i / frameRateHz, i in [0, ceil(totalSec * frameRateHz)), note times relative
    to the first note's start. Portamento and vibrato by D-007. */
std::vector<float> f0Curve (const std::vector<NoteAssignment>& notes, double bpm, double frameRateHz, double totalSec,
                            double portamentoSec = 0.06, double vibratoCents = 0.0, double vibratoHz = 5.5);

/** RVC coarse pitch bin 1..255 for a frequency in Hz, as RVC infer/vc/pipeline.py get_f0 (f0_min 50 Hz, f0_max 1100 Hz) (C-021). */
int rvcCoarsePitch (double hz);

/** Converts spans to frame counts by D-007: every count >= 1 and the sum equals round(lastEnd * frameRateHz).
    Throws ValidationError when that total is smaller than the number of spans. */
std::vector<std::int64_t> spansToFrameDurations (const std::vector<PhonemeSpan>& spans, double frameRateHz);

/** Output soft clip (D-021): identity for |x| <= 0.8*ceiling, then a tanh knee that approaches but never reaches ceiling;
    odd-symmetric and monotonic. Safe on the audio thread. */
float softClip (float x, float ceiling = 0.98f) noexcept;

/** Largest absolute sample value (0 for empty input). */
float peakAbs (const std::vector<float>& x) noexcept;

} // namespace singvst
