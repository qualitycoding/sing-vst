// FROZEN — DO NOT MODIFY. Frozen by plan Phase 2E (tests/FROZEN_MANIFEST.sha256). Rules: plan/DECISIONS.md. Change only via TEST_CHALLENGE.md.
// Shared test helpers. Each helper states its precondition and has no fallback (PK-27).
#pragma once
#include <filesystem>
#include <fstream>
#include <iterator>
#include <stdexcept>
#include <string>
#include "singvst/lyrics.hpp"

namespace testutil {

/** Reads a whole file as bytes. Precondition: the file exists; otherwise throws std::runtime_error naming it. */
inline std::string readFile (const std::filesystem::path& p)
{
    std::ifstream f (p, std::ios::binary);
    if (! f) throw std::runtime_error ("test fixture missing: " + p.string());
    return { std::istreambuf_iterator<char> (f), std::istreambuf_iterator<char>() };
}

inline std::filesystem::path fixture (const std::string& rel) { return std::filesystem::path { SINGVST_FIXTURES } / rel; }

inline singvst::LyricToken text (std::string t, bool cont = false)
{
    singvst::LyricToken k; k.kind = singvst::TokenKind::Text; k.text = std::move (t); k.continuesWord = cont; return k;
}

inline singvst::LyricToken phon (std::vector<std::string> p, bool cont = false)
{
    singvst::LyricToken k; k.kind = singvst::TokenKind::Phonemes; k.phonemes = std::move (p); k.continuesWord = cont; return k;
}

inline singvst::LyricToken extend() { singvst::LyricToken k; k.kind = singvst::TokenKind::Extend; return k; }

} // namespace testutil
