#pragma once
#include "ps2_port_extension.hpp"
#include "provenance.hpp"
#include "frontend_transaction.hpp"
#include <array>
#include <vector>
#include <limits>
namespace gfx2::ps2port {
constexpr bool frontend_fixed_pixel_shader(DWORD native,bool known,DWORD shadow)noexcept{return native==0&&(!known||shadow==native);}
struct FrontendVertex {float xyz[3],normal[3];DWORD color;float uv[2];};
static_assert(sizeof(FrontendVertex)==36);
struct FrontendMesh {uint32_t node,mode,texture[3],first,count;};
struct FrontendTexture {UINT width,height;std::vector<DWORD> pixels;};
struct FrontendAsset {std::vector<FrontendVertex> vertices;std::vector<uint32_t> indices;std::vector<FrontendMesh> meshes;std::vector<FrontendTexture> textures;};
bool decode_frontend_asset(const std::vector<uint8_t>&,FrontendAsset&)noexcept;
// Certificate contains current source identity, never historical draw ordinals.
struct FrontendOwner {uintptr_t packet=0,instance=0,model=0,root=0;uint32_t name=0;std::array<uintptr_t,24> meshes{};bool operator==(const FrontendOwner& x)const noexcept{return packet==x.packet&&instance==x.instance&&model==x.model&&root==x.root&&name==x.name&&meshes==x.meshes;}};
struct FrontendRecord {uintptr_t mesh=0;DrawSnapshot geometry;bool valid=false;};
class FrontendModel {
 bool requested_=false,diagnostics_=false,disabled_=false;uint32_t logs_=0;
 FrontendAsset asset_;std::vector<IDirect3DTexture8*> textures_;std::vector<std::vector<FrontendVertex>> expanded_;
public:
 FrontendTransaction transaction;D3DMATRIX environment{};bool environment_known=false,validated=false;
 FrontendOwner owner{};std::array<FrontendRecord,24> records{};uint32_t seen=0;uint64_t observed_frame=UINT64_MAX,drawn_frame=UINT64_MAX;D3DMATRIX drawn_world{};bool certified=false;
 FrontendModel(bool,const std::wstring&)noexcept;~FrontendModel(){transaction.release();reset();}
 bool requested()const noexcept{return requested_&&!disabled_;}bool diagnostics()const noexcept{return diagnostics_;}
 bool claim(uint32_t bit)noexcept{if(!diagnostics_||(logs_&bit))return false;logs_|=bit;return true;}
 const FrontendAsset& asset()const noexcept{return asset_;}const auto& expanded()const noexcept{return expanded_;}
 IDirect3DTexture8* texture(uint32_t i)const noexcept{return i<textures_.size()?textures_[i]:nullptr;}
 bool initialize(IDirect3DDevice8&)noexcept;void reset()noexcept;void invalidate()noexcept{environment_known=false;validated=false;certified=false;seen=0;records={};observed_frame=drawn_frame=UINT64_MAX;owner={};}
 void disable()noexcept{disabled_=true;invalidate();}
};
}
