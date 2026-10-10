// STUBS: every function throws NotImplemented until its plan step replaces it (plan/PLAN.md S-002..S-008).
// The implementer deletes this file once every symbol has a real definition (S-008).
#include "singvst/align.hpp"
#include "singvst/engine.hpp"
#include "singvst/errors.hpp"
#include "singvst/g2p.hpp"
#include "singvst/lyrics.hpp"
#include "singvst/playback.hpp"
#include "singvst/render.hpp"
#include "singvst/synthesis.hpp"
#include "singvst/voice.hpp"

namespace singvst {
std::vector<LyricToken> parseLyrics (std::string_view) { throw NotImplemented ("parseLyrics"); }

Dictionary Dictionary::fromCmuText (std::string_view) { throw NotImplemented ("Dictionary::fromCmuText"); }
std::optional<Phones> Dictionary::lookup (std::string_view) const { throw NotImplemented ("Dictionary::lookup"); }
std::size_t Dictionary::size() const { throw NotImplemented ("Dictionary::size"); }
bool Dictionary::hasPhone (std::string_view) const { throw NotImplemented ("Dictionary::hasPhone"); }
bool isVowel (std::string_view) { throw NotImplemented ("isVowel"); }
std::vector<Phones> syllabify (const Phones&, std::size_t) { throw NotImplemented ("syllabify"); }

std::vector<Note> toMonophonic (std::vector<Note>) { throw NotImplemented ("toMonophonic"); }
AlignmentResult align (const std::vector<Note>&, const std::vector<LyricToken>&, const Dictionary&) { throw NotImplemented ("align"); }

double midiToHz (double) { throw NotImplemented ("midiToHz"); }
std::vector<PhonemeSpan> layoutPhonemes (const std::vector<NoteAssignment>&, double, double) { throw NotImplemented ("layoutPhonemes"); }
std::vector<float> f0Curve (const std::vector<NoteAssignment>&, double, double, double, double, double, double) { throw NotImplemented ("f0Curve"); }
int rvcCoarsePitch (double) { throw NotImplemented ("rvcCoarsePitch"); }
std::vector<std::int64_t> spansToFrameDurations (const std::vector<PhonemeSpan>&, double) { throw NotImplemented ("spansToFrameDurations"); }
float softClip (float, float) noexcept { return 1.0e9f; }   // noexcept stub: a value no test accepts
float peakAbs (const std::vector<float>&) noexcept { return -1.0f; }

VoiceManifest parseManifest (std::string_view) { throw NotImplemented ("parseManifest"); }
void validatePackage (const std::filesystem::path&, const VoiceManifest&, std::uintmax_t) { throw NotImplemented ("validatePackage"); }

std::optional<std::int64_t> takeSampleAt (const RenderedTake&, double, double, double) { throw NotImplemented ("takeSampleAt"); }
void renderBlock (const RenderedTake*, bool, double, double, double, float, float* out, int n) noexcept { for (int i = 0; i < n; ++i) out[i] = 1.0e9f; }
std::uint64_t phraseHash (const std::vector<Note>&, const std::vector<LyricToken>&, const RenderParams&) { throw NotImplemented ("phraseHash"); }
void CaptureRecorder::noteOn (double, int) { throw NotImplemented ("CaptureRecorder::noteOn"); }
void CaptureRecorder::noteOff (double, int) { throw NotImplemented ("CaptureRecorder::noteOff"); }
std::vector<Note> CaptureRecorder::finish (double) { throw NotImplemented ("CaptureRecorder::finish"); }
void CaptureRecorder::clear() { throw NotImplemented ("CaptureRecorder::clear"); }
std::string toJson (const PluginState&) { throw NotImplemented ("toJson"); }
PluginState pluginStateFromJson (std::string_view) { throw NotImplemented ("pluginStateFromJson"); }
TakeSlot::TakeSlot() = default;
TakeSlot::~TakeSlot() = default;
void TakeSlot::publish (std::unique_ptr<RenderedTake>) { throw NotImplemented ("TakeSlot::publish"); }
const RenderedTake* TakeSlot::acquire() noexcept { return nullptr; }
void TakeSlot::release() noexcept {}
std::size_t TakeSlot::collect() { throw NotImplemented ("TakeSlot::collect"); }
std::size_t TakeSlot::retiredCount() const { throw NotImplemented ("TakeSlot::retiredCount"); }

std::unique_ptr<GuideEngine> GuideEngine::load (const VoiceManifest&, const std::filesystem::path&) { throw NotImplemented ("GuideEngine::load"); }
std::unique_ptr<ConverterEngine> ConverterEngine::load (const VoiceManifest&, const std::filesystem::path&) { throw NotImplemented ("ConverterEngine::load"); }
std::vector<float> resample (const std::vector<float>&, int, int) { throw NotImplemented ("resample"); }

RenderedTake renderTake (const RenderRequest&, const Dictionary&, GuideEngine&, ConverterEngine*, const std::atomic<bool>&, std::vector<std::string>*) { throw NotImplemented ("renderTake"); }
struct Renderer::Impl {};
Renderer::Renderer (RenderFn) { throw NotImplemented ("Renderer"); }
Renderer::~Renderer() = default;
void Renderer::submit (RenderRequest) { throw NotImplemented ("Renderer::submit"); }
RenderStatus Renderer::status() const { throw NotImplemented ("Renderer::status"); }
std::shared_ptr<const RenderedTake> Renderer::latest() const { throw NotImplemented ("Renderer::latest"); }
std::string Renderer::lastError() const { throw NotImplemented ("Renderer::lastError"); }
int Renderer::renderCount() const { throw NotImplemented ("Renderer::renderCount"); }
bool Renderer::waitIdle (std::chrono::milliseconds) const { throw NotImplemented ("Renderer::waitIdle"); }
} // namespace singvst
