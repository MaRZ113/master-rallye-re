#pragma once
// COURSE-RENDER-FIX1 native side of render_queue_order.hpp: a call-site patch on the single call of the queue flush
// (MRallye.exe 0x56bab8 -> 0x562810, retail image base 0x400000, bytes verified) that runs prepare() on the queue object
// right before the engine sorts and draws it. Same mechanism as the baseline's camera submit hook (game_fov.cpp): the
// original ECX, flags, registers and x87/SSE state survive and control continues in the original function.
//
// ReflectionWorldFirst=1 (default with Reflection=4): the records of the race cars (proven participants, bodies and
// wheels) are sorted behind every other opaque record. ReflectionStageDiag=1 additionally writes ps2_render_queue
// records (the submitted records of the flush grouped by owner and material id) for the frames that get a stage report.
// Anything unexpected leaves the queue untouched.
#include "render_queue_order.hpp"
#include "reflection_native_integration.hpp"
#include "frontend_model_native.hpp"   // brings fleet_participant_native.hpp
#include "game_fov.hpp"
#include <array>
#include <intrin.h>

namespace gfx2::renderorder {

struct State {
    Device8* device = nullptr;
    bool modify = false, observe = false, installed = false, failed = false;
    const char* reason = "not_requested";
    uintptr_t original = 0;
    uint64_t dump_frame = UINT64_MAX; unsigned dump_flush = 0; unsigned dumps = 0;
    ps2port::RenderQueueStats stats;
    CallPatch patch;
};
inline State& state() noexcept { static State s; return s; }
inline uintptr_t original_flush = 0;

namespace detail {
class Memory final : public PatchMemory {
public:
    bool read(void* d, const void* s, size_t n) noexcept override { return frontendmodelintegration::read_leaf(reinterpret_cast<uintptr_t>(s), d, n); }
    bool write(void* d, const void* s, size_t n) noexcept override { __try { std::memcpy(d, s, n); return true; } __except (EXCEPTION_EXECUTE_HANDLER) { return false; } }
    bool protect(void* p, size_t n, DWORD v, DWORD& old) noexcept override { return VirtualProtect(p, n, v, &old) != FALSE; }
    bool flush(void* p, size_t n) noexcept override { return FlushInstructionCache(GetCurrentProcess(), p, n) != FALSE; }
};
inline bool write_word(uintptr_t address, uint32_t value) noexcept {
    if (address < 0x10000 || (address & 3)) return false;
    __try { *reinterpret_cast<volatile uint32_t*>(address) = value; return true; } __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
}
}

inline void __stdcall prepare(uintptr_t queue) noexcept {
    auto& s = state();
    try {
        if ((!s.modify && !s.observe) || !s.device) return;
        Device8& d = *s.device;
        if (!d.trace.scene_active || GetCurrentThreadId() != d.trace.render_thread_id()) return;
        const auto& table = frontendmodelintegration::fleet_participant_table(d);
        const auto read = [](uintptr_t a, uint32_t& v) noexcept { return frontendmodelintegration::word(a, v); };
        const auto is_vehicle = [&](uint32_t owner) noexcept { uint32_t index = 0; ps2port::FleetRole role = ps2port::FleetRole::None; unsigned wheel = 0; return table.find(owner, index, role, wheel); };
        auto* x = d.ps2_port();
        auto* p = x ? x->reflection() : nullptr;
        const uint64_t frame = d.trace.frame_number();
        if (s.dump_frame != frame) { s.dump_frame = frame; s.dump_flush = 0; }
        const bool dump = s.observe && p && x->ledger_enabled() && p->mixed_capture().decision().stage_next() && s.dump_flush < 8 && s.dumps < 256;
        ps2port::RenderQueueSnapshot snapshot;
        // A table that is not proven moves nothing (menu, loading, split-screen ambiguity): the engine order stays.
        const bool modify = s.modify && table.valid;
        ps2port::prioritize_vehicle_records(queue, read, detail::write_word, is_vehicle, s.stats, dump ? &snapshot : nullptr, modify);
        if (dump && snapshot.records) {
            ++s.dumps;
            x->diag_write(ps2port::render_queue_json(snapshot, frame, s.dump_flush++, modify));
        }
    } catch (...) {}
}

// Original ECX (the queue), flags, registers, x87/SSE state and the return address survive; the original flush runs next.
__declspec(naked) inline void flush_bridge() {
    __asm {
        pushfd
        pushad
        mov ebp, esp
        and esp, -16
        sub esp, 528
        fxsave [esp]
        cld
        push ecx
        call prepare
        fxrstor [esp]
        mov esp, ebp
        popad
        popfd
        jmp dword ptr [original_flush]
    }
}

// Installed once, kept for the process lifetime (the module is pinned). Failure leaves the engine untouched.
inline bool ensure_installed(Device8& d, bool modify, bool observe) noexcept {
    auto& s = state();
    s.device = &d; s.modify = modify; s.observe = observe;
    if (s.installed || s.failed || (!modify && !observe)) return s.installed;
    const auto base = reinterpret_cast<uintptr_t>(GetModuleHandleW(nullptr));
    if (base != 0x400000) { s.failed = true; s.reason = "unexpected_image_base"; return false; }
    constexpr std::array<unsigned char, 5> call_bytes = {0xe8, 0x53, 0x6d, 0xff, 0xff};
    constexpr std::array<unsigned char, 9> flush_bytes = {0x83, 0xec, 0x0c, 0x53, 0x8b, 0xd9, 0x8b, 0x4b, 0x44};
    std::array<unsigned char, 9> seen{};
    if (!frontendmodelintegration::read_leaf(base + ps2port::kQueueFlushRva, seen.data(), seen.size()) || seen != flush_bytes) {
        s.failed = true; s.reason = "flush_prologue_mismatch"; return false;
    }
    HMODULE pinned = nullptr;
    if (!GetModuleHandleExW(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS | GET_MODULE_HANDLE_EX_FLAG_PIN, reinterpret_cast<LPCWSTR>(&flush_bridge), &pinned)) {
        s.failed = true; s.reason = "module_pin_failed"; return false;
    }
    original_flush = base + ps2port::kQueueFlushRva;
    detail::Memory memory;
    if (!s.patch.install(memory, reinterpret_cast<void*>(base + ps2port::kQueueFlushCallRva), reinterpret_cast<uintptr_t>(&flush_bridge), call_bytes)) {
        s.failed = true; s.reason = "call_site_mismatch_or_patch_failed"; return false;
    }
    s.installed = true; s.reason = "installed";
    return true;
}

inline std::string status_json() {
    const auto& s = state();
    const auto& t = s.stats;
    return std::string("{\"modify\":") + (s.modify ? "true" : "false") + ",\"observe\":" + (s.observe ? "true" : "false") +
        ",\"installed\":" + (s.installed ? "true" : "false") + ",\"reason\":" + ps2diag::quote(s.reason) +
        ",\"flushes\":" + std::to_string(t.flushes) + ",\"records\":" + std::to_string(t.records) +
        ",\"vehicle_records\":" + std::to_string(t.vehicle_records) + ",\"promoted\":" + std::to_string(t.promoted) +
        ",\"rejected\":" + std::to_string(t.rejected) + ",\"unreadable\":" + std::to_string(t.unreadable) +
        ",\"last\":{\"records\":" + std::to_string(t.last_records) + ",\"vehicles\":" + std::to_string(t.last_vehicles) +
        ",\"promoted\":" + std::to_string(t.last_promoted) + ",\"reason\":" + ps2diag::quote(t.last_reason) + "}}";
}

} // namespace gfx2::renderorder
