// renderTake and the background Renderer (D-013).
#include "singvst/render.hpp"
#include "singvst/errors.hpp"
#include "singvst/synthesis.hpp"
#include <condition_variable>
#include <mutex>
#include <optional>
#include <thread>

namespace singvst {
namespace {
constexpr std::size_t kMaxNotes = 5000;
constexpr double kMaxSeconds = 900.0;
constexpr double kGuideFrameRate = 44100.0 / 512.0;

void checkCancel (const std::atomic<bool>& cancel) { if (cancel.load()) throw Cancelled(); }
} // namespace

RenderedTake renderTake (const RenderRequest& request, const Dictionary& dict, GuideEngine& guide, ConverterEngine* converter,
                         const std::atomic<bool>& cancel, std::vector<std::string>* warnings)
{
    checkCancel (cancel);
    const auto mono = toMonophonic (request.notes);
    if (mono.empty()) throw ValidationError ("no notes to render");
    if (mono.size() > kMaxNotes) throw ValidationError ("the take has " + std::to_string (mono.size()) + " notes; the limit is 5000");
    const double bpm = request.params.bpm;
    if ((mono.back().endBeat - mono.front().startBeat) * 60.0 / bpm > kMaxSeconds)
        throw ValidationError ("the take is longer than 900 s (limit 900 s)");

    auto aligned = align (mono, request.tokens, dict);
    if (warnings != nullptr) warnings->insert (warnings->end(), aligned.warnings.begin(), aligned.warnings.end());

    const auto spans = layoutPhonemes (aligned.notes, bpm);
    const auto durations = spansToFrameDurations (spans, kGuideFrameRate);
    std::int64_t frames = 0;
    for (auto d : durations) frames += d;
    auto f0 = f0Curve (aligned.notes, bpm, kGuideFrameRate, static_cast<double> (frames) / kGuideFrameRate, request.params.portamentoSec,
                       request.params.vibratoCents);
    f0.resize (static_cast<std::size_t> (frames), 0.0f);   // guard against a frame-count rounding difference at the tail

    checkCancel (cancel);
    std::vector<float> audio = guide.render (spans, f0, cancel);
    int rate = guide.sampleRate();

    if (request.params.conversionEnabled && converter != nullptr) {
        checkCancel (cancel);
        const auto f0c = f0Curve (aligned.notes, bpm, 100.0, static_cast<double> (audio.size()) / rate, request.params.portamentoSec,
                                  request.params.vibratoCents);
        audio = converter->convert (audio, rate, f0c, request.params.seed, cancel);
        rate = converter->sampleRate();
    }
    checkCancel (cancel);

    RenderedTake take;
    take.samples = resample (audio, rate, request.params.outputSampleRate);
    take.sampleRate = request.params.outputSampleRate;
    take.startBeat = mono.front().startBeat;
    take.bpm = bpm;
    take.unclippedPeak = peakAbs (take.samples);
    take.contentHash = phraseHash (request.notes, request.tokens, request.params);
    return take;
}

struct Renderer::Impl {
    explicit Impl (RenderFn f) : fn (std::move (f)) { worker = std::thread ([this] { run(); }); }

    ~Impl()
    {
        {
            std::lock_guard<std::mutex> l (m);
            stopping = true;
            queued.reset();
            if (current) current->store (true);
        }
        cv.notify_all();
        if (worker.joinable()) worker.join();
    }

    void run()
    {
        std::unique_lock<std::mutex> l (m);
        for (;;) {
            cv.wait (l, [this] { return stopping || queued.has_value(); });
            if (stopping) return;
            RenderRequest req = std::move (*queued);
            queued.reset();
            auto flag = std::make_shared<std::atomic<bool>> (false);
            current = flag;
            running = true;
            status = RenderStatus::Rendering;
            l.unlock();

            std::optional<RenderedTake> result;
            std::string error;
            bool failed = false;
            try { result = fn (req, *flag); }
            catch (const Cancelled&) {}
            catch (const std::exception& e) { failed = true; error = e.what(); }
            catch (...) { failed = true; error = "unknown error"; }

            l.lock();
            running = false;
            current.reset();
            const bool superseded = flag->load() || stopping;
            if (! superseded) {
                if (result) {
                    latest = std::make_shared<const RenderedTake> (std::move (*result));
                    lastErr.clear();
                    ++count;
                    status = RenderStatus::Ready;
                } else if (failed) {
                    lastErr = error;
                    status = RenderStatus::Failed;
                }
            }
            if (queued.has_value()) status = RenderStatus::Rendering;
            else if (superseded) status = lastErr.empty() ? (latest ? RenderStatus::Ready : RenderStatus::Idle) : RenderStatus::Failed;
            cv.notify_all();
        }
    }

    RenderFn fn;
    mutable std::mutex m;
    mutable std::condition_variable cv;
    std::thread worker;
    bool stopping = false, running = false;
    std::optional<RenderRequest> queued;
    std::shared_ptr<std::atomic<bool>> current;
    RenderStatus status = RenderStatus::Idle;
    std::shared_ptr<const RenderedTake> latest;
    std::string lastErr;
    int count = 0;
};

Renderer::Renderer (RenderFn fn) : impl (std::make_unique<Impl> (std::move (fn))) {}
Renderer::~Renderer() = default;

void Renderer::submit (RenderRequest request)
{
    const auto h = phraseHash (request.notes, request.tokens, request.params);
    {
        std::lock_guard<std::mutex> l (impl->m);
        if (impl->latest && impl->latest->contentHash == h) {   // the approved take already is this request: nothing to render
            impl->queued.reset();
            if (impl->current) impl->current->store (true);
            impl->lastErr.clear();
            impl->status = RenderStatus::Ready;
        } else {
            impl->queued = std::move (request);
            if (impl->current) impl->current->store (true);
            impl->status = RenderStatus::Rendering;
        }
    }
    impl->cv.notify_all();
}

RenderStatus Renderer::status() const { std::lock_guard<std::mutex> l (impl->m); return impl->status; }
std::shared_ptr<const RenderedTake> Renderer::latest() const { std::lock_guard<std::mutex> l (impl->m); return impl->latest; }
std::string Renderer::lastError() const { std::lock_guard<std::mutex> l (impl->m); return impl->lastErr; }
int Renderer::renderCount() const { std::lock_guard<std::mutex> l (impl->m); return impl->count; }

bool Renderer::waitIdle (std::chrono::milliseconds timeout) const
{
    std::unique_lock<std::mutex> l (impl->m);
    return impl->cv.wait_for (l, timeout, [this] { return ! impl->running && ! impl->queued.has_value(); });
}

} // namespace singvst
