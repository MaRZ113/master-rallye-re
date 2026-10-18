#pragma once
#include "fleet_frame_policy.hpp"
namespace gfx2::frontendmodelintegration {
// One race certificate per device/reset/frame for all race-fleet paths. In
// menus and multi-car races this rejects before caller-stack walks, buffer
// copies and identity hashing; each path still re-verifies its own live owner.
// The certificate is cached per frame; the participant part of the decision is per draw.
inline bool fleet_frame_admitted(Device8& d)noexcept{
 struct Cache{uint64_t device=UINT64_MAX,reset=UINT64_MAX,frame=UINT64_MAX;bool single=false;RaceCertificate race{};};
 static thread_local Cache cache;
 auto* e=d.ps2_port();if(!e)return false;
 const uint64_t device=d.trace.device_id(),reset=e->reset_generation(),frame=d.trace.frame_number();
 if(cache.device!=device||cache.reset!=reset||cache.frame!=frame){
  cache.device=device;cache.reset=reset;cache.frame=frame;cache.race=courseintegration::certificate(d,cache.single);
 }
 return ps2port::fleet_single_car_race(cache.single,cache.race);
}
}
