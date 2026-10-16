#pragma once
#include "frontend_model.hpp"
#include "kia_wheel_registry.hpp"
namespace gfx2::ps2port {
inline const auto kKiaWheelLoaderSources=[](){std::array<FrontendSource,4> out{};for(unsigned i=0;i<4;++i)out[i]={kKiaWheelSources[i].geometry,kKiaWheelSources[i].vertices,kKiaWheelSources[i].triangles};return out;}();
inline const FleetProfile kKiaWheelLoader={"KiaSportage","KIASPORTAGE","KIASPORTAGE-WHEEL-FLEET.ps2model","f213128983480386efc336816b53d7df7130f3fcfc40f5595a9bfd5e464816f1",78401,300,756,6,4,4,kKiaWheelLoaderSources.data(),nullptr,kKiaWheelMixed};
}
