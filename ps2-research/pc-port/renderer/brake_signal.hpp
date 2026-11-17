#pragma once
#include <array>
#include <cstdint>
// RCX-GLINT1c: per-car "brake lamp ON" signal. The PS2 fleet lamp path (fleet_lamp_native.hpp) draws the brake ON
// core / additive glow layers, which the game submits only while the car brakes; those draws never reach the
// Atmosphere observers. The fleet path notes the owner instance here, the lamp rigs read it (day and night).
namespace gfx2::brakesignal {
struct Entry {uintptr_t instance=0;uint64_t frame=UINT64_MAX;};
inline std::array<Entry,32> entries{};
inline uint64_t notes=0;
inline void note(uintptr_t instance,uint64_t frame)noexcept{
    if(!instance)return;++notes;Entry* slot=nullptr;for(auto& e:entries)if(e.instance==instance){slot=&e;break;}
    if(!slot){slot=&entries[0];for(auto& e:entries){if(!e.instance){slot=&e;break;}if(e.frame<slot->frame)slot=&e;}}
    slot->instance=instance;slot->frame=frame;
}
inline bool recent(uintptr_t instance,uint64_t frame)noexcept{
    for(const auto& e:entries)if(e.instance==instance)return e.frame!=UINT64_MAX&&e.frame+2>=frame;return false;
}
}
