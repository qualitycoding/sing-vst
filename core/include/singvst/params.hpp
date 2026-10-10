// Interface frozen by plan D-003; the single source of every user-visible parameter (D-010, PK-40).
#pragma once
#include <array>
#include <string_view>

namespace singvst {

struct ParamSpec {
    std::string_view id;      // stable automation ID (never renamed; JUCE ParameterID version 1)
    std::string_view name;    // display name
    float minValue;
    float maxValue;
    float defaultValue;
    float step;               // 0 = continuous; 1 = integer / toggle
    std::string_view unit;
};

/** Order is the host parameter order. The plugin's AudioProcessorValueTreeState, the editor and docs/PARAMETERS.md are
    generated from this table; T-049 checks the plugin exposes exactly these. */
inline constexpr std::array<ParamSpec, 5> kParams { {
    { "gain",       "Output gain",         -36.0f, 12.0f,  0.0f, 0.0f, "dB" },
    { "convert",    "Voice conversion",      0.0f,  1.0f,  1.0f, 1.0f, ""   },
    { "portamento", "Portamento",            0.0f, 0.30f, 0.06f, 0.0f, "s"  },
    { "vibrato",    "Vibrato depth",         0.0f, 100.0f, 0.0f, 0.0f, "cents" },
    { "seed",       "Converter seed",        0.0f, 9999.0f, 0.0f, 1.0f, ""  },
} };

} // namespace singvst
