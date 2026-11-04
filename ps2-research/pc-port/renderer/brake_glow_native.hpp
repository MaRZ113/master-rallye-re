#pragma once
#include "ps2_race_certificate.hpp"
#include "frontend_model_native.hpp"
#include "lamp_integration.hpp"
#include "xtrail_native_integration.hpp"
namespace gfx2::lampintegration {
inline bool owned_lamp_context(Device8& d,const RaceCertificate& race,const ps2port::DrawSnapshot& g,const D3DMATRIX& world,uintptr_t texture,ps2port::LampOwnerContext& c,unsigned& family)noexcept{
 using namespace frontendmodelintegration;auto* e=d.ps2_port();auto* parent=e?e->race_model():nullptr;auto* body=parent?parent->car_child():nullptr;family=UINT_MAX;
 if(!parent||!parent->car_fleet_enabled())return false;
 if(body&&body->observed_frame!=d.trace.frame_number())body=nullptr;
 if(body&&parent->car_index()<std::size(ps2port::kRaceFleetProfiles))family=parent->car_index();else if(parent->certified&&parent->drawn_frame==d.trace.frame_number()){body=parent;for(unsigned i=0;i<std::size(ps2port::kRaceFleetProfiles);++i)if(!std::strcmp(ps2port::kRaceFleetProfiles[i].ps2Family,"XTRAIL"))family=i;}
 if(!body||family==UINT_MAX||race.race_generation!=body->race_generation||race.owner_lifetime!=body->race_owner_lifetime)return false;
 const bool rendered=body->certified&&body->drawn_frame==d.trace.frame_number();const bool native_damage_fallback=body->owner.private_tree&&body->observed_frame==d.trace.frame_number()&&body->fleet_damage.healthy_complete();if(!rendered&&!native_damage_fallback)return false;
 const auto exe=reinterpret_cast<uintptr_t>(GetModuleHandleW(nullptr));uintptr_t mesh=0,instance=0,packet=0,model=0,back=0,list=0;bool priv=false;
 if(!pointer_word(caller_stack+0x34,mesh)||!ps2port::frontend_queue_owner(caller_stack,exe,mesh,frontendmodelintegration::word,instance)||!pointer_word(instance+0xb0,packet)||!pointer_word(instance+0x8c,model)||!pointer_word(packet+0x74,back)||back!=instance||instance!=body->owner.instance||packet!=body->owner.packet||model!=body->owner.model||!ps2port::race_selected_list(instance,model,frontendmodelintegration::word,list,priv)||list!=body->owner.native_list||priv!=body->owner.private_tree||std::memcmp(&world,&body->drawn_world,64))return false;
 ps2port::RaceDescriptors desc;uintptr_t v=0,i=0;if(!ps2port::race_descriptors(exe,mesh,frontendmodelintegration::word,desc)||!pointer_word(desc.vd[0],v)||!pointer_word(desc.id[0],i)||reinterpret_cast<uintptr_t>(d.unwrap_vertex_buffer(reinterpret_cast<IDirect3DVertexBuffer8*>(v)))!=g.vertex_resource||reinterpret_cast<uintptr_t>(d.unwrap_index_buffer(reinterpret_cast<IDirect3DIndexBuffer8*>(i)))!=g.index_resource||g.base_vertex||desc.vd[2]!=g.min_index||desc.vd[3]!=g.vertex_count||desc.vd[4]!=g.fvf||desc.vd[5]!=g.stride||desc.id[2]!=g.start_index||desc.id[3]!=g.primitive_count*3||desc.id[4]!=g.index_format)return false;
 uintptr_t materials=0,begin=0;uint32_t token=0,end=0;if(!pointer_word(mesh+0x38,materials)||!pointer_word(materials+4,begin)||!frontendmodelintegration::word(materials+8,end)||end!=begin+4||!frontendmodelintegration::word(begin,token))return false;
 c={d.trace.device_id(),race.race_generation,race.owner_lifetime,d.trace.resources.generation(texture),instance,packet,model,materials,token,texture,true,priv};return true;
}
inline dipintegration::Result draw_fleet_lamp(Device8&,D3DPRIMITIVETYPE,UINT,UINT,UINT,UINT,uintptr_t)noexcept;
inline dipintegration::Result draw(Device8& d,D3DPRIMITIVETYPE type,UINT min_index,UINT vertices,UINT start,UINT count,uintptr_t pc)noexcept{
 // First PS2 entry of every indexed draw: frame boundary of the PERF2 timing window.
 ps2port::perf::frame(d.trace.device_id(),d.trace.frame_number(),[](const std::string& r){session().write(r);});
 ps2port::note_render_frame(d.trace.device_id(),d.trace.frame_number());
 ps2port::perf::Timer perf_timer(ps2port::perf::LampEntry);
 frontendmodelintegration::FleetParticipantScope fleet_scope(d,pc);
 const auto fleet=draw_fleet_lamp(d,type,min_index,vertices,start,count,pc);if(fleet.handled)return fleet;
 // Every PS2 lamp layer (ON core, additive glow, OFF) of every fleet car, Kia and X-Trail included, goes through the
 // owner-verified fleet path; the pre-fleet Kia route (single-car races only) is retired (VEHICLE-UNIFY1).
 return fleet;
}
}

#include "fleet_lamp_native.hpp"
