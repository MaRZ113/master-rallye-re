#pragma once

// Separate, optional configuration and selection policy. Legacy INI parsing
// belongs to core.hpp and is intentionally unchanged.
#include "core.hpp"
#include <array>
#include <string>
#include <string_view>

namespace extra_options {

struct Config {
    bool enabled = false;
    bool liveries = false;
    bool tires = false;
    // [Ghost] / [Difficulty] (EXTRA-GHOST1). The ghost caves re-read the three
    // [Ghost] child options from this file on every Quick Race start.
    bool ghost = false;
    bool ghost_with_opponents = false;
    bool ghost_record_all_modes = false;
    bool ghost_use_alpha_model = true;
    bool five_difficulties = false;
};

struct ConfigResult {
    bool accepted = false;
    Config config{};
    const char* error = "";
};

inline ConfigResult parse_config(std::string_view text) {
    ConfigResult result;
    Config parsed;
    if (text.empty() || text.size() > 4096) { result.error = "size"; return result; }
    for (std::size_t i = 0; i < text.size(); ++i) {
        const auto c = static_cast<unsigned char>(text[i]);
        if (c == 0 || c > 0x7f || (c == '\r' && (i + 1 == text.size() || text[i+1] != '\n'))) {
            result.error = "encoding"; return result;
        }
    }
    bool general = false, customization = false, ghost = false, difficulty = false, version = false;
    bool seen_enabled = false, seen_liveries = false, seen_tires = false;
    bool seen_ghost[4]{}, seen_levels = false;
    std::string section;
    std::size_t start = 0;
    while (start <= text.size()) {
        const auto end = text.find('\n', start);
        auto line = text.substr(start, end == std::string_view::npos ? text.size() - start : end - start);
        if (!line.empty() && line.back() == '\r') line.remove_suffix(1);
        line = rmod1::trim_ascii(line);
        if (!line.empty() && line.front() != ';' && line.front() != '#') {
            if (line.front() == '[') {
                if (line.size() < 3 || line.back() != ']') { result.error = "section syntax"; return result; }
                section = rmod1::ascii_lower(rmod1::trim_ascii(line.substr(1, line.size() - 2)));
                bool* seen = section == "general" ? &general : section == "customization" ? &customization :
                             section == "ghost" ? &ghost : section == "difficulty" ? &difficulty : nullptr;
                if (!seen || *seen) { result.error = "unknown or duplicate section"; return result; }
                *seen = true;
            } else {
                const auto eq = line.find('=');
                if (eq == std::string_view::npos || line.find('=', eq + 1) != std::string_view::npos) {
                    result.error = "assignment"; return result;
                }
                const auto key = rmod1::ascii_lower(rmod1::trim_ascii(line.substr(0, eq)));
                const auto value = rmod1::trim_ascii(line.substr(eq + 1));
                if (section == "general" && key == "configversion") {
                    unsigned number = 0;
                    if (version || !rmod1::parse_unsigned(value, number) || number != 1) {
                        result.error = "version"; return result;
                    }
                    version = true;
                } else if (section == "customization") {
                    bool* target = key == "enabled" ? &parsed.enabled :
                                   key == "liveries" ? &parsed.liveries :
                                   key == "tires" ? &parsed.tires : nullptr;
                    bool* seen = key == "enabled" ? &seen_enabled : key == "liveries" ? &seen_liveries :
                                 key == "tires" ? &seen_tires : nullptr;
                    if (!target || *seen || !rmod1::parse_bool(value, *target)) {
                        result.error = "unknown, duplicate or invalid option"; return result;
                    }
                    *seen = true;
                } else if (section == "ghost") {
                    static constexpr const char* keys[] = {"enabled", "withopponents", "recordallmodes", "usealphamodel"};
                    bool* targets[] = {&parsed.ghost, &parsed.ghost_with_opponents, &parsed.ghost_record_all_modes, &parsed.ghost_use_alpha_model};
                    unsigned k = 0;
                    while (k < 4 && key != keys[k]) ++k;
                    if (k == 4 || seen_ghost[k] || (value != "0" && value != "1")) {
                        result.error = "unknown, duplicate or invalid ghost option"; return result;
                    }
                    // 0/1 only: the caves read these keys with GetPrivateProfileIntA.
                    *targets[k] = value == "1";
                    seen_ghost[k] = true;
                } else if (section == "difficulty" && key == "levels") {
                    unsigned levels = 0;
                    if (seen_levels || !rmod1::parse_unsigned(value, levels) || (levels != 4 && levels != 5)) {
                        result.error = "Difficulty.Levels must be 4 or 5"; return result;
                    }
                    parsed.five_difficulties = levels == 5;
                    seen_levels = true;
                } else { result.error = "unknown key"; return result; }
            }
        }
        if (end == std::string_view::npos) break;
        start = end + 1;
    }
    if (!version) { result.config = {}; result.error = "missing version"; return result; }
    result.config = parsed;
    result.accepted = true;
    return result;
}

enum class Tire : unsigned { Stock, Tarmac, HardDirt, Gravel, Grass, Mud };
inline constexpr std::array<const char*, 6> kTireNames = {{
    "", "tarmac", "harddirt", "gravel", "grass", "mud"
}};

struct RaceContext {
    int race_type = -1;
    int players = 0;
    int participant = -1;
    int player_type = -1;
    int physical_car_id = -1;
    int selected_car_id = -1;
    bool attract = true;
    bool replay = true;
    bool already_initialized = true;
};

// No native writes: returns the exact pair an independently validated runtime
// adapter may use. Stock means passthrough; it never invents a replacement.
struct TirePlan { bool applies = false; bool passthrough = true; const char* front = nullptr; const char* rear = nullptr; };
inline TirePlan plan_tires(const Config& config, Tire choice, const RaceContext& ctx, unsigned complete_tables) {
    const auto index = static_cast<unsigned>(choice);
    if (!config.enabled || !config.tires || index >= kTireNames.size() || ctx.race_type != 2 ||
        ctx.players != 1 || ctx.participant != 0 || ctx.player_type != 1 ||
        ctx.physical_car_id < 0 || ctx.physical_car_id != ctx.selected_car_id ||
        ctx.attract || ctx.replay || ctx.already_initialized) return {};
    if (choice == Tire::Stock) return {true, true, nullptr, nullptr};
    if (!(complete_tables & (1u << index))) return {};
    return {true, false, kTireNames[index], kTireNames[index]};
}

} // namespace extra_options
