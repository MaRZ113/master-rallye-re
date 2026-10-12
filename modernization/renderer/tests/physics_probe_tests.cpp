#include "physics_probe_model.hpp"

#include <array>
#include <cstdint>
#include <cstring>
#include <map>
#include "provenance.hpp"

#define CHECK(condition) do { if (!(condition)) return __LINE__; } while (0)

using namespace gfx2::physics_probe;
std::map<uint32_t,uint32_t> recovery_words;
unsigned recovery_reads=0;
bool churn_recovery_pointer=false;
bool read_recovery_test(uint32_t address,uint32_t& value) noexcept {
    ++recovery_reads;
    const auto found=recovery_words.find(address);
    if(found==recovery_words.end())return false;
    value=found->second;
    if(churn_recovery_pointer&&recovery_reads==3)recovery_words[0x51050]=0x119BC280;
    return true;
}

int main() {
    CHECK(gfx2::sha256_bytes("abc",3)=="ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad");
    recovery_words={{0x51014,1},{0x51050,0x119BC270},{0x119BC270,0}};
    auto native_recovery=read_recovery_manager(0x51000,0,&read_recovery_test);
    CHECK(native_recovery.readable&&native_recovery.stable&&native_recovery.countdown_array==0x119BC270);
    CHECK(evaluate_recovery_manager(native_recovery,RecoveryPhase::ArmIdle).accepted);
    CHECK(evaluate_recovery_manager(native_recovery,RecoveryPhase::NativeSelection).accepted);
    recovery_words[0x119BC270]=3;
    native_recovery=read_recovery_manager(0x51000,0,&read_recovery_test);
    CHECK(!evaluate_recovery_manager(native_recovery,RecoveryPhase::ArmIdle).accepted);
    CHECK(!evaluate_recovery_manager(native_recovery,RecoveryPhase::NativeSelection).accepted);
    recovery_words[0x51014]=2;recovery_words[0x119BC270]=0;recovery_words[0x119BC274]=6;
    CHECK(read_recovery_manager(0x51000,0,&read_recovery_test).countdown==0);
    CHECK(read_recovery_manager(0x51000,1,&read_recovery_test).countdown==6);
    CHECK(!read_recovery_manager(0x51000,2,&read_recovery_test).readable);
    CHECK(!evaluate_recovery_manager(read_recovery_manager(0x51000,0,&read_recovery_test),RecoveryPhase::NativeSelection).accepted);
    recovery_words[0x51014]=1;recovery_reads=0;churn_recovery_pointer=true;
    CHECK(!read_recovery_manager(0x51000,0,&read_recovery_test).stable);
    churn_recovery_pointer=false;recovery_words[0x51050]=0;
    CHECK(!read_recovery_manager(0x51000,0,&read_recovery_test).readable);
    CHECK(owner_class(1) == OwnerClass::HumanCandidate);
    CHECK(owner_class(2) == OwnerClass::AiCandidate);
    CHECK(owner_class(0) == OwnerClass::Unknown);
    CHECK(owner_class(3) == OwnerClass::Unknown);
    VehicleOwnerEvidence owner{};
    owner.race_certificate_current = true;
    owner.single_human_car = true;
    owner.race_generation = owner.expected_race_generation = 7;
    owner.owner_lifetime = owner.expected_owner_lifetime = 2;
    owner.participant_count = 1;
    owner.participant_index = 0;
    owner.participant_identity_verified = true;
    owner.participant_player_type = 1;
    owner.tracked_controllers = 4; // three AI tracks are permitted
    owner.human_controllers = 1;
    owner.physical_player_type = 1;
    owner.race_owner_actor = 0x11000;
    owner.physical_actor = 0x21000; // distinct identity domains are expected
    owner.controller = 0x31000;
    owner.backing = 0x41000;
    owner.links_readable = owner.links_stable = true;
    owner.track_generation = owner.current_track_generation = 3;
    owner.cached_apply_flag_known = owner.cached_apply_flag_set = true;
    owner.current_apply_flag_readable = true;
    owner.current_apply_flag = 0;
    owner.recovery = {0x51000, 0, 1, 0x119BC270, 0, true, true};
    CHECK(evaluate_vehicle_owner(owner).accepted);
    auto owner_bad = owner;
    owner_bad.physical_player_type = 2;
    CHECK(std::strcmp(evaluate_vehicle_owner(owner_bad).reason,
                      "actor_relationship_unverified") == 0);
    owner_bad = owner;
    owner_bad.current_apply_flag = 1;
    CHECK(std::strcmp(evaluate_vehicle_owner(owner_bad).reason, "apply_flag_active") == 0);
    owner_bad = owner;
    owner_bad.pending_native_recovery = true;
    CHECK(std::strcmp(evaluate_vehicle_owner(owner_bad).reason,
                      "native_recovery_in_progress") == 0);
    owner_bad = owner;
    owner_bad.human_controllers = 2;
    CHECK(std::strcmp(evaluate_vehicle_owner(owner_bad).reason,
                      "multiple_human_controllers") == 0);
    owner_bad = owner;
    owner_bad.expected_race_generation = 8;
    CHECK(std::strcmp(evaluate_vehicle_owner(owner_bad).reason,
                      "race_generation_mismatch") == 0);
    owner_bad = owner;
    owner_bad.recovery.readable = false;
    CHECK(std::strcmp(evaluate_vehicle_owner(owner_bad).reason,
                      "reset_manager_unreadable") == 0);
    owner_bad = owner;
    owner_bad.links_stable = false;
    CHECK(std::strcmp(evaluate_vehicle_owner(owner_bad).reason,
                      "controller_links_invalid") == 0);
    CHECK(!pointer_shape(0));
    CHECK(!route_getter_hook_requested(false, false));
    CHECK(!route_getter_hook_requested(false, true));
    CHECK(!route_getter_hook_requested(true, false));
    CHECK(route_getter_hook_requested(true, true));
    CHECK(physics_call_patch_count(false) == 3);
    CHECK(physics_call_patch_count(true) == 4);
    CHECK(physics_call_patch_count(true, true) == 5);

    NativeLinks links{0x10000, 0x20000, 0x10000, 0x30000, 0x40000,
                      0x50000, 0x60000, 1};
    CHECK(links_valid(links));
    auto replacement = links;
    replacement.body = 0x70000;
    CHECK(!same_identity(links, replacement));
    replacement = links;
    replacement.handle_controller = 0x11000;
    CHECK(!links_valid(replacement));
    replacement = links;
    replacement.wheel_records = 0x60001;
    CHECK(!links_valid(replacement));

    std::array<uint8_t, 5> call{};
    CHECK(encode_relative_call(CONTROLLER_CALL_VA, CONTROLLER_CALL_TARGET_VA, call));
    CHECK((call == std::array<uint8_t, 5>{0xE8, 0xB4, 0x12, 0x00, 0x00}));
    CHECK(encode_relative_call(SUBSTEP_BEGIN_CALL_VA, SUBSTEP_BEGIN_TARGET_VA, call));
    CHECK((call == std::array<uint8_t, 5>{0xE8, 0x9E, 0xFD, 0xFF, 0xFF}));
    CHECK(encode_relative_call(SUBSTEP_TAIL_CALL_VA, SUBSTEP_TAIL_TARGET_VA, call));
    CHECK((call == std::array<uint8_t, 5>{0xE8, 0x0E, 0x05, 0x00, 0x00}));
    CHECK(encode_relative_call(ROUTE_GETTER_CALL_VA, ROUTE_GETTER_TARGET_VA, call));
    CHECK(call == ROUTE_GETTER_CALL);
    CHECK(!encode_relative_call(0xFFFFFFFCu, 0x00400000u, call));

    const std::array<uint8_t, 14> retail_controller_context = {
        0x56, 0x57, 0x8B, 0xF9, 0x8B, 0x4F, 0x14, 0xE8,
        0xB4, 0x12, 0x00, 0x00, 0x33, 0xF6
    };
    const std::array<uint8_t, 15> retail_substep_begin_context = {
        0x8B, 0xCE, 0xD9, 0x5C, 0x24, 0x0C, 0xE8, 0x9E,
        0xFD, 0xFF, 0xFF, 0x8B, 0x7C, 0x24, 0x0C
    };
    const std::array<uint8_t, 25> retail_substep_tail_context = {
        0x57, 0x8B, 0xCE, 0xE8, 0x1C, 0x03, 0x00, 0x00,
        0x8B, 0xCE, 0xE8, 0xB5, 0x04, 0x00, 0x00,
        0x8B, 0xCE, 0xE8, 0x0E, 0x05, 0x00, 0x00,
        0x4B, 0x75, 0xA6
    };
    CHECK(context_bytes_match(CONTROLLER_CONTEXT.data(), CONTROLLER_CONTEXT.size(),
                              retail_controller_context.data(), retail_controller_context.size()));
    CHECK(context_bytes_match(SUBSTEP_BEGIN_CONTEXT.data(), SUBSTEP_BEGIN_CONTEXT.size(),
                              retail_substep_begin_context.data(), retail_substep_begin_context.size()));
    CHECK(context_bytes_match(SUBSTEP_TAIL_CONTEXT.data(), SUBSTEP_TAIL_CONTEXT.size(),
                              retail_substep_tail_context.data(), retail_substep_tail_context.size()));
    auto damaged_tail_context = retail_substep_tail_context;
    damaged_tail_context[4] ^= 1;
    CHECK(!context_bytes_match(SUBSTEP_TAIL_CONTEXT.data(), SUBSTEP_TAIL_CONTEXT.size(),
                               damaged_tail_context.data(), damaged_tail_context.size()));
    CHECK(!context_bytes_match(SUBSTEP_TAIL_CONTEXT.data(), SUBSTEP_TAIL_CONTEXT.size(),
                               retail_substep_tail_context.data(), retail_substep_tail_context.size() - 1));
    CHECK(!context_bytes_match(nullptr, SUBSTEP_TAIL_CONTEXT.size(),
                               retail_substep_tail_context.data(), retail_substep_tail_context.size()));
    const std::array<uint8_t, 16> retail_route_getter_context = {
        0x8D, 0x46, 0x54, 0x50, 0xE8, 0x11, 0x85, 0x01,
        0x00, 0x8B, 0xC8, 0xE8, 0x6A, 0x80, 0x01, 0x00
    };
    CHECK(context_bytes_match(ROUTE_GETTER_CONTEXT.data(), ROUTE_GETTER_CONTEXT.size(),
                              retail_route_getter_context.data(), retail_route_getter_context.size()));
    const std::array<uint8_t, 31> retail_road_adjust_context = {
        0x8B,0x4C,0x24,0x28,0x57,0x51,0x55,0x8B,
        0xCE,0xE8,0xC7,0x04,0x00,0x00,0x8B,0x57,
        0x04,0x8D,0x2C,0xC0,0xC1,0xE5,0x03,0x89,
        0x44,0x24,0x28,0x8B,0x4C,0x2A,0x38
    };
    CHECK(context_bytes_match(ROAD_ADJUST_CONTEXT.data(), ROAD_ADJUST_CONTEXT.size(),
                              retail_road_adjust_context.data(), retail_road_adjust_context.size()));
    auto damaged_road_adjust_context = retail_road_adjust_context;
    damaged_road_adjust_context[10] ^= 1;
    CHECK(!context_bytes_match(ROAD_ADJUST_CONTEXT.data(), ROAD_ADJUST_CONTEXT.size(),
                               damaged_road_adjust_context.data(), damaged_road_adjust_context.size()));
    CHECK(encode_relative_call(ROAD_ADJUST_CALL_VA, ROAD_ADJUST_TARGET_VA, call));
    CHECK(call == ROAD_ADJUST_CALL);
    const std::array<uint8_t, 13> retail_route_getter_entry = {
        0x8B, 0x44, 0x24, 0x04, 0x8B, 0x10, 0x8B, 0x41, 0x04,
        0x85, 0xC0, 0x74, 0x12
    };
    CHECK(context_bytes_match(ROUTE_GETTER_CALLEE_ENTRY_CONTEXT.data(),
                              ROUTE_GETTER_CALLEE_ENTRY_CONTEXT.size(),
                              retail_route_getter_entry.data(), retail_route_getter_entry.size()));
    const std::array<uint8_t, 3> retail_route_getter_ret4 = {0xC2, 0x04, 0x00};
    CHECK(context_bytes_match(ROUTE_GETTER_RET4_CONTEXT.data(), ROUTE_GETTER_RET4_CONTEXT.size(),
                              retail_route_getter_ret4.data(), retail_route_getter_ret4.size()));
    auto damaged_getter_ret = retail_route_getter_ret4;
    damaged_getter_ret[1] = 0;
    CHECK(!context_bytes_match(ROUTE_GETTER_RET4_CONTEXT.data(), ROUTE_GETTER_RET4_CONTEXT.size(),
                               damaged_getter_ret.data(), damaged_getter_ret.size()));
    auto damaged_route_context = retail_route_getter_context;
    damaged_route_context[11] ^= 1;
    CHECK(!context_bytes_match(ROUTE_GETTER_CONTEXT.data(), ROUTE_GETTER_CONTEXT.size(),
                               damaged_route_context.data(), damaged_route_context.size()));
    CHECK(!context_bytes_match(ROUTE_GETTER_CONTEXT.data(), ROUTE_GETTER_CONTEXT.size(),
                               retail_route_getter_context.data(), retail_route_getter_context.size() - 1));
    const std::array<uint8_t, 7> retail_clear_gate_context = {
        0x8B, 0x40, 0x08, 0xC6, 0x40, 0x33, 0x00
    };
    const std::array<uint8_t, 7> retail_clear_recovery_context = {
        0x8B, 0x48, 0x08, 0xC6, 0x41, 0x33, 0x00
    };
    const std::array<uint8_t, 6> retail_clear_timer_context = {
        0x8B, 0x40, 0x08, 0x88, 0x48, 0x33
    };
    CHECK(context_bytes_match(CLEAR_GATE_CONTEXT.data(), CLEAR_GATE_CONTEXT.size(),
                              retail_clear_gate_context.data(), retail_clear_gate_context.size()));
    CHECK(context_bytes_match(CLEAR_RECOVERY_CONTEXT.data(), CLEAR_RECOVERY_CONTEXT.size(),
                              retail_clear_recovery_context.data(), retail_clear_recovery_context.size()));
    CHECK(context_bytes_match(CLEAR_TIMER_CONTEXT.data(), CLEAR_TIMER_CONTEXT.size(),
                              retail_clear_timer_context.data(), retail_clear_timer_context.size()));
    auto damaged_clear = retail_clear_timer_context;
    damaged_clear[4] ^= 1;
    CHECK(!context_bytes_match(CLEAR_TIMER_CONTEXT.data(), CLEAR_TIMER_CONTEXT.size(),
                               damaged_clear.data(), damaged_clear.size()));
    CHECK(!context_bytes_match(CLEAR_TIMER_CONTEXT.data(), CLEAR_TIMER_CONTEXT.size(),
                               retail_clear_timer_context.data(), retail_clear_timer_context.size() - 1));
    CHECK(std::strcmp(clear_context_failure_reason(false, false, false),
                      "clear_gate_context_mismatch") == 0);
    CHECK(std::strcmp(clear_context_failure_reason(true, false, false),
                      "clear_recovery_context_mismatch") == 0);
    CHECK(std::strcmp(clear_context_failure_reason(true, true, false),
                      "clear_timer_context_mismatch") == 0);
    CHECK(clear_context_failure_reason(true, true, true) == nullptr);
    CHECK(clear_writer(CLEAR_GATE_STORE_VA) == ClearWriter::GateRejected);
    CHECK(clear_writer(CLEAR_RECOVERY_STORE_VA) == ClearWriter::RecoveryMode0);
    CHECK(clear_writer(CLEAR_TIMER_STORE_VA) == ClearWriter::TimerExpired);
    CHECK(clear_writer(0x004CD1E0) == ClearWriter::Unknown);
    CHECK(std::strcmp(clear_writer_name(clear_writer(CLEAR_TIMER_STORE_VA)),
                      "recovery_timer_expired") == 0);
    auto pause = pause_state_at({true, true, 1000}, 1450, 500);
    CHECK(pause.known && pause.paused && pause.age_ms == 450);
    pause = pause_state_at({true, false, 1000}, 1500, 500);
    CHECK(pause.known && !pause.paused && pause.age_ms == 500);
    CHECK(!pause_state_at({true, true, 1000}, 1501, 500).known);
    CHECK(!pause_state_at({true, true, 1501}, 1500, 500).known);
    CHECK(!pause_state_at({false, true, 1000}, 1000, 500).known);
    CHECK(std::strcmp(context_failure_reason(false, false, false),
                      "controller_context_mismatch") == 0);
    CHECK(std::strcmp(context_failure_reason(true, false, false),
                      "substep_begin_context_mismatch") == 0);
    CHECK(std::strcmp(context_failure_reason(true, true, false),
                      "substep_tail_context_mismatch") == 0);
    CHECK(context_failure_reason(true, true, true) == nullptr);

    FlagTracker flag{};
    CHECK(observe_flag(flag, 0) == FlagEvent::None);
    CHECK(observe_flag(flag, 1) == FlagEvent::SetEdge);
    CHECK(observe_flag(flag, 1) == FlagEvent::RepeatedSet);
    CHECK(observe_flag(flag, 1) == FlagEvent::RepeatedSet);
    CHECK(observe_flag(flag, 1) == FlagEvent::RepeatedSet);
    CHECK(observe_flag(flag, 1) == FlagEvent::None);
    CHECK(observe_flag(flag, 1) == FlagEvent::None);
    CHECK(observe_flag(flag, 0) == FlagEvent::ClearEdge);
    CHECK(observe_flag(flag, 0) == FlagEvent::Settling);
    CHECK(observe_flag(flag, 0) == FlagEvent::Settling);
    CHECK(observe_flag(flag, 0) == FlagEvent::Settling);
    CHECK(observe_flag(flag, 0) == FlagEvent::None);
    CHECK(flag.calls == 12);
    CHECK(flag.set_calls == 6);
    CHECK(flag.rises == 1);
    CHECK(flag.clears == 1);

    FlagTracker initially_set{};
    CHECK(observe_flag(initially_set, 1) == FlagEvent::FirstSetObserved);
    CHECK(initially_set.rises == 1);
    CHECK(std::strcmp(flag_event_name(FlagEvent::ClearEdge), "clear_edge") == 0);

    size_t used = 0;
    CHECK(reserve_bounded_slot(used, 2));
    CHECK(reserve_bounded_slot(used, 2));
    CHECK(!reserve_bounded_slot(used, 2));
    CHECK(used == 2);

    // The old capture kept 32 routine zeros and dropped the following 465.
    // All 497 zeros must now leave every transition slot available.
    ClearCapture capture{};
    for (size_t i = 0; i < 497; ++i) {
        auto decision = observe_clear_store(capture, ClearWriter::GateRejected, true, 0, 0);
        CHECK(!decision.retained);
        CHECK(decision.observation == StoreObservation::SuppressedZero);
    }
    CHECK(capture.writers[1].calls == 497);
    CHECK(capture.writers[1].zero_stores_suppressed == 497);
    CHECK(capture.transition_count == 0 && capture.diagnostic_count == 0);
    auto clear = observe_clear_store(capture, ClearWriter::RecoveryMode0, true, 1, 0);
    CHECK(clear.retained && clear.slot == 0);
    CHECK(clear.observation == StoreObservation::Transition);
    CHECK(capture.writers[2].clears == 1);
    auto rise = observe_clear_store(capture, ClearWriter::TimerExpired, true, 0, 1);
    CHECK(rise.retained && rise.slot == 1);
    CHECK(capture.writers[3].rises == 1);
    auto noncanonical = observe_clear_store(capture, ClearWriter::TimerExpired, true, 2, 3);
    CHECK(noncanonical.retained && noncanonical.slot == 2);
    CHECK(capture.writers[3].other_transitions == 1);
    // Diagnostic noise cannot steal slots from flag changes.
    for (size_t i = 0; i < 100; ++i) {
        auto repeated = observe_clear_store(capture, ClearWriter::GateRejected, true, 1, 1);
        CHECK(repeated.observation == StoreObservation::RepeatedNonzero);
        CHECK(repeated.retained == (i < CLEAR_DIAGNOSTIC_CAPACITY));
        if (repeated.retained) CHECK(repeated.slot == CLEAR_TRANSITION_CAPACITY + i);
    }
    CHECK(capture.diagnostic_overflow == 100 - CLEAR_DIAGNOSTIC_CAPACITY);
    CHECK(capture.transition_overflow == 0);
    auto unreadable = observe_clear_store(capture, ClearWriter::Unknown, false, 1, 0);
    CHECK(unreadable.observation == StoreObservation::Unreadable && !unreadable.retained);
    CHECK(capture.writers[0].unreadable == 1 && capture.writers[0].clears == 0);
    for (size_t i = 3; i < CLEAR_TRANSITION_CAPACITY; ++i) {
        auto next = observe_clear_store(capture, ClearWriter::TimerExpired, true, 1, 0);
        CHECK(next.retained && next.slot == i);
    }
    CHECK(!observe_clear_store(capture, ClearWriter::TimerExpired, true, 1, 0).retained);
    CHECK(capture.transition_overflow == 1);
    CHECK(capture.transition_count == CLEAR_TRANSITION_CAPACITY);
    ClearCapture invalid_writer{};
    CHECK(observe_clear_store(invalid_writer, static_cast<ClearWriter>(255), false, 0, 0).retained);
    CHECK(invalid_writer.writers[0].calls == 1);
    capture.writers[3].calls = UINT64_MAX;
    capture.transition_overflow = UINT64_MAX;
    CHECK(!observe_clear_store(capture, ClearWriter::TimerExpired, true, 1, 0).retained);
    CHECK(capture.writers[3].calls == UINT64_MAX && capture.transition_overflow == UINT64_MAX);
    capture = {};
    CHECK(observe_clear_store(capture, ClearWriter::RecoveryMode0, true, 1, 0).slot == 0);
    return 0;
}
