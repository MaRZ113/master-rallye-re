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
// * COURSE-ALIVE4 (opt-in PS2CheckpointBarrels=1, docs/course-alive4): the 432 PS2 checkpoint barrels (12 per course on all
//   36 courses). On the PS2 every gaRaceSplitTimeAI turns the Eggs "<its Egg>-0..3" into gaAiRigidBody props on its first
//   update (1822c0: mass 500, MOI 487.5/900/487.5, barrel PSM); here they are props of the same World (flag bit 1), and the
//   native PC checkpoint boards (Misc/Checkpoints/checkpoint.dx) of such a course are not drawn.
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

inline constexpr char kRigidPropsArtifactSha[]="12750a3d8ea43976fd15555175b7a7b4094aa79bbe7acb42ffc4092ae3fa53da";
inline constexpr size_t kRigidPropsMaximumAssetBytes=4u*1024u*1024u;
inline constexpr size_t kRigidMaximumPropsPerCourse=32;
inline constexpr uint32_t kRigidMaterialObject=0,kRigidMaterialTreeblend=1,kRigidMaterialMetal=2;   // metal: drawn as object
inline constexpr uint32_t kRigidFlagShadow=1,kRigidFlagCheckpoint=2;
// Native PC checkpoint boards (Misc/Checkpoints/checkpoint.dx): draw 0 = 48 triangles of i2a_planks2-tga, draw 1 = 4
// triangles of stamp_01-tga; SHA-256 of the 128x128 A8R8G8B8 level 0 as uploaded (the DXT pixel bytes, GroundDetail rule).
inline constexpr char kPcCheckpointPlanksSha[]="906be0d95d48376b1e3e595229f294c1f0d1ceef110a0c64247a176d4bf299bb";
inline constexpr char kPcCheckpointStampSha[]="dbba864c047e577e77e15f583ace512c26f0c1136059a6ad5bbffbbada5ffc7a";
inline constexpr UINT kPcCheckpointPlanksTriangles=48,kPcCheckpointStampTriangles=4;

struct RigidTexture { uint32_t width=0,height=0; std::vector<DWORD> bgra; };
struct RigidModelDraw { uint32_t texture=0,first=0,count=0; };
struct RigidModel {
    std::string name; uint32_t material=kRigidMaterialObject; std::vector<RigidModelDraw> draws; float radius=0;
    ps2rigid::Hull hull;
    int32_t env=-1;                        // $shader(dull): CommonTextures/dull added by the mode-3 environment pass
    std::array<float,6> aabb{};            // model AABB min, max (the 332628 shadow box)
};
struct RigidPropDef { std::string egg; uint32_t model=0; bool casts_shadow=false,checkpoint=false; float mass=0; ps2rigid::V3 moi{}; float trigger=0; std::array<float,12> matrix{}; };
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
// Course Studio assets: accepted when the file digest equals the pinned artifact or the 64-hex digest the owner
// declared in the INI (RigidPropsAssetSha256, written by the Studio build next to its asset); the full layout check
// of decode_rigid_props_layout applies either way.
bool decode_rigid_props_asset_declared(const uint8_t*,size_t,std::string_view digest,std::string_view declared,
                                       RigidPropsAsset&) noexcept;
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

// Which props of a course take part: hay bales/tumbleweeds (RigidProps=1) and/or checkpoint barrels (PS2CheckpointBarrels=1).
struct RigidSelection { bool props=true,barrels=true; };
// Asset prop indices of a course that the selection admits, in asset order.
std::vector<uint32_t> rigid_members(const RigidPropsAsset&,size_t course,RigidSelection) noexcept;

// The per-race physics of one course. No D3D: tests drive it directly.
class RigidCourseRuntime {
    const RigidPropsAsset* asset_=nullptr;
    const ps2rigid::Terrain* terrain_=nullptr;
    size_t course_=SIZE_MAX;uint64_t race_=0;
    std::vector<uint32_t> members_;        // asset prop index of every body
    size_t barrels_=0;
    ps2rigid::World world_;
    ps2rigid::TickClock clock_;
    struct CarTrack { ps2rigid::Pose pose; double time=0; bool have=false; };
    std::unordered_map<uint32_t,CarTrack> cars_;
    uint32_t car_wakes_=0;
public:
    bool start(const RigidPropsAsset&,size_t course,const ps2rigid::Terrain&,uint64_t race_generation,RigidSelection={}) noexcept;
    void stop() noexcept {asset_=nullptr;terrain_=nullptr;course_=SIZE_MAX;race_=0;members_.clear();barrels_=0;world_.stop();clock_.reset();cars_.clear();car_wakes_=0;}
    const std::vector<uint32_t>& members() const noexcept {return members_;}
    size_t barrels() const noexcept {return barrels_;}
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
    bool requested_=false,verified_=false,disabled_=false,suspended_=false,blocked_=false,declared_asset_=false;
    bool diagnostics_=false,stock_courses_=false,logged_rejection_=false,logged_draw_=false,car_impulse_=true;
    RigidSelection selection_{false,false};
    // COURSE-ALIVE4: race generation whose World holds barrels (the native boards of that race are not drawn).
    uint64_t barrel_race_=0;uint64_t boards_hidden_=0;bool logged_boards_=false;
    struct BoardIdentity { uintptr_t texture=0; uint64_t generation=0; int kind=0; };   // 1 planks, 2 stamp, 0 other
    std::array<BoardIdentity,16> boards_{};size_t next_board_=0;
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
    RigidSelection selection()const noexcept{return selection_;}
    bool barrels_requested()const noexcept{return selection_.barrels;}
    // Barrels of race `race_generation` are simulated and drawn: its native checkpoint boards are to be hidden.
    bool hide_boards(uint64_t race_generation)const noexcept{return active()&&race_generation&&barrel_race_==race_generation&&runtime_.ready()&&runtime_.barrels();}
    // Stage-0 texture content of a native draw: 1 = PC checkpoint planks, 2 = PC checkpoint stamp, 0 = other (cached).
    int board_texture(IDirect3DBaseTexture8*,uint64_t generation) noexcept;
    uint64_t note_board_hidden() noexcept {return ++boards_hidden_;}
    bool claim_board_log() noexcept {if(!diagnostics_||logged_boards_)return false;logged_boards_=true;return true;}
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
