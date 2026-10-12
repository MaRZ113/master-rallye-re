#pragma once

#include "road_target_model.hpp"
#include "physics_probe_model.hpp"
#include <array>
#include <cstdint>

namespace gfx2::road_teleport {

enum class State : uint8_t {
    Disabled,
    Idle,
    Armed,
    RecoveryEntered,
    DestinationOverridden,
    DestinationCommitted,
    NativeConsumed,
    Completed,
    Cancelled,
    Expired,
    Rejected,
    CommitMismatch,
    TimedOut
};

struct Request {
    State state = State::Disabled;
    uint64_t sequence = 0;
    uint64_t race_generation = 0;
    uint64_t owner_lifetime = 0;
    uint64_t route_sequence = 0;
    uint64_t route_fingerprint = 0;
    uint64_t armed_tick_ms = 0;
    uint64_t deadline_tick_ms = 0;
    uint64_t transaction_tick_ms = 0;
    uint32_t human_actor = 0;
    uint32_t human_controller = 0;
    uint32_t human_backing = 0;
    uint64_t human_identity_generation = 0;
    uint32_t reset_manager = 0;
    uint32_t recovery_countdown_array = 0;
    uint32_t route_object = 0;
    uint32_t marker_ordinal = UINT32_MAX;
    uint32_t participant_index = UINT32_MAX;
    uint32_t original_marker_ordinal = UINT32_MAX;
    uint32_t native_adjusted_ordinal = UINT32_MAX;
    uint32_t native_thread_id = 0;
    uint64_t active_consumer_calls = 0;
    uint32_t controller_backing = 0;
    road_target::Vec3 target{};
    road_target::Vec3 committed_translation{};
    road_target::Vec3 chassis_after{};
    std::array<uint32_t, 16> committed_matrix{};
    const char* reason = "not_requested";
    const char* owner_gate_reason = "not_evaluated";
    physics_probe::VehicleOwnerEvidence owner_evidence{};
    physics_probe::RecoveryManagerState selection_recovery{};
    const char* clear_writer = "none";
    bool route_candidate_only = true;
    bool input_overridden = false;
    bool native_selection_contract_verified = false;
    bool stock_adjustment_returned = false;
    bool matrix_committed = false;
    bool native_publication_seen = false;
    uint64_t native_transaction_candidate = 0;
    bool matrix_matches_target = false;
    bool native_consumed = false;
    bool chassis_matches_destination = false;
    bool native_clear_seen = false;
    bool settled_zero_seen = false;
};

struct ArmFacts {
    bool enabled = false;
    bool exact_build = false;
    bool freecam_active = false;
    bool pause_known = false;
    bool paused = false;
    bool race_certificate = false;
    bool single_human_car_race = false;
    bool unique_current_human_controller = false;
    bool no_active_recovery = false;
    bool native_selection_contract_verified = false;
    const char* owner_gate_reason = "not_evaluated";
    physics_probe::VehicleOwnerEvidence owner_evidence{};
    uint64_t race_generation = 0;
    uint64_t owner_lifetime = 0;
    uint64_t now_tick_ms = 0;
    uint32_t human_actor = 0;
    uint32_t human_controller = 0;
    uint32_t human_backing = 0;
    uint64_t human_identity_generation = 0;
    uint32_t arm_timeout_seconds = 60;
    double maximum_horizontal_distance = 20.0;
};

struct ArmResult {
    bool accepted = false;
    const char* reason = "not_requested";
    uint32_t marker_ordinal = UINT32_MAX;
    road_target::Vec3 target{};
};

struct NativeCallFacts {
    bool exact_build = false;
    bool race_context_current = false;
    bool unique_current_human_controller = false;
    bool no_active_recovery = false;
    bool native_selection_contract_verified = false;
    physics_probe::RecoveryManagerState recovery{};
    bool route_snapshot_current = false;
    uint64_t race_generation = 0;
    uint64_t owner_lifetime = 0;
    uint64_t route_fingerprint = 0;
    uint64_t now_tick_ms = 0;
    uint32_t human_actor = 0;
    uint32_t human_controller = 0;
    uint32_t human_backing = 0;
    uint64_t human_identity_generation = 0;
    uint32_t reset_manager = 0;
    uint32_t route_object = 0;
    uint32_t participant_index = UINT32_MAX;
    uint32_t route_count = 0;
    uint32_t native_thread_id = 0;
};

struct SelectionResult {
    bool changed = false;
    const char* reason = "no_armed_request";
    uint32_t original_ordinal = UINT32_MAX;
    uint32_t selected_ordinal = UINT32_MAX;
};

void initialize(Request& request, bool enabled) noexcept;
ArmResult arm(Request& request, uint64_t sequence, const ArmFacts& facts,
              const road_target::LiveSnapshot& snapshot,
              const road_target::Preview& selected) noexcept;
SelectionResult select_native_destination(Request& request,
                                          const NativeCallFacts& facts,
                                          uint32_t& marker_argument) noexcept;
bool commit_matrix(Request& request, uint32_t reset_manager,
                   uint32_t participant_index,
                   const std::array<uint32_t, 16>& matrix,
                   double horizontal_tolerance = 0.25) noexcept;
bool observe_native_adjustment(Request& request,
                               uint32_t adjusted_marker_ordinal) noexcept;
bool observe_native_consumption(Request& request, uint32_t backing,
                                const std::array<uint32_t, 16>& matrix,
                                road_target::Vec3 chassis_after,
                                bool active_flag,
                                uint64_t active_consumer_calls,
                                double horizontal_tolerance = 0.25) noexcept;
bool observe_clear(Request& request, uint32_t backing, uint32_t store_va,
                   uint8_t flag_before, uint8_t native_value) noexcept;
bool observe_settled_zero(Request& request, uint32_t backing,
                          uint8_t flag_value) noexcept;
void cancel(Request& request, const char* reason) noexcept;
void invalidate_generation(Request& request, uint64_t race_generation,
                           uint64_t owner_lifetime) noexcept;
bool expire(Request& request, uint64_t now_tick_ms,
            uint32_t transaction_timeout_ms = 5000) noexcept;
const char* state_name(State state) noexcept;

} // namespace gfx2::road_teleport
