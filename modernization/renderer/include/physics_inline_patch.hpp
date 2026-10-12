#pragma once
#include "game_fov.hpp"
#include <array>
#include <cstring>
namespace gfx2 {
struct InlinePatchUnit {
    void* address = nullptr;
    size_t size = 0;
    std::array<uint8_t, 8> original{};
    std::array<uint8_t, 8> replacement{};
    bool owned = false;
};

inline bool exchange_physics_inline(PatchMemory& memory, InlinePatchUnit& unit, bool installing, bool& rollback_verified) noexcept {
    if (!unit.address || (unit.size != 6 && unit.size != 7 && unit.size != 8)) return false;
    const auto& expected = installing ? unit.original : unit.replacement;
    const auto& replacement = installing ? unit.replacement : unit.original;
    std::array<uint8_t, 8> actual{};
    if (!memory.read(actual.data(), unit.address, unit.size) ||
        std::memcmp(actual.data(), expected.data(), unit.size) != 0) return false;
    DWORD old = 0, ignored = 0;
    if (!memory.protect(unit.address, unit.size, PAGE_EXECUTE_READWRITE, old)) return false;
    bool okay = memory.write(unit.address, replacement.data(), unit.size) &&
        memory.read(actual.data(), unit.address, unit.size) &&
        std::memcmp(actual.data(), replacement.data(), unit.size) == 0 &&
        memory.flush(unit.address, unit.size);
    const bool protection_restored = memory.protect(unit.address, unit.size, old, ignored);
    if (okay && protection_restored) {
        unit.owned = installing;
        return true;
    }

    DWORD recovery = 0;
    bool restored = memory.protect(unit.address, unit.size, PAGE_EXECUTE_READWRITE, recovery) &&
        memory.write(unit.address, expected.data(), unit.size) &&
        memory.read(actual.data(), unit.address, unit.size) &&
        std::memcmp(actual.data(), expected.data(), unit.size) == 0 &&
        memory.flush(unit.address, unit.size);
    const bool permissions = memory.protect(unit.address, unit.size, old, ignored);
    rollback_verified = rollback_verified && restored && permissions;
    if (!restored || !permissions) unit.owned = true;
    return false;
}

}
