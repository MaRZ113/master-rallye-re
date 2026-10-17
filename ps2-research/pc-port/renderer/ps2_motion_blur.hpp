#pragma once
// Opt-in PS2MotionBlur (default 0 = off): the PS2 display-copy blend, applied last before Present.
//
// PS2 (ps2-research/course-light1/findings.md section 10, EE 2f5528/2ef870/1b1e70): every frame the
// draw buffer is copied into the display buffer with ALPHA (Cs-Cd)*FIX+Cd, FIX = 128 - blur*128, the
// display buffer still holding the previous shown frame. Race chase camera: FIX 103 (blur 0.195)
// measured in a GS dump. PC: shown = new*(1-b) + previous_shown*b, b = PS2MotionBlur, in races only.
// The PS2 (PAL, SLES-50906) renders one full frame per 50 Hz vsync (GS dumps: same GIF traffic every
// vsync), so b is a per-20 ms weight; the PC frame weight is b^(dt*50) to keep the same trail in time.
// PS2MotionBlur=0/1 switches it; PS2MotionBlurStrength = b (default 0.195 = measured chase camera,
// 0 = no blend, capped at 0.9; unparsable text keeps the default).
#include "sdk.hpp"
#include <array>
#include <cmath>
#include <cstdint>
#include <cwchar>

namespace gfx2::ps2port {

inline constexpr float kPS2ChaseMotionBlur=0.195f,kPS2FrameRate=50.f,kMotionBlurMaxFrameTime=0.1f;

inline float parse_motion_blur_strength(const wchar_t* text) noexcept {
    if(!text||!text[0])return kPS2ChaseMotionBlur;
    wchar_t* end=nullptr;const float v=std::wcstof(text,&end);
    if(end==text||v!=v)return kPS2ChaseMotionBlur;
    return v<=0.f?0.f:v>0.9f?0.9f:v;
}

// Per-frame history weight for a frame of dt seconds, matched to the PS2 50 Hz frame weight b.
inline float motion_blur_frame_weight(float blur,float dt) noexcept {
    if(!(blur>0.f))return 0.f;
    if(!(dt>0.f))dt=1.f/kPS2FrameRate;
    return float(std::pow(double(blur),double(dt)*kPS2FrameRate));
}

inline DWORD motion_blur_factor(float blur) noexcept {
    const float c=blur<0.f?0.f:blur>1.f?1.f:blur;
    return DWORD(c*255.f+.5f)<<24;
}

enum class BlurStateKind : uint8_t { Render, Stage, VertexShader, PixelShader, Texture };
struct BlurStateOp { BlurStateKind kind; DWORD key, stage, value; };
inline constexpr std::array<BlurStateOp,40> kMotionBlurOps={{
    {BlurStateKind::Render,D3DRS_ZENABLE,0,D3DZB_FALSE},{BlurStateKind::Render,D3DRS_ZWRITEENABLE,0,FALSE},
    {BlurStateKind::Render,D3DRS_ALPHATESTENABLE,0,FALSE},{BlurStateKind::Render,D3DRS_ALPHABLENDENABLE,0,TRUE},
    {BlurStateKind::Render,D3DRS_SRCBLEND,0,D3DBLEND_SRCALPHA},{BlurStateKind::Render,D3DRS_DESTBLEND,0,D3DBLEND_INVSRCALPHA},
    {BlurStateKind::Render,D3DRS_BLENDOP,0,D3DBLENDOP_ADD},{BlurStateKind::Render,D3DRS_CULLMODE,0,D3DCULL_NONE},
    {BlurStateKind::Render,D3DRS_LIGHTING,0,FALSE},{BlurStateKind::Render,D3DRS_FOGENABLE,0,FALSE},
    {BlurStateKind::Render,D3DRS_STENCILENABLE,0,FALSE},{BlurStateKind::Render,D3DRS_CLIPPLANEENABLE,0,0},
    {BlurStateKind::Render,D3DRS_COLORWRITEENABLE,0,15},{BlurStateKind::Render,D3DRS_FILLMODE,0,D3DFILL_SOLID},
    {BlurStateKind::Render,D3DRS_CLIPPING,0,TRUE},{BlurStateKind::Render,D3DRS_DITHERENABLE,0,FALSE},
    {BlurStateKind::Render,D3DRS_SPECULARENABLE,0,FALSE},{BlurStateKind::Render,D3DRS_VERTEXBLEND,0,D3DVBF_DISABLE},
    {BlurStateKind::Render,D3DRS_INDEXEDVERTEXBLENDENABLE,0,FALSE},{BlurStateKind::Render,D3DRS_WRAP0,0,0},
    {BlurStateKind::Render,D3DRS_TEXTUREFACTOR,0,0},
    {BlurStateKind::Stage,D3DTSS_COLOROP,0,D3DTOP_SELECTARG1},{BlurStateKind::Stage,D3DTSS_COLORARG1,0,D3DTA_TEXTURE},
    {BlurStateKind::Stage,D3DTSS_ALPHAOP,0,D3DTOP_SELECTARG1},{BlurStateKind::Stage,D3DTSS_ALPHAARG1,0,D3DTA_TFACTOR},
    {BlurStateKind::Stage,D3DTSS_TEXCOORDINDEX,0,0},{BlurStateKind::Stage,D3DTSS_TEXTURETRANSFORMFLAGS,0,D3DTTFF_DISABLE},
    {BlurStateKind::Stage,D3DTSS_ADDRESSU,0,D3DTADDRESS_CLAMP},{BlurStateKind::Stage,D3DTSS_ADDRESSV,0,D3DTADDRESS_CLAMP},
    {BlurStateKind::Stage,D3DTSS_MAGFILTER,0,D3DTEXF_POINT},{BlurStateKind::Stage,D3DTSS_MINFILTER,0,D3DTEXF_POINT},
    {BlurStateKind::Stage,D3DTSS_MIPFILTER,0,D3DTEXF_NONE},{BlurStateKind::Stage,D3DTSS_RESULTARG,0,D3DTA_CURRENT},
    {BlurStateKind::Stage,D3DTSS_COLOROP,1,D3DTOP_DISABLE},{BlurStateKind::Stage,D3DTSS_ALPHAOP,1,D3DTOP_DISABLE},
    {BlurStateKind::VertexShader,0,0,D3DFVF_XYZRHW|D3DFVF_DIFFUSE|D3DFVF_TEX1},{BlurStateKind::PixelShader,0,0,0},
    {BlurStateKind::Texture,0,0,0},{BlurStateKind::Texture,0,1,0},{BlurStateKind::Render,D3DRS_SHADEMODE,0,D3DSHADE_GOURAUD},
}};
inline constexpr size_t kMotionBlurFactorOp=20,kMotionBlurTexture0Op=37;

struct MotionBlurVertex { float x,y,z,rhw; DWORD color; float u,v; };
struct MotionBlurStatus { const char* reason="not_attempted"; HRESULT hr=S_FALSE, restore_hr=S_FALSE; uint64_t blended=0; float weight=0.f; };

class PS2MotionBlur {
    struct Saved { DWORD scalar=0; IDirect3DBaseTexture8* texture=nullptr; };
    float blur_=0.f;
    std::array<Saved,kMotionBlurOps.size()> saved_{};
    uint64_t pending_=0;
    D3DVIEWPORT8 viewport_{};
    IDirect3DVertexBuffer8* stream_=nullptr; UINT stride_=0;
    bool viewport_pending_=false, stream_pending_=false, unsupported_=false, history_valid_=false;
    IDirect3DTexture8* history_=nullptr; IDirect3DSurface8* history_surface_=nullptr;
    D3DFORMAT format_=D3DFMT_UNKNOWN; UINT width_=0,height_=0,tex_w_=0,tex_h_=0;
    MotionBlurStatus status_{};
    template<class T> static void drop(T*& p) noexcept {if(p)p->Release();p=nullptr;}
    template<class T> struct Ref { T* value=nullptr; ~Ref(){drop(value);} };
    static UINT pow2(UINT v) noexcept {UINT r=1;while(r<v&&r<=0x40000000u)r<<=1;return r;}
    static bool same_surface(IDirect3DSurface8* a,IDirect3DSurface8* b) noexcept {
        if(!a||!b)return false;if(a==b)return true;Ref<IUnknown> x,y;
        return SUCCEEDED(a->QueryInterface(IID_IUnknown,reinterpret_cast<void**>(&x.value)))&&SUCCEEDED(b->QueryInterface(IID_IUnknown,reinterpret_cast<void**>(&y.value)))&&x.value&&x.value==y.value;
    }
    void release_saved() noexcept {for(auto& s:saved_){drop(s.texture);s={};}drop(stream_);}
    HRESULT write(IDirect3DDevice8& d,size_t i,DWORD scalar,IDirect3DBaseTexture8* texture) noexcept {
        const auto& op=kMotionBlurOps[i];pending_|=uint64_t(1)<<i;
        switch(op.kind){
        case BlurStateKind::Render:return d.SetRenderState(static_cast<D3DRENDERSTATETYPE>(op.key),scalar);
        case BlurStateKind::Stage:return d.SetTextureStageState(op.stage,static_cast<D3DTEXTURESTAGESTATETYPE>(op.key),scalar);
        case BlurStateKind::VertexShader:return d.SetVertexShader(scalar);
        case BlurStateKind::PixelShader:return d.SetPixelShader(scalar);
        case BlurStateKind::Texture:return d.SetTexture(op.stage,texture);
        }
        return E_INVALIDARG;
    }
    HRESULT capture(IDirect3DDevice8& d) noexcept {
        release_saved();HRESULT hr=S_OK;
        for(size_t i=0;i<kMotionBlurOps.size()&&SUCCEEDED(hr);++i){
            const auto& op=kMotionBlurOps[i];auto& v=saved_[i];
            switch(op.kind){
            case BlurStateKind::Render:hr=d.GetRenderState(static_cast<D3DRENDERSTATETYPE>(op.key),&v.scalar);break;
            case BlurStateKind::Stage:hr=d.GetTextureStageState(op.stage,static_cast<D3DTEXTURESTAGESTATETYPE>(op.key),&v.scalar);break;
            case BlurStateKind::VertexShader:hr=d.GetVertexShader(&v.scalar);break;
            case BlurStateKind::PixelShader:hr=d.GetPixelShader(&v.scalar);break;
            case BlurStateKind::Texture:hr=d.GetTexture(op.stage,&v.texture);break;
            }
        }
        if(SUCCEEDED(hr))hr=d.GetViewport(&viewport_);
        if(SUCCEEDED(hr))hr=d.GetStreamSource(0,&stream_,&stride_);
        if(FAILED(hr))release_saved();
        return hr;
    }
    HRESULT fail(const char* reason,HRESULT hr,bool permanent=false) noexcept {status_.reason=reason;status_.hr=hr;if(permanent)unsupported_=true;return hr;}
    HRESULT allocate(IDirect3DDevice8& d,const D3DSURFACE_DESC& desc,const D3DCAPS8& caps) noexcept {
        UINT w=desc.Width,h=desc.Height;
        if(caps.TextureCaps&D3DPTEXTURECAPS_POW2){w=pow2(w);h=pow2(h);}
        if(caps.TextureCaps&D3DPTEXTURECAPS_SQUAREONLY)w=h=w>h?w:h;
        if(history_&&format_==desc.Format&&width_==desc.Width&&height_==desc.Height&&tex_w_==w&&tex_h_==h)return S_OK;
        release_resources();
        if(!w||!h||w>caps.MaxTextureWidth||h>caps.MaxTextureHeight||uint64_t(w)*h*4>64ull*1024*1024)return D3DERR_NOTAVAILABLE;
        if(desc.MultiSampleType!=D3DMULTISAMPLE_NONE&&(w!=desc.Width||h!=desc.Height))return D3DERR_NOTAVAILABLE;
        HRESULT hr=d.CreateTexture(w,h,1,D3DUSAGE_RENDERTARGET,desc.Format,D3DPOOL_DEFAULT,&history_);
        if(SUCCEEDED(hr)&&!history_)hr=E_FAIL;
        if(SUCCEEDED(hr))hr=history_->GetSurfaceLevel(0,&history_surface_);
        if(SUCCEEDED(hr)&&!history_surface_)hr=E_FAIL;
        if(FAILED(hr)){release_resources();return hr;}
        format_=desc.Format;width_=desc.Width;height_=desc.Height;tex_w_=w;tex_h_=h;return S_OK;
    }
public:
    PS2MotionBlur()=default;
    ~PS2MotionBlur(){release_saved();release_resources();}
    PS2MotionBlur(const PS2MotionBlur&)=delete;
    PS2MotionBlur& operator=(const PS2MotionBlur&)=delete;
    void configure(float blur) noexcept {blur_=blur;}
    float blur() const noexcept {return blur_;}
    bool enabled() const noexcept {return blur_>0.f;}
    bool pending() const noexcept {return pending_||viewport_pending_||stream_pending_;}
    const MotionBlurStatus& status() const noexcept {return status_;}
    void release_resources() noexcept {drop(history_surface_);drop(history_);history_valid_=false;format_=D3DFMT_UNKNOWN;width_=height_=tex_w_=tex_h_=0;}
    void before_reset() noexcept {release_resources();unsupported_=false;}
    // Outside a race the history is dropped, so the first race frame shows no trail.
    void interrupt() noexcept {history_valid_=false;}
    HRESULT restore(IDirect3DDevice8& d) noexcept {
        HRESULT result=S_OK;const auto keep=[&](HRESULT hr){if(FAILED(hr)&&SUCCEEDED(result))result=hr;};
        if(viewport_pending_){const HRESULT hr=d.SetViewport(&viewport_);if(SUCCEEDED(hr))viewport_pending_=false;else keep(hr);}
        if(stream_pending_){const HRESULT hr=d.SetStreamSource(0,stream_,stride_);if(SUCCEEDED(hr))stream_pending_=false;else keep(hr);}
        for(size_t i=kMotionBlurOps.size();i-- >0;){
            const uint64_t bit=uint64_t(1)<<i;if(!(pending_&bit))continue;
            const HRESULT hr=write(d,i,saved_[i].scalar,saved_[i].texture);
            if(SUCCEEDED(hr))pending_&=~bit;else keep(hr);
        }
        if(!pending())release_saved();
        status_.restore_hr=result;return result;
    }
    // Last pass before Present: blend the previous shown frame over this one, then keep this one.
    // dt = seconds since the previous Present; a stall longer than 0.1 s restarts the history.
    HRESULT apply(IDirect3DDevice8& d,bool scene_active,bool recording,float dt=1.f/kPS2FrameRate) noexcept {
        if(!enabled())return S_FALSE;
        if(dt>kMotionBlurMaxFrameTime)history_valid_=false;
        if(unsupported_)return status_.hr;
        if(pending())return fail("native_restore_pending",D3DERR_INVALIDCALL);
        if(scene_active||recording){history_valid_=false;return fail(scene_active?"scene_still_active":"stateblock_recording",S_FALSE);}
        Ref<IDirect3DSurface8> current,back;
        HRESULT hr=d.GetRenderTarget(&current.value);if(FAILED(hr))return fail("get_render_target_failed",hr);
        hr=d.GetBackBuffer(0,D3DBACKBUFFER_TYPE_MONO,&back.value);if(FAILED(hr))return fail("get_backbuffer_failed",hr);
        if(!same_surface(current.value,back.value)){history_valid_=false;return fail("not_main_backbuffer",S_FALSE);}
        D3DSURFACE_DESC desc{};hr=back.value->GetDesc(&desc);if(FAILED(hr))return fail("surface_description_failed",hr);
        if(desc.Format!=D3DFMT_X8R8G8B8&&desc.Format!=D3DFMT_A8R8G8B8)return fail("source_format_unsupported",D3DERR_NOTAVAILABLE,true);
        D3DCAPS8 caps{};hr=d.GetDeviceCaps(&caps);if(FAILED(hr))return fail("device_caps_failed",hr);
        if(!(caps.TextureOpCaps&D3DTEXOPCAPS_SELECTARG1)||!(caps.SrcBlendCaps&D3DPBLENDCAPS_SRCALPHA)||!(caps.DestBlendCaps&D3DPBLENDCAPS_INVSRCALPHA)||
           !(caps.TextureFilterCaps&D3DPTFILTERCAPS_MAGFPOINT)||!(caps.TextureFilterCaps&D3DPTFILTERCAPS_MINFPOINT))return fail("fixed_function_caps_unsupported",D3DERR_NOTAVAILABLE,true);
        const bool resized=!history_||width_!=desc.Width||height_!=desc.Height||format_!=desc.Format;
        hr=allocate(d,desc,caps);if(FAILED(hr))return fail("history_allocation_failed",hr,hr==D3DERR_NOTAVAILABLE);
        if(resized)history_valid_=false;
        HRESULT blended=S_FALSE;
        if(history_valid_){
            hr=capture(d);if(FAILED(hr))return fail("native_state_capture_failed",hr);
            hr=d.BeginScene();
            if(FAILED(hr)){restore(d);return fail("begin_scene_failed",hr);}
            viewport_pending_=true;const D3DVIEWPORT8 full{0,0,width_,height_,0.f,1.f};hr=d.SetViewport(&full);
            for(size_t i=0;i<kMotionBlurOps.size()&&SUCCEEDED(hr);++i)
                hr=write(d,i,i==kMotionBlurFactorOp?motion_blur_factor(status_.weight=motion_blur_frame_weight(blur_,dt)):kMotionBlurOps[i].value,i==kMotionBlurTexture0Op?history_:nullptr);
            if(SUCCEEDED(hr)){
                const float u=float(width_)/tex_w_,v=float(height_)/tex_h_,r=float(width_)-.5f,b=float(height_)-.5f;const DWORD c=0xffffffffu;
                const MotionBlurVertex q[4]={{-.5f,-.5f,0.f,1.f,c,0.f,0.f},{r,-.5f,0.f,1.f,c,u,0.f},{-.5f,b,0.f,1.f,c,0.f,v},{r,b,0.f,1.f,c,u,v}};
                stream_pending_=true;hr=d.DrawPrimitiveUP(D3DPT_TRIANGLESTRIP,2,q,sizeof(MotionBlurVertex));
            }
            const HRESULT ended=d.EndScene();
            const HRESULT restored=restore(d);
            if(FAILED(restored)){history_valid_=false;return fail("native_state_restore_failed",restored);}
            if(FAILED(hr)||FAILED(ended)){history_valid_=false;return fail(FAILED(hr)?"blend_draw_failed":"end_scene_failed",FAILED(hr)?hr:ended);}
            blended=S_OK;
        }
        const bool multisampled=desc.MultiSampleType!=D3DMULTISAMPLE_NONE;
        const RECT rect{0,0,LONG(desc.Width),LONG(desc.Height)};const POINT origin{0,0};
        hr=d.CopyRects(back.value,multisampled?nullptr:&rect,multisampled?0:1,history_surface_,multisampled?nullptr:&origin);
        if(FAILED(hr)){history_valid_=false;return fail(multisampled?"msaa_resolve_copy_failed":"copyrects_failed",hr,multisampled);}
        history_valid_=true;
        if(blended==S_OK){++status_.blended;status_.reason="blended";status_.hr=S_OK;return S_OK;}
        status_.reason="history_primed";status_.hr=S_FALSE;return S_FALSE;
    }
    // ReflectionDebug=2: show a texture (the PC env target) unblended at dst, point sampled, before Present.
    HRESULT overlay(IDirect3DDevice8& d,IDirect3DTexture8* texture,UINT width,UINT height,float x,float y,float size,bool scene_active,bool recording) noexcept {
        if(!texture||!width||!height)return S_FALSE;
        if(pending()||scene_active||recording)return S_FALSE;
        HRESULT hr=capture(d);if(FAILED(hr))return hr;
        hr=d.BeginScene();if(FAILED(hr)){restore(d);return hr;}
        viewport_pending_=true;const D3DVIEWPORT8 full{0,0,width,height,0.f,1.f};hr=d.SetViewport(&full);
        for(size_t i=0;i<kMotionBlurOps.size()&&SUCCEEDED(hr);++i){
            DWORD value=kMotionBlurOps[i].value;
            if(kMotionBlurOps[i].kind==BlurStateKind::Render&&kMotionBlurOps[i].key==D3DRS_ALPHABLENDENABLE)value=FALSE;
            hr=write(d,i,value,i==kMotionBlurTexture0Op?texture:nullptr);
        }
        if(SUCCEEDED(hr)){
            const float l=x-.5f,t=y-.5f,r=x+size-.5f,b=y+size-.5f;const DWORD c=0xffffffffu;
            const MotionBlurVertex q[4]={{l,t,0.f,1.f,c,0.f,0.f},{r,t,0.f,1.f,c,1.f,0.f},{l,b,0.f,1.f,c,0.f,1.f},{r,b,0.f,1.f,c,1.f,1.f}};
            stream_pending_=true;hr=d.DrawPrimitiveUP(D3DPT_TRIANGLESTRIP,2,q,sizeof(MotionBlurVertex));
        }
        const HRESULT ended=d.EndScene();const HRESULT restored=restore(d);
        return FAILED(restored)?restored:FAILED(hr)?hr:ended;
    }
};

}  // namespace gfx2::ps2port
