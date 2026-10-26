#pragma once
// COURSE-ALIVE2 (opt-in PS2Birds=1, docs/course-alive2): the PS2 BirdManager on all 36 courses with their own settings.
// Motion: ps2_birds.hpp (portable), one Manager per race generation, 30 game ticks per second (ps2spline::SplineClock),
// frozen while paused, observer = the verified gameplay camera. Draw: the PS2 Burdy bank (BURDYBROWN.PSB frames 0..2,
// atlas cells as separate textures = PS2 REGION_CLAMP), texture x white (MODULATE), source-alpha blend, no depth write,
// depth test, course fog, after the course and water at the typed pre-UI boundary (same proof as spline objects).
#include "course_objects.hpp"
#include "ps2_birds.hpp"
#include "ps2_spline_motion.hpp"
#include "spline_objects.hpp"
#include <array>
#include <cstdint>
#include <string>
#include <string_view>
#include <vector>

namespace gfx2::ps2port {

inline constexpr char kPS2BirdsArtifactSha[]="f37cebd6821b83fc8137c070ba8537d59221a5323be76b13e6340ade0b158c8c";
inline constexpr size_t kBirdCell=16;

struct BirdFrameTriangle { std::array<float,6> xy{}, uv{}; };
struct BirdFrame { uint32_t cell=0; std::array<BirdFrameTriangle,2> tri{}; float u0=0,v0=0; };
struct BirdCourseDef {
    std::string id,dx_path; std::array<uint8_t,32> retail_sha{};
    float min_fly=0,max_fly=0,min_mil=0,max_mil=0; int32_t rnd_fly=0,rnd_mil=0;
    bool flight_present=false,mill_present=false; uint32_t first=0,count=0;
};
struct BirdsAsset {
    std::array<std::vector<DWORD>,4> cells;   // 16x16 BGRA, VRAM row order (row 0 = PS2 v 0.75)
    std::array<BirdFrame,4> frames;
    std::vector<BirdCourseDef> courses;
    std::vector<ps2birds::Vec3> points;
};
bool decode_birds_layout(const uint8_t*,size_t,BirdsAsset&) noexcept;
bool decode_birds_asset(const uint8_t*,size_t,std::string_view digest,BirdsAsset&) noexcept;
size_t birds_course_index(const BirdsAsset&,std::string_view course_id) noexcept;
ps2birds::CourseConfig birds_course_config(const BirdsAsset&,size_t course);

// Camera of a verified D3D gameplay VIEW matrix (row vectors): position, look (view +z) and up (view +y) in world space.
bool birds_camera(const D3DMATRIX& view,ps2birds::Vec3& position,ps2birds::Vec3& look,ps2birds::Vec3& up) noexcept;
struct BirdBatch { uint32_t cell=0; std::vector<ObjectVertex> vertices; };
// World triangle lists per atlas cell for the current snapshot (frame key -> PSB frame -> cell).
bool birds_build(const BirdsAsset&,const std::vector<ps2birds::BirdView>&,const ps2birds::Vec3& look,const ps2birds::Vec3& up,
                 std::vector<BirdBatch>&) noexcept;

class PS2BirdsPilot {
    bool requested_=false,verified_=false,disabled_=false,suspended_=false,blocked_=false;
    bool diagnostics_=false,stock_courses_=false,ignore_gate_=false,logged_rejection_=false,logged_draw_=false,course_log_pending_=false;
    const char* reason_="stock_default";
    BirdsAsset asset_;
    std::array<IDirect3DTexture8*,4> textures_{};
    ps2birds::Manager manager_;
    ps2spline::SplineClock clock_;
    size_t course_=SIZE_MAX;uint64_t race_=0;
    // The PS2 RNG is one process-global stream (seeded once, 1d5de0); it continues from race to race.
    uint32_t session_rng_=ps2birds::kSeed;bool manager_started_=false;
    uint64_t consumed_frame_=UINT64_MAX,consumed_race_=0,consumed_reset_=0;
    uint64_t advanced_frame_=UINT64_MAX,last_qpc_=0,guard_race_=0,last_log_slot_=0;
    size_t guard_course_=SIZE_MAX;const char* guard_reason_="not_checked";
    std::wstring game_root_;
    void release_textures() noexcept;
public:
    CourseWorldProof proof;
    CourseObjectTransaction transaction;
    PS2BirdsPilot(bool supported,const std::wstring& ini) noexcept;
    ~PS2BirdsPilot(){shutdown();}
    bool requested()const noexcept{return requested_;}
    bool active()const noexcept{return requested_&&verified_&&!disabled_&&!suspended_&&!blocked_&&textures_[0];}
    bool identity_requested()const noexcept{return requested_&&verified_&&!disabled_;}
    bool blocked()const noexcept{return blocked_;}
    bool diagnostics()const noexcept{return diagnostics_;}
    bool ignore_gate()const noexcept{return ignore_gate_;}
    const char* reason()const noexcept{return reason_;}
    const char* guard_reason()const noexcept{return guard_reason_;}
    const BirdsAsset& asset()const noexcept{return asset_;}
    const ps2birds::Manager& manager()const noexcept{return manager_;}
    size_t course()const noexcept{return course_;}
    uint64_t race()const noexcept{return race_;}
    IDirect3DTexture8* texture(uint32_t cell)const noexcept{return cell<textures_.size()?textures_[cell]:nullptr;}
    bool initialize(IDirect3DDevice8&) noexcept;
    // Live race certificate course; a new race generation restarts the manager (pool, clock, RNG seed).
    bool select_course(std::string_view course_id,uint64_t race_generation) noexcept;
    // Once per frame: host time -> 30 Hz ticks with the camera of this frame.
    unsigned advance_frame(uint64_t frame,bool paused,const ps2birds::Vec3& camera) noexcept;
    bool take_course_log() noexcept {const bool v=course_log_pending_;course_log_pending_=false;return v;}
    bool claim_state_log() noexcept;
    bool consume_boundary(uint64_t frame,uint64_t race,uint64_t reset)noexcept;
    bool boundary_consumed(uint64_t frame,uint64_t race,uint64_t reset)const noexcept {
        return consumed_frame_==frame&&consumed_race_==race&&consumed_reset_==reset;
    }
    bool claim_log(bool draw)noexcept;
    void disable(const char* reason)noexcept{ps2diag::disable_log().note("birds",reason);disabled_=true;reason_=reason;proof.clear();course_=SIZE_MAX;race_=0;}
    void before_reset()noexcept;
    void after_reset(IDirect3DDevice8&,bool native_called,bool success)noexcept;
    void shutdown()noexcept;
};
} // namespace gfx2::ps2port
