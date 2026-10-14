// STUB until S-011: a silent, valid instrument (pluginval can load it; D-023) whose sing-vst controls throw NotImplemented.
// It deliberately exposes no parameters and keeps no state, so T-053..T-058 fail against it (PK-25).
#include "PluginProcessor.h"
#include "singvst/errors.hpp"

namespace singvst {

struct SingVstProcessor::Impl {
    explicit Impl (juce::AudioProcessor& p) : apvts { p, nullptr, "PARAMS", {} } {}
    juce::AudioProcessorValueTreeState apvts;
};

SingVstProcessor::SingVstProcessor()
    : AudioProcessor (BusesProperties().withOutput ("Output", juce::AudioChannelSet::stereo(), true)),
      impl { std::make_unique<Impl> (*this) } {}
SingVstProcessor::~SingVstProcessor() = default;

const juce::String SingVstProcessor::getName() const { return "Sing VST"; }
void SingVstProcessor::prepareToPlay (double, int) {}
void SingVstProcessor::releaseResources() {}
bool SingVstProcessor::isBusesLayoutSupported (const BusesLayout& l) const
{
    const auto out = l.getMainOutputChannelSet();
    return l.getMainInputChannelSet().isDisabled() && (out == juce::AudioChannelSet::stereo() || out == juce::AudioChannelSet::mono());
}
void SingVstProcessor::processBlock (juce::AudioBuffer<float>& buffer, juce::MidiBuffer&) { buffer.clear(); }
juce::AudioProcessorEditor* SingVstProcessor::createEditor() { return new juce::GenericAudioProcessorEditor (*this); }
bool SingVstProcessor::hasEditor() const { return true; }
bool SingVstProcessor::acceptsMidi() const { return true; }
bool SingVstProcessor::producesMidi() const { return false; }
double SingVstProcessor::getTailLengthSeconds() const { return 0.0; }
int SingVstProcessor::getNumPrograms() { return 1; }
int SingVstProcessor::getCurrentProgram() { return 0; }
void SingVstProcessor::setCurrentProgram (int) {}
const juce::String SingVstProcessor::getProgramName (int) { return {}; }
void SingVstProcessor::changeProgramName (int, const juce::String&) {}
void SingVstProcessor::getStateInformation (juce::MemoryBlock&) {}
void SingVstProcessor::setStateInformation (const void*, int) {}
juce::AudioProcessorValueTreeState& SingVstProcessor::parameters() noexcept { return impl->apvts; }

void SingVstProcessor::setLyrics (const juce::String&) { throw NotImplemented ("SingVstProcessor::setLyrics"); }
juce::String SingVstProcessor::getLyrics() const { throw NotImplemented ("SingVstProcessor::getLyrics"); }
bool SingVstProcessor::loadVoice (const juce::File&) { throw NotImplemented ("SingVstProcessor::loadVoice"); }
bool SingVstProcessor::importMidiFile (const juce::File&) { throw NotImplemented ("SingVstProcessor::importMidiFile"); }
void SingVstProcessor::arm (bool) { throw NotImplemented ("SingVstProcessor::arm"); }
CaptureState SingVstProcessor::captureState() const noexcept { return static_cast<CaptureState> (-1); }
std::vector<Note> SingVstProcessor::storedNotes() const { throw NotImplemented ("SingVstProcessor::storedNotes"); }
RenderStatus SingVstProcessor::renderStatus() const { throw NotImplemented ("SingVstProcessor::renderStatus"); }
juce::String SingVstProcessor::lastError() const { throw NotImplemented ("SingVstProcessor::lastError"); }
std::vector<std::string> SingVstProcessor::lastWarnings() const { throw NotImplemented ("SingVstProcessor::lastWarnings"); }
void SingVstProcessor::publishTakeForTesting (std::unique_ptr<RenderedTake>) { throw NotImplemented ("SingVstProcessor::publishTakeForTesting"); }

} // namespace singvst

juce::AudioProcessor* JUCE_CALLTYPE createPluginFilter() { return new singvst::SingVstProcessor(); }
