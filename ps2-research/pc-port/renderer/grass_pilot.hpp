#pragma once

// Source-derived point preview, not the PS2 camera-history placement lifecycle
// or a claim of live VU/GS parity. All coordinates remain game-source world XYZ.
#include "course_objects.hpp"
#include <array>
#include <cstddef>
#include <cstdint>
#include <string>
#include <string_view>
#include <vector>

namespace gfx2::ps2port {
inline constexpr char kTurkey3GrassGxiSha[]="519908ac79ca57591a8a38d3629286e25ffc51539705342864a5056785427eb6";
inline constexpr char kTurkey3GrassPcDxSha[]="724a69da708a124f7dbfd666b7ad8d391bcaf22ff94bd2c91143e305749cf7f8";
inline constexpr char kTurkey3GrassArtifactSha[]="6af6393c444a485b2c648c2a6973a91bd5783db3c0f90269a0d653b2f089cfad";
inline constexpr char kTurkey3BushGxiSha[]="2e4178614fbcbb3dbc3eaf5931001d2a566e76d59ef6adf7e66cd372556d40e9";
inline constexpr char kTurkey3ShrubsArtifactSha[]="688947a32776ffab67c553b4adc95e4597c399f2d70ece37534fd682044752b4";
enum class GroundDetailKind { Grass, Shrubs };
struct GrassSourceContract {
    const char* course;
    const char* psm;
    const char* pc;
    const char* grass_artifact;
    const char* shrubs_artifact;
    const wchar_t* stem;
};
inline constexpr std::array<GrassSourceContract,3> kGrassSources={{
    {"RaceTest/Turkey3",kTurkey3PsmSha,kTurkey3GrassPcDxSha,kTurkey3GrassArtifactSha,kTurkey3ShrubsArtifactSha,L"Turkey3"},
    {"RaceTest/France1","d0b9845218ddd1ff4f12b3b16e77eff43aa182ac73992b5cbea8d81be04f935d",
     "a6bfcef97684f41154596f91fdfaa9522a8fdf6b65d181f4d1ac327b9caf07d5",
     "354cb84c7238e8a1a4959c95fc7e265587f32a3f26dcb29b98aa818c1096f961",
     "69e64191810c4f3ce5b9b06862e9afe8d4ea2a69940ee7d4449cb71430fc2802",L"France1"},
    {"RaceTest/ItalyS1","f74854a0789c1d3bb416cef8d70a02c65141a2d7afc5a150068c047b94bc30a0",
     "5cd86704667cbdc95d4a3b1ff1444c885431fcdd0313cc0f15eca980e3965e8a",
     "e764d52060bc87c797e43459d743ec3dc6a4cd1aff67f239a62c59e82863c1ae",
     "e2d08cfc56f7f3ea8e91b5225ba1b4a228ec40062b361c697426694c0f88234d",L"ItalyS1"}
}};
inline constexpr size_t kGrassMaximumVisiblePoints=16384;
inline constexpr size_t kGrassMaximumAssetBytes=64u*1024u*1024u;
inline constexpr float kGrassBinWidth=8.f;
struct GrassPoint {float x,y,z;};
static_assert(sizeof(GrassPoint)==12);
struct GrassBin {int32_t x,z;uint32_t first,count;};
static_assert(sizeof(GrassBin)==16);
struct GrassAsset {
    std::vector<GrassPoint> points;
    std::vector<GrassBin> bins;
    std::vector<DWORD> texture_bgra;
};

// Layout-only reader exists for synthetic tests. Runtime MUST use the digest
// admission reader below with the independently pinned complete artifact SHA.
bool decode_grass_asset_layout(const uint8_t*,size_t,GrassAsset&,GroundDetailKind=GroundDetailKind::Grass,
                             const GrassSourceContract* source=nullptr) noexcept;
bool decode_grass_asset(const uint8_t*,size_t,std::string_view digest,GrassAsset&,GroundDetailKind=GroundDetailKind::Grass) noexcept;
bool decode_course_grass_asset(const uint8_t*,size_t,std::string_view,GrassAsset&,GroundDetailKind,const GrassSourceContract&) noexcept;
bool grass_ee_floor(float,int32_t&) noexcept;
bool grass_camera_center(const D3DMATRIX&,std::array<float,3>& world_camera,
                         std::array<float,2>& snapped_xz) noexcept;
bool grass_distance_alpha(const GrassPoint&,const std::array<float,2>&,
                          uint32_t& lut_index,float& alpha_128) noexcept;
bool grass_preview_vertices(const GrassAsset&,const D3DMATRIX&,float sprite_half_size,
                            std::vector<ObjectVertex>&,const char*& reason) noexcept;

class GrassPilot {
    GroundDetailKind kind_=GroundDetailKind::Grass;
    bool requested_=false,verified_=false,disabled_=false,suspended_=false,blocked_=false;
    bool diagnostics_=false,logged_rejection_=false,logged_draw_=false,logged_build_=false;
    const char* reason_="stock_default";
    float sprite_half_size_=.33f;
    GrassAsset asset_;
    std::array<GrassAsset,2> extra_assets_;
    std::array<bool,3> course_ready_{};
    bool multi_course_=false;
    size_t selected_course_=0;
    IDirect3DTexture8* texture_=nullptr;
    uint64_t consumed_frame_=UINT64_MAX,consumed_race_=0,consumed_reset_=0;
public:
    CourseWorldProof proof;
    CourseObjectTransaction transaction;
    GrassPilot(bool supported,const std::wstring& ini,GroundDetailKind=GroundDetailKind::Grass) noexcept;
    ~GrassPilot(){shutdown();}
    bool requested()const noexcept{return requested_;}
    bool active()const noexcept{return requested_&&verified_&&!disabled_&&!suspended_&&!blocked_&&texture_;}
    bool identity_requested()const noexcept{return requested_&&verified_&&!disabled_;}
    bool blocked()const noexcept{return blocked_;}
    const char* reason()const noexcept{return reason_;}
    float sprite_half_size()const noexcept{return sprite_half_size_;}
    GroundDetailKind kind()const noexcept{return kind_;}
    const char* category()const noexcept{return kind_==GroundDetailKind::Shrubs?"shrubs":"grass";}
    const char* artifact_sha()const noexcept{return kind_==GroundDetailKind::Shrubs?kGrassSources[selected_course_].shrubs_artifact:kGrassSources[selected_course_].grass_artifact;}
    const char* course()const noexcept{return kGrassSources[selected_course_].course;}
    const GrassAsset& asset()const noexcept{return selected_course_?extra_assets_[selected_course_-1]:asset_;}
    bool select_course(std::string_view,IDirect3DDevice8&) noexcept;
    IDirect3DTexture8* texture()const noexcept{return texture_;}
    bool initialize(IDirect3DDevice8&)noexcept;
    bool build_vertices(const D3DMATRIX&,std::vector<ObjectVertex>&)noexcept;
    bool consume_boundary(uint64_t frame,uint64_t race,uint64_t reset)noexcept;
    bool boundary_consumed(uint64_t frame,uint64_t race,uint64_t reset)const noexcept {
        return consumed_frame_==frame&&consumed_race_==race&&consumed_reset_==reset;
    }
    bool claim_log(bool draw)noexcept;
    bool claim_build_log()noexcept {if(!diagnostics_||logged_build_)return false;logged_build_=true;return true;}
    void disable(const char* reason)noexcept{disabled_=true;reason_=reason;proof.clear();}
    void before_reset()noexcept;
    void after_reset(IDirect3DDevice8&,bool native_called,bool success)noexcept;
    void shutdown()noexcept;
};
} // namespace gfx2::ps2port
