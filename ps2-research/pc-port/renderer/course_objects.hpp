#pragma once
#include "ps2_diag.hpp"
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
// SPLIT-GRASS1 (opt-in PS2SplitScreen=1, docs/split-grass1): the frame scheduler 0x653080 draws every active
// camera into its own viewport (camera 1: SetViewport + PROJECTION + VIEW; camera 2: SetViewport + VIEW only).
// Each camera pass keeps its own world proof; nothing is shared between passes except the frame-level gameplay
// projection, which camera 2 may inherit only when the device still holds exactly that verified matrix.
inline constexpr size_t kCourseSplitPasses=2;
struct CourseWorldPass {
    uint32_t camera=0;bool view_site=false,projection_site=false,world_draw=false;
    D3DMATRIX view{},projection{};D3DVIEWPORT8 viewport{};
    IDirect3DSurface8* target=nullptr;IDirect3DSurface8* depth=nullptr;
    CourseWorldPass()=default;
    CourseWorldPass(const CourseWorldPass&)=delete;
    CourseWorldPass& operator=(const CourseWorldPass&)=delete;
    ~CourseWorldPass(){clear();}
    void invalidate_depth() noexcept {world_draw=false;if(target)target->Release();if(depth)depth->Release();target=depth=nullptr;}
    void clear() noexcept {invalidate_depth();camera=0;view_site=projection_site=false;}
};
struct CourseSplitProof {
    uint64_t frame=UINT64_MAX,device=0,reset=0,race=0,owner=0;
    std::array<CourseWorldPass,kCourseSplitPasses> passes;
    size_t count=0,current=SIZE_MAX;
    bool projection_site=false;D3DMATRIX projection{};
    void invalidate_depth() noexcept {for(auto& pass:passes)pass.invalidate_depth();}
    void clear() noexcept {for(auto& pass:passes)pass.clear();frame=UINT64_MAX;device=reset=race=owner=0;
        count=0;current=SIZE_MAX;projection_site=false;projection={};}
    bool same_frame(uint64_t f,uint64_t d,uint64_t r,uint64_t race_generation,uint64_t owner_lifetime) const noexcept {
        return count&&frame==f&&device==d&&reset==r&&race==race_generation&&owner==owner_lifetime;
    }
    CourseWorldPass* current_pass() noexcept {return current<count?&passes[current]:nullptr;}
    // Selects the pass of `camera` in this frame or opens the next one. A new frame/device/reset/race/owner
    // starts over; a third distinct camera in one frame is not a two-player split and clears everything.
    CourseWorldPass* begin_pass(uint64_t f,uint64_t d,uint64_t r,uint64_t race_generation,uint64_t owner_lifetime,uint32_t camera) noexcept {
        if(!camera||!d||!race_generation||!owner_lifetime){clear();return nullptr;}
        if(!same_frame(f,d,r,race_generation,owner_lifetime)){clear();frame=f;device=d;reset=r;race=race_generation;owner=owner_lifetime;}
        for(size_t i=0;i<count;++i)if(passes[i].camera==camera){current=i;return &passes[i];}
        if(count==kCourseSplitPasses){clear();return nullptr;}
        current=count++;passes[current].clear();passes[current].camera=camera;return &passes[current];
    }
};
struct CourseWorldProof {
    uint64_t frame=UINT64_MAX,device=0,reset=0,race=0,owner=0;
    uint32_t camera=0;bool view_site=false,projection_site=false,world_draw=false;
    D3DMATRIX view{},projection{};D3DVIEWPORT8 viewport{};
    IDirect3DSurface8* target=nullptr;IDirect3DSurface8* depth=nullptr;
    // Empty unless a split-screen certificate is active; render-target/clear/scene hooks reach it through
    // invalidate_depth()/clear() exactly like the single proof.
    CourseSplitProof split;
    CourseWorldProof()=default;
    CourseWorldProof(const CourseWorldProof&)=delete;
    ~CourseWorldProof(){clear();}
    void invalidate_single_depth() noexcept {world_draw=false;if(target)target->Release();if(depth)depth->Release();target=depth=nullptr;}
    void clear_single() noexcept {if(target)target->Release();if(depth)depth->Release();target=depth=nullptr;
        frame=UINT64_MAX;device=reset=race=owner=0;camera=0;view_site=projection_site=world_draw=false;}
    void invalidate_depth() noexcept {invalidate_single_depth();split.invalidate_depth();}
    void clear() noexcept {clear_single();split.clear();}
};
// A split pass viewport lies inside the render target, is not empty and keeps the PC depth range.
inline bool course_split_viewport(const D3DVIEWPORT8& v,UINT width,UINT height) noexcept {
    return v.Width&&v.Height&&v.X<width&&v.Y<height&&v.Width<=width-v.X&&v.Height<=height-v.Y&&v.MinZ==0&&v.MaxZ==1;
}
inline bool course_viewports_disjoint(const D3DVIEWPORT8& a,const D3DVIEWPORT8& b) noexcept {
    const uint64_t ax=a.X,ay=a.Y,bx=b.X,by=b.Y;
    return ax+a.Width<=bx||bx+b.Width<=ax||ay+a.Height<=by||by+b.Height<=ay;
}
struct CourseSplitAdmission {
    bool supported_build=false,render_thread=false,scene_active=false,asset_ready=false;
    bool ui_callsite=false,ui_consumer=false,state_block_recording=false;
    bool race_valid=false,split_certificate=false,native_dependency_states=false;
    std::string_view course;
    uint64_t frame=0,device=0,reset=0,race=0,owner=0;uint32_t camera=0;
    UINT target_width=0,target_height=0;
    std::array<bool,kCourseSplitPasses> target_matches{},depth_matches{},pc_depth_convention{};
};
// Every check of course_object_admission, per pass, plus: exactly two passes of two distinct cameras, the UI
// certificate (scheduler 0x653080 rebinds camera slot 0 for the UI) names one of them, disjoint viewports.
const char* course_split_admission(const CourseSplitAdmission&,const CourseSplitProof&,std::string_view source_course) noexcept;
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
    void disable(const char* reason)noexcept{ps2diag::disable_log().note("course_objects",reason);disabled_=true;reason_=reason;proof.clear();}
    void before_reset()noexcept;
    void after_reset(IDirect3DDevice8&,bool native_called,bool success)noexcept;
    void shutdown()noexcept;
};
} // namespace gfx2::ps2port
