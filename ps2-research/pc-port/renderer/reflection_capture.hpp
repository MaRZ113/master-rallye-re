#pragma once

// Private, bounded GPU composition. These draws never become application draws.
// Main-target state is restored before the caller submits its original draw.
#include "state_tracker.hpp"
#include <array>
#include <cstdint>

namespace gfx2::ps2port {
// Mixed PS2 environment target: .625*static (FIX 80/128) + .375*flipped framebuffer (FIX 48/128).
// The static GXI is already uploaded at 80/128 (ReflectionPilot texture upload), so this pass is unscaled.
inline constexpr DWORD kReflectionStaticPassColor=0xffffffffu;
inline constexpr DWORD kReflectionFramebufferPassColor=0xff606060u;
inline constexpr UINT kPS2FrameWidth=640,kPS2FrameHeight=448;

struct ReflectionCaptureLayout {
    UINT source_width=0, source_height=0, texture_width=0, texture_height=0;
    uint64_t bytes=0;
};
bool reflection_capture_layout(UINT width, UINT height, const D3DCAPS8& caps,
                               ReflectionCaptureLayout& out) noexcept;
struct ReflectionCaptureVertex { float x,y,z,rhw; DWORD color; float u,v; };
std::array<ReflectionCaptureVertex,4> reflection_capture_quad(
    float u_max, float v_max, bool flip_y, DWORD color,float width=64.f,float height=64.f) noexcept;

enum class ReflectionCaptureStateKind : uint8_t { Render, Stage, VertexShader, PixelShader, Texture };
struct ReflectionCaptureStateOp {
    ReflectionCaptureStateKind kind;
    DWORD key, stage, value;
};
inline constexpr std::array<ReflectionCaptureStateOp,42> kReflectionCaptureOps={{
    {ReflectionCaptureStateKind::Render,D3DRS_ZENABLE,0,D3DZB_FALSE},
    {ReflectionCaptureStateKind::Render,D3DRS_ZWRITEENABLE,0,FALSE},
    {ReflectionCaptureStateKind::Render,D3DRS_ALPHATESTENABLE,0,FALSE},
    {ReflectionCaptureStateKind::Render,D3DRS_ALPHABLENDENABLE,0,FALSE},
    {ReflectionCaptureStateKind::Render,D3DRS_SRCBLEND,0,D3DBLEND_ONE},
    {ReflectionCaptureStateKind::Render,D3DRS_DESTBLEND,0,D3DBLEND_ONE},
    {ReflectionCaptureStateKind::Render,D3DRS_BLENDOP,0,D3DBLENDOP_ADD},
    {ReflectionCaptureStateKind::Render,D3DRS_CULLMODE,0,D3DCULL_NONE},
    {ReflectionCaptureStateKind::Render,D3DRS_LIGHTING,0,FALSE},
    {ReflectionCaptureStateKind::Render,D3DRS_FOGENABLE,0,FALSE},
    {ReflectionCaptureStateKind::Render,D3DRS_STENCILENABLE,0,FALSE},
    {ReflectionCaptureStateKind::Render,D3DRS_CLIPPLANEENABLE,0,0},
    {ReflectionCaptureStateKind::Render,D3DRS_COLORWRITEENABLE,0,15},
    {ReflectionCaptureStateKind::Render,D3DRS_FILLMODE,0,D3DFILL_SOLID},
    {ReflectionCaptureStateKind::Render,D3DRS_CLIPPING,0,TRUE},
    {ReflectionCaptureStateKind::Render,D3DRS_DITHERENABLE,0,FALSE},
    {ReflectionCaptureStateKind::Render,D3DRS_SPECULARENABLE,0,FALSE},
    {ReflectionCaptureStateKind::Render,D3DRS_VERTEXBLEND,0,D3DVBF_DISABLE},
    {ReflectionCaptureStateKind::Render,D3DRS_INDEXEDVERTEXBLENDENABLE,0,FALSE},
    {ReflectionCaptureStateKind::Render,D3DRS_WRAP0,0,0},
    {ReflectionCaptureStateKind::Stage,D3DTSS_COLOROP,0,D3DTOP_MODULATE},
    {ReflectionCaptureStateKind::Stage,D3DTSS_COLORARG1,0,D3DTA_TEXTURE},
    {ReflectionCaptureStateKind::Stage,D3DTSS_COLORARG2,0,D3DTA_DIFFUSE},
    {ReflectionCaptureStateKind::Stage,D3DTSS_ALPHAOP,0,D3DTOP_SELECTARG2},
    {ReflectionCaptureStateKind::Stage,D3DTSS_ALPHAARG1,0,D3DTA_TEXTURE},
    {ReflectionCaptureStateKind::Stage,D3DTSS_ALPHAARG2,0,D3DTA_DIFFUSE},
    {ReflectionCaptureStateKind::Stage,D3DTSS_TEXCOORDINDEX,0,0},
    {ReflectionCaptureStateKind::Stage,D3DTSS_TEXTURETRANSFORMFLAGS,0,D3DTTFF_DISABLE},
    {ReflectionCaptureStateKind::Stage,D3DTSS_ADDRESSU,0,D3DTADDRESS_CLAMP},
    {ReflectionCaptureStateKind::Stage,D3DTSS_ADDRESSV,0,D3DTADDRESS_CLAMP},
    {ReflectionCaptureStateKind::Stage,D3DTSS_MAGFILTER,0,D3DTEXF_LINEAR},
    {ReflectionCaptureStateKind::Stage,D3DTSS_MINFILTER,0,D3DTEXF_LINEAR},
    {ReflectionCaptureStateKind::Stage,D3DTSS_MIPFILTER,0,D3DTEXF_NONE},
    {ReflectionCaptureStateKind::Stage,D3DTSS_RESULTARG,0,D3DTA_CURRENT},
    {ReflectionCaptureStateKind::Stage,D3DTSS_MAXMIPLEVEL,0,0},
    {ReflectionCaptureStateKind::Stage,D3DTSS_MIPMAPLODBIAS,0,0},
    {ReflectionCaptureStateKind::Stage,D3DTSS_COLOROP,1,D3DTOP_DISABLE},
    {ReflectionCaptureStateKind::Stage,D3DTSS_ALPHAOP,1,D3DTOP_DISABLE},
    {ReflectionCaptureStateKind::VertexShader,0,0,D3DFVF_XYZRHW|D3DFVF_DIFFUSE|D3DFVF_TEX1},
    {ReflectionCaptureStateKind::PixelShader,0,0,0},
    {ReflectionCaptureStateKind::Texture,0,0,0},
    {ReflectionCaptureStateKind::Texture,0,1,0},
}};

using ReflectionCaptureWriter=void(*)(void*,uint32_t,const Args&,HRESULT) noexcept;
struct ReflectionCaptureSaved { DWORD scalar=0; IDirect3DBaseTexture8* texture=nullptr; };

class ReflectionCaptureTransaction {
    std::array<ReflectionCaptureSaved,kReflectionCaptureOps.size()> saved_{};
    uint64_t pending_=0;
    IDirect3DSurface8* target_=nullptr;
    IDirect3DSurface8* depth_=nullptr;
    IDirect3DVertexBuffer8* stream_=nullptr;
    UINT stride_=0;
    D3DVIEWPORT8 viewport_{};
    bool captured_=false, target_pending_=false, viewport_pending_=false, stream_pending_=false;
    ReflectionCaptureWriter writer_=nullptr;
    void* context_=nullptr;
    void notify(uint32_t slot,const Args& args,HRESULT hr) noexcept;
    HRESULT write(IDirect3DDevice8&,size_t,const ReflectionCaptureSaved&) noexcept;
public:
    ReflectionCaptureTransaction()=default;
    ~ReflectionCaptureTransaction(){release();}
    ReflectionCaptureTransaction(const ReflectionCaptureTransaction&)=delete;
    ReflectionCaptureTransaction& operator=(const ReflectionCaptureTransaction&)=delete;
    void set_writer(void* context,ReflectionCaptureWriter writer) noexcept {context_=context;writer_=writer;}
    bool pending() const noexcept {return pending_||target_pending_||viewport_pending_||stream_pending_;}
    HRESULT capture(IDirect3DDevice8&) noexcept;
    HRESULT apply(IDirect3DDevice8&,IDirect3DSurface8* private_target,IDirect3DTexture8* env,UINT width=64,UINT height=64,bool chained=false) noexcept;
    HRESULT framebuffer_pass(IDirect3DDevice8&,IDirect3DTexture8* copied_frame) noexcept;
    // Mark before UP, including failing submissions. Explicitly synchronize its
    // native stream side effect afterward without recording another game draw.
    void mark_up() noexcept {stream_pending_=captured_;}
    HRESULT sync_up_stream(IDirect3DDevice8&) noexcept;
    HRESULT restore(IDirect3DDevice8&) noexcept;
    void release() noexcept; // Reset/final teardown only if native repair is pending.
};

struct ReflectionCaptureStatus {
    const char* reason="not_attempted";
    uint64_t frame=0;
    HRESULT capture_hr=S_FALSE, copy_hr=S_FALSE, restore_hr=S_FALSE;
    D3DFORMAT source_format=D3DFMT_UNKNOWN;
    D3DFORMAT target_format=D3DFMT_UNKNOWN;
    bool precision_fallback=false;
    D3DMULTISAMPLE_TYPE source_multisample=D3DMULTISAMPLE_NONE;
    ReflectionCaptureLayout layout{};
    UINT private_draws=0;
};

class MixedReflectionCapture {
    IDirect3DTexture8* copy_texture_=nullptr;
    IDirect3DSurface8* copy_surface_=nullptr;
    IDirect3DTexture8* mixed_texture_=nullptr;
    IDirect3DSurface8* mixed_surface_=nullptr;
    // PS2 frame-sized intermediate (640x448): the original downsamples a 640x448 frame into 64x64.
    IDirect3DTexture8* ps2frame_texture_=nullptr;
    IDirect3DSurface8* ps2frame_surface_=nullptr;
    D3DFORMAT format_=D3DFMT_UNKNOWN;
    D3DFORMAT target_format_=D3DFMT_UNKNOWN;
    bool prefer_16bit_=false;
    bool debug_pattern_=false;
    ReflectionCaptureLayout layout_{};
    ReflectionCaptureTransaction transaction_;
    ReflectionCaptureStatus status_{};
    uint64_t ready_frame_=0, attempted_frame_=0;
    bool ready_=false, attempted_=false;
    bool permanently_unsupported_=false;
    HRESULT allocate(IDirect3DDevice8&,const D3DSURFACE_DESC&,const ReflectionCaptureLayout&) noexcept;
    void release_resources() noexcept;
public:
    MixedReflectionCapture()=default;
    ~MixedReflectionCapture(){release();}
    MixedReflectionCapture(const MixedReflectionCapture&)=delete;
    MixedReflectionCapture& operator=(const MixedReflectionCapture&)=delete;
    void prefer_16bit(bool enabled) noexcept {prefer_16bit_=enabled;}
    // ReflectionDebug: the target holds only the (pattern) static pass, no framebuffer term.
    void debug_pattern(bool enabled) noexcept {debug_pattern_=enabled;}
    void set_writer(void* context,ReflectionCaptureWriter writer) noexcept {transaction_.set_writer(context,writer);}
    HRESULT capture(IDirect3DDevice8&,IDirect3DTexture8* weighted_static_env,
                    uint64_t frame,bool stateblock_recording) noexcept;
    HRESULT repair(IDirect3DDevice8&) noexcept;
    void release() noexcept;
    IDirect3DTexture8* ready_texture(uint64_t frame) const noexcept {
        return ready_&&ready_frame_==frame&&!pending()?mixed_texture_:nullptr;
    }
    bool pending() const noexcept {return transaction_.pending();}
    // ReflectionDebug=2 view: the last composed target, whatever frame it belongs to.
    IDirect3DTexture8* last_texture() const noexcept {return ready_&&!pending()?mixed_texture_:nullptr;}
    const ReflectionCaptureStatus& last_status() const noexcept {return status_;}
};
} // namespace gfx2::ps2port
