#pragma once
#include "damage_identity.hpp"
#include "provenance.hpp"
namespace gfx2::ps2port {
// Current native queue owner + healthy exact source, never a historical pointer alone.
struct KiaLampContext {
 uint64_t device=0,race=0,lifetime=0,texture_generation=0;
 uintptr_t instance=0,packet=0,model=0,material_vector=0;uint32_t material_token=0;uintptr_t texture=0;
 bool owner_verified=false,private_tree=false;
 bool same_owner(const KiaLampContext& b)const noexcept{return device==b.device&&race==b.race&&lifetime==b.lifetime&&instance==b.instance&&packet==b.packet&&model==b.model;}
};
class NativeLampContinuity {
 struct Reference {KiaLampContext context;std::string uv_indices;bool valid=false;};
 std::array<Reference,3> references_{};
public:
 static bool exact_on(const DrawSnapshot& g){if(g.fvf!=0x102||g.stride!=20||g.vertex_count!=16||g.primitive_count!=12||topology(g).empty())return false;auto copy=g;copy.fvf=0x112;copy.stride=32;copy.vertex_byte_offset=(uint64_t(g.base_vertex)+g.min_index)*32;copy.vertex_bytes.assign(g.vertex_count*32,0);for(unsigned i=0;i<g.vertex_count;++i){std::memcpy(copy.vertex_bytes.data()+i*32,g.vertex_bytes.data()+i*20,12);std::memcpy(copy.vertex_bytes.data()+i*32+24,g.vertex_bytes.data()+i*20+12,8);}return position_uv_corner_sha(copy)=="3bfdba6278a48d057ca7508e9db3b4dc2ed3155b8075d173ee4f61376d1e0687";}
 static std::string topology(const DrawSnapshot& g){
  if(!g.supported_build||!g.device_id||!g.vertex_resource||!g.index_resource||((g.fvf!=0x102||g.stride!=20)&&(g.fvf!=0x112||g.stride!=32)&&(g.fvf!=0x152||g.stride!=36))||!g.complete_mirror_coverage||!g.vertex_generation||!g.index_generation||!g.vertex_revision||!g.index_revision||g.primitive_type!=D3DPT_TRIANGLELIST||g.vertex_byte_offset!=(uint64_t(g.base_vertex)+g.min_index)*g.stride||g.vertex_bytes.size()!=uint64_t(g.vertex_count)*g.stride)return {};
  const unsigned width=g.index_format==D3DFMT_INDEX16?2:g.index_format==D3DFMT_INDEX32?4:0;if(!width||g.index_bytes.size()!=uint64_t(g.primitive_count)*3*width)return {};
  std::vector<BYTE> bytes;for(unsigned i=0;i<g.vertex_count;++i){float xyz[3],coords[2];std::memcpy(xyz,g.vertex_bytes.data()+i*g.stride,12);std::memcpy(coords,g.vertex_bytes.data()+i*g.stride+g.stride-8,8);for(float x:xyz)if(!std::isfinite(x))return {};for(float x:coords)if(!std::isfinite(x))return {};const auto* uv=g.vertex_bytes.data()+i*g.stride+g.stride-8;bytes.insert(bytes.end(),uv,uv+8);}
  for(unsigned i=0;i<g.primitive_count*3;++i){uint32_t index=0;std::memcpy(&index,g.index_bytes.data()+i*width,width);if(index<g.min_index||index-g.min_index>=g.vertex_count)return {};index-=g.min_index;const auto* raw=reinterpret_cast<const BYTE*>(&index);bytes.insert(bytes.end(),raw,raw+4);}return sha256_bytes(bytes.data(),bytes.size());
 }
 bool match(unsigned kind,const DrawSnapshot& g,const KiaLampContext& c,bool exact_healthy,const char*& reason){return match_source(kind,g,c,exact_healthy,reason,kind?32u:16u,kind?32u:12u);}
 bool match_source(unsigned kind,const DrawSnapshot& g,const KiaLampContext& c,bool exact_healthy,const char*& reason,unsigned vertices,unsigned triangles){
  reason="wrong_family_lamp_layout";if(kind>2||g.vertex_count!=vertices||g.primitive_count!=triangles)return false;
  if(!c.owner_verified||!c.device||!c.race||!c.lifetime||!c.instance||!c.packet||!c.model){reason="current_kia_chassis_owner_not_verified";return false;}
  if(!c.material_vector||!c.material_token||!c.texture||!c.texture_generation){reason="material_or_texture_identity_unavailable";return false;}
  auto topology_sha=topology(g);if(topology_sha.empty()){reason="invalid_current_glow_buffers";return false;}
  auto& ref=references_[kind];if(ref.valid&&!ref.context.same_owner(c))ref={};
  if(exact_healthy){if(ref.valid&&(ref.context.material_vector!=c.material_vector||ref.context.material_token!=c.material_token||ref.context.texture!=c.texture||ref.context.texture_generation!=c.texture_generation||ref.uv_indices!=topology_sha)){reason="healthy_resource_identity_changed";return false;}ref={c,std::move(topology_sha),true};reason="healthy_exact_source";return true;}
  if(!c.private_tree){reason="healthy_geometry_signature_mismatch";return false;}if(!ref.valid){reason="damaged_branch_without_healthy_reference";return false;}
  if(ref.context.material_vector!=c.material_vector||ref.context.material_token!=c.material_token){reason="damaged_material_identity_changed";return false;}
  if(ref.context.texture!=c.texture||ref.context.texture_generation!=c.texture_generation){reason="damaged_texture_identity_changed";return false;}
  if(ref.uv_indices!=topology_sha){reason="damaged_uv_or_index_topology_changed";return false;}
  reason="damaged_owned_clone_uv_index_match";return true;
 }
};
using KiaLampContinuity=NativeLampContinuity;
}
