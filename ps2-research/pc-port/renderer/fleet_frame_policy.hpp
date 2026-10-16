#pragma once
#include "race_epoch.hpp"
namespace gfx2::ps2port {
// Every race-fleet CAR, wheel and lamp effect requires a live single-human-car
// race with exactly one participant. Shared by the per-frame draw gate.
inline bool fleet_single_car_race(bool single,const RaceCertificate& race)noexcept{
 return single&&race.valid&&race.single_human_car_race&&race.participant_count==1;
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
