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
    int sampleRate = 44100;            // must be 44100 (C-009, vocoder)
    int hopSize = 512;                 // must be 512
    std::string language = "en";       // prefix tried for 'lang/phone' model phonemes (C-035)
    int steps = 20;                    // acoustic sampling steps, 1..1000 (C-034)
    double depth = 1.0;                // shallow-diffusion depth, (0, 1] (C-034)
    std::map<std::string, std::string> files; // role -> relative path. Required: acoustic, vocoder, phonemes, config. Optional: languages, phoneme_map
};

struct ConverterSpec {
    int sampleRate = 48000;            // 48000 or 32000 (RVC v2 configs, C-005)
    int speakerId = 0;
    std::map<std::string, std::string> files; // role -> relative path. Required: synth, content
};

struct VoiceManifest {
    int formatVersion = 1;
    std::string name;
    std::string consent;               // non-empty attestation (A-011)
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
