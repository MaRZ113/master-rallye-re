#pragma once

// R-MOD1 shared semantic core.  This header has no Win32, renderer, Vehicle
// SDK, filesystem, or process-memory dependencies.  The suspended launcher
// and any future proxy adapter must link this same implementation.

#include <algorithm>
#include <array>
#include <cctype>
#include <cstdint>
#include <functional>
#include <iterator>
#include <map>
#include <set>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

namespace rmod1 {

constexpr std::size_t kMaxConfigBytes = 4096;
constexpr std::uint32_t kRetailFileSize = 3121214;
constexpr std::uint16_t kPe32MachineI386 = 0x014c;
constexpr char kRetailSha256[] =
    "bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4";
constexpr unsigned kNativeAiMaximum = 3;
constexpr unsigned kMaximumAi = 7;
constexpr unsigned kMaximumTotalCars = 8;

enum class Policy { Stock, Full, T1, T2, T3, Mixed, Diverse };
enum class GameMode { QuickRace, RallyeCup, MasterRallye, Invitation, Challenge, Practice, Unknown };
enum class AddonMode { StockOnly, RegisteredOnly };
enum class SelectionKind { NativeStock, SelectedId, Refused };
#if defined(RMOD3_G2_PLAYER_OVERRIDE)
enum class PlayerVehicleMode { Stock = 0, Forced = 1, Random = 2 };
#endif
enum class Severity { Info, Warning, Error };
enum class PatchTargetKind { ImageRva, AllocatedRegion };
enum class PatchPhase { BeforeGameEntry, LaterUnsupported };
enum class RegionPermission { ReadOnly, ReadWrite, ReadExecute };

struct Diagnostic {
    Severity severity = Severity::Error;
    std::string code;
    std::string message;
    std::size_t line = 0;
};

inline bool has_error(const std::vector<Diagnostic>& diagnostics);

struct Config {
    unsigned config_version = 1; // missing/invalid INI remains a no-feature safe default
    std::array<Policy, 5> mode_policies{{
        Policy::Stock, Policy::Stock, Policy::Stock, Policy::Stock, Policy::Stock
    }};
    // The V1 members remain so previously accepted public configs keep their
    // exact enable/count semantics. V2 derives feature selection from policies
    // and MaxOpponents instead of hidden enable switches.
    bool randomizer_enabled = false;
    Policy quick_race = Policy::Stock;
    bool duplicates_when_needed = true;
    bool opponents_enabled = false;
    unsigned max_opponents = 3;
    // Five-to-seven-AI Quick Races are opt-in experimental and remain subject
    // to the eight-participant limit. Actual human topology is validated
    // from Race/NumPlayers and participant records after setup exists.
    bool experimental_extended_ai = false;
    AddonMode addons = AddonMode::StockOnly;
    bool logging_enabled = false;
#if defined(RMOD3_G2_PLAYER_OVERRIDE)
    // G2-only fields are excluded from F3/G1 builds so their frozen runtime
    // identities remain reproducible from the existing source checkpoints.
    PlayerVehicleMode player_vehicle_mode = PlayerVehicleMode::Stock;
    int forced_player_car_id = 0;
    Policy player_random_policy = Policy::Full;
#endif
};

// Process-local Challenge preview identity. The selected absolute CarID is
// prepared when the preview is built and then consumed by the race owner;
// policy reloads cannot silently replace the visible opponent.
struct ChallengeSelection {
    bool ready = false;
    int event_id = -1;
    int human_id = -1;
    int authored_opponent_id = -1;
    int selected_opponent_id = -1;
    unsigned generation_id = 0;
    Policy policy = Policy::Stock;
    std::string config_hash;

    bool matches(int event, int human, int authored) const {
        return ready && event_id == event && human_id == human &&
            authored_opponent_id == authored;
    }

    int preview_identity() const {
        return selected_opponent_id >= 0 ? selected_opponent_id : authored_opponent_id;
    }

    int consume(int event, int human, int authored) const {
        return matches(event, human, authored) ? selected_opponent_id : -1;
    }

    void prepare(int event, int human, int authored, unsigned generation,
                 Policy selected_policy, std::string selected_hash) {
        ready = true;
        event_id = event;
        human_id = human;
        authored_opponent_id = authored;
        selected_opponent_id = -1;
        generation_id = generation;
        policy = selected_policy;
        config_hash = std::move(selected_hash);
    }

    void clear() {
        ready = false;
        event_id = human_id = authored_opponent_id = selected_opponent_id = -1;
        generation_id = 0;
        policy = Policy::Stock;
        config_hash.clear();
    }
};

inline bool runtime_operation_selected(std::uint32_t operation_feature,
                                       std::uint32_t requested_features,
                                       std::uint32_t bootstrap_feature,
                                       bool diagnostics_enabled) {
    if (operation_feature == bootstrap_feature)
        return requested_features != 0 || diagnostics_enabled;
    return (operation_feature & requested_features) != 0;
}

struct ParseOutcome {
    bool accepted = false;
    Config config{};
    std::vector<Diagnostic> diagnostics;
};

inline std::string ascii_lower(std::string_view value) {
    std::string result;
    result.reserve(value.size());
    for (unsigned char c : value) {
        result.push_back(static_cast<char>(c >= 'A' && c <= 'Z' ? c + ('a' - 'A') : c));
    }
    return result;
}

inline std::string_view trim_ascii(std::string_view value) {
    while (!value.empty() && (value.front() == ' ' || value.front() == '\t')) value.remove_prefix(1);
    while (!value.empty() && (value.back() == ' ' || value.back() == '\t')) value.remove_suffix(1);
    return value;
}

inline bool parse_bool(std::string_view value, bool& output) {
    const auto lowered = ascii_lower(value);
    if (lowered == "1") { output = true; return true; }
    if (lowered == "0") { output = false; return true; }
    if (lowered == "true") { output = true; return true; }
    if (lowered == "false") { output = false; return true; }
    return false;
}

inline bool parse_unsigned(std::string_view value, unsigned& output);

inline bool parse_policy(std::string_view value, Policy& output) {
    const auto lowered = ascii_lower(value);
    if (lowered == "0" || lowered == "stock") output = Policy::Stock;
    else if (lowered == "1" || lowered == "full") output = Policy::Full;
    else if (lowered == "2" || lowered == "t1") output = Policy::T1;
    else if (lowered == "3" || lowered == "t2") output = Policy::T2;
    else if (lowered == "4" || lowered == "t3") output = Policy::T3;
    else if (lowered == "5" || lowered == "mixed") output = Policy::Mixed;
    else if (lowered == "6" || lowered == "diverse") output = Policy::Diverse;
    else return false;
    return true;
}

inline bool parse_policy_for_version(std::string_view value, unsigned version, Policy& output) {
    const auto lowered = ascii_lower(value);
    if (lowered == "stock") { output = Policy::Stock; return true; }
    if (lowered == "t1") { output = Policy::T1; return true; }
    if (lowered == "t2") { output = Policy::T2; return true; }
    if (lowered == "t3") { output = Policy::T3; return true; }
    if (lowered == "full") { output = Policy::Full; return true; }
    if (lowered == "mixed") { output = Policy::Mixed; return true; }
    if (lowered == "diverse") { output = Policy::Diverse; return true; }
    unsigned numeric = 0;
    if (!parse_unsigned(value, numeric) || numeric > 6) return false;
    if (version == 1) {
        static constexpr Policy v1[] = {Policy::Stock, Policy::Full, Policy::T1,
            Policy::T2, Policy::T3, Policy::Mixed, Policy::Diverse};
        output = v1[numeric];
        return true;
    }
    if (version == 2
#if defined(RMOD3_G2_PLAYER_OVERRIDE)
        || version == 3
#endif
        ) {
        static constexpr Policy v2[] = {Policy::Stock, Policy::T1, Policy::T2,
            Policy::T3, Policy::Full, Policy::Mixed, Policy::Diverse};
        output = v2[numeric];
        return true;
    }
    return false;
}

inline unsigned policy_numeric_id(Policy policy) {
    switch (policy) {
    case Policy::Stock: return 0;
    case Policy::Full: return 1;
    case Policy::T1: return 2;
    case Policy::T2: return 3;
    case Policy::T3: return 4;
    case Policy::Mixed: return 5;
    case Policy::Diverse: return 6;
    }
    return 0;
}

inline unsigned policy_numeric_id_for_version(Policy policy, unsigned version) {
    if (version != 2
#if defined(RMOD3_G2_PLAYER_OVERRIDE)
        && version != 3
#endif
        ) return policy_numeric_id(policy);
    switch (policy) {
    case Policy::Stock: return 0;
    case Policy::T1: return 1;
    case Policy::T2: return 2;
    case Policy::T3: return 3;
    case Policy::Full: return 4;
    case Policy::Mixed: return 5;
    case Policy::Diverse: return 6;
    }
    return 0;
}

inline const char* policy_name(Policy policy) {
    switch (policy) {
    case Policy::Stock: return "Stock";
    case Policy::Full: return "Full";
    case Policy::T1: return "T1";
    case Policy::T2: return "T2";
    case Policy::T3: return "T3";
    case Policy::Mixed: return "Mixed";
    case Policy::Diverse: return "Diverse";
    }
    return "Stock";
}

inline int mode_policy_index(GameMode mode) {
    switch (mode) {
    case GameMode::QuickRace: return 0;
    case GameMode::RallyeCup: return 1;
    case GameMode::MasterRallye: return 2;
    case GameMode::Invitation: return 3;
    case GameMode::Challenge: return 4;
    default: return -1;
    }
}

inline Policy policy_for_mode(const Config& config, GameMode mode) {
    if (config.config_version == 1) {
        return mode == GameMode::QuickRace && config.randomizer_enabled
            ? config.quick_race : Policy::Stock;
    }
    const int index = mode_policy_index(mode);
    return index >= 0 ? config.mode_policies[static_cast<std::size_t>(index)] : Policy::Stock;
}

inline bool config_requests_randomizer(const Config& config) {
    if (config.config_version == 1)
        return config.randomizer_enabled && config.quick_race != Policy::Stock;
    return std::any_of(config.mode_policies.begin(), config.mode_policies.end(),
        [](Policy policy) { return policy != Policy::Stock; });
}

inline bool config_needs_randomizer_hooks(const Config& config) {
    // V2's Stock policy is a live-editable per-mode off switch. Install the
    // pass-through callbacks once for a valid V2 package so a later policy
    // edit can take effect at the next generation boundary.
    return config.config_version == 2
#if defined(RMOD3_G2_PLAYER_OVERRIDE)
        || config.config_version == 3
#endif
        || config_requests_randomizer(config);
}

inline bool config_requests_opponent_extension(const Config& config) {
    return config.config_version == 1 ? config.opponents_enabled : config.max_opponents != 3;
}

inline bool config_allows_extended_ai(const Config& config) {
    return config.config_version == 1 ? config.experimental_extended_ai
        : config.max_opponents > kNativeAiMaximum;
}

inline bool parse_duplicates(std::string_view value, bool& when_needed) {
    const auto lowered = ascii_lower(value);
    if (lowered == "0" || lowered == "never") { when_needed = false; return true; }
    if (lowered == "1" || lowered == "whenneeded") { when_needed = true; return true; }
    return false;
}

inline bool parse_addon_mode(std::string_view value, AddonMode& output) {
    const auto lowered = ascii_lower(value);
    if (lowered == "0" || lowered == "stock" || lowered == "stockonly")
        output = AddonMode::StockOnly;
    else if (lowered == "1" || lowered == "auto" || lowered == "registeredonly")
        output = AddonMode::RegisteredOnly;
    else return false;
    return true;
}

inline const char* addon_mode_name(AddonMode mode) {
    return mode == AddonMode::RegisteredOnly ? "AutoRegistered" : "StockOnly";
}

inline bool parse_unsigned(std::string_view value, unsigned& output) {
    if (value.empty()) return false;
    unsigned parsed = 0;
    for (char c : value) {
        if (c < '0' || c > '9') return false;
        const unsigned digit = static_cast<unsigned>(c - '0');
        if (parsed > (UINT32_MAX - digit) / 10u) return false;
        parsed = parsed * 10u + digit;
    }
    output = parsed;
    return true;
}

inline ParseOutcome parse_ini(std::string_view bytes) {
    ParseOutcome result;
    result.config = Config{}; // whole-file safe defaults, including on every error
    auto fail = [&](std::string code, std::string message, std::size_t line = 0) {
        result.accepted = false;
        result.config = Config{};
        result.diagnostics.push_back({Severity::Error, std::move(code), std::move(message), line});
    };

    if (bytes.size() > kMaxConfigBytes) {
        fail("CONFIG_TOO_LARGE", "Configuration exceeds the 4096-byte limit.");
        return result;
    }
    for (std::size_t i = 0; i < bytes.size(); ++i) {
        const auto c = static_cast<unsigned char>(bytes[i]);
        if (c == 0) {
            fail("CONFIG_NUL", "NUL bytes are not allowed.");
            return result;
        }
        if (c > 0x7f) {
            fail("CONFIG_NON_ASCII", "Only ASCII configuration text is supported.");
            return result;
        }
        if (c == '\r' && (i + 1 >= bytes.size() || bytes[i + 1] != '\n')) {
            fail("CONFIG_LINE_ENDING", "Use LF or CRLF line endings; bare CR is invalid.");
            return result;
        }
    }

    Config parsed{};
    parsed.config_version = 2;
    std::set<std::string> sections;
    std::map<std::string, std::set<std::string>> keys;
    static constexpr const char* mode_keys[] = {
        "quickrace", "rallyecup", "masterrallye", "invitation", "challenge"
    };
    std::array<std::string, 5> raw_policies{};
    std::array<bool, 5> policy_seen{};
    std::string section;
    bool version_seen = false;
    unsigned config_version = 0;
    bool randomizer_enabled_seen = false;
    bool opponents_enabled_seen = false;
    bool extended_ai_seen = false;
    bool duplicates_seen = false;
    bool max_opponents_seen = false;
    bool addons_seen = false;
    bool logging_seen = false;
#if defined(RMOD3_G2_PLAYER_OVERRIDE)
    bool player_mode_seen = false;
    bool forced_player_car_seen = false;
    bool player_random_policy_seen = false;
#endif
    std::size_t line_number = 0;
    std::size_t begin = 0;
    while (begin <= bytes.size()) {
        ++line_number;
        const auto end = bytes.find('\n', begin);
        auto line = bytes.substr(begin, end == std::string_view::npos ? bytes.size() - begin : end - begin);
        if (!line.empty() && line.back() == '\r') line.remove_suffix(1);
        line = trim_ascii(line);
        if (!line.empty() && line.front() != ';' && line.front() != '#') {
            if (line.front() == '[') {
                if (line.size() < 3 || line.back() != ']') {
                    fail("CONFIG_SECTION_SYNTAX", "Section must be a single [Name] token.", line_number);
                    return result;
                }
                const auto raw_name = trim_ascii(line.substr(1, line.size() - 2));
                section = ascii_lower(raw_name);
                static const std::set<std::string> allowed = {"general", "randomizer", "opponents", "experimental", "addons", "logging"
#if defined(RMOD3_G2_PLAYER_OVERRIDE)
                    , "player"
#endif
                };
                if (!allowed.count(section)) {
                    fail("CONFIG_UNKNOWN_SECTION", "Unknown section: " + std::string(raw_name), line_number);
                    return result;
                }
                if (!sections.insert(section).second) {
                    fail("CONFIG_DUPLICATE_SECTION", "Section appears more than once: " + std::string(raw_name), line_number);
                    return result;
                }
            } else {
                if (section.empty()) {
                    fail("CONFIG_KEY_OUTSIDE_SECTION", "Every key must appear inside a known section.", line_number);
                    return result;
                }
                const auto equal = line.find('=');
                if (equal == std::string_view::npos || line.find('=', equal + 1) != std::string_view::npos) {
                    fail("CONFIG_ASSIGNMENT_SYNTAX", "Expected exactly one key=value assignment.", line_number);
                    return result;
                }
                const auto key_view = trim_ascii(line.substr(0, equal));
                const auto value_view = trim_ascii(line.substr(equal + 1));
                if (key_view.empty() || value_view.empty()) {
                    fail("CONFIG_EMPTY_KEY_OR_VALUE", "Key and value must both be non-empty.", line_number);
                    return result;
                }
                const auto key = ascii_lower(key_view);
                const auto value = ascii_lower(value_view);
                if (!keys[section].insert(key).second) {
                    fail("CONFIG_DUPLICATE_KEY", "Key appears more than once: " + std::string(key_view), line_number);
                    return result;
                }

                bool bool_value = false;
                if (section == "general" && key == "configversion") {
                    unsigned version = 0;
                    if (!parse_unsigned(value_view, version) || (version != 1 && version != 2
#if defined(RMOD3_G2_PLAYER_OVERRIDE)
                        && version != 3
#endif
                        )) {
                        fail("CONFIG_VERSION_UNSUPPORTED", "ConfigVersion must be 1 or 2"
#if defined(RMOD3_G2_PLAYER_OVERRIDE)
                            " or 3"
#endif
                            ".", line_number);
                        return result;
                    }
                    config_version = version;
                    parsed.config_version = version;
                    version_seen = true;
                } else if (section == "randomizer" && key == "enabled") {
                    if (!parse_bool(value, bool_value)) { fail("CONFIG_BOOL_INVALID", "Randomizer.Enabled must be 0, 1, true, or false.", line_number); return result; }
                    parsed.randomizer_enabled = bool_value;
                    randomizer_enabled_seen = true;
                } else if (section == "randomizer" &&
                           (key == "quickrace" || key == "rallyecup" ||
                            key == "masterrallye" || key == "invitation" || key == "challenge")) {
                    for (std::size_t index = 0; index < std::size(mode_keys); ++index) {
                        if (key == mode_keys[index]) {
                            raw_policies[index] = std::string(value_view);
                            policy_seen[index] = true;
                            break;
                        }
                    }
                } else if (section == "randomizer" && key == "duplicates") {
                    if (!parse_duplicates(value, parsed.duplicates_when_needed)) { fail("CONFIG_DUPLICATES_INVALID", "Duplicates must be 0 (Never), 1 (WhenNeeded), or the legacy WhenNeeded value.", line_number); return result; }
                    duplicates_seen = true;
                } else if (section == "opponents" && key == "enabled") {
                    if (!parse_bool(value, bool_value)) { fail("CONFIG_BOOL_INVALID", "Opponents.Enabled must be 0, 1, true, or false.", line_number); return result; }
                    parsed.opponents_enabled = bool_value;
                    opponents_enabled_seen = true;
                } else if (section == "opponents" && key == "maxopponents") {
                    unsigned count = 0;
                    if (!parse_unsigned(value_view, count) || count < 1 || count > kMaximumAi) {
                        fail("CONFIG_OPPONENT_LIMIT", "MaxOpponents must be an integer from 1 through 7.", line_number);
                        return result;
                    }
                    parsed.max_opponents = count;
                    max_opponents_seen = true;
                } else if (section == "experimental" && key == "extendedai") {
                    if (!parse_bool(value, bool_value)) { fail("CONFIG_BOOL_INVALID", "Experimental.ExtendedAI must be 0, 1, true, or false.", line_number); return result; }
                    parsed.experimental_extended_ai = bool_value;
                    extended_ai_seen = true;
                } else if (section == "addons" && key == "include") {
                    if (!parse_addon_mode(value, parsed.addons)) { fail("CONFIG_ADDON_POLICY_INVALID", "Addons.Include must be 0 (Stock-only), 1 (Auto), or a supported legacy alias.", line_number); return result; }
                    addons_seen = true;
                } else if (section == "logging" && key == "enabled") {
                    if (!parse_bool(value, bool_value)) { fail("CONFIG_BOOL_INVALID", "Logging.Enabled must be 0, 1, true, or false.", line_number); return result; }
                    parsed.logging_enabled = bool_value;
                    logging_seen = true;
#if defined(RMOD3_G2_PLAYER_OVERRIDE)
                } else if (section == "player" && key == "mode") {
                    unsigned mode = 0;
                    if (value == "stock") mode = 0;
                    else if (value == "forced") mode = 1;
                    else if (value == "random") mode = 2;
                    else if (!parse_unsigned(value_view, mode) || mode > 2) {
                        fail("CONFIG_PLAYER_MODE_INVALID", "Player.Mode must be 0 (Stock), 1 (Forced), or 2 (Random).", line_number);
                        return result;
                    }
                    parsed.player_vehicle_mode = static_cast<PlayerVehicleMode>(mode);
                    player_mode_seen = true;
                } else if (section == "player" && key == "forcedcarid") {
                    unsigned id = 0;
                    if (!parse_unsigned(value_view, id) || id > 24) {
                        fail("CONFIG_PLAYER_CAR_INVALID", "Player.ForcedCarID must be a stock physical CarID from 0 through 24.", line_number);
                        return result;
                    }
                    parsed.forced_player_car_id = static_cast<int>(id);
                    forced_player_car_seen = true;
                } else if (section == "player" && key == "randompolicy") {
                    if (!parse_policy_for_version(value_view, 3, parsed.player_random_policy)) {
                        fail("CONFIG_PLAYER_POLICY_INVALID", "Player.RandomPolicy must use the ConfigVersion=2 numeric mapping 0=Stock, 1=T1, 2=T2, 3=T3, 4=Full, 5=Mixed, 6=Diverse.", line_number);
                        return result;
                    }
                    player_random_policy_seen = true;
#endif
                } else {
                    fail("CONFIG_UNKNOWN_KEY", "Unknown key: [" + section + "] " + std::string(key_view), line_number);
                    return result;
                }
            }
        }
        if (end == std::string_view::npos) break;
        begin = end + 1;
    }
    if (!sections.count("general") || !version_seen) {
        fail("CONFIG_VERSION_REQUIRED", "A single [General] section with a supported ConfigVersion is required.");
        return result;
    }

    if (config_version == 1) {
#if defined(RMOD3_G2_PLAYER_OVERRIDE)
        if (sections.count("player")) {
            fail("CONFIG_V1_PLAYER_UNSUPPORTED", "ConfigVersion=1 does not accept the Player section.");
            return result;
        }
#endif
        for (std::size_t index = 1; index < policy_seen.size(); ++index) {
            if (policy_seen[index]) {
                fail("CONFIG_UNKNOWN_KEY", "ConfigVersion=1 accepts only Randomizer.QuickRace policies.");
                return result;
            }
        }
        if (policy_seen[0] && !parse_policy_for_version(raw_policies[0], 1, parsed.quick_race)) {
            fail("CONFIG_POLICY_INVALID", "V1 QuickRace must be 0..6 or a supported textual alias.");
            return result;
        }
        parsed.mode_policies[0] = parsed.quick_race;
        if (parsed.randomizer_enabled && !parsed.duplicates_when_needed && !parsed.opponents_enabled) {
            fail("CONFIG_DUPLICATE_GUARD_REQUIRED",
                 "Duplicates=Never with Randomizer requires Opponents.Enabled=1 so the prepared roster can be checked before Start.");
            return result;
        }
        if (parsed.experimental_extended_ai &&
            (!parsed.opponents_enabled || parsed.max_opponents < 4)) {
            fail("CONFIG_EXPERIMENTAL_EXTENDER_CONFLICT",
                 "Experimental.ExtendedAI=1 requires Opponents.Enabled=1 and MaxOpponents of at least 4.");
            return result;
        }
        result.diagnostics.push_back({Severity::Warning, "CONFIG_V1_MIGRATION",
            "ConfigVersion=1 keeps its legacy numeric mapping (1=Full). Migrate to ConfigVersion=2; V2 uses 1=T1 and 4=Full.", 0});
#if defined(RMOD3_G2_PLAYER_OVERRIDE)
    } else if (config_version == 2) {
#else
    } else {
#endif
        if (randomizer_enabled_seen || opponents_enabled_seen || extended_ai_seen || sections.count("experimental")
#if defined(RMOD3_G2_PLAYER_OVERRIDE)
            || sections.count("player")
#endif
            ) {
            fail("CONFIG_V2_LEGACY_SWITCH", "ConfigVersion=2 does not accept Randomizer.Enabled, Opponents.Enabled, or the Experimental section.");
            return result;
        }
        for (std::size_t index = 0; index < policy_seen.size(); ++index) {
            if (!policy_seen[index]) {
                fail("CONFIG_V2_POLICY_REQUIRED", "ConfigVersion=2 requires a policy for every supported mode.");
                return result;
            }
            if (!parse_policy_for_version(raw_policies[index], 2, parsed.mode_policies[index])) {
                fail("CONFIG_POLICY_INVALID", "V2 mode policies use 0=Stock, 1=T1, 2=T2, 3=T3, 4=Full, 5=Mixed, 6=Diverse.");
                return result;
            }
        }
        if (!duplicates_seen || !max_opponents_seen || !addons_seen || !logging_seen) {
            fail("CONFIG_V2_REQUIRED_SETTING", "ConfigVersion=2 requires Duplicates, MaxOpponents, Addons.Include, and Logging.Enabled.");
            return result;
        }
        parsed.quick_race = parsed.mode_policies[0];
        parsed.randomizer_enabled = std::any_of(parsed.mode_policies.begin(), parsed.mode_policies.end(),
            [](Policy policy) { return policy != Policy::Stock; });
        parsed.opponents_enabled = parsed.max_opponents != 3;
        parsed.experimental_extended_ai = parsed.max_opponents > kNativeAiMaximum;
    }
#if defined(RMOD3_G2_PLAYER_OVERRIDE)
    else if (config_version == 3) {
        if (randomizer_enabled_seen || opponents_enabled_seen || extended_ai_seen || sections.count("experimental")) {
            fail("CONFIG_V3_LEGACY_SWITCH", "ConfigVersion=3 does not accept Randomizer.Enabled, Opponents.Enabled, or the Experimental section.");
            return result;
        }
        for (std::size_t index = 0; index < policy_seen.size(); ++index) {
            if (!policy_seen[index]) {
                fail("CONFIG_V3_POLICY_REQUIRED", "ConfigVersion=3 requires a policy for every supported mode.");
                return result;
            }
            if (!parse_policy_for_version(raw_policies[index], 3, parsed.mode_policies[index])) {
                fail("CONFIG_POLICY_INVALID", "V3 mode policies use 0=Stock, 1=T1, 2=T2, 3=T3, 4=Full, 5=Mixed, 6=Diverse.");
                return result;
            }
        }
        if (!duplicates_seen || !max_opponents_seen || !addons_seen || !logging_seen) {
            fail("CONFIG_V3_REQUIRED_SETTING", "ConfigVersion=3 requires Duplicates, MaxOpponents, Addons.Include, and Logging.Enabled.");
            return result;
        }
        if (!player_mode_seen || !forced_player_car_seen || !player_random_policy_seen) {
            fail("CONFIG_V3_PLAYER_SETTING", "ConfigVersion=3 requires Player.Mode, Player.ForcedCarID, and Player.RandomPolicy.");
            return result;
        }
        parsed.quick_race = parsed.mode_policies[0];
        parsed.randomizer_enabled = std::any_of(parsed.mode_policies.begin(), parsed.mode_policies.end(),
            [](Policy policy) { return policy != Policy::Stock; });
        parsed.opponents_enabled = parsed.max_opponents != 3;
        parsed.experimental_extended_ai = parsed.max_opponents > kNativeAiMaximum;
    }
#endif
    result.accepted = true;
    result.config = parsed;
    result.diagnostics.push_back({Severity::Info, "CONFIG_ACCEPTED", "Configuration is valid; all required versioned policies and public runtime settings have been validated.", 0});
    return result;
}

struct RegisteredAddon {
    int physical_id = -1;
    int class_id = -1;
    bool current_process_registered = false;
    bool resources_verified = false;
    bool physics_verified = false;
    bool quick_race_eligible = false;
    std::uint32_t mode_mask = 0; // zero retains the original Quick Race-only ABI
};

struct Vehicle {
    int physical_id = -1;
    int class_id = -1; // 0=T1, 1=T2, 2=T3
    bool addon = false;
};

inline std::vector<Vehicle> eligible_vehicles(GameMode mode,
                                               std::uint8_t unlocked_reward_mask = 0,
                                               const std::vector<RegisteredAddon>& registered = {},
                                               AddonMode addon_mode = AddonMode::StockOnly) {
    std::vector<Vehicle> result;
    if (mode == GameMode::Practice || mode == GameMode::Unknown) return result;
    for (int id = 0; id <= 20; ++id) result.push_back({id, id <= 6 ? 0 : id <= 13 ? 1 : 2, false});
    // Invitation is authored around the ordinary/core T3 roster and must not
    // absorb bonus/progression T3 entries. Other proven dynamic owners retain
    // the native reward eligibility predicates.
    for (int id = 21; id <= 24 && mode != GameMode::Invitation; ++id) {
        const unsigned bit = static_cast<unsigned>(id - 21);
        if (unlocked_reward_mask & (1u << bit)) result.push_back({id, 2, false});
    }
    // No directory scan or manifest discovery. The caller may supply only IDs
    // proven registered/materializable in this game process.
    if (addon_mode == AddonMode::RegisteredOnly) for (const auto& addon : registered) {
        const bool eligible = addon.mode_mask ? (addon.mode_mask & (1u << static_cast<unsigned>(mode))) != 0 :
            (mode == GameMode::QuickRace && addon.quick_race_eligible);
        if (addon.physical_id < 26 || addon.class_id < 0 || addon.class_id > 2 ||
            !addon.current_process_registered || !addon.resources_verified ||
            !addon.physics_verified || !eligible || (mode == GameMode::Invitation && addon.class_id != 2)) continue;
        const auto duplicate = std::find_if(result.begin(), result.end(), [&](const Vehicle& v) {
            return v.physical_id == addon.physical_id;
        });
        if (duplicate == result.end()) result.push_back({addon.physical_id, addon.class_id, true});
    }
    return result;
}

struct ClassCycle {
    std::array<int, 3> order{{0, 1, 2}};
    unsigned size = 0;
    unsigned cursor = 0;
    unsigned consumed_mask = 0;

    template <typename Draw>
    bool begin(unsigned class_mask, Draw draw) {
        size = cursor = 0;
        consumed_mask = 0;
        for (int cls = 0; cls < 3; ++cls) if (class_mask & (1u << cls)) order[size++] = cls;
        for (unsigned i = size; i > 1; --i) {
            const int j = draw(static_cast<int>(i));
            if (j < 0 || static_cast<unsigned>(j) >= i) return false;
            std::swap(order[i - 1], order[static_cast<unsigned>(j)]);
        }
        return size > 0;
    }

    int next(unsigned active_mask) {
        if (!active_mask) return -1;
        for (unsigned scanned = 0; scanned < size; ++scanned) {
            const unsigned index = (cursor + scanned) % size;
            const unsigned bit = 1u << order[index];
            if ((active_mask & bit) && !(consumed_mask & bit)) {
                cursor = (index + 1) % size;
                consumed_mask |= bit;
                return order[index];
            }
        }
        consumed_mask = 0;
        for (unsigned scanned = 0; scanned < size; ++scanned) {
            const unsigned index = (cursor + scanned) % size;
            if (active_mask & (1u << order[index])) {
                cursor = (index + 1) % size;
                consumed_mask |= 1u << order[index];
                return order[index];
            }
        }
        return -1;
    }
};

struct Selection {
    SelectionKind kind = SelectionKind::Refused;
    int physical_id = -1;
    int class_id = -1;
    std::string reason;
};

enum class ClassSelectionKind { NativeStock, SelectedClass, Refused };

struct ClassSelection {
    ClassSelectionKind kind = ClassSelectionKind::Refused;
    int class_id = -1;
    std::string reason;
    bool duplicates_needed = false;
};

inline int policy_class(Policy policy) {
    if (policy == Policy::T1) return 0;
    if (policy == Policy::T2) return 1;
    if (policy == Policy::T3) return 2;
    return -1;
}

// Count the distinct physical IDs available to a Quick Race class policy
// before applying Duplicates=Never. The native start callback uses this only
// for the bounded extended Quick Race path, before participant setup begins.
inline unsigned quick_race_unique_capacity(Policy policy, int player_class,
                                          int player_physical_id,
                                          const std::vector<Vehicle>& eligible) {
    int fixed_class = policy_class(policy);
    if (policy == Policy::Stock) fixed_class = player_class;
    std::vector<int> ids;
    for (const auto& vehicle : eligible) {
        if (vehicle.physical_id < 0 || vehicle.class_id < 0 || vehicle.class_id > 2 ||
            (fixed_class >= 0 && vehicle.class_id != fixed_class)) continue;
        if (std::find(ids.begin(), ids.end(), vehicle.physical_id) == ids.end())
            ids.push_back(vehicle.physical_id);
    }
    const bool has_alternative = std::any_of(ids.begin(), ids.end(), [&](int id) {
        return id != player_physical_id;
    });
    if (has_alternative)
        ids.erase(std::remove(ids.begin(), ids.end(), player_physical_id), ids.end());
    return static_cast<unsigned>(ids.size());
}

// Select only the class at the native class-pool seam. The game remains the
// owner of physical CarID selection, participant allocation and DriverID.
// This shares the same eligibility/duplicate-first policy as choose_vehicle()
// without consuming an unused physical-ID draw in a class-only native hook.
template <typename Draw>
ClassSelection choose_class(Policy policy,
                            bool randomizer_enabled,
                            unsigned active_ai_count,
                            int player_class,
                            int player_physical_id,
                            const std::vector<Vehicle>& eligible,
                            const std::vector<int>& prior_ai_ids,
                            ClassCycle* diverse_cycle,
                            Draw draw,
                            bool duplicates_when_needed = true) {
    if (active_ai_count < 1 || active_ai_count > kMaximumAi)
        return {ClassSelectionKind::Refused, -1, "AI count is outside 1..7."};
    if (player_class < 0 || player_class > 2)
        return {ClassSelectionKind::Refused, -1, "Player class is not a registered T1/T2/T3 class."};
    if (policy != Policy::Stock && policy != Policy::Full && policy != Policy::T1 &&
        policy != Policy::T2 && policy != Policy::T3 && policy != Policy::Mixed &&
        policy != Policy::Diverse)
        return {ClassSelectionKind::Refused, -1, "Unknown randomizer policy."};
    if (!randomizer_enabled && active_ai_count <= kNativeAiMaximum)
        return {ClassSelectionKind::NativeStock, -1, "Randomizer is disabled; retain native Stock class selection."};
    if (!randomizer_enabled) policy = Policy::Stock;
    if (policy == Policy::Stock && active_ai_count <= kNativeAiMaximum)
        return {ClassSelectionKind::NativeStock, -1, "Stock policy retains the native class selector within its retail count."};

    const int fixed_class = policy == Policy::Stock ? player_class : policy_class(policy);
    std::vector<Vehicle> allowed;
    for (const auto& vehicle : eligible) {
        if ((fixed_class < 0 || vehicle.class_id == fixed_class) &&
            vehicle.class_id >= 0 && vehicle.class_id <= 2 && vehicle.physical_id >= 0)
            allowed.push_back(vehicle);
    }
    if (allowed.empty())
        return {ClassSelectionKind::Refused, -1, "No verified vehicles are eligible for this policy."};

    if (std::any_of(allowed.begin(), allowed.end(), [&](const Vehicle& v) {
            return v.physical_id != player_physical_id;
        })) {
        allowed.erase(std::remove_if(allowed.begin(), allowed.end(), [&](const Vehicle& v) {
            return v.physical_id == player_physical_id;
        }), allowed.end());
    }
    if (allowed.empty())
        return {ClassSelectionKind::Refused, -1, "The only eligible physical ID is the human vehicle."};

    std::vector<Vehicle> unique;
    for (const auto& vehicle : allowed) {
        if (std::find(prior_ai_ids.begin(), prior_ai_ids.end(), vehicle.physical_id) == prior_ai_ids.end())
            unique.push_back(vehicle);
    }
    if (unique.empty() && !duplicates_when_needed)
        return {ClassSelectionKind::Refused, -1, "Duplicates=Never and all eligible physical IDs have already been used."};
    const auto& pool = unique.empty() ? allowed : unique;
    unsigned class_mask = 0;
    for (const auto& vehicle : pool) class_mask |= 1u << vehicle.class_id;

    int selected_class = fixed_class;
    if (policy == Policy::Mixed) {
        std::array<int, 3> classes{};
        unsigned count = 0;
        for (int cls = 0; cls < 3; ++cls) if (class_mask & (1u << cls)) classes[count++] = cls;
        const int index = draw(static_cast<int>(count));
        if (!count || index < 0 || static_cast<unsigned>(index) >= count)
            return {ClassSelectionKind::Refused, -1, "Random source returned an invalid class draw."};
        selected_class = classes[static_cast<unsigned>(index)];
    } else if (policy == Policy::Diverse) {
        if (!diverse_cycle)
            return {ClassSelectionKind::Refused, -1, "Diverse class cycle is unavailable for this generation."};
        selected_class = diverse_cycle->next(class_mask);
        if (selected_class < 0)
            return {ClassSelectionKind::Refused, -1, "Diverse class cycle has no eligible class."};
    } else if (policy == Policy::Full) {
        const int index = draw(static_cast<int>(pool.size()));
        if (index < 0 || static_cast<unsigned>(index) >= pool.size())
            return {ClassSelectionKind::Refused, -1, "Random source returned an invalid vehicle-class draw."};
        selected_class = pool[static_cast<unsigned>(index)].class_id;
    }

    return {ClassSelectionKind::SelectedClass, selected_class,
            unique.empty() ? "Unique eligible IDs are exhausted; retain the selected class and let the native participant chooser repeat a physical CarID."
                           : "Selected a class from the remaining eligible physical IDs.",
            unique.empty()};
}

template <typename Draw>
Selection choose_vehicle(Policy policy,
                         bool randomizer_enabled,
                         unsigned active_ai_count,
                         int player_class,
                         int player_physical_id,
                         const std::vector<Vehicle>& eligible,
                         const std::vector<int>& prior_ai_ids,
                         ClassCycle* diverse_cycle,
                         Draw draw,
                         bool duplicates_when_needed = true) {
    if (active_ai_count < 1 || active_ai_count > kMaximumAi)
        return {SelectionKind::Refused, -1, -1, "AI count is outside 1..7."};
    if (player_class < 0 || player_class > 2)
        return {SelectionKind::Refused, -1, -1, "Player class is not a registered T1/T2/T3 class."};
    if (!randomizer_enabled && active_ai_count <= kNativeAiMaximum)
        return {SelectionKind::NativeStock, -1, -1, "Randomizer is disabled; retain native Stock selection."};
    if (!randomizer_enabled) policy = Policy::Stock;
    if (policy == Policy::Stock && active_ai_count <= kNativeAiMaximum)
        return {SelectionKind::NativeStock, -1, -1, "Stock policy retains the native chooser within its retail count."};

    int fixed_class = policy_class(policy);
    if (policy == Policy::Stock) fixed_class = player_class; // explicit stock-class-compatible extension
    std::vector<Vehicle> allowed;
    for (const auto& vehicle : eligible) {
        if (fixed_class < 0 || vehicle.class_id == fixed_class) allowed.push_back(vehicle);
    }
    if (allowed.empty()) return {SelectionKind::Refused, -1, -1, "No verified vehicles are eligible for this policy."};

    const bool has_non_player = std::any_of(allowed.begin(), allowed.end(), [&](const Vehicle& v) {
        return v.physical_id != player_physical_id;
    });
    if (has_non_player) {
        allowed.erase(std::remove_if(allowed.begin(), allowed.end(), [&](const Vehicle& v) {
            return v.physical_id == player_physical_id;
        }), allowed.end());
    }
    if (allowed.empty()) return {SelectionKind::Refused, -1, -1, "The only eligible physical ID is the human vehicle."};

    auto is_prior = [&](int id) {
        return std::find(prior_ai_ids.begin(), prior_ai_ids.end(), id) != prior_ai_ids.end();
    };
    std::vector<Vehicle> unique;
    for (const auto& vehicle : allowed) if (!is_prior(vehicle.physical_id)) unique.push_back(vehicle);
    const bool duplicates_needed = unique.empty();
    if (duplicates_needed && !duplicates_when_needed)
        return {SelectionKind::Refused, -1, -1, "Duplicates=Never and all eligible physical IDs have already been used."};
    const auto& pool = duplicates_needed ? allowed : unique;

    int selected_class = fixed_class;
    if (policy == Policy::Mixed) {
        unsigned class_mask = 0;
        for (const auto& vehicle : pool) class_mask |= 1u << vehicle.class_id;
        std::array<int, 3> classes{};
        unsigned count = 0;
        for (int cls = 0; cls < 3; ++cls) if (class_mask & (1u << cls)) classes[count++] = cls;
        const int class_pick = draw(static_cast<int>(count));
        if (!count || class_pick < 0 || static_cast<unsigned>(class_pick) >= count)
            return {SelectionKind::Refused, -1, -1, "Random source returned an invalid class draw."};
        selected_class = classes[static_cast<unsigned>(class_pick)];
    } else if (policy == Policy::Diverse) {
        if (!diverse_cycle) return {SelectionKind::Refused, -1, -1, "Diverse policy has no generation-scoped class cycle."};
        unsigned class_mask = 0;
        for (const auto& vehicle : pool) class_mask |= 1u << vehicle.class_id;
        if (!class_mask) for (const auto& vehicle : allowed) class_mask |= 1u << vehicle.class_id;
        selected_class = diverse_cycle->next(class_mask);
        if (selected_class < 0) return {SelectionKind::Refused, -1, -1, "Diverse class cycle has no eligible class."};
    } else if (policy == Policy::Full) {
        selected_class = -1;
    }

    std::vector<Vehicle> final_pool;
    for (const auto& vehicle : pool) {
        if (selected_class < 0 || vehicle.class_id == selected_class) final_pool.push_back(vehicle);
    }
    if (final_pool.empty() && duplicates_needed && selected_class >= 0) {
        // A Mixed/Diverse class can be exhausted before another class. Keep
        // unique identities first globally, then permit a repeated ID.
        for (const auto& vehicle : allowed) if (vehicle.class_id == selected_class) final_pool.push_back(vehicle);
    }
    if (final_pool.empty()) return {SelectionKind::Refused, -1, -1, "Selected class has no materializable vehicle."};
    const int index = draw(static_cast<int>(final_pool.size()));
    if (index < 0 || static_cast<unsigned>(index) >= final_pool.size())
        return {SelectionKind::Refused, -1, -1, "Random source returned an invalid vehicle draw."};
    const auto& chosen = final_pool[static_cast<unsigned>(index)];
    return {SelectionKind::SelectedId, chosen.physical_id, chosen.class_id,
            duplicates_needed ? "Unique eligible IDs are exhausted; a separate participant may reuse this CarID." : "Selected a unique eligible physical ID."};
}

struct ParticipantDecision {
    bool use_extension = false;
    bool allowed = false;
    unsigned humans = 0;
    unsigned ai = 0;
    unsigned total = 0;
    std::string reason;
};

// Physical stock IDs have sparse class boundaries in the retail registry.
// This helper is intentionally limited to the stock-only R-MOD1 release
// profile; addon IDs require an explicit process-registration record and are
// never inferred from a number range.
inline int stock_class_for_physical_id(int physical_id) {
    if (physical_id >= 0 && physical_id <= 6) return 0;
    if (physical_id >= 7 && physical_id <= 13) return 1;
    if (physical_id >= 14 && physical_id <= 24) return 2;
    return -1;
}

#if defined(RMOD3_G2_PLAYER_OVERRIDE)
enum class PlayerVehicleDecisionKind { PreserveNative, Selected, Refused };

struct PlayerVehicleDecision {
    PlayerVehicleDecisionKind kind = PlayerVehicleDecisionKind::Refused;
    int physical_id = -1;
    int class_id = -1;
    std::string reason;
};

template <typename Draw>
PlayerVehicleDecision choose_player_vehicle(const Config& config,
                                              int original_id,
                                              const std::vector<Vehicle>& installed_stock,
                                              Draw draw) {
    const int original_class = stock_class_for_physical_id(original_id);
    if (original_class < 0)
        return {PlayerVehicleDecisionKind::Refused, original_id, original_class,
                "Current Quick Race Car0 is not a verified stock physical ID."};
    if (config.config_version != 3 || config.player_vehicle_mode == PlayerVehicleMode::Stock)
        return {PlayerVehicleDecisionKind::PreserveNative, original_id, original_class,
                "Stock player mode preserves the native Quick Race selection."};

    auto valid_stock = [&](int id) {
        return std::find_if(installed_stock.begin(), installed_stock.end(), [id](const Vehicle& vehicle) {
            return vehicle.physical_id == id && !vehicle.addon &&
                vehicle.class_id == stock_class_for_physical_id(id);
        });
    };
    if (config.player_vehicle_mode == PlayerVehicleMode::Forced) {
        const auto found = valid_stock(config.forced_player_car_id);
        if (found == installed_stock.end())
            return {PlayerVehicleDecisionKind::Refused, original_id, original_class,
                    "Forced physical CarID is unavailable in the current stock Quick Race pool."};
        return {PlayerVehicleDecisionKind::Selected, found->physical_id, found->class_id,
                "Selected the configured stock physical CarID."};
    }

    const Policy policy = config.player_random_policy;
    if (policy == Policy::Stock)
        return {PlayerVehicleDecisionKind::PreserveNative, original_id, original_class,
                "RandomPolicy=Stock preserves the native player selection."};
    std::vector<Vehicle> pool;
    for (const auto& vehicle : installed_stock) {
        if (vehicle.physical_id < 0 || vehicle.physical_id > 24 || vehicle.addon ||
            stock_class_for_physical_id(vehicle.physical_id) != vehicle.class_id) continue;
        pool.push_back(vehicle);
    }
    if (pool.empty())
        return {PlayerVehicleDecisionKind::Refused, original_id, original_class,
                "No verified installed stock vehicle is available for player selection."};

    int selected_class = policy_class(policy);
    if (policy == Policy::Full) {
        selected_class = -1;
    } else if (policy == Policy::Mixed || policy == Policy::Diverse) {
        unsigned class_mask = 0;
        for (const auto& vehicle : pool) class_mask |= 1u << vehicle.class_id;
        if (policy == Policy::Mixed) {
            std::array<int, 3> classes{};
            unsigned count = 0;
            for (int cls = 0; cls < 3; ++cls)
                if (class_mask & (1u << cls)) classes[count++] = cls;
            const int pick = draw(static_cast<int>(count));
            if (!count || pick < 0 || static_cast<unsigned>(pick) >= count)
                return {PlayerVehicleDecisionKind::Refused, original_id, original_class,
                        "Random source returned an invalid mixed-class player draw."};
            selected_class = classes[static_cast<unsigned>(pick)];
        } else {
            ClassCycle cycle;
            if (!cycle.begin(class_mask, draw))
                return {PlayerVehicleDecisionKind::Refused, original_id, original_class,
                        "Diverse player class cycle could not be initialized."};
            selected_class = cycle.next(class_mask);
        }
    }

    std::vector<Vehicle> candidates;
    for (const auto& vehicle : pool)
        if (selected_class < 0 || vehicle.class_id == selected_class) candidates.push_back(vehicle);
    if (candidates.empty())
        return {PlayerVehicleDecisionKind::Refused, original_id, original_class,
                "The requested player policy has no available stock physical IDs."};
    const int pick = draw(static_cast<int>(candidates.size()));
    if (pick < 0 || static_cast<unsigned>(pick) >= candidates.size())
        return {PlayerVehicleDecisionKind::Refused, original_id, original_class,
                "Random source returned an invalid player vehicle draw."};
    const auto& selected = candidates[static_cast<unsigned>(pick)];
    return {PlayerVehicleDecisionKind::Selected, selected.physical_id, selected.class_id,
            "Selected one available stock physical CarID for this Vehicle Select entry."};
}

struct PreparedPlayerVehicle {
    bool ready = false;
    bool consumed = false;
    unsigned generation = 0;
    GameMode event_mode = GameMode::Unknown;
    int player_slot = -1;
    int original_id = -1;
    int physical_id = -1;
    int class_id = -1;
    PlayerVehicleMode mode_snapshot = PlayerVehicleMode::Stock;
    Config config_snapshot{};

    void clear() {
        ready = false;
        consumed = false;
        event_mode = GameMode::Unknown;
        player_slot = -1;
        original_id = physical_id = class_id = -1;
        mode_snapshot = PlayerVehicleMode::Stock;
        config_snapshot = Config{};
    }
};

template <typename Draw>
PlayerVehicleDecision prepare_player_vehicle(PreparedPlayerVehicle& prepared,
                                               const Config& snapshot,
                                               GameMode event_mode,
                                               int player_slot,
                                               int original_id,
                                               const std::vector<Vehicle>& installed_stock,
                                               Draw draw) {
    const unsigned next_generation = prepared.generation + 1u;
    prepared.clear();
    prepared.generation = next_generation;
    const auto decision = (event_mode == GameMode::QuickRace && player_slot == 0)
        ? choose_player_vehicle(snapshot, original_id, installed_stock, draw)
        : PlayerVehicleDecision{PlayerVehicleDecisionKind::PreserveNative, original_id,
                                stock_class_for_physical_id(original_id),
                                "Player override is limited to Quick Race player zero."};
    if (decision.kind != PlayerVehicleDecisionKind::Refused) {
        prepared.ready = true;
        prepared.event_mode = event_mode;
        prepared.player_slot = player_slot;
        prepared.original_id = original_id;
        prepared.physical_id = decision.physical_id;
        prepared.class_id = decision.class_id;
        prepared.mode_snapshot = snapshot.player_vehicle_mode;
        prepared.config_snapshot = snapshot;
    }
    return decision;
}

inline int consume_prepared_player_vehicle(PreparedPlayerVehicle& prepared,
                                           GameMode event_mode,
                                           int player_slot,
                                           int current_id) {
    if (!prepared.ready || prepared.event_mode != event_mode ||
        prepared.player_slot != player_slot) return current_id;
    if (prepared.mode_snapshot == PlayerVehicleMode::Stock) {
        prepared.consumed = true;
        return current_id;
    }
    if (prepared.physical_id < 0 || prepared.class_id != stock_class_for_physical_id(prepared.physical_id))
        return current_id;
    prepared.consumed = true;
    return prepared.physical_id;
}
#endif

struct QuickRaceTopology {
    bool quick_race = false;
    bool raw_split_screen = false;
    // These remain zero until the native Race object exists. The frontend
    // SplitScreen value is logged, but it is not treated as evidence that a
    // second human participant was actually materialized.
    unsigned humans = 0;
    unsigned num_cars = 0;
    unsigned ai = 0;
};

// FUN_0047B780 is the verified mode-2 setup owner and publishes selected
// count+1 as Race/NumCars. The raw frontend SplitScreen value is diagnostic
// only here. The effective human and AI counts are read from Race/NumPlayers
// and the participant PlayerType fields after native setup.
inline QuickRaceTopology derive_quick_race_topology(int mode_id,
                                                     unsigned selected_count,
                                                     bool raw_split_screen) {
    QuickRaceTopology topology;
    topology.quick_race = mode_id == 2;
    topology.raw_split_screen = raw_split_screen;
    if (!topology.quick_race || selected_count == 0 || selected_count > kMaximumAi)
        return topology;
    topology.num_cars = selected_count + 1u;
    return topology;
}

inline bool unique_ai_physical_ids(const std::vector<int>& ai_ids,
                                   const std::vector<int>& human_ids) {
    if (std::any_of(human_ids.begin(), human_ids.end(), [](int id) { return id < 0; })) return false;
    std::set<int> unique;
    for (const int id : ai_ids) {
        if (id < 0 || !unique.insert(id).second) return false;
        if (std::find(human_ids.begin(), human_ids.end(), id) != human_ids.end()) return false;
    }
    return true;
}

struct NativeParticipantRecord {
    int player_type = -1;
    int physical_id = -1;
    int class_id = -1;
};

struct NativeRosterSnapshot {
    unsigned num_cars = 0;
    unsigned num_players = 0;
    unsigned participants = 0;
    unsigned humans = 0;
    unsigned ai = 0;
    bool bounds_valid = false;
    bool slots_complete = false;
    bool valid_types = true;
    bool valid_identity = true;
    bool unique_ai_ids = true;
};

inline NativeRosterSnapshot analyze_native_roster(int native_num_cars,
                                                   int native_num_players,
                                                   const std::vector<NativeParticipantRecord>& slots) {
    NativeRosterSnapshot snapshot;
    if (native_num_cars < 1 || native_num_cars > static_cast<int>(kMaximumTotalCars) ||
        native_num_players < 1 || native_num_players > 2)
        return snapshot;
    snapshot.bounds_valid = true;
    snapshot.num_cars = static_cast<unsigned>(native_num_cars);
    snapshot.num_players = static_cast<unsigned>(native_num_players);
    snapshot.slots_complete = slots.size() == snapshot.num_cars;
    std::vector<int> ai_ids;
    std::vector<int> human_ids;
    for (const auto& slot : slots) {
        if (slot.player_type != 1 && slot.player_type != 2) {
            snapshot.valid_types = false;
            continue;
        }
        ++snapshot.participants;
        if (slot.physical_id < 0 || slot.physical_id > 24 || slot.class_id < 0 || slot.class_id > 2 ||
            stock_class_for_physical_id(slot.physical_id) != slot.class_id)
            snapshot.valid_identity = false;
        if (slot.player_type == 1) {
            ++snapshot.humans;
            human_ids.push_back(slot.physical_id);
        } else {
            ++snapshot.ai;
            ai_ids.push_back(slot.physical_id);
        }
    }
    snapshot.unique_ai_ids = unique_ai_physical_ids(ai_ids, human_ids);
    return snapshot;
}

inline bool native_roster_matches_topology(const NativeRosterSnapshot& roster,
                                           const QuickRaceTopology& topology) {
    return topology.quick_race && roster.bounds_valid && roster.slots_complete &&
        roster.num_cars == topology.num_cars && roster.num_players <= roster.num_cars &&
        roster.participants == roster.num_cars && roster.humans == roster.num_players &&
        roster.humans + roster.ai == roster.num_cars &&
        roster.valid_types && roster.valid_identity;
}

inline bool experimental_extended_roster_matches(const NativeRosterSnapshot& roster,
                                                   const ParticipantDecision& decision,
                                                   unsigned selected_ai_count) {
    const unsigned expected_total = selected_ai_count + 1u;
    return decision.use_extension && decision.allowed && selected_ai_count >= 4 &&
        selected_ai_count <= kMaximumAi && decision.total == expected_total &&
        roster.bounds_valid && roster.slots_complete && roster.num_cars == expected_total &&
        roster.num_players == 1 && roster.participants == expected_total && roster.humans == 1 &&
        roster.ai == selected_ai_count && roster.valid_types && roster.valid_identity;
}

inline ParticipantDecision plan_quick_race(int mode_id,
                                            unsigned selected_count,
                                            bool raw_split_screen,
                                            const Config& config) {
    const auto topology = derive_quick_race_topology(mode_id, selected_count, raw_split_screen);
    if (!topology.quick_race)
        return {false, true, 0, 0, 0,
                "Native mode passthrough; no Quick Race opponent extension applied."};
    if (selected_count < 1 || selected_count > kMaximumAi)
        return {false, false, topology.humans, topology.ai, topology.num_cars,
                "Selected count is outside the implemented One..Seven UI range."};
    if (topology.num_cars > kMaximumTotalCars || topology.ai > kMaximumAi)
        return {false, false, topology.humans, topology.ai, topology.num_cars,
                "Native participant bound would exceed Car0..Car7."};
    if (config.config_version == 2 && selected_count > config.max_opponents)
        return {false, false, topology.humans, topology.ai, topology.num_cars,
                "Selected count exceeds the ConfigVersion=2 MaxOpponents ceiling."};
    if (selected_count <= kNativeAiMaximum)
        return {false, true, topology.humans, topology.ai, topology.num_cars,
                "Native Quick Race selection; preserve the mode-2 setup topology."};
    if (!config.opponents_enabled)
        return {false, false, topology.humans, topology.ai, topology.num_cars,
                "Opponent extender is disabled; counts above three are not admitted."};
    if (selected_count > config.max_opponents)
        return {false, false, topology.humans, topology.ai, topology.num_cars,
                "Selected count exceeds configured MaxOpponents."};
    if (!config_allows_extended_ai(config))
        return {false, false, topology.humans, topology.ai, topology.num_cars,
                "Extended counts above three AI require Experimental.ExtendedAI=1."};
    return {true, true, topology.humans, topology.ai, topology.num_cars,
            "Experimental extended Quick Race admitted by mode/count/config; raw SplitScreen is diagnostic only until Race participants exist."};
}

struct StartGateEvaluation {
    ParticipantDecision decision;
    QuickRaceTopology topology;
    unsigned selected_count = 0;
};

// Shared decision path called by MRCanStartQuickRaceV1 and exercised by the
// native-core callback harness. Unknown/non-mode-2 frontend contexts are
// intentionally passed through without consulting the Quick Race count.
inline StartGateEvaluation evaluate_native_start_gate(int mode_id, int raw_count,
                                                       bool raw_split_screen,
                                                       const Config& config) {
    StartGateEvaluation result;
    if (mode_id != 2) {
        result.selected_count = 0;
        result.topology = derive_quick_race_topology(mode_id, 0, raw_split_screen);
        result.decision = plan_quick_race(mode_id, 0, raw_split_screen, config);
        return result;
    }
    result.selected_count = raw_count > 0 && raw_count <= static_cast<int>(kMaximumAi)
        ? static_cast<unsigned>(raw_count) : 0u;
    result.topology = derive_quick_race_topology(mode_id, result.selected_count, raw_split_screen);
    result.decision = plan_quick_race(mode_id, result.selected_count, raw_split_screen, config);
    return result;
}

inline ParticipantDecision enforce_quickrace_duplicate_capacity(
    ParticipantDecision decision, int mode_id, unsigned selected_count,
    bool selector_active, bool duplicates_when_needed, Policy policy,
    int player_class, int player_physical_id,
    const std::vector<Vehicle>& eligible) {
    if (!decision.allowed || !decision.use_extension || mode_id != 2 ||
        selected_count <= kNativeAiMaximum || !selector_active ||
        duplicates_when_needed) return decision;
    const unsigned capacity = quick_race_unique_capacity(
        policy, player_class, player_physical_id, eligible);
    if (selected_count <= capacity) return decision;
    decision.allowed = false;
    decision.reason = "Duplicates=Never cannot provide " + std::to_string(selected_count) +
        " unique Quick Race vehicles; only " + std::to_string(capacity) +
        " are eligible after the human-car exclusion.";
    return decision;
}

struct ImageIdentity {
    std::string disk_sha256;
    std::uint32_t disk_file_size = 0;
    std::uint16_t pe_machine = 0;
    std::uint32_t mapped_image_size = 0;
    std::uintptr_t mapped_base = 0;
    bool mapped_image_matches_disk = false;
};

inline bool rva_to_runtime_address(const ImageIdentity& image, std::uint32_t rva,
                                  std::size_t length, std::uintptr_t& address) {
    if (!image.mapped_base || !image.mapped_image_size || length == 0 ||
        static_cast<std::uint64_t>(rva) + length > image.mapped_image_size ||
        image.mapped_base > UINTPTR_MAX - rva) return false;
    address = image.mapped_base + rva;
    return true;
}

inline std::vector<Diagnostic> verify_image_identity(const ImageIdentity& image) {
    std::vector<Diagnostic> result;
    if (ascii_lower(image.disk_sha256) != kRetailSha256)
        result.push_back({Severity::Error, "EXECUTABLE_HASH_UNSUPPORTED", "Only the exact pristine retail SHA256 is supported.", 0});
    if (image.disk_file_size != kRetailFileSize)
        result.push_back({Severity::Error, "EXECUTABLE_SIZE_MISMATCH", "Retail executable size does not match the pinned build.", 0});
    if (image.pe_machine != kPe32MachineI386)
        result.push_back({Severity::Error, "EXECUTABLE_ARCH_UNSUPPORTED", "Process image must be 32-bit x86 PE.", 0});
    if (!image.mapped_base || !image.mapped_image_size || !image.mapped_image_matches_disk)
        result.push_back({Severity::Error, "MAPPED_IMAGE_UNVERIFIED", "Mapped process image/path/architecture has not been matched to the verified disk image.", 0});
    if (result.empty()) result.push_back({Severity::Info, "EXECUTABLE_VERIFIED", "Exact pristine retail file and mapped x86 process image verified.", 0});
    return result;
}

struct RegionPlan {
    std::string id;
    std::uint32_t size = 0;
    RegionPermission initial = RegionPermission::ReadWrite;
    RegionPermission final = RegionPermission::ReadOnly;
    bool allocated_before_entry = true;
};

struct PatchOperation {
    std::string id;
    std::string owner;
    std::string semantic;
    PatchTargetKind target_kind = PatchTargetKind::ImageRva;
    std::string region_id;
    std::uint32_t rva_or_offset = 0;
    std::vector<std::uint8_t> expected;
    std::vector<std::uint8_t> replacement;
    PatchPhase phase = PatchPhase::BeforeGameEntry;
    std::vector<std::string> depends_on;
    struct Relative32Fixup {
        std::uint32_t displacement_offset = 0;
        std::uint32_t instruction_end_offset = 0;
        PatchTargetKind target_kind = PatchTargetKind::ImageRva;
        std::string target_region_id;
        std::uint32_t target_rva_or_offset = 0;
    };
    std::vector<Relative32Fixup> relative32_fixups;
};

struct PatchBundle {
    std::string required_sha256 = kRetailSha256;
    std::uint32_t required_file_size = kRetailFileSize;
    std::uint16_t required_machine = kPe32MachineI386;
    std::vector<RegionPlan> regions;
    std::vector<PatchOperation> operations;
};

enum class InstallFeature { Randomizer, OpponentExtender };

struct FeatureOperationBinding {
    InstallFeature feature = InstallFeature::Randomizer;
    std::string role;
    std::string operation_id;
};

struct InstallablePatchPlan {
    PatchBundle patch_bundle;
    std::vector<InstallFeature> enabled_features;
    std::vector<FeatureOperationBinding> coverage;
};

inline const std::vector<std::string>& required_operation_roles(InstallFeature feature) {
    static const std::vector<std::string> randomizer{
        "shared_semantic_core", "quickrace_ai_selection"};
    static const std::vector<std::string> opponent_extender{
        "opponent_selector_ui", "participant_count_publication", "participant_setup"};
    return feature == InstallFeature::Randomizer ? randomizer : opponent_extender;
}

inline bool valid_install_feature(InstallFeature feature) {
    return feature == InstallFeature::Randomizer || feature == InstallFeature::OpponentExtender;
}

inline std::string_view feature_name(InstallFeature feature) {
    if (feature == InstallFeature::Randomizer) return "randomizer";
    if (feature == InstallFeature::OpponentExtender) return "opponent_extender";
    return "unknown";
}

inline std::vector<Diagnostic> validate_feature_operation_coverage(const InstallablePatchPlan& plan) {
    std::vector<Diagnostic> diagnostics;
    if (plan.enabled_features.empty())
        diagnostics.push_back({Severity::Error, "INSTALL_FEATURES_EMPTY", "An installable plan must enable Randomizer, Opponent Extender, or both.", 0});

    std::set<InstallFeature> enabled;
    for (const auto feature : plan.enabled_features) {
        if (!valid_install_feature(feature)) {
            diagnostics.push_back({Severity::Error, "INSTALL_FEATURE_UNKNOWN", "Installable plan contains an unknown feature value.", 0});
            continue;
        }
        if (!enabled.insert(feature).second)
            diagnostics.push_back({Severity::Error, "INSTALL_FEATURE_DUPLICATE", "Installable plan repeats an enabled feature.", 0});
    }

    std::map<std::string, const PatchOperation*> operation_by_id;
    for (const auto& operation : plan.patch_bundle.operations)
        operation_by_id.emplace(operation.id, &operation);
    std::set<std::pair<InstallFeature, std::string>> bound_roles;
    for (const auto& binding : plan.coverage) {
        if (!valid_install_feature(binding.feature)) {
            diagnostics.push_back({Severity::Error, "INSTALL_COVERAGE_FEATURE_UNKNOWN", "Coverage contains an unknown feature value.", 0});
            continue;
        }
        if (!enabled.count(binding.feature)) {
            diagnostics.push_back({Severity::Error, "INSTALL_COVERAGE_FEATURE_DISABLED", "Coverage references a feature that is not enabled: " + std::string(feature_name(binding.feature)), 0});
            continue;
        }
        const auto& roles = required_operation_roles(binding.feature);
        if (std::find(roles.begin(), roles.end(), binding.role) == roles.end())
            diagnostics.push_back({Severity::Error, "INSTALL_COVERAGE_ROLE_UNKNOWN", "Unknown operation role for " + std::string(feature_name(binding.feature)) + ": " + binding.role, 0});
        const auto operation = operation_by_id.find(binding.operation_id);
        if (binding.operation_id.empty() || operation == operation_by_id.end())
            diagnostics.push_back({Severity::Error, "INSTALL_COVERAGE_OPERATION_MISSING", "Feature role points to an absent native operation: " + binding.operation_id, 0});
        else if (operation->second->expected == operation->second->replacement)
            diagnostics.push_back({Severity::Error, "INSTALL_COVERAGE_OPERATION_NOOP", "A mandatory feature role cannot be satisfied by a no-op operation: " + binding.operation_id, 0});
        if (!bound_roles.emplace(binding.feature, binding.role).second)
            diagnostics.push_back({Severity::Error, "INSTALL_COVERAGE_ROLE_DUPLICATE", "Feature operation role is bound more than once: " + binding.role, 0});
    }

    for (const auto feature : enabled) {
        for (const auto& role : required_operation_roles(feature)) {
            if (!bound_roles.count({feature, role}))
                diagnostics.push_back({Severity::Error, "INSTALL_COVERAGE_ROLE_REQUIRED", "Installable " + std::string(feature_name(feature)) + " plan is missing required role: " + role, 0});
        }
    }
    if (!has_error(diagnostics))
        diagnostics.push_back({Severity::Info, "INSTALL_FEATURE_COVERAGE_PASS", "Every enabled feature is backed by its mandatory native operation roles.", 0});
    return diagnostics;
}

class ReadOnlyMemory {
public:
    virtual ~ReadOnlyMemory() = default;
    virtual bool read(PatchTargetKind kind, const std::string& region_id,
                      std::uint32_t address, std::size_t size,
                      std::vector<std::uint8_t>& output) const = 0;
};

struct RegionMapping {
    std::string id;
    std::uintptr_t base = 0;
};

struct MaterializedOperation {
    std::string id;
    std::uintptr_t address = 0;
    std::vector<std::uint8_t> bytes;
};

struct MaterializationOutcome {
    bool accepted = false;
    std::vector<MaterializedOperation> operations;
    std::vector<Diagnostic> diagnostics;
};

inline std::vector<Diagnostic> validate_patch_bundle(const ImageIdentity& image,
                                                       const PatchBundle& bundle,
                                                       const ReadOnlyMemory* memory = nullptr) {
    auto diagnostics = verify_image_identity(image);
    if (!diagnostics.empty() && diagnostics.front().severity == Severity::Error) return diagnostics;
    if (ascii_lower(bundle.required_sha256) != kRetailSha256 || bundle.required_file_size != kRetailFileSize ||
        bundle.required_machine != kPe32MachineI386) {
        return {{Severity::Error, "PATCH_PROFILE_MISMATCH", "Patch bundle does not target the pinned retail x86 build.", 0}};
    }
    std::map<std::string, const RegionPlan*> regions;
    for (const auto& region : bundle.regions) {
        if (region.id.empty() || !region.size || !region.allocated_before_entry ||
            region.initial != RegionPermission::ReadWrite ||
            (region.final != RegionPermission::ReadOnly && region.final != RegionPermission::ReadExecute))
            diagnostics.push_back({Severity::Error, "PATCH_REGION_INVALID", "Regions must be bounded, prepared before entry, written RW, then finalized RO or RX.", 0});
        if (!regions.emplace(region.id, &region).second)
            diagnostics.push_back({Severity::Error, "PATCH_REGION_DUPLICATE", "Allocated region ID appears more than once: " + region.id, 0});
    }

    std::set<std::string> operation_ids;
    for (const auto& operation : bundle.operations) {
        if (operation.id.empty() || operation.owner.empty() || operation.semantic.empty())
            diagnostics.push_back({Severity::Error, "PATCH_OPERATION_UNOWNED", "Every operation needs an ID, semantic owner, and purpose.", 0});
        if (!operation_ids.insert(operation.id).second)
            diagnostics.push_back({Severity::Error, "PATCH_OPERATION_DUPLICATE", "Operation ID appears more than once: " + operation.id, 0});
        if (operation.phase != PatchPhase::BeforeGameEntry)
            diagnostics.push_back({Severity::Error, "PATCH_PHASE_UNSUPPORTED", "All R-MOD1 operations must be installed before game entry.", 0});
        if (operation.expected.empty() || operation.expected.size() != operation.replacement.size())
            diagnostics.push_back({Severity::Error, "PATCH_BYTE_LENGTH", "Expected and replacement byte ranges must be non-empty and equal length.", 0});
        std::vector<std::pair<std::uint32_t, std::uint32_t>> fixup_ranges;
        for (const auto& fixup : operation.relative32_fixups) {
            const std::uint64_t displacement_end = static_cast<std::uint64_t>(fixup.displacement_offset) + 4;
            if (displacement_end > operation.replacement.size() ||
                fixup.instruction_end_offset > operation.replacement.size() ||
                fixup.instruction_end_offset < displacement_end) {
                diagnostics.push_back({Severity::Error, "PATCH_FIXUP_BOUNDS", "Relative32 fixup is outside its emitted instruction bytes: " + operation.id, 0});
            }
            for (const auto& existing : fixup_ranges) {
                if (fixup.displacement_offset < existing.second && existing.first < displacement_end)
                    diagnostics.push_back({Severity::Error, "PATCH_FIXUP_OVERLAP", "Relative32 fixups overlap inside " + operation.id, 0});
            }
            fixup_ranges.push_back({fixup.displacement_offset, static_cast<std::uint32_t>(displacement_end)});
            if (fixup.target_kind == PatchTargetKind::AllocatedRegion && !regions.count(fixup.target_region_id))
                diagnostics.push_back({Severity::Error, "PATCH_FIXUP_REGION_MISSING", "Relative32 fixup references an unknown target region: " + fixup.target_region_id, 0});
            if (fixup.target_kind == PatchTargetKind::AllocatedRegion) {
                const auto region = regions.find(fixup.target_region_id);
                if (region != regions.end() && fixup.target_rva_or_offset >= region->second->size)
                    diagnostics.push_back({Severity::Error, "PATCH_FIXUP_TARGET_BOUNDS", "Relative32 target exceeds its allocated region.", 0});
            } else if (fixup.target_rva_or_offset >= image.mapped_image_size) {
                diagnostics.push_back({Severity::Error, "PATCH_FIXUP_TARGET_BOUNDS", "Relative32 target RVA exceeds the mapped image.", 0});
            }
        }
        if (operation.target_kind == PatchTargetKind::ImageRva) {
            const std::uint64_t end = static_cast<std::uint64_t>(operation.rva_or_offset) + operation.replacement.size();
            if (end > image.mapped_image_size)
                diagnostics.push_back({Severity::Error, "PATCH_RVA_OUT_OF_IMAGE", "Image RVA range exceeds the verified mapped image.", 0});
            if (!operation.region_id.empty())
                diagnostics.push_back({Severity::Error, "PATCH_TARGET_AMBIGUOUS", "Image RVA operation must not name an allocated region.", 0});
        } else {
            auto region = regions.find(operation.region_id);
            if (region == regions.end())
                diagnostics.push_back({Severity::Error, "PATCH_REGION_MISSING", "Operation references an unknown allocated region: " + operation.region_id, 0});
            else if (static_cast<std::uint64_t>(operation.rva_or_offset) + operation.replacement.size() > region->second->size)
                diagnostics.push_back({Severity::Error, "PATCH_REGION_BOUNDS", "Operation exceeds its allocated region.", 0});
        }
    }
    for (const auto& operation : bundle.operations) {
        for (const auto& dependency : operation.depends_on) {
            if (!operation_ids.count(dependency))
                diagnostics.push_back({Severity::Error, "PATCH_DEPENDENCY_MISSING", operation.id + " depends on missing operation " + dependency, 0});
        }
    }
    std::map<std::string, unsigned> visit_state;
    std::map<std::string, const PatchOperation*> operation_by_id;
    for (const auto& operation : bundle.operations) operation_by_id[operation.id] = &operation;
    std::function<bool(const std::string&)> visit = [&](const std::string& id) {
        auto& state = visit_state[id];
        if (state == 1) return false;
        if (state == 2) return true;
        state = 1;
        const auto found = operation_by_id.find(id);
        if (found != operation_by_id.end()) {
            for (const auto& dependency : found->second->depends_on) {
                if (operation_by_id.count(dependency) && !visit(dependency)) return false;
            }
        }
        state = 2;
        return true;
    };
    for (const auto& operation : bundle.operations) {
        if (!visit(operation.id)) {
            diagnostics.push_back({Severity::Error, "PATCH_DEPENDENCY_CYCLE", "Patch operation dependencies contain a cycle.", 0});
            break;
        }
    }
    for (std::size_t i = 0; i < bundle.operations.size(); ++i) {
        const auto& left = bundle.operations[i];
        for (std::size_t j = i + 1; j < bundle.operations.size(); ++j) {
            const auto& right = bundle.operations[j];
            if (left.target_kind != right.target_kind) continue;
            if (left.target_kind == PatchTargetKind::AllocatedRegion && left.region_id != right.region_id) continue;
            const std::uint64_t left_end = static_cast<std::uint64_t>(left.rva_or_offset) + left.replacement.size();
            const std::uint64_t right_end = static_cast<std::uint64_t>(right.rva_or_offset) + right.replacement.size();
            if (left.rva_or_offset < right_end && right.rva_or_offset < left_end)
                diagnostics.push_back({Severity::Error, "PATCH_OVERLAP", left.id + " overlaps " + right.id + ".", 0});
        }
    }
    if (memory) {
        // This pass is deliberately read-only and validates every preimage
        // before an adapter may write any operation.
        for (const auto& operation : bundle.operations) {
            std::vector<std::uint8_t> actual;
            if (!memory->read(operation.target_kind, operation.region_id, operation.rva_or_offset,
                              operation.expected.size(), actual)) {
                diagnostics.push_back({Severity::Error, "PATCH_PREIMAGE_UNREADABLE", "Cannot read preimage for " + operation.id + ".", 0});
            } else if (actual != operation.expected) {
                diagnostics.push_back({Severity::Error, "PATCH_PREIMAGE_MISMATCH", "Expected original bytes differ for " + operation.id + ".", 0});
            }
        }
    }
    const bool has_error = std::any_of(diagnostics.begin(), diagnostics.end(), [](const Diagnostic& d) { return d.severity == Severity::Error; });
    if (!has_error) diagnostics.push_back({Severity::Info, "PATCH_BUNDLE_PREFLIGHT_PASS", "Image, regions, dependencies, ranges and all available preimages passed read-only preflight.", 0});
    return diagnostics;
}

inline std::vector<Diagnostic> validate_installable_patch_plan(
    const ImageIdentity& image, const InstallablePatchPlan& plan,
    const ReadOnlyMemory* memory = nullptr) {
    auto diagnostics = validate_feature_operation_coverage(plan);
    auto patch_diagnostics = validate_patch_bundle(image, plan.patch_bundle, memory);
    diagnostics.insert(diagnostics.end(), patch_diagnostics.begin(), patch_diagnostics.end());
    return diagnostics;
}

inline MaterializationOutcome materialize_patch_bundle(const ImageIdentity& image,
                                                        const PatchBundle& bundle,
                                                        const std::vector<RegionMapping>& mappings) {
    MaterializationOutcome result;
    result.diagnostics = validate_patch_bundle(image, bundle);
    if (has_error(result.diagnostics)) return result;

    std::map<std::string, std::uintptr_t> bases;
    for (const auto& mapping : mappings) {
        if (!bases.emplace(mapping.id, mapping.base).second)
            result.diagnostics.push_back({Severity::Error, "PATCH_REGION_MAPPING_DUPLICATE", "Allocated region mapping is duplicated: " + mapping.id, 0});
    }
    for (const auto& mapping : mappings) {
        const bool known = std::any_of(bundle.regions.begin(), bundle.regions.end(), [&](const RegionPlan& region) {
            return region.id == mapping.id;
        });
        if (!known)
            result.diagnostics.push_back({Severity::Error, "PATCH_REGION_MAPPING_UNKNOWN", "Runtime mapping is supplied for an undeclared region: " + mapping.id, 0});
    }
    const std::uint64_t image_begin = image.mapped_base;
    const std::uint64_t image_end = image_begin + image.mapped_image_size;
    for (const auto& region : bundle.regions) {
        const auto found = bases.find(region.id);
        if (found == bases.end() || !found->second) {
            result.diagnostics.push_back({Severity::Error, "PATCH_REGION_MAPPING_MISSING", "Runtime base is missing for allocated region " + region.id, 0});
            continue;
        }
        const std::uint64_t begin = found->second;
        const std::uint64_t end = begin + region.size;
        if ((begin & 0xfffu) != 0 || end > 0x100000000ull || (begin < image_end && image_begin < end))
            result.diagnostics.push_back({Severity::Error, "PATCH_REGION_MAPPING_INVALID", "Region mapping is unaligned, out of x86 address space, or overlaps the main image: " + region.id, 0});
    }
    for (std::size_t i = 0; i < bundle.regions.size(); ++i) {
        const auto left = bases.find(bundle.regions[i].id);
        if (left == bases.end()) continue;
        for (std::size_t j = i + 1; j < bundle.regions.size(); ++j) {
            const auto right = bases.find(bundle.regions[j].id);
            if (right == bases.end()) continue;
            const std::uint64_t left_begin = left->second;
            const std::uint64_t left_end = left_begin + bundle.regions[i].size;
            const std::uint64_t right_begin = right->second;
            const std::uint64_t right_end = right_begin + bundle.regions[j].size;
            if (left_begin < right_end && right_begin < left_end)
                result.diagnostics.push_back({Severity::Error, "PATCH_REGION_MAPPING_OVERLAP", "Allocated runtime regions overlap.", 0});
        }
    }
    if (has_error(result.diagnostics)) return result;

    auto resolve_target = [&](PatchTargetKind kind, const std::string& region_id,
                              std::uint32_t offset, std::uintptr_t& output) -> bool {
        if (kind == PatchTargetKind::ImageRva) {
            return rva_to_runtime_address(image, offset, 1, output);
        }
        const auto base = bases.find(region_id);
        if (base == bases.end() || base->second > UINTPTR_MAX - offset) return false;
        output = base->second + offset;
        return true;
    };

    for (const auto& operation : bundle.operations) {
        MaterializedOperation item;
        item.id = operation.id;
        if (!resolve_target(operation.target_kind, operation.region_id, operation.rva_or_offset, item.address)) {
            result.diagnostics.push_back({Severity::Error, "PATCH_TARGET_UNRESOLVED", "Could not resolve runtime target for " + operation.id, 0});
            result.operations.clear();
            return result;
        }
        item.bytes = operation.replacement;
        for (const auto& fixup : operation.relative32_fixups) {
            std::uintptr_t target = 0;
            if (!resolve_target(fixup.target_kind, fixup.target_region_id, fixup.target_rva_or_offset, target) ||
                item.address > UINTPTR_MAX - fixup.instruction_end_offset) {
                result.diagnostics.push_back({Severity::Error, "PATCH_FIXUP_UNRESOLVED", "Could not resolve branch target for " + operation.id, 0});
                result.operations.clear();
                return result;
            }
            const std::int64_t next_instruction = static_cast<std::int64_t>(item.address + fixup.instruction_end_offset);
            const std::int64_t delta = static_cast<std::int64_t>(target) - next_instruction;
            if (delta < INT32_MIN || delta > INT32_MAX) {
                result.diagnostics.push_back({Severity::Error, "PATCH_FIXUP_RANGE", "Relative branch target is outside signed 32-bit reach for " + operation.id, 0});
                result.operations.clear();
                return result;
            }
            const std::uint32_t encoded = static_cast<std::uint32_t>(static_cast<std::int32_t>(delta));
            for (unsigned byte = 0; byte < 4; ++byte)
                item.bytes[fixup.displacement_offset + byte] = static_cast<std::uint8_t>((encoded >> (byte * 8)) & 0xffu);
        }
        result.operations.push_back(std::move(item));
    }
    result.accepted = true;
    result.diagnostics.push_back({Severity::Info, "PATCH_OPERATIONS_MATERIALIZED", "All operation addresses and relative branches resolved; no process memory was written.", 0});
    return result;
}

inline MaterializationOutcome preflight_and_materialize_patch_bundle(
    const ImageIdentity& image, const PatchBundle& bundle,
    const ReadOnlyMemory& memory, const std::vector<RegionMapping>& mappings) {
    auto preflight = validate_patch_bundle(image, bundle, &memory);
    if (has_error(preflight)) return {false, {}, std::move(preflight)};
    auto materialized = materialize_patch_bundle(image, bundle, mappings);
    materialized.diagnostics.insert(materialized.diagnostics.begin(), preflight.begin(), preflight.end());
    return materialized;
}

inline MaterializationOutcome preflight_and_materialize_installable_patch_plan(
    const ImageIdentity& image, const InstallablePatchPlan& plan,
    const ReadOnlyMemory& memory, const std::vector<RegionMapping>& mappings) {
    MaterializationOutcome result;
    result.diagnostics = validate_installable_patch_plan(image, plan, &memory);
    if (has_error(result.diagnostics)) return result;
    auto materialized = materialize_patch_bundle(image, plan.patch_bundle, mappings);
    materialized.diagnostics.insert(materialized.diagnostics.begin(),
                                    result.diagnostics.begin(), result.diagnostics.end());
    return materialized;
}

inline bool has_error(const std::vector<Diagnostic>& diagnostics) {
    return std::any_of(diagnostics.begin(), diagnostics.end(), [](const Diagnostic& d) { return d.severity == Severity::Error; });
}

} // namespace rmod1
