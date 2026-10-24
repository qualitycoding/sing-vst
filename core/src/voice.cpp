// Voice package manifest parsing and validation (D-008).
#include "singvst/voice.hpp"
#include "sha256.hpp"
#include "singvst/errors.hpp"
#include <fstream>
#include <nlohmann/json.hpp>
#include <set>
#include <system_error>

namespace singvst {
namespace {
using json = nlohmann::json;

[[noreturn]] void fail (const std::string& field, const std::string& why) { throw ValidationError (field + ": " + why); }

json need (const json& o, const char* key, const std::string& where)
{
    if (! o.is_object() || ! o.contains (key)) fail (where + key, "required key missing");
    return o.at (key);
}

std::string nonEmptyString (const json& o, const char* key, const std::string& where)
{
    const auto v = need (o, key, where);
    if (! v.is_string() || v.get<std::string>().empty()) fail (where + key, "must be a non-empty string");
    return v.get<std::string>();
}

bool safePath (const std::string& p)
{
    if (p.empty() || p.front() == '/') return false;
    std::size_t a = 0;
    while (a <= p.size()) {
        std::size_t b = p.find ('/', a);
        if (b == std::string::npos) b = p.size();
        const std::string seg = p.substr (a, b - a);
        if (seg.empty() || seg == "." || seg == "..") return false;
        for (char c : seg)
            if (! ((c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z') || (c >= '0' && c <= '9') || c == '.' || c == '_' || c == '-')) return false;
        a = b + 1;
    }
    return true;
}

std::map<std::string, std::string> readFiles (const json& o, const std::string& where, const std::set<std::string>& required,
                                              const std::set<std::string>& optional)
{
    const auto f = need (o, "files", where);
    if (! f.is_object()) fail (where + "files", "must be an object");
    std::map<std::string, std::string> out;
    for (auto it = f.begin(); it != f.end(); ++it) {
        if (! required.count (it.key()) && ! optional.count (it.key())) fail (where + "files." + it.key(), "unknown file role");
        if (! it.value().is_string() || ! safePath (it.value().get<std::string>())) fail (where + "files." + it.key(), "not a safe relative path");
        out[it.key()] = it.value().get<std::string>();
    }
    for (const auto& r : required) if (! out.count (r)) fail (where + "files." + r, "required file role missing");
    return out;
}

bool isHex64 (const std::string& s)
{
    if (s.size() != 64) return false;
    for (char c : s) if (! ((c >= '0' && c <= '9') || (c >= 'a' && c <= 'f'))) return false;
    return true;
}

std::set<std::string> referenced (const VoiceManifest& m)
{
    std::set<std::string> r;
    for (const auto& kv : m.guide.files) r.insert (kv.second);
    if (m.converter) for (const auto& kv : m.converter->files) r.insert (kv.second);
    return r;
}
} // namespace

VoiceManifest parseManifest (std::string_view text)
{
    json j = json::parse (text.begin(), text.end(), nullptr, false);
    if (j.is_discarded() || ! j.is_object()) fail ("manifest", "not a valid JSON object");
    VoiceManifest m;
    if (nonEmptyString (j, "format", "") != "singvoice") fail ("format", "must be \"singvoice\"");
    const auto fv = need (j, "format_version", "");
    if (! fv.is_number_integer() || fv.get<long long>() != 1) fail ("format_version", "must be 1");
    m.formatVersion = 1;
    m.name = nonEmptyString (j, "name", "");
    m.consent = nonEmptyString (j, "consent", "");
    m.guideLicence = nonEmptyString (j, "guide_licence", "");

    const auto g = need (j, "guide", "");
    if (! g.is_object()) fail ("guide", "must be an object");
    if (nonEmptyString (g, "type", "guide.") != "diffsinger") fail ("guide.type", "must be \"diffsinger\"");
    const auto intField = [&] (const json& o, const char* key, const std::string& where) {
        const auto v = need (o, key, where);
        if (! v.is_number_integer()) fail (where + key, "must be an integer");
        return v.get<long long>();
    };
    if (intField (g, "sample_rate", "guide.") != 44100) fail ("guide.sample_rate", "must be 44100");
    if (intField (g, "hop_size", "guide.") != 512) fail ("guide.hop_size", "must be 512");
    const auto steps = intField (g, "steps", "guide.");
    if (steps < 1 || steps > 1000) fail ("guide.steps", "must be 1..1000");
    m.guide.steps = static_cast<int> (steps);
    const auto depth = need (g, "depth", "guide.");
    if (! depth.is_number() || ! (depth.get<double>() > 0.0 && depth.get<double>() <= 1.0)) fail ("guide.depth", "must be in (0, 1]");
    m.guide.depth = depth.get<double>();
    if (g.contains ("language")) m.guide.language = nonEmptyString (g, "language", "guide.");
    m.guide.files = readFiles (g, "guide.", { "acoustic", "vocoder", "phonemes" }, { "speaker", "languages" });

    if (j.contains ("converter") && ! j.at ("converter").is_null()) {
        const auto& c = j.at ("converter");
        if (! c.is_object()) fail ("converter", "must be an object or null");
        if (nonEmptyString (c, "type", "converter.") != "rvc-v2") fail ("converter.type", "must be \"rvc-v2\"");
        const auto sr = intField (c, "sample_rate", "converter.");
        if (sr != 48000 && sr != 32000) fail ("converter.sample_rate", "must be 48000 or 32000");
        ConverterSpec cs;
        cs.sampleRate = static_cast<int> (sr);
        if (c.contains ("speaker_id")) {
            const auto sid = intField (c, "speaker_id", "converter.");
            if (sid < 0) fail ("converter.speaker_id", "must be >= 0");
            cs.speakerId = static_cast<int> (sid);
        }
        cs.files = readFiles (c, "converter.", { "synth", "content" }, {});
        m.converter = std::move (cs);
    }

    const auto h = need (j, "sha256", "");
    if (! h.is_object()) fail ("sha256", "must be an object");
    std::set<std::string> keys;
    for (auto it = h.begin(); it != h.end(); ++it) {
        if (! it.value().is_string() || ! isHex64 (it.value().get<std::string>())) fail ("sha256." + it.key(), "must be 64 lower-case hex digits");
        m.sha256[it.key()] = it.value().get<std::string>();
        keys.insert (it.key());
    }
    const auto refs = referenced (m);
    for (const auto& r : refs) if (! keys.count (r)) fail ("sha256." + r, "no hash for a referenced file");
    for (const auto& k : keys) if (! refs.count (k)) fail ("sha256." + k, "hash for a file the manifest does not reference");
    return m;
}

void validatePackage (const std::filesystem::path& dir, const VoiceManifest& m, std::uintmax_t maxFileBytes)
{
    namespace fs = std::filesystem;
    for (const auto& rel : referenced (m)) {
        if (! safePath (rel)) fail (rel, "not a safe relative path");
        const auto it = m.sha256.find (rel);
        if (it == m.sha256.end()) fail (rel, "not listed in sha256");
        const fs::path file = dir / fs::path (rel);
        std::error_code ec;
        const auto st = fs::symlink_status (file, ec);
        if (ec || ! fs::is_regular_file (st)) fail (rel, "missing or not a regular file");
        const auto size = fs::file_size (file, ec);
        if (ec) fail (rel, "cannot read size");
        if (size > maxFileBytes) fail (rel, "file larger than the allowed maximum");
        std::ifstream in (file, std::ios::binary);
        if (! in) fail (rel, "cannot open");
        Sha256 sha;
        std::vector<char> buf (1 << 20);
        while (in) {
            in.read (buf.data(), static_cast<std::streamsize> (buf.size()));
            sha.update (buf.data(), static_cast<std::size_t> (in.gcount()));
        }
        if (sha.finishHex() != it->second) fail (rel, "SHA-256 mismatch");
    }
}

} // namespace singvst
