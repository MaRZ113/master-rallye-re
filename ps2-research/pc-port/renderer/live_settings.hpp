#pragma once
// PAUSE-MENU1: draw-time PS2 effects switched off live from the race pause SETTINGS (pause_settings.hpp).
// Each gate sits next to the matching PS2PerfBypassKey check, so OFF means exactly what the validated F7 bypass does:
// the native draw is kept or the extra PS2 draw is skipped. Nothing here loads or unloads assets.
#include <atomic>
namespace gfx2::ps2port::live {
enum : unsigned { Grass=1u, Ground=2u, Forest=4u, Water=8u, Birds=16u, Blur=32u, Color=64u, Output=128u };
inline std::atomic<unsigned>& off_bits() noexcept { static std::atomic<unsigned> bits{0}; return bits; }
inline bool disabled(unsigned bit) noexcept { return (off_bits().load(std::memory_order_relaxed)&bit)!=0; }
inline void set(unsigned bit,bool on) noexcept {
    if(on)off_bits().fetch_and(~bit,std::memory_order_relaxed);else off_bits().fetch_or(bit,std::memory_order_relaxed);
}
}  // namespace gfx2::ps2port::live
