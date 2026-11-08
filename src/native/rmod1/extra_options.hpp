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

// EXTRA-SET2 tyre compounds. Retail tyre "types" 0..4 are AI grip tiers (the
// AI writes its difficulty level to enController_Car+0x74); human cars always
// use type 0, whose five records are per surface. A compound scales the grip
// fields (PeakMu, CorneringCoeff) of the human wheel's type-0 records.
enum class Tire : unsigned { Stock, Tarmac, HardDirt, Gravel, Grass, Mud };
inline constexpr unsigned kTireCount = 6, kSurfaceCount = 5;
inline constexpr std::array<const char*, kTireCount> kTireLabels = {{
    "Stock", "Tarmac", "Hard Dirt", "Gravel", "Grass", "Mud"
}};
// Broker surface record prefixes (Vehicles/Tyres/<surface>0), ordered by looseness.
inline constexpr std::array<const char*, kSurfaceCount> kSurfaces = {{
    "tarmac", "harddirt", "gravel", "grass", "mud"
}};
// Record field order of the native loader 0x491120 (12 floats, 0x30 bytes).
inline constexpr unsigned kTyreFields = 12, kPeakMu = 0, kScaleFactor = 4, kCornering = 5, kCorneringGradient = 6;
inline constexpr std::array<const char*, kTyreFields> kTyreFieldNames = {{
    "PeakMu", "SoftRating", "IceRating", "WetRating", "ScaleFactor", "CorneringCoeff",
    "CorneringCoeffGradient", "PneumaticTrailCoeff", "CamberStiffness", "LongitudinalStiffness",
    "InflationStiffness", "InflationStiffnessDamping"
}};
// +10 % on the compound's own surface, +3 % next to it, then -7 % per step.
inline float grip_scale(Tire tire, unsigned surface) {
    const auto c = static_cast<unsigned>(tire);
    if (c == 0 || c >= kTireCount || surface >= kSurfaceCount) return 1.0f;
    const unsigned own = c - 1, distance = own > surface ? own - surface : surface - own;
    return distance == 0 ? 1.10f : 1.10f - 0.07f * static_cast<float>(distance);
}

struct Participant {
    int player_type = -1;   // Race/Car<n>/PlayerType, 1 = human
    int car_id = -1;        // Race/Car<n>/CarID
    bool attract = true;    // Race/AttractMode
};
// Any race mode: the choice follows the human player and physical CarID, not Race/Type.
inline bool tire_applies(const Config& config, const Participant& p) {
    return config.enabled && config.tires && p.player_type == 1 && !p.attract && p.car_id >= 0 && p.car_id < 256;
}

// Wheel record override: scales only records still equal to the stock type-0 record of a
// known surface, so it is idempotent and never touches AI tiers or foreign data.
inline bool same(float a, float b) { return a == b; }
inline int match_surface(const float* record, const float (&stock)[kSurfaceCount][kTyreFields]) {
    for (unsigned s = 0; s < kSurfaceCount; ++s)
        if (same(record[kPeakMu], stock[s][kPeakMu]) && same(record[kScaleFactor], stock[s][kScaleFactor]) &&
            same(record[kCornering], stock[s][kCornering]) && same(record[kCorneringGradient], stock[s][kCorneringGradient]))
            return static_cast<int>(s);
    return -1;
}
inline unsigned apply_compound(float* records, unsigned count, Tire tire, const float (&stock)[kSurfaceCount][kTyreFields]) {
    if (tire == Tire::Stock) return 0;
    unsigned changed = 0;
    for (unsigned r = 0; r < count; ++r) {
        float* record = records + r * kTyreFields;
        const int s = match_surface(record, stock);
        if (s < 0) continue;
        const float k = grip_scale(tire, static_cast<unsigned>(s));
        record[kPeakMu] = stock[s][kPeakMu] * k;
        record[kCornering] = stock[s][kCornering] * k;
        ++changed;
    }
    return changed;
}

} // namespace extra_options
