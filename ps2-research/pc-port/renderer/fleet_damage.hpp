#pragma once
#include "race_damage.hpp"
#include "race_fleet_registry.hpp"
#include "fleet_damage_registry.hpp"
#include <memory>
namespace gfx2::ps2port {
inline const fleet_damage_draft::Profile* fleet_damage_profile(const char* family)noexcept{for(const auto& p:fleet_damage_draft::profiles)if(!std::strcmp(p.ps2Family,family))return &p;return nullptr;}
class FleetDamageState {
 using Point=std::array<float,3>;const fleet_damage_draft::Profile* profile_=nullptr;
 std::array<std::shared_ptr<const std::vector<Point>>,32> reference_{};std::array<std::vector<Point>,32> current_{};
 std::array<uintptr_t,32> materials_{};std::array<uint32_t,32> tokens_{};std::array<std::string,32> hashes_{};
 uint32_t mask_=0;uint64_t race_=0,lifetime_=0,revision_=0;uintptr_t instance_=0,packet_=0,model_=0;std::string key_;
public:
 void invalidate_current()noexcept{mask_=0;for(auto& v:current_)v.clear();hashes_={};}
 void bind_context(const fleet_damage_draft::Profile* p,uint64_t race,uint64_t lifetime,uintptr_t instance,uintptr_t packet,uintptr_t model){if(profile_!=p||race_!=race||lifetime_!=lifetime||instance_!=instance||packet_!=packet||model_!=model){profile_=p;reference_={};materials_={};tokens_={};key_.clear();invalidate_current();++revision_;race_=race;lifetime_=lifetime;instance_=instance;packet_=packet;model_=model;}}
 bool material(unsigned i,uintptr_t m,uint32_t t)const noexcept{return i<32&&reference_[i]&&!reference_[i]->empty()&&materials_[i]==m&&tokens_[i]==t;}
 bool complete()const noexcept{return profile_&&profile_->sourceCount&&profile_->sourceCount<=30&&mask_==((1u<<profile_->sourceCount)-1);}
 bool healthy_complete()const noexcept{if(!profile_||!profile_->sourceCount||profile_->sourceCount>30)return false;for(unsigned i=0;i<profile_->sourceCount;++i)if(!reference_[i]||reference_[i]->empty())return false;return true;}
 bool eligible()const noexcept{return profile_&&profile_->eligible;}
 unsigned select(const FleetRaceProfile& p,const DrawSnapshot& g,const std::string& xyz,const std::string& uv,bool priv,uintptr_t m,uint32_t t)const noexcept{unsigned n=0,selected=p.pcDrawCount,original=p.pcDrawCount,originals=0;if(!profile_||profile_->sourceCount!=p.pcDrawCount)return selected;for(unsigned i=0;i<p.pcDrawCount;++i){const auto& s=p.source[i];if(s.vertices!=g.vertex_count||s.triangles!=g.primitive_count||uv!=s.uvWinding||(!priv&&xyz!=s.orderedPosition)||(priv&&!material(i,m,t)))continue;selected=i;++n;if(xyz==s.orderedPosition){original=i;++originals;}}return n==1?selected:n>1&&originals==1?original:p.pcDrawCount;}
 bool observe(unsigned i,const DrawSnapshot& g,const FleetRaceSource& s,bool priv,uintptr_t m,uint32_t t){if(i>=32||!profile_||i>=profile_->sourceCount||!m)return false;mask_&=~(1u<<i);std::vector<Point> points;std::string xyz,uv;if(!RaceDamageState::snapshot(g,points,xyz,uv)||g.vertex_count!=s.vertices||g.primitive_count!=s.triangles||uv!=s.uvWinding)return false;if(!priv){if(xyz!=s.orderedPosition)return false;if(!reference_[i]){reference_[i]=std::make_shared<const std::vector<Point>>(points);materials_[i]=m;tokens_[i]=t;}else if(!material(i,m,t))return false;}else if(!material(i,m,t))return false;if(reference_[i]->size()!=points.size())return false;current_[i]=std::move(points);hashes_[i]=std::move(xyz);mask_|=1u<<i;return true;}
 bool delta(unsigned vertex,Point& out)const noexcept{out={};if(!complete()||!eligible()||vertex>=profile_->mappingCount)return false;const auto& map=profile_->mapping[vertex];if(map.vertex!=vertex||map.first>profile_->candidateCount||map.count>profile_->candidateCount-map.first)return false;if(!map.count)return profile_->staticCount&&std::binary_search(profile_->staticVertices,profile_->staticVertices+profile_->staticCount,vertex);for(unsigned k=0;k<map.count;++k){const auto& c=profile_->candidates[map.first+k];if(c.slot>=profile_->sourceCount||!reference_[c.slot]||c.vertex>=current_[c.slot].size()||c.vertex>=reference_[c.slot]->size())return false;Point d{};for(unsigned j=0;j<3;++j){d[j]=current_[c.slot][c.vertex][j]-(*reference_[c.slot])[c.vertex][j];if(!std::isfinite(d[j])||(k&&std::fabs(d[j]-out[j])>1e-6f))return false;}if(!k)out=d;}return true;}
 bool validate(const std::vector<uint32_t>& referenced){if(!complete()||!eligible())return false;Point d;for(auto i:referenced)if(!delta(i,d))return false;std::string next;for(unsigned i=0;i<profile_->sourceCount;++i)next+=hashes_[i];if(next!=key_){key_=std::move(next);++revision_;}return true;}
 uint64_t revision()const noexcept{return revision_;}
 unsigned asset_vertex_count()const noexcept{return profile_?profile_->assetVertexCount:0;}
};
}
