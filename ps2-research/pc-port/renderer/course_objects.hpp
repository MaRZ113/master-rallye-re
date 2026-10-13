#pragma once
#include "sdk.hpp"
#include "course_object_transaction.hpp"
#include <array>
#include <cstdint>
#include <string>
#include <string_view>
#include <vector>

namespace gfx2::ps2port {
inline constexpr char kTurkey3PsmSha[]="dd274ac1cb56c16d35410fbe2e8e3771a750b47710b747fddc70604fdb3d59fc";
inline constexpr char kTurkey3WaterSha[]="65a8318d8c432764c91d56b53b843f8096b4629d3f53894d4d6d5caf46945d34";
// Filled from the independently extracted deterministic local artifact.
inline constexpr char kTurkey3ObjectArtifactSha[]="2e3d6f8c90b3ed602d121f96fe7246a6fe3b70ab7c3c5d547c4bb8bf03a02b95";
enum class SourceCoordinates { GameWorld };
enum class ObjectMaterial { PuddleAuthoredTexturePreview=1 };
struct ObjectVertex {float x,y,z;DWORD color;float u,v;};
static_assert(sizeof(ObjectVertex)==24);
struct SourceMesh {uint32_t node_offset,material_offset,first_vertex,vertex_count;};
struct CourseObjectAsset {
    SourceCoordinates coordinates=SourceCoordinates::GameWorld;
    ObjectMaterial material=ObjectMaterial::PuddleAuthoredTexturePreview;
    std::vector<SourceMesh> meshes;
    std::vector<ObjectVertex> vertices;
    std::vector<DWORD> texture_bgra;
};
bool decode_course_object_asset(const uint8_t*,size_t,std::string_view digest,CourseObjectAsset&) noexcept;
bool turkey3_course(std::string_view) noexcept;
bool course_id_matches(std::string_view,std::string_view) noexcept;
struct CourseAdmission {
    bool supported_build=false,render_thread=false,scene_active=false,asset_ready=false;
    bool ui_callsite=false,ui_consumer=false,camera_single=false,race_valid=false;
    bool view_site=false,projection_site=false,world_draw=false,target_matches=false;
    bool depth_matches=false,viewport_matches=false,pc_depth_convention=false;
    bool native_dependency_states=false,state_block_recording=false;
    std::string_view course;
    uint64_t frame=0,proof_frame=UINT64_MAX,device=0,proof_device=0;
    uint64_t reset=0,proof_reset=0,race=0,proof_race=0,owner=0,proof_owner=0;
    uint32_t camera=0,proof_camera=0;
};
const char* course_object_admission(const CourseAdmission&,std::string_view source_course="RaceTest/Turkey3") noexcept;
struct CourseWorldProof {
    uint64_t frame=UINT64_MAX,device=0,reset=0,race=0,owner=0;
    uint32_t camera=0;bool view_site=false,projection_site=false,world_draw=false;
    D3DMATRIX view{},projection{};D3DVIEWPORT8 viewport{};
    IDirect3DSurface8* target=nullptr;IDirect3DSurface8* depth=nullptr;
    CourseWorldProof()=default;
    CourseWorldProof(const CourseWorldProof&)=delete;
    ~CourseWorldProof(){clear();}
    void invalidate_depth() noexcept {world_draw=false;if(target)target->Release();if(depth)depth->Release();target=depth=nullptr;}
    void clear() noexcept {if(target)target->Release();if(depth)depth->Release();target=depth=nullptr;
        frame=UINT64_MAX;device=reset=race=owner=0;camera=0;view_site=projection_site=world_draw=false;}
};
// Cheap rejection BEFORE reading race broker keys or native GPU state.
// This is not admission: the live certificate and complete native checks
// still follow for every eligible private batch.
struct CourseBoundaryContext {
    uint64_t frame=0,device=0,reset=0;
    bool render_thread=false,scene_active=false,ui_consumer=false,state_block_recording=false;
};
inline bool course_world_preflight(const CourseWorldProof& p,const CourseBoundaryContext& c) noexcept {
    return c.render_thread&&c.scene_active&&c.ui_consumer&&!c.state_block_recording&&
        c.device&&p.frame==c.frame&&p.device==c.device&&p.reset==c.reset&&
        p.race&&p.owner&&p.camera&&p.view_site&&p.projection_site&&p.world_draw;
}
class CourseObjectsPilot {
    bool requested_=false,verified_=false,disabled_=false,suspended_=false,blocked_=false;
    bool diagnostics_=false,logged_rejection_=false,logged_draw_=false;
    const char* reason_="stock_default";
    CourseObjectAsset asset_;
    IDirect3DTexture8* texture_=nullptr;
    uint64_t consumed_frame_=UINT64_MAX,consumed_race_=0,consumed_reset_=0;
public:
    CourseWorldProof proof;
    CourseObjectTransaction transaction;
    CourseObjectsPilot(bool supported,const std::wstring& ini) noexcept;
    ~CourseObjectsPilot(){shutdown();}
    bool requested()const noexcept{return requested_;}
    bool active()const noexcept{return requested_&&verified_&&!disabled_&&!suspended_&&!blocked_&&texture_;}
    bool identity_requested()const noexcept{return requested_&&verified_&&!disabled_;}
    bool blocked()const noexcept{return blocked_;}
    const char* reason()const noexcept{return reason_;}
    const CourseObjectAsset& asset()const noexcept{return asset_;}
    IDirect3DTexture8* texture()const noexcept{return texture_;}
    bool initialize(IDirect3DDevice8&)noexcept;
    bool consume_boundary(uint64_t frame,uint64_t race,uint64_t reset)noexcept;
    bool boundary_consumed(uint64_t frame,uint64_t race,uint64_t reset)const noexcept {
        return consumed_frame_==frame&&consumed_race_==race&&consumed_reset_==reset;
    }
    bool claim_log(bool draw)noexcept;
    void disable(const char* reason)noexcept{disabled_=true;reason_=reason;proof.clear();}
    void before_reset()noexcept;
    void after_reset(IDirect3DDevice8&,bool native_called,bool success)noexcept;
    void shutdown()noexcept;
};
} // namespace gfx2::ps2port
