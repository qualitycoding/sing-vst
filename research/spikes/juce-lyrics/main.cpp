// Spike R6 (C-013): JUCE 9.0.3 juce::MidiFile reads lyric meta events (0x05) with timestamps.
#include <juce_audio_basics/juce_audio_basics.h>
int main (int argc, char** argv) {
    if (argc < 2) return 1;
    juce::FileInputStream in { juce::File { juce::String { argv[1] } } };
    juce::MidiFile mf;
    if (! mf.readFrom (in)) return 2;
    mf.convertTimestampTicksToSeconds();
    for (auto* e : *mf.getTrack (0)) {
        const auto& m = e->message;
        if (m.isMetaEvent() && m.getMetaEventType() == 0x05) std::printf ("lyric t=%.3f '%s'\n", m.getTimeStamp(), m.getTextFromTextMetaEvent().toRawUTF8());
        if (m.isNoteOn()) std::printf ("note  t=%.3f %d\n", m.getTimeStamp(), m.getNoteNumber());
    }
    return 0;
}
