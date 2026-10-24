// Sing VST editor (D-027): lyrics, Load voice, Import MIDI, Arm capture, status line, warnings and the kParams controls.
#pragma once
#include <functional>
#include <memory>
#include <string>
#include <vector>
#include "PluginProcessor.h"

namespace singvst {

/** What the editor shows beside the controls; read from the processor under its message mutex (D-010). */
struct EditorStatus {
    std::string voiceName, voiceShaPrefix;   // empty when no voice is loaded
    RenderStatus renderStatus = RenderStatus::Idle;
    std::string error;
    std::vector<std::string> warnings;
    CaptureState captureState = CaptureState::Idle;
    juce::int64 cacheBytes = 0;
};

class SingVstEditor final : public juce::AudioProcessorEditor, private juce::Timer, private juce::TextEditor::Listener {
public:
    SingVstEditor (SingVstProcessor&, std::function<EditorStatus()> statusSource);
    ~SingVstEditor() override;
    void resized() override;
    void paint (juce::Graphics&) override;

private:
    void timerCallback() override;
    void textEditorTextChanged (juce::TextEditor&) override;
    void chooseVoice();
    void chooseMidi();
    void refresh();

    SingVstProcessor& processor;
    std::function<EditorStatus()> status;

    juce::TextEditor lyrics;
    juce::TextButton loadVoiceButton { "Load voice..." }, importMidiButton { "Import MIDI..." }, armButton { "Arm capture" };
    juce::Label statusLabel, cacheLabel;
    juce::TextEditor warningsBox;

    struct Control {
        juce::Label label;
        juce::Slider slider;
        juce::ToggleButton toggle;
        std::unique_ptr<juce::AudioProcessorValueTreeState::SliderAttachment> sliderAttachment;
        std::unique_ptr<juce::AudioProcessorValueTreeState::ButtonAttachment> buttonAttachment;
        bool isToggle = false;
    };
    std::vector<std::unique_ptr<Control>> controls;

    std::unique_ptr<juce::FileChooser> chooser;
    juce::String shownLyrics;
    bool refreshing = false;

    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR (SingVstEditor)
};

} // namespace singvst
