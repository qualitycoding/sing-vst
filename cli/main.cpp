// singvst-render (D-014): renders a MIDI file with a voice package to a float32 mono WAV plus a provenance sidecar.
// Exit codes: 0 success; 2 usage, missing file or invalid voice/input; 3 render failure.
#include <atomic>
#include <chrono>
#include <cmath>
#include <cstdio>
#include <ctime>
#include <fstream>
#include <iterator>
#include <map>
#include <set>
#include <sstream>
#include <string>
#include <thread>
#include <nlohmann/json.hpp>
#include "ort_threads.hpp"
#include "singvst_git_commit.h"
#include "singvst/engine.hpp"
#include "singvst/errors.hpp"
#include "singvst/midifile.hpp"
#include "singvst/ort_runtime.hpp"
#include "singvst/render.hpp"
#include "singvst/synthesis.hpp"
#include "singvst/voice.hpp"
#ifdef _WIN32
 #define NOMINMAX
 #include <windows.h>
#else
 #include <sys/utsname.h>
 #include <unistd.h>
#endif

using namespace singvst;
namespace fs = std::filesystem;
using json = nlohmann::json;

namespace {
struct UsageError : std::runtime_error { using std::runtime_error::runtime_error; };

const char* kUsage =
    "usage: singvst-render --voice DIR --midi FILE --out FILE.wav [--lyrics TEXT | --lyrics-file FILE] [--dict FILE] [--seed N]\n"
    "                      [--no-convert] [--bpm X] [--rate HZ] [--gain-db X] [--raw] [--ort-lib PATH]\n"
    "       singvst-render --check-voice DIR [--ort-lib PATH]\n";

std::string u8 (const fs::path& p) { const auto s = p.u8string(); return std::string (s.begin(), s.end()); }

std::string readFile (const fs::path& p, const char* what)
{
    std::ifstream in (p, std::ios::binary);
    if (! in) throw UsageError (std::string (what) + ": cannot read " + u8 (p));
    return { std::istreambuf_iterator<char> (in), std::istreambuf_iterator<char>() };
}

fs::path exeDir()
{
#ifdef _WIN32
    wchar_t buf[32768];
    const DWORD n = ::GetModuleFileNameW (nullptr, buf, 32768);
    return n > 0 ? fs::path (std::wstring (buf, n)).parent_path() : fs::path (".");
#else
    std::error_code ec;
    const auto p = fs::read_symlink ("/proc/self/exe", ec);
    return ec ? fs::path (".") : p.parent_path();
#endif
}

struct Args {
    std::map<std::string, std::string> values;
    std::set<std::string> flags;
    bool has (const std::string& k) const { return values.count (k) > 0; }
    std::string get (const std::string& k, const std::string& dflt = "") const { const auto it = values.find (k); return it == values.end() ? dflt : it->second; }
};

Args parseArgs (int argc, char** argv)
{
    static const std::set<std::string> valued { "--voice", "--midi", "--out", "--lyrics", "--lyrics-file", "--dict", "--seed", "--bpm", "--rate",
                                                "--gain-db", "--ort-lib", "--check-voice" };
    static const std::set<std::string> boolean { "--no-convert", "--raw", "--help" };
    Args a;
    for (int i = 1; i < argc; ++i) {
        const std::string k = argv[i];
        if (boolean.count (k)) a.flags.insert (k);
        else if (valued.count (k)) {
            if (i + 1 >= argc) throw UsageError ("option " + k + " needs a value");
            a.values[k] = argv[++i];
        } else throw UsageError ("unknown option " + k);
    }
    return a;
}

double toDouble (const std::string& s, const char* name)
{
    try { std::size_t used = 0; const double v = std::stod (s, &used); if (used == s.size() && std::isfinite (v)) return v; } catch (...) {}
    throw UsageError (std::string ("invalid number for ") + name + ": " + s);
}

std::uint64_t toSeed (const std::string& s)
{
    try { std::size_t used = 0; const auto v = std::stoull (s, &used); if (used == s.size() && s.find ('-') == std::string::npos) return v; } catch (...) {}
    throw UsageError ("invalid --seed: " + s);
}

std::string utcNow()
{
    const std::time_t t = std::time (nullptr);
    std::tm tm {};
#ifdef _WIN32
    gmtime_s (&tm, &t);
#else
    gmtime_r (&t, &tm);
#endif
    char b[32];
    std::strftime (b, sizeof b, "%Y-%m-%dT%H:%M:%SZ", &tm);
    return b;
}

std::string osName()
{
#ifdef _WIN32
    using RtlGetVersionFn = LONG (WINAPI*) (OSVERSIONINFOW*);
    OSVERSIONINFOW vi {};
    vi.dwOSVersionInfoSize = sizeof vi;
    if (auto* f = reinterpret_cast<RtlGetVersionFn> (reinterpret_cast<void*> (::GetProcAddress (::GetModuleHandleW (L"ntdll.dll"), "RtlGetVersion"))))
        if (f (&vi) == 0) return "Windows " + std::to_string (vi.dwMajorVersion) + "." + std::to_string (vi.dwMinorVersion) + "." + std::to_string (vi.dwBuildNumber);
    return "Windows";
#else
    utsname u {};
    return ::uname (&u) == 0 ? std::string (u.sysname) + " " + u.release : "unknown";
#endif
}

std::string cpuName()
{
#ifdef _WIN32
    HKEY key;
    if (::RegOpenKeyExA (HKEY_LOCAL_MACHINE, "HARDWARE\\DESCRIPTION\\System\\CentralProcessor\\0", 0, KEY_READ, &key) == ERROR_SUCCESS) {
        char buf[256]; DWORD n = sizeof buf;
        const bool ok = ::RegQueryValueExA (key, "ProcessorNameString", nullptr, nullptr, reinterpret_cast<LPBYTE> (buf), &n) == ERROR_SUCCESS;
        ::RegCloseKey (key);
        if (ok) return std::string (buf);
    }
    return "unknown";
#else
    std::ifstream in ("/proc/cpuinfo");
    for (std::string line; std::getline (in, line);)
        if (line.rfind ("model name", 0) == 0) {
            const auto c = line.find (':');
            if (c != std::string::npos) { auto v = line.substr (c + 1); while (! v.empty() && v.front() == ' ') v.erase (v.begin()); return v; }
        }
    return "unknown";
#endif
}

void writeWavFloat32 (const fs::path& path, const std::vector<float>& s, int rate)
{
    std::ofstream out (path, std::ios::binary | std::ios::trunc);
    if (! out) throw UsageError ("cannot write " + u8 (path));
    const auto u32 = [&] (std::uint32_t v) { const char b[4] = { char (v), char (v >> 8), char (v >> 16), char (v >> 24) }; out.write (b, 4); };
    const auto u16 = [&] (std::uint16_t v) { const char b[2] = { char (v), char (v >> 8) }; out.write (b, 2); };
    const std::uint32_t dataBytes = static_cast<std::uint32_t> (s.size() * 4);
    out.write ("RIFF", 4); u32 (36 + dataBytes); out.write ("WAVE", 4);
    out.write ("fmt ", 4); u32 (16); u16 (3); u16 (1); u32 (static_cast<std::uint32_t> (rate)); u32 (static_cast<std::uint32_t> (rate) * 4); u16 (4); u16 (32);
    out.write ("data", 4); u32 (dataBytes);
    out.write (reinterpret_cast<const char*> (s.data()), static_cast<std::streamsize> (dataBytes));   // little-endian host
    if (! out) throw UsageError ("cannot write " + u8 (path));
}

struct Voice {
    VoiceManifest manifest;
    std::string sha;
};

Voice loadVoice (const fs::path& dir)
{
    std::string text;
    try { text = readFile (dir / "manifest.json", "voice"); }
    catch (const UsageError&) { throw UsageError ("voice: cannot read " + u8 (dir / "manifest.json")); }
    Voice v;
    try {
        v.manifest = parseManifest (text);
        validatePackage (dir, v.manifest);
    } catch (const ValidationError& e) { throw UsageError (std::string ("voice: ") + e.what()); }
    v.sha = sha256Hex (text);
    return v;
}

const OrtRuntimeInfo& loadRuntime (const Args& a)
{
    const fs::path lib = a.has ("--ort-lib") ? fs::path (a.get ("--ort-lib")) : exeDir() / bundledOrtFileName();
    try { return loadOrtRuntime (lib); }
    catch (const ValidationError& e) { throw UsageError (std::string ("ONNX Runtime: ") + e.what()); }
}

int checkVoice (const Args& a)
{
    const auto v = loadVoice (a.get ("--check-voice"));
    loadRuntime (a);
    try {
        (void) GuideEngine::load (v.manifest, a.get ("--check-voice"));
        if (v.manifest.converter) (void) ConverterEngine::load (v.manifest, a.get ("--check-voice"));
    } catch (const ValidationError& e) { throw UsageError (std::string ("voice: ") + e.what()); }
    std::printf ("ok %s\n", v.manifest.name.c_str());
    return 0;
}

int render (const Args& a)
{
    for (const char* req : { "--voice", "--midi", "--out" })
        if (! a.has (req)) throw UsageError (std::string ("missing required option ") + req);
    if (a.has ("--lyrics") && a.has ("--lyrics-file")) throw UsageError ("--lyrics and --lyrics-file are exclusive");
    const bool convert = ! a.flags.count ("--no-convert"), raw = a.flags.count ("--raw") > 0;
    const std::uint64_t seed = a.has ("--seed") ? toSeed (a.get ("--seed")) : 0;
    const double gainDb = a.has ("--gain-db") ? toDouble (a.get ("--gain-db"), "--gain-db") : 0.0;
    const double rateD = a.has ("--rate") ? toDouble (a.get ("--rate"), "--rate") : 48000.0;
    if (rateD < 8000.0 || rateD > 192000.0 || rateD != std::floor (rateD)) throw UsageError ("--rate must be a whole number from 8000 to 192000");
    const int rate = static_cast<int> (rateD);

    const fs::path voiceDir = a.get ("--voice");
    const auto voice = loadVoice (voiceDir);
    const auto& ort = loadRuntime (a);
    std::unique_ptr<GuideEngine> guide;
    std::unique_ptr<ConverterEngine> converter;
    try {
        guide = GuideEngine::load (voice.manifest, voiceDir);
        if (convert && voice.manifest.converter) converter = ConverterEngine::load (voice.manifest, voiceDir);
    } catch (const ValidationError& e) { throw UsageError (std::string ("voice: ") + e.what()); }

    MidiImport midi;
    try { midi = importMidi (readFile (a.get ("--midi"), "midi")); }
    catch (const ValidationError& e) { throw UsageError (e.what()); }

    std::string lyrics = midi.lyrics, source = "midi";
    if (a.has ("--lyrics")) { lyrics = a.get ("--lyrics"); source = "text"; }
    else if (a.has ("--lyrics-file")) { lyrics = readFile (a.get ("--lyrics-file"), "lyrics"); source = "file"; }
    const double bpm = a.has ("--bpm") ? toDouble (a.get ("--bpm"), "--bpm") : midi.bpm;
    if (! (bpm > 0.0)) throw UsageError ("--bpm must be positive");

    RenderRequest rq;
    try { rq.tokens = parseLyrics (lyrics); }
    catch (const ParseError& e) { throw UsageError (std::string ("lyrics: ") + e.what() + " at byte " + std::to_string (e.position)); }

    const fs::path dictPath = a.has ("--dict") ? fs::path (a.get ("--dict")) : exeDir() / "cmudict.dict";
    const Dictionary dict = Dictionary::fromCmuText (readFile (dictPath, "dictionary"));

    rq.notes = midi.notes;
    if (toMonophonic (rq.notes).empty()) throw UsageError ("no notes in the MIDI file");
    rq.params.voiceId = voice.sha;
    rq.params.bpm = bpm;
    rq.params.outputSampleRate = rate;
    rq.params.conversionEnabled = convert;
    rq.params.seed = seed;

    std::vector<std::string> warnings = midi.warnings;
    const std::atomic<bool> noCancel { false };
    RenderedTake take;
    const auto t0 = std::chrono::steady_clock::now();
    try { take = renderTake (rq, dict, *guide, converter.get(), noCancel, &warnings); }
    catch (const std::exception& e) { std::fprintf (stderr, "singvst-render: render failed: %s\n", e.what()); return 3; }
    const double renderSeconds = std::chrono::duration<double> (std::chrono::steady_clock::now() - t0).count();

    const float gain = static_cast<float> (std::pow (10.0, gainDb / 20.0));
    std::vector<float> y (take.samples.size());
    for (std::size_t i = 0; i < y.size(); ++i) y[i] = raw ? gain * take.samples[i] : softClip (gain * take.samples[i]);
    const fs::path out = a.get ("--out");
    writeWavFloat32 (out, y, rate);

    json side = {
        { "git_commit", SINGVST_GIT_COMMIT },
        { "voice_sha256", voice.sha },
        { "params", { { "bpm", bpm }, { "rate", rate }, { "gain_db", gainDb }, { "raw", raw }, { "convert", convert },
                      { "dict", u8 (dictPath) }, { "lyrics_source", source } } },
        { "seeds", { { "converter", seed } } },
        { "utc_timestamp", utcNow() },
        { "hardware", { { "os", osName() }, { "cpu", cpuName() }, { "logical_cores", std::thread::hardware_concurrency() } } },
        { "threads", ortIntraOpThreads() },
        { "ort_version", ort.version },
        { "warnings", warnings },
        { "unclipped_peak", take.unclippedPeak },
        { "render_seconds", renderSeconds },
        { "audio_seconds", static_cast<double> (y.size()) / rate },
    };
    std::ofstream sideOut (fs::path (out.string() + ".provenance.json"), std::ios::binary | std::ios::trunc);
    if (! sideOut) throw UsageError ("cannot write the provenance file next to " + u8 (out));
    sideOut << side.dump (2, ' ', false, json::error_handler_t::replace) << "\n";
    return 0;
}
} // namespace

int main (int argc, char** argv)
{
    try {
        if (argc < 2) { std::fputs (kUsage, stderr); return 2; }
        const Args a = parseArgs (argc, argv);
        if (a.flags.count ("--help")) { std::fputs (kUsage, stdout); return 0; }
        if (a.has ("--check-voice")) return checkVoice (a);
        return render (a);
    } catch (const UsageError& e) {
        std::fprintf (stderr, "singvst-render: %s\n", e.what());
        if (std::string (e.what()).rfind ("option", 0) == 0 || std::string (e.what()).rfind ("unknown", 0) == 0 || std::string (e.what()).rfind ("missing", 0) == 0) std::fputs (kUsage, stderr);
        return 2;
    } catch (const std::exception& e) {
        std::fprintf (stderr, "singvst-render: %s\n", e.what());
        return 2;
    }
}
