#pragma once
#include "ps2_port_extension.hpp"
#include "provenance.hpp"
#include "race_damage_registry.hpp"
#include <algorithm>
#include <cmath>
#include <cstring>
namespace gfx2::ps2port {
class RaceDamageState {
 using Point=std::array<float,3>;
 std::array<std::vector<Point>,13> reference_,current_;
 std::array<bool,13> valid_{};
 uint64_t revision_=0;unsigned reports_=0;std::string last_report_;
public:
 static bool snapshot(const DrawSnapshot& g,std::vector<Point>& positions,std::string& position_sha,std::string& winding_sha){
  // 0x42 (XYZ|DIFFUSE) carries no texture coordinate; the authored source UV of such records is (0,0), so the certificate uses zero.
  const bool textured=g.fvf!=0x42;const unsigned uv=g.fvf==0x142?16:g.fvf==0x152?28:g.fvf==0x112?24:0,stride=g.fvf==0x142?24:g.fvf==0x152?36:g.fvf==0x112?32:g.fvf==0x42?16:0;
  const unsigned width=g.index_format==D3DFMT_INDEX16?2:g.index_format==D3DFMT_INDEX32?4:0;
  if(!g.supported_build||!g.device_id||!g.complete_mirror_coverage||!g.vertex_resource||!g.index_resource||!g.vertex_generation||!g.index_generation||!g.vertex_revision||!g.index_revision||g.primitive_type!=D3DPT_TRIANGLELIST||!stride||g.stride!=stride||!width||!g.vertex_count||g.vertex_count>8192||!g.primitive_count||g.primitive_count>8192||g.vertex_bytes.size()!=uint64_t(g.vertex_count)*stride||g.index_bytes.size()!=uint64_t(g.primitive_count)*3*width||g.vertex_byte_offset!=(uint64_t(g.base_vertex)+g.min_index)*stride)return false;
  std::string xyz,certificate;xyz.reserve(g.vertex_count*12);certificate.reserve(g.vertex_count*8+g.primitive_count*12);positions.resize(g.vertex_count);
  for(unsigned i=0;i<g.vertex_count;++i){const auto* v=g.vertex_bytes.data()+i*stride;std::memcpy(positions[i].data(),v,12);for(float f:positions[i])if(!std::isfinite(f))return false;float coords[2]={0.f,0.f};if(textured)std::memcpy(coords,v+uv,8);for(float f:coords)if(!std::isfinite(f))return false;xyz.append(reinterpret_cast<const char*>(v),12);certificate.append(reinterpret_cast<const char*>(coords),8);}
  for(unsigned i=0;i<g.primitive_count*3;++i){uint32_t index=0;std::memcpy(&index,g.index_bytes.data()+i*width,width);if(index<g.min_index||index-g.min_index>=g.vertex_count)return false;index-=g.min_index;certificate.append(reinterpret_cast<const char*>(&index),4);}
  position_sha=sha256_bytes(xyz.data(),xyz.size());winding_sha=sha256_bytes(certificate.data(),certificate.size());return true;
 }
 bool observe(unsigned slot,const DrawSnapshot& g,bool original_geometry,bool private_tree)noexcept{try{
  if(slot>=13)return false;valid_[slot]=false;const auto& profile=damage_source_draft::profiles[slot];if(g.vertex_count!=profile.vertices||g.primitive_count!=profile.triangles)return false;
  std::vector<Point> points;std::string positions,winding;if(!snapshot(g,points,positions,winding)||winding!=profile.uv_winding_sha)return false;
  if(original_geometry&&positions==profile.ordered_position_sha){if(reference_[slot].empty())reference_[slot]=points;}
  else if(!private_tree)return false;
  if(reference_[slot].size()!=points.size())return false;current_[slot]=std::move(points);valid_[slot]=true;++revision_;return true;
 }catch(...){return false;}}
 void invalidate_current()noexcept{valid_={};for(auto& p:current_)p.clear();++revision_;}
 uint64_t revision()const noexcept{return revision_;}
 bool complete()const noexcept{for(unsigned i=0;i<13;++i)if(!valid_[i]||current_[i].size()!=reference_[i].size()||reference_[i].empty())return false;return true;}
 bool delta(unsigned slot,uint32_t ps2_vertex,Point& result)const noexcept{
  result={};if(slot>=13||!valid_[slot])return false;const auto& p=damage_source_draft::profiles[slot];const auto* m=std::lower_bound(p.mapping,p.mapping+p.mappings,ps2_vertex,[](const auto& a,uint32_t v){return a.vertex<v;});
  if(m==p.mapping+p.mappings||m->vertex!=ps2_vertex||m->first>p.candidates||m->count>p.candidates-m->first)return false;
  // Explicit original interior differences have zero candidates, hence no guessed motion.
  if(!m->count)return true;
  for(unsigned k=0;k<m->count;++k){const auto index=p.candidate[m->first+k];if(index>=reference_[slot].size()||index>=current_[slot].size())return false;Point d{};for(unsigned axis=0;axis<3;++axis){d[axis]=current_[slot][index][axis]-reference_[slot][index][axis];if(!std::isfinite(d[axis]))return false;if(k&&std::fabs(d[axis]-result[axis])>1e-6f)return false;}if(!k)result=d;}
  return true;
 }
 bool claim_report()noexcept{try{if(!complete()||reports_>=4)return false;std::string all;for(const auto& p:current_)all.append(reinterpret_cast<const char*>(p.data()),p.size()*sizeof(Point));const auto hash=sha256_bytes(all.data(),all.size());if(hash==last_report_)return false;last_report_=hash;++reports_;return true;}catch(...){return false;}}
 const std::string& state_sha()const noexcept{return last_report_;}
};
}
