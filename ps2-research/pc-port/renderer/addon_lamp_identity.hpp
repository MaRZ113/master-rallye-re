#pragma once
#include "fleet_lamp_identity.hpp"
#include "addon_lamp_registry.hpp"
namespace gfx2::ps2port {
// Cache only immutable draw identity. Owner/material/texture lifetime proof is
// deliberately outside this cache and is repeated at every draw/transaction.
inline unsigned cached_addon_lamp_identity(const std::vector<AddonLampRecord>& profiles,const DrawSnapshot& g){
 struct Key {
  const void* catalog=nullptr;uint64_t device=0,reset=0,vg=0,ig=0,vr=0,ir=0;uintptr_t vb=0,ib=0;
  unsigned min=0,base=0,start=0,vertices=0,triangles=0,fvf=0,stride=0,format=0;
  bool operator==(const Key& b)const noexcept{return catalog==b.catalog&&device==b.device&&reset==b.reset&&vg==b.vg&&ig==b.ig&&vr==b.vr&&ir==b.ir&&vb==b.vb&&ib==b.ib&&min==b.min&&base==b.base&&start==b.start&&vertices==b.vertices&&triangles==b.triangles&&fvf==b.fvf&&stride==b.stride&&format==b.format;}
 };
 struct Entry{Key key;unsigned profile=UINT_MAX;};
 static thread_local std::array<Entry,128> cache{};static thread_local unsigned cursor=0;
 const Key key{profiles.data(),g.device_id,g.reset_generation,g.vertex_generation,g.index_generation,g.vertex_revision,g.index_revision,g.vertex_resource,g.index_resource,g.min_index,g.base_vertex,g.start_index,g.vertex_count,g.primitive_count,g.fvf,g.stride,unsigned(g.index_format)};
 const unsigned width=g.index_format==D3DFMT_INDEX16?2:g.index_format==D3DFMT_INDEX32?4:0;
 if(!g.supported_build||!g.complete_mirror_coverage||!g.device_id||!g.vertex_resource||!g.index_resource||!g.vertex_generation||!g.index_generation||!g.vertex_revision||!g.index_revision||g.primitive_type!=D3DPT_TRIANGLELIST||!width||g.vertex_bytes.size()!=uint64_t(g.vertex_count)*g.stride||g.index_bytes.size()!=uint64_t(g.primitive_count)*3*width)return UINT_MAX;
 for(const auto& e:cache)if(e.key==key)return e.profile;
 unsigned found=UINT_MAX;
 for(unsigned i=0;i<profiles.size();++i){const auto& p=profiles[i];if(p.vertices!=g.vertex_count||p.triangles!=g.primitive_count)continue;if(exact_native_lamp(g,p.vertices,p.triangles,p.geometry.c_str(),p.positionUv.c_str())){if(found!=UINT_MAX)return UINT_MAX;found=i;}}
 cache[cursor++%cache.size()]={key,found};return found;
}
}
