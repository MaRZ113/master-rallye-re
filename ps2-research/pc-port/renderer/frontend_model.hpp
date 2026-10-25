#pragma once
#include "ps2_diag.hpp"
#include <cmath>
#include "ps2_port_extension.hpp"
#include "ps2_content_fixes.hpp"
#include "provenance.hpp"
#include "frontend_transaction.hpp"
#include "model_probe.hpp"
#include "fleet_car_probe.hpp"
#include "fleet_damage_probe.hpp"
#include "kia_wheel_warmup.hpp"
#include "kia_damage.hpp"
#include "fleet_damage.hpp"
#include "race_damage.hpp"
#include "headlight_damage_registry.hpp"
#include "front_lamp_5_damage_registry.hpp"
#include "front_lamp_11_damage_registry.hpp"
#include "frontend_source_registry.hpp"
#include "frontend_fleet_registry.hpp"
#include <array>
#include <vector>
#include <limits>
namespace gfx2::ps2port {
constexpr bool frontend_fixed_pixel_shader(DWORD native,bool known,DWORD shadow)noexcept{return native==0&&(!known||shadow==native);}
// Read the current queue record through preserved caller registers, never the
// emitter argument slot reused as render-state scratch by the original engine.
template<class Read> bool frontend_queue_owner(uintptr_t stack,uintptr_t base,uintptr_t mesh,Read read,uintptr_t& instance)noexcept{
 uint32_t caller=0,manager=0,index=0,begin=0,end=0,record=0,owner=0,current_mesh=0;
 if(!read(stack+0x48,caller))return false;
 const auto index_slot=caller==base+0x1628c1?0x24u:caller==base+0x1629ee?0x20u:0u;
 if(!index_slot||!read(stack+0x28,manager)||manager<0x10000||(manager&3)||!read(stack+index_slot,index)||!read(manager+0x44,begin)||!read(manager+0x48,end)||begin<0x10000||(begin&3)||(end&3)||end<begin||(end-begin)/4>4096||index>=(end-begin)/4||!read(begin+index*4,record)||record<0x10000||(record&3)||!read(record,owner)||owner<0x10000||(owner&3)||!read(record+4,current_mesh)||current_mesh!=mesh)return false;
 instance=owner;return true;
}
// Original native model renderer 0054C9D0 selects instance-private list first.
template<class Read> bool race_selected_list(uintptr_t instance,uintptr_t model,Read read,uintptr_t& list,bool& private_tree)noexcept{uint32_t p=0;if(!read(instance+0x90,p))return false;private_tree=p!=0;if(!p&&!read(model+0x18,p))return false;if(p<0x10000||p>0x7ffffffc||(p&3))return false;list=p;return true;}
struct FrontendVertex {float xyz[3],normal[3];DWORD color;float uv[2];};
static_assert(sizeof(FrontendVertex)==36);
// X-Trail COMPLETE runtime primary sampling orientation, established by user A/B.
inline FrontendVertex frontend_primary_sample_vertex(FrontendVertex v)noexcept{v.uv[1]=1.0f-v.uv[1];return v;}
// PS2 prepared vehicle lighting (refl1/body-reflection.md, EE 322220): carshiny/carflat source colours are
// replaced by a model-space normal-Y grayscale, gray=clamp(round((.225*ny+.4)*255),2,254), stored at half
// and modulated by GS as tex*vcol/128, i.e. a D3D diffuse of gray/255 (alpha 254).
inline DWORD ps2_prepared_vertex_color(float ny)noexcept{if(!std::isfinite(ny))ny=0.f;long g=std::lrintf((ny*.225f+.4f)*255.f);if(g<2)g=2;if(g>254)g=254;const DWORD c=DWORD(g);return 0xFE000000u|(c<<16)|(c<<8)|c;}
inline bool ps2_prepared_lighting_mode(uint32_t mode)noexcept{return mode==1||mode==3;}
inline DrawSnapshot frontend_position_snapshot(const DrawSnapshot& g){auto copy=g;if((g.fvf==0x112&&g.stride==32)||(g.fvf==0x42&&g.stride==16)){if(g.vertex_bytes.size()!=uint64_t(g.vertex_count)*g.stride)return {};copy.fvf=0x152;copy.stride=36;copy.base_vertex=0;copy.vertex_byte_offset=uint64_t(g.min_index)*36;copy.vertex_bytes.assign(uint64_t(g.vertex_count)*36,0);for(unsigned i=0;i<g.vertex_count;++i)std::memcpy(copy.vertex_bytes.data()+i*36,g.vertex_bytes.data()+i*g.stride,12);}return copy;}
struct FrontendMesh {uint32_t node,mode,texture[3],first,count;};
struct FrontendTexture {UINT width,height;std::vector<DWORD> pixels;};
struct FrontendAsset {std::vector<FrontendVertex> vertices;std::vector<uint32_t> indices;std::vector<FrontendMesh> meshes;std::vector<FrontendTexture> textures;};
bool decode_frontend_asset(const std::vector<uint8_t>&,FrontendAsset&,unsigned role=0,const FleetProfile* profile=nullptr,const char* pinned_sha=nullptr,std::size_t pinned_size=0)noexcept;
// Certificate contains current source identity, never historical draw ordinals.
struct FrontendOwner {uintptr_t packet=0,instance=0,model=0,root=0,native_list=0;bool private_tree=false;uint32_t name=0;std::array<uintptr_t,64> meshes{};bool operator==(const FrontendOwner& x)const noexcept{return packet==x.packet&&instance==x.instance&&model==x.model&&root==x.root&&native_list==x.native_list&&private_tree==x.private_tree&&name==x.name&&meshes==x.meshes;}};
struct FrontendRecord {uintptr_t mesh=0;DrawSnapshot geometry;bool valid=false;};
struct WheelOwnerState {FrontendOwner owner{};std::array<FrontendRecord,4> records{};uint64_t frame=UINT64_MAX,drawn_frame=UINT64_MAX,blocked_frame=UINT64_MAX;uint32_t seen=0;bool certified=false;D3DMATRIX world{};};
struct FleetWheelOwnerState {FrontendOwner owner{};std::array<FrontendRecord,16> records{};uint64_t frame=UINT64_MAX,drawn_frame=UINT64_MAX,blocked_frame=UINT64_MAX;uint32_t seen=0;bool certified=false;D3DMATRIX world{},view{},projection{};D3DVIEWPORT8 viewport{};uintptr_t target=0;};
class FrontendModel {
 const FleetProfile* profile_=nullptr;const PS2ContentFix* content_fix_=nullptr;bool ps2_lighting_=false;std::wstring ini_;bool fleet_=false;bool car_fleet_=false;uint32_t car_failed_=0;unsigned car_index_=UINT_MAX;std::unique_ptr<FrontendModel> car_child_,car_wheel_;bool car_wheels_=false;const FleetProfile* car_wheel_failed_=nullptr;
 std::unique_ptr<FrontendModel> off_child_;const FleetProfile* off_failed_=nullptr;
 bool requested_=false,diagnostics_=false,disabled_=false,parts_=false,crew_=false;uint32_t logs_=0;
 float source_radius_sq_=0;FrontendAsset asset_;std::vector<IDirect3DTexture8*> textures_;std::vector<std::vector<FrontendVertex>> expanded_;
 std::vector<std::vector<FrontendVertex>> kia_deformed_;uint64_t kia_revision_=UINT64_MAX;
 std::array<std::vector<FrontendVertex>,5> trim_;
 std::array<std::vector<FrontendVertex>,2> race_body_;
 std::array<std::vector<std::array<float,3>>,3> headlight_reference_;std::array<std::vector<FrontendVertex>,3> headlight_current_;
 std::array<std::vector<FrontendVertex>,13> deformed_;uint64_t deformation_revision_=UINT64_MAX;bool deformation_ready_=false;
 std::array<std::vector<FrontendVertex>,4> crew_vertices_;
public:
 FleetDamageState fleet_damage;KiaDamageState kia_damage;KiaWheelWarmup kia_warmup;FleetDamageProbe fleet_damage_probe;ModelProbe damage_probe;FleetCarProbe fleet_probe;RaceDamageState damage;
 std::array<FrontendRecord,64> fleet_probes{};unsigned fleet_probe_count=0;uint32_t fleet_failed=0;
 std::vector<std::pair<unsigned,unsigned>> trim17_native_runs;std::array<WheelOwnerState,4> wheel_owners{};std::array<FleetWheelOwnerState,16> fleet_wheel_owners{};FrontendTransaction transaction;D3DMATRIX environment{};bool environment_known=false,validated=false;
 uint32_t car_source_logs=0;D3DMATRIX car_view{},car_projection{};D3DVIEWPORT8 car_viewport{};uintptr_t car_target=0;uint64_t car_fault_frame=UINT64_MAX,car_blocked_frame=UINT64_MAX;uint32_t parts_validated=0;uint64_t race_generation=0,race_owner_lifetime=0;FrontendOwner owner{};std::array<FrontendRecord,32> records{};uint32_t seen=0;uint64_t observed_frame=UINT64_MAX,drawn_frame=UINT64_MAX;D3DMATRIX drawn_world{};bool certified=false;
 FrontendModel(bool,const std::wstring&,unsigned role=0,const FleetProfile* profile=nullptr)noexcept;~FrontendModel(){transaction.release();reset();}
 bool fleet_enabled()const noexcept{return fleet_&&!disabled_;}
 const FleetProfile* profile()const noexcept{return profile_;}const PS2ContentFix* content_fix()const noexcept{return content_fix_;}bool ps2_lighting()const noexcept{return ps2_lighting_;}void apply_ps2_lighting(const std::wstring& ini)noexcept;
 bool select_fleet(const FleetProfile&)noexcept;
 bool select_off(const FleetProfile&)noexcept;FrontendModel* off_child()noexcept{return off_child_.get();}
 bool car_fleet_enabled()const noexcept{return car_fleet_&&requested();}
 FrontendModel* car_child()noexcept{return car_child_.get();}const FrontendModel* car_child()const noexcept{return car_child_.get();}
 unsigned car_index()const noexcept{return car_index_;}bool select_car(unsigned)noexcept;
 bool select_car_wheel(const FleetProfile&)noexcept;FrontendModel* car_wheel()noexcept{return car_wheel_.get();}bool car_wheels_enabled()const noexcept{return car_fleet_enabled()&&car_wheels_;}
 bool states_pending()const noexcept{return transaction.pending()||(car_child_&&car_child_->states_pending())||(car_wheel_&&car_wheel_->states_pending());}
 bool requested()const noexcept{return requested_&&!disabled_;}bool diagnostics()const noexcept{return diagnostics_;}
 bool parts_enabled()const noexcept{return requested()&&parts_;}
 bool crew_enabled()const noexcept{return parts_enabled()&&crew_;}
 const auto& crew_vertices(unsigned i)const noexcept{return crew_vertices_[i];}
 bool claim(uint32_t bit)noexcept{if(!diagnostics_||(logs_&bit))return false;logs_|=bit;return true;}
 float source_radius_sq()const noexcept{return source_radius_sq_;}
 const FrontendAsset& asset()const noexcept{return asset_;}const auto& expanded()const noexcept{return expanded_;}
 const auto& trim(unsigned i)const noexcept{return trim_[i];}
 const auto& race_base_vertices(unsigned root)const noexcept{return root==0?race_body_[0]:root==7?race_body_[1]:expanded_[root];}
 const std::vector<FrontendVertex>& race_vertices(unsigned root)const noexcept{if(deformation_ready_)for(unsigned i=0;i<13;++i)if(damage_source_draft::profiles[i].root==root)return deformed_[i];return race_base_vertices(root);}
 bool prepare_damage()noexcept;bool prepare_fleet_damage()noexcept;bool prepare_kia_damage()noexcept;const auto& fleet_vertices(unsigned i)const noexcept{return kia_deformed_.empty()?expanded_[i]:kia_deformed_[i];}
 IDirect3DTexture8* texture(uint32_t i)const noexcept{return i<textures_.size()?textures_[i]:nullptr;}
 bool prepare_headlight(const DrawSnapshot&,bool original,bool private_tree,unsigned part=0)noexcept;const std::vector<FrontendVertex>& headlight_vertices(unsigned part=0)const noexcept{return headlight_current_[part];}
 bool initialize(IDirect3DDevice8&)noexcept;void reset()noexcept;void invalidate()noexcept{kia_deformed_.clear();kia_revision_=UINT64_MAX;kia_damage.invalidate_current();fleet_damage.invalidate_current();for(auto& v:headlight_current_)v.clear();damage.invalidate_current();deformation_ready_=false;deformation_revision_=UINT64_MAX;trim17_native_runs.clear();kia_warmup={};wheel_owners={};fleet_wheel_owners={};environment_known=false;validated=false;parts_validated=0;certified=false;seen=0;records={};observed_frame=drawn_frame=UINT64_MAX;owner={};}
 void disable()noexcept{ps2diag::disable_log().note("model","draw_failed_or_exception");disabled_=true;invalidate();}
};
}

