#pragma once

// This route does not authorize a private PS2 body. It draws the real native
// damaged record once, with Mode4 only on a wholly reflective source material.
inline xtrailintegration::Result fleet_damage_reflection(Device8& d,ps2port::FrontendModel& parent,ps2port::FrontendModel& model,const ps2port::FleetRaceProfile& profile,const Context& owner,const D3DMATRIX& world,D3DPRIMITIVETYPE type,UINT min,UINT vertices,UINT start,UINT count,uintptr_t pc) {
 if(!owner.owner.private_tree||model.fleet_damage.eligible()||!model.fleet_damage.healthy_complete())return {};
 auto* e=d.ps2_port();auto* reflection=e?e->reflection():nullptr;if(!reflection||!reflection->active()||reflection->mode_value()!=4||!reflection->expanded())return {};
 ps2port::RaceDescriptors desc;desc.vd=owner.vd;std::copy(owner.id.begin(),owner.id.end(),desc.id.begin());D3DINDEXBUFFER_DESC format{};ps2integration::Ref<IDirect3DIndexBuffer8> ib;UINT base=0;if(FAILED(d.native()->GetIndices(&ib.value,&base))||!ib.value||base||FAILED(ib.value->GetDesc(&format)))return {};desc.id[4]=format.Format;
 ps2port::DrawSnapshot g;if(!fleet_source_snapshot(d,desc,g)||g.fvf!=0x152||g.stride!=36)return {};
 ps2port::FrontendRecord record;record.mesh=owner.mesh;record.geometry=g;record.valid=true;uintptr_t material=0;uint32_t token=0;if(!fleet_material_identity(record,material,token))return {};
 std::vector<std::array<float,3>> points;std::string xyz,uv;if(!ps2port::RaceDamageState::snapshot(g,points,xyz,uv))return {};const auto slot=model.fleet_damage.select(profile,g,xyz,uv,true,material,token);if(slot>=profile.pcDrawCount)return {};
 const auto& source=profile.source[slot];for(const auto& mixed:ps2port::kVehiclePartitionMaterials)if(!std::strcmp(mixed.vehicle,profile.family)&&std::string_view(mixed.geometry_sha)==source.geometry)return {};for(const auto& mixed:ps2port::kLampPartitionMaterials)if(!std::strcmp(mixed.vehicle,profile.family)&&std::string_view(mixed.geometry_sha)==source.geometry)return {};bool reflective=false;for(const auto& m:ps2port::kReflectionMaterials)if(!std::strcmp(m.vehicle,profile.family)&&m.geometry_sha==std::string_view(source.geometry)&&m.vertices==vertices&&m.triangles==count)reflective=true;if(!reflective)return {};
 ps2port::DrawSnapshot current;ps2port::ReflectionSnapshot snapshot;DrawClassification classification{};if(!ps2integration::snapshot(d,classification,type,min,vertices,start,count,current,snapshot)||current.vertex_resource!=g.vertex_resource||current.index_resource!=g.index_resource||current.vertex_generation!=g.vertex_generation||current.index_generation!=g.index_generation||current.vertex_revision!=g.vertex_revision||current.index_revision!=g.index_revision)return {};
 // Source identity is proved by the current queue owner, retained healthy
 // material token and exact ordered UV/index certificate, not draw ordinals.
 snapshot.vehicle_body_verified=true;const auto identity=ps2port::reflection_identity_for_hash(snapshot,source.geometry,e->reset_generation(),true);if(!identity.accepted)return {};
 Context final;bool single=false;const auto race=courseintegration::certificate(single);if(!single||!race.valid||race.race_generation!=model.race_generation||race.owner_lifetime!=model.race_owner_lifetime||!fleet_owner(caller_stack,pc,final)||!(final.owner==owner.owner)||final.mesh!=owner.mesh||!fleet_owner_world(final,world)||!fleet_descriptor_tokens(d,record))return {};
 uintptr_t final_material=0;uint32_t final_token=0;if(!fleet_material_identity(record,final_material,final_token)||material!=final_material||token!=final_token)return {};
 ps2integration::Scope scope(d,snapshot,identity,pc);const auto ready=scope.pre_draw_status();if(FAILED(ready))return {true,ready};if(!scope.applied())return {};const auto drawn=d.native()->DrawIndexedPrimitive(type,min,vertices,start,count);notify(d,71,pack(type,min,vertices,start,count),drawn);scope.draw_result(drawn);const auto restored=ps2integration::repair(d);
 try{if(parent.fleet_probe.active(d.trace.control.active,d.trace.frame_number()))parent.fleet_probe.record(d.trace.device_id(),{owner.mesh,0xf20b,min,start},"{\"type\":\"fleet_native_damage_reflection\",\"frame\":"+std::to_string(d.trace.frame_number())+",\"family\":"+quote(profile.family)+",\"source_index\":"+std::to_string(slot)+",\"source_geometry_sha256\":"+quote(source.geometry)+",\"current_geometry_sha256\":"+quote(source_hash(g))+",\"native_damaged_geometry_preserved\":true,\"ps2_body_replacement\":false,\"draw_hresult\":"+std::to_string(uint32_t(drawn))+",\"restore_hresult\":"+std::to_string(uint32_t(restored))+"}");}catch(...){}return {true,FAILED(restored)?restored:drawn};
}



