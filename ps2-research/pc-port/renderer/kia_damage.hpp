#pragma once
#include "race_damage.hpp"
#include "race_fleet_registry.hpp"
#include "kia_damage_registry.hpp"
#include <memory>
namespace gfx2::ps2port {
class KiaDamageState {
 using Point=std::array<float,3>;
 std::array<std::shared_ptr<const std::vector<Point>>,26> reference_{};
 std::array<std::vector<Point>,26> current_{};
 std::array<uintptr_t,26> materials_{};std::array<uint32_t,26> tokens_{};
 std::array<bool,26> valid_{};std::array<std::string,26> hashes_{};
 uint32_t valid_mask_=0;uint64_t race_=0,lifetime_=0;uintptr_t instance_=0,packet_=0,model_=0;std::string key_;uint64_t revision_=0;
public:
 void invalidate_current()noexcept{valid_mask_=0;valid_={};for(auto& p:current_)p.clear();hashes_={};}
 void clear()noexcept{reference_={};materials_={};tokens_={};key_.clear();invalidate_current();++revision_;}
 void bind_context(uint64_t race,uint64_t lifetime,uintptr_t instance,uintptr_t packet,uintptr_t model)noexcept{if(race_!=race||lifetime_!=lifetime||instance_!=instance||packet_!=packet||model_!=model){clear();race_=race;lifetime_=lifetime;instance_=instance;packet_=packet;model_=model;}}
 bool has_reference(unsigned slot)const noexcept{return slot<26&&reference_[slot]&&!reference_[slot]->empty();}
 bool material(unsigned slot,uintptr_t pointer,uint32_t token)const noexcept{return has_reference(slot)&&materials_[slot]==pointer&&tokens_[slot]==token;}
 unsigned select(const FleetRaceProfile& profile,unsigned vertices,unsigned triangles,const std::string& position,const std::string& uv,bool private_tree,uintptr_t pointer,uint32_t token)const noexcept{if(profile.pcDrawCount!=26||std::strcmp(profile.ps2Family,"KIASPORTAGE"))return 26;unsigned total=0,selected=26,exact=26,exact_count=0;for(unsigned i=0;i<26;++i){const auto& source=profile.source[i];if(source.vertices!=vertices||source.triangles!=triangles||uv!=source.uvWinding||(!private_tree&&position!=source.orderedPosition)||(private_tree&&!material(i,pointer,token)))continue;selected=i;++total;if(position==source.orderedPosition){exact=i;++exact_count;}}return total==1?selected:total>1&&exact_count==1?exact:26;}
 bool observe(unsigned slot,const DrawSnapshot& g,const FleetRaceSource& profile,bool private_tree,uintptr_t pointer,uint32_t token){
  if(slot>=26||!pointer)return false;std::vector<Point> points;std::string xyz,uv;if(!RaceDamageState::snapshot(g,points,xyz,uv)||g.vertex_count!=profile.vertices||g.primitive_count!=profile.triangles||uv!=profile.uvWinding)return false;
  if(!private_tree){if(xyz!=profile.orderedPosition)return false;if(!has_reference(slot)){reference_[slot]=std::make_shared<const std::vector<Point>>(points);materials_[slot]=pointer;tokens_[slot]=token;}else if(!material(slot,pointer,token))return false;}
  else if(!material(slot,pointer,token))return false;
  if(!reference_[slot]||reference_[slot]->size()!=points.size())return false;current_[slot]=std::move(points);hashes_[slot]=std::move(xyz);valid_[slot]=true;valid_mask_|=1u<<slot;return true;
 }
 bool complete()const noexcept{return valid_mask_==((1u<<26)-1);}
 bool delta(uint32_t vertex,Point& out)const noexcept{
  out={};if(!complete()||vertex>=std::size(kia_damage_draft::mapping))return false;const auto& m=kia_damage_draft::mapping[vertex];if(m.vertex!=vertex||m.first>std::size(kia_damage_draft::candidates)||m.count>std::size(kia_damage_draft::candidates)-m.first)return false;
  if(!m.count)return std::binary_search(std::begin(kia_damage_draft::static_source_vertices),std::end(kia_damage_draft::static_source_vertices),vertex);
  for(unsigned i=0;i<m.count;++i){const auto& c=kia_damage_draft::candidates[m.first+i];if(c.slot>=26||c.vertex>=current_[c.slot].size()||c.vertex>=reference_[c.slot]->size())return false;Point d{};for(unsigned axis=0;axis<3;++axis){d[axis]=current_[c.slot][c.vertex][axis]-(*reference_[c.slot])[c.vertex][axis];if(!std::isfinite(d[axis])||(i&&std::fabs(d[axis]-out[axis])>1e-6f))return false;}if(!i)out=d;}return true;
 }
 bool validate(){if(!complete())return false;Point d;for(unsigned i=0;i<std::size(kia_damage_draft::mapping);++i)if(!delta(i,d))return false;std::string next;for(const auto& h:hashes_)next+=h;if(next!=key_){key_=std::move(next);++revision_;}return true;}
 uint64_t revision()const noexcept{return revision_;}
};
}
