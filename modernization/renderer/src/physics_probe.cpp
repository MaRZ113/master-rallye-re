#include "physics_probe.hpp"
#include "free_camera.hpp"

#include "physics_probe_model.hpp"
#include "physics_transaction_model.hpp"
#include "physics_inline_patch.hpp"
#include "road_teleport_model.hpp"
#include "road_teleport_events.hpp"
#include "road_teleport_bridge.hpp"
#include "provenance.hpp"
#include "race_epoch.hpp"
#include "state_tracker.hpp"

#include <tlhelp32.h>
#include <array>
#include <algorithm>
#include <atomic>
#include <cstring>
#include <cstdio>
#include <iterator>
#include <iomanip>
#include <sstream>
#include <cmath>
#include <cwctype>
#include <cwchar>
#include <intrin.h>

namespace gfx2 {
extern "C" void physics_probe_route_getter_bridge();
extern "C" void physics_probe_clear_gate_bridge();
extern "C" void physics_probe_clear_recovery_bridge();
extern "C" void physics_probe_clear_timer_bridge();
extern "C" void physics_probe_publish_bridge();
extern "C" void physics_probe_matrix_complete_bridge();
extern "C" void physics_probe_input_flag_bridge();
extern "C" void physics_probe_restore_flag_bridge();
extern "C" void physics_probe_road_adjust_bridge();
namespace {
using namespace physics_probe;

enum class EventKind : uint8_t {
    Controller,
    SubstepBeginBefore,
    SubstepBeginAfter,
    SubstepTailBefore,
    SubstepTailAfter
};

struct WheelSample {
    uint32_t address = 0;
    uint32_t word_120 = 0;
    uint8_t byte_04 = 0;
    uint8_t valid = 0;
};

struct Snapshot {
    NativeLinks links{};
    uint64_t qpc = 0;
    uint32_t thread_id = 0;
    bool pause_state_known = false;
    bool pause_paused = false;
    uint64_t pause_sample_age_ms = 0;
    int32_t participant_index = -1;
    uint32_t valid_mask = 0;
    uint8_t apply_flag = 0;
    uint8_t controller_byte_13 = 0;
    uint8_t controller_byte_18 = 0;
    uint8_t body_byte_04 = 0;
    std::array<uint32_t, 16> transform_bits{};
    std::array<uint32_t, 3> current_position_bits{};
    std::array<uint32_t, 3> previous_position_bits{};
    std::array<uint32_t, 6> body_opaque_11c_130{};
    std::array<WheelSample, 4> wheels{};
};

struct Event {
    uint64_t sequence = 0;
    EventKind kind = EventKind::Controller;
    FlagEvent flag_event = FlagEvent::None;
    uint32_t manager = 0;
    uint32_t loop_remaining = 0;
    bool has_before = false;
    bool has_after = false;
    bool has_baseline = false;
    Snapshot before{};
    Snapshot after{};
    Snapshot baseline{};
    size_t participant_count = 0;
    std::array<Snapshot, MAX_TRACKS> participants{};
};

struct Track {
    bool used = false;
    bool has_last = false;
    bool pending = false;
    uint32_t pending_thread = 0;
    uint64_t identity_generation = 0;
    NativeLinks identity{};
    FlagTracker flag{};
    FlagEvent pending_event = FlagEvent::None;
    bool pending_has_baseline = false;
    Snapshot last{};
    Snapshot pending_before{};
    Snapshot pending_baseline{};
    uint64_t overlap_calls = 0;
    uint64_t identity_changes = 0;
    uint64_t interval_consumer_calls = 0;
    uint64_t last_flagged_consumer_qpc = 0;
    uint32_t last_flagged_consumer_thread = 0;
};

struct InlinePatchBatch {
    std::array<InlinePatchUnit, 7> sites{};
    size_t count = 0;
    bool rollback_verified = true;
    bool owned() const noexcept {
        for (size_t i = 0; i < count; ++i) if (sites[i].owned) return true;
        return false;
    }
};

struct ClearWriterEvent {
    uint64_t sequence = 0;
    uint64_t qpc = 0;
    uint32_t store_va = 0;
    uint32_t entry_object = 0;
    uint32_t backing = 0;
    uint32_t thread_id = 0;
    uint32_t player_type = 0;
    uint32_t native_store_value = 0;
    uint64_t pause_sample_age_ms = 0;
    uint8_t flag_before = 0;
    bool backing_valid = false;
    bool owner_known = false;
    bool pause_state_known = false;
    bool pause_paused = false;
    StoreObservation observation = StoreObservation::Unreadable;
    uint32_t controller = 0;
    uint64_t owner_identity_generation = 0;
    uint64_t interval_consumer_calls = 0;
    uint64_t last_flagged_consumer_qpc = 0;
    uint32_t last_flagged_consumer_thread = 0;
    bool consumer_in_progress = false;
    bool owner_links_current = false;
    bool race_context_valid = false;
    uint64_t race_generation = 0;
    uint64_t owner_lifetime = 0;
};

struct ProbeState {
    SRWLOCK lock = SRWLOCK_INIT;
    RacePatchBatch batch{};
    InlinePatchBatch clear_writer_batch{};
    std::array<Track, MAX_TRACKS> tracks{};
    std::array<Event, MAX_EVENTS> events{};
    std::array<ClearWriterEvent, CLEAR_EVENT_CAPACITY> clear_writer_events{};
    ClearCapture clear_capture{};
    uint64_t clear_writer_event_sequence = 0;
    size_t event_count = 0;
    uint64_t event_sequence = 0;
    uint64_t dropped_events = 0;
    volatile LONG invalid_snapshots = 0;
    volatile LONG invalid_managers = 0;
    uint64_t dropped_tracks = 0;
    uint64_t substep_events = 0;
    uint64_t substep_windows = 0;
    uint64_t controller_calls_while_paused = 0;
    uint64_t substep_phase_records_while_paused = 0;
    uint64_t clear_writes_while_paused = 0;
    uint32_t substep_budget = 0;
    volatile LONG substep_window_active = 0;
    volatile LONG enabled = 0;
    volatile LONG route_preview_enabled = 0;
    bool road_teleport_enabled = false;
    bool route_context_valid = false;
    uint64_t route_context_race_generation = 0;
    uint64_t route_context_owner_lifetime = 0;
    road_target::LiveSnapshot route_snapshot{};
    uint64_t route_snapshot_sequence = 0;
    uint64_t route_capture_attempts = 0;
    uint64_t route_capture_failures = 0;
    const char* route_last_failure = "not_requested";
    double route_preview_radius = 60.0;
    double road_teleport_max_distance = 20.0;
    uint32_t road_teleport_arm_timeout_seconds = 60;
    road_teleport::Request road_teleport{};
    uint64_t road_teleport_next_sequence = 0;
    uint64_t road_teleport_selection_attempts = 0;
    uint64_t road_teleport_owner_gate_attempts = 0;
    uint64_t road_teleport_owner_gate_accepted = 0;
    uint64_t road_teleport_owner_gate_rejected = 0;
    uint64_t road_teleport_override_count = 0;
    uint64_t road_teleport_stock_fallback_count = 0;
    uint64_t road_teleport_stack_write_failures = 0;
    bool pause_state_known = false;
    bool pause_paused = false;
    uint64_t pause_sample_tick_ms = 0;
    uint32_t leases = 0;
    uint32_t base = 0;
    bool installed = false;
    bool patch_intact = false;
    bool module_pinned = false;
    const char* reason = "not_requested";
    const char* release_reason = "not_released";
    HMODULE pinned_module = nullptr;
} probe;

bool batch_intact() noexcept;
void disable_after_ownership_loss() noexcept;

class NativeMemory final : public PatchMemory {
public:
    bool read(void* dst, const void* src, size_t size) noexcept override {
        return safe_copy(dst, src, size);
    }
    bool write(void* dst, const void* src, size_t size) noexcept override {
        return safe_copy(dst, src, size);
    }
    bool protect(void* address, size_t size, DWORD protection, DWORD& prior) noexcept override {
        return VirtualProtect(address, size, protection, &prior) != FALSE;
    }
    bool flush(void* address, size_t size) noexcept override {
        return FlushInstructionCache(GetCurrentProcess(), address, size) != FALSE;
    }
} memory;

struct SuspendedThreads {
    std::array<HANDLE, 128> handles{};
    size_t count = 0;

    ~SuspendedThreads() {
        for (size_t i = count; i > 0; --i) {
            ResumeThread(handles[i - 1]);
            CloseHandle(handles[i - 1]);
        }
    }

    bool freeze(const RacePatchBatch& batch, const InlinePatchBatch* inline_batch = nullptr) noexcept {
        HANDLE snapshot = CreateToolhelp32Snapshot(TH32CS_SNAPTHREAD, 0);
        if (snapshot == INVALID_HANDLE_VALUE) return false;
        bool okay = true;
        THREADENTRY32 entry{};
        entry.dwSize = sizeof(entry);
        if (!Thread32First(snapshot, &entry)) {
            CloseHandle(snapshot);
            return false;
        }
        do {
            if (entry.th32OwnerProcessID != GetCurrentProcessId() ||
                entry.th32ThreadID == GetCurrentThreadId()) continue;
            if (count == handles.size()) { okay = false; break; }
            HANDLE thread = OpenThread(THREAD_SUSPEND_RESUME | THREAD_GET_CONTEXT |
                                       THREAD_QUERY_INFORMATION, FALSE, entry.th32ThreadID);
            if (!thread) { okay = false; break; }
            if (SuspendThread(thread) == DWORD(-1)) {
                CloseHandle(thread);
                okay = false;
                break;
            }
            handles[count++] = thread;
            CONTEXT context{};
            context.ContextFlags = CONTEXT_CONTROL;
            if (!GetThreadContext(thread, &context)) { okay = false; break; }
            for (size_t i = 0; i < batch.count; ++i) {
                const auto& site = batch.sites[i];
                const uintptr_t start = reinterpret_cast<uintptr_t>(site.address);
                if (context.Eip >= start && context.Eip < start + site.size) {
                    okay = false;
                    break;
                }
            }
            if (okay && inline_batch) {
                for (size_t i = 0; i < inline_batch->count; ++i) {
                    const auto& site = inline_batch->sites[i];
                    const uintptr_t start = reinterpret_cast<uintptr_t>(site.address);
                    if (context.Eip >= start && context.Eip < start + site.size) {
                        okay = false;
                        break;
                    }
                }
            }
            if (!okay) break;
        } while (Thread32Next(snapshot, &entry));
        CloseHandle(snapshot);
        return okay;
    }
};

bool add_address(uint32_t base, uint32_t offset, uint32_t& address) noexcept {
    if (base > UINT32_MAX - offset) return false;
    address = base + offset;
    return true;
}

bool read_u32(uint32_t base, uint32_t offset, uint32_t& value) noexcept {
    uint32_t address = 0;
    return add_address(base, offset, address) &&
           safe_copy(&value, reinterpret_cast<const void*>(address), sizeof(value));
}

bool read_u8(uint32_t base, uint32_t offset, uint8_t& value) noexcept {
    uint32_t address = 0;
    return add_address(base, offset, address) &&
           safe_copy(&value, reinterpret_cast<const void*>(address), sizeof(value));
}

void capture_pause_state(Snapshot& out) noexcept {
    const uint64_t now = GetTickCount64();
    AcquireSRWLockShared(&probe.lock);
    const PauseStateSample sample{probe.pause_state_known, probe.pause_paused,
                                  probe.pause_sample_tick_ms};
    ReleaseSRWLockShared(&probe.lock);
    const auto state = pause_state_at(sample, now, 500);
    out.pause_state_known = state.known;
    out.pause_paused = state.paused;
    out.pause_sample_age_ms = state.age_ms;
}

bool read_bytes(uint32_t base, uint32_t offset, void* output, size_t size) noexcept {
    if (size > UINT32_MAX) return false;
    uint32_t address = 0;
    if (!add_address(base, offset, address) || size > UINT32_MAX - address) return false;
    return safe_copy(output, reinterpret_cast<const void*>(address), size);
}

void fail_route_capture(const char* reason) noexcept {
    AcquireSRWLockExclusive(&probe.lock);
    if (probe.route_capture_attempts != UINT64_MAX) ++probe.route_capture_attempts;
    if (probe.route_capture_failures != UINT64_MAX) ++probe.route_capture_failures;
    probe.route_last_failure = reason ? reason : "route_snapshot_failed";
    probe.route_snapshot.available = false;
    probe.route_snapshot.reason = probe.route_last_failure;
    ReleaseSRWLockExclusive(&probe.lock);
}

void capture_live_route(uint32_t route_object, uint32_t recovery_manager) noexcept {
    if (InterlockedCompareExchange(&probe.enabled, 0, 0) == 0 ||
        InterlockedCompareExchange(&probe.route_preview_enabled, 0, 0) == 0) return;

    uint64_t race_generation = 0, owner_lifetime = 0;
    AcquireSRWLockExclusive(&probe.lock);
    if (InterlockedCompareExchange(&probe.enabled, 0, 0) == 0 ||
        InterlockedCompareExchange(&probe.route_preview_enabled, 0, 0) == 0) {
        ReleaseSRWLockExclusive(&probe.lock);
        return;
    }
    if (!batch_intact()) {
        disable_after_ownership_loss();
        ReleaseSRWLockExclusive(&probe.lock);
        return;
    }
    const bool context_valid = probe.route_context_valid;
    race_generation = probe.route_context_race_generation;
    owner_lifetime = probe.route_context_owner_lifetime;
    ReleaseSRWLockExclusive(&probe.lock);
    if (!context_valid || !race_generation || !owner_lifetime) {
        fail_route_capture("no_current_supported_france1_race_certificate");
        return;
    }
    if (!pointer_shape(route_object) || !pointer_shape(recovery_manager)) {
        fail_route_capture("native_raceline_object_pointer_invalid");
        return;
    }

    uint32_t begin = 0, end = 0;
    if (!read_u32(route_object, 0x04, begin) || !read_u32(route_object, 0x08, end) ||
        !pointer_shape(begin) || !pointer_shape(end) || end < begin) {
        fail_route_capture("native_raceline_bounds_unreadable");
        return;
    }
    const uint32_t byte_length = end - begin;
    if (byte_length % road_target::NATIVE_MARKER_STRIDE != 0) {
        fail_route_capture("native_raceline_extent_not_stride_aligned");
        return;
    }
    const uint32_t count = byte_length / road_target::NATIVE_MARKER_STRIDE;
    if (count != road_target::FRANCE1_MARKER_COUNT ||
        count > road_target::FRANCE1_MARKER_COUNT ||
        static_cast<uint64_t>(begin) + byte_length > UINT32_MAX) {
        fail_route_capture("native_raceline_count_or_extent_mismatch");
        return;
    }

    road_target::LiveSnapshot candidate{};
    candidate.count = count;
    candidate.stride = road_target::NATIVE_MARKER_STRIDE;
    candidate.position_offset = road_target::NATIVE_POSITION_OFFSET;
    candidate.race_generation = race_generation;
    candidate.owner_lifetime = owner_lifetime;
    candidate.native_route_object = route_object;
    candidate.native_position_begin = begin;
    candidate.native_position_end = end;
    candidate.recovery_manager = recovery_manager;
    candidate.native_thread_id = GetCurrentThreadId();
    candidate.source_native_live = true;
    candidate.exact_supported_course = true; // Published race certificates currently require France1.
    candidate.capture_owner_current = true;
    candidate.reason = "native_live_raceline_snapshot";

    for (uint32_t ordinal = 0; ordinal < count; ++ordinal) {
        const uint64_t record = static_cast<uint64_t>(begin) +
                                static_cast<uint64_t>(ordinal) * candidate.stride;
        const uint64_t position = record + candidate.position_offset;
        if (position + sizeof(road_target::Vec3) > static_cast<uint64_t>(begin) + byte_length ||
            position > UINT32_MAX) {
            fail_route_capture("native_raceline_position_outside_list_extent");
            return;
        }
        auto& marker = candidate.markers[ordinal];
        if (!safe_copy(&marker, reinterpret_cast<const void*>(static_cast<uint32_t>(position)),
                       sizeof(marker))) {
            fail_route_capture("native_raceline_position_unreadable");
            return;
        }
        if (!std::isfinite(marker.x) || !std::isfinite(marker.y) || !std::isfinite(marker.z)) {
            fail_route_capture("native_raceline_non_finite_position");
            return;
        }
    }
    std::array<road_target::Vec3, road_target::FRANCE1_MARKER_COUNT> verification_copy{};
    for (uint32_t ordinal = 0; ordinal < count; ++ordinal) {
        const uint64_t position = static_cast<uint64_t>(begin) +
            static_cast<uint64_t>(ordinal) * candidate.stride + candidate.position_offset;
        if (position > UINT32_MAX ||
            !safe_copy(&verification_copy[ordinal],
                       reinterpret_cast<const void*>(static_cast<uint32_t>(position)),
                       sizeof(verification_copy[ordinal]))) {
            fail_route_capture("native_raceline_verification_copy_unreadable");
            return;
        }
        if (std::memcmp(&verification_copy[ordinal], &candidate.markers[ordinal],
                        sizeof(road_target::Vec3)) != 0) {
            fail_route_capture("native_raceline_contents_changed_during_snapshot");
            return;
        }
    }
    uint32_t begin_after = 0, end_after = 0;
    if (!read_u32(route_object, 0x04, begin_after) || !read_u32(route_object, 0x08, end_after) ||
        begin_after != begin || end_after != end) {
        fail_route_capture("native_raceline_storage_changed_during_snapshot");
        return;
    }
    candidate.fingerprint = road_target::position_fingerprint(candidate.markers.data(), count);
    if (!candidate.fingerprint) {
        fail_route_capture("native_raceline_fingerprint_failed");
        return;
    }
    candidate.available = true;

    AcquireSRWLockExclusive(&probe.lock);
    if (!probe.route_context_valid ||
        probe.route_context_race_generation != race_generation ||
        probe.route_context_owner_lifetime != owner_lifetime) {
        if (probe.route_capture_attempts != UINT64_MAX) ++probe.route_capture_attempts;
        if (probe.route_capture_failures != UINT64_MAX) ++probe.route_capture_failures;
        probe.route_last_failure = "race_context_changed_during_native_snapshot";
        candidate.available = false;
        candidate.reason = probe.route_last_failure;
        probe.route_snapshot = candidate;
        ReleaseSRWLockExclusive(&probe.lock);
        return;
    }
    if (probe.route_capture_attempts != UINT64_MAX) ++probe.route_capture_attempts;
    if (probe.route_snapshot_sequence != UINT64_MAX) ++probe.route_snapshot_sequence;
    candidate.sequence = probe.route_snapshot_sequence;
    probe.route_snapshot = candidate;
    probe.route_last_failure = "none";
    ReleaseSRWLockExclusive(&probe.lock);
}

bool live_route_matches(const road_target::LiveSnapshot& expected,
                        uint32_t route_object, uint32_t recovery_manager) noexcept {
    if (!pointer_shape(route_object) || !pointer_shape(recovery_manager) ||
        route_object != expected.native_route_object ||
        recovery_manager != expected.recovery_manager ||
        expected.native_thread_id != GetCurrentThreadId()) return false;
    uint32_t begin = 0, end = 0;
    if (!read_u32(route_object, 0x04, begin) || !read_u32(route_object, 0x08, end) ||
        begin != expected.native_position_begin || end != expected.native_position_end ||
        end < begin || (end - begin) != road_target::FRANCE1_MARKER_COUNT * road_target::NATIVE_MARKER_STRIDE)
        return false;
    std::array<road_target::Vec3, road_target::FRANCE1_MARKER_COUNT> first{}, second{};
    for (uint32_t i = 0; i < road_target::FRANCE1_MARKER_COUNT; ++i) {
        const uint64_t position = static_cast<uint64_t>(begin) +
            static_cast<uint64_t>(i) * road_target::NATIVE_MARKER_STRIDE + road_target::NATIVE_POSITION_OFFSET;
        if (position > UINT32_MAX ||
            !safe_copy(&first[i], reinterpret_cast<const void*>(static_cast<uint32_t>(position)), sizeof(first[i])) ||
            std::memcmp(&first[i], &expected.markers[i], sizeof(first[i])) != 0 ||
            !safe_copy(&second[i], reinterpret_cast<const void*>(static_cast<uint32_t>(position)), sizeof(second[i])) ||
            std::memcmp(&first[i], &second[i], sizeof(first[i])) != 0) return false;
    }
    uint32_t begin_after = 0, end_after = 0;
    return read_u32(route_object, 0x04, begin_after) && read_u32(route_object, 0x08, end_after) &&
        begin_after == begin && end_after == end &&
        road_target::position_fingerprint(first.data(), first.size()) == expected.fingerprint;
}

bool read_native_links(uint32_t controller, NativeLinks& links) noexcept;
bool verify_road_adjust_context(uint32_t base) noexcept;
bool verify_native_adjustment_body(uint32_t base) noexcept;
bool read_native_word(uint32_t address, uint32_t& value) noexcept {
    return safe_copy(&value, reinterpret_cast<const void*>(address), sizeof(value));
}

bool unique_human_controller_idle(uint32_t& controller, uint32_t& backing,
                                 uint32_t& actor, uint64_t& identity_generation,
                                 VehicleOwnerEvidence* evidence = nullptr,
                                 const RaceCertificate* certificate = nullptr,
                                 uint32_t reset_manager = 0) noexcept {
    size_t used = 0, humans = 0;
    const Track* human_track = nullptr;
    controller = backing = actor = 0;
    identity_generation = 0;
    if (evidence) *evidence = VehicleOwnerEvidence{};
    for (const auto& track : probe.tracks) {
        if (!track.used) continue;
        ++used;
        NativeLinks observed{};
        // Inspect AI tracks too: a cached type must not hide a newly-human
        // controller. Changed links are never silently adopted by this gate.
        const bool readable = read_native_links(track.identity.controller, observed);
        if (track.identity.player_type != 1 && (!readable || observed.player_type != 1)) continue;
        ++humans;
        human_track = &track;
    }
    if (evidence) {
        evidence->tracked_controllers = used;
        evidence->human_controllers = humans;
        if (certificate) {
            evidence->race_certificate_current = probe.route_context_valid && certificate->valid &&
                probe.route_context_race_generation == certificate->race_generation &&
                probe.route_context_owner_lifetime == certificate->owner_lifetime;
            evidence->single_human_car = certificate->single_human_car_race;
            evidence->race_generation = certificate->race_generation;
            evidence->expected_race_generation = probe.route_context_race_generation;
            evidence->owner_lifetime = certificate->owner_lifetime;
            evidence->expected_owner_lifetime = probe.route_context_owner_lifetime;
            evidence->participant_count = certificate->participant_count;
            evidence->participant_index = certificate->human_participant_index;
            evidence->participant_identity_verified = certificate->human_participant_identity_verified;
            evidence->participant_player_type = certificate->human_participant_player_type;
            evidence->race_owner_actor = certificate->actor;
        }
    }
    if (humans != 1 || !human_track) return false;
    if (evidence) {
        evidence->physical_player_type = human_track->identity.player_type;
        evidence->pending_native_recovery = human_track->pending;
        evidence->cached_apply_flag_known = human_track->flag.known;
        evidence->cached_apply_flag_set = human_track->flag.set;
        evidence->track_generation = human_track->identity_generation;
    }
    NativeLinks current{};
    const bool links_read = read_native_links(human_track->identity.controller, current);
    const bool links_stable = links_read && same_identity(human_track->identity, current);
    uint8_t flag = 0xFF;
    const bool flag_read = links_stable && read_u8(current.backing, 0x33, flag);
    if (evidence) {
        evidence->controller = current.controller;
        evidence->backing = current.backing;
        evidence->physical_actor = current.actor;
        evidence->links_readable = links_read;
        evidence->links_stable = links_stable;
        evidence->current_track_generation = links_stable ? human_track->identity_generation : 0;
        evidence->current_apply_flag_readable = flag_read;
        evidence->current_apply_flag = flag;
        evidence->recovery = read_recovery_manager(reset_manager, 0, &read_native_word);
    }
    if (!links_stable || !flag_read || flag != 0 || human_track->pending) return false;
    controller = current.controller;
    backing = current.backing;
    actor = current.actor;
    identity_generation = human_track->identity_generation;
    return true;
}

void road_teleport_selection_observe(const RoadAdjustSaved* saved) noexcept {
    if (!saved || InterlockedCompareExchange(&probe.enabled, 0, 0) == 0 ||
        !probe.road_teleport_enabled) return;
    AcquireSRWLockExclusive(&probe.lock);
    if (!probe.road_teleport_enabled || !probe.installed || !batch_intact()) {
        if (probe.installed) disable_after_ownership_loss();
        ReleaseSRWLockExclusive(&probe.lock);
        return;
    }
    auto& request = probe.road_teleport;
    if (request.state != road_teleport::State::Armed) {
        ReleaseSRWLockExclusive(&probe.lock);
        return;
    }
    if (probe.road_teleport_selection_attempts != UINT64_MAX)
        ++probe.road_teleport_selection_attempts;

    road_teleport::NativeCallFacts facts{};
    facts.exact_build = probe.base == 0x00400000;
    facts.race_context_current = probe.route_context_valid &&
        probe.route_context_race_generation == request.race_generation &&
        probe.route_context_owner_lifetime == request.owner_lifetime;
    facts.race_generation = probe.route_context_race_generation;
    facts.owner_lifetime = probe.route_context_owner_lifetime;
    facts.reset_manager = saved->esi;
    facts.route_object = saved->route_object;
    facts.participant_index = saved->participant_index;
    facts.route_count = probe.route_snapshot.count;
    facts.route_fingerprint = probe.route_snapshot.fingerprint;
    facts.native_thread_id = GetCurrentThreadId();
    facts.now_tick_ms = GetTickCount64();
    uint32_t human_controller = 0, human_backing = 0, human_actor = 0;
    uint64_t human_identity_generation = 0;
    facts.unique_current_human_controller = unique_human_controller_idle(
        human_controller, human_backing, human_actor, human_identity_generation);
    facts.human_actor = human_actor;
    facts.human_controller = human_controller;
    facts.human_backing = human_backing;
    facts.human_identity_generation = human_identity_generation;
    facts.recovery = read_recovery_manager(saved->esi, saved->participant_index, &read_native_word);
    facts.native_selection_contract_verified = verify_native_adjustment_body(probe.base);
    facts.no_active_recovery = facts.unique_current_human_controller &&
        evaluate_recovery_manager(facts.recovery, RecoveryPhase::NativeSelection).accepted;
    facts.route_snapshot_current = probe.route_snapshot.available &&
        probe.route_snapshot.race_generation == request.race_generation &&
        probe.route_snapshot.owner_lifetime == request.owner_lifetime &&
        live_route_matches(probe.route_snapshot, saved->route_object, saved->esi);
    const uint32_t stack_argument_address = saved->saved_esp <= UINT32_MAX - 12u ? saved->saved_esp + 12u : 0;
    uint32_t marker_argument = UINT32_MAX;
    const bool stack_context_valid = saved->return_pc == probe.base + ROAD_ADJUST_CALL_VA + 5u - 0x00400000u &&
        saved->participant_index == 0 && saved->route_object == saved->edi &&
        stack_argument_address && safe_copy(&marker_argument,
            reinterpret_cast<const void*>(stack_argument_address), sizeof(marker_argument)) &&
        marker_argument == saved->marker_ordinal;
    // The return PC and arguments come from a verified callsite. If its live
    // stack shape differs, preserve the original marker and cancel the request.
    if (!stack_context_valid) facts.route_snapshot_current = false;

    const auto selected = road_teleport::select_native_destination(request, facts, marker_argument);
    if (selected.changed) {
        if (safe_copy(reinterpret_cast<void*>(stack_argument_address), &marker_argument,
                      sizeof(marker_argument))) {
            request.native_thread_id = facts.native_thread_id;
            if (probe.road_teleport_override_count != UINT64_MAX)
                ++probe.road_teleport_override_count;
        } else {
            road_teleport::cancel(request, "native_stack_argument_write_failed_stock_path_preserved");
            if (probe.road_teleport_stack_write_failures != UINT64_MAX)
                ++probe.road_teleport_stack_write_failures;
        }
    } else if (probe.road_teleport_stock_fallback_count != UINT64_MAX) {
        ++probe.road_teleport_stock_fallback_count;
    }
    ReleaseSRWLockExclusive(&probe.lock);
}

void road_teleport_selection_after(RoadAdjustSaved* saved) noexcept {
    if (!saved || !InterlockedCompareExchange(&probe.enabled, 0, 0)) return;
    AcquireSRWLockExclusive(&probe.lock);
    if (probe.road_teleport_enabled && probe.road_teleport.state == road_teleport::State::DestinationOverridden) {
        road_teleport::observe_native_adjustment(probe.road_teleport, saved->eax);
        // Post-call observation never substitutes an unadjusted progress marker
        // for the native result. The single-participant contract is proved before writing.
    }
    ReleaseSRWLockExclusive(&probe.lock);
}

bool read_native_links(uint32_t controller, NativeLinks& links) noexcept {
    links = {};
    links.controller = controller;
    return pointer_shape(controller) && read_u32(controller, 0x6C, links.handle) &&
        read_u32(links.handle, 0x14, links.handle_controller) &&
        read_u32(links.handle, 0x08, links.actor) &&
        read_u32(links.actor, 0x04, links.body) &&
        read_u32(controller, 0x74, links.backing) &&
        read_u32(links.handle, 0x0C, links.wheel_records) &&
        read_u32(links.handle, 0x00, links.player_type) && links_valid(links);
}

bool capture_snapshot(uint32_t controller, Snapshot& out) noexcept {
    out = Snapshot{};
    out.thread_id = GetCurrentThreadId();
    LARGE_INTEGER qpc{};
    if (QueryPerformanceCounter(&qpc)) out.qpc = static_cast<uint64_t>(qpc.QuadPart);
    capture_pause_state(out);

    auto& links = out.links;
    if (!read_native_links(controller, links)) {
        return false;
    }

    if (read_u8(links.backing, 0x33, out.apply_flag)) out.valid_mask |= 1u << 0;
    if (read_u8(controller, 0x13, out.controller_byte_13) &&
        read_u8(controller, 0x18, out.controller_byte_18)) out.valid_mask |= 1u << 1;
    if (read_bytes(links.backing, 0x34, out.transform_bits.data(),
                   sizeof(out.transform_bits))) out.valid_mask |= 1u << 2;
    if (read_bytes(links.body, 0xA0, out.current_position_bits.data(),
                   sizeof(out.current_position_bits))) out.valid_mask |= 1u << 3;
    if (read_bytes(links.body, 0x144, out.previous_position_bits.data(),
                   sizeof(out.previous_position_bits))) out.valid_mask |= 1u << 4;
    if (read_bytes(links.body, 0x11C, out.body_opaque_11c_130.data(),
                   sizeof(out.body_opaque_11c_130))) out.valid_mask |= 1u << 5;
    if (read_u8(links.body, 0x04, out.body_byte_04)) out.valid_mask |= 1u << 6;

    bool all_wheels = true;
    for (uint32_t i = 0; i < out.wheels.size(); ++i) {
        const uint64_t wide = static_cast<uint64_t>(links.wheel_records) +
                              static_cast<uint64_t>(i) * 0x188u;
        if (wide > UINT32_MAX) { all_wheels = false; continue; }
        auto& wheel = out.wheels[i];
        wheel.address = static_cast<uint32_t>(wide);
        const bool byte_ok = read_u8(wheel.address, 0x04, wheel.byte_04);
        const bool word_ok = read_u32(wheel.address, 0x120, wheel.word_120);
        wheel.valid = static_cast<uint8_t>((byte_ok ? 1u : 0u) | (word_ok ? 2u : 0u));
        if (!byte_ok || !word_ok) all_wheels = false;
    }
    if (all_wheels) out.valid_mask |= 1u << 7;
    return true;
}

Track* find_track(uint32_t controller) noexcept {
    for (auto& track : probe.tracks)
        if (track.used && track.identity.controller == controller) return &track;
    return nullptr;
}

Track* get_track(const Snapshot& snapshot) noexcept {
    if (auto* found = find_track(snapshot.links.controller)) {
        if (!same_identity(found->identity, snapshot.links)) {
            if (probe.road_teleport_enabled &&
                probe.road_teleport.human_controller == found->identity.controller &&
                probe.road_teleport.human_identity_generation == found->identity_generation)
                road_teleport::cancel(probe.road_teleport, "current_controller_identity_replaced");
            const uint64_t next_generation = found->identity_generation + 1;
            const uint64_t changes = found->identity_changes + 1;
            *found = Track{};
            found->used = true;
            found->identity = snapshot.links;
            found->identity_generation = next_generation;
            found->identity_changes = changes;
        }
        return found;
    }
    for (auto& track : probe.tracks) {
        if (!track.used) {
            track = Track{};
            track.used = true;
            track.identity = snapshot.links;
            track.identity_generation = 1;
            return &track;
        }
    }
    ++probe.dropped_tracks;
    return nullptr;
}

void append_event(Event&& event) noexcept {
    if (!reserve_bounded_slot(probe.event_count, probe.events.size())) {
        ++probe.dropped_events;
        return;
    }
    event.sequence = ++probe.event_sequence;
    probe.events[probe.event_count - 1] = event;
}

bool verify_bytes(uint32_t base, uint32_t va, const uint8_t* expected, size_t size) noexcept {
    if (va < 0x00400000 || !size || size > 32) return false;
    std::array<uint8_t, 32> actual{};
    return safe_copy(actual.data(), reinterpret_cast<const void*>(base + va - 0x00400000), size) &&
           context_bytes_match(expected, size, actual.data(), size);
}

const char* verify_contexts(uint32_t base) noexcept {
    const bool controller_ok = verify_bytes(base, CONTROLLER_CONTEXT_VA,
                                            CONTROLLER_CONTEXT.data(), CONTROLLER_CONTEXT.size());
    const bool begin_ok = controller_ok && verify_bytes(base, SUBSTEP_BEGIN_CONTEXT_VA,
                                                        SUBSTEP_BEGIN_CONTEXT.data(), SUBSTEP_BEGIN_CONTEXT.size());
    const bool tail_ok = controller_ok && begin_ok && verify_bytes(base, SUBSTEP_TAIL_CONTEXT_VA,
                                                                   SUBSTEP_TAIL_CONTEXT.data(), SUBSTEP_TAIL_CONTEXT.size());
    return context_failure_reason(controller_ok, begin_ok, tail_ok);
}

bool verify_route_getter_context(uint32_t base) noexcept {
    return verify_bytes(base, ROUTE_GETTER_CONTEXT_VA,
                        ROUTE_GETTER_CONTEXT.data(), ROUTE_GETTER_CONTEXT.size());
}

bool verify_native_adjustment_body(uint32_t base) noexcept {
    std::array<uint8_t, ROAD_ADJUST_BODY_SIZE> native{};
    uint32_t distance_limit = 0;
    // Complete body pins self-skip, threshold and unchanged-input return, not
    // just the patched CALL. Count == 1 and participant == 0 select that path.
    return base == 0x400000u && read_native_word(ROAD_ADJUST_DISTANCE_LIMIT_VA, distance_limit) &&
        distance_limit == ROAD_ADJUST_DISTANCE_LIMIT_BITS &&
        safe_copy(native.data(), reinterpret_cast<const void*>(base + ROAD_ADJUST_TARGET_VA - 0x400000u), native.size()) &&
        sha256_bytes(native.data(), native.size()) == ROAD_ADJUST_BODY_SHA256;
}
bool verify_road_adjust_context(uint32_t base) noexcept {
    return verify_native_adjustment_body(base) && verify_bytes(base, ROAD_ADJUST_CONTEXT_VA,
                        ROAD_ADJUST_CONTEXT.data(), ROAD_ADJUST_CONTEXT.size()) &&
        verify_bytes(base, ROAD_ADJUST_CALL_VA,
                     ROAD_ADJUST_CALL.data(), ROAD_ADJUST_CALL.size());
}

const char* verify_route_getter_abi(uint32_t base) noexcept {
    if (!verify_bytes(base, ROUTE_GETTER_CALLEE_ENTRY_VA,
                      ROUTE_GETTER_CALLEE_ENTRY_CONTEXT.data(),
                      ROUTE_GETTER_CALLEE_ENTRY_CONTEXT.size()))
        return "route_getter_entry_abi_mismatch";
    if (!verify_bytes(base, ROUTE_GETTER_SUCCESS_RET_VA,
                      ROUTE_GETTER_RET4_CONTEXT.data(), ROUTE_GETTER_RET4_CONTEXT.size()))
        return "route_getter_success_ret4_mismatch";
    if (!verify_bytes(base, ROUTE_GETTER_NULL_RET_VA,
                      ROUTE_GETTER_RET4_CONTEXT.data(), ROUTE_GETTER_RET4_CONTEXT.size()))
        return "route_getter_null_ret4_mismatch";
    return nullptr;
}

void configure_call(size_t index, uint32_t base, uint32_t site_va, uint32_t target_va,
                    uintptr_t bridge, const std::array<uint8_t, 5>& expected) noexcept {
    auto& unit = probe.batch.sites[index];
    unit.address = reinterpret_cast<void*>(base + site_va - 0x00400000);
    unit.size = 5;
    for (size_t i = 0; i < expected.size(); ++i) unit.original[i] = expected[i];
    std::array<uint8_t, 5> encoded{};
    if (!encode_relative_call(site_va, static_cast<uint32_t>(bridge), encoded)) {
        // The production callsites and Win32 proxy share the 32-bit address space.
        unit.size = 0;
        return;
    }
    // The target in the EXE is intentionally checked separately from the
    // bridge displacement. This catches a mistaken site/target pairing.
    const uint32_t decoded_target = site_va + 5u +
        static_cast<uint32_t>(static_cast<int32_t>(
            static_cast<uint32_t>(expected[1]) |
            (static_cast<uint32_t>(expected[2]) << 8) |
            (static_cast<uint32_t>(expected[3]) << 16) |
            (static_cast<uint32_t>(expected[4]) << 24)));
    if (expected[0] != 0xE8 || decoded_target != target_va) {
        unit.size = 0;
        return;
    }
    for (size_t i = 0; i < encoded.size(); ++i) unit.replacement[i] = encoded[i];
}

bool exchange_inline(InlinePatchUnit& unit, bool installing) noexcept {
    return exchange_physics_inline(memory,unit,installing,probe.clear_writer_batch.rollback_verified);
}

bool install_inline_batch() noexcept {
    for (size_t i = 0; i < probe.clear_writer_batch.count; ++i) {
        if (!exchange_inline(probe.clear_writer_batch.sites[i], true)) {
            for (size_t j = i; j > 0; --j) {
                auto& prior = probe.clear_writer_batch.sites[j - 1];
                if (prior.owned) exchange_inline(prior, false);
            }
            return false;
        }
    }
    return true;
}

bool remove_inline_batch() noexcept {
    bool okay = true;
    for (size_t i = probe.clear_writer_batch.count; i > 0; --i) {
        auto& site = probe.clear_writer_batch.sites[i - 1];
        if (site.owned && !exchange_inline(site, false)) okay = false;
    }
    return okay;
}

const char* verify_clear_writer_contexts(uint32_t base) noexcept {
    const bool gate_ok = verify_bytes(base, CLEAR_GATE_PATCH_VA,
                                      CLEAR_GATE_CONTEXT.data(), CLEAR_GATE_CONTEXT.size());
    const bool recovery_ok = gate_ok && verify_bytes(base, CLEAR_RECOVERY_PATCH_VA,
                                      CLEAR_RECOVERY_CONTEXT.data(), CLEAR_RECOVERY_CONTEXT.size());
    const bool timer_ok = recovery_ok && verify_bytes(base, CLEAR_TIMER_PATCH_VA,
                                      CLEAR_TIMER_CONTEXT.data(), CLEAR_TIMER_CONTEXT.size());
    if (const char* reason = clear_context_failure_reason(gate_ok, recovery_ok, timer_ok)) return reason;
    if (!verify_bytes(base, PUBLISH_PATCH_VA, PUBLISH_CONTEXT.data(), PUBLISH_CONTEXT.size())) return "publication_context_mismatch";
    if (!verify_bytes(base, MATRIX_COMPLETE_PATCH_VA, MATRIX_COMPLETE_CONTEXT.data(), MATRIX_COMPLETE_CONTEXT.size())) return "matrix_completion_context_mismatch";
    static constexpr uint8_t input_owner[] = {0x8B,0x41,0x2C,0x8A,0x51,0x78,0x88,0x50,0x33,0x8B,0x41,0x2C};
    if (!verify_bytes(base, INPUT_FLAG_PATCH_VA - 6, input_owner, sizeof(input_owner))) return "input_flag_context_mismatch";
    if (!verify_bytes(base, RESTORE_FLAG_PATCH_VA, RESTORE_FLAG_CONTEXT.data(), RESTORE_FLAG_CONTEXT.size()) ||
        !verify_bytes(base, 0x004D0580, RESTORE_CALLEE_CONTEXT.data(), RESTORE_CALLEE_CONTEXT.size())) return "restore_flag_context_mismatch";
    static constexpr uint8_t ret4[] = {0xC2,0x04,0x00};
    if (!verify_bytes(base, 0x004D0597, ret4, sizeof(ret4))) return "restore_callee_ret4_mismatch";
    static constexpr uint8_t matrix_call[] = {0x8D,0x4D,0x34,0xE8,0x2F,0x7D,0xF3,0xFF};
    if (!verify_bytes(base, 0x004CD129, matrix_call, sizeof(matrix_call))) return "matrix_copy_target_mismatch";
    for (size_t offset=0;offset<MATRIX_COPY_CONTEXT.size();offset+=32) {
        const size_t count=(std::min)(size_t{32},MATRIX_COPY_CONTEXT.size()-offset);
        if (!verify_bytes(base,0x00404E60+static_cast<uint32_t>(offset),MATRIX_COPY_CONTEXT.data()+offset,count)) return "complete_matrix_copy_context_mismatch";
    }
    return nullptr;
}

void configure_clear_writer_site(size_t index, uint32_t base, uint32_t site_va,
                                 uintptr_t bridge, const uint8_t* expected,
                                 size_t size) noexcept {
    if (index >= probe.clear_writer_batch.sites.size() || !expected ||
        (size != 6 && size != 7 && size != 8)) return;
    auto& unit = probe.clear_writer_batch.sites[index];
    unit.address = reinterpret_cast<void*>(base + site_va - 0x00400000);
    unit.size = size;
    std::copy_n(expected, size, unit.original.begin());
    std::array<uint8_t, 5> encoded{};
    if (!encode_relative_call(site_va, static_cast<uint32_t>(bridge), encoded)) {
        unit.size = 0;
        return;
    }
    std::copy(encoded.begin(), encoded.end(), unit.replacement.begin());
    for (size_t i = encoded.size(); i < size; ++i) unit.replacement[i] = 0x90;
}

void configure_clear_writer_batch(uint32_t base) noexcept {
    probe.clear_writer_batch = InlinePatchBatch{};
    probe.clear_writer_batch.count = 7;
    configure_clear_writer_site(0, base, CLEAR_GATE_PATCH_VA,
        reinterpret_cast<uintptr_t>(&physics_probe_clear_gate_bridge),
        CLEAR_GATE_CONTEXT.data(), CLEAR_GATE_CONTEXT.size());
    configure_clear_writer_site(1, base, CLEAR_RECOVERY_PATCH_VA,
        reinterpret_cast<uintptr_t>(&physics_probe_clear_recovery_bridge),
        CLEAR_RECOVERY_CONTEXT.data(), CLEAR_RECOVERY_CONTEXT.size());
    configure_clear_writer_site(2, base, CLEAR_TIMER_PATCH_VA,
        reinterpret_cast<uintptr_t>(&physics_probe_clear_timer_bridge),
        CLEAR_TIMER_CONTEXT.data(), CLEAR_TIMER_CONTEXT.size());
    configure_clear_writer_site(3, base, PUBLISH_PATCH_VA,
        reinterpret_cast<uintptr_t>(&physics_probe_publish_bridge), PUBLISH_CONTEXT.data(), PUBLISH_CONTEXT.size());
    configure_clear_writer_site(4, base, MATRIX_COMPLETE_PATCH_VA,
        reinterpret_cast<uintptr_t>(&physics_probe_matrix_complete_bridge), MATRIX_COMPLETE_CONTEXT.data(), MATRIX_COMPLETE_CONTEXT.size());
    configure_clear_writer_site(5, base, INPUT_FLAG_PATCH_VA,
        reinterpret_cast<uintptr_t>(&physics_probe_input_flag_bridge), INPUT_FLAG_CONTEXT.data(), INPUT_FLAG_CONTEXT.size());
    configure_clear_writer_site(6, base, RESTORE_FLAG_PATCH_VA,
        reinterpret_cast<uintptr_t>(&physics_probe_restore_flag_bridge), RESTORE_FLAG_CONTEXT.data(), RESTORE_FLAG_CONTEXT.size());

}

bool batch_intact() noexcept {
    const size_t expected_count = 3 +
        (InterlockedCompareExchange(&probe.route_preview_enabled, 0, 0) ? 1u : 0u) +
        (probe.road_teleport_enabled ? 1u : 0u);
    if (probe.batch.count != expected_count || probe.clear_writer_batch.count != 7) return false;
    for (size_t i = 0; i < probe.batch.count; ++i) {
        const auto& site = probe.batch.sites[i];
        std::array<uint8_t, 5> actual{};
        if (!site.owned || !memory.read(actual.data(), site.address, site.size) ||
            std::memcmp(actual.data(), site.replacement.data(), site.size) != 0) return false;
    }
    for (size_t i = 0; i < probe.clear_writer_batch.count; ++i) {
        const auto& site = probe.clear_writer_batch.sites[i];
        std::array<uint8_t, 8> actual{};
        if (!site.owned || !memory.read(actual.data(), site.address, site.size) ||
            std::memcmp(actual.data(), site.replacement.data(), site.size) != 0) return false;
    }
    return true;
}

void disable_after_ownership_loss() noexcept {
    probe.patch_intact = false;
    probe.reason = "hook_ownership_lost_observation_disabled";
    probe.route_last_failure = "hook_ownership_lost";
    road_teleport::cancel(probe.road_teleport, "physics_probe_hook_ownership_lost");
    InterlockedExchange(&probe.enabled, 0);
    InterlockedExchange(&probe.substep_window_active, 0);
}

bool same_preview_configuration(const PhysicsProbeSettings& settings) noexcept {
    const bool enabled = InterlockedCompareExchange(&probe.route_preview_enabled, 0, 0) != 0;
    return enabled == settings.road_target_preview_enabled &&
        (!enabled || probe.route_preview_radius == settings.road_target_preview_radius) &&
        probe.road_teleport_enabled == settings.road_teleport_enabled &&
        (!probe.road_teleport_enabled ||
         (probe.road_teleport_max_distance == settings.road_teleport_max_distance &&
          probe.road_teleport_arm_timeout_seconds == settings.road_teleport_arm_timeout_seconds));
}

#include "physics_transaction_capture.inc"

road_teleport::ConsumerEvent consumer_event(const Track& track, const Snapshot& sample) noexcept {
    road_teleport::ConsumerEvent out{};
    out.race_current = probe.route_context_valid;
    out.race_generation = probe.route_context_race_generation;
    out.owner_lifetime = probe.route_context_owner_lifetime;
    out.identity_generation = track.identity_generation;
    out.thread = sample.thread_id; out.controller = sample.links.controller;
    out.backing = sample.links.backing; out.actor = sample.links.actor;
    out.owner_current = same_identity(track.identity, sample.links);
    out.human = sample.links.player_type == 1;
    out.flag_readable = (sample.valid_mask & 1u) != 0;
    out.matrix_readable = (sample.valid_mask & (1u << 2)) != 0;
    out.flag = sample.apply_flag; out.matrix = sample.transform_bits;
    return out;
}

void dev_teleport_apply_before_controller(uint32_t controller) noexcept;

uint32_t __cdecl controller_before(uint32_t controller) noexcept {
    if (InterlockedCompareExchange(&probe.enabled, 0, 0) == 0) return 0;
    dev_teleport_apply_before_controller(controller);
    Snapshot before{};
    if (!capture_snapshot(controller, before) || !(before.valid_mask & 1u)) {
        InterlockedIncrement(&probe.invalid_snapshots);
        return 0;
    }

    AcquireSRWLockExclusive(&probe.lock);
    if (InterlockedCompareExchange(&probe.enabled, 0, 0) == 0) {
        ReleaseSRWLockExclusive(&probe.lock);
        return 0;
    }
    if (!batch_intact()) {
        disable_after_ownership_loss();
        ReleaseSRWLockExclusive(&probe.lock);
        return 0;
    }
    if (before.pause_state_known && before.pause_paused &&
        probe.controller_calls_while_paused != UINT64_MAX)
        ++probe.controller_calls_while_paused;
    Track* track = get_track(before);
    if (!track) {
        ReleaseSRWLockExclusive(&probe.lock);
        return 0;
    }
    if (track->pending) {
        ++track->overlap_calls;
        ReleaseSRWLockExclusive(&probe.lock);
        return 0;
    }

    if (probe.road_teleport_enabled) {
        auto settled = consumer_event(*track, before);
        road_teleport::handle_settled_event(probe.road_teleport, settled);
    }

    const FlagEvent flag_event = observe_flag(track->flag, before.apply_flag);
    if (flag_event == FlagEvent::FirstSetObserved || flag_event == FlagEvent::SetEdge) {
        track->interval_consumer_calls = 0;
        if (InterlockedCompareExchange(&probe.substep_window_active, 0, 0) == 0) {
            probe.substep_budget = SUBSTEP_WINDOW_EVENTS;
            InterlockedExchange(&probe.substep_window_active, 1);
            ++probe.substep_windows;
        }
    }

    if ((before.valid_mask & 1u) && before.apply_flag) {
        ++track->interval_consumer_calls;
        track->last_flagged_consumer_qpc = before.qpc;
        track->last_flagged_consumer_thread = before.thread_id;
    }

    track->pending = true;
    track->pending_thread = before.thread_id;
    track->pending_event = flag_event;
    track->pending_before = before;
    track->pending_has_baseline = track->has_last &&
        (flag_event == FlagEvent::FirstSetObserved || flag_event == FlagEvent::SetEdge);
    if (track->pending_has_baseline) track->pending_baseline = track->last;
    ReleaseSRWLockExclusive(&probe.lock);
    return controller;
}

void __cdecl controller_after(uint32_t controller) noexcept {
    if (!controller || InterlockedCompareExchange(&probe.enabled, 0, 0) == 0) return;
    Snapshot after{};
    const bool after_valid = capture_snapshot(controller, after);

    AcquireSRWLockExclusive(&probe.lock);
    if (InterlockedCompareExchange(&probe.enabled, 0, 0) == 0) {
        ReleaseSRWLockExclusive(&probe.lock);
        return;
    }
    if (!batch_intact()) {
        disable_after_ownership_loss();
        ReleaseSRWLockExclusive(&probe.lock);
        return;
    }
    Track* track = find_track(controller);
    if (!track || !track->pending || track->pending_thread != GetCurrentThreadId()) {
        if (track) ++track->overlap_calls;
        if (!after_valid) InterlockedIncrement(&probe.invalid_snapshots);
        ReleaseSRWLockExclusive(&probe.lock);
        return;
    }

    const uint64_t candidate = transaction_consumer(track->pending_before, after, after_valid);
    if (probe.road_teleport_enabled) {
        auto consumed = consumer_event(*track, track->pending_before);
        consumed.owner_current = consumed.owner_current && after_valid &&
            same_identity(track->pending_before.links, after.links);
        consumed.chassis_readable = after_valid && (after.valid_mask & (1u << 3));
        std::memcpy(&consumed.chassis_after.x, &after.current_position_bits[0], sizeof(float));
        std::memcpy(&consumed.chassis_after.y, &after.current_position_bits[1], sizeof(float));
        std::memcpy(&consumed.chassis_after.z, &after.current_position_bits[2], sizeof(float));
        consumed.active_consumer_calls = track->interval_consumer_calls;
        consumed.transaction_candidate = candidate;
        road_teleport::handle_consumer_event(probe.road_teleport, consumed);
    }
    if (track->pending_event != FlagEvent::None) {
        Event event{};
        event.kind = EventKind::Controller;
        event.flag_event = track->pending_event;
        event.has_before = true;
        event.before = track->pending_before;
        event.has_after = after_valid;
        if (after_valid) event.after = after;
        event.has_baseline = track->pending_has_baseline;
        if (event.has_baseline) event.baseline = track->pending_baseline;
        append_event(std::move(event));
    }
    if (after_valid) {
        track->last = after;
        track->has_last = true;
        // Keep the flag tracker at its pre-call state so a clear that occurs
        // between controller iterations is visible as a transition next time.
    } else {
        InterlockedIncrement(&probe.invalid_snapshots);
        track->has_last = false;
    }
    track->pending = false;
    track->pending_thread = 0;
    track->pending_event = FlagEvent::None;
    track->pending_has_baseline = false;
    ReleaseSRWLockExclusive(&probe.lock);
}

size_t capture_manager(uint32_t manager, Snapshot* output, size_t capacity) noexcept {
    uint32_t begin = 0, end = 0;
    if (!pointer_shape(manager) || !read_u32(manager, 0x18, begin) ||
        !read_u32(manager, 0x1C, end) || !pointer_shape(begin) || end < begin ||
        ((end - begin) & 3u) != 0) {
        InterlockedIncrement(&probe.invalid_managers);
        return 0;
    }
    const uint32_t count = (end - begin) / 4;
    if (count > MAX_TRACKS || count > capacity) {
        InterlockedIncrement(&probe.invalid_managers);
        return 0;
    }
    size_t used = 0;
    for (uint32_t i = 0; i < count; ++i) {
        uint32_t handle = 0, controller = 0;
        if (!read_u32(begin + i * 4, 0, handle) || !pointer_shape(handle) ||
            !read_u32(handle, 0x14, controller) || !pointer_shape(controller)) {
            InterlockedIncrement(&probe.invalid_snapshots);
            continue;
        }
        Snapshot snapshot{};
        if (!capture_snapshot(controller, snapshot) || snapshot.links.handle != handle) {
            InterlockedIncrement(&probe.invalid_snapshots);
            continue;
        }
        snapshot.participant_index = static_cast<int32_t>(i);
        output[used++] = snapshot;
    }
    return used;
}

void substep_observe(EventKind kind, uint32_t manager, uint32_t loop_remaining) noexcept {
    if (InterlockedCompareExchange(&probe.enabled, 0, 0) == 0 ||
        InterlockedCompareExchange(&probe.substep_window_active, 0, 0) == 0) return;
    std::array<Snapshot, MAX_TRACKS> snapshots{};
    const size_t count = capture_manager(manager, snapshots.data(), snapshots.size());

    AcquireSRWLockExclusive(&probe.lock);
    if (InterlockedCompareExchange(&probe.enabled, 0, 0) == 0 ||
        InterlockedCompareExchange(&probe.substep_window_active, 0, 0) == 0) {
        ReleaseSRWLockExclusive(&probe.lock);
        return;
    }
    if (!batch_intact()) {
        disable_after_ownership_loss();
        ReleaseSRWLockExclusive(&probe.lock);
        return;
    }
    Event event{};
    event.kind = kind;
    event.manager = manager;
    event.loop_remaining = loop_remaining;
    event.participant_count = count;
    for (size_t i = 0; i < count; ++i) event.participants[i] = snapshots[i];
    append_event(std::move(event));
    ++probe.substep_events;
    bool observed_paused = false;
    for (size_t i = 0; i < count; ++i)
        observed_paused = observed_paused ||
            (snapshots[i].pause_state_known && snapshots[i].pause_paused);
    if (observed_paused && probe.substep_phase_records_while_paused != UINT64_MAX)
        ++probe.substep_phase_records_while_paused;
    if (probe.substep_budget) --probe.substep_budget;
    if (!probe.substep_budget || probe.event_count >= probe.events.size()) {
        InterlockedExchange(&probe.substep_window_active, 0);
    }
    ReleaseSRWLockExclusive(&probe.lock);
}

extern "C" void __cdecl physics_probe_transaction_observe(const uint32_t* saved, uint32_t site, uint32_t after) noexcept {
    gfx2::transaction_inline(saved,site,after!=0);
}
extern "C" uint32_t __cdecl physics_probe_controller_before(uint32_t controller) noexcept {
    return gfx2::controller_before(controller);
}
extern "C" void __cdecl physics_probe_controller_after(uint32_t controller) noexcept {
    gfx2::controller_after(controller);
}
extern "C" void __cdecl physics_probe_substep(uint32_t phase, uint32_t manager,
                                               uint32_t loop_remaining) noexcept {
    EventKind kind = EventKind::SubstepBeginBefore;
    switch (phase) {
    case 1: kind = EventKind::SubstepBeginAfter; break;
    case 2: kind = EventKind::SubstepTailBefore; break;
    case 3: kind = EventKind::SubstepTailAfter; break;
    default: break;
    }
    gfx2::substep_observe(kind, manager, loop_remaining);
}

extern "C" void __cdecl physics_probe_route_after_getter(uint32_t route_object,
                                                          uint32_t recovery_manager) noexcept {
    gfx2::capture_live_route(route_object, recovery_manager);
}

extern "C" __declspec(naked) void physics_probe_route_getter_bridge() {
    __asm {
        // The native getter's input object is ECX; EAX is dead on entry.
        // Forward a duplicate of the original stack argument to its ret 4.
        push dword ptr [esp + 4]
        mov eax, 004E4D20h
        call eax
        // Native ret 4 returns ESP to this bridge's original entry stack.
        // Preserve the full native result around the read-only observer.
        pushfd
        pushad
        mov eax, dword ptr [esp + 28]
        mov edx, dword ptr [esp + 4]
        push edx
        push eax
        call physics_probe_route_after_getter
        add esp, 8
        popad
        popfd
        // Consume the caller's original argument exactly as native ret 4 did.
        ret 4
    }
}

extern "C" void __cdecl physics_probe_clear_writer_observe(uint32_t store_va,
                                                             uint32_t entry_object,
                                                             uint32_t native_store_value) noexcept {
    if (InterlockedCompareExchange(&probe.enabled, 0, 0) == 0) return;
    ClearWriterEvent event{};
    event.store_va = store_va;
    event.entry_object = entry_object;
    event.thread_id = GetCurrentThreadId();
    event.native_store_value = static_cast<uint8_t>(native_store_value);
    const uint64_t now = GetTickCount64();
    AcquireSRWLockShared(&probe.lock);
    const PauseStateSample sample{probe.pause_state_known, probe.pause_paused,
                                  probe.pause_sample_tick_ms};
    ReleaseSRWLockShared(&probe.lock);
    const auto pause = pause_state_at(sample, now, 500);
    event.pause_state_known = pause.known;
    event.pause_paused = pause.paused;
    event.pause_sample_age_ms = pause.age_ms;
    LARGE_INTEGER qpc{};
    if (QueryPerformanceCounter(&qpc)) event.qpc = static_cast<uint64_t>(qpc.QuadPart);
    uint32_t backing = 0;
    if (pointer_shape(entry_object) && read_u32(entry_object, 0x08, backing) &&
        pointer_shape(backing) && read_u8(backing, 0x33, event.flag_before)) {
        event.backing = backing;
        event.backing_valid = true;
    }

    AcquireSRWLockExclusive(&probe.lock);
    if (InterlockedCompareExchange(&probe.enabled, 0, 0) != 0) {
        if (!batch_intact()) {
            disable_after_ownership_loss();
        } else {
            const auto decision = observe_clear_store(probe.clear_capture,
                clear_writer(store_va), event.backing_valid, event.flag_before,
                static_cast<uint8_t>(event.native_store_value));
            if (event.pause_state_known && event.pause_paused &&
                probe.clear_writes_while_paused != UINT64_MAX)
                ++probe.clear_writes_while_paused;
            if (!decision.retained) {
                ReleaseSRWLockExclusive(&probe.lock);
                return;
            }
            event.observation = decision.observation;
            event.sequence = ++probe.clear_writer_event_sequence;
            event.race_context_valid = probe.route_context_valid;
            event.race_generation = probe.route_context_race_generation;
            event.owner_lifetime = probe.route_context_owner_lifetime;
            size_t owner_matches = 0;
            for (const auto& track : probe.tracks) {
                if (track.used && event.backing_valid && track.identity.backing == backing) {
                    ++owner_matches;
                    event.owner_known = true;
                    event.player_type = track.identity.player_type;
                    event.controller = track.identity.controller;
                    event.owner_identity_generation = track.identity_generation;
                    event.interval_consumer_calls = track.interval_consumer_calls;
                    event.last_flagged_consumer_qpc = track.last_flagged_consumer_qpc;
                    event.last_flagged_consumer_thread = track.last_flagged_consumer_thread;
                    event.consumer_in_progress = track.pending;
                    NativeLinks current{};
                    event.owner_links_current = read_native_links(track.identity.controller, current) &&
                        same_identity(track.identity, current);
                }
            }
            if (owner_matches != 1) {
                event.owner_known = false;
                event.owner_links_current = false;
                event.controller = 0;
                event.player_type = 0;
                event.owner_identity_generation = 0;
                event.interval_consumer_calls = 0;
                event.last_flagged_consumer_qpc = 0;
                event.last_flagged_consumer_thread = 0;
                event.consumer_in_progress = false;
            }
            probe.clear_writer_events[decision.slot] = event;
        }
    }
    ReleaseSRWLockExclusive(&probe.lock);
}

extern "C" { uintptr_t physics_probe_restore_target = 0x004D0580; }
#include "physics_transaction_bridges.inc"

extern "C" __declspec(naked) void physics_probe_controller_bridge() {
    __asm {
        pushfd
        pushad
        mov eax, ecx
        push eax
        call physics_probe_controller_before
        add esp, 4
        mov dword ptr [esp + 12], eax
        popad
        popfd
        push dword ptr [esp - 24]
        mov eax, 00444AE0h
        call eax
        pushfd
        pushad
        mov eax, dword ptr [esp + 36]
        push eax
        call physics_probe_controller_after
        add esp, 4
        popad
        popfd
        add esp, 4
        ret
    }
}

extern "C" __declspec(naked) void physics_probe_substep_begin_bridge() {
    __asm {
        pushfd
        pushad
        mov eax, ebx
        push eax
        push ecx
        push 0
        call physics_probe_substep
        add esp, 12
        popad
        popfd
        mov eax, 0043F650h
        call eax
        pushfd
        pushad
        mov eax, ebx
        push eax
        mov eax, esi
        push eax
        push 1
        call physics_probe_substep
        add esp, 12
        popad
        popfd
        ret
    }
}

extern "C" __declspec(naked) void physics_probe_substep_tail_bridge() {
    __asm {
        pushfd
        pushad
        mov eax, ebx
        push eax
        push ecx
        push 2
        call physics_probe_substep
        add esp, 12
        popad
        popfd
        mov eax, 0043FE00h
        call eax
        pushfd
        pushad
        mov eax, ebx
        push eax
        mov eax, esi
        push eax
        push 3
        call physics_probe_substep
        add esp, 12
        popad
        popfd
        ret
    }
}

const char* owner_name(uint32_t player_type) noexcept {
    switch (owner_class(player_type)) {
    case OwnerClass::HumanCandidate: return "human_candidate";
    case OwnerClass::AiCandidate: return "ai_candidate";
    default: return "unknown";
    }
}

const char* event_name(EventKind kind) noexcept {
    switch (kind) {
    case EventKind::Controller: return "controller_transform_consumer";
    case EventKind::SubstepBeginBefore: return "substep_begin_before_previous_sync";
    case EventKind::SubstepBeginAfter: return "substep_begin_after_previous_sync";
    case EventKind::SubstepTailBefore: return "substep_tail_before_final_stage";
    case EventKind::SubstepTailAfter: return "substep_tail_after_final_stage";
    default: return "unknown";
    }
}

std::string hex32(uint32_t value) {
    char text[11]{};
    sprintf_s(text, "0x%08X", value);
    return text;
}

std::string hex64(uint64_t value) {
    char text[19]{};
    sprintf_s(text, "0x%016llX", static_cast<unsigned long long>(value));
    return text;
}

void append_words(std::ostringstream& out, const uint32_t* words, size_t count) {
    out << '[';
    for (size_t i = 0; i < count; ++i) {
        if (i) out << ',';
        out << quote(hex32(words[i]));
    }
    out << ']';
}

void append_snapshot(std::ostringstream& out, const Snapshot& s) {
    out << "{\"identity_links_valid\":" << (links_valid(s.links) ? "true" : "false")
        << ",\"controller\":" << quote(hex32(s.links.controller))
        << ",\"handle\":" << quote(hex32(s.links.handle))
        << ",\"actor\":" << quote(hex32(s.links.actor))
        << ",\"body\":" << quote(hex32(s.links.body))
        << ",\"backing\":" << quote(hex32(s.links.backing))
        << ",\"wheel_records\":" << quote(hex32(s.links.wheel_records))
        << ",\"player_type\":" << s.links.player_type
        << ",\"owner_candidate\":" << quote(owner_name(s.links.player_type))
        << ",\"participant_index\":";
    if (s.participant_index < 0) out << "null"; else out << s.participant_index;
    out << ",\"thread_id\":" << s.thread_id << ",\"qpc\":" << s.qpc
        << ",\"pause_state_known\":" << (s.pause_state_known ? "true" : "false")
        << ",\"pause_state\":" << quote(s.pause_state_known ? (s.pause_paused ? "paused" : "running") : "unknown")
        << ",\"pause_sample_age_ms\":";
    if (s.pause_state_known) out << s.pause_sample_age_ms; else out << "null";
    out << ",\"valid_mask\":" << s.valid_mask
        << ",\"apply_flag_P_plus_0x33\":" << static_cast<unsigned>(s.apply_flag)
        << ",\"controller_byte_0x13\":" << static_cast<unsigned>(s.controller_byte_13)
        << ",\"controller_byte_0x18\":" << static_cast<unsigned>(s.controller_byte_18)
        << ",\"body_byte_0x04\":" << static_cast<unsigned>(s.body_byte_04)
        << ",\"transform_P_plus_0x34_raw_dwords\":";
    append_words(out, s.transform_bits.data(), s.transform_bits.size());
    out << ",\"body_current_position_0xA0_raw_dwords\":";
    append_words(out, s.current_position_bits.data(), s.current_position_bits.size());
    out << ",\"body_previous_position_0x144_raw_dwords\":";
    append_words(out, s.previous_position_bits.data(), s.previous_position_bits.size());
    out << ",\"body_opaque_0x11C_to_0x130_raw_dwords\":";
    append_words(out, s.body_opaque_11c_130.data(), s.body_opaque_11c_130.size());
    out << ",\"wheels\":[";
    for (size_t i = 0; i < s.wheels.size(); ++i) {
        if (i) out << ',';
        const auto& wheel = s.wheels[i];
        out << "{\"address\":" << quote(hex32(wheel.address))
            << ",\"byte_0x04\":" << static_cast<unsigned>(wheel.byte_04)
            << ",\"raw_word_0x120\":" << quote(hex32(wheel.word_120))
            << ",\"valid_mask\":" << static_cast<unsigned>(wheel.valid) << '}';
    }
    out << "]}";
}

void write_event(const Event& event) noexcept {
    try {
        std::ostringstream out;
        out << "{\"type\":\"physics_probe_event\",\"phase\":\"ROAD-TRANSACTION-CORRELATION-1\",\"sequence\":" << event.sequence
            << ",\"event\":" << quote(event_name(event.kind));
        if (event.kind == EventKind::Controller) {
            out << ",\"flag_event\":" << quote(flag_event_name(event.flag_event))
                << ",\"before\":";
            append_snapshot(out, event.before);
            out << ",\"after\":";
            if (event.has_after) append_snapshot(out, event.after); else out << "null";
            out << ",\"baseline_before_flag\":";
            if (event.has_baseline) append_snapshot(out, event.baseline); else out << "null";
        } else {
            out << ",\"manager\":" << quote(hex32(event.manager))
                << ",\"loop_remaining\":" << event.loop_remaining
                << ",\"participants\":[";
            for (size_t i = 0; i < event.participant_count; ++i) {
                if (i) out << ',';
                append_snapshot(out, event.participants[i]);
            }
            out << ']';
        }
        out << '}';
        session().write(out.str());
    } catch (...) {}
}

void write_clear_writer_event(const ClearWriterEvent& event) noexcept {
    try {
        std::ostringstream out;
        out << "{\"type\":\"physics_probe_clear_writer_event\",\"phase\":\"ROAD-TRANSACTION-CORRELATION-1\",\"sequence\":" << event.sequence
            << ",\"capture_policy\":\"transition_priority_v1\""
            << ",\"observation\":" << quote(store_observation_name(event.observation))
            << ",\"writer\":" << quote(clear_writer_name(clear_writer(event.store_va)))
            << ",\"store_va\":" << quote(hex32(event.store_va))
            << ",\"observation_phase\":\"before_original_store\""
            << ",\"entry_object\":" << quote(hex32(event.entry_object))
            << ",\"backing\":";
        if (event.backing_valid) out << quote(hex32(event.backing)); else out << "null";
        out << ",\"backing_valid\":" << (event.backing_valid ? "true" : "false")
            << ",\"apply_flag_before\":";
        if (event.backing_valid) out << static_cast<unsigned>(event.flag_before); else out << "null";
        out << ",\"native_store_value\":" << event.native_store_value
            << ",\"owner_known\":" << (event.owner_known ? "true" : "false")
            << ",\"player_type\":";
        if (event.owner_known) out << event.player_type; else out << "null";
        out << ",\"owner_links_current\":" << (event.owner_links_current ? "true" : "false")
            << ",\"owner_relation\":" << quote(!event.owner_known ? "unattributed" :
                !event.owner_links_current ? "historical_links_only" :
                event.player_type == 1 ? "current_human_candidate" :
                event.player_type == 2 ? "current_ai_candidate" : "current_unknown_owner")
            << ",\"controller\":" << quote(hex32(event.controller))
            << ",\"owner_identity_generation_local\":" << event.owner_identity_generation
            << ",\"race_context_valid\":" << (event.race_context_valid ? "true" : "false")
            << ",\"race_generation\":" << event.race_generation
            << ",\"owner_lifetime\":" << event.owner_lifetime
            << ",\"flag_address\":";
        if (event.backing_valid && event.backing <= UINT32_MAX - 0x33u)
            out << quote(hex32(event.backing + 0x33u));
        else out << "null";
        out << ",\"interval_flagged_consumer_calls\":" << event.interval_consumer_calls
            << ",\"last_flagged_consumer_qpc\":" << event.last_flagged_consumer_qpc
            << ",\"last_flagged_consumer_thread\":" << event.last_flagged_consumer_thread
            << ",\"consumer_in_progress\":" << (event.consumer_in_progress ? "true" : "false")
            << ",\"store_completion_observed\":false"
            << ",\"pause_state_known\":" << (event.pause_state_known ? "true" : "false")
            << ",\"pause_state\":" << quote(event.pause_state_known ? (event.pause_paused ? "paused" : "running") : "unknown")
            << ",\"pause_sample_age_ms\":";
        if (event.pause_state_known) out << event.pause_sample_age_ms; else out << "null";
        out << ",\"thread_id\":" << event.thread_id << ",\"qpc\":" << event.qpc << '}';
        session().write(out.str());
    } catch (...) {}
}


void write_transaction_record(const TransactionRecord& record) noexcept {
    try {
        const auto& b=record.before;const auto& a=record.after;
        std::ostringstream out;
        out << "{\"type\":\"physics_probe_transaction_event\",\"schema\":1,\"event_sequence\":" << b.sequence
            << ",\"event_kind\":" << quote(record.kind==1 ? "controller_consumption" : b.site==MATRIX_COMPLETE_PATCH_VA ? "matrix_complete" : "flag_store")
            << ",\"reset_transaction_candidate_id\":" << b.candidate
            << ",\"native_callsite\":" << quote(hex32(b.site))
            << ",\"native_scheduler_phase\":" << quote(record.kind==1 ? "verified_controller_call" : "verified_inline_store_or_copy_return")
            << ",\"reset_state_evidence\":" << quote(b.site==PUBLISH_PATCH_VA || b.site==MATRIX_COMPLETE_PATCH_VA ? "recovery_mode1_branch" :
                b.site==CLEAR_RECOVERY_STORE_VA ? "recovery_mode0_branch" : b.site==CLEAR_TIMER_STORE_VA ? "reset_timer_path" :
                b.site==CLEAR_GATE_STORE_VA ? "reset_gate_rejected" : b.site==INPUT_FLAG_PATCH_VA ? "input_flag_forward" :
                b.site==RESTORE_FLAG_PATCH_VA ? "serialized_backing_restore" : "controller_consumer")
            << ",\"race_generation\":" << b.race << ",\"owner_lifetime\":" << b.lifetime
            << ",\"race_context_valid\":" << (b.race_valid && a.race_valid && b.race==a.race && b.lifetime==a.lifetime ? "true":"false")
            << ",\"reset_manager_identity\":" << quote(hex32(b.manager))
            << ",\"writer_owner\":" << quote(hex32(b.writer_owner))
            << ",\"participant_index\":";
        if (b.participant>=0) out << b.participant; else out << "null";
        out << ",\"controller_identity\":" << quote(hex32(b.controller))
            << ",\"controller_identity_generation\":" << b.identity_generation
            << ",\"controller_backing_pointer\":" << quote(hex32(b.backing))
            << ",\"current_human_candidate\":" << (b.human && a.human && b.owner_current && a.owner_current && b.controller==a.controller && b.identity_generation==a.identity_generation ? "true":"false")
            << ",\"observation_readable\":" << (b.readable && a.readable ? "true":"false")
            << ",\"flag_value_before\":" << static_cast<unsigned>(b.flag)
            << ",\"flag_value_after\":" << static_cast<unsigned>(a.flag)
            << ",\"native_store_value\":" << static_cast<unsigned>(b.store_operand)
            << ",\"store_completion_observed\":" << (record.kind==0 && b.site!=MATRIX_COMPLETE_PATCH_VA && b.readable && a.readable ? "true":"false")
            << ",\"store_result_matches_operand\":" << (record.kind==0 && b.site!=MATRIX_COMPLETE_PATCH_VA && a.readable && a.flag==b.store_operand ? "true":"false")
            << ",\"unknown_transition_before\":" << (b.unknown_transition ? "true":"false")
            << ",\"thread_id\":" << b.thread << ",\"qpc_timestamp\":" << b.qpc << ",\"qpc_after\":" << a.qpc
            << ",\"pause_state\":" << quote(!b.paused_known ? "unknown" : b.paused ? "paused":"running")
            << ",\"transform_digest_before\":" << quote(hex64(matrix_digest(b.matrix)))
            << ",\"transform_digest\":" << quote(hex64(matrix_digest(a.matrix)))
            << ",\"transform_bits_before\":[";
        for (size_t i=0;i<16;++i) {if(i)out<<',';out<<quote(hex32(b.matrix[i]));}
        out << "],\"transform_bits\":[";
        for (size_t i=0;i<16;++i) {if(i)out<<',';out<<quote(hex32(a.matrix[i]));}
        out << "],\"transform_translation\":[";
        for (size_t i=12;i<15;++i) {if(i!=12)out<<',';float v=0;std::memcpy(&v,&a.matrix[i],sizeof(v));if(std::isfinite(v))out<<std::setprecision(9)<<v;else out<<"null";}
        out << "],\"causal_proof\":false,\"game_data_writes_by_observer\":false}";
        session().write(out.str());
    } catch (...) {}
}
void write_transaction_capture() noexcept {
    try {
        std::ostringstream out;
        out << "{\"type\":\"physics_probe_transaction_summary\",\"schema\":1,\"capture_policy\":\"transition_priority_v2\",\"important_capacity\":128,\"diagnostic_capacity\":16,\"important_records\":" << transaction.count
            << ",\"important_overflow\":" << transaction.overflow << ",\"diagnostic_overflow\":" << transaction.diagnostic_overflow
            << ",\"instrumented_inline_sites\":[\"0x004CCC6D\",\"0x004CD19E\",\"0x004CD1DB\",\"0x004CCFF1\",\"0x004CD131\",\"0x00591345\",\"0x004CB62A\"]"
            << ",\"inline_rollback_verified\":" << (probe.clear_writer_batch.rollback_verified ? "true":"false")
            << ",\"in_flight_store_observations\":" << transaction.pending_observations
            << ",\"pairing_failures\":" << transaction.pairing_failures << ",\"unknown_transitions\":" << transaction.unknown_transitions
            << ",\"zero_stores_suppressed\":" << transaction.zero_stores << ",\"repeated_nonzero_stores\":" << transaction.repeated_stores
            << ",\"writer_coverage_exhaustive\":false,\"unhooked_initialization_store\":\"0x00508A1A\",\"one_shot_guaranteed\":false,\"teleport_enabled\":false}";
        session().write(out.str());
        for(size_t i=0;i<transaction.count;++i) write_transaction_record(transaction.important[i]);
        for(size_t i=0;i<transaction.diagnostic_count;++i) write_transaction_record(transaction.diagnostics[i]);
    } catch (...) {}
}

void write_summary(bool patch_restored) noexcept {
    bool lock_held = true;
    try {
        AcquireSRWLockExclusive(&probe.lock);
        std::ostringstream out;
        out << "{\"type\":\"physics_probe_summary\",\"phase\":\"ROAD-TRANSACTION-CORRELATION-1\","
            << "\"read_only_game_data\":true,\"exact_retail_build\":true,"
            << "\"instrumented_call_sites\":["
            << "{\"va\":\"0x00443827\",\"rva\":\"0x00043827\",\"target_va\":\"0x00444AE0\"},"
            << "{\"va\":\"0x0043F8AD\",\"rva\":\"0x0003F8AD\",\"target_va\":\"0x0043F650\"},"
            << "{\"va\":\"0x0043F8ED\",\"rva\":\"0x0003F8ED\",\"target_va\":\"0x0043FE00\"}";
        if (InterlockedCompareExchange(&probe.route_preview_enabled, 0, 0))
            out << ", {\"va\":\"0x004CCCB1\",\"rva\":\"0x000CCCB1\",\"target_va\":\"0x004E4D20\",\"role\":\"native_live_raceline_snapshot\"}";
        out << "],\"clear_writer_sites\":["
            << "{\"patch_va\":\"0x004CCC6D\",\"store_va\":\"0x004CCC70\",\"writer\":\"reset_gate_rejected\"},"
            << "{\"patch_va\":\"0x004CD19E\",\"store_va\":\"0x004CD1A1\",\"writer\":\"recovery_mode0\"},"
            << "{\"patch_va\":\"0x004CD1DB\",\"store_va\":\"0x004CD1DE\",\"writer\":\"recovery_timer_expired\"}],"
            << "\"pause_sample_max_age_ms\":500,"
            << "\"installed\":" << (probe.installed ? "true" : "false")
            << ",\"patch_restored\":" << (patch_restored ? "true" : "false")
            << ",\"module_pinned\":" << (probe.module_pinned ? "true" : "false")
            << ",\"reason\":" << quote(probe.reason)
            << ",\"release_reason\":" << quote(probe.release_reason)
            << ",\"road_target_preview\":{\"enabled\":"
            << (InterlockedCompareExchange(&probe.route_preview_enabled, 0, 0) ? "true" : "false")
            << ",\"snapshot_available\":" << (probe.route_snapshot.available ? "true" : "false")
            << ",\"source\":" << quote(probe.route_snapshot.source_native_live ? "native_live_raceline" : "unavailable")
            << ",\"race_generation\":" << probe.route_snapshot.race_generation
            << ",\"owner_lifetime\":" << probe.route_snapshot.owner_lifetime
            << ",\"snapshot_sequence\":" << probe.route_snapshot.sequence
            << ",\"count\":" << probe.route_snapshot.count
            << ",\"stride\":" << probe.route_snapshot.stride
            << ",\"position_offset\":" << probe.route_snapshot.position_offset
            << ",\"fingerprint\":" << quote(hex64(probe.route_snapshot.fingerprint))
            << ",\"capture_attempts\":" << probe.route_capture_attempts
            << ",\"capture_failures\":" << probe.route_capture_failures
            << ",\"last_failure\":" << quote(probe.route_last_failure)
            << ",\"preview_search_radius_horizontal\":" << probe.route_preview_radius
            << ",\"physical_placement_verified\":false},\"qpc_frequency\":";
        LARGE_INTEGER frequency{};
        QueryPerformanceFrequency(&frequency);
        out << static_cast<uint64_t>(frequency.QuadPart)
            << ",\"counts\":{\"tracked_controllers\":";
        size_t tracks_used = 0;
        uint64_t updates = 0, set_calls = 0, rises = 0, clears = 0, overlaps = 0, identity_changes = 0;
        for (const auto& track : probe.tracks) {
            if (!track.used) continue;
            ++tracks_used;
            updates += track.flag.calls;
            set_calls += track.flag.set_calls;
            rises += track.flag.rises;
            clears += track.flag.clears;
            overlaps += track.overlap_calls;
            identity_changes += track.identity_changes;
        }
        out << tracks_used << ",\"controller_updates\":" << updates
            << ",\"flag_set_consumer_calls\":" << set_calls
            << ",\"flag_rises_observed\":" << rises
            << ",\"flag_clears_observed\":" << clears
            << ",\"same_controller_overlap_calls\":" << overlaps
            << ",\"identity_changes\":" << identity_changes
            << ",\"invalid_native_snapshots\":" << static_cast<uint32_t>(probe.invalid_snapshots)
            << ",\"invalid_physics_managers\":" << static_cast<uint32_t>(probe.invalid_managers)
            << ",\"dropped_tracks\":" << probe.dropped_tracks
            << ",\"dropped_events\":" << probe.dropped_events
            << ",\"substep_events\":" << probe.substep_events
            << ",\"substep_windows_opened\":" << probe.substep_windows
            << ",\"controller_calls_while_paused\":" << probe.controller_calls_while_paused
            << ",\"substep_phase_records_while_paused\":" << probe.substep_phase_records_while_paused
            << ",\"clear_writes_while_paused\":" << probe.clear_writes_while_paused
            << ",\"clear_writer_events\":" << (probe.clear_capture.transition_count + probe.clear_capture.diagnostic_count)
            << ",\"clear_writer_events_dropped\":" << (probe.clear_capture.transition_overflow + probe.clear_capture.diagnostic_overflow)
            << ",\"events_written\":" << probe.event_count << "},\"controllers\":[";
        bool first = true;
        for (const auto& track : probe.tracks) {
            if (!track.used) continue;
            if (!first) out << ',';
            first = false;
            out << "{\"controller\":" << quote(hex32(track.identity.controller))
                << ",\"handle\":" << quote(hex32(track.identity.handle))
                << ",\"body\":" << quote(hex32(track.identity.body))
                << ",\"player_type\":" << track.identity.player_type
                << ",\"owner_candidate\":" << quote(owner_name(track.identity.player_type))
                << ",\"identity_generation_local\":" << track.identity_generation
                << ",\"updates\":" << track.flag.calls
                << ",\"flag_set_calls\":" << track.flag.set_calls
                << ",\"flag_rises\":" << track.flag.rises
                << ",\"flag_clears\":" << track.flag.clears
                << ",\"overlap_calls\":" << track.overlap_calls
                << ",\"identity_changes\":" << track.identity_changes << '}';
        }
        out << "],\"clear_writer_capture\":{\"policy\":\"transition_priority_v1\""
            << ",\"transition_capacity\":" << CLEAR_TRANSITION_CAPACITY
            << ",\"diagnostic_capacity\":" << CLEAR_DIAGNOSTIC_CAPACITY
            << ",\"transitions_retained\":" << probe.clear_capture.transition_count
            << ",\"diagnostics_retained\":" << probe.clear_capture.diagnostic_count
            << ",\"transition_overflow\":" << probe.clear_capture.transition_overflow
            << ",\"diagnostic_overflow\":" << probe.clear_capture.diagnostic_overflow
            << ",\"all_sampled_store_transitions_retained\":"
            << (probe.clear_capture.transition_overflow == 0 ? "true" : "false")
            << ",\"writers\":[";
        for (size_t i = 0; i < probe.clear_capture.writers.size(); ++i) {
            if (i) out << ',';
            const auto& counts = probe.clear_capture.writers[i];
            out << "{\"writer\":" << quote(clear_writer_name(static_cast<ClearWriter>(i)))
                << ",\"calls\":" << counts.calls
                << ",\"zero_stores_suppressed\":" << counts.zero_stores_suppressed
                << ",\"clear_transitions\":" << counts.clears
                << ",\"rise_transitions\":" << counts.rises
                << ",\"other_transitions\":" << counts.other_transitions
                << ",\"repeated_nonzero\":" << counts.repeated_nonzero
                << ",\"unreadable\":" << counts.unreadable << '}';
        }
        out << "]}}";
        ReleaseSRWLockExclusive(&probe.lock);
        lock_held = false;
        session().write(out.str());
        write_transaction_capture();
        for (size_t i = 0; i < probe.event_count; ++i) write_event(probe.events[i]);
        // Preserve observation order across the two reserved partitions.
        auto clear_events = probe.clear_writer_events;
        std::sort(clear_events.begin(), clear_events.end(),
            [](const ClearWriterEvent& a, const ClearWriterEvent& b) { return a.sequence < b.sequence; });
        for (const auto& event : clear_events)
            if (event.sequence) write_clear_writer_event(event);
    } catch (...) {
        if (lock_held) ReleaseSRWLockExclusive(&probe.lock);
    }
}

bool pin_probe_module() noexcept {
    if (probe.module_pinned) return true;
    HMODULE module = nullptr;
    const auto address = reinterpret_cast<uintptr_t>(&physics_probe_controller_bridge);
    if (!GetModuleHandleExW(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS,
                            reinterpret_cast<LPCWSTR>(address), &module)) return false;
    probe.pinned_module = module;
    probe.module_pinned = true;
    return true;
}

void configure_batch(uint32_t base, bool include_route_getter, bool include_road_adjust) noexcept {
    probe.batch = RacePatchBatch{};
    probe.batch.count = physics_call_patch_count(include_route_getter, include_road_adjust);
    configure_call(0, base, CONTROLLER_CALL_VA, CONTROLLER_CALL_TARGET_VA,
                   reinterpret_cast<uintptr_t>(&physics_probe_controller_bridge),
                   {0xE8, 0xB4, 0x12, 0x00, 0x00});
    configure_call(1, base, SUBSTEP_BEGIN_CALL_VA, SUBSTEP_BEGIN_TARGET_VA,
                   reinterpret_cast<uintptr_t>(&physics_probe_substep_begin_bridge),
                   {0xE8, 0x9E, 0xFD, 0xFF, 0xFF});
    configure_call(2, base, SUBSTEP_TAIL_CALL_VA, SUBSTEP_TAIL_TARGET_VA,
                   reinterpret_cast<uintptr_t>(&physics_probe_substep_tail_bridge),
                   {0xE8, 0x0E, 0x05, 0x00, 0x00});
    if (include_route_getter) {
        configure_call(3, base, ROUTE_GETTER_CALL_VA, ROUTE_GETTER_TARGET_VA,
                       reinterpret_cast<uintptr_t>(&physics_probe_route_getter_bridge),
                       ROUTE_GETTER_CALL);
    }
    if (include_road_adjust) {
        configure_call(include_route_getter ? 4 : 3, base, ROAD_ADJUST_CALL_VA,
                       ROAD_ADJUST_TARGET_VA,
                       reinterpret_cast<uintptr_t>(&road_teleport_adjust_bridge),
                       ROAD_ADJUST_CALL);
        road_teleport_adjust_original = base + ROAD_ADJUST_TARGET_VA - 0x00400000u;
    }
}

void note_setup(bool requested, bool exact, bool installed, const char* reason,
                const PhysicsProbeSettings& settings) noexcept {
    try {
        session().write("{\"type\":\"physics_probe_setup\",\"phase\":\"ROAD-TRANSACTION-CORRELATION-1\","
                        "\"requested\":" + std::string(requested ? "true" : "false") +
                        ",\"exact_retail_build\":" + (exact ? "true" : "false") +
                        ",\"installed\":" + (installed ? "true" : "false") +
                        ",\"road_target_preview_enabled\":" +
                        (settings.road_target_preview_enabled ? "true" : "false") +
                        ",\"road_teleport_requested\":" + (settings.road_teleport_requested ? "true" : "false") +
                        ",\"road_teleport_road_only\":" + (settings.road_teleport_road_only ? "true" : "false") +
                        ",\"road_teleport_enabled\":" + (settings.road_teleport_enabled ? "true" : "false") +
                        ",\"native_selection_argument_override\":" +
                        (installed && settings.road_teleport_enabled ? "true" : "false") +
                        ",\"direct_physics_or_broker_writes\":false,\"reason\":" + quote(reason) + "}");
    } catch (...) {}
}

} // namespace

PhysicsProbeSettings read_physics_probe_settings(const std::wstring& path) noexcept {
    PhysicsProbeSettings settings;
    try {
        wchar_t enabled_buffer[32]{};
        wchar_t preview_buffer[32]{};
        wchar_t radius_buffer[64]{};
        const DWORD enabled_length = GetPrivateProfileStringW(
            L"PhysicsObserver", L"Enabled", L"0", enabled_buffer,
            static_cast<DWORD>(std::size(enabled_buffer)), path.c_str());
        const DWORD preview_length = GetPrivateProfileStringW(
            L"PhysicsObserver", L"RoadTargetPreviewEnabled", L"0", preview_buffer,
            static_cast<DWORD>(std::size(preview_buffer)), path.c_str());
        const DWORD radius_length = GetPrivateProfileStringW(
            L"PhysicsObserver", L"RoadTargetPreviewRadius", L"60.0", radius_buffer,
            static_cast<DWORD>(std::size(radius_buffer)), path.c_str());
        const std::string enabled_raw = enabled_length >= std::size(enabled_buffer) - 1 ?
            "__TRUNCATED_INVALID__" : utf8(enabled_buffer);
        const std::string preview_raw = preview_length >= std::size(preview_buffer) - 1 ?
            "__TRUNCATED_INVALID__" : utf8(preview_buffer);
        const std::string radius_raw = radius_length >= std::size(radius_buffer) - 1 ?
            "__TRUNCATED_INVALID__" : utf8(radius_buffer);
        settings.raw_value = "enabled=" + enabled_raw + ";road_preview=" + preview_raw +
                             ";radius=" + radius_raw;

        bool enabled = false, preview_enabled = false;
        const bool booleans_valid = enabled_raw != "__TRUNCATED_INVALID__" &&
            preview_raw != "__TRUNCATED_INVALID__" &&
            parse_config_boolean(enabled_raw, enabled) &&
            parse_config_boolean(preview_raw, preview_enabled);
        wchar_t* end = nullptr;
        const double radius = std::wcstod(radius_buffer, &end);
        while (end && *end && iswspace(*end)) ++end;
        const bool radius_valid = radius_raw != "__TRUNCATED_INVALID__" &&
            end != radius_buffer && end && *end == L'\0' && std::isfinite(radius) &&
            radius >= 0.0 && radius <= 100000.0;
        if (!booleans_valid || !radius_valid) {
            settings.valid = false;
            settings.enabled = false;
            settings.road_target_preview_enabled = false;
        } else {
            settings.enabled = enabled;
            settings.road_target_preview_enabled = preview_enabled;
            settings.road_target_preview_radius = radius;
        }
    } catch (...) {
        settings.valid = false;
        settings.enabled = false;
        settings.road_target_preview_enabled = false;
        settings.raw_value = "__READ_FAILED__";
    }
    return settings;
}

PhysicsProbeSettings forward_free_camera_teleport_settings(
    PhysicsProbeSettings settings, const FreeCameraConfig& camera) noexcept {
    settings.road_teleport_requested = camera.vehicle_teleport_enabled;
    settings.road_teleport_road_only = camera.vehicle_teleport_road_only;
    settings.road_teleport_enabled = camera.enabled &&
        camera.vehicle_teleport_enabled && camera.vehicle_teleport_road_only;
    settings.road_teleport_max_distance = camera.vehicle_teleport_max_road_distance;
    settings.road_teleport_arm_timeout_seconds = camera.vehicle_teleport_arm_timeout_seconds;
    return settings;
}

bool attach_physics_probe(bool exact_retail, const PhysicsProbeSettings& settings) noexcept {
    const auto report_setup = [&](bool requested, bool exact, bool installed, const char* reason) noexcept {
        note_setup(requested, exact, installed, reason, settings);
    };
    try {
        session().write("{\"type\":\"physics_probe_config\",\"phase\":\"ROAD-TRANSACTION-CORRELATION-1\","
                        "\"enabled_raw\":" + quote(settings.raw_value) +
                        ",\"valid\":" + (settings.valid ? "true" : "false") +
                        ",\"requested\":" + (settings.enabled ? "true" : "false") +
                        ",\"road_target_preview_enabled\":" + (settings.road_target_preview_enabled ? "true" : "false") +
                        ",\"road_target_preview_radius_horizontal\":" + std::to_string(settings.road_target_preview_radius) +
                        ",\"road_teleport_requested\":" + (settings.road_teleport_requested ? "true" : "false") +
                        ",\"road_teleport_road_only\":" + (settings.road_teleport_road_only ? "true" : "false") +
                        ",\"road_teleport_enabled\":" + (settings.road_teleport_enabled ? "true" : "false") +
                        ",\"road_teleport_max_distance\":" + std::to_string(settings.road_teleport_max_distance) +
                        ",\"road_teleport_arm_timeout_seconds\":" + std::to_string(settings.road_teleport_arm_timeout_seconds) + "}");
    } catch (...) {}
    if (settings.road_teleport_enabled && !settings.enabled) {
        report_setup(true, exact_retail, false, "road_teleport_requires_physics_observer");
        return false;
    }
    if (settings.road_teleport_enabled && !settings.road_target_preview_enabled) {
        report_setup(true, exact_retail, false, "road_teleport_requires_live_route_preview");
        return false;
    }
    if (settings.road_teleport_enabled &&
        (!std::isfinite(settings.road_teleport_max_distance) ||
         settings.road_teleport_max_distance <= 0.0 || settings.road_teleport_max_distance > 20.0 ||
         settings.road_teleport_arm_timeout_seconds < 1 ||
         settings.road_teleport_arm_timeout_seconds > 300)) {
        report_setup(true, exact_retail, false, "road_teleport_configuration_out_of_range");
        return false;
    }
    if (!settings.enabled) {
        report_setup(false, exact_retail, false, settings.valid ? "disabled_by_default_or_config" : "invalid_config_disabled");
        return false;
    }
    if (!settings.valid) {
        report_setup(true, exact_retail, false, "invalid_config_disabled");
        return false;
    }
    if (!exact_retail) {
        report_setup(true, false, false, "exact_pristine_build_required");
        return false;
    }

    AcquireSRWLockExclusive(&probe.lock);
    if (probe.leases && probe.installed && batch_intact()) {
        if (!same_preview_configuration(settings) || probe.leases == UINT32_MAX) {
            const char* mismatch = probe.leases == UINT32_MAX ?
                "probe_lease_count_exhausted" : "probe_lease_configuration_mismatch";
            ReleaseSRWLockExclusive(&probe.lock);
            report_setup(true, true, false, mismatch);
            return false;
        }
        ++probe.leases;
        InterlockedExchange(&probe.enabled, 1);
        ReleaseSRWLockExclusive(&probe.lock);
        report_setup(true, true, true, "existing_probe_lease");
        return true;
    }
    if (probe.leases) {
        ReleaseSRWLockExclusive(&probe.lock);
        report_setup(true, true, false, "probe_lease_state_inconsistent");
        return false;
    }

    if (probe.installed && batch_intact()) {
        if (!same_preview_configuration(settings)) {
            ReleaseSRWLockExclusive(&probe.lock);
            report_setup(true, true, false, "probe_reactivation_configuration_mismatch");
            return false;
        }
        probe.leases = 1;
        probe.reason = "reactivated_owned_hook";
        InterlockedExchange(&probe.enabled, 1);
        ReleaseSRWLockExclusive(&probe.lock);
        report_setup(true, true, true, "reactivated_owned_hook");
        return true;
    }
    if (probe.batch.owned()) {
        probe.reason = "partial_or_foreign_hook_requires_process_exit";
        ReleaseSRWLockExclusive(&probe.lock);
        report_setup(true, true, false, probe.reason);
        return false;
    }
    if (probe.clear_writer_batch.owned()) {
        probe.reason = "partial_or_foreign_clear_writer_hook_requires_process_exit";
        ReleaseSRWLockExclusive(&probe.lock);
        report_setup(true, true, false, probe.reason);
        return false;
    }

    probe.tracks = {};
    probe.events = {};
    probe.event_count = 0;
    probe.event_sequence = 0;
    probe.dropped_events = 0;
    probe.invalid_snapshots = 0;
    probe.invalid_managers = 0;
    probe.dropped_tracks = 0;
    probe.substep_events = 0;
    probe.substep_windows = 0;
    probe.substep_budget = 0;
    transaction = {};
    transaction_pending = {};
    probe.clear_writer_events = {};
    probe.clear_capture = {};
    probe.clear_writer_event_sequence = 0;
    probe.controller_calls_while_paused = 0;
    probe.substep_phase_records_while_paused = 0;
    probe.clear_writes_while_paused = 0;
    InterlockedExchange(&probe.substep_window_active, 0);
    probe.route_context_valid = false;
    probe.route_context_race_generation = 0;
    probe.route_context_owner_lifetime = 0;
    probe.route_snapshot = road_target::LiveSnapshot{};
    probe.route_snapshot_sequence = 0;
    probe.route_capture_attempts = 0;
    probe.route_capture_failures = 0;
    probe.route_last_failure = settings.road_target_preview_enabled ?
        "awaiting_supported_race_certificate_and_stock_reset" : "disabled_by_config";
    probe.route_preview_radius = settings.road_target_preview_radius;
    probe.road_teleport_enabled = settings.road_teleport_enabled;
    probe.road_teleport_max_distance = settings.road_teleport_max_distance;
    probe.road_teleport_arm_timeout_seconds = settings.road_teleport_arm_timeout_seconds;
    probe.road_teleport_next_sequence = 0;
    probe.road_teleport_selection_attempts = 0;
    probe.road_teleport_owner_gate_attempts = 0;
    probe.road_teleport_owner_gate_accepted = 0;
    probe.road_teleport_owner_gate_rejected = 0;
    probe.road_teleport_override_count = 0;
    probe.road_teleport_stock_fallback_count = 0;
    probe.road_teleport_stack_write_failures = 0;
    road_teleport::initialize(probe.road_teleport, settings.road_teleport_enabled);
    probe.pause_state_known = false;
    probe.pause_paused = false;
    probe.pause_sample_tick_ms = 0;
    InterlockedExchange(&probe.route_preview_enabled,
                        settings.road_target_preview_enabled ? 1 : 0);

    probe.base = static_cast<uint32_t>(reinterpret_cast<uintptr_t>(GetModuleHandleW(nullptr)));
    if (probe.base != 0x00400000 || !pin_probe_module()) {
        probe.reason = "image_base_or_module_pin_failed";
        ReleaseSRWLockExclusive(&probe.lock);
        report_setup(true, true, false, probe.reason);
        return false;
    }
    const bool include_route_getter = route_getter_hook_requested(
        settings.enabled, settings.road_target_preview_enabled);
    const bool include_road_adjust = settings.road_teleport_enabled;
    configure_batch(probe.base, include_route_getter, include_road_adjust);
    configure_clear_writer_batch(probe.base);
    bool installed = false;
    {
        SuspendedThreads suspended;
        if (!suspended.freeze(probe.batch, &probe.clear_writer_batch)) {
            probe.reason = "thread_quiescence_check_failed";
        } else {
            const char* context_failure = verify_contexts(probe.base);
            if (context_failure) {
                probe.reason = context_failure;
            } else if (const char* clear_context_failure = verify_clear_writer_contexts(probe.base)) {
                probe.reason = clear_context_failure;
            } else if (include_route_getter &&
                       !verify_route_getter_context(probe.base)) {
                probe.reason = "route_getter_context_mismatch";
            } else if (include_road_adjust && !verify_road_adjust_context(probe.base)) {
                probe.reason = "native_recovery_selection_context_mismatch";
            } else if (const char* abi_failure = include_route_getter ?
                           verify_route_getter_abi(probe.base) : nullptr;
                       abi_failure != nullptr) {
                probe.reason = abi_failure;
            } else {
                installed = probe.batch.install(memory);
                if (!installed) {
                    probe.reason = "exact_physics_callsite_patch_failed";
                } else if (!install_inline_batch()) {
                    installed = false;
                    remove_inline_batch();
                    probe.reason = "clear_writer_patch_install_failed";
                    if (probe.batch.owned()) {
                        probe.batch.remove(memory);
                    }
                    if (probe.batch.owned() || probe.clear_writer_batch.owned())
                        probe.reason = "partial_hook_remains_disabled_module_pinned";
                }
            }
        }
    }
    if (!installed) {
        probe.installed = false;
        probe.patch_intact = probe.batch.owned() || probe.clear_writer_batch.owned();
        InterlockedExchange(&probe.enabled, 0);
        ReleaseSRWLockExclusive(&probe.lock);
        report_setup(true, true, false, probe.reason);
        return false;
    }

    probe.installed = true;
    probe.patch_intact = true;
    probe.reason = "exact_callsites_installed_read_only";
    if (include_road_adjust) probe.reason = "exact_callsites_installed_with_road_selection_override_disabled_until_armed";
    probe.leases = 1;
    InterlockedExchange(&probe.enabled, 1);
    ReleaseSRWLockExclusive(&probe.lock);
    report_setup(true, true, true, probe.reason);
    return true;
}

void release_physics_probe() noexcept {
    AcquireSRWLockExclusive(&probe.lock);
    if (!probe.leases) {
        ReleaseSRWLockExclusive(&probe.lock);
        return;
    }
    --probe.leases;
    if (probe.leases) {
        ReleaseSRWLockExclusive(&probe.lock);
        return;
    }
    road_teleport::cancel(probe.road_teleport, "physics_probe_device_release");
    InterlockedExchange(&probe.enabled, 0);
    probe.release_reason = "device_release_disable_and_restore";
    ReleaseSRWLockExclusive(&probe.lock);

    bool restored = false;
    if (probe.installed && (probe.batch.owned() || probe.clear_writer_batch.owned())) {
        {
            SuspendedThreads suspended;
            if (suspended.freeze(probe.batch, &probe.clear_writer_batch)) {
                const bool clear_restored = probe.clear_writer_batch.owned() ? remove_inline_batch() : true;
                const bool call_restored = probe.batch.owned() ? probe.batch.remove(memory) : true;
                restored = clear_restored && call_restored;
            }
        }
    }

    AcquireSRWLockExclusive(&probe.lock);
    probe.patch_intact = !restored && (probe.batch.owned() || probe.clear_writer_batch.owned());
    if (restored) {
        probe.installed = false;
        probe.release_reason = "hook_restored";
    } else if (probe.batch.owned() || probe.clear_writer_batch.owned()) {
        probe.release_reason = "restore_not_safe_or_foreign_patch;disabled_and_module_pinned";
    } else {
        probe.installed = false;
        probe.release_reason = "hook_already_absent";
    }
    ReleaseSRWLockExclusive(&probe.lock);
    write_summary(restored);
}

void publish_physics_probe_race_context(bool valid, uint64_t race_generation,
                                        uint64_t owner_lifetime) noexcept {
    if (InterlockedCompareExchange(&probe.route_preview_enabled, 0, 0) == 0) return;
    const bool accepted = valid && race_generation != 0 && owner_lifetime != 0;
    AcquireSRWLockExclusive(&probe.lock);
    const bool changed = probe.route_context_valid != accepted ||
        probe.route_context_race_generation != (accepted ? race_generation : 0) ||
        probe.route_context_owner_lifetime != (accepted ? owner_lifetime : 0);
    probe.route_context_valid = accepted;
    probe.route_context_race_generation = accepted ? race_generation : 0;
    probe.route_context_owner_lifetime = accepted ? owner_lifetime : 0;
    road_teleport::invalidate_generation(probe.road_teleport,
        accepted ? race_generation : 0, accepted ? owner_lifetime : 0);
    if (changed) {
        transaction.identities = {};
        // Instance tracks must not survive a race certificate epoch change.
        // Pending observers are dropped; the native calls themselves still forward.
        probe.tracks = {};
    }
    if (changed && probe.route_snapshot.available) {
        probe.route_snapshot.available = false;
        probe.route_snapshot.reason = accepted ? "race_generation_or_owner_changed" :
                                                 "race_certificate_invalidated";
        probe.route_last_failure = probe.route_snapshot.reason;
    }
    ReleaseSRWLockExclusive(&probe.lock);
}

void publish_physics_probe_pause_state(bool known, bool paused,
                                       uint64_t sampled_tick_ms) noexcept {
    if (InterlockedCompareExchange(&probe.enabled, 0, 0) == 0) return;
    AcquireSRWLockExclusive(&probe.lock);
    probe.pause_state_known = known && sampled_tick_ms != 0;
    probe.pause_paused = probe.pause_state_known && paused;
    probe.pause_sample_tick_ms = probe.pause_state_known ? sampled_tick_ms : 0;
    ReleaseSRWLockExclusive(&probe.lock);
}

// Development-only direct relocation for collision probes. It reuses the stock
// recovery publication contract (matrix at P+0x34, level flag at P+0x33) with a
// caller-chosen destination. Not certified: the reset manager may clear the flag
// before the controller consumes it, so the pair is re-asserted until the chassis
// reaches the target or a frame budget expires. Default OFF; see ProbeTeleport.
namespace {
struct DevTeleport {
    volatile bool active = false;
    float x = 0, y = 0, z = 0, yaw_degrees = 0;
    uint32_t frames = 0;   // native writes performed inside the controller hook
    uint32_t ticks = 0;    // render-side polls since the request
    uint64_t sequence = 0;
};
DevTeleport dev_teleport;
constexpr uint32_t DEV_TELEPORT_WRITE_BUDGET = 30;
constexpr uint32_t DEV_TELEPORT_TICK_BUDGET = 240;

void dev_teleport_log(const char* state, const char* reason) noexcept {
    try {
        session().write(std::string("{\"type\":\"probe_teleport\",\"state\":") + quote(std::string(state)) +
            ",\"reason\":" + quote(std::string(reason)) + ",\"sequence\":" + std::to_string(dev_teleport.sequence) +
            ",\"target\":[" + std::to_string(dev_teleport.x) + ',' + std::to_string(dev_teleport.y) + ',' +
            std::to_string(dev_teleport.z) + "],\"yaw_degrees\":" + std::to_string(dev_teleport.yaw_degrees) +
            ",\"frames\":" + std::to_string(dev_teleport.frames) + "}");
    } catch (...) {}
}
}

const char* physics_probe_dev_teleport_request(float x, float y, float z, float yaw_degrees) noexcept {
    if (InterlockedCompareExchange(&probe.enabled, 0, 0) == 0) return "physics_observer_disabled";
    if (!std::isfinite(x) || !std::isfinite(y) || !std::isfinite(z) || !std::isfinite(yaw_degrees))
        return "target_not_finite";
    AcquireSRWLockExclusive(&probe.lock);
    dev_teleport.active = true;
    dev_teleport.x = x; dev_teleport.y = y; dev_teleport.z = z;
    dev_teleport.yaw_degrees = yaw_degrees;
    dev_teleport.frames = 0;
    dev_teleport.ticks = 0;
    ++dev_teleport.sequence;
    ReleaseSRWLockExclusive(&probe.lock);
    dev_teleport_log("requested", "hotkey");
    return "requested";
}

// Runs inside the controller bridge, immediately before the native controller update.
// The reset manager clears P+0x33 almost every tick, so only a write at this point is
// guaranteed to be seen by the consumer in the same tick.
namespace {
void dev_teleport_apply_before_controller(uint32_t controller) noexcept {
    if (!dev_teleport.active) return;
    NativeLinks links{};
    if (!read_native_links(controller, links) || links.player_type != 1) return;
    AcquireSRWLockExclusive(&probe.lock);
    if (dev_teleport.active && dev_teleport.frames < DEV_TELEPORT_WRITE_BUDGET && batch_intact()) {
        const float radians = dev_teleport.yaw_degrees * 3.14159265358979f / 180.0f;
        const float c = std::cos(radians), sn = std::sin(radians);
        // Row-major 4x4, translation in row 3 (stock layout). Yaw about +Y only;
        // the sign and the car's forward axis are unverified.
        const float m[16] = { c, 0, -sn, 0,  0, 1, 0, 0,  sn, 0, c, 0,
                              dev_teleport.x, dev_teleport.y, dev_teleport.z, 1 };
        const uint8_t one = 1;
        if (safe_copy(reinterpret_cast<void*>(static_cast<uintptr_t>(links.backing) + 0x34), m, sizeof(m)) &&
            safe_copy(reinterpret_cast<void*>(static_cast<uintptr_t>(links.backing) + 0x33), &one, 1))
            ++dev_teleport.frames;
    }
    ReleaseSRWLockExclusive(&probe.lock);
}
} // namespace

void physics_probe_dev_teleport_tick() noexcept {
    if (InterlockedCompareExchange(&probe.enabled, 0, 0) == 0) return;
    if (!dev_teleport.active) return;
    AcquireSRWLockExclusive(&probe.lock);
    if (!dev_teleport.active) { ReleaseSRWLockExclusive(&probe.lock); return; }
    const char* failure = nullptr;
    bool done = false;
    ++dev_teleport.ticks;
    NativeLinks links{};
    if (!probe.installed || probe.base != 0x00400000) failure = "probe_not_installed";
    else if (!batch_intact()) failure = "hook_ownership_lost";
    else {
        const Track* human = nullptr;
        size_t humans = 0;
        for (const auto& track : probe.tracks)
            if (track.used && track.identity.player_type == 1) { ++humans; human = &track; }
        if (humans != 1) failure = "no_unique_human_controller";
        else if (!read_native_links(human->identity.controller, links)) failure = "controller_links_unreadable";
    }
    if (!failure) {
        float position[3]{};
        if (dev_teleport.frames > 0 && read_bytes(links.body, 0xA0, position, sizeof(position)) &&
            std::fabs(position[0] - dev_teleport.x) < 1.5f && std::fabs(position[2] - dev_teleport.z) < 1.5f)
            done = true;
        else if (dev_teleport.frames >= DEV_TELEPORT_WRITE_BUDGET)
            failure = "chassis_did_not_reach_target";
        else if (dev_teleport.ticks >= DEV_TELEPORT_TICK_BUDGET)
            failure = dev_teleport.frames ? "chassis_did_not_reach_target" : "controller_hook_never_ran_for_human";
    }
    if (failure || done) dev_teleport.active = false;
    const char* state = failure ? "failed" : done ? "completed" : nullptr;
    ReleaseSRWLockExclusive(&probe.lock);
    if (state) dev_teleport_log(state, failure ? failure : "chassis_at_target");
}

bool arm_physics_probe_road_teleport(float camera_x, float camera_y, float camera_z,
                                     bool freecam_active, bool pause_known, bool paused,
                                     const RaceCertificate& certificate,
                                     uint32_t timeout_seconds, double maximum_distance) noexcept {
    if (InterlockedCompareExchange(&probe.enabled, 0, 0) == 0) return false;
    const uint64_t now = GetTickCount64();
    AcquireSRWLockExclusive(&probe.lock);
    auto& request = probe.road_teleport;
    if (!probe.road_teleport_enabled || !probe.installed) {
        if (request.state == road_teleport::State::Disabled)
            request.reason = "road_teleport_not_installed_or_disabled";
        ReleaseSRWLockExclusive(&probe.lock);
        return false;
    }
    if (!batch_intact()) {
        disable_after_ownership_loss();
        road_teleport::cancel(request, "physics_probe_hook_ownership_lost");
        ReleaseSRWLockExclusive(&probe.lock);
        return false;
    }
    const auto pause = pause_state_at(
        {probe.pause_state_known, probe.pause_paused, probe.pause_sample_tick_ms}, now, 500);
    const bool actual_pause_agrees = pause.known && pause.paused && pause_known && paused;
    uint32_t controller = 0, backing = 0, actor = 0;
    uint64_t identity_generation = 0;
    const auto& snapshot = probe.route_snapshot;
    VehicleOwnerEvidence owner_evidence{};
    const bool idle_human = unique_human_controller_idle(
        controller, backing, actor, identity_generation, &owner_evidence,
        &certificate, snapshot.recovery_manager);
    const auto owner_decision = evaluate_vehicle_owner(owner_evidence);
    if (probe.road_teleport_owner_gate_attempts != UINT64_MAX) ++probe.road_teleport_owner_gate_attempts;
    auto& owner_counter = owner_decision.accepted ? probe.road_teleport_owner_gate_accepted :
        probe.road_teleport_owner_gate_rejected;
    if (owner_counter != UINT64_MAX) ++owner_counter;
    road_target::Preview selected{};
    if (snapshot.available && snapshot.race_generation == certificate.race_generation &&
        snapshot.owner_lifetime == certificate.owner_lifetime && snapshot.source_native_live &&
        snapshot.exact_supported_course && snapshot.capture_owner_current) {
        selected = road_target::nearest_marker(snapshot, {camera_x,camera_y,camera_z},
            maximum_distance, certificate.race_generation, certificate.owner_lifetime, true);
    } else {
        selected.reason = snapshot.reason ? snapshot.reason : "current_live_route_snapshot_unavailable";
    }

    road_teleport::ArmFacts facts{};
    facts.enabled = true;
    facts.exact_build = probe.base == 0x00400000;
    facts.freecam_active = freecam_active;
    facts.pause_known = actual_pause_agrees;
    facts.paused = actual_pause_agrees;
    facts.race_certificate = probe.route_context_valid &&
        probe.route_context_race_generation == certificate.race_generation &&
        probe.route_context_owner_lifetime == certificate.owner_lifetime;
    facts.single_human_car_race = certificate.single_human_car_race;
    facts.unique_current_human_controller = idle_human && owner_decision.accepted;
    facts.owner_gate_reason = owner_decision.reason;
    facts.owner_evidence = owner_evidence;
    facts.no_active_recovery = evaluate_recovery_manager(owner_evidence.recovery, RecoveryPhase::ArmIdle).accepted &&
        !owner_evidence.pending_native_recovery;
    facts.native_selection_contract_verified = verify_native_adjustment_body(probe.base);
    facts.race_generation = certificate.race_generation;
    facts.owner_lifetime = certificate.owner_lifetime;
    facts.now_tick_ms = now;
    // Pin the physical actor used by the native transaction. The race
    // certificate actor is a separate lifecycle object and is not comparable.
    facts.human_actor = actor;
    facts.human_controller = controller;
    facts.human_backing = backing;
    facts.human_identity_generation = identity_generation;
    facts.arm_timeout_seconds = timeout_seconds;
    facts.maximum_horizontal_distance = maximum_distance;

    uint64_t sequence = 0;
    if (probe.road_teleport_next_sequence == UINT64_MAX) {
        request.state = road_teleport::State::Rejected;
        request.reason = "road_teleport_sequence_exhausted";
        ReleaseSRWLockExclusive(&probe.lock);
        return false;
    }
    sequence = ++probe.road_teleport_next_sequence;
    const auto result = road_teleport::arm(request, sequence, facts, snapshot, selected);
    if (!result.accepted && request.state == road_teleport::State::Rejected)
        request.sequence = sequence;
    ReleaseSRWLockExclusive(&probe.lock);
    return result.accepted;
}

RoadTeleportStatus physics_probe_road_teleport_status() noexcept {
    AcquireSRWLockExclusive(&probe.lock);
    road_teleport::expire(probe.road_teleport, GetTickCount64());
    const RoadTeleportStatus status{probe.road_teleport.sequence,
        road_teleport::state_name(probe.road_teleport.state),
        probe.road_teleport.reason ? probe.road_teleport.reason : "unknown"};
    ReleaseSRWLockExclusive(&probe.lock);
    return status;
}

std::string physics_probe_road_teleport_status_json() noexcept {
    try {
        road_teleport::Request request{};
        bool enabled = false, installed = false;
        uint64_t attempts = 0, overrides = 0, fallbacks = 0, write_failures = 0;
        uint64_t owner_attempts = 0, owner_accepted = 0, owner_rejected = 0;
        AcquireSRWLockExclusive(&probe.lock);
        road_teleport::expire(probe.road_teleport, GetTickCount64());
        request = probe.road_teleport;
        enabled = probe.road_teleport_enabled;
        installed = probe.installed && probe.patch_intact;
        attempts = probe.road_teleport_selection_attempts;
        overrides = probe.road_teleport_override_count;
        fallbacks = probe.road_teleport_stock_fallback_count;
        write_failures = probe.road_teleport_stack_write_failures;
        owner_attempts = probe.road_teleport_owner_gate_attempts;
        owner_accepted = probe.road_teleport_owner_gate_accepted;
        owner_rejected = probe.road_teleport_owner_gate_rejected;
        ReleaseSRWLockExclusive(&probe.lock);
        std::ostringstream out;
        out << "{\"enabled\":" << (enabled ? "true" : "false")
            << ",\"hook_installed\":" << (installed ? "true" : "false")
            << ",\"state\":" << quote(road_teleport::state_name(request.state))
            << ",\"reason\":" << quote(request.reason ? request.reason : "unknown")
            << ",\"owner_gate_reason\":" << quote(request.owner_gate_reason ? request.owner_gate_reason : "not_evaluated")
            << ",\"owner_gate\":{"
            << "\"accepted\":" << (std::strcmp(request.owner_gate_reason ? request.owner_gate_reason : "", "accepted") == 0 ? "true" : "false")
            << ",\"race_certificate_current\":" << (request.owner_evidence.race_certificate_current ? "true" : "false")
            << ",\"single_human_car\":" << (request.owner_evidence.single_human_car ? "true" : "false")
            << ",\"race_generation\":" << request.owner_evidence.race_generation
            << ",\"owner_lifetime\":" << request.owner_evidence.owner_lifetime
            << ",\"participant_count\":" << request.owner_evidence.participant_count
            << ",\"participant_index\":" << request.owner_evidence.participant_index
            << ",\"participant_identity_verified\":" << (request.owner_evidence.participant_identity_verified ? "true" : "false")
            << ",\"participant_player_type\":" << request.owner_evidence.participant_player_type
            << ",\"tracked_controllers\":" << request.owner_evidence.tracked_controllers
            << ",\"human_controllers\":" << request.owner_evidence.human_controllers
            << ",\"race_owner_actor\":" << quote(hex32(request.owner_evidence.race_owner_actor))
            << ",\"physical_actor\":" << quote(hex32(request.owner_evidence.physical_actor))
            << ",\"physical_player_type\":" << request.owner_evidence.physical_player_type
            << ",\"controller\":" << quote(hex32(request.owner_evidence.controller))
            << ",\"backing\":" << quote(hex32(request.owner_evidence.backing))
            << ",\"links_readable\":" << (request.owner_evidence.links_readable ? "true" : "false")
            << ",\"links_stable\":" << (request.owner_evidence.links_stable ? "true" : "false")
            << ",\"track_generation\":" << request.owner_evidence.track_generation
            << ",\"current_track_generation\":" << request.owner_evidence.current_track_generation
            << ",\"cached_apply_flag_known\":" << (request.owner_evidence.cached_apply_flag_known ? "true" : "false")
            << ",\"cached_apply_flag_set\":" << (request.owner_evidence.cached_apply_flag_set ? "true" : "false")
            << ",\"current_apply_flag_readable\":" << (request.owner_evidence.current_apply_flag_readable ? "true" : "false")
            << ",\"current_apply_flag\":" << unsigned(request.owner_evidence.current_apply_flag)
            << ",\"apply_flag_snapshot_stale\":" << (request.owner_evidence.cached_apply_flag_known && request.owner_evidence.current_apply_flag_readable && request.owner_evidence.cached_apply_flag_set != (request.owner_evidence.current_apply_flag != 0) ? "true" : "false")
            << ",\"apply_flag_source\":\"current_native_backing_P_plus_0x33\""
            << ",\"pending_native_recovery\":" << (request.owner_evidence.pending_native_recovery ? "true" : "false")
            << ",\"recovery_manager\":" << quote(hex32(request.owner_evidence.recovery.manager))
            << ",\"recovery_countdown_array\":" << quote(hex32(request.owner_evidence.recovery.countdown_array))
            << ",\"native_participant_count\":" << request.owner_evidence.recovery.participant_count
            << ",\"recovery_state_readable\":" << (request.owner_evidence.recovery.readable ? "true" : "false")
            << ",\"recovery_state_stable\":" << (request.owner_evidence.recovery.stable ? "true" : "false")
            << ",\"recovery_countdown\":" << request.owner_evidence.recovery.countdown << "}"
            << ",\"sequence\":" << request.sequence
            << ",\"race_generation\":" << request.race_generation
            << ",\"owner_lifetime\":" << request.owner_lifetime
            << ",\"owner_gate_attempts\":" << owner_attempts
            << ",\"owner_gate_accepted\":" << owner_accepted
            << ",\"owner_gate_rejected\":" << owner_rejected
            << ",\"human_actor\":" << quote(hex32(request.human_actor))
            << ",\"reset_manager\":" << quote(hex32(request.reset_manager))
            << ",\"route_object\":" << quote(hex32(request.route_object))
            << ",\"route_generation\":" << request.race_generation
            << ",\"route_snapshot_sequence\":" << request.route_sequence
            << ",\"route_fingerprint\":" << quote(hex64(request.route_fingerprint))
            << ",\"marker_ordinal\":";
        if (request.marker_ordinal == UINT32_MAX) out << "null"; else out << request.marker_ordinal;
        out << ",\"original_marker_ordinal\":";
        if (request.original_marker_ordinal == UINT32_MAX) out << "null"; else out << request.original_marker_ordinal;
        out << ",\"native_adjusted_marker_ordinal\":";
        if (request.native_adjusted_ordinal == UINT32_MAX) out << "null"; else out << request.native_adjusted_ordinal;
        out << ",\"target\":[" << std::setprecision(9) << request.target.x << ','
            << request.target.y << ',' << request.target.z << ']'
            << ",\"native_thread_id\":" << request.native_thread_id
            << ",\"input_overridden\":" << (request.input_overridden ? "true" : "false")
            << ",\"native_result_overridden\":false"
            << ",\"native_selection_contract_verified\":" << (request.native_selection_contract_verified ? "true" : "false")
            << ",\"selection_countdown_array\":" << quote(hex32(request.selection_recovery.countdown_array))
            << ",\"selection_countdown\":" << request.selection_recovery.countdown
            << ",\"selection_participant_count\":" << request.selection_recovery.participant_count
            << ",\"native_publication_seen\":" << (request.native_publication_seen ? "true" : "false")
            << ",\"native_transaction_candidate\":" << request.native_transaction_candidate
            << ",\"stock_adjustment_returned\":" << (request.stock_adjustment_returned ? "true" : "false")
            << ",\"matrix_committed\":" << (request.matrix_committed ? "true" : "false")
            << ",\"matrix_matches_target_xz\":" << (request.matrix_matches_target ? "true" : "false")
            << ",\"committed_translation\":[" << request.committed_translation.x << ','
            << request.committed_translation.y << ',' << request.committed_translation.z << ']'
            << ",\"native_consumed\":" << (request.native_consumed ? "true" : "false")
            << ",\"controller_backing\":" << quote(hex32(request.controller_backing))
            << ",\"active_consumer_calls\":" << request.active_consumer_calls
            << ",\"chassis_matches_destination_xz\":" << (request.chassis_matches_destination ? "true" : "false")
            << ",\"chassis_after\":[" << request.chassis_after.x << ',' << request.chassis_after.y << ',' << request.chassis_after.z << ']'
            << ",\"clear_writer\":" << quote(request.clear_writer ? request.clear_writer : "none")
            << ",\"native_clear_seen\":" << (request.native_clear_seen ? "true" : "false")
            << ",\"settled_zero_seen\":" << (request.settled_zero_seen ? "true" : "false")
            << ",\"physical_clearance_verified\":false"
            << ",\"selection_attempts\":" << attempts
            << ",\"overrides\":" << overrides
            << ",\"stock_fallbacks\":" << fallbacks
            << ",\"native_stack_write_failures\":" << write_failures
            << ",\"direct_physics_or_broker_writes\":false}";
        return out.str();
    } catch (...) {
        return "{\"enabled\":false,\"state\":\"unavailable\",\"reason\":\"status_serialization_failed\"}";
    }
}

std::string physics_probe_road_target_preview_json(float camera_x, float camera_y,
                                                   float camera_z, bool freecam_active,
                                                   uint64_t race_generation,
                                                   uint64_t owner_lifetime) noexcept {
    try {
        bool enabled = false, context_valid = false;
        uint64_t context_generation = 0, context_owner = 0;
        double radius = 60.0;
        const char* last_failure = "not_requested";
        road_target::LiveSnapshot snapshot{};
        AcquireSRWLockShared(&probe.lock);
        enabled = InterlockedCompareExchange(&probe.route_preview_enabled, 0, 0) != 0;
        context_valid = probe.route_context_valid;
        context_generation = probe.route_context_race_generation;
        context_owner = probe.route_context_owner_lifetime;
        radius = probe.route_preview_radius;
        last_failure = probe.route_last_failure;
        snapshot = probe.route_snapshot;
        ReleaseSRWLockShared(&probe.lock);

        std::ostringstream out;
        out << "{\"phase\":\"ROAD-TRANSACTION-CORRELATION-1\",\"enabled\":" << (enabled ? "true" : "false")
            << ",\"route_source\":"
            << quote(enabled && snapshot.source_native_live ? "native_live_raceline" : "unavailable")
            << ",\"race_scene\":" << (context_valid ? quote("RaceTest/France1") : "null")
            << ",\"snapshot_available\":" << (snapshot.available ? "true" : "false")
            << ",\"route_generation\":" << snapshot.race_generation
            << ",\"owner_lifetime\":" << snapshot.owner_lifetime
            << ",\"snapshot_sequence\":" << snapshot.sequence
            << ",\"route_count\":" << snapshot.count
            << ",\"route_stride\":" << snapshot.stride
            << ",\"position_offset\":" << snapshot.position_offset
            << ",\"route_fingerprint\":" << quote(hex64(snapshot.fingerprint))
            << ",\"preview_search_radius_horizontal\":" << radius
            << ",\"physical_placement_verified\":false";

        const bool current_identity = context_valid && race_generation != 0 && owner_lifetime != 0 &&
            race_generation == context_generation && owner_lifetime == context_owner;
        const bool snapshot_current = current_identity && snapshot.available &&
            snapshot.race_generation == context_generation &&
            snapshot.owner_lifetime == context_owner;
        out << ",\"snapshot_current\":" << (snapshot_current ? "true" : "false");
        if (!enabled) {
            out << ",\"status\":\"disabled\",\"reason\":\"disabled_by_config\"}";
            return out.str();
        }
        if (!current_identity) {
            out << ",\"status\":\"unavailable\",\"reason\":"
                << quote(context_valid ? "current_race_identity_mismatch" :
                                       "current_supported_france1_race_certificate_required") << '}';
            return out.str();
        }
        if (!snapshot.available) {
            const char* reason = snapshot.reason ? snapshot.reason : last_failure;
            out << ",\"status\":\"unavailable\",\"reason\":"
                << quote(reason ? reason : "native_live_route_not_captured") << '}';
            return out.str();
        }

        if (!freecam_active) {
            out << ",\"status\":\"route_ready_freecam_inactive\",\"reason\":\"freecam_inactive\"}";
            return out.str();
        }
        out << ",\"camera_position\":[";
        if (std::isfinite(camera_x) && std::isfinite(camera_y) && std::isfinite(camera_z))
            out << std::setprecision(9) << camera_x << ',' << camera_y << ',' << camera_z;
        else
            out << "null,null,null";
        out << ']';

        const auto selected = road_target::nearest_marker(
            snapshot, {camera_x, camera_y, camera_z}, radius,
            race_generation, owner_lifetime, true);
        out << ",\"status\":" << quote(selected.found ?
            (selected.route_candidate_valid ? "candidate" : "candidate_rejected") : "unavailable")
            << ",\"reason\":" << quote(selected.reason ? selected.reason : "unknown")
            << ",\"route_candidate_valid\":" << (selected.route_candidate_valid ? "true" : "false")
            << ",\"nearest_tie_count\":" << selected.nearest_tie_count
            << ",\"height_ambiguous\":" << (selected.height_ambiguous ? "true" : "false")
            << ",\"selected_marker\":";
        if (!selected.found) {
            out << "null}";
            return out.str();
        }
        out << "{\"ordinal\":" << selected.marker_ordinal
            << ",\"position\":[" << std::setprecision(9) << selected.marker.x << ','
            << selected.marker.y << ',' << selected.marker.z << ']'
            << ",\"horizontal_distance\":" << selected.horizontal_distance
            << ",\"vertical_difference\":" << selected.vertical_difference
            << ",\"world_distance\":" << selected.world_distance << "}}";
        return out.str();
    } catch (...) {
        return "{\"enabled\":true,\"route_source\":\"unavailable\",\"status\":\"unavailable\",\"physical_placement_verified\":false,\"reason\":\"preview_serialization_failed\"}";
    }
}

} // namespace gfx2

extern "C" {
uintptr_t road_teleport_adjust_original = 0;

void road_teleport_adjust_bridge_observe(
    const gfx2::RoadAdjustSaved* saved) noexcept {
    gfx2::road_teleport_selection_observe(saved);
}

void road_teleport_adjust_bridge_after(
    gfx2::RoadAdjustSaved* saved) noexcept {
    gfx2::road_teleport_selection_after(saved);
}
}

#include "road_teleport_bridge.inc"
