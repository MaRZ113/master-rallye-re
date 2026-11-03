#pragma once
// COURSE-ALIVE3 (opt-in RigidProps=1, docs/course-alive3): the 83 PS2 gaAiRigidBody props of 9 courses (58 hay bales on
// Italy2/S1/S4/W1/W2, 25 tumbleweeds on Turkey1/3/M/S2Flip) as physical objects that the cars knock over.
//
// * Physics: ps2_rigid_props.hpp (portable; PS2 tick, gravity, mass/MOI, activation, far decay, rest and placement from
//   RIGID1, own contact solver), one World per race generation, 30 ticks per second from host time, frozen while the race
//   is paused.
// * Landscape: the course DX tag1400 collision triangles of the installed PS2 course package (the same parse as
//   COLLISION-DEBUG1), loaded once per course on a worker thread; vehicles: the tag101 hull (representation B) of every
//   participant's car.dx at its render instance world matrix (instance+0x44, COLLISION-DEBUG1 round 5), kinematic.
// * Geometry/material: the course-port W5 PC models (hay; tumbleweed with its PS2 texture), packed with their textures and
//   the PS2 tag101 hulls by tools/prepare_rigid_props.py into one pinned private asset. Hay = PS2 object shader (opaque,
//   MODULATE, fog, depth written); tumbleweed = treeblend (source alpha blend, no depth write).
// * Course guard: only a loose course DX that is not the retail PC one (a PS2 course package): the props stand on the PS2
//   terrain, and the PS2 packages hold no static copy of them (docs/course-alive3/README.md).
#include "ps2_diag.hpp"
#include "course_objects.hpp"
#include "course_object_transaction.hpp"
#include "ps2_rigid_props.hpp"
#include "sma_archive.hpp"
#include <array>
#include <atomic>
#include <cstdint>
#include <filesystem>
#include <memory>
#include <string>
#include <string_view>
#include <thread>
#include <unordered_map>
#include <utility>
#include <vector>

namespace gfx2::ps2port {

inline constexpr char kRigidPropsArtifactSha[]="98846199fad8be4bbf29a1f6c4c9e9833e71af52ee126bf867a03174db2d12ba";
inline constexpr size_t kRigidPropsMaximumAssetBytes=4u*1024u*1024u;
inline constexpr size_t kRigidMaximumPropsPerCourse=32;
inline constexpr uint32_t kRigidMaterialObject=0,kRigidMaterialTreeblend=1;

struct RigidTexture { uint32_t width=0,height=0; std::vector<DWORD> bgra; };
struct RigidModelDraw { uint32_t texture=0,first=0,count=0; };
struct RigidModel {
    std::string name; uint32_t material=kRigidMaterialObject; std::vector<RigidModelDraw> draws; float radius=0;
    ps2rigid::Hull hull;
    int32_t env=-1;                        // $shader(dull): CommonTextures/dull added by the mode-3 environment pass
    std::array<float,6> aabb{};            // model AABB min, max (the 332628 shadow box)
};
struct RigidPropDef { std::string egg; uint32_t model=0; bool casts_shadow=false; float mass=0; ps2rigid::V3 moi{}; float trigger=0; std::array<float,12> matrix{}; };
struct RigidCourseDef { std::string id,dx_path; std::array<uint8_t,32> retail_sha{}; uint32_t first=0,count=0; };
struct RigidPropsAsset {
    std::vector<RigidTexture> textures;
    std::vector<RigidModel> models;
    std::vector<ObjectVertex> vertices;
    std::vector<ps2rigid::V3> normals;     // per vertex, model space
    uint32_t shadow_texture=0;             // Misc\Shadow\shadow (black, alpha blob)
    std::vector<RigidCourseDef> courses;
    std::vector<RigidPropDef> props;
};

// Layout-only reader for synthetic tests; the pilot uses the digest-pinned reader.
bool decode_rigid_props_layout(const uint8_t*,size_t,RigidPropsAsset&) noexcept;
bool decode_rigid_props_asset(const uint8_t*,size_t,std::string_view digest,RigidPropsAsset&) noexcept;
size_t rigid_course_index(const RigidPropsAsset&,std::string_view course_id) noexcept;
// Port contact coefficients per material (RIGID1: the PS2 surface coefficients are not identified).
void rigid_material_coefficients(uint32_t material,float& restitution,float& friction,float& rolling) noexcept;

// Landscape from course DX bytes: the unique valid tag1400 (COLLISION-DEBUG1 rule) -> triangle corners and planes.
bool rigid_terrain_from_course_dx(const uint8_t*,size_t,ps2rigid::Terrain&,size_t& records) noexcept;  // + water flags
// car.dx tag101 representation B with its face loops -> convex hull (planes), the COLLISION-DEBUG1 candidate rule.
bool rigid_vehicle_hull(const uint8_t*,size_t,ps2rigid::Hull&) noexcept;

// Draw passes in order: PS2 drop shadows on the ground, opaque objects, their additive environment layer, treeblend.
enum class RigidPass : uint8_t { Shadow, Object, Env, Treeblend };
struct RigidBatch { uint32_t texture=0,material=kRigidMaterialObject; RigidPass pass=RigidPass::Object; float distance=0; std::vector<ObjectVertex> vertices; };
// PS2 drop shadow (332628, the world-entity shadow of the shared model draw 330780) of one prop on the landscape.
// Box = model AABB X x1.75, Z x1.5 in the prop's yaw frame; landscape triangles within half its larger side whose up
// normal n.y > 0.05, not $surfacetype(water), with a vertex below the box centre; vertices lifted 0.1; UV projected into
// the box (+0.5); alpha = n.y * 0.85 / (0.75 * max(0, d - 0.5) + 1), d = depth below the centre along the prop's up axis.
void rigid_shadow_triangles(const ps2rigid::Terrain&,const ps2rigid::Pose&,const std::array<float,6>& aabb,std::vector<ObjectVertex>& out);

// One car of the live race for the physics: the render instance pose and the hull of its folder.
struct RigidCarInput {
    uint32_t instance=0; std::string folder; bool pose_valid=false; std::array<float,12> rows{}; bool local=false;
    // PC vehicle physics body (class 0x691A04: mass +0x20, position +0xA0, P +0x104, L +0x110); 0 = not coupled.
    uint32_t body=0; float mass=0; ps2rigid::V3 com{};
};

// The per-race physics of one course. No D3D: tests drive it directly.
class RigidCourseRuntime {
    const RigidPropsAsset* asset_=nullptr;
    const ps2rigid::Terrain* terrain_=nullptr;
    size_t course_=SIZE_MAX;uint64_t race_=0;
    ps2rigid::World world_;
    ps2rigid::TickClock clock_;
    struct CarTrack { ps2rigid::Pose pose; double time=0; bool have=false; };
    std::unordered_map<uint32_t,CarTrack> cars_;
    uint32_t car_wakes_=0;
public:
    bool start(const RigidPropsAsset&,size_t course,const ps2rigid::Terrain&,uint64_t race_generation) noexcept;
    void stop() noexcept {asset_=nullptr;terrain_=nullptr;course_=SIZE_MAX;race_=0;world_.stop();clock_.reset();cars_.clear();car_wakes_=0;}
    bool ready() const noexcept {return asset_&&course_!=SIZE_MAX&&world_.ready();}
    size_t course() const noexcept {return course_;}
    uint64_t race() const noexcept {return race_;}
    const ps2rigid::World& world() const noexcept {return world_;}
    ps2rigid::World& world_mut() noexcept {return world_;}
    float fraction() const noexcept {return clock_.fraction();}
    // Kinematic car inputs at host time `now` (seconds): velocity from the previous pose of the same instance.
    void cars(const std::vector<RigidCarInput>&,const std::unordered_map<std::string,const ps2rigid::Hull*>& hulls,double now,
              std::vector<ps2rigid::Kinematic>& out) noexcept;
    // Host seconds since the previous frame; no ticks while paused.
    // Coupled cars in `in` collect the reaction impulses of all ticks of the frame.
    unsigned advance(double seconds,bool paused,ps2rigid::TickInput&) noexcept;
    void tick(unsigned n,ps2rigid::TickInput&) noexcept;
    // World-space triangle lists in draw order (shadows, objects, environment, treeblend far to near) at the interpolated
    // pose. view = the gameplay VIEW matrix (environment UV from view-space normals); shadows within shadow_range.
    bool build(const ps2rigid::V3& camera,const float* view16,float shadow_range,std::vector<RigidBatch>&) const noexcept;
};

class RigidPropsPilot {
    bool requested_=false,verified_=false,disabled_=false,suspended_=false,blocked_=false;
    bool diagnostics_=false,stock_courses_=false,logged_rejection_=false,logged_draw_=false,car_impulse_=true;
    unsigned impulse_logs_=0;
    const char* reason_="stock_default";
    RigidPropsAsset asset_;
    std::vector<IDirect3DTexture8*> textures_;
    RigidCourseRuntime runtime_;
    uint64_t consumed_frame_=UINT64_MAX,consumed_reset_=0,advanced_frame_=UINT64_MAX,last_qpc_=0,last_state_log_=0;
    uint64_t guard_race_=0;size_t guard_course_=SIZE_MAX;const char* guard_reason_="not_checked";bool course_log_pending_=false;
    std::wstring game_root_,archive_path_;
    // Landscape: one course DX per course, parsed on a worker thread; the terrain stays while the course is the same.
    struct TerrainJob { std::string dx_path; ps2rigid::Terrain terrain; size_t records=0; const char* reason="not_loaded"; double ms=0; };
    std::thread worker_;std::atomic<bool> job_done_{false};bool loading_=false;TerrainJob job_;
    std::string terrain_path_;ps2rigid::Terrain terrain_;size_t terrain_records_=0;const char* terrain_reason_="not_loaded";double terrain_ms_=0;
    void finish_job() noexcept;
    // Vehicle hulls by car folder (lower case): loose DataGx in the working directory or the proxy folder, else Data.sma.
    struct GameRoot { std::filesystem::path folder; std::unique_ptr<sma::Archive> archive; };
    std::vector<GameRoot> roots_;bool roots_ready_=false;
    std::unordered_map<std::string,std::unique_ptr<ps2rigid::Hull>> hulls_;std::string missing_hulls_;
    void ensure_roots() noexcept;
    bool read_game_file(const std::string& rel,std::vector<uint8_t>& out,uint64_t limit) const;
    void release_textures() noexcept;
public:
    CourseObjectTransaction transaction;
    struct Proof { uint64_t frame=UINT64_MAX,device=0,reset=0; bool view_site=false,projection_site=false; D3DMATRIX view{},projection{};
                   void clear() noexcept {*this=Proof{};} } proof;
    RigidPropsPilot(bool supported,const std::wstring& ini) noexcept;
    ~RigidPropsPilot(){shutdown();}
    bool requested()const noexcept{return requested_;}
    bool active()const noexcept{return requested_&&verified_&&!disabled_&&!suspended_&&!blocked_&&!textures_.empty();}
    bool identity_requested()const noexcept{return requested_&&verified_&&!disabled_;}
    bool blocked()const noexcept{return blocked_;}
    bool diagnostics()const noexcept{return diagnostics_;}
    // RigidPropsCarImpulse (default 1): props push back on the cars through the PC vehicle body momenta.
    bool car_impulse()const noexcept{return car_impulse_;}
    const char* reason()const noexcept{return reason_;}
    const char* guard_reason()const noexcept{return guard_reason_;}
    const char* terrain_reason()const noexcept{return terrain_reason_;}
    size_t terrain_records()const noexcept{return terrain_records_;}
    double terrain_ms()const noexcept{return terrain_ms_;}
    const std::string& missing_hulls()const noexcept{return missing_hulls_;}
    const RigidPropsAsset& asset()const noexcept{return asset_;}
    const RigidCourseRuntime& runtime()const noexcept{return runtime_;}
    RigidCourseRuntime& runtime_mut() noexcept{return runtime_;}
    IDirect3DTexture8* texture(uint32_t i)const noexcept{return i<textures_.size()?textures_[i]:nullptr;}
    bool initialize(IDirect3DDevice8&) noexcept;
    // Course id of the live race certificate: guard, landscape load and a new World on a new race generation.
    // False = not a prop course, guard refused, landscape still loading or bad data (guard_reason()).
    bool select_course(std::string_view course_id,uint64_t race_generation) noexcept;
    // Hull of a car folder (loaded on first use); nullptr when missing or unparsable.
    const ps2rigid::Hull* hull(const std::string& folder) noexcept;
    // Once per frame: host time -> PS2 ticks.
    unsigned advance_frame(uint64_t frame,bool paused,ps2rigid::TickInput&) noexcept;
    double host_seconds() const noexcept;
    bool take_course_log() noexcept {const bool v=course_log_pending_;course_log_pending_=false;return v;}
    bool claim_state_log() noexcept;
    bool consume_boundary(uint64_t frame,uint64_t reset) noexcept {
        if(consumed_frame_==frame&&consumed_reset_==reset)return false;consumed_frame_=frame;consumed_reset_=reset;return true;}
    // Car impulse records (diagnostics): at most 64 per session.
    bool claim_impulse_log()noexcept{if(!diagnostics_||impulse_logs_>=64)return false;++impulse_logs_;return true;}
    bool claim_log(bool draw)noexcept{auto& done=draw?logged_draw_:logged_rejection_;if(!diagnostics_||done)return false;done=true;return true;}
    void disable(const char* reason)noexcept{ps2diag::disable_log().note("rigid_props",reason);disabled_=true;reason_=reason;proof.clear();runtime_.stop();}
    void before_reset()noexcept;
    void after_reset(IDirect3DDevice8&,bool native_called,bool success)noexcept;
    void shutdown()noexcept;
};
} // namespace gfx2::ps2port
