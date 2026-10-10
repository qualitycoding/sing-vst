// Interface frozen by plan D-003; plugin behaviour in D-010, D-022, D-027. Implemented in S-011.
#pragma once
#include <juce_audio_processors/juce_audio_processors.h>
#include <atomic>
#include <memory>
#include <string>
#include <vector>
#include "singvst/playback.hpp"
#include "singvst/render.hpp"

static_assert (JUCE_MAJOR_VERSION == 9, "sing-vst is pinned to JUCE 9.0.3 (D-001)");

namespace singvst {

/** Capture state machine (D-010): Idle -> Armed (button) -> Capturing (transport starts while armed) -> Idle (transport stops:
    captured notes are stored and a render is submitted). Disarm returns to Idle without changing stored notes. */
enum class CaptureState { Idle, Armed, Capturing };

class SingVstProcessor final : public juce::AudioProcessor {
public:
    SingVstProcessor();
    ~SingVstProcessor() override;

    // juce::AudioProcessor
    const juce::String getName() const override;
    void prepareToPlay (double sampleRate, int maximumExpectedSamplesPerBlock) override;
    void releaseResources() override;
    bool isBusesLayoutSupported (const BusesLayout&) const override;          // stereo or mono output, no input
    void processBlock (juce::AudioBuffer<float>&, juce::MidiBuffer&) override; // D-022: no locks, no allocation
    juce::AudioProcessorEditor* createEditor() override;
    bool hasEditor() const override;
    bool acceptsMidi() const override;
    bool producesMidi() const override;
    double getTailLengthSeconds() const override;
    int getNumPrograms() override;
    int getCurrentProgram() override;
    void setCurrentProgram (int) override;
    const juce::String getProgramName (int) override;
    void changeProgramName (int, const juce::String&) override;
    void getStateInformation (juce::MemoryBlock&) override;                  // PluginState JSON (D-010), UTF-8
    void setStateInformation (const void*, int) override;                    // malformed state: keep defaults, set lastError

    juce::AudioProcessorValueTreeState& parameters() noexcept;               // built from kParams (params.hpp)

    // Message-thread controls used by the editor and by tests.
    void setLyrics (const juce::String& utf8);
    juce::String getLyrics() const;
    bool loadVoice (const juce::File& voiceDir);                             // validates (D-008); false + lastError on failure
    bool importMidiFile (const juce::File& midi);                            // notes + lyric meta events (D-010); false + lastError
    void arm (bool shouldArm);
    CaptureState captureState() const noexcept;
    std::vector<Note> storedNotes() const;
    RenderStatus renderStatus() const;
    juce::String lastError() const;
    std::vector<std::string> lastWarnings() const;

    /** Test seam (T-050, T-051): publishes a take as if a render had finished. Message thread only. */
    void publishTakeForTesting (std::unique_ptr<RenderedTake> take);

private:
    struct Impl;
    std::unique_ptr<Impl> impl;
    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR (SingVstProcessor)
};

} // namespace singvst
