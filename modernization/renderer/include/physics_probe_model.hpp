#pragma once

#include <array>
#include <cstddef>
#include <cstdint>

namespace gfx2::physics_probe {

inline constexpr uint32_t CONTROLLER_CALL_VA = 0x00443827;
inline constexpr uint32_t CONTROLLER_CALL_TARGET_VA = 0x00444AE0;
inline constexpr uint32_t SUBSTEP_BEGIN_CALL_VA = 0x0043F8AD;
inline constexpr uint32_t SUBSTEP_BEGIN_TARGET_VA = 0x0043F650;
inline constexpr uint32_t SUBSTEP_TAIL_CALL_VA = 0x0043F8ED;
inline constexpr uint32_t SUBSTEP_TAIL_TARGET_VA = 0x0043FE00;
inline constexpr uint32_t CONTROLLER_CONTEXT_VA = 0x00443820;
inline constexpr uint32_t SUBSTEP_BEGIN_CONTEXT_VA = 0x0043F8A7;
inline constexpr uint32_t SUBSTEP_TAIL_CONTEXT_VA = 0x0043F8DC;
inline constexpr uint32_t ROUTE_GETTER_CALL_VA = 0x004CCCB1;
inline constexpr uint32_t ROUTE_GETTER_TARGET_VA = 0x004E4D20;
inline constexpr uint32_t ROUTE_GETTER_CONTEXT_VA = 0x004CCCA6;
inline constexpr uint32_t ROAD_ADJUST_CALL_VA = 0x004CCD34;
inline constexpr uint32_t ROAD_ADJUST_TARGET_VA = 0x004CD200;
inline constexpr size_t ROAD_ADJUST_BODY_SIZE = 0x29A;
inline constexpr const char* ROAD_ADJUST_BODY_SHA256 = "0d81df8f1a1af9de4d10bd3baa2ea8adf703fbe52ad9f8abb503b54c274f2688";
inline constexpr uint32_t ROAD_ADJUST_DISTANCE_LIMIT_VA = 0x00691170;
inline constexpr uint32_t ROAD_ADJUST_DISTANCE_LIMIT_BITS = 0x42200000; // 40.0f
inline constexpr uint32_t ROAD_ADJUST_CONTEXT_VA = 0x004CCD2B;
inline constexpr uint32_t ROUTE_GETTER_CALLEE_ENTRY_VA = 0x004E4D20;
inline constexpr uint32_t ROUTE_GETTER_SUCCESS_RET_VA = 0x004E4D3C;
inline constexpr uint32_t ROUTE_GETTER_NULL_RET_VA = 0x004E4D41;
inline constexpr uint32_t CLEAR_GATE_PATCH_VA = 0x004CCC6D;
inline constexpr uint32_t CLEAR_GATE_STORE_VA = 0x004CCC70;
inline constexpr uint32_t CLEAR_RECOVERY_PATCH_VA = 0x004CD19E;
inline constexpr uint32_t CLEAR_RECOVERY_STORE_VA = 0x004CD1A1;
inline constexpr uint32_t CLEAR_TIMER_PATCH_VA = 0x004CD1DB;
inline constexpr uint32_t CLEAR_TIMER_STORE_VA = 0x004CD1DE;
inline constexpr std::array<uint8_t, 14> CONTROLLER_CONTEXT = {
    0x56, 0x57, 0x8B, 0xF9, 0x8B, 0x4F, 0x14, 0xE8,
    0xB4, 0x12, 0x00, 0x00, 0x33, 0xF6
};
inline constexpr std::array<uint8_t, 15> SUBSTEP_BEGIN_CONTEXT = {
    0x8B, 0xCE, 0xD9, 0x5C, 0x24, 0x0C, 0xE8, 0x9E,
    0xFD, 0xFF, 0xFF, 0x8B, 0x7C, 0x24, 0x0C
};
inline constexpr std::array<uint8_t, 25> SUBSTEP_TAIL_CONTEXT = {
    0x57, 0x8B, 0xCE, 0xE8, 0x1C, 0x03, 0x00, 0x00,
    0x8B, 0xCE, 0xE8, 0xB5, 0x04, 0x00, 0x00,
    0x8B, 0xCE, 0xE8, 0x0E, 0x05, 0x00, 0x00,
    0x4B, 0x75, 0xA6
};
inline constexpr std::array<uint8_t, 16> ROUTE_GETTER_CONTEXT = {
    0x8D, 0x46, 0x54, 0x50, 0xE8, 0x11, 0x85, 0x01,
    0x00, 0x8B, 0xC8, 0xE8, 0x6A, 0x80, 0x01, 0x00
};
inline constexpr std::array<uint8_t, 5> ROUTE_GETTER_CALL = {
    0xE8, 0x6A, 0x80, 0x01, 0x00
};
// Includes argument preparation, ECX manager, native call, and first use of
// its returned marker. The call bridge changes only the local marker argument.
inline constexpr std::array<uint8_t, 31> ROAD_ADJUST_CONTEXT = {
    0x8B,0x4C,0x24,0x28,0x57,0x51,0x55,0x8B,
    0xCE,0xE8,0xC7,0x04,0x00,0x00,0x8B,0x57,
    0x04,0x8D,0x2C,0xC0,0xC1,0xE5,0x03,0x89,
    0x44,0x24,0x28,0x8B,0x4C,0x2A,0x38
};
inline constexpr std::array<uint8_t, 5> ROAD_ADJUST_CALL = {
    0xE8, 0xC7, 0x04, 0x00, 0x00
};
inline constexpr std::array<uint8_t, 13> ROUTE_GETTER_CALLEE_ENTRY_CONTEXT = {
    0x8B, 0x44, 0x24, 0x04, 0x8B, 0x10, 0x8B, 0x41, 0x04,
    0x85, 0xC0, 0x74, 0x12
};
inline constexpr std::array<uint8_t, 3> ROUTE_GETTER_RET4_CONTEXT = {
    0xC2, 0x04, 0x00
};
inline constexpr std::array<uint8_t, 7> CLEAR_GATE_CONTEXT = {
    0x8B, 0x40, 0x08, 0xC6, 0x40, 0x33, 0x00
};
inline constexpr std::array<uint8_t, 7> CLEAR_RECOVERY_CONTEXT = {
    0x8B, 0x48, 0x08, 0xC6, 0x41, 0x33, 0x00
};
inline constexpr std::array<uint8_t, 6> CLEAR_TIMER_CONTEXT = {
    0x8B, 0x40, 0x08, 0x88, 0x48, 0x33
};
// Exact instruction blocks replayed by transaction bridges. No relative CALL
// is copied verbatim: restore bridge forwards the verified callee's ret-4 ABI.
inline constexpr uint32_t PUBLISH_PATCH_VA = 0x004CCFF1;
inline constexpr uint32_t MATRIX_COMPLETE_PATCH_VA = 0x004CD131;
inline constexpr uint32_t INPUT_FLAG_PATCH_VA = 0x00591345;
inline constexpr uint32_t RESTORE_FLAG_PATCH_VA = 0x004CB62A;
inline constexpr std::array<uint8_t, 7> PUBLISH_CONTEXT = {0xC6,0x45,0x33,0x01,0x8B,0x4E,0x1C};
inline constexpr std::array<uint8_t, 7> MATRIX_COMPLETE_CONTEXT = {0x8B,0x4E,0x3C,0x8B,0xD3,0x03,0xD1};
inline constexpr std::array<uint8_t, 6> INPUT_FLAG_CONTEXT = {0x88,0x50,0x33,0x8B,0x41,0x2C};
inline constexpr std::array<uint8_t, 8> RESTORE_FLAG_CONTEXT = {0x88,0x46,0x33,0xE8,0x4E,0x4F,0x00,0x00};
inline constexpr std::array<uint8_t, 24> RESTORE_CALLEE_CONTEXT = {
 0x8B,0x44,0x24,0x04,0x56,0x8B,0xF1,0x50,0xE8,0x63,0x3F,0x00,0x00,
 0x8B,0xC8,0xE8,0xCC,0x3E,0x00,0x00,0x89,0x06,0x5E,0xC2};
inline constexpr std::array<uint8_t, 103> MATRIX_COPY_CONTEXT = {
    0x8B,0xC1,0x8B,0x4C,0x24,0x04,0x8B,0x11,0x89,0x10,0x8B,0x51,0x04,0x89,0x50,0x04,
    0x8B,0x51,0x08,0x89,0x50,0x08,0x8B,0x51,0x0C,0x89,0x50,0x0C,0x8B,0x51,0x10,0x89,
    0x50,0x10,0x8B,0x51,0x14,0x89,0x50,0x14,0x8B,0x51,0x18,0x89,0x50,0x18,0x8B,0x51,
    0x1C,0x89,0x50,0x1C,0x8B,0x51,0x20,0x89,0x50,0x20,0x8B,0x51,0x24,0x89,0x50,0x24,
    0x8B,0x51,0x28,0x89,0x50,0x28,0x8B,0x51,0x2C,0x89,0x50,0x2C,0x8B,0x51,0x30,0x89,
    0x50,0x30,0x8B,0x51,0x34,0x89,0x50,0x34,0x8B,0x51,0x38,0x89,0x50,0x38,0x8B,0x49,
    0x3C,0x89,0x48,0x3C,0xC2,0x04,0x00
};

enum class ClearWriter : uint8_t { Unknown, GateRejected, RecoveryMode0, TimerExpired };
ClearWriter clear_writer(uint32_t store_va) noexcept;
const char* clear_writer_name(ClearWriter writer) noexcept;
// Routine zero stores cannot consume the transition partition. Once either
// partition fills, loss is explicit; this is not an unbounded capture promise.
inline constexpr size_t CLEAR_TRANSITION_CAPACITY = 24;
inline constexpr size_t CLEAR_DIAGNOSTIC_CAPACITY = 8;
inline constexpr size_t CLEAR_EVENT_CAPACITY =
    CLEAR_TRANSITION_CAPACITY + CLEAR_DIAGNOSTIC_CAPACITY;
enum class StoreObservation : uint8_t {
    SuppressedZero, Transition, RepeatedNonzero, Unreadable
};
struct ClearWriterCounters {
    uint64_t calls = 0;
    uint64_t zero_stores_suppressed = 0;
    uint64_t clears = 0;
    uint64_t rises = 0;
    uint64_t other_transitions = 0;
    uint64_t repeated_nonzero = 0;
    uint64_t unreadable = 0;
};
struct ClearCapture {
    std::array<ClearWriterCounters, 4> writers{};
    size_t transition_count = 0;
    size_t diagnostic_count = 0;
    uint64_t transition_overflow = 0;
    uint64_t diagnostic_overflow = 0;
};
struct ClearCaptureDecision {
    StoreObservation observation = StoreObservation::SuppressedZero;
    bool retained = false;
    size_t slot = 0;
};
ClearCaptureDecision observe_clear_store(ClearCapture& capture, ClearWriter writer,
                                         bool readable, uint8_t before,
                                         uint8_t native_value) noexcept;
const char* store_observation_name(StoreObservation observation) noexcept;
struct PauseStateSample {
    bool known = false;
    bool paused = false;
    uint64_t sampled_tick_ms = 0;
};
struct PauseStateAtTime {
    bool known = false;
    bool paused = false;
    uint64_t age_ms = 0;
};
PauseStateAtTime pause_state_at(PauseStateSample sample, uint64_t now_ms,
                                uint64_t maximum_age_ms) noexcept;
const char* clear_context_failure_reason(bool gate_ok, bool recovery_ok,
                                        bool timer_ok) noexcept;
inline constexpr size_t MAX_TRACKS = 8;
inline constexpr size_t MAX_EVENTS = 64;
inline constexpr uint32_t SUBSTEP_WINDOW_EVENTS = 24;
inline constexpr uint8_t MAX_FLAGGED_SAMPLES = 4;
inline constexpr uint8_t SETTLING_SAMPLES = 3;

enum class OwnerClass : uint8_t { Unknown, HumanCandidate, AiCandidate };
OwnerClass owner_class(uint32_t player_type) noexcept;

// Read-only semantic join between the Broker race participant certificate and
// the independently-created native physics controller chain. Pointer equality
// between those two actor objects is deliberately not part of this proof.
struct VehicleOwnerEvidence {
    bool race_certificate_current = false;
    bool single_human_car = false;
    uint64_t race_generation = 0, expected_race_generation = 0;
    uint64_t owner_lifetime = 0, expected_owner_lifetime = 0;
    uint32_t participant_count = 0, participant_index = UINT32_MAX;
    bool participant_identity_verified = false;
    int32_t participant_player_type = -1;
    size_t tracked_controllers = 0, human_controllers = 0;
    uint32_t physical_player_type = 0;
    uint32_t race_owner_actor = 0, physical_actor = 0;
    uint32_t controller = 0, backing = 0;
    bool links_readable = false, links_stable = false;
    uint64_t track_generation = 0, current_track_generation = 0;
    bool pending_native_recovery = false;
    bool cached_apply_flag_known = false, cached_apply_flag_set = false;
    bool current_apply_flag_readable = false;
    uint8_t current_apply_flag = 0;
    struct RecoveryManagerState {
        uint32_t manager = 0, participant = UINT32_MAX, participant_count = 0;
        uint32_t countdown_array = 0;
        int32_t countdown = -1;
        bool readable = false, stable = false;
    } recovery{};
};
using RecoveryManagerState = VehicleOwnerEvidence::RecoveryManagerState;
using NativeWordRead = bool (*)(uint32_t, uint32_t&) noexcept;
RecoveryManagerState read_recovery_manager(uint32_t manager, uint32_t participant,
                                           NativeWordRead read) noexcept;
enum class RecoveryPhase : uint8_t { ArmIdle, NativeSelection };
struct RecoveryDecision { bool accepted = false; const char* reason = "reset_manager_unreadable"; };
RecoveryDecision evaluate_recovery_manager(const RecoveryManagerState&, RecoveryPhase) noexcept;
struct VehicleOwnerDecision { bool accepted = false; const char* reason = "human_participant_missing"; };
VehicleOwnerDecision evaluate_vehicle_owner(const VehicleOwnerEvidence&) noexcept;

struct NativeLinks {
    uint32_t controller = 0;
    uint32_t handle = 0;
    uint32_t handle_controller = 0;
    uint32_t actor = 0;
    uint32_t body = 0;
    uint32_t backing = 0;
    uint32_t wheel_records = 0;
    uint32_t player_type = 0;
};

bool pointer_shape(uint32_t pointer) noexcept;
bool route_getter_hook_requested(bool observer_enabled,
                                 bool road_preview_enabled) noexcept;
size_t physics_call_patch_count(bool include_route_getter) noexcept;
size_t physics_call_patch_count(bool include_route_getter,
                                bool include_road_adjust) noexcept;
bool links_valid(const NativeLinks& links) noexcept;
bool same_identity(const NativeLinks& a, const NativeLinks& b) noexcept;
bool encode_relative_call(uint32_t site_va, uint32_t target_va,
                          std::array<uint8_t, 5>& output) noexcept;
bool context_bytes_match(const uint8_t* expected, size_t expected_size,
                         const uint8_t* actual, size_t actual_size) noexcept;
const char* context_failure_reason(bool controller_ok, bool substep_begin_ok,
                                   bool substep_tail_ok) noexcept;

enum class FlagEvent : uint8_t {
    None,
    FirstSetObserved,
    SetEdge,
    RepeatedSet,
    ClearEdge,
    Settling
};

struct FlagTracker {
    bool known = false;
    bool set = false;
    uint8_t captured_set_samples = 0;
    uint8_t settling_remaining = 0;
    uint64_t calls = 0;
    uint64_t set_calls = 0;
    uint64_t rises = 0;
    uint64_t clears = 0;
};

FlagEvent observe_flag(FlagTracker& tracker, uint8_t value) noexcept;
bool reserve_bounded_slot(size_t& used, size_t capacity) noexcept;
const char* flag_event_name(FlagEvent event) noexcept;

} // namespace gfx2::physics_probe
