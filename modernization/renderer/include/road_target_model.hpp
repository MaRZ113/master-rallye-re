#pragma once

#include <array>
#include <cstddef>
#include <cstdint>

namespace gfx2::road_target {

inline constexpr uint32_t FRANCE1_MARKER_COUNT = 448;
inline constexpr uint32_t NATIVE_MARKER_STRIDE = 0x48;
inline constexpr uint32_t NATIVE_POSITION_OFFSET = 0x38;
inline constexpr double HORIZONTAL_TIE_EPSILON = 0.0001;
inline constexpr double HEIGHT_EQUAL_EPSILON = 0.0001;

struct Vec3 {
    float x = 0;
    float y = 0;
    float z = 0;
};
static_assert(sizeof(Vec3) == 12, "Native RaceLine position is three packed float32 values");

struct LiveSnapshot {
    std::array<Vec3, FRANCE1_MARKER_COUNT> markers{};
    uint32_t count = 0;
    uint32_t stride = 0;
    uint32_t position_offset = 0;
    uint64_t race_generation = 0;
    uint64_t owner_lifetime = 0;
    uint64_t sequence = 0;
    uint64_t fingerprint = 0;
    // Native pointer values are retained only as generation-scoped identity
    // tokens. Consumers must never dereference these cached values.
    uint32_t native_route_object = 0;
    uint32_t native_position_begin = 0;
    uint32_t native_position_end = 0;
    uint32_t recovery_manager = 0;
    uint32_t native_thread_id = 0;
    bool source_native_live = false;
    bool exact_supported_course = false;
    bool capture_owner_current = false;
    bool available = false;
    const char* reason = "not_captured";
};

struct SnapshotCheck {
    bool accepted = false;
    const char* reason = "snapshot_unavailable";
};

struct Preview {
    bool found = false;
    bool route_candidate_valid = false;
    bool within_radius = false;
    bool height_ambiguous = false;
    uint32_t marker_ordinal = 0;
    uint32_t nearest_tie_count = 0;
    Vec3 marker{};
    double horizontal_distance = 0;
    double vertical_difference = 0; // marker Y minus camera Y
    double world_distance = 0;
    const char* reason = "not_selected";
};

SnapshotCheck validate_snapshot(const LiveSnapshot& snapshot,
                                uint64_t expected_race_generation,
                                uint64_t expected_owner_lifetime,
                                bool exact_supported_course) noexcept;

Preview nearest_marker(const LiveSnapshot& snapshot, Vec3 camera,
                       double horizontal_search_radius,
                       uint64_t expected_race_generation,
                       uint64_t expected_owner_lifetime,
                       bool exact_supported_course) noexcept;

uint64_t position_fingerprint(const Vec3* markers, size_t count) noexcept;

} // namespace gfx2::road_target
