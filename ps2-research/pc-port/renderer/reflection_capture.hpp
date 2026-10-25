#pragma once

// Private, bounded GPU composition. These draws never become application draws.
// Main-target state is restored before the caller submits its original draw.
#include "state_tracker.hpp"
#include "ps2_diag.hpp"
#include <array>
#include <cstdint>
#include <utility>
#include <vector>

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
    bool late=false;   // the capture ran at the end of the world pass for the NEXT frame
    D3DMULTISAMPLE_TYPE source_multisample=D3DMULTISAMPLE_NONE;
    ReflectionCaptureLayout layout{};
    UINT private_draws=0;
};

// COURSE-RENDER-FIX1: one compact readback of every stage of a capture (ReflectionStageDiag=1).
struct ReflectionStageReport {
    bool valid=false, late=false, readback_ok=false;
    uint64_t frame=0, race=0;
    unsigned ordinal=0;
    const char* reason="";
    D3DFORMAT source_format=D3DFMT_UNKNOWN, env_format=D3DFMT_UNKNOWN;
    D3DMULTISAMPLE_TYPE source_multisample=D3DMULTISAMPLE_NONE;
    ps2diag::ImageStats source{}, ps2frame{}, bottom{}, env{}, static_term{}, dynamic{};
    ps2diag::Montage montage;
};
struct ReflectionCaptureCounters {
    uint32_t attempts=0, ok=0, late_ok=0, failed=0, probes=0, probes_incomplete=0, stage_reports=0, readback_failed=0, late_latched_races=0, resolve_latch_cleared=0;
    const char* last_failure="";
    HRESULT last_failure_hr=S_OK;
};
// Diagnostics only (reflection_inspect.hpp): after a successful capture the surfaces are handed to an installed inspector, which
// reads the scheduled stages back. reflection_capture.cpp itself never reads a surface back.
struct ReflectionInspectInput {
    IDirect3DDevice8* native=nullptr;
    IDirect3DSurface8 *copy=nullptr, *ps2frame=nullptr, *target=nullptr;
    D3DFORMAT copy_format=D3DFMT_UNKNOWN, target_format=D3DFMT_UNKNOWN, source_format=D3DFMT_UNKNOWN;
    D3DMULTISAMPLE_TYPE source_multisample=D3DMULTISAMPLE_NONE;
    UINT source_width=0, source_height=0;
    uint64_t frame=0, race=0; unsigned ordinal=0; bool late=false, probe=false, stage=false;
    const char* reason="";
    const std::vector<uint8_t>* static_rgb=nullptr;
};
struct ReflectionInspectResult { bool probe_ok=false, incomplete=false; ReflectionStageReport report; };
class ReflectionInspector {
public:
    virtual ~ReflectionInspector()=default;
    virtual void inspect(const ReflectionInspectInput&,ReflectionInspectResult&) noexcept=0;
    virtual void release() noexcept=0;
};
// Observer: begin (before the work) and end (with the outcome) of every capture attempt that does work.
struct ReflectionCaptureEvent { uint64_t frame=0; bool late=false, begin=true; HRESULT hr=S_OK; const char* reason=""; };
using ReflectionCaptureObserver=void(*)(void*,const ReflectionCaptureEvent&) noexcept;

class MixedReflectionCapture {
    IDirect3DTexture8* copy_texture_=nullptr;
    IDirect3DSurface8* copy_surface_=nullptr;
    IDirect3DTexture8* mixed_texture_=nullptr;
    IDirect3DSurface8* mixed_surface_=nullptr;
    // PS2 frame-sized intermediate (640x448): the original downsamples a 640x448 frame into 64x64.
    IDirect3DTexture8* ps2frame_texture_=nullptr;
    IDirect3DSurface8* ps2frame_surface_=nullptr;
    // COURSE-RENDER-FIX1: second target of the end-of-world capture (valid for the next frame), created on first use.
    IDirect3DTexture8* late_texture_=nullptr;
    IDirect3DSurface8* late_surface_=nullptr;
    D3DFORMAT format_=D3DFMT_UNKNOWN;
    D3DFORMAT target_format_=D3DFMT_UNKNOWN;
    bool prefer_16bit_=false;
    bool debug_pattern_=false;
    ReflectionCaptureLayout layout_{};
    ReflectionCaptureTransaction transaction_;
    ReflectionCaptureStatus status_{};
    uint64_t ready_frame_=0, attempted_frame_=0, late_frame_=0, late_attempted_frame_=0;
    bool ready_=false, attempted_=false, late_ready_=false, late_attempted_=false;
    bool permanently_unsupported_=false, late_unsupported_=false, msaa_resolve_latched_=false;
    ps2diag::TimingDecision decision_{};
    ReflectionCaptureCounters counters_{};
    void* observer_context_=nullptr;
    ReflectionCaptureObserver observer_=nullptr;
    std::vector<uint8_t> static_rgb_;
    mutable uint64_t served_total_=0, served_frame_=0;
    mutable uint32_t served_in_frame_=0;
    ReflectionStageReport report_{};
    bool report_pending_=false;
    ReflectionInspector* inspector_=nullptr;
    HRESULT allocate(IDirect3DDevice8&,const D3DSURFACE_DESC&,const ReflectionCaptureLayout&) noexcept;
    HRESULT allocate_late(IDirect3DDevice8&) noexcept;
    void release_resources() noexcept;
    HRESULT execute(IDirect3DDevice8&,IDirect3DTexture8* env,uint64_t frame,bool late,bool recording) noexcept;
    void inspect(IDirect3DDevice8&,IDirect3DSurface8* target,uint64_t frame,bool late,bool probe,bool stage) noexcept;
public:
    MixedReflectionCapture()=default;
    ~MixedReflectionCapture(){release();}
    MixedReflectionCapture(const MixedReflectionCapture&)=delete;
    MixedReflectionCapture& operator=(const MixedReflectionCapture&)=delete;
    void prefer_16bit(bool enabled) noexcept {prefer_16bit_=enabled;}
    // ReflectionDebug: the target holds only the (pattern) static pass, no framebuffer term.
    void debug_pattern(bool enabled) noexcept {debug_pattern_=enabled;}
    void set_writer(void* context,ReflectionCaptureWriter writer) noexcept {transaction_.set_writer(context,writer);}
    void set_observer(void* context,ReflectionCaptureObserver observer) noexcept {observer_context_=context;observer_=observer;}
    // Diagnostics: the readbacks of the timing probe and the stage report (null = none; the inspector outlives the capture).
    void set_inspector(ReflectionInspector* inspector) noexcept {inspector_=inspector;}
    // ReflectionCaptureTiming / ReflectionStageDiag (default: the original in-frame capture, no readbacks).
    void configure(ps2diag::CaptureTiming timing,bool stage_diag) noexcept {decision_.configure(timing,stage_diag);}
    // 64x64 BGRA of the static term (80/128 already applied) for the stage report.
    void set_static_pixels(const std::vector<DWORD>& bgra);
    // Race generation of the frame being drawn (0 outside a race); restarts the per-race timing probe.
    void set_race(uint64_t generation) noexcept;
    const ps2diag::TimingDecision& decision() const noexcept {return decision_;}
    bool late_wanted() const noexcept {return decision_.late_wanted();}
    HRESULT capture(IDirect3DDevice8&,IDirect3DTexture8* weighted_static_env,
                    uint64_t frame,bool stateblock_recording) noexcept;
    // End of the world pass of `frame`: captures the finished frame for use by frame+1 (no car in the PS2 sense, but the
    // whole course). The in-frame capture() of frame+1 then returns at once.
    HRESULT capture_late(IDirect3DDevice8&,IDirect3DTexture8* weighted_static_env,
                         uint64_t frame,bool stateblock_recording) noexcept;
    bool take_stage_report(ReflectionStageReport& out) noexcept {if(!report_pending_)return false;out=std::move(report_);report_={};report_pending_=false;return true;}
    HRESULT repair(IDirect3DDevice8&) noexcept;
    void release() noexcept;
    IDirect3DTexture8* ready_texture(uint64_t frame) const noexcept {
        if(pending())return nullptr;
        IDirect3DTexture8* texture=nullptr;
        if(ready_&&ready_frame_==frame)texture=mixed_texture_;
        else if(late_ready_&&late_frame_==frame)texture=late_texture_;
        if(texture){ // consumer lookups of the env target (stage report: do the car draws actually receive it?)
            ++served_total_;
            if(served_frame_!=frame){served_frame_=frame;served_in_frame_=0;}
            ++served_in_frame_;
        }
        return texture;
    }
    bool has_ready(uint64_t frame) const noexcept {
        return !pending()&&((ready_&&ready_frame_==frame)||(late_ready_&&late_frame_==frame));
    }
    uint64_t served_total() const noexcept {return served_total_;}
    uint64_t served_last_frame() const noexcept {return served_frame_;}
    uint32_t served_in_frame() const noexcept {return served_in_frame_;}
    bool pending() const noexcept {return transaction_.pending();}
    // ReflectionDebug=2 view: the last composed target, whatever frame it belongs to.
    IDirect3DTexture8* last_texture() const noexcept {
        if(pending())return nullptr;
        if(ready_&&late_ready_)return late_frame_>=ready_frame_?late_texture_:mixed_texture_;
        return late_ready_?late_texture_:ready_?mixed_texture_:nullptr;
    }
    const ReflectionCaptureStatus& last_status() const noexcept {return status_;}
    const ReflectionCaptureCounters& counters() const noexcept {return counters_;}
    bool permanently_unsupported() const noexcept {return permanently_unsupported_;}
    bool resources_allocated() const noexcept {return copy_texture_&&mixed_texture_&&ps2frame_texture_;}
    bool late_allocated() const noexcept {return late_texture_!=nullptr;}
};
} // namespace gfx2::ps2port
