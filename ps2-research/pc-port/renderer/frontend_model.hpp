#pragma once
#include "ps2_port_extension.hpp"
#include "provenance.hpp"
#include "frontend_transaction.hpp"
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
struct FrontendVertex {float xyz[3],normal[3];DWORD color;float uv[2];};
static_assert(sizeof(FrontendVertex)==36);
// X-Trail COMPLETE runtime primary sampling orientation, established by user A/B.
inline FrontendVertex frontend_primary_sample_vertex(FrontendVertex v)noexcept{v.uv[1]=1.0f-v.uv[1];return v;}
struct FrontendMesh {uint32_t node,mode,texture[3],first,count;};
struct FrontendTexture {UINT width,height;std::vector<DWORD> pixels;};
struct FrontendAsset {std::vector<FrontendVertex> vertices;std::vector<uint32_t> indices;std::vector<FrontendMesh> meshes;std::vector<FrontendTexture> textures;};
bool decode_frontend_asset(const std::vector<uint8_t>&,FrontendAsset&,unsigned role=0,const FleetProfile* profile=nullptr)noexcept;
// Certificate contains current source identity, never historical draw ordinals.
struct FrontendOwner {uintptr_t packet=0,instance=0,model=0,root=0;uint32_t name=0;std::array<uintptr_t,32> meshes{};bool operator==(const FrontendOwner& x)const noexcept{return packet==x.packet&&instance==x.instance&&model==x.model&&root==x.root&&name==x.name&&meshes==x.meshes;}};
struct FrontendRecord {uintptr_t mesh=0;DrawSnapshot geometry;bool valid=false;};
struct WheelOwnerState {FrontendOwner owner{};std::array<FrontendRecord,4> records{};uint64_t frame=UINT64_MAX;uint32_t seen=0;bool certified=false;D3DMATRIX world{};};
class FrontendModel {
 const FleetProfile* profile_=nullptr;std::wstring ini_;bool fleet_=false;
 bool requested_=false,diagnostics_=false,disabled_=false,parts_=false,crew_=false;uint32_t logs_=0;
 FrontendAsset asset_;std::vector<IDirect3DTexture8*> textures_;std::vector<std::vector<FrontendVertex>> expanded_;
 std::array<std::vector<FrontendVertex>,5> trim_;
 std::array<std::vector<FrontendVertex>,2> race_body_;
 std::array<std::vector<FrontendVertex>,4> crew_vertices_;
public:
 std::array<FrontendRecord,64> fleet_probes{};unsigned fleet_probe_count=0;uint32_t fleet_failed=0;
 std::vector<std::pair<unsigned,unsigned>> trim17_native_runs;std::array<WheelOwnerState,4> wheel_owners{};FrontendTransaction transaction;D3DMATRIX environment{};bool environment_known=false,validated=false;
 uint32_t parts_validated=0;uint64_t race_generation=0,race_owner_lifetime=0;FrontendOwner owner{};std::array<FrontendRecord,32> records{};uint32_t seen=0;uint64_t observed_frame=UINT64_MAX,drawn_frame=UINT64_MAX;D3DMATRIX drawn_world{};bool certified=false;
 FrontendModel(bool,const std::wstring&,unsigned role=0,const FleetProfile* profile=nullptr)noexcept;~FrontendModel(){transaction.release();reset();}
 bool fleet_enabled()const noexcept{return fleet_&&!disabled_;}
 const FleetProfile* profile()const noexcept{return profile_;}
 bool select_fleet(const FleetProfile&)noexcept;
 bool requested()const noexcept{return requested_&&!disabled_;}bool diagnostics()const noexcept{return diagnostics_;}
 bool parts_enabled()const noexcept{return requested()&&parts_;}
 bool crew_enabled()const noexcept{return parts_enabled()&&crew_;}
 const auto& crew_vertices(unsigned i)const noexcept{return crew_vertices_[i];}
 bool claim(uint32_t bit)noexcept{if(!diagnostics_||(logs_&bit))return false;logs_|=bit;return true;}
 const FrontendAsset& asset()const noexcept{return asset_;}const auto& expanded()const noexcept{return expanded_;}
 const auto& trim(unsigned i)const noexcept{return trim_[i];}
 const auto& race_vertices(unsigned root)const noexcept{return root==0?race_body_[0]:root==7?race_body_[1]:expanded_[root];}
 IDirect3DTexture8* texture(uint32_t i)const noexcept{return i<textures_.size()?textures_[i]:nullptr;}
 bool initialize(IDirect3DDevice8&)noexcept;void reset()noexcept;void invalidate()noexcept{trim17_native_runs.clear();wheel_owners={};environment_known=false;validated=false;parts_validated=0;certified=false;seen=0;records={};observed_frame=drawn_frame=UINT64_MAX;owner={};}
 void disable()noexcept{disabled_=true;invalidate();}
};
}
