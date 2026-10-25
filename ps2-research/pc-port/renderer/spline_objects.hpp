#pragma once
// COURSE-ALIVE1 (opt-in SplineObjects=1, docs/course-alive1): the 24 PS2 gaEntitySpline objects of 17 courses
// (dinghies, barges, airships) moving on their PS2 routes.
//
// * Motion: ps2_spline_motion.hpp (portable PS2 controller), one Controller per object, 30 Hz invocations from host
//   time, frozen while the race is paused, restarted with every race generation (the PS2 owner is created when the
//   course Egg hatches).
// * Geometry/material: the course-port W5 PC models (DataGx/Misc/PS2Port/<model>, retail loader winding), packed with
//   their DXT textures by tools/prepare_spline_objects.py into one pinned private asset. Drawn as PS2 objects are:
//   texture x vertex colour (MODULATE), opaque, no back-face culling, course fog, depth tested and written.
// * Nothing static is added or hidden: the PS2 course packages contain no spline Egg and no copy of these models
//   (docs/course-alive1/README.md, verify_spline_objects.py), so the moving object is the only instance.
#include "ps2_diag.hpp"
#include "course_objects.hpp"
#include "ps2_spline_motion.hpp"
#include <array>
#include <cstdint>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

namespace gfx2::ps2port {

inline constexpr char kSplineObjectsArtifactSha[]="3b1ae1cb33bbd8807ebd35a61e441c997e601ef34ab7347c87e2e6ef2729a8e8";
inline constexpr size_t kSplineObjectsMaximumAssetBytes=4u*1024u*1024u;
inline constexpr size_t kSplineMaximumObjectsPerCourse=4;

struct SplineTexture { uint32_t width=0,height=0; std::vector<DWORD> bgra; };
struct SplineModelDraw { uint32_t texture=0,first=0,count=0; };
struct SplineModel { std::string name; std::vector<SplineModelDraw> draws; float radius=0; };
struct SplineObjectDef { std::string egg; uint32_t model=0,first_point=0,point_count=0; ps2spline::Config config; };
struct SplineCourseDef { std::string id,dx_path; std::array<uint8_t,32> retail_sha{}; uint32_t first=0,count=0; };
struct SplineObjectsAsset {
    std::vector<SplineTexture> textures;
    std::vector<SplineModel> models;
    std::vector<ObjectVertex> vertices;
    std::vector<SplineCourseDef> courses;
    std::vector<SplineObjectDef> objects;
    std::vector<ps2spline::Vec3> points;
};

// Layout-only reader for synthetic tests; the pilot uses the digest-pinned reader.
bool decode_spline_objects_layout(const uint8_t*,size_t,SplineObjectsAsset&) noexcept;
bool decode_spline_objects_asset(const uint8_t*,size_t,std::string_view digest,SplineObjectsAsset&) noexcept;
// Index of the course entry, or SIZE_MAX.
size_t spline_course_index(const SplineObjectsAsset&,std::string_view course_id) noexcept;

// "ps2_course_package" when the installed loose course DX exists and is not the retail PC file; the stock PC course
// geometry is not the PS2 one these routes were authored for.
const char* spline_course_guard(const std::array<uint8_t,32>& retail,bool loose_present,std::string_view loose_sha_hex) noexcept;

struct SplineBatch { uint32_t texture=0; std::vector<ObjectVertex> vertices; };

// The per-race motion state of one course. No D3D: tests drive it directly.
class SplineCourseRuntime {
    const SplineObjectsAsset* asset_=nullptr;
    size_t course_=SIZE_MAX;
    uint64_t race_=0,ticks_=0;
    std::vector<ps2spline::Controller> controllers_;
    ps2spline::SplineClock clock_;
public:
    bool start(const SplineObjectsAsset&,size_t course,uint64_t race_generation) noexcept;
    void stop() noexcept {asset_=nullptr;course_=SIZE_MAX;race_=ticks_=0;controllers_.clear();clock_.reset();}
    bool ready() const noexcept {return asset_&&course_!=SIZE_MAX&&!controllers_.empty();}
    size_t course() const noexcept {return course_;}
    uint64_t race() const noexcept {return race_;}
    uint64_t ticks() const noexcept {return ticks_;}
    const std::vector<ps2spline::Controller>& controllers() const noexcept {return controllers_;}
    // Host seconds since the previous frame; no ticks while paused. observer = Car0 position or nullptr.
    unsigned advance(double seconds,bool paused,const ps2spline::Vec3* observer) noexcept;
    // Exactly n invocations (tests, diagnostics).
    void tick(unsigned n,const ps2spline::Vec3* observer) noexcept;
    // World-space triangle lists grouped by texture, every object at its current published pose.
    bool build(std::vector<SplineBatch>&) const noexcept;
};

class SplineObjectsPilot {
    bool requested_=false,verified_=false,disabled_=false,suspended_=false,blocked_=false;
    bool diagnostics_=false,stock_courses_=false,logged_rejection_=false,logged_draw_=false;
    const char* reason_="stock_default";
    SplineObjectsAsset asset_;
    std::vector<IDirect3DTexture8*> textures_;
    SplineCourseRuntime runtime_;
    uint64_t consumed_frame_=UINT64_MAX,consumed_race_=0,consumed_reset_=0;
    uint64_t advanced_frame_=UINT64_MAX,last_qpc_=0,guard_race_=0,last_pose_log_=0;
    size_t guard_course_=SIZE_MAX;const char* guard_reason_="not_checked";bool course_log_pending_=false;
    std::wstring game_root_;
    void release_textures() noexcept;
public:
    CourseWorldProof proof;
    CourseObjectTransaction transaction;
    SplineObjectsPilot(bool supported,const std::wstring& ini) noexcept;
    ~SplineObjectsPilot(){shutdown();}
    bool requested()const noexcept{return requested_;}
    bool active()const noexcept{return requested_&&verified_&&!disabled_&&!suspended_&&!blocked_&&!textures_.empty();}
    bool identity_requested()const noexcept{return requested_&&verified_&&!disabled_;}
    bool blocked()const noexcept{return blocked_;}
    bool diagnostics()const noexcept{return diagnostics_;}
    const char* reason()const noexcept{return reason_;}
    const char* guard_reason()const noexcept{return guard_reason_;}
    const SplineObjectsAsset& asset()const noexcept{return asset_;}
    const SplineCourseRuntime& runtime()const noexcept{return runtime_;}
    IDirect3DTexture8* texture(uint32_t i)const noexcept{return i<textures_.size()?textures_[i]:nullptr;}
    bool initialize(IDirect3DDevice8&) noexcept;
    // Course id of the live race certificate. Starts the motion state on a new race generation; false = not a
    // spline course, guard refused or bad data (reason()).
    bool select_course(std::string_view course_id,uint64_t race_generation) noexcept;
    // Once per frame: host time -> PS2 invocations.
    unsigned advance_frame(uint64_t frame,bool paused,const ps2spline::Vec3* observer) noexcept;
    bool claim_pose_log() noexcept;
    // One course-selection record per race generation (guard verdict), for the session log.
    bool take_course_log() noexcept {const bool v=course_log_pending_;course_log_pending_=false;return v;}
    bool consume_boundary(uint64_t frame,uint64_t race,uint64_t reset)noexcept;
    bool boundary_consumed(uint64_t frame,uint64_t race,uint64_t reset)const noexcept {
        return consumed_frame_==frame&&consumed_race_==race&&consumed_reset_==reset;
    }
    bool claim_log(bool draw)noexcept;
    void disable(const char* reason)noexcept{ps2diag::disable_log().note("spline",reason);disabled_=true;reason_=reason;proof.clear();runtime_.stop();}
    void before_reset()noexcept;
    void after_reset(IDirect3DDevice8&,bool native_called,bool success)noexcept;
    void shutdown()noexcept;
};
} // namespace gfx2::ps2port
