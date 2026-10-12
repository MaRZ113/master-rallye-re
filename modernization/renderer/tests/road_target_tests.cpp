#include "road_target_model.hpp"

#include <cmath>
#include <cstdint>
#include <cstring>
#include <limits>

#define CHECK(condition) do { if (!(condition)) return __LINE__; } while (0)

using namespace gfx2::road_target;

static LiveSnapshot valid_snapshot() {
    LiveSnapshot snapshot{};
    snapshot.count = FRANCE1_MARKER_COUNT;
    snapshot.stride = NATIVE_MARKER_STRIDE;
    snapshot.position_offset = NATIVE_POSITION_OFFSET;
    snapshot.race_generation = 7;
    snapshot.owner_lifetime = 11;
    snapshot.sequence = 1;
    snapshot.source_native_live = true;
    snapshot.exact_supported_course = true;
    snapshot.capture_owner_current = true;
    snapshot.available = true;
    snapshot.reason = "native_live_raceline_snapshot";
    for (uint32_t i = 0; i < snapshot.count; ++i)
        snapshot.markers[i] = {1000.0f + static_cast<float>(i) * 20.0f, 10.0f, 2000.0f};
    return snapshot;
}

int main() {
    auto snapshot = valid_snapshot();
    CHECK(validate_snapshot(snapshot, 7, 11, true).accepted);

    auto selected = nearest_marker(snapshot, snapshot.markers[17], 60.0, 7, 11, true);
    CHECK(selected.found && selected.route_candidate_valid);
    CHECK(selected.marker_ordinal == 17 && selected.horizontal_distance == 0.0);
    CHECK(selected.reason && std::strcmp(selected.reason,
          "route_candidate_only_physical_clearance_unverified") == 0);

    selected = nearest_marker(snapshot, {1000.0f + 20.0f * 18.4f, 30.0f, 2000.0f},
                              60.0, 7, 11, true);
    CHECK(selected.found && selected.marker_ordinal == 18);

    // Ranking is horizontal XZ; camera altitude remains separate diagnostic data.
    selected = nearest_marker(snapshot, {snapshot.markers[20].x, 500.0f,
                                         snapshot.markers[20].z}, 0.0, 7, 11, true);
    CHECK(selected.found && selected.route_candidate_valid);
    CHECK(selected.marker_ordinal == 20);
    CHECK(selected.vertical_difference == -490.0);
    CHECK(selected.world_distance == 490.0);

    const float route_end = snapshot.markers[snapshot.count - 1].x;
    selected = nearest_marker(snapshot, {route_end + 60.0f,
                                         snapshot.markers[20].y,
                                         snapshot.markers[20].z}, 60.0, 7, 11, true);
    CHECK(selected.found && selected.within_radius && selected.route_candidate_valid);
    selected = nearest_marker(snapshot, {route_end + 60.01f,
                                         snapshot.markers[20].y,
                                         snapshot.markers[20].z}, 60.0, 7, 11, true);
    CHECK(selected.found && !selected.within_radius && !selected.route_candidate_valid);
    CHECK(std::strcmp(selected.reason, "outside_preview_search_radius") == 0);

    auto invalid = snapshot;
    invalid.count = 0;
    CHECK(!validate_snapshot(invalid, 7, 11, true).accepted);
    invalid = snapshot;
    invalid.stride = 0x40;
    CHECK(!validate_snapshot(invalid, 7, 11, true).accepted);
    invalid = snapshot;
    invalid.position_offset = 0x34;
    CHECK(!validate_snapshot(invalid, 7, 11, true).accepted);
    invalid = snapshot;
    invalid.markers[19].x = std::numeric_limits<float>::quiet_NaN();
    CHECK(!validate_snapshot(invalid, 7, 11, true).accepted);
    invalid.markers[19].x = std::numeric_limits<float>::infinity();
    CHECK(!validate_snapshot(invalid, 7, 11, true).accepted);
    selected = nearest_marker(invalid, {0, 0, 0}, 60.0, 7, 11, true);
    CHECK(!selected.found && std::strcmp(selected.reason, "non_finite_live_marker") == 0);

    invalid = snapshot;
    invalid.markers[4] = invalid.markers[3];
    selected = nearest_marker(invalid, invalid.markers[3], 1.0, 7, 11, true);
    CHECK(selected.found && selected.marker_ordinal == 3 && selected.nearest_tie_count == 2);
    CHECK(!selected.height_ambiguous && selected.route_candidate_valid);

    invalid = snapshot;
    invalid.markers[6] = invalid.markers[5];
    invalid.markers[6].y += 25.0f;
    selected = nearest_marker(invalid, invalid.markers[5], 1.0, 7, 11, true);
    CHECK(selected.found && selected.marker_ordinal == 5 && selected.nearest_tie_count == 2);
    CHECK(selected.height_ambiguous && !selected.route_candidate_valid);
    CHECK(std::strcmp(selected.reason, "height_separated_horizontal_overlap") == 0);

    invalid = snapshot;
    invalid.markers[9] = {10.0f, 5.0f, 0.0f};
    invalid.markers[10] = {-10.0f, 5.0f, 0.0f};
    selected = nearest_marker(invalid, {0.0f, 5.0f, 0.0f}, 10.0, 7, 11, true);
    CHECK(selected.found && selected.marker_ordinal == 9 && selected.nearest_tie_count == 2);

    invalid = snapshot;
    invalid.markers[0] = {1.0e30f, 2.0e30f, -1.0e30f};
    selected = nearest_marker(invalid, {1.0e30f, 2.0e30f, -1.0e30f}, 0.0, 7, 11, true);
    CHECK(selected.found && selected.marker_ordinal == 0 && selected.world_distance == 0.0);
    selected = nearest_marker(snapshot, {std::numeric_limits<float>::infinity(), 0, 0},
                              60.0, 7, 11, true);
    CHECK(!selected.found && std::strcmp(selected.reason, "camera_position_non_finite") == 0);
    selected = nearest_marker(snapshot, {0, 0, 0},
                              std::numeric_limits<double>::quiet_NaN(), 7, 11, true);
    CHECK(!selected.found && std::strcmp(selected.reason, "invalid_preview_search_radius") == 0);

    CHECK(!validate_snapshot(snapshot, 8, 11, true).accepted); // restart generation
    CHECK(std::strcmp(validate_snapshot(snapshot, 8, 11, true).reason,
                       "race_generation_mismatch") == 0);
    CHECK(!validate_snapshot(snapshot, 7, 12, true).accepted); // owner reuse
    CHECK(!validate_snapshot(snapshot, 7, 11, false).accepted); // unsupported course
    invalid = snapshot;
    invalid.source_native_live = false;
    CHECK(std::strcmp(validate_snapshot(invalid, 7, 11, true).reason,
                       "source_not_native_live_raceline") == 0); // no XML fallback
    invalid = snapshot;
    invalid.capture_owner_current = false;
    CHECK(std::strcmp(validate_snapshot(invalid, 7, 11, true).reason,
                       "stale_or_unverified_race_owner") == 0);

    const uint64_t first_fingerprint = position_fingerprint(snapshot.markers.data(), snapshot.count);
    CHECK(first_fingerprint != 0);
    snapshot.markers[0].z += 0.25f;
    CHECK(position_fingerprint(snapshot.markers.data(), snapshot.count) != first_fingerprint);
    return 0;
}
