// Interface frozen by plan D-003; rules in D-013.
#pragma once
#include <atomic>
#include <chrono>
#include <functional>
#include <memory>
#include <string>
#include <vector>
#include "singvst/engine.hpp"
#include "singvst/g2p.hpp"
#include "singvst/playback.hpp"

namespace singvst {

struct RenderRequest {
    std::vector<Note> notes;
    std::vector<LyricToken> tokens;
    RenderParams params;
};

/** The whole-take pipeline (D-013): toMonophonic -> align -> layoutPhonemes -> f0Curve -> guide.render ->
    [converter.convert when params.conversionEnabled and converter != nullptr] -> resample to params.outputSampleRate.
    Fills startBeat, bpm, sampleRate, samples, unclippedPeak and contentHash = phraseHash(request). No clipping is applied.
    Throws ValidationError when there are no notes, Cancelled when cancel becomes true. */
RenderedTake renderTake (const RenderRequest& request, const Dictionary& dict, GuideEngine& guide, ConverterEngine* converter,
                         const std::atomic<bool>& cancel, std::vector<std::string>* warnings = nullptr);

enum class RenderStatus { Idle, Rendering, Ready, Failed };

using RenderFn = std::function<RenderedTake (const RenderRequest&, const std::atomic<bool>& cancel)>;

/** Background renderer (D-013): one worker thread; submit() cancels any in-flight job and keeps only the newest queued
    request; results of superseded or cancelled jobs are discarded; a request whose phraseHash equals the current Ready
    take's is not re-rendered; a failure sets Failed and lastError() but keeps latest(); the destructor cancels and joins. */
class Renderer {
public:
    explicit Renderer (RenderFn fn);
    ~Renderer();
    void submit (RenderRequest request);
    RenderStatus status() const;
    std::shared_ptr<const RenderedTake> latest() const;
    std::string lastError() const;
    int renderCount() const;                                 // completed (not discarded) renders
    bool waitIdle (std::chrono::milliseconds timeout) const; // true when no job is queued or running
private:
    struct Impl;
    std::unique_ptr<Impl> impl;
};

} // namespace singvst
