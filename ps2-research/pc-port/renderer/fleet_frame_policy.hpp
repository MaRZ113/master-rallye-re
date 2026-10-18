#pragma once
#include "race_epoch.hpp"
#include "fleet_participants.hpp"
namespace gfx2::ps2port {
// Every race-fleet CAR, wheel and lamp effect requires a live single-human-car
// race with exactly one participant, or (PS2FleetAllCars=1) a live single-camera
// race certificate plus the exact participant egg chain of the current draw for
// the same race generation and owner (fleet_participants.hpp). Shared by every
// per-draw gate and final re-check.
inline bool fleet_participant_race(bool single,const RaceCertificate& race,const FleetActive& a)noexcept{
 return a.active&&single&&race.valid&&race.race_generation&&race.race_generation==a.race_generation&&
  race.owner_lifetime==a.owner_lifetime&&race.participant_count>=1&&race.participant_count<=kFleetMaxCars&&a.index<race.participant_count;
}
inline bool fleet_single_car_race(bool single,const RaceCertificate& race,const FleetActive& a=fleet_active)noexcept{
 return (single&&race.valid&&race.single_human_car_race&&race.participant_count==1)||fleet_participant_race(single,race,a);
}
// Cheap per-draw shape test for the frontend model path: the active profile's
// sources (or the X-Trail COMPLETE sources) and, while fleet selection is on,
// any unique frontend fleet source. Only draws passing this can be selected.
template<class Source>
inline bool frontend_shape_candidate(const Source* sources,unsigned source_count,unsigned vertices,unsigned triangles)noexcept{
 for(unsigned i=0;i<source_count;++i)if(sources[i].vertices==vertices&&sources[i].triangles==triangles)return true;
 return false;
}
}
