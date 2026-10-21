// Planning sketch (not shipped): proves T-067/T-068 are satisfiable under D-038. Its 900 × sampleRate bound is superseded by
// D-038's 901 (R-067); D-038 wins wherever they differ.
#include "singvst/take_cache.hpp"
#include <cstdio>
#include <cstring>
#include <fstream>
#include <system_error>
namespace singvst {
std::uint64_t phraseHash (const std::vector<Note>& n, const std::vector<LyricToken>& t, const RenderParams& p)
{ std::uint64_t h = 1469598103934665603ull; auto mix=[&](std::uint64_t v){ h ^= v; h *= 1099511628211ull; };
  for (auto& x : n) mix ((std::uint64_t) x.midiNote * 31 + (std::uint64_t) (x.startBeat * 1000)); mix (t.size()); mix (p.voiceId.size()); return h; }
static std::uint64_t fnv (const char* d, std::size_t n) { std::uint64_t h = 14695981039346656037ull; for (std::size_t i=0;i<n;++i){ h ^= (unsigned char) d[i]; h *= 1099511628211ull; } return h; }
template <class T> static void put (std::string& s, T v) { char b[sizeof (T)]; std::memcpy (b, &v, sizeof (T)); s.append (b, sizeof (T)); }
template <class T> static T get (const std::string& s, std::size_t& o) { T v; std::memcpy (&v, s.data() + o, sizeof (T)); o += sizeof (T); return v; }
std::filesystem::path takeFileName (std::uint64_t h) { char b[32]; std::snprintf (b, sizeof b, "%016llx.take", (unsigned long long) h); return b; }
bool storeTake (const std::filesystem::path& dir, const RenderedTake& t) noexcept
{ try { std::error_code ec; std::filesystem::create_directories (dir, ec); if (ec) return false;
    std::string s = "SVTAKE01"; put (s, t.contentHash); put (s, t.startBeat); put (s, t.bpm); put (s, (std::int32_t) t.sampleRate);
    put (s, t.unclippedPeak); put (s, (std::uint64_t) t.samples.size()); s.append ((const char*) t.samples.data(), t.samples.size() * 4);
    put (s, fnv (s.data(), s.size()));
    const auto fin = dir / takeFileName (t.contentHash); auto tmp = fin; tmp += ".tmp";
    { std::ofstream f (tmp, std::ios::binary | std::ios::trunc); if (! f) return false; f.write (s.data(), (std::streamsize) s.size()); if (! f) return false; }
    std::filesystem::rename (tmp, fin, ec); return ! ec; } catch (...) { return false; } }
std::optional<RenderedTake> loadTake (const std::filesystem::path& dir, std::uint64_t h) noexcept
{ try { const auto p = dir / takeFileName (h); std::error_code ec; const auto sz = std::filesystem::file_size (p, ec); if (ec || sz < 56) return std::nullopt;
    if ((sz - 56) % 4) return std::nullopt; const auto n = (sz - 56) / 4;
    std::ifstream f (p, std::ios::binary); std::string s ((std::size_t) sz, '\0'); f.read (s.data(), (std::streamsize) sz); if (! f) return std::nullopt;
    if (s.compare (0, 8, "SVTAKE01") != 0) return std::nullopt; std::size_t o = 8; RenderedTake t;
    t.contentHash = get<std::uint64_t> (s, o); t.startBeat = get<double> (s, o); t.bpm = get<double> (s, o); t.sampleRate = get<std::int32_t> (s, o);
    t.unclippedPeak = get<float> (s, o); const auto cnt = get<std::uint64_t> (s, o);
    if (cnt != n || t.contentHash != h || t.sampleRate <= 0 || cnt > 900ull * (std::uint64_t) t.sampleRate) return std::nullopt;
    t.samples.resize ((std::size_t) n); std::memcpy (t.samples.data(), s.data() + o, n * 4); o += n * 4;
    if (get<std::uint64_t> (s, o) != fnv (s.data(), (std::size_t) sz - 8)) return std::nullopt; return t; } catch (...) { return std::nullopt; } }
RenderFn cachedRender (RenderFn fn, std::filesystem::path dir)
{ return [fn = std::move (fn), dir = std::move (dir)] (const RenderRequest& r, const std::atomic<bool>& c) {
    const auto h = phraseHash (r.notes, r.tokens, r.params); if (auto t = loadTake (dir, h)) return *t;
    auto t = fn (r, c); if (t.contentHash == h) (void) storeTake (dir, t); return t; }; }
}
