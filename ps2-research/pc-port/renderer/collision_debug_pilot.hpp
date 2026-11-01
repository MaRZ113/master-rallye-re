#pragma once
// COLLISION-DEBUG1 (opt-in CollisionDebug=1, docs/collision-debug1): course collision overlay with hotkey-cycled modes.
// Course source per race: every landscape entity of the race XML (loose DataScene/<race>.xml, else the asset table) with
// its en3d Matrix -> its course DX. A loose course DX (converted PS2 courses, new and joined courses) is parsed in place
// (collision_debug.hpp); a retail course, which lives inside Data.sma, comes from CourseCollision.mrcoll
// (tools/prepare_collision_debug.py). The asset is optional. The legend is drawn at Present over the HUD.
#include "collision_debug.hpp"
#include "course_object_transaction.hpp"
#include "ps2_diag.hpp"
#include "ps2_hud_damage.hpp"
#include "sma_archive.hpp"
#include "fleet_participants.hpp"
#include <memory>
#include <unordered_map>
#include <atomic>
#include <cstdint>
#include <thread>
#include <string>
#include <string_view>
#include <vector>

namespace gfx2::ps2port {

inline constexpr char kCollisionDebugArtifactSha[]="5e9426549fa10fd93791cfe4b2813aa27a8be54785a192930466e85520bebbdc";

struct CollisionProof {
    uint64_t frame=UINT64_MAX,device=0,reset=0;
    bool view_site=false,projection_site=false;
    D3DMATRIX view{},projection{};
    void clear() noexcept {*this=CollisionProof{};}
};
// One landscape of the current race: where its collision came from.
struct CollisionLandscape {
    std::string dx_path,source,sha;const char* status="not_loaded";
    size_t triangles=0;bool identity=true;
    // tag100 BSP: tree found, solid cells, object faces (polygons) and their distinct codes.
    bool bsp=false;size_t solid_cells=0,object_faces=0,object_codes=0;
};

// Result of one background course load.
struct CourseLoad {
    colldebug::Mesh mesh;std::vector<CollisionLandscape> landscapes;std::string source="none",race_xml="none";
    const char* reason="not_loaded";double ms=0;bool ok=false;
    std::vector<colldebug::MarkerList> markers;
};

class CollisionDebugPilot {
    bool requested_=false,disabled_=false,suspended_=false,blocked_=false,legend_=true,asset_ok_=false;
    const char* reason_="stock_default";
    std::string asset_reason_="not_requested",asset_sha_;
    std::vector<uint8_t> asset_bytes_;
    std::vector<colldebug::AssetEntry> asset_index_;
    std::wstring game_root_;
    colldebug::Mesh mesh_;
    colldebug::Settings settings_;
    colldebug::Mode mode_=colldebug::Mode::Surface;
    colldebug::LegendAnchor anchor_=colldebug::LegendAnchor::TopCenter;
    UINT key_=0x7A;std::string key_name_="F11";bool key_down_=false,mode_log_pending_=true;
    // Course selection cache (one resolution per race generation and course id).
    std::string course_id_,source_="none",race_xml_;const char* course_reason_="not_selected";
    std::vector<CollisionLandscape> landscapes_;
    uint64_t course_race_=0;bool course_ok_=false,course_log_pending_=false;
    uint64_t consumed_frame_=UINT64_MAX,consumed_reset_=0;
    IDirect3DTexture8* white_=nullptr;
    bool logged_draw_=false,logged_gate_=false;
    bool legend_ready_=false;UINT legend_width_=0,legend_height_=0;const char* legend_logged_=nullptr;
    void release_texture() noexcept;
    const char* load_landscape(const std::string& dx_path,colldebug::Mesh& out,CollisionLandscape& info);
    const char* parse_landscape(const std::vector<uint8_t>& bytes,colldebug::Mesh& out,CollisionLandscape& info,const char* ok);
    // Data.sma (retail courses and race XML), opened on the first course selection.
    sma::Archive sma_;bool sma_tried_=false;std::wstring archive_path_;double load_ms_=0;
    // Background load (BSP faces take 1..2 s per landscape): one worker at a time, applied on the render thread.
    std::thread worker_;std::atomic<bool> job_done_{false};bool loading_=false;CourseLoad job_;
    void load_course(const std::string& id,CourseLoad& r) noexcept;
    // Race markers and vehicle hulls (round 4).
    std::vector<colldebug::MarkerList> markers_;uint8_t markers_mode_=0;UINT markers_key_=0x7B;std::string markers_key_name_="F12";bool markers_key_down_=false;
    bool cars_=true,hull_log_pending_=false;std::unordered_map<std::string,std::unique_ptr<colldebug::Hull>> hulls_;
    void apply_load() noexcept;
public:
    CollisionProof proof;
    CourseObjectTransaction transaction;
    PS2HudLayer legend_layer;
    colldebug::Batch batch;
    colldebug::Legend legend;
    CollisionDebugPilot(bool supported,const std::wstring& ini) noexcept;
    ~CollisionDebugPilot(){shutdown();}
    bool requested()const noexcept{return requested_;}
    bool active()const noexcept{return requested_&&!disabled_&&!suspended_&&!blocked_&&white_;}
    bool blocked()const noexcept{return blocked_;}
    const char* reason()const noexcept{return reason_;}
    const std::string& asset_reason()const noexcept{return asset_reason_;}
    const std::string& asset_sha()const noexcept{return asset_sha_;}
    size_t asset_courses()const noexcept{return asset_index_.size();}
    colldebug::Mode mode()const noexcept{return mode_;}
    colldebug::LegendAnchor anchor()const noexcept{return anchor_;}
    const std::string& key_name()const noexcept{return key_name_;}
    bool legend_enabled()const noexcept{return legend_;}
    const colldebug::Settings& settings()const noexcept{return settings_;}
    const colldebug::Mesh& mesh()const noexcept{return mesh_;}
    const std::string& source()const noexcept{return source_;}
    const std::string& race_xml()const noexcept{return race_xml_;}
    const std::vector<CollisionLandscape>& landscapes()const noexcept{return landscapes_;}
    const char* course_reason()const noexcept{return course_reason_;}
    bool archive_open()const noexcept{return sma_.is_open();}
    bool loading()const noexcept{return loading_;}
    const std::vector<colldebug::MarkerList>& markers()const noexcept{return markers_;}
    uint8_t markers_mode()const noexcept{return markers_mode_;}
    const std::string& markers_key_name()const noexcept{return markers_key_name_;}
    bool cars_enabled()const noexcept{return cars_;}
    const colldebug::Hull* hull(const std::string& folder) noexcept;
    bool take_hull_log() noexcept {const bool v=hull_log_pending_;hull_log_pending_=false;return v;}
    size_t hulls_loaded()const noexcept{size_t n=0;for(const auto& h:hulls_)n+=h.second!=nullptr;return n;}
    size_t hulls_failed()const noexcept{size_t n=0;for(const auto& h:hulls_)n+=h.second==nullptr;return n;}
    ps2port::FleetParticipantResolver participants;
    double load_ms()const noexcept{return load_ms_;}
    IDirect3DTexture8* texture()const noexcept{return white_;}
    bool initialize(IDirect3DDevice8&) noexcept;
    // Edge-triggered hotkey (only while this process owns the foreground window). Returns true when the mode changed.
    bool poll_hotkey() noexcept;
    bool take_mode_log() noexcept {const bool v=mode_log_pending_;mode_log_pending_=false;return v;}
    // Resolves and loads the collision mesh of a race course (once per race generation and course id).
    bool select_course(std::string_view course_id,uint64_t race_generation) noexcept;
    bool take_course_log() noexcept {const bool v=course_log_pending_;course_log_pending_=false;return v;}
    bool consume_boundary(uint64_t frame,uint64_t reset) noexcept {
        if(consumed_frame_==frame&&consumed_reset_==reset)return false;consumed_frame_=frame;consumed_reset_=reset;return true;}
    bool claim_log(bool draw) noexcept {auto& done=draw?logged_draw_:logged_gate_;if(done)return false;done=true;return true;}
    // Legend: built at the pre-UI boundary of a race frame, drawn by the next Present (over the HUD), then consumed.
    void stage_legend(UINT width,UINT height) noexcept {legend_ready_=!legend.quads.empty();legend_width_=width;legend_height_=height;}
    bool legend_ready()const noexcept{return legend_ready_&&active();}
    HRESULT draw_legend(IDirect3DDevice8& device,bool scene_active,bool recording) noexcept;
    // Reason string when the legend draw outcome changed (session log), else nullptr.
    const char* take_legend_log(HRESULT) noexcept {const char* r=legend_layer.status().reason;if(r==legend_logged_)return nullptr;legend_logged_=r;return r;}
    void disable(const char* reason) noexcept {ps2diag::disable_log().note("collision_debug",reason);disabled_=true;reason_=reason;proof.clear();legend_ready_=false;}
    void before_reset() noexcept;
    void after_reset(IDirect3DDevice8&,bool native_called,bool success) noexcept;
    void shutdown() noexcept;
};

// "F1".."F24", "INSERT", "HOME", "PAGEUP"... or a number (decimal / 0x hex). 0 = invalid. F10 is the trace key.
UINT collision_debug_key(const wchar_t* name) noexcept;

} // namespace gfx2::ps2port
