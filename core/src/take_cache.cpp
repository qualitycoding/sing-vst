// Take cache and resampleTake (D-038; R-017, R-072). Little-endian file format; the supported hosts are x86-64.
#include "singvst/take_cache.hpp"
#include "singvst/errors.hpp"
#include "singvst/synthesis.hpp"
#include <cstdio>
#include <cstring>
#include <fstream>
#include <system_error>

namespace singvst {
namespace {
constexpr char kMagic[9] = "SVTAKE01";
constexpr std::size_t kHeader = 48;

struct Fnv {
    std::uint64_t h = 14695981039346656037ULL;
    void update (const void* d, std::size_t n)
    {
        const auto* p = static_cast<const unsigned char*> (d);
        for (std::size_t i = 0; i < n; ++i) { h ^= p[i]; h *= 1099511628211ULL; }
    }
};
template <class T> void put (std::string& s, T v) { char b[sizeof (T)]; std::memcpy (b, &v, sizeof (T)); s.append (b, sizeof (T)); }
template <class T> T get (const char* p) { T v; std::memcpy (&v, p, sizeof (T)); return v; }
} // namespace

std::filesystem::path takeFileName (std::uint64_t contentHash)
{
    char b[32];
    std::snprintf (b, sizeof b, "%016llx.take", static_cast<unsigned long long> (contentHash));
    return b;
}

bool storeTake (const std::filesystem::path& dir, const RenderedTake& t) noexcept
{
    try {
        std::error_code ec;
        std::filesystem::create_directories (dir, ec);
        if (ec) return false;
        std::string s (kMagic, 8);
        put (s, t.contentHash); put (s, t.startBeat); put (s, t.bpm); put (s, static_cast<std::int32_t> (t.sampleRate));
        put (s, t.unclippedPeak); put (s, static_cast<std::uint64_t> (t.samples.size()));
        s.append (reinterpret_cast<const char*> (t.samples.data()), t.samples.size() * sizeof (float));
        Fnv f;
        f.update (s.data(), s.size());
        put (s, f.h);
        const auto fin = dir / takeFileName (t.contentHash);
        auto tmp = fin;
        tmp += ".tmp";
        {
            std::ofstream out (tmp, std::ios::binary | std::ios::trunc);
            if (! out) return false;
            out.write (s.data(), static_cast<std::streamsize> (s.size()));
            out.flush();
            if (! out) { out.close(); std::filesystem::remove (tmp, ec); return false; }
        }
        std::filesystem::rename (tmp, fin, ec);
        if (ec) { std::filesystem::remove (tmp, ec); return false; }
        return true;
    } catch (...) { return false; }
}

std::optional<RenderedTake> loadTake (const std::filesystem::path& dir, std::uint64_t contentHash) noexcept
{
    try {
        const auto path = dir / takeFileName (contentHash);
        std::error_code ec;
        const auto size = std::filesystem::file_size (path, ec);
        if (ec || size < kHeader + 8 || (size - kHeader - 8) % 4 != 0) return std::nullopt;
        std::ifstream in (path, std::ios::binary);
        char hdr[kHeader];
        in.read (hdr, kHeader);
        if (! in || std::memcmp (hdr, kMagic, 8) != 0) return std::nullopt;
        RenderedTake t;
        t.contentHash = get<std::uint64_t> (hdr + 8);
        t.startBeat = get<double> (hdr + 16);
        t.bpm = get<double> (hdr + 24);
        t.sampleRate = get<std::int32_t> (hdr + 32);
        t.unclippedPeak = get<float> (hdr + 36);
        const auto n = get<std::uint64_t> (hdr + 40);
        if (t.contentHash != contentHash || t.sampleRate <= 0) return std::nullopt;
        if (n > 901ULL * static_cast<std::uint64_t> (t.sampleRate) || n != (size - kHeader - 8) / 4) return std::nullopt;   // checked before allocating
        t.samples.resize (static_cast<std::size_t> (n));
        in.read (reinterpret_cast<char*> (t.samples.data()), static_cast<std::streamsize> (n * sizeof (float)));
        char tail[8];
        in.read (tail, 8);
        if (! in) return std::nullopt;
        Fnv f;
        f.update (hdr, kHeader);
        f.update (t.samples.data(), t.samples.size() * sizeof (float));
        if (get<std::uint64_t> (tail) != f.h) return std::nullopt;
        return t;
    } catch (...) { return std::nullopt; }
}

RenderFn cachedRender (RenderFn fn, std::filesystem::path dir)
{
    return [fn = std::move (fn), dir = std::move (dir)] (const RenderRequest& r, const std::atomic<bool>& cancel) {
        const auto h = phraseHash (r.notes, r.tokens, r.params);
        if (auto t = loadTake (dir, h)) return std::move (*t);
        auto t = fn (r, cancel);
        if (t.contentHash == h) (void) storeTake (dir, t);
        return t;
    };
}

RenderedTake resampleTake (const RenderedTake& take, int targetRate)
{
    if (targetRate <= 0) throw ValidationError ("resampleTake: target rate must be positive");
    RenderedTake out = take;
    if (targetRate == take.sampleRate) return out;
    out.samples = resample (take.samples, take.sampleRate, targetRate);
    out.sampleRate = targetRate;
    out.unclippedPeak = peakAbs (out.samples);
    return out;
}

} // namespace singvst
