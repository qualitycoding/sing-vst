// Temporary build smoke test, removed before the freeze.
#include <catch2/catch_test_macros.hpp>
#include "singvst/errors.hpp"
#include "singvst/lyrics.hpp"
TEST_CASE ("smoke") { CHECK_THROWS_AS (singvst::parseLyrics ("la"), singvst::NotImplemented); }
