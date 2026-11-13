#pragma once
// R-SURFACE1 G1.2 PERF: the grime pass applies its ~45 states with one D3D8 state block and restores the previous values
// with a second one (Capture + Apply), instead of a Get/Set/notify per state (~30 us per pass). D3D8 requires state blocks to
// be deleted before IDirect3DDevice8::Reset: PS2PortExtension::fleet_before_reset() calls grime_blocks_before_reset().
#include "sdk.hpp"
namespace gfx2::grimeintegration {
struct StateBlocks { IDirect3DDevice8* device = nullptr; DWORD apply = 0, save = 0; bool failed = false; uint64_t created = 0;
                     DWORD sheen_apply = 0, sheen_save = 0; bool sheen_failed = false; };   // G3.1 wet sheen pass
inline StateBlocks& state_blocks() noexcept { static StateBlocks b; return b; }
inline void grime_blocks_before_reset() noexcept {
    auto& b = state_blocks();
    if (b.device) { for (DWORD* t : {&b.apply, &b.save, &b.sheen_apply, &b.sheen_save}) if (*t) b.device->DeleteStateBlock(*t); }
    b.apply = b.save = b.sheen_apply = b.sheen_save = 0; b.device = nullptr; b.failed = b.sheen_failed = false;
}
// G3.1: called by the reflection scope right after a native draw, while the draw's reflection (PC live reflection or PS2
// reflection: texture, env coordinates, transform) is still applied, so the wet sheen boosts exactly that reflection.
// Installed by atmosphere_native.hpp.
inline void (*wet_sheen_hook)(void* device) noexcept = nullptr;
}
