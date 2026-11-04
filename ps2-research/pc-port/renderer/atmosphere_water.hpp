#pragma once
#include "atmosphere_scene.hpp"
namespace gfx2::atmosphere {
// Common shader/base_water secondary, NOT a course/object geometry whitelist.
// Retail DataGx/Misc/Water/watersurface3.dxt SHA a7b158b846148b37fe8b9caab374137c7effd252521885c5f4a62cbac1e69c03.
inline bool pc_water_secondary(const std::string& sha)noexcept{
    return sha=="2cc07bb39117f1f0c102e6007a9dfb2245a7f6180a578352d6b7ba09b2f705f6"||sha=="7a3ea0f30ef0df4c894739a71ff1fa83b9b0b0e255873a0c7b71d66299c5b719";
}
inline DWORD pc_water_factor(const Lighting& s,DWORD original_factor=0xffffffffu)noexcept{
    DWORD out=original_factor&0xff000000u;
    for(unsigned i=0;i<3;++i){const unsigned shift=(2-i)*8;const float fog=float((s.fog>>shift)&255)/255;
        // Sky ambient dominates water; a small fog contribution avoids the
        // unrelated bright blue surface under the retained sunset sky.
        const float fog_mix=s.fog_enabled?.2f:0.f;
        const float gain=std::clamp((s.ambient[i]*(1-fog_mix)+fog*fog_mix)*s.world_brightness*s.exposure,0.f,1.f);
        const float effective=s.active()?1+std::clamp(s.strength,0.f,1.f)*(gain-1):1;
        out|=DWORD(std::clamp(std::lround(effective*255),0l,255l))<<shift;
    }return out;
}
}
