#pragma once
#include "reflection_pilot.hpp"
namespace gfx2::ps2port {
inline constexpr const char* kTerranoBumperUvTopology="0a2b22490eb19dea97565d3f235d52dc61c18bd13c31c5f6d31f4a523757609f";
inline constexpr const char* kTerranoLampOffUvTopology="c0d72e3faadd6286af69dcf265ce53151f79176be84a721ad6ef5fa81fd18e86";
inline constexpr const char* kXtrailLampOffPositionUv="49c1ec25031b36c03036b2b796e07fa0d45fc16ac32a59cf9df9cd6934fd9c9f";
std::string position_uv_corner_sha(const DrawSnapshot&);
std::string damage_uv_topology_sha(const DrawSnapshot&);
ReflectionIdentity damage_compatible_identity(const ReflectionSnapshot&,std::string_view,std::string_view,uint64_t,bool);
}
