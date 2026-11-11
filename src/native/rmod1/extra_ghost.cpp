#define WIN32_LEAN_AND_MEAN
#define NOMINMAX
#include <windows.h>
#include "extra_ghost.hpp"
#include "extra_ghost_plan.hpp"
#include "extra_options.hpp"
#include "rmod2_inprocess.hpp"
#include "vehicle_roster.hpp"
#include <cstdio>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iterator>
#include <string>
#include <vector>

// EXTRA-GHOST1: GHOST1 Ghost Mode + five difficulty levels on the unmodified retail EXE.
// The caves live in a loader-owned region (extra_ghost_plan::kBase) because SDK33 owns the
// .text slack the GHOST1 test EXEs used; only the hook sites in retail code are written.
namespace extra_ghost {
namespace {
namespace fs = std::filesystem;

void log(const fs::path& dir, const char* text) noexcept {
    try { std::ofstream f(dir / "MRallyeExtraOptions.log", std::ios::app); f << text << '\n'; } catch (...) {}
}

std::vector<std::uint8_t> hex(const char* text) {
    std::vector<std::uint8_t> out;
    const auto nibble = [](char c) { return static_cast<std::uint8_t>(c <= '9' ? c - '0' : (c | 0x20) - 'a' + 10); };
    for (std::size_t i = 0; text[i] && text[i + 1]; i += 2)
        out.push_back(static_cast<std::uint8_t>(nibble(text[i]) << 4 | nibble(text[i + 1])));
    return out;
}

// The loose QuickModeSelect.xml carries the GHOST panel (group 5, buttons 10/11); without it the
// mode hooks would address controls that do not exist.
bool ghost_frontend_present(const fs::path& dir) {
    // The game opens loose scenes relative to its working directory (the SDK launcher's
    // resource root); a plain install has the same folder as the EXE.
    // The Vehicle Manager roster overlay is served before both (VehicleRoster import hook), so read what the
    // game will actually open.
    std::ifstream f;
    char served[MAX_PATH * 2]{};
    if (vehicle_roster::redirect("DataScene/FrontendScreens/QuickModeSelect.xml", served, sizeof(served))) f.open(served, std::ios::binary);
    if (!f) f.open("DataScene/FrontendScreens/QuickModeSelect.xml", std::ios::binary);
    if (!f) f.open(dir / "DataScene/FrontendScreens/QuickModeSelect.xml", std::ios::binary);
    if (!f) return false;
    const std::string xml((std::istreambuf_iterator<char>(f)), {});
    return xml.find("GhostList") != std::string::npos && xml.find("RightArrowGhost") != std::string::npos;
}
}

bool initialize() noexcept {
    fs::path dir;
    try {
        char exe[MAX_PATH]{};
        const DWORD n = GetModuleFileNameA(nullptr, exe, MAX_PATH);
        if (!n || n >= MAX_PATH) return false;
        dir = fs::path(exe).parent_path();
        std::ifstream f(dir / "MRallyeExtraOptions.ini", std::ios::binary);
        if (!f) return false;
        const std::string ini((std::istreambuf_iterator<char>(f)), {});
        const auto parsed = extra_options::parse_config(ini);
        if (!parsed.accepted) { log(dir, "GHOST_DISABLED config rejected"); return false; }
        std::uint32_t features = (parsed.config.ghost ? extra_ghost_plan::kGhost : 0u) |
                                 (parsed.config.five_difficulties ? extra_ghost_plan::kDifficulty : 0u);
        if (!features) { log(dir, "GHOST_DISABLED Ghost.Enabled=0 and Difficulty.Levels=4"); return true; }
        if ((features & extra_ghost_plan::kGhost) && !ghost_frontend_present(dir)) {
            log(dir, "GHOST_UNAVAILABLE DataScene/FrontendScreens/QuickModeSelect.xml with the GHOST panel is missing");
            features &= ~extra_ghost_plan::kGhost;
            if (!features) return false;
        }

        // Loader region: page 0 = caves + strings (RX), page 1 = INI path + summary buffer (RW).
        auto* region = static_cast<std::uint8_t*>(VirtualAlloc(reinterpret_cast<void*>(extra_ghost_plan::kBase),
            extra_ghost_plan::kSize, MEM_RESERVE | MEM_COMMIT, PAGE_READWRITE));
        if (region != reinterpret_cast<std::uint8_t*>(extra_ghost_plan::kBase)) {
            if (region) VirtualFree(region, 0, MEM_RELEASE);
            log(dir, "GHOST_FAILED fixed cave region 0x70020000 is not available");
            return false;
        }
        std::memcpy(region, extra_ghost_plan::kPage, sizeof(extra_ghost_plan::kPage));
        for (const auto& nop : extra_ghost_plan::kNops)
            if (!(features & nop.feature)) std::memset(region + nop.offset, 0x90, nop.size);
        // Absolute INI path so the caves do not depend on the working directory.
        const std::string path = (dir / "MRallyeExtraOptions.ini").string();
        char* ini_path = reinterpret_cast<char*>(extra_ghost_plan::kIniPath);
        std::snprintf(ini_path, extra_ghost_plan::kIniPathCapacity, "%s",
                      path.size() < extra_ghost_plan::kIniPathCapacity ? path.c_str() : ".\\MRallyeExtraOptions.ini");
        DWORD old = 0;
        if (!VirtualProtect(region, extra_ghost_plan::kCodePage, PAGE_EXECUTE_READ, &old) ||
            !FlushInstructionCache(GetCurrentProcess(), region, extra_ghost_plan::kCodePage)) {
            VirtualFree(region, 0, MEM_RELEASE);
            log(dir, "GHOST_FAILED cannot protect cave page");
            return false;
        }

        std::vector<std::vector<std::uint8_t>> bytes;
        std::vector<rmod2_boot::NativeWrite> writes;
        bytes.reserve(2 * std::size(extra_ghost_plan::kHooks));
        for (const auto& h : extra_ghost_plan::kHooks) {
            if (!(features & h.features)) continue;
            bytes.push_back(hex(h.expected_hex)); bytes.push_back(hex(h.replacement_hex));
            const auto& e = bytes[bytes.size() - 2]; const auto& r = bytes.back();
            writes.push_back({h.va, e.data(), r.data(), e.size(), h.id});
        }
        char error[256]{};
        if (!rmod2_boot::apply_native_writes(writes.data(), writes.size(), error, sizeof(error))) {
            VirtualFree(region, 0, MEM_RELEASE);
            char line[400]{}; std::snprintf(line, sizeof(line), "GHOST_FAILED hooks not installed: %s", error);
            log(dir, line);
            return false;
        }
        char line[300]{};
        std::snprintf(line, sizeof(line), "GHOST_READY ghost=%d five_difficulties=%d hooks=%u region=0x%08x WithOpponents=%d RecordAllModes=%d UseAlphaModel=%d (child options re-read at race start)",
                      (features & extra_ghost_plan::kGhost) ? 1 : 0, (features & extra_ghost_plan::kDifficulty) ? 1 : 0,
                      static_cast<unsigned>(writes.size()), extra_ghost_plan::kBase, parsed.config.ghost_with_opponents,
                      parsed.config.ghost_record_all_modes, parsed.config.ghost_use_alpha_model);
        log(dir, line);
        return true;
    } catch (...) {
        log(dir, "GHOST_FAILED unexpected initialization error");
        return false;
    }
}
} // namespace extra_ghost
