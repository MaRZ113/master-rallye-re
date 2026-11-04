#pragma once
#include "live_settings.hpp"
#include "ps2_race_certificate.hpp"
// Native layer of GroundDetail (renderer/ground_detail.hpp). Compiled only into the staged baseline.
// Admits a draw only when the complete PC `shader/base_noise` contract (585ac0) is live on the native
// device and the stage1 texture is the exact PC noise-tga; anything else stays the original draw.
#include "dip_integration.hpp"
#include "ground_detail.hpp"

namespace gfx2::groundintegration {
// MRallye.exe course mesh draw loop (0x57707e), observed for every base_noise draw in F10 traces.
inline constexpr uintptr_t COURSE_DRAW_RETURN_RVA=0x17707e;

inline ps2port::GroundDetail* ground(Device8& d) noexcept {return d.ps2_port()?d.ps2_port()->ground_detail():nullptr;}

inline void log(Device8& d,ps2port::GroundDetail& g,const char* reason,HRESULT hr=S_OK) noexcept {
    if(auto* x=d.ps2_port())x->note(ps2diag::Effect::GroundDetail,reason);
    if(!g.note_reason(reason))return;
    try{session().write("{\"type\":\"ps2_ground_detail\",\"reason\":\""+std::string(reason)+"\",\"hr\":"+std::to_string(static_cast<uint32_t>(hr))+
        ",\"frame\":"+std::to_string(d.trace.frame_number())+",\"passes\":"+std::to_string(g.passes())+"}");}catch(...){}
}

inline HRESULT repair(Device8& d) noexcept {
    auto* g=ground(d);if(!g||!g->transaction.pending())return S_OK;
    g->transaction.set_writer(&d,[](void* o,uint32_t slot,const Args& a,HRESULT hr) noexcept {dipintegration::notify(*static_cast<Device8*>(o),slot,a,hr);});
    return g->transaction.restore(*d.native());
}

// The proxy's tracked native state (effective_shadow, updated by every forwarded and native-only write) answers
// first; only an unknown value is read back from the device. ~150 base_noise draws per view and frame.
inline bool stage_value(Device8& d,IDirect3DDevice8& n,DWORD s,D3DTEXTURESTAGESTATETYPE k,DWORD& v) noexcept {
    const auto& t=d.trace.effective_shadow.tss[s][k];if(t.known){v=t.value;return true;}
    return SUCCEEDED(n.GetTextureStageState(s,k,&v));
}
inline bool stage(Device8& d,IDirect3DDevice8& n,DWORD s,D3DTEXTURESTAGESTATETYPE k,DWORD expected) noexcept {DWORD v=0;return stage_value(d,n,s,k,v)&&v==expected;}
inline bool render(Device8& d,IDirect3DDevice8& n,D3DRENDERSTATETYPE k,DWORD expected) noexcept {
    const auto& t=d.trace.effective_shadow.rs[k];if(t.known)return t.value==expected;
    DWORD v=0;return SUCCEEDED(n.GetRenderState(k,&v))&&v==expected;
}

// The course landscape is drawn with an identity WORLD; cars (race fleet, menu COMPLETE models) and Egg models share the
// course draw loop 0x57707e but carry their own WORLD. FPS1.3: without this test ForestFix took the blended COMPLETE parts
// (glass) of the menu car, so the frontend model never saw all its source draws and stayed PC.
inline bool course_world(Device8& d) noexcept {
    const auto& w=d.trace.effective_shadow.matrices[D3DTS_WORLD];if(!w.known)return false;
    for(int r=0;r<4;++r)for(int c=0;c<4;++c)if(w.value.m[r][c]!=(r==c?1.f:0.f))return false;
    return true;
}
// FPS1 ForestFix (docs/perf-fps1): the PC course loop draws the treeblend foliage cards alpha-blended with Z write and
// no alpha test (F10 FranceS1: SRCALPHA/INVSRCALPHA, ZWRITE on, ALPHATEST off), so their transparent texels write depth
// and cut out every later layer behind them. The PS2 treeblend mode (docs TREEBLEND1: mode 2, ABE1, ATE0, ZMSK1) blends
// with depth writes masked: ForestFix=1 does exactly that. ForestFix=2 keeps depth and drops texels at or below
// ForestFixAlphaRef (default 32) instead. The sky (Z off) is never matched.
inline dipintegration::Result forest(Device8& d,ps2port::GroundDetail& g,IDirect3DDevice8& n,D3DPRIMITIVETYPE type,UINT min_index,UINT vertices,UINT start,UINT count) noexcept {
    auto& t=g.transaction;
    t.set_writer(&d,[](void* o,uint32_t slot,const Args& a,HRESULT hr) noexcept {dipintegration::notify(*static_cast<Device8*>(o),slot,a,hr);});
    HRESULT hr=t.capture(n,&d.trace.effective_shadow);if(FAILED(hr)){log(d,g,"forest_capture_failed",hr);return {};}
    if(g.forest_fix()==1)hr=t.set(n,ps2port::kForestZWriteOp,FALSE);
    else{
        hr=t.set(n,ps2port::kForestAlphaTestOp,TRUE);
        if(SUCCEEDED(hr))hr=t.set(n,ps2port::kForestAlphaFuncOp,D3DCMP_GREATER);
        if(SUCCEEDED(hr))hr=t.set(n,ps2port::kForestAlphaRefOp,g.forest_alpha_ref());
    }
    if(FAILED(hr)){const HRESULT restored=t.restore(n);log(d,g,"forest_state_failed",hr);if(FAILED(restored)){g.disable();return {true,restored};}return {};}
    const HRESULT drawn=n.DrawIndexedPrimitive(type,min_index,vertices,start,count);
    const HRESULT restored=t.restore(n);
    if(FAILED(restored)){g.disable();log(d,g,"forest_restore_failed",restored);return {true,restored};}
    log(d,g,FAILED(drawn)?"forest_draw_failed":"forest_fix_applied",drawn);
    return {true,drawn};
}

inline dipintegration::Result draw(Device8& d,D3DPRIMITIVETYPE type,UINT min_index,UINT vertices,UINT start,UINT count,uintptr_t pc) noexcept {
    if(ps2port::perf::bypassed(ps2port::perf::BypassGround))return {};ps2port::perf::Timer perf_timer(ps2port::perf::Ground);
    auto* g=ground(d);if(!g)return {};
    if(const char* startup=g->take_startup_reason())log(d,*g,startup);
    // PAUSE-MENU1 live switches: ground noise and ForestFix independently.
    const bool ground_on=g->requested()&&!ps2port::live::disabled(ps2port::live::Ground),forest_on=g->forest_fix()&&!ps2port::live::disabled(ps2port::live::Forest);
    if((!ground_on&&!forest_on)||!count||!d.trace.scene_active||d.trace.shadow.recording||d.trace.effective_shadow.recording||
       GetCurrentThreadId()!=d.trace.render_thread_id())return {};
    auto& n=*d.native();
    if(forest_on&&pc==reinterpret_cast<uintptr_t>(GetModuleHandleW(nullptr))+COURSE_DRAW_RETURN_RVA&&course_world(d)&&
       render(d,n,D3DRS_ALPHABLENDENABLE,TRUE)&&render(d,n,D3DRS_ZWRITEENABLE,TRUE)&&render(d,n,D3DRS_ALPHATESTENABLE,FALSE)&&
       render(d,n,D3DRS_ZENABLE,D3DZB_TRUE)&&render(d,n,D3DRS_SRCBLEND,D3DBLEND_SRCALPHA)&&render(d,n,D3DRS_DESTBLEND,D3DBLEND_INVSRCALPHA))
        return forest(d,*g,n,type,min_index,vertices,start,count);
    if(!ground_on)return {};
    // Cheap pre-filter: only the noise stage of base_noise uses MODULATE2X in stage1.
    if(!stage(d,n,1,D3DTSS_COLOROP,D3DTOP_MODULATE2X))return {};
    if(pc!=reinterpret_cast<uintptr_t>(GetModuleHandleW(nullptr))+COURSE_DRAW_RETURN_RVA){log(d,*g,"modulate2x_outside_course_draw_loop");return {};}
    // Complete base_noise contract (opaque variant only; _alpha/_alphatest stay original).
    DWORD pixel=1;const auto& tracked_ps=d.trace.effective_shadow.bindings.pixel_shader;
    if(tracked_ps.known)pixel=tracked_ps.value;else if(FAILED(n.GetPixelShader(&pixel)))pixel=1;
    if(!stage(d,n,0,D3DTSS_COLOROP,D3DTOP_MODULATE)||!stage(d,n,0,D3DTSS_COLORARG1,D3DTA_TEXTURE)||!stage(d,n,0,D3DTSS_COLORARG2,D3DTA_DIFFUSE)||
       !stage(d,n,1,D3DTSS_COLORARG1,D3DTA_CURRENT)||!stage(d,n,1,D3DTSS_COLORARG2,D3DTA_TEXTURE)||!stage(d,n,1,D3DTSS_TEXTURETRANSFORMFLAGS,D3DTTFF_DISABLE)||
       !stage(d,n,2,D3DTSS_COLOROP,D3DTOP_DISABLE)||pixel){log(d,*g,"base_noise_stage_contract_mismatch");return {};}
    if(!render(d,n,D3DRS_ALPHABLENDENABLE,FALSE)||!render(d,n,D3DRS_ALPHATESTENABLE,FALSE)||!render(d,n,D3DRS_ZENABLE,D3DZB_TRUE)||
       !render(d,n,D3DRS_BLENDOP,D3DBLENDOP_ADD)){log(d,*g,"base_noise_variant_not_opaque_or_state_mismatch");return {};}
    ps2integration::Ref<IDirect3DBaseTexture8> noise;
    if(FAILED(n.GetTexture(1,&noise.value))||!noise.value){log(d,*g,"stage1_texture_missing");return {};}
    const auto noise_id=reinterpret_cast<uintptr_t>(noise.value);
    const auto& tracked=d.trace.effective_shadow.bindings.textures[1];
    if(!tracked.known||tracked.value!=noise_id){log(d,*g,"stage1_texture_not_tracked");return {};}
    const auto identity=g->identify(noise.value,d.trace.resources.generation(noise_id));
    if(!identity.match){log(d,*g,identity.reason);return {};}
    if(!g->caps_ok(n)){log(d,*g,"device_caps_rejected");return {};}
    if(!g->initialize(n)){log(d,*g,"ps2_noise_texture_create_failed");return {};}

    auto& t=g->transaction;
    t.set_writer(&d,[](void* o,uint32_t slot,const Args& a,HRESULT hr) noexcept {dipintegration::notify(*static_cast<Device8*>(o),slot,a,hr);});
    HRESULT hr=t.capture(n,&d.trace.effective_shadow);if(FAILED(hr)){log(d,*g,"transaction_capture_failed",hr);return {};}
    DWORD uv=0,address_u=0,address_v=0;
    if(!stage_value(d,n,1,D3DTSS_TEXCOORDINDEX,uv)||!stage_value(d,n,1,D3DTSS_ADDRESSU,address_u)||
       !stage_value(d,n,1,D3DTSS_ADDRESSV,address_v)){t.release();log(d,*g,"stage1_sampler_read_failed");return {};}
    if(g->single_pass()){
        // GroundDetail=2: one draw, stage1 = CURRENT - PS2 noise on the PC noise UV/sampler. Unlike the PS2 the
        // noise is fogged (it fades with distance); no extra draw and four state writes instead of ~40.
        hr=t.set(n,0,D3DTOP_SUBTRACT);if(SUCCEEDED(hr))hr=t.set(n,ps2port::kGroundStage1TextureOp,0,g->texture());
        if(FAILED(hr)){const HRESULT restored=t.restore(n);log(d,*g,"single_pass_state_failed",hr);if(FAILED(restored)){g->disable();return {true,restored};}return {};}
        const HRESULT single=n.DrawIndexedPrimitive(type,min_index,vertices,start,count);
        const HRESULT restored=t.restore(n);
        if(FAILED(restored)){g->disable();log(d,*g,"restore_failed",restored);return {true,restored};}
        if(FAILED(single)){log(d,*g,"single_pass_draw_failed",single);return {true,single};}
        g->count_pass();log(d,*g,"ground_detail_single_pass_applied");
        return {true,single};
    }
    // Pass 1: the original draw without the PC noise term.
    hr=t.set(n,0,D3DTOP_DISABLE);if(SUCCEEDED(hr))hr=t.set(n,1,D3DTOP_DISABLE);
    if(FAILED(hr)){const HRESULT restored=t.restore(n);log(d,*g,"pass1_state_failed",hr);if(FAILED(restored)){g->disable();return {true,restored};}return {};}
    const HRESULT drawn=n.DrawIndexedPrimitive(type,min_index,vertices,start,count);
    // Pass 2: dest - PS2 noise on the same geometry and the PC noise UV set, unfogged, no Z write.
    HRESULT second=drawn;
    if(SUCCEEDED(second)){
        const std::array<std::pair<size_t,DWORD>,19> pass2{{
            {2,TRUE},{3,D3DBLEND_ONE},{4,D3DBLEND_ONE},{5,D3DBLENDOP_REVSUBTRACT},{6,FALSE},{7,D3DCMP_LESSEQUAL},{8,FALSE},{9,FALSE},
            {10,D3DTOP_SELECTARG1},{11,D3DTA_TEXTURE},{12,D3DTOP_SELECTARG1},{13,D3DTA_TEXTURE},{14,uv},{15,address_u},{16,address_v},
            {17,D3DTEXF_LINEAR},{18,D3DTEXF_LINEAR},{19,D3DTEXF_LINEAR},{20,D3DTTFF_DISABLE}}};
        for(const auto& [i,v]:pass2){second=t.set(n,i,v);if(FAILED(second))break;}
        if(SUCCEEDED(second))second=t.set(n,ps2port::kGroundStage0TextureOp,0,g->texture());
        if(SUCCEEDED(second))second=n.DrawIndexedPrimitive(type,min_index,vertices,start,count);
    }
    const HRESULT restored=t.restore(n);
    if(FAILED(restored)){g->disable();log(d,*g,"restore_failed",restored);return {true,restored};}
    if(FAILED(drawn)){log(d,*g,"pass1_draw_failed",drawn);return {true,drawn};}
    if(FAILED(second)){log(d,*g,"pass2_failed",second);return {true,drawn};}
    g->count_pass();log(d,*g,"ground_detail_applied");
    return {true,drawn};
}
}  // namespace gfx2::groundintegration
