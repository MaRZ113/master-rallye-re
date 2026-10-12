#pragma once
#include <cstdint>

namespace gfx2 {
// PUSHFD/PUSHAD image at the exact ResetManager callsite. saved_esp points to
// the caller's stack after PUSHFD; the selected ordinal is at saved_esp+12.
struct RoadAdjustSaved {
    uint32_t edi, esi, ebp, saved_esp, ebx, edx, ecx, eax, flags;
    uint32_t return_pc, participant_index, marker_ordinal, route_object;
};
static_assert(sizeof(RoadAdjustSaved) == 52, "x86 recovery bridge stack image");
}

extern "C" uintptr_t road_teleport_adjust_original;
extern "C" void road_teleport_adjust_bridge_observe(const gfx2::RoadAdjustSaved*) noexcept;
extern "C" void road_teleport_adjust_bridge_after(gfx2::RoadAdjustSaved*) noexcept;
extern "C" void road_teleport_adjust_bridge();
