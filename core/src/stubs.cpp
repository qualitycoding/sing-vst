// STUBS: every function throws NotImplemented until its plan step replaces it (plan/PLAN.md S-002..S-009).
// The implementer deletes this file once every symbol has a real definition (S-009).
#include "singvst/align.hpp"
#include "singvst/engine.hpp"
#include "singvst/errors.hpp"
#include "singvst/g2p.hpp"
#include "singvst/lyrics.hpp"
#include "singvst/midifile.hpp"
#include "singvst/ort_runtime.hpp"
#include "singvst/playback.hpp"
#include "singvst/render.hpp"
#include "singvst/synthesis.hpp"
#include "singvst/voice.hpp"

namespace singvst {






std::unique_ptr<GuideEngine> GuideEngine::load (const VoiceManifest&, const std::filesystem::path&) { throw NotImplemented ("GuideEngine::load"); }
std::unique_ptr<ConverterEngine> ConverterEngine::load (const VoiceManifest&, const std::filesystem::path&) { throw NotImplemented ("ConverterEngine::load"); }
std::vector<float> resample (const std::vector<float>&, int, int) { throw NotImplemented ("resample"); }
std::vector<float> standardNormal (std::uint64_t, std::size_t) { throw NotImplemented ("standardNormal"); }
const OrtRuntimeInfo& loadOrtRuntime (const std::filesystem::path&) { throw NotImplemented ("loadOrtRuntime"); }
bool ortRuntimeLoaded() noexcept { return false; }
std::string bundledOrtFileName() { throw NotImplemented ("bundledOrtFileName"); }
MidiImport importMidi (std::string_view) { throw NotImplemented ("importMidi"); }

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

// Pre-mortem round 1 additions (D-038); implemented by S-009.
#include "singvst/take_cache.hpp"
namespace singvst {
std::filesystem::path takeFileName (std::uint64_t) { throw NotImplemented ("takeFileName"); }
bool storeTake (const std::filesystem::path&, const RenderedTake&) noexcept { return false; }
std::optional<RenderedTake> loadTake (const std::filesystem::path&, std::uint64_t) noexcept { return std::nullopt; }
RenderFn cachedRender (RenderFn, std::filesystem::path) { throw NotImplemented ("cachedRender"); }
RenderedTake resampleTake (const RenderedTake&, int) { throw NotImplemented ("resampleTake"); }
} // namespace singvst
