#include "PluginEditor.h"
#include "singvst/params.hpp"

namespace singvst {
namespace {
juce::String statusText (const EditorStatus& s)
{
    juce::String voice = s.voiceName.empty() ? juce::String ("no voice") : juce::String::fromUTF8 (s.voiceName.c_str()) + " (" + s.voiceShaPrefix + ")";
    const char* render = "idle";
    switch (s.renderStatus) {
        case RenderStatus::Idle: render = "idle"; break;
        case RenderStatus::Rendering: render = "rendering..."; break;
        case RenderStatus::Ready: render = "ready"; break;
        case RenderStatus::Failed: render = "render failed"; break;
    }
    juce::String cap = s.captureState == CaptureState::Armed ? " | armed: press play" : s.captureState == CaptureState::Capturing ? " | capturing" : "";
    juce::String text = "Voice: " + voice + " | " + render + cap;
    if (s.error.size()) text += " | " + juce::String::fromUTF8 (s.error.c_str());
    return text;
}
} // namespace

SingVstEditor::SingVstEditor (SingVstProcessor& p, std::function<EditorStatus()> statusSource)
    : AudioProcessorEditor (p), processor (p), status (std::move (statusSource))
{
    lyrics.setMultiLine (true, true);
    lyrics.setReturnKeyStartsNewLine (true);
    lyrics.setTextToShowWhenEmpty ("Type lyrics: hel- lo +   (+ holds a vowel, [hh ah] gives phonemes)", juce::Colours::grey);
    lyrics.addListener (this);
    addAndMakeVisible (lyrics);

    for (auto* b : { &loadVoiceButton, &importMidiButton, &armButton }) addAndMakeVisible (*b);
    armButton.setClickingTogglesState (true);
    loadVoiceButton.onClick = [this] { chooseVoice(); };
    importMidiButton.onClick = [this] { chooseMidi(); };
    armButton.onClick = [this] { processor.arm (armButton.getToggleState()); };

    statusLabel.setJustificationType (juce::Justification::centredLeft);
    addAndMakeVisible (statusLabel);
    cacheLabel.setJustificationType (juce::Justification::centredLeft);
    addAndMakeVisible (cacheLabel);
    warningsBox.setMultiLine (true, true);
    warningsBox.setReadOnly (true);
    warningsBox.setTextToShowWhenEmpty ("Warnings appear here.", juce::Colours::grey);
    addAndMakeVisible (warningsBox);

    for (const auto& k : kParams) {
        auto c = std::make_unique<Control>();
        const juce::String id { std::string (k.id) }, name { std::string (k.name) };
        c->label.setText (name, juce::dontSendNotification);
        c->isToggle = k.step == 1.0f && k.maxValue == 1.0f && k.minValue == 0.0f;
        addAndMakeVisible (c->label);
        if (c->isToggle) {
            c->toggle.setButtonText (name);
            addAndMakeVisible (c->toggle);
            c->buttonAttachment = std::make_unique<juce::AudioProcessorValueTreeState::ButtonAttachment> (processor.parameters(), id, c->toggle);
        } else {
            c->slider.setSliderStyle (juce::Slider::LinearHorizontal);
            c->slider.setTextBoxStyle (juce::Slider::TextBoxRight, false, 90, 20);
            c->slider.setTextValueSuffix (" " + juce::String (std::string (k.unit)));
            addAndMakeVisible (c->slider);
            c->sliderAttachment = std::make_unique<juce::AudioProcessorValueTreeState::SliderAttachment> (processor.parameters(), id, c->slider);
        }
        controls.push_back (std::move (c));
    }

    setResizable (true, true);
    setResizeLimits (480, 420, 1400, 1000);
    setSize (640, 560);
    lyrics.setText (processor.getLyrics(), false);
    shownLyrics = processor.getLyrics();
    refresh();
    startTimerHz (4);
}

SingVstEditor::~SingVstEditor()
{
    stopTimer();
    lyrics.removeListener (this);
}

void SingVstEditor::paint (juce::Graphics& g) { g.fillAll (getLookAndFeel().findColour (juce::ResizableWindow::backgroundColourId)); }

void SingVstEditor::resized()
{
    auto area = getLocalBounds().reduced (10);
    auto buttons = area.removeFromTop (30);
    const int w = buttons.getWidth() / 3;
    loadVoiceButton.setBounds (buttons.removeFromLeft (w).reduced (2));
    importMidiButton.setBounds (buttons.removeFromLeft (w).reduced (2));
    armButton.setBounds (buttons.reduced (2));
    area.removeFromTop (6);
    statusLabel.setBounds (area.removeFromTop (24));
    cacheLabel.setBounds (area.removeFromTop (20));
    auto controlsArea = area.removeFromBottom (static_cast<int> (controls.size()) * 30 + 4);
    auto warnings = area.removeFromBottom (juce::jmax (60, area.getHeight() / 4));
    warningsBox.setBounds (warnings.reduced (0, 2));
    lyrics.setBounds (area.reduced (0, 2));
    for (auto& c : controls) {
        auto row = controlsArea.removeFromTop (30);
        c->label.setBounds (row.removeFromLeft (150));
        if (c->isToggle) c->toggle.setBounds (row);
        else c->slider.setBounds (row);
    }
}

void SingVstEditor::refresh()
{
    const auto s = status();
    statusLabel.setText (statusText (s), juce::dontSendNotification);
    cacheLabel.setText ("Take cache: " + juce::File::descriptionOfSizeInBytes (s.cacheBytes), juce::dontSendNotification);
    juce::String w;
    for (const auto& line : s.warnings) w += juce::String::fromUTF8 (line.c_str()) + "\n";
    if (warningsBox.getText() != w) warningsBox.setText (w, false);
    const bool armed = s.captureState != CaptureState::Idle;
    if (armButton.getToggleState() != armed) armButton.setToggleState (armed, juce::dontSendNotification);

    // Show lyrics that changed outside the box (MIDI import, restored state), but never fight the user's typing.
    const auto current = processor.getLyrics();
    if (current != shownLyrics && ! lyrics.hasKeyboardFocus (true)) {
        refreshing = true;
        lyrics.setText (current, false);
        refreshing = false;
        shownLyrics = current;
    }
}

void SingVstEditor::timerCallback() { refresh(); }

void SingVstEditor::textEditorTextChanged (juce::TextEditor&)
{
    if (refreshing) return;
    shownLyrics = lyrics.getText();
    processor.setLyrics (shownLyrics);   // the processor re-renders 500 ms after the last keystroke
}

void SingVstEditor::chooseVoice()
{
    chooser = std::make_unique<juce::FileChooser> ("Select the voice folder (contains manifest.json)", juce::File(), "");
    juce::Component::SafePointer<SingVstEditor> safe (this);
    chooser->launchAsync (juce::FileBrowserComponent::openMode | juce::FileBrowserComponent::canSelectDirectories, [safe] (const juce::FileChooser& fc) {
        if (safe == nullptr) return;
        const auto f = fc.getResult();
        if (f != juce::File()) safe->processor.loadVoice (f);
    });
}

void SingVstEditor::chooseMidi()
{
    chooser = std::make_unique<juce::FileChooser> ("Select a MIDI file with lyric events", juce::File(), "*.mid;*.midi");
    juce::Component::SafePointer<SingVstEditor> safe (this);
    chooser->launchAsync (juce::FileBrowserComponent::openMode | juce::FileBrowserComponent::canSelectFiles, [safe] (const juce::FileChooser& fc) {
        if (safe == nullptr) return;
        const auto f = fc.getResult();
        if (f != juce::File()) safe->processor.importMidiFile (f);
    });
}

} // namespace singvst
