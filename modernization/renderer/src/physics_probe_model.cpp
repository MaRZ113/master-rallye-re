#include "physics_probe_model.hpp"

#include <cstring>
#include <limits>

namespace gfx2::physics_probe {

RecoveryManagerState read_recovery_manager(uint32_t manager, uint32_t participant,
                                           NativeWordRead read) noexcept {
    RecoveryManagerState s{}; s.manager = manager; s.participant = participant;
    uint32_t count = 0, array = 0, value = 0, count_after = 0, array_after = 0, value_after = 0;
    if (!read || !pointer_shape(manager) || manager > UINT32_MAX - 0x50u ||
        !read(manager + 0x14, count) || count < 1 || count > MAX_TRACKS || participant >= count ||
        !read(manager + 0x50, array) || !pointer_shape(array) ||
        uint64_t(array) + uint64_t(participant) * 4u + 4u > UINT32_MAX ||
        !read(array + participant * 4u, value)) return s;
    s.participant_count = count; s.countdown_array = array;
    std::memcpy(&s.countdown, &value, sizeof(value)); s.readable = true;
    s.stable = read(manager + 0x14, count_after) && read(manager + 0x50, array_after) &&
        read(array + participant * 4u, value_after) && count == count_after &&
        array == array_after && value == value_after;
    return s;
}

RecoveryDecision evaluate_recovery_manager(const RecoveryManagerState& s, RecoveryPhase phase) noexcept {
    if (!s.readable || !pointer_shape(s.manager) || !pointer_shape(s.countdown_array))
        return {false, "reset_manager_unreadable"};
    if (!s.stable) return {false, "reset_manager_storage_changed"};
    if (s.participant_count != 1 || s.participant != 0)
        return {false, "native_single_participant_required"};
    if (s.countdown < 0) return {false, "native_recovery_countdown_invalid"};
    if (s.countdown != 0) return {false, phase == RecoveryPhase::ArmIdle ?
        "native_recovery_in_progress" : "native_selection_before_countdown_elapsed"};
    return {true, phase == RecoveryPhase::ArmIdle ? "native_recovery_idle" : "native_recovery_selection_ready"};
}

OwnerClass owner_class(uint32_t player_type) noexcept {
    if (player_type == 1) return OwnerClass::HumanCandidate;
    if (player_type == 2) return OwnerClass::AiCandidate;
    return OwnerClass::Unknown;
}

VehicleOwnerDecision evaluate_vehicle_owner(const VehicleOwnerEvidence& e) noexcept {
    if (!e.race_certificate_current || !e.single_human_car ||
        !e.participant_count || e.participant_index != 0 ||
        !e.participant_identity_verified || e.participant_player_type != 1)
        return {false, "human_participant_missing"};
    if (!e.race_generation || e.race_generation != e.expected_race_generation ||
        !e.owner_lifetime || e.owner_lifetime != e.expected_owner_lifetime)
        return {false, "race_generation_mismatch"};
    if (!e.human_controllers) return {false, "controller_owner_mismatch"};
    if (e.human_controllers != 1) return {false, "multiple_human_controllers"};
    if (e.physical_player_type != 1 || !pointer_shape(e.race_owner_actor) || !e.physical_actor ||
        !e.controller || !e.backing)
        return {false, "actor_relationship_unverified"};
    if (!e.links_readable || !e.links_stable || !pointer_shape(e.controller) ||
        !pointer_shape(e.backing) || !pointer_shape(e.physical_actor))
        return {false, "controller_links_invalid"};
    if (!e.track_generation || e.track_generation != e.current_track_generation)
        return {false, "controller_generation_stale"};
    if (e.pending_native_recovery) return {false, "native_recovery_in_progress"};
    if (!e.current_apply_flag_readable) return {false, "apply_flag_unreadable"};
    if (e.current_apply_flag != 0) return {false, "apply_flag_active"};
    // A stale cached set bit is diagnostic only: current native backing is the
    // authority at arm time, including while the game is paused.
    const auto recovery = evaluate_recovery_manager(e.recovery, RecoveryPhase::ArmIdle);
    if (!recovery.accepted) return {false, recovery.reason};
    return {true, "accepted"};
}

bool pointer_shape(uint32_t pointer) noexcept {
    return pointer >= 0x10000u && (pointer & 3u) == 0;
}

bool route_getter_hook_requested(bool observer_enabled,
                                 bool road_preview_enabled) noexcept {
    return observer_enabled && road_preview_enabled;
}

size_t physics_call_patch_count(bool include_route_getter) noexcept {
    return physics_call_patch_count(include_route_getter, false);
}

size_t physics_call_patch_count(bool include_route_getter,
                                bool include_road_adjust) noexcept {
    return 3u + (include_route_getter ? 1u : 0u) + (include_road_adjust ? 1u : 0u);
}

bool links_valid(const NativeLinks& links) noexcept {
    return pointer_shape(links.controller) && pointer_shape(links.handle) &&
           links.handle_controller == links.controller && pointer_shape(links.actor) &&
           pointer_shape(links.body) && pointer_shape(links.backing) &&
           pointer_shape(links.wheel_records);
}

bool same_identity(const NativeLinks& a, const NativeLinks& b) noexcept {
    return links_valid(a) && links_valid(b) && a.controller == b.controller &&
           a.handle == b.handle && a.actor == b.actor && a.body == b.body &&
           a.backing == b.backing && a.wheel_records == b.wheel_records &&
           a.player_type == b.player_type;
}

bool encode_relative_call(uint32_t site_va, uint32_t target_va,
                          std::array<uint8_t, 5>& output) noexcept {
    output = {};
    if (site_va > std::numeric_limits<uint32_t>::max() - 5u) return false;
    const int64_t displacement = static_cast<int64_t>(target_va) -
                                 static_cast<int64_t>(site_va) - 5;
    if (displacement < std::numeric_limits<int32_t>::min() ||
        displacement > std::numeric_limits<int32_t>::max()) return false;
    const int32_t rel32 = static_cast<int32_t>(displacement);
    output[0] = 0xE8;
    std::memcpy(output.data() + 1, &rel32, sizeof(rel32));
    return true;
}

bool context_bytes_match(const uint8_t* expected, size_t expected_size,
                         const uint8_t* actual, size_t actual_size) noexcept {
    return expected && actual && expected_size != 0 && expected_size == actual_size &&
           std::memcmp(expected, actual, expected_size) == 0;
}

const char* context_failure_reason(bool controller_ok, bool substep_begin_ok,
                                   bool substep_tail_ok) noexcept {
    if (!controller_ok) return "controller_context_mismatch";
    if (!substep_begin_ok) return "substep_begin_context_mismatch";
    if (!substep_tail_ok) return "substep_tail_context_mismatch";
    return nullptr;
}

ClearWriter clear_writer(uint32_t store_va) noexcept {
    switch (store_va) {
    case CLEAR_GATE_STORE_VA: return ClearWriter::GateRejected;
    case CLEAR_RECOVERY_STORE_VA: return ClearWriter::RecoveryMode0;
    case CLEAR_TIMER_STORE_VA: return ClearWriter::TimerExpired;
    default: return ClearWriter::Unknown;
    }
}

const char* clear_writer_name(ClearWriter writer) noexcept {
    switch (writer) {
    case ClearWriter::GateRejected: return "reset_gate_rejected";
    case ClearWriter::RecoveryMode0: return "recovery_mode0";
    case ClearWriter::TimerExpired: return "recovery_timer_expired";
    default: return "unknown";
    }
}

ClearCaptureDecision observe_clear_store(ClearCapture& capture, ClearWriter writer,
                                         bool readable, uint8_t before,
                                         uint8_t native_value) noexcept {
    auto index = static_cast<size_t>(writer);
    if (index >= capture.writers.size()) index = 0;
    auto& counts = capture.writers[index];
    const auto increment = [](uint64_t& value) {
        if (value != UINT64_MAX) ++value;
    };
    increment(counts.calls);
    ClearCaptureDecision result{};
    if (!readable) {
        increment(counts.unreadable);
        result.observation = StoreObservation::Unreadable;
    } else if (before != native_value) {
        result.observation = StoreObservation::Transition;
        if (before != 0 && native_value == 0) increment(counts.clears);
        else if (before == 0 && native_value != 0) increment(counts.rises);
        else increment(counts.other_transitions);
        if (capture.transition_count < CLEAR_TRANSITION_CAPACITY) {
            result.retained = true;
            result.slot = capture.transition_count++;
        } else increment(capture.transition_overflow);
        return result;
    } else if (before == 0) {
        increment(counts.zero_stores_suppressed);
        return result;
    } else {
        increment(counts.repeated_nonzero);
        result.observation = StoreObservation::RepeatedNonzero;
    }
    if (capture.diagnostic_count < CLEAR_DIAGNOSTIC_CAPACITY) {
        result.retained = true;
        result.slot = CLEAR_TRANSITION_CAPACITY + capture.diagnostic_count++;
    } else increment(capture.diagnostic_overflow);
    return result;
}

const char* store_observation_name(StoreObservation observation) noexcept {
    switch (observation) {
    case StoreObservation::Transition: return "before_store_transition";
    case StoreObservation::RepeatedNonzero: return "repeated_nonzero_store";
    case StoreObservation::Unreadable: return "unreadable_backing";
    default: return "routine_zero_suppressed";
    }
}

PauseStateAtTime pause_state_at(PauseStateSample sample, uint64_t now_ms,
                                uint64_t maximum_age_ms) noexcept {
    if (!sample.known || !sample.sampled_tick_ms || now_ms < sample.sampled_tick_ms ||
        now_ms - sample.sampled_tick_ms > maximum_age_ms) return {};
    return {true, sample.paused, now_ms - sample.sampled_tick_ms};
}

const char* clear_context_failure_reason(bool gate_ok, bool recovery_ok,
                                        bool timer_ok) noexcept {
    if (!gate_ok) return "clear_gate_context_mismatch";
    if (!recovery_ok) return "clear_recovery_context_mismatch";
    if (!timer_ok) return "clear_timer_context_mismatch";
    return nullptr;
}

FlagEvent observe_flag(FlagTracker& tracker, uint8_t value) noexcept {
    const bool now_set = value != 0;
    ++tracker.calls;
    if (now_set) ++tracker.set_calls;

    if (!tracker.known) {
        tracker.known = true;
        tracker.set = now_set;
        if (now_set) {
            ++tracker.rises;
            tracker.captured_set_samples = 1;
            tracker.settling_remaining = 0;
            return FlagEvent::FirstSetObserved;
        }
        return FlagEvent::None;
    }

    if (!tracker.set && now_set) {
        tracker.set = true;
        ++tracker.rises;
        tracker.captured_set_samples = 1;
        tracker.settling_remaining = 0;
        return FlagEvent::SetEdge;
    }
    if (tracker.set && now_set) {
        if (tracker.captured_set_samples < MAX_FLAGGED_SAMPLES) {
            ++tracker.captured_set_samples;
            return FlagEvent::RepeatedSet;
        }
        return FlagEvent::None;
    }
    if (tracker.set && !now_set) {
        tracker.set = false;
        ++tracker.clears;
        tracker.settling_remaining = SETTLING_SAMPLES;
        return FlagEvent::ClearEdge;
    }
    if (tracker.settling_remaining) {
        --tracker.settling_remaining;
        return FlagEvent::Settling;
    }
    return FlagEvent::None;
}

bool reserve_bounded_slot(size_t& used, size_t capacity) noexcept {
    if (used >= capacity) return false;
    ++used;
    return true;
}

const char* flag_event_name(FlagEvent event) noexcept {
    switch (event) {
    case FlagEvent::FirstSetObserved: return "first_set_observed";
    case FlagEvent::SetEdge: return "set_edge";
    case FlagEvent::RepeatedSet: return "repeated_set";
    case FlagEvent::ClearEdge: return "clear_edge";
    case FlagEvent::Settling: return "settling";
    default: return "none";
    }
}

} // namespace gfx2::physics_probe
