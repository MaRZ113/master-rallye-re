#pragma once
#include "xtrail_fidelity.hpp"
#include "lamp_transaction.hpp"
#include <vector>
namespace gfx2::ps2port {
struct GlassSourceVertex {std::array<uint8_t,32> position_hash;float expected_normal[3],expected_uv[2];DWORD expected_color;float normal[3],uv[2];DWORD color;};
static_assert(sizeof(GlassSourceVertex)==80);
bool decode_xtrail_glass(const std::vector<uint8_t>&,std::vector<GlassSourceVertex>&,std::vector<DWORD>&,std::vector<DWORD>&) noexcept;
std::vector<XtrailDecalVertex> glass_vertices(const DrawSnapshot&,const std::vector<GlassSourceVertex>&,std::string_view expected);
class XtrailGlass {
    bool requested_=false,diagnostics_=false,disabled_=false,blocked_=false,ready_=false;
    struct Cache {std::array<uint64_t,15> key{};std::vector<XtrailDecalVertex> vertices;bool valid=false;};
    std::array<Cache,16> cache_{};size_t next_=0;
    uint32_t logged_=0;std::vector<GlassSourceVertex> vertices_;std::vector<DWORD> primary_,highlight_;
    IDirect3DTexture8* primary_texture_=nullptr;IDirect3DTexture8* highlight_texture_=nullptr;
public:
    LampTransaction transaction;
    XtrailGlass(bool,const std::wstring&)noexcept;
    ~XtrailGlass(){before_reset();}
    bool requested()const noexcept{return requested_&&!disabled_;}
    bool blocked()const noexcept{return blocked_;}
    void disable()noexcept{disabled_=true;}
    bool claim(bool success)noexcept{const uint32_t bit=success?2:1;if(!diagnostics_||(logged_&bit))return false;logged_|=bit;return true;}
    const std::vector<XtrailDecalVertex>* prepare(const DrawSnapshot&)noexcept;
    bool initialize(IDirect3DDevice8&)noexcept;
    IDirect3DTexture8* primary()noexcept{return primary_texture_;}
    IDirect3DTexture8* highlight()noexcept{return highlight_texture_;}
    const std::vector<GlassSourceVertex>& source()const noexcept{return vertices_;}
    void before_reset()noexcept;
    void after_reset(bool called,bool success)noexcept{if(called&&success){blocked_=false;logged_=0;}}
};
} // namespace gfx2::ps2port
