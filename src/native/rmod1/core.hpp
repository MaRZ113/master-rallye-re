#pragma once

// R-MOD1 shared semantic core.  This header has no Win32, renderer, Vehicle
// SDK, filesystem, or process-memory dependencies.  The suspended launcher
// and any future proxy adapter must link this same implementation.

#include <algorithm>
#include <array>
#include <cctype>
#include <cstdint>
#include <functional>
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
enum class AddonMode { RegisteredOnly };
enum class SelectionKind { NativeStock, SelectedId, Refused };
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
    bool randomizer_enabled = false;
    Policy quick_race = Policy::Stock;
    bool duplicates_when_needed = true;
    bool opponents_enabled = false;
    unsigned max_opponents = 3;
    AddonMode addons = AddonMode::RegisteredOnly;
    bool logging_enabled = false;
};

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
    if (lowered == "true") { output = true; return true; }
    if (lowered == "false") { output = false; return true; }
    return false;
}

inline bool parse_policy(std::string_view value, Policy& output) {
    const auto lowered = ascii_lower(value);
    if (lowered == "stock") output = Policy::Stock;
    else if (lowered == "full") output = Policy::Full;
    else if (lowered == "t1") output = Policy::T1;
    else if (lowered == "t2") output = Policy::T2;
    else if (lowered == "t3") output = Policy::T3;
    else if (lowered == "mixed") output = Policy::Mixed;
    else if (lowered == "diverse") output = Policy::Diverse;
    else return false;
    return true;
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
    std::set<std::string> sections;
    std::map<std::string, std::set<std::string>> keys;
    std::string section;
    bool version_seen = false;
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
                static const std::set<std::string> allowed = {"general", "randomizer", "opponents", "addons", "logging"};
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
                    if (!parse_unsigned(value_view, version) || version != 1) {
                        fail("CONFIG_VERSION_UNSUPPORTED", "Only ConfigVersion=1 is supported.", line_number);
                        return result;
                    }
                    version_seen = true;
                } else if (section == "randomizer" && key == "enabled") {
                    if (!parse_bool(value, bool_value)) { fail("CONFIG_BOOL_INVALID", "Randomizer.Enabled must be true or false.", line_number); return result; }
                    parsed.randomizer_enabled = bool_value;
                } else if (section == "randomizer" && key == "quickrace") {
                    if (!parse_policy(value, parsed.quick_race)) { fail("CONFIG_POLICY_INVALID", "QuickRace must be Stock, Full, T1, T2, T3, Mixed, or Diverse.", line_number); return result; }
                } else if (section == "randomizer" && key == "duplicates") {
                    if (value != "whenneeded") { fail("CONFIG_DUPLICATES_INVALID", "Only Duplicates=WhenNeeded is supported.", line_number); return result; }
                    parsed.duplicates_when_needed = true;
                } else if (section == "opponents" && key == "enabled") {
                    if (!parse_bool(value, bool_value)) { fail("CONFIG_BOOL_INVALID", "Opponents.Enabled must be true or false.", line_number); return result; }
                    parsed.opponents_enabled = bool_value;
                } else if (section == "opponents" && key == "maxopponents") {
                    unsigned count = 0;
                    if (!parse_unsigned(value_view, count) || count < 1 || count > kMaximumAi) {
                        fail("CONFIG_OPPONENT_LIMIT", "MaxOpponents must be an integer from 1 through 7.", line_number);
                        return result;
                    }
                    parsed.max_opponents = count;
                } else if (section == "addons" && key == "include") {
                    if (value != "auto") { fail("CONFIG_ADDON_POLICY_INVALID", "Only Addons.Include=Auto is currently accepted; Auto means registered process entries only.", line_number); return result; }
                    parsed.addons = AddonMode::RegisteredOnly;
                } else if (section == "logging" && key == "enabled") {
                    if (!parse_bool(value, bool_value)) { fail("CONFIG_BOOL_INVALID", "Logging.Enabled must be true or false.", line_number); return result; }
                    parsed.logging_enabled = bool_value;
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
        fail("CONFIG_VERSION_REQUIRED", "A single [General] section with ConfigVersion=1 is required.");
        return result;
    }
    result.accepted = true;
    result.config = parsed;
    result.diagnostics.push_back({Severity::Info, "CONFIG_ACCEPTED", "Configuration is valid; omitted settings use safe defaults.", 0});
    return result;
}

struct RegisteredAddon {
    int physical_id = -1;
    int class_id = -1;
    bool current_process_registered = false;
    bool resources_verified = false;
    bool physics_verified = false;
    bool quick_race_eligible = false;
};

struct Vehicle {
    int physical_id = -1;
    int class_id = -1; // 0=T1, 1=T2, 2=T3
    bool addon = false;
};

inline std::vector<Vehicle> eligible_vehicles(GameMode mode,
                                               std::uint8_t unlocked_reward_mask = 0,
                                               const std::vector<RegisteredAddon>& registered = {}) {
    std::vector<Vehicle> result;
    if (mode != GameMode::QuickRace) return result; // non-Quick-Race owners remain native Stock
    for (int id = 0; id <= 20; ++id) result.push_back({id, id <= 6 ? 0 : id <= 13 ? 1 : 2, false});
    for (int id = 21; id <= 24; ++id) {
        const unsigned bit = static_cast<unsigned>(id - 21);
        if (unlocked_reward_mask & (1u << bit)) result.push_back({id, 2, false});
    }
    // No directory scan or manifest discovery. The caller may supply only IDs
    // proven registered/materializable in this game process.
    for (const auto& addon : registered) {
        if (addon.physical_id < 26 || addon.class_id < 0 || addon.class_id > 2 ||
            !addon.current_process_registered || !addon.resources_verified ||
            !addon.physics_verified || !addon.quick_race_eligible) continue;
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

inline int policy_class(Policy policy) {
    if (policy == Policy::T1) return 0;
    if (policy == Policy::T2) return 1;
    if (policy == Policy::T3) return 2;
    return -1;
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
                         Draw draw) {
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

inline ParticipantDecision plan_quick_race(unsigned humans,
                                            unsigned requested_ai,
                                            bool split_screen,
                                            unsigned track_id,
                                            unsigned player_car_id,
                                            int player_class,
                                            bool ghost_enabled,
                                            const std::vector<int>& ai_classes,
                                            const Config& config) {
    if (requested_ai < 1 || requested_ai > kMaximumAi)
        return {false, false, humans, requested_ai, humans + requested_ai, "Requested AI count must be 1..7."};
    if (humans != 1 || split_screen)
        return {false, requested_ai <= kNativeAiMaximum, humans, std::min(requested_ai, kNativeAiMaximum),
                humans + std::min(requested_ai, kNativeAiMaximum),
                "Modded count is single-player only; preserve native SplitScreen behavior."};
    if (!config.opponents_enabled && requested_ai > kNativeAiMaximum)
        return {false, false, humans, requested_ai, humans + requested_ai,
                "Opponent extension is disabled; counts above the retail maximum are not published."};
    if (config.opponents_enabled && requested_ai > config.max_opponents)
        return {false, false, humans, requested_ai, humans + requested_ai, "Requested count exceeds configured MaxOpponents."};
    if (requested_ai <= kNativeAiMaximum)
        return {false, true, humans, requested_ai, humans + requested_ai, "Native Quick Race count; no capacity extension needed."};
    if (requested_ai == 4 && track_id == 10 && player_car_id == 0 && player_class == 0 && !ghost_enabled &&
        ai_classes.size() == 4 && std::all_of(ai_classes.begin(), ai_classes.end(), [](int cls) { return cls == 0; }))
        return {true, true, humans, requested_ai, humans + requested_ai,
                "Exact five-car R-AI2 runtime profile: Track10, T1 ID0 human, four T1 AI, Ghost OFF."};
    return {false, false, humans, requested_ai, humans + requested_ai,
            "Extended count has no matching course/roster clearance qualification; fail closed before Start."};
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

inline bool has_error(const std::vector<Diagnostic>& diagnostics) {
    return std::any_of(diagnostics.begin(), diagnostics.end(), [](const Diagnostic& d) { return d.severity == Severity::Error; });
}

} // namespace rmod1
