// Private streaming SHA-256 (FIPS 180-4) shared by sha256Hex and validatePackage (D-008).
#pragma once
#include <array>
#include <cstddef>
#include <cstdint>
#include <string>

namespace singvst {
class Sha256 {
public:
    Sha256();
    void update (const void* data, std::size_t n);
    std::string finishHex();
private:
    void block (const std::uint8_t* p);
    std::array<std::uint32_t, 8> h;
    std::array<std::uint8_t, 64> buf {};
    std::size_t fill = 0;
    std::uint64_t total = 0;
};
} // namespace singvst
