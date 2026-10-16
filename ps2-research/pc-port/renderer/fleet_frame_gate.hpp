#pragma once
#include "fleet_frame_policy.hpp"
namespace gfx2::frontendmodelintegration {
// One race certificate per device/reset/frame for all race-fleet paths. In
// menus and multi-car races this rejects before caller-stack walks, buffer
// copies and identity hashing; each path still re-verifies its own live owner.
inline bool fleet_frame_admitted(Device8& d)noexcept{
 struct Cache{uint64_t device=UINT64_MAX,reset=UINT64_MAX,frame=UINT64_MAX;bool admitted=false;};
 static thread_local Cache cache;
 auto* e=d.ps2_port();if(!e)return false;
 const uint64_t device=d.trace.device_id(),reset=e->reset_generation(),frame=d.trace.frame_number();
 if(cache.device!=device||cache.reset!=reset||cache.frame!=frame){
  bool single=false;const auto race=courseintegration::certificate(single);
  cache={device,reset,frame,ps2port::fleet_single_car_race(single,race)};
 }
 return cache.admitted;
}
}
