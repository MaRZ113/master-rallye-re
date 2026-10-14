#pragma once
#include "buffer_provenance.hpp"
#include <cstdint>

namespace gfx2::ps2port {
// Retention, never revalidation: raw escapes, failed uploads and poisoned data
// remain unknown. The owner must still clear bindings and recheck live state.
inline bool retain_managed_mirror_on_reset(bool enabled, bool reset_reason,
    const BufferMirror& mirror, uint64_t current_generation,
    uint64_t registered_proxy_generation) noexcept {
    return enabled && reset_reason && mirror.available && !mirror.poisoned &&
        (mirror.pool==D3DPOOL_MANAGED || mirror.pool==D3DPOOL_SYSTEMMEM) &&
        mirror.generation && mirror.generation==current_generation &&
        mirror.generation==registered_proxy_generation;
}
}
