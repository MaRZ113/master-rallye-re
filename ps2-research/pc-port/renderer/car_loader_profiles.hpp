#pragma once
#include "race_fleet_registry.hpp"
namespace gfx2::ps2port {
struct CarLoaderProfiles {
 std::array<std::array<FrontendSource,30>,std::size(kRaceFleetProfiles)> source{};
 std::array<FleetProfile,std::size(kRaceFleetProfiles)> profile{};
 CarLoaderProfiles(){for(unsigned i=0;i<profile.size();++i){const auto& r=kRaceFleetProfiles[i];for(unsigned j=0;j<r.pcDrawCount;++j)source[i][j]={r.source[j].geometry,r.source[j].vertices,r.source[j].triangles};profile[i]={r.family,r.ps2Family,r.filename,r.sha,r.size,r.vertices,r.indices,r.textures,r.ps2Meshes,r.pcDrawCount,source[i].data(),nullptr,r.mixed};}}
};
inline const CarLoaderProfiles kCarLoaderProfiles{};
}
