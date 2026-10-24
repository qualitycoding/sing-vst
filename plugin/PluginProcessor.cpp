// Sing VST processor (D-010, D-022, D-027). Audio thread: no locks, no allocation. Message thread: one recursive mutex guards
// all editable state; processBlock never takes it.
#include "PluginProcessor.h"
#include "PluginEditor.h"
#include "singvst/errors.hpp"
#include "singvst/g2p.hpp"
#include "singvst/lyrics.hpp"
#include "singvst/midifile.hpp"
#include "singvst/ort_runtime.hpp"
#include "singvst/params.hpp"
#include "singvst/synthesis.hpp"
#include "singvst/take_cache.hpp"
#include "singvst/voice.hpp"
#include <condition_variable>
#include <mutex>
#include <optional>
#include <thread>

namespace singvst {
namespace {
constexpr int kFifoSize = 4096;
constexpr double kBpmTolerance = 0.1;
constexpr juce::uint32 kLyricDebounceMs = 500;
constexpr int kTimerHz = 4;
constexpr int kBlockSilenceMs = 2000;

// Capture state values (D-022): the three public ones plus Stopping, Cancelling and CancelAck.
enum Cap : int { kIdle = 0, kArmed = 1, kCapturing = 2, kStopping = 3, kCancelling = 4, kCancelAck = 5 };

struct CaptureEvent { double ppq = 0.0; int note = 0; bool on = false; };

struct Voice {
    VoiceManifest manifest;
    std::string sha;
    std::shared_ptr<GuideEngine> guide;
    std::shared_ptr<ConverterEngine> converter;
};

std::filesystem::path toPath (const juce::File& f)
{
#if JUCE_WINDOWS
    return std::filesystem::path (std::wstring (f.getFullPathName().toWideCharPointer()));   // non-ASCII folders survive
#else
    return std::filesystem::path (f.getFullPathName().toStdString());
#endif
}
juce::File moduleDir() { return juce::File::getSpecialLocation (juce::File::currentExecutableFile).getParentDirectory(); }
juce::File cacheDirectory()
{
    return juce::File::getSpecialLocation (juce::File::userApplicationDataDirectory).getChildFile ("sing-vst").getChildFile ("takes");
}

juce::AudioProcessorValueTreeState::ParameterLayout makeLayout()
{
    juce::AudioProcessorValueTreeState::ParameterLayout layout;
    for (const auto& k : kParams)
        layout.add (std::make_unique<juce::AudioParameterFloat> (
            juce::ParameterID { juce::String (std::string (k.id)), 1 }, juce::String (std::string (k.name)),
            juce::NormalisableRange<float> (k.minValue, k.maxValue, k.step), k.defaultValue,
            juce::AudioParameterFloatAttributes().withLabel (juce::String (std::string (k.unit)))));
    return layout;
}
} // namespace

struct SingVstProcessor::Impl : private juce::Timer {
    explicit Impl (SingVstProcessor& p)
        : apvts (p, nullptr, "PARAMS", makeLayout()),
          fifo (kFifoSize),
          fifoData (static_cast<std::size_t> (kFifoSize)),
          alive (std::make_shared<std::atomic<bool>> (true)),
          renderer (cachedRender ([this] (const RenderRequest& r, const std::atomic<bool>& cancel) { return runRender (r, cancel); },
                                  toPath (cacheDirectory())))
    {
        pGain = apvts.getRawParameterValue ("gain");
        pConvert = apvts.getRawParameterValue ("convert");
        pPort = apvts.getRawParameterValue ("portamento");
        pVib = apvts.getRawParameterValue ("vibrato");
        pSeed = apvts.getRawParameterValue ("seed");
        worker = std::thread ([this] { workerLoop(); });
        startTimerHz (kTimerHz);
    }

    ~Impl() override
    {
        alive->store (false);
        stopTimer();
        {
            std::lock_guard<std::mutex> l (wm);
            stopWorker = true;
            job.reset();
        }
        wcv.notify_all();
        if (worker.joinable()) worker.join();
        // `renderer` (declared last) is destroyed first: it cancels and joins its thread before the engines go away.
    }

    // ---------------------------------------------------------------- helpers (message thread, mtx held)
    void setErr (const std::string& s) { lastErr = s; }

    RenderParams currentParams() const
    {
        RenderParams rp;
        {
            std::lock_guard<std::mutex> l (voiceMtx);
            rp.voiceId = voice ? voice->sha : std::string();
        }
        rp.bpm = storedBpm;
        rp.outputSampleRate = 48000;
        rp.conversionEnabled = pConvert->load() >= 0.5f;
        rp.portamentoSec = pPort->load();
        rp.vibratoCents = pVib->load();
        rp.seed = static_cast<std::uint64_t> (std::max (0.0f, pSeed->load()) + 0.5f);
        return rp;
    }

    std::shared_ptr<Voice> voiceSnapshot() const { std::lock_guard<std::mutex> l (voiceMtx); return voice; }

    std::shared_ptr<const Dictionary> ensureDictionary()
    {
        {
            std::lock_guard<std::mutex> l (voiceMtx);
            if (dict) return dict;
        }
        const auto f = moduleDir().getChildFile ("cmudict.dict");
        if (! f.existsAsFile()) throw ValidationError ("cmudict.dict not found beside the plugin (" + f.getFullPathName().toStdString() + ")");
        const auto text = f.loadFileAsString().toStdString();
        auto d = std::make_shared<const Dictionary> (Dictionary::fromCmuText (text));
        std::lock_guard<std::mutex> l (voiceMtx);
        dict = d;
        return dict;
    }

    static void ensureRuntime()
    {
        if (! ortRuntimeLoaded()) (void) loadOrtRuntime (toPath (moduleDir().getChildFile (juce::String (bundledOrtFileName()))));
    }

    // The renderer's function (worker thread): takes its own references to the voice and dictionary (R-025).
    RenderedTake runRender (const RenderRequest& r, const std::atomic<bool>& cancel)
    {
        const auto v = voiceSnapshot();
        if (! v) throw ValidationError ("Load a voice");
        const auto d = ensureDictionary();
        std::vector<std::string> warnings;
        auto take = renderTake (r, *d, *v->guide, v->converter.get(), cancel, &warnings);
        std::lock_guard<std::mutex> l (rwm);
        renderWarnings = { take.contentHash, std::move (warnings) };
        return take;
    }

    /** Blocking conditions in D-010's order, then the request. Returns true when a request was submitted. */
    bool submitRender()
    {
        if (! voiceSnapshot()) { setErr ("Load a voice"); return false; }
        std::vector<LyricToken> tokens;
        try { tokens = parseLyrics (lyrics); }
        catch (const ParseError& e) { setErr (std::string ("Lyrics: ") + e.what()); return false; }
        if (notes.empty()) return false;
        try { (void) ensureDictionary(); }
        catch (const ValidationError& e) { setErr (e.what()); return false; }
        RenderRequest rq;
        rq.notes = notes;
        rq.tokens = std::move (tokens);
        rq.params = currentParams();
        lastSubmitted = rq.params;
        haveSubmitted = true;
        lyricsDirtyAt = 0;
        lastErr.clear();
        renderer.submit (std::move (rq));
        return true;
    }

    // ---------------------------------------------------------------- resample worker (D-010)
    struct Job { std::uint64_t gen = 0; std::shared_ptr<const RenderedTake> take; int rate = 0; };

    void postJob()
    {
        if (! originalTake) return;
        const int rate = static_cast<int> (hostRate.load() + 0.5);
        usedRate = rate;
        const auto gen = ++newestGen;
        {
            std::lock_guard<std::mutex> l (wm);
            job = Job { gen, originalTake, rate };
        }
        wcv.notify_one();
    }

    void workerLoop()
    {
        for (;;) {
            Job j;
            {
                std::unique_lock<std::mutex> l (wm);
                wcv.wait (l, [this] { return stopWorker || job.has_value(); });
                if (stopWorker) return;
                j = std::move (*job);
                job.reset();
            }
            std::shared_ptr<RenderedTake> out;
            try {
                out = (j.rate <= 0 || j.rate == j.take->sampleRate) ? std::make_shared<RenderedTake> (*j.take)
                                                                    : std::make_shared<RenderedTake> (resampleTake (*j.take, j.rate));
            } catch (...) { continue; }
            const auto flag = alive;
            juce::MessageManager::callAsync ([this, flag, gen = j.gen, out] {
                if (! flag->load()) return;
                publishFromWorker (gen, out);
            });
        }
    }

    void publishFromWorker (std::uint64_t gen, const std::shared_ptr<RenderedTake>& take)
    {
        std::lock_guard<std::recursive_mutex> l (mtx);
        if (gen != newestGen.load()) return;
        slot.publish (std::make_unique<RenderedTake> (*take));
        publishedGen = gen;
    }

    // ---------------------------------------------------------------- capture (D-022)
    bool casState (int expected, int desired) { return capState.compare_exchange_strong (expected, desired); }

    void armRequest (bool shouldArm)
    {
        if (shouldArm) {
            if (casState (kIdle, kArmed)) return;
            const int s = capState.load();
            if (s == kCancelling || s == kCancelAck) pendingArm = true;
        } else {
            pendingArm = false;
            if (casState (kArmed, kIdle)) return;
            (void) casState (kCapturing, kCancelling);
        }
    }

    CaptureState publicCaptureState() const
    {
        switch (capState.load()) {
            case kArmed: return CaptureState::Armed;
            case kCapturing: case kStopping: return CaptureState::Capturing;
            default: return CaptureState::Idle;
        }
    }

    void drainFifo (CaptureRecorder& rec)
    {
        const int ready = fifo.getNumReady();
        if (ready <= 0) return;
        const auto rd = fifo.read (ready);
        rd.forEach ([&] (int i) {
            const auto& e = fifoData[static_cast<std::size_t> (i)];
            if (e.on) rec.noteOn (e.ppq, e.note); else rec.noteOff (e.ppq, e.note);
        });
    }

    void applyPendingArm()
    {
        if (pendingArm.exchange (false)) (void) casState (kIdle, kArmed);
    }

    void handleCapture()
    {
        const int s = capState.load();
        if (s == kStopping) {
            CaptureRecorder rec;
            drainFifo (rec);
            notes = rec.finish (captureEnd.load());
            const double hb = hostBpm.load();
            if (hb > 0.0) storedBpm = hb;
            baseWarnings.clear();
            const int lost = dropped.exchange (0);
            if (lost > 0) baseWarnings.push_back ("capture buffer full: " + std::to_string (lost) + " events dropped");
            heldCaptureWarning = "stored notes replaced; the previous take stays in the take cache";
            heldRestoreWarning.clear();
            fifo.reset();
            capState.store (kIdle);
            applyPendingArm();
            (void) submitRender();
        } else if (s == kCancelling || s == kCancelAck) {
            const bool acked = s == kCancelAck;
            const bool silent = juce::Time::getMillisecondCounter() - lastBlockMs.load() > static_cast<juce::uint32> (kBlockSilenceMs);
            if (acked || silent) {
                CaptureRecorder discard;
                drainFifo (discard);
                dropped.store (0);
                fifo.reset();
                capState.store (kIdle);
                applyPendingArm();
            }
        }
    }

    // ---------------------------------------------------------------- timer (message thread, 4 Hz)
    void timerCallback() override
    {
        std::lock_guard<std::recursive_mutex> l (mtx);
        handleCapture();

        const auto now = juce::Time::getMillisecondCounter();
        if (voiceSnapshot() != nullptr && ! notes.empty()) {
            bool resubmit = false;
            if (lyricsDirtyAt != 0 && now - lyricsDirtyAt >= kLyricDebounceMs) resubmit = true;
            if (haveSubmitted) {
                const auto cur = currentParams();
                if (cur.conversionEnabled != lastSubmitted.conversionEnabled || cur.portamentoSec != lastSubmitted.portamentoSec
                    || cur.vibratoCents != lastSubmitted.vibratoCents || cur.seed != lastSubmitted.seed)
                    resubmit = true;
                const double hb = hostBpm.load();
                if (hb > 0.0 && std::abs (hb - lastSubmitted.bpm) > kBpmTolerance) { storedBpm = hb; resubmit = true; }
            }
            if (resubmit) (void) submitRender();
        }

        const auto latestNow = renderer.latest();
        if (latestNow != seenLatest) {
            seenLatest = latestNow;
            originalTake = latestNow;
            {
                std::lock_guard<std::mutex> rl (rwm);
                if (latestNow && renderWarnings.first == latestNow->contentHash) baseWarnings = renderWarnings.second;
                else baseWarnings.clear();
            }
            postJob();
        } else if (originalTake && static_cast<int> (hostRate.load() + 0.5) != usedRate) {
            postJob();
        }
        if (renderer.status() == RenderStatus::Failed) setErr (renderer.lastError());
        (void) slot.collect();
    }

    // ---------------------------------------------------------------- status for the editor
    EditorStatus editorStatus()
    {
        std::lock_guard<std::recursive_mutex> l (mtx);
        EditorStatus s;
        if (const auto v = voiceSnapshot()) { s.voiceName = v->manifest.name; s.voiceShaPrefix = v->sha.substr (0, 8); }
        s.renderStatus = renderStatusLocked();
        s.error = lastErr;
        s.warnings = warningsLocked();
        s.captureState = publicCaptureState();
        const auto now = juce::Time::getMillisecondCounter();
        if (cacheSizeAt == 0 || now - cacheSizeAt > 5000) {
            cacheSizeAt = now | 1u;
            cacheSize = 0;
            for (const auto& f : cacheDirectory().findChildFiles (juce::File::findFiles, false, "*.take")) cacheSize += f.getSize();
        }
        s.cacheBytes = cacheSize;
        return s;
    }

    RenderStatus renderStatusLocked() const
    {
        const auto s = renderer.status();
        if (s == RenderStatus::Rendering) return RenderStatus::Rendering;
        if (renderer.latest() != seenLatest || publishedGen.load() < newestGen.load()) return RenderStatus::Rendering;
        if (s == RenderStatus::Failed) return RenderStatus::Failed;
        if (publishedGen.load() > 0) return RenderStatus::Ready;
        return s == RenderStatus::Ready ? RenderStatus::Ready : RenderStatus::Idle;
    }

    std::vector<std::string> warningsLocked() const
    {
        auto w = baseWarnings;
        if (! heldCaptureWarning.empty()) w.push_back (heldCaptureWarning);
        if (! heldRestoreWarning.empty()) w.push_back (heldRestoreWarning);
        return w;
    }

    // ---------------------------------------------------------------- members
    juce::AudioProcessorValueTreeState apvts;
    std::atomic<float>* pGain = nullptr;
    std::atomic<float>* pConvert = nullptr;
    std::atomic<float>* pPort = nullptr;
    std::atomic<float>* pVib = nullptr;
    std::atomic<float>* pSeed = nullptr;

    // audio-thread side
    TakeSlot slot;
    std::atomic<double> hostBpm { 0.0 }, hostRate { 0.0 }, captureEnd { 0.0 };
    std::atomic<int> capState { kIdle }, dropped { 0 };
    std::atomic<bool> pendingArm { false };
    std::atomic<juce::uint32> lastBlockMs { 0 };
    juce::AbstractFifo fifo;
    std::vector<CaptureEvent> fifoData;

    // message-thread side
    mutable std::recursive_mutex mtx;
    mutable std::mutex voiceMtx;
    std::shared_ptr<Voice> voice;
    std::shared_ptr<const Dictionary> dict;
    std::string lyrics, voicePath, lastErr;
    std::vector<Note> notes;
    double storedBpm = 120.0;
    std::vector<std::string> baseWarnings;
    std::string heldCaptureWarning, heldRestoreWarning;
    juce::uint32 lyricsDirtyAt = 0;
    RenderParams lastSubmitted;
    bool haveSubmitted = false;
    mutable std::mutex rwm;
    std::pair<std::uint64_t, std::vector<std::string>> renderWarnings;
    juce::uint32 cacheSizeAt = 0;
    juce::int64 cacheSize = 0;

    // resample worker
    std::mutex wm;
    std::condition_variable wcv;
    std::optional<Job> job;
    bool stopWorker = false;
    std::thread worker;
    std::atomic<std::uint64_t> newestGen { 0 }, publishedGen { 0 };
    std::shared_ptr<const RenderedTake> originalTake, seenLatest;
    int usedRate = 0;
    std::shared_ptr<std::atomic<bool>> alive;

    Renderer renderer;   // last: destroyed first
};

// ==================================================================== SingVstProcessor
SingVstProcessor::SingVstProcessor()
    : AudioProcessor (BusesProperties().withOutput ("Output", juce::AudioChannelSet::stereo(), true)),
      impl { std::make_unique<Impl> (*this) } {}
SingVstProcessor::~SingVstProcessor() = default;

const juce::String SingVstProcessor::getName() const { return "Sing VST"; }

void SingVstProcessor::prepareToPlay (double sampleRate, int) { impl->hostRate.store (sampleRate); }
void SingVstProcessor::releaseResources() {}

bool SingVstProcessor::isBusesLayoutSupported (const BusesLayout& l) const
{
    const auto out = l.getMainOutputChannelSet();
    return l.getMainInputChannelSet().isDisabled() && (out == juce::AudioChannelSet::stereo() || out == juce::AudioChannelSet::mono());
}

void SingVstProcessor::processBlock (juce::AudioBuffer<float>& buffer, juce::MidiBuffer& midi)
{
    juce::ScopedNoDenormals noDenormals;
    auto& m = *impl;
    const int n = buffer.getNumSamples();
    const int channels = buffer.getNumChannels();
    m.lastBlockMs.store (juce::Time::getMillisecondCounter());

    double ppq = 0.0, bpm = m.hostBpm.load();
    bool playing = false;
    if (auto* ph = getPlayHead())
        if (const auto pos = ph->getPosition()) {
            if (const auto b = pos->getBpm()) bpm = *b;
            if (const auto q = pos->getPpqPosition()) { ppq = *q; playing = pos->getIsPlaying(); }
        }
    if (bpm > 0.0) m.hostBpm.store (bpm);
    if (bpm <= 0.0) bpm = 120.0;
    const double rate = getSampleRate() > 0.0 ? getSampleRate() : m.hostRate.load();
    const double beatsPerSample = rate > 0.0 ? bpm / (60.0 * rate) : 0.0;

    // Capture state machine: every transition is a compare-and-swap on both threads (R-078).
    int s = m.capState.load();
    if (s == kCancelling) { (void) m.casState (kCancelling, kCancelAck); s = kCancelAck; }
    else if (s == kArmed && playing) { if (m.casState (kArmed, kCapturing)) s = kCapturing; else s = m.capState.load(); }
    if (s == kCapturing) {
        if (playing) {
            m.captureEnd.store (ppq + n * beatsPerSample);
            for (const auto meta : midi) {
                const auto msg = meta.getMessage();
                const bool on = msg.isNoteOn(), off = msg.isNoteOff();
                if (! on && ! off) continue;
                const auto w = m.fifo.write (1);
                if (w.blockSize1 + w.blockSize2 < 1) { m.dropped.fetch_add (1); continue; }
                auto& e = m.fifoData[static_cast<std::size_t> (w.blockSize1 > 0 ? w.startIndex1 : w.startIndex2)];
                e.ppq = ppq + meta.samplePosition * beatsPerSample;
                e.note = msg.getNoteNumber();
                e.on = on;
            }
        } else {
            (void) m.casState (kCapturing, kStopping);
        }
    }

    if (channels == 0) return;
    const float gain = juce::Decibels::decibelsToGain (m.pGain->load());
    const RenderedTake* take = m.slot.acquire();
    renderBlock (take, playing, ppq, bpm, rate > 0.0 ? rate : 48000.0, gain, buffer.getWritePointer (0), n);
    m.slot.release();
    for (int c = 1; c < channels; ++c) juce::FloatVectorOperations::copy (buffer.getWritePointer (c), buffer.getReadPointer (0), n);
}

juce::AudioProcessorEditor* SingVstProcessor::createEditor()
{
    return new SingVstEditor (*this, [this] { return impl->editorStatus(); });
}
bool SingVstProcessor::hasEditor() const { return true; }
bool SingVstProcessor::acceptsMidi() const { return true; }
bool SingVstProcessor::producesMidi() const { return false; }
double SingVstProcessor::getTailLengthSeconds() const { return 0.0; }
int SingVstProcessor::getNumPrograms() { return 1; }
int SingVstProcessor::getCurrentProgram() { return 0; }
void SingVstProcessor::setCurrentProgram (int) {}
const juce::String SingVstProcessor::getProgramName (int) { return {}; }
void SingVstProcessor::changeProgramName (int, const juce::String&) {}

void SingVstProcessor::getStateInformation (juce::MemoryBlock& dest)
{
    std::lock_guard<std::recursive_mutex> l (impl->mtx);
    PluginState st;
    st.lyrics = impl->lyrics;
    st.voicePath = impl->voicePath;
    st.notes = impl->notes;
    st.params = impl->currentParams();
    st.outputGainDb = impl->pGain->load();
    const auto json = toJson (st);
    dest.setSize (0);
    dest.append (json.data(), json.size());
}

void SingVstProcessor::setStateInformation (const void* data, int size)
{
    auto& m = *impl;
    std::lock_guard<std::recursive_mutex> l (m.mtx);
    PluginState st;
    try { st = pluginStateFromJson (std::string_view (static_cast<const char*> (data), static_cast<std::size_t> (std::max (0, size)))); }
    catch (const ValidationError& e) { m.setErr (std::string ("Could not restore the saved state: ") + e.what()); return; }

    const auto setParam = [&] (const char* id, float v) {
        if (auto* p = m.apvts.getParameter (id)) p->setValueNotifyingHost (p->convertTo0to1 (v));
    };
    setParam ("gain", static_cast<float> (st.outputGainDb));
    setParam ("convert", st.params.conversionEnabled ? 1.0f : 0.0f);
    setParam ("portamento", static_cast<float> (st.params.portamentoSec));
    setParam ("vibrato", static_cast<float> (st.params.vibratoCents));
    setParam ("seed", static_cast<float> (st.params.seed));
    m.lyrics = st.lyrics;
    m.notes = st.notes;
    m.storedBpm = st.params.bpm > 0.0 ? st.params.bpm : 120.0;
    m.lastErr.clear();
    m.baseWarnings.clear();
    m.heldCaptureWarning.clear();
    m.heldRestoreWarning.clear();

    // The stored take first: a cache hit plays even when the voice folder cannot be found (R-059).
    bool hit = false;
    if (! m.notes.empty()) {
        try {
            const auto tokens = parseLyrics (m.lyrics);
            if (auto t = loadTake (toPath (cacheDirectory()), phraseHash (m.notes, tokens, st.params))) {
                m.originalTake = std::make_shared<const RenderedTake> (std::move (*t));
                m.postJob();
                hit = true;
            }
        } catch (const ParseError&) {}
        if (! hit) m.heldRestoreWarning = "approved take not found in the take cache; a new performance was rendered";
    }

    m.voicePath = st.voicePath;
    if (! st.voicePath.empty()) {
        const juce::File dir (juce::String::fromUTF8 (st.voicePath.c_str()));
        if (dir.isDirectory()) (void) loadVoice (dir);
        else m.setErr (hit ? "voice not found \xE2\x80\x94 playing the stored take" : "Voice folder not found: " + st.voicePath);
    }
}

juce::AudioProcessorValueTreeState& SingVstProcessor::parameters() noexcept { return impl->apvts; }

void SingVstProcessor::setLyrics (const juce::String& utf8)
{
    std::lock_guard<std::recursive_mutex> l (impl->mtx);
    impl->lyrics = utf8.toStdString();
    impl->lyricsDirtyAt = juce::Time::getMillisecondCounter() | 1u;   // never 0
}

juce::String SingVstProcessor::getLyrics() const
{
    std::lock_guard<std::recursive_mutex> l (impl->mtx);
    return juce::String::fromUTF8 (impl->lyrics.c_str());
}

bool SingVstProcessor::loadVoice (const juce::File& voiceDir)
{
    auto& m = *impl;
    std::lock_guard<std::recursive_mutex> l (m.mtx);
    try {
        const auto manifestFile = voiceDir.getChildFile ("manifest.json");
        if (! manifestFile.existsAsFile()) throw ValidationError ("voice: manifest.json not found in " + voiceDir.getFullPathName().toStdString());
        const auto text = manifestFile.loadFileAsString().toStdString();
        auto v = std::make_shared<Voice>();
        v->manifest = parseManifest (text);
        validatePackage (toPath (voiceDir), v->manifest);
        v->sha = sha256Hex (text);
        Impl::ensureRuntime();
        v->guide = GuideEngine::load (v->manifest, toPath (voiceDir));
        if (v->manifest.converter) v->converter = ConverterEngine::load (v->manifest, toPath (voiceDir));
        {
            std::lock_guard<std::mutex> vl (m.voiceMtx);
            m.voice = std::move (v);
        }
        m.voicePath = voiceDir.getFullPathName().toStdString();
        m.lastErr.clear();
    } catch (const std::exception& e) {
        m.setErr (e.what());
        return false;
    }
    (void) m.submitRender();
    return true;
}

bool SingVstProcessor::importMidiFile (const juce::File& midi)
{
    auto& m = *impl;
    std::lock_guard<std::recursive_mutex> l (m.mtx);
    MidiImport imp;
    try {
        juce::MemoryBlock bytes;
        if (! midi.loadFileAsData (bytes)) throw ValidationError ("cannot read " + midi.getFullPathName().toStdString());
        imp = importMidi (std::string_view (static_cast<const char*> (bytes.getData()), bytes.getSize()));
    } catch (const std::exception& e) {
        m.setErr (e.what());
        return false;
    }
    m.notes = std::move (imp.notes);
    m.lyrics = std::move (imp.lyrics);
    m.storedBpm = imp.bpm;
    m.baseWarnings = std::move (imp.warnings);
    m.heldCaptureWarning.clear();
    m.heldRestoreWarning.clear();
    m.lastErr.clear();
    (void) m.submitRender();
    return true;
}

void SingVstProcessor::arm (bool shouldArm) { impl->armRequest (shouldArm); }
CaptureState SingVstProcessor::captureState() const noexcept { return impl->publicCaptureState(); }

std::vector<Note> SingVstProcessor::storedNotes() const
{
    std::lock_guard<std::recursive_mutex> l (impl->mtx);
    return impl->notes;
}

RenderStatus SingVstProcessor::renderStatus() const
{
    std::lock_guard<std::recursive_mutex> l (impl->mtx);
    return impl->renderStatusLocked();
}

juce::String SingVstProcessor::lastError() const
{
    std::lock_guard<std::recursive_mutex> l (impl->mtx);
    return juce::String::fromUTF8 (impl->lastErr.c_str());
}

std::vector<std::string> SingVstProcessor::lastWarnings() const
{
    std::lock_guard<std::recursive_mutex> l (impl->mtx);
    return impl->warningsLocked();
}

void SingVstProcessor::publishTakeForTesting (std::unique_ptr<RenderedTake> take) { impl->slot.publish (std::move (take)); }

} // namespace singvst

juce::AudioProcessor* JUCE_CALLTYPE createPluginFilter() { return new singvst::SingVstProcessor(); }
