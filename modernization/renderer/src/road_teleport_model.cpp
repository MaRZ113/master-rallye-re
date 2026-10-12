#include "road_teleport_model.hpp"
#include <cmath>
#include <cstring>

namespace gfx2::road_teleport {
namespace {
bool active_state(State state) noexcept {
    return state == State::Armed || state == State::RecoveryEntered ||
        state == State::DestinationOverridden || state == State::DestinationCommitted ||
        state == State::NativeConsumed;
}
bool finite(road_target::Vec3 value) noexcept {
    return std::isfinite(value.x) && std::isfinite(value.y) && std::isfinite(value.z);
}
road_target::Vec3 translation(const std::array<uint32_t, 16>& matrix) noexcept {
    road_target::Vec3 result{};
    std::memcpy(&result.x, &matrix[12], sizeof(float));
    std::memcpy(&result.y, &matrix[13], sizeof(float));
    std::memcpy(&result.z, &matrix[14], sizeof(float));
    return result;
}
bool same_matrix(const std::array<uint32_t, 16>& left,
                 const std::array<uint32_t, 16>& right) noexcept {
    return std::memcmp(left.data(), right.data(), sizeof(left)) == 0;
}
bool close_horizontal(road_target::Vec3 left, road_target::Vec3 right,
                      double tolerance) noexcept {
    return std::isfinite(tolerance) && tolerance >= 0 && finite(left) && finite(right) &&
        std::abs(double(left.x) - right.x) <= tolerance &&
        std::abs(double(left.z) - right.z) <= tolerance;
}
}

void initialize(Request& request, bool enabled) noexcept {
    request = Request{};
    request.state = enabled ? State::Idle : State::Disabled;
    request.reason = enabled ? "idle" : "disabled_by_config";
}

ArmResult arm(Request& request, uint64_t sequence, const ArmFacts& facts,
              const road_target::LiveSnapshot& snapshot,
              const road_target::Preview& selected) noexcept {
    const auto owner_decision = physics_probe::evaluate_vehicle_owner(facts.owner_evidence);
    auto reject = [&](const char* reason) {
        if (!active_state(request.state)) {
            request.state = State::Rejected;
            request.reason = reason;
            request.owner_gate_reason = owner_decision.reason;
            request.owner_evidence = facts.owner_evidence;
        }
        return ArmResult{false, reason, UINT32_MAX, {}};
    };
    if (!facts.enabled || request.state == State::Disabled)
        return reject("disabled_by_config");
    if (active_state(request.state)) return {false, "request_already_active", request.marker_ordinal, request.target};
    if (!facts.exact_build) return reject("exact_retail_build_required");
    if (!facts.freecam_active) return reject("freecam_inactive");
    if (!facts.pause_known || !facts.paused) return reject("verified_pause_required");
    if (!facts.race_certificate || !facts.race_generation || !facts.owner_lifetime)
        return reject("live_france1_race_certificate_required");
    if (!facts.single_human_car_race) return reject("single_human_car_race_required");
    if (!facts.unique_current_human_controller || !owner_decision.accepted || !facts.human_actor ||
        !facts.human_controller || !facts.human_backing ||
        !facts.human_identity_generation)
        return reject("unique_current_human_controller_required");
    if (!facts.no_active_recovery) return reject("native_recovery_already_active");
    if (!facts.native_selection_contract_verified) return reject("native_single_participant_contract_unverified");
    if (facts.human_actor != facts.owner_evidence.physical_actor ||
        facts.race_generation != facts.owner_evidence.race_generation ||
        facts.owner_lifetime != facts.owner_evidence.owner_lifetime ||
        facts.human_controller != facts.owner_evidence.controller ||
        facts.human_backing != facts.owner_evidence.backing ||
        facts.human_identity_generation != facts.owner_evidence.track_generation)
        return reject("owner_evidence_request_identity_mismatch");
    if (!sequence) return reject("request_sequence_unavailable");
    if (facts.arm_timeout_seconds < 1 || facts.arm_timeout_seconds > 300)
        return reject("arm_timeout_out_of_range");
    if (!std::isfinite(facts.maximum_horizontal_distance) ||
        facts.maximum_horizontal_distance <= 0 || facts.maximum_horizontal_distance > 60.0)
        return reject("road_target_radius_out_of_range");
    const auto snapshot_check = road_target::validate_snapshot(
        snapshot, facts.race_generation, facts.owner_lifetime, true);
    if (!snapshot_check.accepted) return reject(snapshot_check.reason);
    if (!snapshot.native_route_object || !snapshot.native_position_begin ||
        !snapshot.native_position_end || !snapshot.recovery_manager)
        return reject("native_recovery_identity_unavailable");
    if (snapshot.recovery_manager != facts.owner_evidence.recovery.manager)
        return reject("native_recovery_manager_identity_mismatch");
    if (!selected.found || !selected.route_candidate_valid || !selected.within_radius ||
        selected.height_ambiguous || selected.marker_ordinal >= snapshot.count)
        return reject(selected.reason ? selected.reason : "no_valid_live_road_marker");
    if (!finite(selected.marker) ||
        std::memcmp(&selected.marker, &snapshot.markers[selected.marker_ordinal],
                    sizeof(selected.marker)) != 0)
        return reject("selected_marker_snapshot_mismatch");
    if (selected.horizontal_distance > facts.maximum_horizontal_distance)
        return reject("selected_marker_exceeds_teleport_radius");
    if (snapshot.count != road_target::FRANCE1_MARKER_COUNT ||
        snapshot.stride != road_target::NATIVE_MARKER_STRIDE ||
        snapshot.position_offset != road_target::NATIVE_POSITION_OFFSET)
        return reject("unsupported_live_route_layout");
    if (facts.now_tick_ms > UINT64_MAX - uint64_t(facts.arm_timeout_seconds) * 1000u)
        return reject("arm_deadline_overflow");

    const uint64_t next_sequence = sequence;
    request = Request{};
    request.state = State::Armed;
    request.sequence = next_sequence;
    request.race_generation = facts.race_generation;
    request.owner_lifetime = facts.owner_lifetime;
    request.route_sequence = snapshot.sequence;
    request.route_fingerprint = snapshot.fingerprint;
    request.armed_tick_ms = facts.now_tick_ms;
    request.deadline_tick_ms = facts.now_tick_ms + uint64_t(facts.arm_timeout_seconds) * 1000u;
    request.human_actor = facts.human_actor;
    request.human_controller = facts.human_controller;
    request.human_backing = facts.human_backing;
    request.human_identity_generation = facts.human_identity_generation;
    request.reset_manager = snapshot.recovery_manager;
    request.recovery_countdown_array = facts.owner_evidence.recovery.countdown_array;
    request.native_selection_contract_verified = facts.native_selection_contract_verified;
    request.route_object = snapshot.native_route_object;
    request.marker_ordinal = selected.marker_ordinal;
    request.original_marker_ordinal = UINT32_MAX;
    request.native_thread_id = snapshot.native_thread_id;
    request.participant_index = 0;
    request.target = selected.marker;
    request.reason = "road_target_validated_and_armed";
    request.owner_gate_reason = owner_decision.reason;
    request.owner_evidence = facts.owner_evidence;
    return {true, request.reason, request.marker_ordinal, request.target};
}

SelectionResult select_native_destination(Request& request,
                                          const NativeCallFacts& facts,
                                          uint32_t& marker_argument) noexcept {
    const uint32_t original = marker_argument;
    if (request.state != State::Armed)
        return {false, "no_armed_request", original, original};
    request.selection_recovery = facts.recovery;
    request.state = State::RecoveryEntered;
    request.reason = "native_recovery_entered";
    auto reject = [&](const char* why) {
        request.state = State::Cancelled;
        request.reason = why;
        return SelectionResult{false, why, original, original};
    };
    if (facts.now_tick_ms >= request.deadline_tick_ms) {
        request.state = State::Expired;
        request.reason = "armed_request_expired_before_native_recovery";
        return {false, request.reason, original, original};
    }
    if (!facts.exact_build) return reject("native_exact_build_check_failed");
    if (!facts.race_context_current || facts.race_generation != request.race_generation ||
        facts.owner_lifetime != request.owner_lifetime || facts.human_actor != request.human_actor)
        return reject("race_or_human_identity_changed_before_recovery");
    if (!facts.unique_current_human_controller ||
        facts.human_actor != request.human_actor ||
        facts.human_controller != request.human_controller ||
        facts.human_backing != request.human_backing ||
        facts.human_identity_generation != request.human_identity_generation)
        return reject("current_human_controller_identity_changed");
    const auto recovery = physics_probe::evaluate_recovery_manager(facts.recovery, physics_probe::RecoveryPhase::NativeSelection);
    if (!recovery.accepted) return reject(recovery.reason);
    if (!facts.no_active_recovery) return reject("conflicting_native_recovery_active");
    if (!request.native_selection_contract_verified || !facts.native_selection_contract_verified)
        return reject("native_single_participant_contract_unverified");
    if (facts.recovery.manager != request.reset_manager ||
        facts.recovery.countdown_array != request.recovery_countdown_array)
        return reject("native_recovery_storage_replaced");
    if (!facts.route_snapshot_current || facts.route_fingerprint != request.route_fingerprint)
        return reject("live_route_identity_or_fingerprint_changed");
    if (facts.reset_manager != request.reset_manager || facts.route_object != request.route_object)
        return reject("native_recovery_owner_changed");
    if (facts.participant_index != request.participant_index)
        return reject("native_participant_is_not_the_single_human");
    if (facts.route_count != road_target::FRANCE1_MARKER_COUNT ||
        request.marker_ordinal >= facts.route_count || original >= facts.route_count)
        return reject("requested_marker_outside_native_route");
    if (!facts.native_thread_id || facts.native_thread_id != request.native_thread_id)
        return reject("native_reset_thread_changed");

    request.original_marker_ordinal = original;
    marker_argument = request.marker_ordinal;
    request.participant_index = facts.participant_index;
    request.input_overridden = true;
    request.transaction_tick_ms = facts.now_tick_ms;
    request.state = State::DestinationOverridden;
    request.reason = "native_selection_argument_overridden_stock_adjustment_retained";
    return {true, request.reason, original, marker_argument};
}

bool commit_matrix(Request& request, uint32_t reset_manager,
                   uint32_t participant_index,
                   const std::array<uint32_t, 16>& matrix,
                   double horizontal_tolerance) noexcept {
    if (request.state != State::DestinationOverridden || !request.input_overridden ||
        !request.stock_adjustment_returned ||
        request.native_adjusted_ordinal != request.marker_ordinal ||
        reset_manager != request.reset_manager || participant_index != request.participant_index)
        return false;
    const road_target::Vec3 position = translation(matrix);
    request.committed_matrix = matrix;
    request.committed_translation = position;
    request.matrix_committed = true;
    request.matrix_matches_target = finite(position) &&
        close_horizontal(position, request.target, horizontal_tolerance);
    if (request.matrix_matches_target) {
        request.state = State::DestinationCommitted;
        request.reason = "stock_matrix_committed_at_selected_route_position";
    } else {
        request.state = State::CommitMismatch;
        request.reason = "stock_matrix_translation_did_not_match_selected_route_position";
    }
    return request.matrix_matches_target;
}

bool observe_native_adjustment(Request& request,
                               uint32_t adjusted_marker_ordinal) noexcept {
    if (request.state != State::DestinationOverridden || !request.input_overridden)
        return false;
    request.native_adjusted_ordinal = adjusted_marker_ordinal;
    request.stock_adjustment_returned = true;
    if (adjusted_marker_ordinal != request.marker_ordinal) {
        // Reject before the call unless single-participant identity is proved.
        // If that verified invariant nevertheless fails, report the failure;
        // never manufacture the original-input native result after the call.
        request.state = State::CommitMismatch;
        request.reason = "native_adjustment_invariant_failed_result_unmodified";
        return false;
    }
    request.reason = "native_adjustment_preserved_selected_road_marker";
    return true;
}

bool observe_native_consumption(Request& request, uint32_t backing,
                                const std::array<uint32_t, 16>& matrix,
                                road_target::Vec3 chassis_after,
                                bool active_flag,
                                uint64_t active_consumer_calls,
                                double horizontal_tolerance) noexcept {
    if (request.state != State::DestinationCommitted || !request.matrix_committed ||
        !active_flag || !backing ||
        (request.human_backing && backing != request.human_backing) ||
        !same_matrix(matrix, request.committed_matrix))
        return false;
    request.controller_backing = backing;
    request.active_consumer_calls = active_consumer_calls;
    request.chassis_after = chassis_after;
    request.native_consumed = true;
    request.chassis_matches_destination = close_horizontal(
        chassis_after, request.committed_translation, horizontal_tolerance);
    request.state = State::NativeConsumed;
    request.reason = active_consumer_calls != 1 ? "native_consumer_count_not_exclusive" :
        request.chassis_matches_destination ? "native_controller_consumed_selected_matrix" : "native_consumed_but_chassis_position_mismatch";
    if (active_consumer_calls != 1 || !request.chassis_matches_destination)
        request.state = State::CommitMismatch;
    return request.chassis_matches_destination && active_consumer_calls == 1;
}

bool observe_clear(Request& request, uint32_t backing, uint32_t store_va,
                   uint8_t flag_before, uint8_t native_value) noexcept {
    if (request.state != State::NativeConsumed || !request.controller_backing ||
        backing != request.controller_backing || flag_before != 1 || native_value != 0)
        return false;
    if (store_va == 0x00591345) request.clear_writer = "forward_input_fields_0x00591345";
    else if (store_va == 0x004CD1DE) request.clear_writer = "reset_timer_0x004CD1DE";
    else if (store_va == 0x004CD1A1) request.clear_writer = "recovery_mode0_0x004CD1A1";
    else if (store_va == 0x004CCC70) request.clear_writer = "reset_gate_0x004CCC70";
    else if (store_va == 0x004CB62A) request.clear_writer = "packed_state_restore_0x004CB62A";
    else return false;
    request.native_clear_seen = true;
    request.reason = "native_clear_observed_waiting_for_zero_consumer";
    return true;
}

bool observe_settled_zero(Request& request, uint32_t backing,
                          uint8_t flag_value) noexcept {
    if (request.state != State::NativeConsumed || !request.native_clear_seen ||
        backing != request.controller_backing || flag_value != 0 ||
        !request.chassis_matches_destination || request.active_consumer_calls != 1)
        return false;
    request.settled_zero_seen = true;
    request.state = State::Completed;
    request.reason = "native_recovery_completed_and_settled";
    return true;
}

void cancel(Request& request, const char* reason) noexcept {
    if (request.state == State::Disabled || request.state == State::Idle ||
        request.state == State::Completed || request.state == State::Cancelled ||
        request.state == State::Expired || request.state == State::Rejected ||
        request.state == State::CommitMismatch || request.state == State::TimedOut)
        return;
    request.state = State::Cancelled;
    request.reason = reason ? reason : "cancelled";
}

void invalidate_generation(Request& request, uint64_t race_generation,
                           uint64_t owner_lifetime) noexcept {
    if (active_state(request.state) &&
        (request.race_generation != race_generation || request.owner_lifetime != owner_lifetime))
        cancel(request, "race_or_owner_generation_changed");
}

bool expire(Request& request, uint64_t now_tick_ms,
            uint32_t transaction_timeout_ms) noexcept {
    if (request.state == State::Armed && now_tick_ms >= request.deadline_tick_ms) {
        request.state = State::Expired;
        request.reason = "armed_request_expired_without_native_recovery";
        return true;
    }
    if ((request.state == State::DestinationOverridden ||
         request.state == State::DestinationCommitted ||
         request.state == State::NativeConsumed) &&
        request.transaction_tick_ms && now_tick_ms >= request.transaction_tick_ms &&
        now_tick_ms - request.transaction_tick_ms > transaction_timeout_ms) {
        request.state = State::TimedOut;
        request.reason = "native_recovery_settlement_not_observed_before_timeout";
        return true;
    }
    return false;
}

const char* state_name(State state) noexcept {
    switch (state) {
    case State::Disabled: return "disabled";
    case State::Idle: return "idle";
    case State::Armed: return "road_teleport_armed";
    case State::RecoveryEntered: return "road_teleport_recovery_entered";
    case State::DestinationOverridden: return "road_teleport_destination_overridden";
    case State::DestinationCommitted: return "road_teleport_destination_committed";
    case State::NativeConsumed: return "road_teleport_native_consumed";
    case State::Completed: return "road_teleport_completed";
    case State::Cancelled: return "road_teleport_cancelled";
    case State::Expired: return "road_teleport_expired";
    case State::Rejected: return "road_teleport_rejected";
    case State::CommitMismatch: return "road_teleport_commit_mismatch";
    case State::TimedOut: return "road_teleport_timed_out";
    }
    return "road_teleport_unknown_state";
}

} // namespace gfx2::road_teleport
