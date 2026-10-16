#pragma once
// Opt-in corrections of defects that exist in the original PS2 content (PS2ContentFixes=1; default 0 =
// original). Each row replaces one pinned asset by a pinned corrected copy with identical counts, mesh
// order, modes and texture bindings, so every per-profile table keyed by the original stays valid.
// Evidence and generator: docs/vehicle-fleet-port3/crew-face1/.
#include <cstddef>
#include <cstring>
#include <string>
#include "ps2_config.hpp"

namespace gfx2::ps2port {

struct PS2ContentFix {
    const char* id;
    unsigned role;  // 0 frontend COMPLETE profile, 3 race fleet CAR child
    const char* originalSha;
    const char* filename;
    const char* sha;
    std::size_t size;
};

inline constexpr PS2ContentFix kPS2ContentFixes[] = {
    {"NAVARA-CREWFACE1", 3, "336318a5cc30f0cd7bf3c6f9addcf7e10848a1d762f5e7e88abee7f2f8caee0e",
     "NAVARA-CAR-FLEET-CREWFACE1.ps2model", "586fd3d717007e407e0ffe8894b37e3ae78377c35cb4abe43617f54a96fd194e", 373616},
    {"TATA-WINDOW1", 3, "20262ea17be8ef15e0faea7b70dc1ae2cff47df9aec2410fe3538587a5d18660",
     "TATA-CAR-FLEET-WINDOW1.ps2model", "8a03e06623a849335e8568b5b613a352cebeb4b9c56a617e9a6320d69f0b0252", 420814},
    {"KAMAZ-COMPLETE-WINDOW1", 0, "df3d58336f6596cc4915b055820c5d0008b116b33091cca6915abdf971d3826c",
     "KAMAZ-COMPLETE-FLEET-WINDOW1.ps2model", "9351c7a6cb39cd9ce49695b94c5b3b6f7bb70646870d0e1615d86f26f4c005e5", 827756},
    // Same cracked-over-intact right window in the race CAR (found by scan, confirmed by the user).
    {"KAMAZ-CAR-WINDOW1", 3, "1807d3e68bf080ad6c793ee548cad86d0846706bac8418b38495705196d401fa",
     "KAMAZ-CAR-FLEET-WINDOW1.ps2model", "763c3a892378faaf8685cd2b09d89e4f376338e81d4164835b2a4b7937adccf1", 463996},
};

inline const PS2ContentFix* content_fix(unsigned role, const char* originalSha) noexcept {
    if (!originalSha) return nullptr;
    for (const auto& fix : kPS2ContentFixes)
        if (fix.role == role && !std::strcmp(fix.originalSha, originalSha)) return &fix;
    return nullptr;
}

inline bool content_fixes_enabled(const std::wstring& ini) noexcept {
    return config::read_int(L"PS2ContentFixes", 0, ini.c_str()) == 1;
}

}  // namespace gfx2::ps2port
