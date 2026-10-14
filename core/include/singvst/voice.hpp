// Interface frozen by plan D-003; voice package format v1 in D-008.
#pragma once
#include <cstdint>
#include <filesystem>
#include <map>
#include <optional>
#include <string>
#include <string_view>

namespace singvst {

struct GuideSpec {
    int sampleRate = 44100;            // must be 44100 (C-009, C-036)
    int hopSize = 512;                 // must be 512
    std::string language = "en";       // prefix tried as '<language>/<phone>' when a phone is not in the model vocabulary (C-035)
    int steps = 20;                    // diffusion sampling steps, 1..1000; legacy models derive 'speedup' from it (C-034, D-012)
    double depth = 1.0;                // shallow-diffusion depth in (0, 1], clamped to the model's max_depth by the packer (C-034)
    // role -> relative path. Required: acoustic, vocoder, phonemes. Optional: speaker (raw float32 .emb), languages (JSON map).
    std::map<std::string, std::string> files;
};

struct ConverterSpec {
    int sampleRate = 48000;            // 48000 or 32000 (RVC v2 configs, C-005)
    int speakerId = 0;                 // value fed to the 'ds' input, >= 0
    std::map<std::string, std::string> files; // role -> relative path. Required: synth, content
};

struct VoiceManifest {
    int formatVersion = 1;
    std::string name;
    std::string consent;               // non-empty attestation (A-011)
    std::string guideLicence;          // non-empty: licence name and URL of the guide voicebank (D-026)
    GuideSpec guide;
    std::optional<ConverterSpec> converter;
    std::map<std::string, std::string> sha256; // relative path -> lower-case hex SHA-256; must cover every referenced file
};

/** Parses manifest.json text. Throws ValidationError on any schema rule in D-008. */
VoiceManifest parseManifest (std::string_view json);

/** For every referenced file: the path is safe and listed in sha256, the file exists under dir, is a regular file of at
    most maxFileBytes, and its SHA-256 matches. Throws ValidationError naming the first failing file. */
void validatePackage (const std::filesystem::path& dir, const VoiceManifest& manifest, std::uintmax_t maxFileBytes = (std::uintmax_t) 2 << 30);

} // namespace singvst
