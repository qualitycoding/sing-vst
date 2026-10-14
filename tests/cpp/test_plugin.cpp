// FROZEN — DO NOT MODIFY. Frozen by plan Phase 2E (tests/FROZEN_MANIFEST.sha256). Rules: plan/DECISIONS.md. Change only via TEST_CHALLENGE.md.
// Plugin tests drive SingVstProcessor headless: a fake host play head, MIDI buffers, and a pumped JUCE message loop.
// They load the ONNX Runtime library and cmudict.dict from beside this test executable, as the plugin does beside its module.
#include <catch2/catch_test_macros.hpp>
#include <catch2/matchers/catch_matchers_floating_point.hpp>
#include <algorithm>
#include <cmath>
#include <functional>
#include "PluginProcessor.h"
#include "helpers.hpp"
#include "singvst/params.hpp"
#include "singvst/playback.hpp"
using namespace singvst;
using Catch::Matchers::WithinAbs;

namespace {
struct Host final : juce::AudioPlayHead {
    double ppq = 0.0, bpm = 120.0; bool playing = false;
    juce::Optional<PositionInfo> getPosition() const override
    {
        PositionInfo p; p.setPpqPosition (ppq); p.setBpm (bpm); p.setIsPlaying (playing); return p;
    }
};
void gui() { static juce::ScopedJuceInitialiser_GUI init; }
/** Pumps the message loop until pred() is true or the timeout passes; returns pred(). */
bool pumpUntil (const std::function<bool()>& pred, int timeoutMs)
{
    const auto end = juce::Time::getMillisecondCounter() + (juce::uint32) timeoutMs;
    while (! pred() && juce::Time::getMillisecondCounter() < end) juce::MessageManager::getInstance()->runDispatchLoopUntil (20);
    return pred();
}
juce::RangedAudioParameter& param (SingVstProcessor& p, const char* id)
{
    auto* r = p.parameters().getParameter (id);
    if (r == nullptr) throw std::runtime_error (std::string ("no parameter ") + id);
    return *r;
}
void setParam (SingVstProcessor& p, const char* id, float v) { auto& r = param (p, id); r.setValueNotifyingHost (r.convertTo0to1 (v)); }
float getParam (SingVstProcessor& p, const char* id) { auto& r = param (p, id); return r.convertFrom0to1 (r.getValue()); }
juce::File fx (const char* rel) { return juce::File { juce::String { testutil::fixture (rel).string() } }; }
std::unique_ptr<RenderedTake> constantTake (float v)
{
    auto t = std::make_unique<RenderedTake>(); t->startBeat = 0.0; t->bpm = 120.0; t->sampleRate = 48000;
    t->samples.assign (96000, v); t->unclippedPeak = v; return t;
}
} // namespace

TEST_CASE ("T-053 the plugin exposes exactly the kParams table, in order (D-010, PK-40)", "[plugin]") {
    gui(); SingVstProcessor p;
    const auto& ps = p.getParameters();
    REQUIRE ((size_t) ps.size() == kParams.size());
    for (size_t i = 0; i < kParams.size(); ++i) {
        const auto& k = kParams[i];
        auto* r = dynamic_cast<juce::RangedAudioParameter*> (ps[(int) i]);
        REQUIRE (r != nullptr);
        INFO (std::string (k.id));
        CHECK (r->getParameterID() == juce::String (std::string (k.id)));
        CHECK (r->getName (100) == juce::String (std::string (k.name)));
        CHECK (r->getLabel() == juce::String (std::string (k.unit)));
        CHECK (r->getNormalisableRange().start == k.minValue);
        CHECK (r->getNormalisableRange().end == k.maxValue);
        CHECK (r->getNormalisableRange().interval == k.step);
        CHECK_THAT (r->convertFrom0to1 (r->getDefaultValue()), WithinAbs (k.defaultValue, 1e-5));
        CHECK (p.parameters().getParameter (juce::String (std::string (k.id))) == r);
    }
}

TEST_CASE ("T-054 state saves as PluginState JSON and restores lyrics, parameters and voice; bad state keeps defaults (D-010)", "[plugin]") {
    gui();
    SingVstProcessor a;
    a.setLyrics (juce::String::fromUTF8 ("hel-lo w\xC3\xB6rld +"));
    setParam (a, "vibrato", 25.0f);
    setParam (a, "gain", -6.0f);
    setParam (a, "convert", 0.0f);
    REQUIRE (a.loadVoice (fx ("voice-legacy")));
    juce::MemoryBlock mb; a.getStateInformation (mb);
    const auto st = pluginStateFromJson (mb.toString().toStdString());       // the state is the D-010 JSON, UTF-8
    CHECK (st.lyrics == "hel-lo w\xC3\xB6rld +");
    CHECK (st.outputGainDb == -6.0);
    SingVstProcessor b;
    b.setStateInformation (mb.getData(), (int) mb.getSize());
    CHECK (b.getLyrics() == a.getLyrics());
    CHECK_THAT (getParam (b, "vibrato"), WithinAbs (25.0, 1e-4));
    CHECK_THAT (getParam (b, "gain"), WithinAbs (-6.0, 1e-4));
    CHECK (getParam (b, "convert") == 0.0f);
    CHECK (b.lastError().isEmpty());                                         // voice restored from the stored path
    auto moved = st; moved.voicePath = "/nonexistent/voice";
    const auto j = toJson (moved);
    SingVstProcessor c;
    c.setStateInformation (j.data(), (int) j.size());
    CHECK (c.lastError().isNotEmpty());                                      // voice missing: error, lyrics kept
    CHECK (c.getLyrics() == a.getLyrics());
    SingVstProcessor d;
    d.setStateInformation ("garbage", 7);
    CHECK (d.lastError().isNotEmpty());
    CHECK (d.getLyrics().isEmpty());
    CHECK_THAT (getParam (d, "vibrato"), WithinAbs (0.0, 1e-6));
}

TEST_CASE ("T-055 processBlock plays the published take on every channel with gain and soft clip; silence when stopped (D-021, D-022)", "[plugin]") {
    gui(); SingVstProcessor p; Host h; p.setPlayHead (&h);
    p.prepareToPlay (48000.0, 256);
    p.publishTakeForTesting (constantTake (0.5f));
    h.playing = true; h.ppq = 0.5;
    juce::AudioBuffer<float> buf (2, 256); juce::MidiBuffer midi;
    const auto all = [&] (const std::function<bool (float)>& ok) {
        for (int c = 0; c < buf.getNumChannels(); ++c) for (int i = 0; i < buf.getNumSamples(); ++i) if (! ok (buf.getSample (c, i))) return false;
        return true; };
    p.processBlock (buf, midi);
    CHECK (all ([] (float v) { return v == 0.5f; }));
    setParam (p, "gain", -6.0206f);
    p.processBlock (buf, midi);
    CHECK (all ([] (float v) { return std::abs (v - 0.25f) < 1e-4f; }));
    setParam (p, "gain", 12.0f);
    p.processBlock (buf, midi);
    CHECK (all ([] (float v) { return v <= 0.98f && v > 0.97f; }));
    setParam (p, "gain", 0.0f);
    midi.addEvent (juce::MidiMessage::noteOn (1, 60, 0.8f), 0);             // live MIDI does not play (not capturing)
    p.processBlock (buf, midi);
    CHECK (all ([] (float v) { return v == 0.5f; }));
    h.playing = false;
    p.processBlock (buf, midi);
    CHECK (all ([] (float v) { return v == 0.0f; }));
    SingVstProcessor m; Host hm; hm.playing = true; hm.ppq = 0.5; m.setPlayHead (&hm);
    juce::AudioProcessor::BusesLayout mono; mono.outputBuses.add (juce::AudioChannelSet::mono());
    REQUIRE (m.setBusesLayout (mono));
    m.prepareToPlay (48000.0, 256); m.publishTakeForTesting (constantTake (0.5f));
    juce::AudioBuffer<float> one (1, 256);
    m.processBlock (one, midi);
    CHECK (one.getSample (0, 100) == 0.5f);
}

TEST_CASE ("T-056 importMidiFile replaces notes, lyrics and tempo; bad files change nothing (D-010, D-031)", "[plugin]") {
    gui(); SingVstProcessor p;
    REQUIRE (p.importMidiFile (fx ("lyrics.mid")));
    CHECK (p.storedNotes() == std::vector<Note> { { 0, 1, 60 }, { 1, 2, 62 }, { 2, 3, 64 } });
    CHECK (p.getLyrics() == "hel- lo world");
    CHECK (pumpUntil ([&] { return p.lastError() == "Load a voice"; }, 2000));   // no voice: nothing rendered
    CHECK (p.renderStatus() == RenderStatus::Idle);
    CHECK_FALSE (p.importMidiFile (fx ("smpte.mid")));
    CHECK (p.lastError().isNotEmpty());
    CHECK (p.storedNotes() == std::vector<Note> { { 0, 1, 60 }, { 1, 2, 62 }, { 2, 3, 64 } });
    CHECK (p.getLyrics() == "hel- lo world");
    REQUIRE (p.importMidiFile (fx ("complex.mid")));
    CHECK (p.getLyrics() == "a b c");
    const auto w = p.lastWarnings();
    CHECK (std::find (w.begin(), w.end(), "tempo changes after beat 2 are ignored") != w.end());
}

TEST_CASE ("T-057 capture: Idle -> Armed -> Capturing -> Idle with sample-accurate note positions (D-010, D-022)", "[plugin]") {
    gui(); SingVstProcessor p; Host h; p.setPlayHead (&h);
    p.prepareToPlay (48000.0, 480);                                         // 480 samples = 0.02 beat at 120 bpm
    CHECK (p.captureState() == CaptureState::Idle);
    p.arm (true);
    CHECK (p.captureState() == CaptureState::Armed);
    juce::AudioBuffer<float> buf (2, 480); juce::MidiBuffer midi;
    p.processBlock (buf, midi);                                             // stopped: still armed
    CHECK (p.captureState() == CaptureState::Armed);
    h.playing = true; h.ppq = 4.0;
    midi.addEvent (juce::MidiMessage::noteOn (1, 60, 0.8f), 0);
    p.processBlock (buf, midi);
    CHECK (p.captureState() == CaptureState::Capturing);
    midi.clear(); h.ppq = 4.02;
    midi.addEvent (juce::MidiMessage::noteOff (1, 60), 240);                // 4.02 + 240 * 120 / (60 * 48000) = 4.03
    midi.addEvent (juce::MidiMessage::noteOn (1, 64, 0.8f), 240);
    p.processBlock (buf, midi);
    midi.clear(); h.ppq = 4.04;
    p.processBlock (buf, midi);
    h.playing = false; h.ppq = 0.0;                                          // host may jump on stop; capture ends at 4.06
    p.processBlock (buf, midi);
    REQUIRE (pumpUntil ([&] { return p.captureState() == CaptureState::Idle && p.storedNotes().size() == 2; }, 3000));
    const auto n = p.storedNotes();
    CHECK_THAT (n[0].startBeat, WithinAbs (4.0, 1e-9));
    CHECK_THAT (n[0].endBeat, WithinAbs (4.03, 1e-9));
    CHECK (n[0].midiNote == 60);
    CHECK_THAT (n[1].startBeat, WithinAbs (4.03, 1e-9));
    CHECK_THAT (n[1].endBeat, WithinAbs (4.06, 1e-9));
    CHECK (n[1].midiNote == 64);
    p.arm (true);
    p.arm (false);                                                          // disarm keeps the stored notes
    CHECK (p.captureState() == CaptureState::Idle);
    CHECK (p.storedNotes().size() == 2);
}

TEST_CASE ("T-058 loadVoice validates; an imported phrase renders in the background and plays (D-008, D-010, D-013)", "[plugin]") {
    gui(); SingVstProcessor p; Host h; p.setPlayHead (&h);
    p.prepareToPlay (48000.0, 512);
    CHECK_FALSE (p.loadVoice (juce::File ("/nonexistent/voice")));
    CHECK (p.lastError().isNotEmpty());
    REQUIRE (p.loadVoice (fx ("voice-convert")));
    REQUIRE (p.importMidiFile (fx ("lyrics.mid")));
    REQUIRE (pumpUntil ([&] { return p.renderStatus() == RenderStatus::Ready; }, 20000));
    h.playing = true; h.ppq = 0.5;
    juce::AudioBuffer<float> buf (2, 512); juce::MidiBuffer midi;
    p.processBlock (buf, midi);
    CHECK (buf.getMagnitude (0, 0, 512) > 0.0f);
    CHECK (buf.getMagnitude (0, 0, 512) <= 0.98f);
}
