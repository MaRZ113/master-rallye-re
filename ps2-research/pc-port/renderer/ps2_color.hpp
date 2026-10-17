#pragma once
// Opt-in PS2Color (default 0): a per-channel tone curve applied to the finished frame just before
// Present, fitted to paired PC/PS2 screenshots (docs/ps2-color1). It is an approximation of the
// PS2 picture, not a recovered PS2 material/light contract, and therefore stays off by default.
//
//   y = (1 - k) * x + k * x^2   per channel, k in [0,1]
//
// Fixed-function only, no shaders: the backbuffer is copied to a private texture, then
//   pass A: dest *= (1 - k)            SRCBLEND ZERO, DESTBLEND SRCCOLOR, colour = TFACTOR
//   pass B: dest += k * copy * copy    SRCBLEND ONE,  DESTBLEND ONE,  stage0 tex*tex, stage1 *TFACTOR
// Every native state touched is captured first and restored in reverse order before Present.
#include "sdk.hpp"
#include <array>
#include <cstdint>
#include <cwchar>
#include <string>
#include "ps2_config.hpp"

namespace gfx2::ps2port {

// Six PC/PS2 pairs, 20 matched regions (docs/ps2-color1/pairs.json, fit_tone_curve.py).
inline constexpr std::array<float,3> kPS2ColorDefaultCurve{0.426f,0.384f,0.364f};

struct PS2ColorConfig {
    bool enabled=false;
    std::array<float,3> k=kPS2ColorDefaultCurve;
};

inline bool parse_ps2_color_curve(const wchar_t* text,std::array<float,3>& out) noexcept {
    if(!text)return false;
    float r=0,g=0,b=0;wchar_t tail=0;
    if(swscanf_s(text,L" %f , %f , %f %lc",&r,&g,&b,&tail,1)!=3)return false;
    for(float v:{r,g,b})if(!(v>=0.f&&v<=1.f))return false;
    out={r,g,b};return true;
}

inline PS2ColorConfig read_ps2_color_config(const wchar_t* ini) noexcept {
    PS2ColorConfig config;
    config.enabled=config::read_int(L"PS2Color",0,ini)==1;
    wchar_t text[64]{};
    config::read_string(L"PS2ColorCurve",L"",text,64,ini);
    if(text[0]&&!parse_ps2_color_curve(text,config.k))config.k=kPS2ColorDefaultCurve;
    return config;
}

inline DWORD ps2_color_factor(const std::array<float,3>& v) noexcept {
    const auto byte=[](float x)->DWORD{const float c=x<0.f?0.f:x>1.f?1.f:x;return static_cast<DWORD>(c*255.f+.5f);};
    return 0xff000000u|(byte(v[0])<<16)|(byte(v[1])<<8)|byte(v[2]);
}

enum class PS2ColorStateKind : uint8_t { Render, Stage, VertexShader, PixelShader, Texture };
struct PS2ColorStateOp { PS2ColorStateKind kind; DWORD key, stage, pass_a, pass_b; };
// TEXTUREFACTOR is written per pass from the configured curve (kFactorOp).
inline constexpr std::array<PS2ColorStateOp,45> kPS2ColorOps={{
    {PS2ColorStateKind::Render,D3DRS_ZENABLE,0,D3DZB_FALSE,D3DZB_FALSE},
    {PS2ColorStateKind::Render,D3DRS_ZWRITEENABLE,0,FALSE,FALSE},
    {PS2ColorStateKind::Render,D3DRS_ALPHATESTENABLE,0,FALSE,FALSE},
    {PS2ColorStateKind::Render,D3DRS_ALPHABLENDENABLE,0,TRUE,TRUE},
    {PS2ColorStateKind::Render,D3DRS_SRCBLEND,0,D3DBLEND_ZERO,D3DBLEND_ONE},
    {PS2ColorStateKind::Render,D3DRS_DESTBLEND,0,D3DBLEND_SRCCOLOR,D3DBLEND_ONE},
    {PS2ColorStateKind::Render,D3DRS_BLENDOP,0,D3DBLENDOP_ADD,D3DBLENDOP_ADD},
    {PS2ColorStateKind::Render,D3DRS_CULLMODE,0,D3DCULL_NONE,D3DCULL_NONE},
    {PS2ColorStateKind::Render,D3DRS_LIGHTING,0,FALSE,FALSE},
    {PS2ColorStateKind::Render,D3DRS_FOGENABLE,0,FALSE,FALSE},
    {PS2ColorStateKind::Render,D3DRS_STENCILENABLE,0,FALSE,FALSE},
    {PS2ColorStateKind::Render,D3DRS_CLIPPLANEENABLE,0,0,0},
    {PS2ColorStateKind::Render,D3DRS_COLORWRITEENABLE,0,15,15},
    {PS2ColorStateKind::Render,D3DRS_FILLMODE,0,D3DFILL_SOLID,D3DFILL_SOLID},
    {PS2ColorStateKind::Render,D3DRS_CLIPPING,0,TRUE,TRUE},
    {PS2ColorStateKind::Render,D3DRS_DITHERENABLE,0,FALSE,FALSE},
    {PS2ColorStateKind::Render,D3DRS_SPECULARENABLE,0,FALSE,FALSE},
    {PS2ColorStateKind::Render,D3DRS_VERTEXBLEND,0,D3DVBF_DISABLE,D3DVBF_DISABLE},
    {PS2ColorStateKind::Render,D3DRS_INDEXEDVERTEXBLENDENABLE,0,FALSE,FALSE},
    {PS2ColorStateKind::Render,D3DRS_WRAP0,0,0,0},
    {PS2ColorStateKind::Render,D3DRS_TEXTUREFACTOR,0,0,0},
    {PS2ColorStateKind::Stage,D3DTSS_COLOROP,0,D3DTOP_SELECTARG2,D3DTOP_MODULATE},
    {PS2ColorStateKind::Stage,D3DTSS_COLORARG1,0,D3DTA_TEXTURE,D3DTA_TEXTURE},
    {PS2ColorStateKind::Stage,D3DTSS_COLORARG2,0,D3DTA_TFACTOR,D3DTA_TEXTURE},
    {PS2ColorStateKind::Stage,D3DTSS_ALPHAOP,0,D3DTOP_SELECTARG2,D3DTOP_SELECTARG2},
    {PS2ColorStateKind::Stage,D3DTSS_ALPHAARG2,0,D3DTA_DIFFUSE,D3DTA_DIFFUSE},
    {PS2ColorStateKind::Stage,D3DTSS_TEXCOORDINDEX,0,0,0},
    {PS2ColorStateKind::Stage,D3DTSS_TEXTURETRANSFORMFLAGS,0,D3DTTFF_DISABLE,D3DTTFF_DISABLE},
    {PS2ColorStateKind::Stage,D3DTSS_ADDRESSU,0,D3DTADDRESS_CLAMP,D3DTADDRESS_CLAMP},
    {PS2ColorStateKind::Stage,D3DTSS_ADDRESSV,0,D3DTADDRESS_CLAMP,D3DTADDRESS_CLAMP},
    {PS2ColorStateKind::Stage,D3DTSS_MAGFILTER,0,D3DTEXF_POINT,D3DTEXF_POINT},
    {PS2ColorStateKind::Stage,D3DTSS_MINFILTER,0,D3DTEXF_POINT,D3DTEXF_POINT},
    {PS2ColorStateKind::Stage,D3DTSS_MIPFILTER,0,D3DTEXF_NONE,D3DTEXF_NONE},
    {PS2ColorStateKind::Stage,D3DTSS_RESULTARG,0,D3DTA_CURRENT,D3DTA_CURRENT},
    {PS2ColorStateKind::Stage,D3DTSS_COLOROP,1,D3DTOP_DISABLE,D3DTOP_MODULATE},
    {PS2ColorStateKind::Stage,D3DTSS_COLORARG1,1,D3DTA_CURRENT,D3DTA_CURRENT},
    {PS2ColorStateKind::Stage,D3DTSS_COLORARG2,1,D3DTA_TFACTOR,D3DTA_TFACTOR},
    {PS2ColorStateKind::Stage,D3DTSS_ALPHAOP,1,D3DTOP_DISABLE,D3DTOP_SELECTARG1},
    {PS2ColorStateKind::Stage,D3DTSS_ALPHAARG1,1,D3DTA_CURRENT,D3DTA_CURRENT},
    {PS2ColorStateKind::Stage,D3DTSS_COLOROP,2,D3DTOP_DISABLE,D3DTOP_DISABLE},
    {PS2ColorStateKind::Stage,D3DTSS_ALPHAOP,2,D3DTOP_DISABLE,D3DTOP_DISABLE},
    {PS2ColorStateKind::VertexShader,0,0,D3DFVF_XYZRHW|D3DFVF_DIFFUSE|D3DFVF_TEX1,D3DFVF_XYZRHW|D3DFVF_DIFFUSE|D3DFVF_TEX1},
    {PS2ColorStateKind::PixelShader,0,0,0,0},
    {PS2ColorStateKind::Texture,0,0,0,0},
    {PS2ColorStateKind::Texture,0,1,0,0},
}};
inline constexpr size_t kPS2ColorFactorOp=20;
inline constexpr size_t kPS2ColorStage0TextureOp=43;

struct PS2ColorVertex { float x,y,z,rhw; DWORD color; float u,v; };

struct PS2ColorStatus {
    const char* reason="not_attempted";
    HRESULT hr=S_FALSE, restore_hr=S_FALSE;
    uint64_t frames=0;
};

class PS2ColorGrade {
    struct Saved { DWORD scalar=0; IDirect3DBaseTexture8* texture=nullptr; };
    PS2ColorConfig config_{};
    std::array<Saved,kPS2ColorOps.size()> saved_{};
    uint64_t pending_=0;
    D3DVIEWPORT8 viewport_{};
    IDirect3DVertexBuffer8* stream_=nullptr;
    UINT stride_=0;
    bool captured_=false, viewport_pending_=false, stream_pending_=false;
    IDirect3DTexture8* copy_texture_=nullptr;
    IDirect3DSurface8* copy_surface_=nullptr;
    D3DFORMAT copy_format_=D3DFMT_UNKNOWN;
    UINT copy_width_=0, copy_height_=0, source_width_=0, source_height_=0;
    bool unsupported_=false;
    PS2ColorStatus status_{};

    template<class T> static void drop(T*& p) noexcept {if(p)p->Release();p=nullptr;}
    template<class T> struct Ref { T* value=nullptr; ~Ref(){drop(value);} };
    static UINT pow2(UINT v) noexcept {UINT r=1;while(r<v&&r<=0x40000000u)r<<=1;return r;}
    static bool same_surface(IDirect3DSurface8* a,IDirect3DSurface8* b) noexcept {
        if(!a||!b)return false;if(a==b)return true;
        Ref<IUnknown> ia,ib;
        return SUCCEEDED(a->QueryInterface(IID_IUnknown,reinterpret_cast<void**>(&ia.value)))&&
            SUCCEEDED(b->QueryInterface(IID_IUnknown,reinterpret_cast<void**>(&ib.value)))&&ia.value&&ia.value==ib.value;
    }
    DWORD value_for(size_t i,bool pass_b) const noexcept {
        if(i==kPS2ColorFactorOp){
            if(pass_b)return ps2_color_factor(config_.k);
            return ps2_color_factor({1.f-config_.k[0],1.f-config_.k[1],1.f-config_.k[2]});
        }
        return pass_b?kPS2ColorOps[i].pass_b:kPS2ColorOps[i].pass_a;
    }
    HRESULT write(IDirect3DDevice8& d,size_t i,DWORD scalar,IDirect3DBaseTexture8* texture) noexcept {
        const auto& op=kPS2ColorOps[i];pending_|=uint64_t(1)<<i;
        switch(op.kind){
        case PS2ColorStateKind::Render:return d.SetRenderState(static_cast<D3DRENDERSTATETYPE>(op.key),scalar);
        case PS2ColorStateKind::Stage:return d.SetTextureStageState(op.stage,static_cast<D3DTEXTURESTAGESTATETYPE>(op.key),scalar);
        case PS2ColorStateKind::VertexShader:return d.SetVertexShader(scalar);
        case PS2ColorStateKind::PixelShader:return d.SetPixelShader(scalar);
        case PS2ColorStateKind::Texture:return d.SetTexture(op.stage,texture);
        }
        return E_INVALIDARG;
    }
    void release_saved() noexcept {for(auto& s:saved_){drop(s.texture);s={};}drop(stream_);captured_=false;}
    HRESULT capture(IDirect3DDevice8& d) noexcept {
        release_saved();HRESULT hr=S_OK;
        for(size_t i=0;i<kPS2ColorOps.size()&&SUCCEEDED(hr);++i){
            const auto& op=kPS2ColorOps[i];auto& v=saved_[i];
            switch(op.kind){
            case PS2ColorStateKind::Render:hr=d.GetRenderState(static_cast<D3DRENDERSTATETYPE>(op.key),&v.scalar);break;
            case PS2ColorStateKind::Stage:hr=d.GetTextureStageState(op.stage,static_cast<D3DTEXTURESTAGESTATETYPE>(op.key),&v.scalar);break;
            case PS2ColorStateKind::VertexShader:hr=d.GetVertexShader(&v.scalar);break;
            case PS2ColorStateKind::PixelShader:hr=d.GetPixelShader(&v.scalar);break;
            case PS2ColorStateKind::Texture:hr=d.GetTexture(op.stage,&v.texture);break;
            }
        }
        if(SUCCEEDED(hr))hr=d.GetViewport(&viewport_);
        if(SUCCEEDED(hr))hr=d.GetStreamSource(0,&stream_,&stride_);
        if(FAILED(hr)){release_saved();return hr;}
        captured_=true;return S_OK;
    }
    HRESULT set_pass(IDirect3DDevice8& d,bool pass_b) noexcept {
        for(size_t i=0;i<kPS2ColorOps.size();++i){
            if(pass_b&&i!=kPS2ColorFactorOp&&kPS2ColorOps[i].pass_a==kPS2ColorOps[i].pass_b&&kPS2ColorOps[i].kind!=PS2ColorStateKind::Texture)continue;
            if(pass_b&&kPS2ColorOps[i].kind==PS2ColorStateKind::Texture)continue;
            IDirect3DBaseTexture8* texture=i==kPS2ColorStage0TextureOp?copy_texture_:nullptr;
            const HRESULT hr=write(d,i,value_for(i,pass_b),texture);if(FAILED(hr))return hr;
        }
        return S_OK;
    }
    HRESULT draw(IDirect3DDevice8& d) noexcept {
        const float u=float(source_width_)/copy_width_,v=float(source_height_)/copy_height_;
        const float r=float(source_width_)-.5f,b=float(source_height_)-.5f;
        const PS2ColorVertex quad[4]={{-.5f,-.5f,0.f,1.f,0xffffffffu,0.f,0.f},{r,-.5f,0.f,1.f,0xffffffffu,u,0.f},
                                      {-.5f,b,0.f,1.f,0xffffffffu,0.f,v},{r,b,0.f,1.f,0xffffffffu,u,v}};
        stream_pending_=true; // DrawPrimitiveUP clears stream 0 even when it fails.
        return d.DrawPrimitiveUP(D3DPT_TRIANGLESTRIP,2,quad,sizeof(PS2ColorVertex));
    }
    HRESULT allocate(IDirect3DDevice8& d,const D3DSURFACE_DESC& desc,UINT w,UINT h) noexcept {
        if(copy_texture_&&copy_format_==desc.Format&&copy_width_==w&&copy_height_==h)return S_OK;
        release_resources();
        HRESULT hr=d.CreateTexture(w,h,1,D3DUSAGE_RENDERTARGET,desc.Format,D3DPOOL_DEFAULT,&copy_texture_);
        if(SUCCEEDED(hr)&&!copy_texture_)hr=E_FAIL;
        if(SUCCEEDED(hr))hr=copy_texture_->GetSurfaceLevel(0,&copy_surface_);
        if(SUCCEEDED(hr)&&!copy_surface_)hr=E_FAIL;
        if(FAILED(hr)){release_resources();return hr;}
        copy_format_=desc.Format;copy_width_=w;copy_height_=h;return S_OK;
    }
    HRESULT fail(const char* reason,HRESULT hr,bool permanent=false) noexcept {
        status_.reason=reason;status_.hr=hr;if(permanent)unsupported_=true;return hr;
    }
public:
    PS2ColorGrade()=default;
    explicit PS2ColorGrade(const PS2ColorConfig& config) noexcept:config_(config){}
    ~PS2ColorGrade(){release_saved();release_resources();}
    PS2ColorGrade(const PS2ColorGrade&)=delete;
    PS2ColorGrade& operator=(const PS2ColorGrade&)=delete;
    void configure(const PS2ColorConfig& config) noexcept {config_=config;}
    const PS2ColorConfig& config() const noexcept {return config_;}
    bool enabled() const noexcept {return config_.enabled;}
    bool pending() const noexcept {return pending_||viewport_pending_||stream_pending_;}
    const PS2ColorStatus& status() const noexcept {return status_;}
    void release_resources() noexcept {drop(copy_surface_);drop(copy_texture_);copy_format_=D3DFMT_UNKNOWN;copy_width_=copy_height_=0;}
    // DEFAULT-pool copy texture must go before Reset; it is recreated on the next frame.
    void before_reset() noexcept {release_resources();unsupported_=false;}

    HRESULT restore(IDirect3DDevice8& d) noexcept {
        HRESULT result=S_OK;const auto keep=[&](HRESULT hr){if(FAILED(hr)&&SUCCEEDED(result))result=hr;};
        if(viewport_pending_){const HRESULT hr=d.SetViewport(&viewport_);if(SUCCEEDED(hr))viewport_pending_=false;else keep(hr);}
        if(stream_pending_){const HRESULT hr=d.SetStreamSource(0,stream_,stride_);if(SUCCEEDED(hr))stream_pending_=false;else keep(hr);}
        for(size_t i=kPS2ColorOps.size();i-- >0;){
            const uint64_t bit=uint64_t(1)<<i;if(!(pending_&bit))continue;
            const auto& op=kPS2ColorOps[i];HRESULT hr=E_INVALIDARG;
            switch(op.kind){
            case PS2ColorStateKind::Render:hr=d.SetRenderState(static_cast<D3DRENDERSTATETYPE>(op.key),saved_[i].scalar);break;
            case PS2ColorStateKind::Stage:hr=d.SetTextureStageState(op.stage,static_cast<D3DTEXTURESTAGESTATETYPE>(op.key),saved_[i].scalar);break;
            case PS2ColorStateKind::VertexShader:hr=d.SetVertexShader(saved_[i].scalar);break;
            case PS2ColorStateKind::PixelShader:hr=d.SetPixelShader(saved_[i].scalar);break;
            case PS2ColorStateKind::Texture:hr=d.SetTexture(op.stage,saved_[i].texture);break;
            }
            if(SUCCEEDED(hr))pending_&=~bit;else keep(hr);
        }
        if(!pending())release_saved();
        status_.restore_hr=result;return result;
    }

    // Called once per Present with the scene closed. Draws nothing unless PS2Color=1.
    HRESULT apply(IDirect3DDevice8& d,bool scene_active,bool stateblock_recording) noexcept {
        if(!config_.enabled)return S_FALSE;
        if(unsupported_)return status_.hr;
        if(pending())return fail("native_restore_pending",D3DERR_INVALIDCALL);
        if(scene_active||stateblock_recording)return fail(scene_active?"scene_still_active":"stateblock_recording",S_FALSE);
        Ref<IDirect3DSurface8> current,back;
        HRESULT hr=d.GetRenderTarget(&current.value);if(FAILED(hr))return fail("get_render_target_failed",hr);
        hr=d.GetBackBuffer(0,D3DBACKBUFFER_TYPE_MONO,&back.value);if(FAILED(hr))return fail("get_backbuffer_failed",hr);
        if(!same_surface(current.value,back.value))return fail("not_main_backbuffer",S_FALSE);
        D3DSURFACE_DESC desc{};hr=back.value->GetDesc(&desc);if(FAILED(hr))return fail("surface_description_failed",hr);
        if(desc.Format!=D3DFMT_X8R8G8B8&&desc.Format!=D3DFMT_A8R8G8B8)return fail("source_format_unsupported",D3DERR_NOTAVAILABLE,true);
        D3DCAPS8 caps{};hr=d.GetDeviceCaps(&caps);if(FAILED(hr))return fail("device_caps_failed",hr);
        const DWORD ops=D3DTEXOPCAPS_MODULATE|D3DTEXOPCAPS_SELECTARG1|D3DTEXOPCAPS_SELECTARG2;
        if((caps.TextureOpCaps&ops)!=ops||caps.MaxTextureBlendStages<2||!(caps.SrcBlendCaps&D3DPBLENDCAPS_ZERO)||!(caps.SrcBlendCaps&D3DPBLENDCAPS_ONE)||
           !(caps.DestBlendCaps&D3DPBLENDCAPS_SRCCOLOR)||!(caps.DestBlendCaps&D3DPBLENDCAPS_ONE)||!(caps.TextureFilterCaps&D3DPTFILTERCAPS_MAGFPOINT)||
           !(caps.TextureFilterCaps&D3DPTFILTERCAPS_MINFPOINT))return fail("fixed_function_caps_unsupported",D3DERR_NOTAVAILABLE,true);
        UINT w=desc.Width,h=desc.Height;
        if(caps.TextureCaps&D3DPTEXTURECAPS_POW2){w=pow2(w);h=pow2(h);}
        if(caps.TextureCaps&D3DPTEXTURECAPS_SQUAREONLY)w=h=w>h?w:h;
        const bool multisampled=desc.MultiSampleType!=D3DMULTISAMPLE_NONE;
        if(!w||!h||w>caps.MaxTextureWidth||h>caps.MaxTextureHeight||uint64_t(w)*h*4>64ull*1024*1024||
           (multisampled&&(w!=desc.Width||h!=desc.Height)))return fail("copy_texture_unsupported",D3DERR_NOTAVAILABLE,true);
        hr=allocate(d,desc,w,h);if(FAILED(hr))return fail("copy_texture_allocation_failed",hr);
        source_width_=desc.Width;source_height_=desc.Height;
        const RECT rect{0,0,LONG(desc.Width),LONG(desc.Height)};const POINT origin{0,0};
        hr=d.CopyRects(back.value,multisampled?nullptr:&rect,multisampled?0:1,copy_surface_,multisampled?nullptr:&origin);
        if(FAILED(hr))return fail(multisampled?"msaa_resolve_copy_failed":"copyrects_failed",hr,multisampled);
        hr=capture(d);if(FAILED(hr))return fail("native_state_capture_failed",hr);
        hr=d.BeginScene();
        if(FAILED(hr)){restore(d);return fail("begin_scene_failed",hr);}
        viewport_pending_=true;
        const D3DVIEWPORT8 full{0,0,desc.Width,desc.Height,0.f,1.f};
        hr=d.SetViewport(&full);
        if(SUCCEEDED(hr))hr=set_pass(d,false);
        if(SUCCEEDED(hr))hr=draw(d);
        if(SUCCEEDED(hr))hr=set_pass(d,true);
        if(SUCCEEDED(hr))hr=draw(d);
        const HRESULT ended=d.EndScene();
        const HRESULT restored=restore(d);
        if(FAILED(restored))return fail("native_state_restore_failed",restored);
        if(FAILED(hr))return fail("private_draw_failed",hr);
        if(FAILED(ended))return fail("end_scene_failed",ended);
        ++status_.frames;status_.reason="graded";status_.hr=S_OK;return S_OK;
    }
};

}  // namespace gfx2::ps2port
