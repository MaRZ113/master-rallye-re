#pragma once
// Opt-in PS2Output (default 0): the PS2 display path applied to the finished frame before Present.
//
// PS2 (ps2-research/output1/findings.md, EE 2f4400/2f01c8/2f5528): the scene is drawn into a 640x512
// buffer and every frame a bilinear SPRITE copies it into a 512x256 field buffer; even and odd frames
// alternate a half display-line offset (XYOFFSET +8/16 = one source row). Woven, each output line is
// the average of two adjacent source rows and each column a 640->512 bilinear resample.
// PC equivalent without interlace flicker, fixed-function only:
//   backbuffer -> (W/2 x H/2 when larger than 1280x1024) -> 640x512 -> 512x512 (+0.5 source row) -> backbuffer
// The whole frame is filtered, HUD included, as on PS2 (HUD is drawn into the same buffer there).
#include "reflection_capture.hpp"
#include "ps2_config.hpp"
#include <array>

namespace gfx2::ps2port {

inline constexpr UINT kPS2DrawWidth=640,kPS2DrawHeight=512,kPS2FieldWidth=512,kPS2FieldLines=512;

struct PS2OutputQuad { float u0,v0,u1,v1; };

// Texture coordinates of one pass: source area srcW x srcH inside a texW x texH texture, sampled
// pixel-centre to pixel-centre; `row_offset` shifts the sample by that many source rows.
inline PS2OutputQuad ps2_output_quad(UINT srcW,UINT srcH,UINT texW,UINT texH,float row_offset=0.f) noexcept {
    const float dv=row_offset/float(texH);
    return {0.f,dv,float(srcW)/float(texW),float(srcH)/float(texH)+dv};
}

inline std::array<ReflectionCaptureVertex,4> ps2_output_vertices(const PS2OutputQuad& q,UINT w,UINT h) noexcept {
    const float r=float(w)-.5f,b=float(h)-.5f;const DWORD c=0xffffffffu;
    return {{{-.5f,-.5f,0.f,1.f,c,q.u0,q.v0},{r,-.5f,0.f,1.f,c,q.u1,q.v0},{-.5f,b,0.f,1.f,c,q.u0,q.v1},{r,b,0.f,1.f,c,q.u1,q.v1}}};
}

struct PS2OutputStatus { const char* reason="not_attempted"; HRESULT hr=S_FALSE, restore_hr=S_FALSE; uint64_t frames=0; UINT draws=0; };

class PS2OutputFilter {
    struct Target { IDirect3DTexture8* texture=nullptr; IDirect3DSurface8* surface=nullptr; ReflectionCaptureLayout layout{}; };
    bool enabled_=false, unsupported_=false;
    Target copy_, mid_, ps2_, field_;
    D3DFORMAT format_=D3DFMT_UNKNOWN;
    UINT width_=0, height_=0;
    ReflectionCaptureTransaction transaction_;
    PS2OutputStatus status_{};
    template<class T> static void drop(T*& p) noexcept {if(p)p->Release();p=nullptr;}
    template<class T> struct Ref { T* value=nullptr; ~Ref(){drop(value);} };
    static bool same_surface(IDirect3DSurface8* a,IDirect3DSurface8* b) noexcept {
        if(!a||!b)return false;if(a==b)return true;Ref<IUnknown> x,y;
        return SUCCEEDED(a->QueryInterface(IID_IUnknown,reinterpret_cast<void**>(&x.value)))&&SUCCEEDED(b->QueryInterface(IID_IUnknown,reinterpret_cast<void**>(&y.value)))&&x.value&&x.value==y.value;
    }
    static void release(Target& t) noexcept {drop(t.surface);drop(t.texture);t.layout={};}
    HRESULT make(IDirect3DDevice8& n,Target& t,UINT w,UINT h,const D3DCAPS8& caps) noexcept {
        if(!reflection_capture_layout(w,h,caps,t.layout))return D3DERR_NOTAVAILABLE;
        HRESULT hr=n.CreateTexture(t.layout.texture_width,t.layout.texture_height,1,D3DUSAGE_RENDERTARGET,format_,D3DPOOL_DEFAULT,&t.texture);
        if(SUCCEEDED(hr)&&!t.texture)hr=E_FAIL;
        if(SUCCEEDED(hr))hr=t.texture->GetSurfaceLevel(0,&t.surface);
        if(SUCCEEDED(hr)&&!t.surface)hr=E_FAIL;
        if(FAILED(hr))release(t);
        return hr;
    }
    bool mid_needed() const noexcept {return width_>2*kPS2DrawWidth||height_>2*kPS2DrawHeight;}
    HRESULT allocate(IDirect3DDevice8& n,const D3DSURFACE_DESC& desc,const D3DCAPS8& caps) noexcept {
        if(copy_.texture&&format_==desc.Format&&width_==desc.Width&&height_==desc.Height)return S_OK;
        release_resources();format_=desc.Format;width_=desc.Width;height_=desc.Height;
        HRESULT hr=make(n,copy_,width_,height_,caps);
        if(SUCCEEDED(hr)&&mid_needed())hr=make(n,mid_,(width_+1)/2,(height_+1)/2,caps);
        if(SUCCEEDED(hr))hr=make(n,ps2_,kPS2DrawWidth,kPS2DrawHeight,caps);
        if(SUCCEEDED(hr))hr=make(n,field_,kPS2FieldWidth,kPS2FieldLines,caps);
        if(FAILED(hr))release_resources();
        return hr;
    }
    HRESULT fail(const char* reason,HRESULT hr,bool permanent=false) noexcept {status_.reason=reason;status_.hr=hr;if(permanent)unsupported_=true;return hr;}
    HRESULT pass(IDirect3DDevice8& n,IDirect3DSurface8* target,UINT w,UINT h,IDirect3DTexture8* source,const PS2OutputQuad& q,bool chained) noexcept {
        HRESULT hr=transaction_.apply(n,target,source,w,h,chained);
        if(FAILED(hr))return hr;
        const auto v=ps2_output_vertices(q,w,h);
        transaction_.mark_up();hr=n.DrawPrimitiveUP(D3DPT_TRIANGLESTRIP,2,v.data(),sizeof(ReflectionCaptureVertex));++status_.draws;
        const HRESULT sync=transaction_.sync_up_stream(n);
        return FAILED(hr)?hr:sync;
    }
public:
    PS2OutputFilter()=default;
    ~PS2OutputFilter(){transaction_.release();release_resources();}
    PS2OutputFilter(const PS2OutputFilter&)=delete;
    PS2OutputFilter& operator=(const PS2OutputFilter&)=delete;
    void configure(bool enabled) noexcept {enabled_=enabled;}
    bool enabled() const noexcept {return enabled_;}
    bool pending() const noexcept {return transaction_.pending();}
    const PS2OutputStatus& status() const noexcept {return status_;}
    void set_writer(void* context,ReflectionCaptureWriter writer) noexcept {transaction_.set_writer(context,writer);}
    void release_resources() noexcept {release(copy_);release(mid_);release(ps2_);release(field_);format_=D3DFMT_UNKNOWN;width_=height_=0;}
    void before_reset() noexcept {release_resources();unsupported_=false;}
    HRESULT restore(IDirect3DDevice8& n) noexcept {const HRESULT hr=transaction_.restore(n);status_.restore_hr=hr;return hr;}

    // Called once per Present with the scene closed and the backbuffer bound.
    HRESULT apply(IDirect3DDevice8& n,bool scene_active,bool recording) noexcept {
        if(!enabled_)return S_FALSE;
        if(unsupported_)return status_.hr;
        if(pending())return fail("native_restore_pending",D3DERR_INVALIDCALL);
        if(scene_active||recording)return fail(scene_active?"scene_still_active":"stateblock_recording",S_FALSE);
        Ref<IDirect3DSurface8> current,back;
        HRESULT hr=n.GetRenderTarget(&current.value);if(FAILED(hr))return fail("get_render_target_failed",hr);
        hr=n.GetBackBuffer(0,D3DBACKBUFFER_TYPE_MONO,&back.value);if(FAILED(hr))return fail("get_backbuffer_failed",hr);
        if(!same_surface(current.value,back.value))return fail("not_main_backbuffer",S_FALSE);
        D3DSURFACE_DESC desc{};hr=back.value->GetDesc(&desc);if(FAILED(hr))return fail("surface_description_failed",hr);
        if(desc.Format!=D3DFMT_X8R8G8B8&&desc.Format!=D3DFMT_A8R8G8B8)return fail("source_format_unsupported",D3DERR_NOTAVAILABLE,true);
        D3DCAPS8 caps{};hr=n.GetDeviceCaps(&caps);if(FAILED(hr))return fail("device_caps_failed",hr);
        const DWORD ops=D3DTEXOPCAPS_MODULATE|D3DTEXOPCAPS_SELECTARG2,filters=D3DPTFILTERCAPS_MAGFLINEAR|D3DPTFILTERCAPS_MINFLINEAR;
        if((caps.TextureOpCaps&ops)!=ops||(caps.TextureFilterCaps&filters)!=filters||!(caps.SrcBlendCaps&D3DPBLENDCAPS_ONE)||!(caps.DestBlendCaps&D3DPBLENDCAPS_ONE))
            return fail("fixed_function_caps_unsupported",D3DERR_NOTAVAILABLE,true);
        const bool multisampled=desc.MultiSampleType!=D3DMULTISAMPLE_NONE;
        hr=allocate(n,desc,caps);if(FAILED(hr))return fail("private_target_allocation_failed",hr,hr==D3DERR_NOTAVAILABLE);
        if(multisampled&&(copy_.layout.texture_width!=desc.Width||copy_.layout.texture_height!=desc.Height))
            return fail("multisample_copy_unsupported_padded_dimensions",D3DERR_NOTAVAILABLE,true);
        const RECT rect{0,0,LONG(desc.Width),LONG(desc.Height)};const POINT origin{0,0};
        hr=n.CopyRects(back.value,multisampled?nullptr:&rect,multisampled?0:1,copy_.surface,multisampled?nullptr:&origin);
        if(FAILED(hr))return fail(multisampled?"msaa_resolve_copy_failed":"copyrects_failed",hr,multisampled);
        hr=transaction_.capture(n);if(FAILED(hr))return fail("native_state_capture_failed",hr);
        hr=n.BeginScene();
        if(FAILED(hr)){restore(n);return fail("begin_scene_failed",hr);}
        status_.draws=0;
        const Target* src=&copy_;UINT sw=width_,sh=height_;bool chained=false;
        if(mid_needed()){
            hr=pass(n,mid_.surface,mid_.layout.source_width,mid_.layout.source_height,copy_.texture,ps2_output_quad(sw,sh,copy_.layout.texture_width,copy_.layout.texture_height),chained);
            src=&mid_;sw=mid_.layout.source_width;sh=mid_.layout.source_height;chained=true;
        }
        if(SUCCEEDED(hr))hr=pass(n,ps2_.surface,kPS2DrawWidth,kPS2DrawHeight,src->texture,ps2_output_quad(sw,sh,src->layout.texture_width,src->layout.texture_height),chained);
        // Woven fields: each output row samples the boundary between source rows r and r+1.
        if(SUCCEEDED(hr))hr=pass(n,field_.surface,kPS2FieldWidth,kPS2FieldLines,ps2_.texture,
            ps2_output_quad(kPS2DrawWidth,kPS2DrawHeight,ps2_.layout.texture_width,ps2_.layout.texture_height,0.5f),true);
        if(SUCCEEDED(hr))hr=pass(n,back.value,width_,height_,field_.texture,
            ps2_output_quad(kPS2FieldWidth,kPS2FieldLines,field_.layout.texture_width,field_.layout.texture_height),true);
        const HRESULT ended=n.EndScene();
        const HRESULT restored=restore(n);
        if(FAILED(restored))return fail("native_state_restore_failed",restored);
        if(FAILED(hr))return fail("private_draw_failed",hr);
        if(FAILED(ended))return fail("end_scene_failed",ended);
        ++status_.frames;status_.reason="filtered";status_.hr=S_OK;return S_OK;
    }
};

}  // namespace gfx2::ps2port
