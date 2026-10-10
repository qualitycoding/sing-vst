// Interface frozen by plan D-003. See plan/DECISIONS.md.
#pragma once
#include <cstddef>
#include <stdexcept>
#include <string>

namespace singvst {

/** Thrown by every stub until the implementing step replaces it. Derives from std::logic_error so that no
    test asserting ValidationError, ParseError or Cancelled can pass against a stub (lesson L-20261009T123011Z). */
struct NotImplemented : std::logic_error {
    explicit NotImplemented (const std::string& what) : std::logic_error ("not implemented: " + what) {}
};

/** Lyric text could not be parsed. position is the 0-based byte offset of the offending character. */
struct ParseError : std::runtime_error {
    ParseError (const std::string& message, std::size_t pos) : std::runtime_error (message), position (pos) {}
    std::size_t position;
};

/** Input violates a documented precondition, or a voice package / model failed validation. */
struct ValidationError : std::runtime_error {
    using std::runtime_error::runtime_error;
};

/** A render observed its cancel flag and stopped. */
struct Cancelled : std::runtime_error {
    Cancelled() : std::runtime_error ("render cancelled") {}
};

} // namespace singvst
