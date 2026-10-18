#pragma once
// PS2FleetAllCars=1 (docs/fleet-all-cars): binds every race-fleet draw entry to the participant whose egg
// owns the draw's instance. Without the key, or for any draw whose instance is not in the proven table,
// no scope is set and every path keeps its original single-car behaviour.
#include "fleet_participants.hpp"
#include <optional>
namespace gfx2::frontendmodelintegration {
struct FleetParticipantFrame {
 uint64_t device=UINT64_MAX,reset=UINT64_MAX,frame=UINT64_MAX;ps2port::FleetParticipantTable table{};
 uint64_t logged_generation=0;uint32_t logged_proven=UINT32_MAX;unsigned logs=0;
};
inline FleetParticipantFrame& fleet_participant_frame()noexcept{static thread_local FleetParticipantFrame state;return state;}
inline ps2port::FleetParticipantResolver& fleet_participant_resolver()noexcept{static thread_local ps2port::FleetParticipantResolver resolver;return resolver;}
inline std::string fleet_participant_json(const ps2port::FleetParticipantTable& t){
 std::string s="{\"type\":\"ps2_fleet_participants\",\"race_generation\":"+std::to_string(t.race_generation)+",\"owner_lifetime\":"+std::to_string(t.owner_lifetime)+",\"count\":"+std::to_string(t.count)+",\"proven\":"+std::to_string(t.proven)+",\"local\":"+(t.local==UINT32_MAX?std::string("null"):std::to_string(t.local))+",\"reason\":"+quote(t.reason)+",\"cars\":[";
 for(uint32_t i=0;i<t.count&&i<t.cars.size();++i){const auto& c=t.cars[i];if(i)s+=",";
  s+="{\"car\":"+std::to_string(i)+",\"valid\":"+(c.valid?"true":"false")+",\"reason\":"+quote(c.reason)+",\"player_type\":"+std::to_string(c.player_type)+",\"folder\":"+quote(c.folder.data())+",\"wheel_mask\":"+std::to_string(c.wheel_mask)+(c.model_text[0]?",\"model_text\":"+quote(c.model_text.data()):std::string())+"}";}
 return s+"]}";
}
// One live table per device/reset/frame, built from the frame's race certificate.
inline const ps2port::FleetParticipantTable& fleet_participant_table(Device8& d)noexcept{
 auto& f=fleet_participant_frame();auto* e=d.ps2_port();
 const uint64_t device=d.trace.device_id(),reset=e?e->reset_generation():0,frame=d.trace.frame_number();
 if(f.device==device&&f.reset==reset&&f.frame==frame)return f.table;
 f.device=device;f.reset=reset;f.frame=frame;f.table={};ps2port::perf::Timer timer(ps2port::perf::Participants);
 try{
  bool single=false;const auto race=courseintegration::certificate(d,single);
  if(!single||!race.valid||reinterpret_cast<uintptr_t>(GetModuleHandleW(nullptr))!=0x400000)return f.table;
  ps2port::HudLiveMemory memory;f.table=fleet_participant_resolver().resolve(memory,0x400000,race,ps2port::ps2_race_certifier().split_screen()?2u:1u);
  if(f.table.race_generation!=f.logged_generation){f.logged_generation=f.table.race_generation;f.logged_proven=UINT32_MAX;f.logs=0;}
  // Bounded: every change of the proven set, at most 16 records per race generation.
  if(f.table.proven!=f.logged_proven&&f.logs<16){f.logged_proven=f.table.proven;++f.logs;session().write(fleet_participant_json(f.table));}
 }catch(...){f.table={};}
 return f.table;
}
// Scope for one draw at the shared emitter: the queue record's instance must be a proven participant body
// or wheel instance. Nested draw entries reuse the outer scope.
class FleetParticipantScope {
 std::optional<ps2port::FleetActiveScope> scope_;
public:
 FleetParticipantScope(Device8& d,uintptr_t pc)noexcept{
  auto* e=d.ps2_port();if(!e||!e->fleet_all_cars()||ps2port::fleet_active.active)return;
  const auto exe=reinterpret_cast<uintptr_t>(GetModuleHandleW(nullptr));
  if(pc!=exe+0x17707e||!d.trace.scene_active||GetCurrentThreadId()!=d.trace.render_thread_id()||!caller_stack)return;
  // The four draw entries of one DrawIndexedPrimitive call share one lookup.
  struct Last{uint64_t serial=UINT64_MAX,device=UINT64_MAX,frame=UINT64_MAX;uintptr_t stack=0;bool found=false;ps2port::FleetActive active{};};static thread_local Last last;
  const uint64_t device=d.trace.device_id(),frame=d.trace.frame_number();
  if(last.serial!=caller_serial||last.device!=device||last.frame!=frame||last.stack!=caller_stack){
   last={caller_serial,device,frame,caller_stack,false,{}};
   const auto& t=fleet_participant_table(d);if(!t.valid)return;
   uintptr_t mesh=0,instance=0;if(!pointer_word(caller_stack+0x34,mesh)||!ps2port::frontend_queue_owner(caller_stack,exe,mesh,word,instance))return;
   uint32_t index=UINT32_MAX;ps2port::FleetRole role=ps2port::FleetRole::None;unsigned wheel=4;
   if(instance>UINT32_MAX||!t.find(static_cast<uint32_t>(instance),index,role,wheel))return;
   auto& a=last.active;a.active=true;a.local=t.local==index;a.index=index;a.role=role;a.wheel=wheel;a.race_generation=t.race_generation;a.owner_lifetime=t.owner_lifetime;a.frame=frame;a.folder=t.cars[index].folder;last.found=true;
  }
  if(last.found)scope_.emplace(last.active);
 }
 FleetParticipantScope(const FleetParticipantScope&)=delete;FleetParticipantScope& operator=(const FleetParticipantScope&)=delete;
};
}
