#include "road_target_model.hpp"

#include <cmath>
#include <cstring>
#include <limits>

namespace gfx2::road_target {
namespace {

bool finite(Vec3 value) noexcept {
    return std::isfinite(value.x) && std::isfinite(value.y) && std::isfinite(value.z);
}

} // namespace

SnapshotCheck validate_snapshot(const LiveSnapshot& snapshot,
                                uint64_t expected_race_generation,
                                uint64_t expected_owner_lifetime,
                                bool exact_supported_course) noexcept {
    if (!snapshot.available) return {false, snapshot.reason ? snapshot.reason : "snapshot_unavailable"};
    if (!snapshot.source_native_live) return {false, "source_not_native_live_raceline"};
    if (!exact_supported_course || !snapshot.exact_supported_course)
        return {false, "unsupported_course"};
    if (!snapshot.capture_owner_current || !expected_owner_lifetime)
        return {false, "stale_or_unverified_race_owner"};
    if (!snapshot.race_generation || snapshot.race_generation != expected_race_generation)
        return {false, "race_generation_mismatch"};
    if (snapshot.owner_lifetime != expected_owner_lifetime)
        return {false, "race_owner_lifetime_mismatch"};
    if (snapshot.count != FRANCE1_MARKER_COUNT)
        return {false, "route_count_mismatch"};
    if (snapshot.stride != NATIVE_MARKER_STRIDE)
        return {false, "route_stride_mismatch"};
    if (snapshot.position_offset != NATIVE_POSITION_OFFSET)
        return {false, "route_position_offset_mismatch"};
    for (uint32_t i = 0; i < snapshot.count; ++i) {
        if (!finite(snapshot.markers[i])) return {false, "non_finite_live_marker"};
    }
    return {true, "validated_native_live_raceline"};
}

Preview nearest_marker(const LiveSnapshot& snapshot, Vec3 camera,
                       double horizontal_search_radius,
                       uint64_t expected_race_generation,
                       uint64_t expected_owner_lifetime,
                       bool exact_supported_course) noexcept {
    Preview result;
    if (!finite(camera)) {
        result.reason = "camera_position_non_finite";
        return result;
    }
    if (!std::isfinite(horizontal_search_radius) || horizontal_search_radius < 0) {
        result.reason = "invalid_preview_search_radius";
        return result;
    }
    const SnapshotCheck checked = validate_snapshot(snapshot, expected_race_generation,
                                                    expected_owner_lifetime,
                                                    exact_supported_course);
    if (!checked.accepted) {
        result.reason = checked.reason;
        return result;
    }

    double best_horizontal = std::numeric_limits<double>::infinity();
    double selected_y = 0;
    bool have_best = false;
    bool height_ambiguous = false;
    uint32_t tie_count = 0;
    uint32_t selected = 0;

    for (uint32_t ordinal = 0; ordinal < snapshot.count; ++ordinal) {
        const Vec3 marker = snapshot.markers[ordinal];
        const double dx = static_cast<double>(marker.x) - camera.x;
        const double dz = static_cast<double>(marker.z) - camera.z;
        const double horizontal_squared = dx * dx + dz * dz;
        const double horizontal = std::sqrt(horizontal_squared);
        if (horizontal < best_horizontal) {
            have_best = true;
            best_horizontal = horizontal;
        }
    }

    if (!have_best) {
        result.reason = "empty_live_route";
        return result;
    }

    bool selected_y_known = false;
    for (uint32_t ordinal = 0; ordinal < snapshot.count; ++ordinal) {
        const Vec3 marker = snapshot.markers[ordinal];
        const double dx = static_cast<double>(marker.x) - camera.x;
        const double dz = static_cast<double>(marker.z) - camera.z;
        const double horizontal = std::sqrt(dx * dx + dz * dz);
        if (std::abs(horizontal - best_horizontal) > HORIZONTAL_TIE_EPSILON) continue;
        ++tie_count;
        if (!selected_y_known) {
            selected = ordinal;
            selected_y = marker.y;
            selected_y_known = true;
        } else if (std::abs(static_cast<double>(marker.y) - selected_y) > HEIGHT_EQUAL_EPSILON) {
            height_ambiguous = true;
        }
    }

    result.found = true;
    result.marker_ordinal = selected;
    result.marker = snapshot.markers[selected];
    const double dx = static_cast<double>(result.marker.x) - camera.x;
    const double dz = static_cast<double>(result.marker.z) - camera.z;
    result.horizontal_distance = std::sqrt(dx * dx + dz * dz);
    result.vertical_difference = static_cast<double>(result.marker.y) - camera.y;
    result.world_distance = std::sqrt(result.horizontal_distance * result.horizontal_distance +
                                      result.vertical_difference * result.vertical_difference);
    result.within_radius = result.horizontal_distance <= horizontal_search_radius;
    result.height_ambiguous = height_ambiguous;
    result.nearest_tie_count = tie_count;
    result.route_candidate_valid = result.within_radius && !height_ambiguous;
    result.reason = height_ambiguous ? "height_separated_horizontal_overlap" :
                    !result.within_radius ? "outside_preview_search_radius" :
                    "route_candidate_only_physical_clearance_unverified";
    return result;
}

uint64_t position_fingerprint(const Vec3* markers, size_t count) noexcept {
    if (!markers && count) return 0;
    uint64_t hash = 14695981039346656037ull;
    auto byte = [&hash](uint8_t value) {
        hash ^= value;
        hash *= 1099511628211ull;
    };
    for (size_t i = 0; i < count; ++i) {
        const float values[3] = {markers[i].x, markers[i].y, markers[i].z};
        for (float value : values) {
            uint32_t bits = 0;
            std::memcpy(&bits, &value, sizeof(bits));
            byte(static_cast<uint8_t>(bits));
            byte(static_cast<uint8_t>(bits >> 8));
            byte(static_cast<uint8_t>(bits >> 16));
            byte(static_cast<uint8_t>(bits >> 24));
        }
    }
    return hash;
}

} // namespace gfx2::road_target
