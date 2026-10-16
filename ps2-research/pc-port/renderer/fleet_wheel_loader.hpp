#pragma once
#include "frontend_model.hpp"
#include "fleet_wheel_registry.hpp"
namespace gfx2::ps2port {
struct FleetWheelLoaders {std::array<std::array<FrontendSource,16>,24> sources{};std::array<FleetProfile,24> profiles{};FleetWheelLoaders(){for(unsigned i=0;i<24;++i){const auto& p=*kPort3WheelProfiles[i];for(unsigned j=0;j<p.pcDrawCount;++j)sources[i][j]={p.source[j].geometry,p.source[j].vertices,p.source[j].triangles};profiles[i]={p.family,p.ps2Family,p.filename,p.sha,p.size,p.vertices,p.indices,p.textures,p.ps2Meshes,p.pcDrawCount,sources[i].data(),nullptr,p.mixed};}}};
inline const FleetWheelLoaders kFleetWheelLoaders{};
inline unsigned fleet_wheel_family(const char* family)noexcept{for(unsigned i=0;i<24;++i)if(!std::strcmp(kPort3WheelProfiles[i]->ps2Family,family))return i;return UINT_MAX;}
}
