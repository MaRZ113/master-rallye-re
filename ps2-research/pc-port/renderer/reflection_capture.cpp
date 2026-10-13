#include "reflection_capture.hpp"
#include <cstring>

namespace gfx2::ps2port {
namespace {
template<class T> void drop(T*& value) noexcept {if(value)value->Release();value=nullptr;}
template<class T> struct Ref { T* value=nullptr; ~Ref(){drop(value);} };
UINT power_two(UINT value) noexcept {UINT result=1;while(result<value&&result<=0x40000000u)result<<=1;return result;}
bool same_surface(IDirect3DSurface8* a,IDirect3DSurface8* b) noexcept {
    if(!a||!b)return false;
    if(a==b)return true;
    Ref<IUnknown> ia,ib;
    return SUCCEEDED(a->QueryInterface(IID_IUnknown,reinterpret_cast<void**>(&ia.value)))&&
        SUCCEEDED(b->QueryInterface(IID_IUnknown,reinterpret_cast<void**>(&ib.value)))&&
        ia.value&&ib.value&&ia.value==ib.value;
}
}
bool reflection_capture_layout(UINT width,UINT height,const D3DCAPS8& caps,ReflectionCaptureLayout& out) noexcept {
    out={};if(!width||!height||width>8192||height>8192)return false;
    UINT tw=width,th=height;
    if(caps.TextureCaps&D3DPTEXTURECAPS_POW2){tw=power_two(tw);th=power_two(th);}
    if(caps.TextureCaps&D3DPTEXTURECAPS_SQUAREONLY)tw=th=tw>th?tw:th;
    if(!tw||!th||tw>caps.MaxTextureWidth||th>caps.MaxTextureHeight||caps.MaxTextureWidth<64||caps.MaxTextureHeight<64)return false;
    if(caps.MaxTextureAspectRatio&&(tw>uint64_t(th)*caps.MaxTextureAspectRatio||th>uint64_t(tw)*caps.MaxTextureAspectRatio))return false;
    const uint64_t bytes=uint64_t(tw)*th*4;
    if(bytes>16ull*1024*1024)return false;
    out={width,height,tw,th,bytes};return true;
}
std::array<ReflectionCaptureVertex,4> reflection_capture_quad(float u,float v,bool flip,DWORD color) noexcept {
    const float top=flip?v:0.f,bottom=flip?0.f:v;
    return {{{-.5f,-.5f,0.f,1.f,color,0.f,top},
             {63.5f,-.5f,0.f,1.f,color,u,top},
             {-.5f,63.5f,0.f,1.f,color,0.f,bottom},
             {63.5f,63.5f,0.f,1.f,color,u,bottom}}};
}
void ReflectionCaptureTransaction::notify(uint32_t slot,const Args& args,HRESULT hr) noexcept {
    if(writer_)writer_(context_,slot,args,hr);
}
HRESULT ReflectionCaptureTransaction::write(IDirect3DDevice8& native,size_t i,const ReflectionCaptureSaved& value) noexcept {
    const auto& op=kReflectionCaptureOps[i];HRESULT hr=E_INVALIDARG;uint32_t slot=0;Args args{};
    switch(op.kind){
    case ReflectionCaptureStateKind::Render:slot=50;args=pack(op.key,value.scalar);hr=native.SetRenderState(static_cast<D3DRENDERSTATETYPE>(op.key),value.scalar);break;
    case ReflectionCaptureStateKind::Stage:slot=63;args=pack(op.stage,op.key,value.scalar);hr=native.SetTextureStageState(op.stage,static_cast<D3DTEXTURESTAGESTATETYPE>(op.key),value.scalar);break;
    case ReflectionCaptureStateKind::VertexShader:slot=76;args=pack(value.scalar);hr=native.SetVertexShader(value.scalar);break;
    case ReflectionCaptureStateKind::PixelShader:slot=88;args=pack(value.scalar);hr=native.SetPixelShader(value.scalar);break;
    case ReflectionCaptureStateKind::Texture:slot=61;args=pack(op.stage,value.texture);hr=native.SetTexture(op.stage,value.texture);break;
    }
    notify(slot,args,hr);return hr;
}
void ReflectionCaptureTransaction::release() noexcept {
    for(auto& s:saved_){drop(s.texture);s={};}
    drop(target_);drop(depth_);drop(stream_);
    captured_=false;pending_=0;target_pending_=viewport_pending_=stream_pending_=false;
}
HRESULT ReflectionCaptureTransaction::capture(IDirect3DDevice8& native) noexcept {
    if(pending())return D3DERR_INVALIDCALL;
    release();HRESULT hr=S_OK;
    for(size_t i=0;i<kReflectionCaptureOps.size();++i){
        const auto& op=kReflectionCaptureOps[i];auto& v=saved_[i];
        switch(op.kind){
        case ReflectionCaptureStateKind::Render:hr=native.GetRenderState(static_cast<D3DRENDERSTATETYPE>(op.key),&v.scalar);break;
        case ReflectionCaptureStateKind::Stage:hr=native.GetTextureStageState(op.stage,static_cast<D3DTEXTURESTAGESTATETYPE>(op.key),&v.scalar);break;
        case ReflectionCaptureStateKind::VertexShader:hr=native.GetVertexShader(&v.scalar);break;
        case ReflectionCaptureStateKind::PixelShader:hr=native.GetPixelShader(&v.scalar);break;
        case ReflectionCaptureStateKind::Texture:hr=native.GetTexture(op.stage,&v.texture);break;
        }
        if(FAILED(hr)){release();return hr;}
    }
    hr=native.GetRenderTarget(&target_);
    if(SUCCEEDED(hr)&&target_)hr=native.GetDepthStencilSurface(&depth_);
    // A null depth surface is legal for an offscreen capture transaction.
    if(hr==D3DERR_NOTFOUND)hr=S_OK;
    if(SUCCEEDED(hr))hr=native.GetViewport(&viewport_);
    if(SUCCEEDED(hr))hr=native.GetStreamSource(0,&stream_,&stride_);
    if(FAILED(hr)||!target_){release();return FAILED(hr)?hr:E_FAIL;}
    captured_=true;return S_OK;
}
HRESULT ReflectionCaptureTransaction::apply(IDirect3DDevice8& native,IDirect3DSurface8* target,IDirect3DTexture8* env) noexcept {
    if(!captured_||pending()||!target||!env)return E_INVALIDARG;
    // Unbind stage 1 before changing targets, including retained previous targets.
    ReflectionCaptureSaved nil{};pending_|=uint64_t(1)<<41;
    HRESULT hr=write(native,41,nil);if(FAILED(hr))return hr;
    target_pending_=viewport_pending_=true; // SetRenderTarget can change viewport.
    hr=native.SetRenderTarget(target,nullptr);notify(31,pack(target,nullptr),hr);if(FAILED(hr))return hr;
    const D3DVIEWPORT8 desired{0,0,64,64,0.f,1.f};
    hr=native.SetViewport(&desired);notify(40,pack(&desired),hr);if(FAILED(hr))return hr;
    for(size_t i=0;i<kReflectionCaptureOps.size();++i){
        if(i==41)continue;
        ReflectionCaptureSaved desired_state{};desired_state.scalar=kReflectionCaptureOps[i].value;
        if(kReflectionCaptureOps[i].kind==ReflectionCaptureStateKind::Texture)desired_state.texture=env;
        pending_|=uint64_t(1)<<i; // Failed calls may have partially mutated native state.
        hr=write(native,i,desired_state);if(FAILED(hr))return hr;
    }
    return S_OK;
}
HRESULT ReflectionCaptureTransaction::framebuffer_pass(IDirect3DDevice8& native,IDirect3DTexture8* copied) noexcept {
    if(!captured_||!copied)return E_INVALIDARG;
    ReflectionCaptureSaved value{};value.scalar=TRUE;
    pending_|=uint64_t(1)<<3;HRESULT hr=write(native,3,value);if(FAILED(hr))return hr;
    value.texture=copied;pending_|=uint64_t(1)<<40;return write(native,40,value);
}
HRESULT ReflectionCaptureTransaction::sync_up_stream(IDirect3DDevice8& native) noexcept {
    if(!captured_)return E_INVALIDARG;
    stream_pending_=true;
    const HRESULT hr=native.SetStreamSource(0,nullptr,0);notify(83,pack(0,nullptr,0),hr);return hr;
}
HRESULT ReflectionCaptureTransaction::restore(IDirect3DDevice8& native) noexcept {
    HRESULT result=S_OK;
    const auto retain_failure=[&](HRESULT hr){if(FAILED(hr)&&SUCCEEDED(result))result=hr;};
    // Restore target first: it implicitly changes viewport. Never release the
    // original target/depth until both state writes have actually succeeded.
    if(target_pending_){const HRESULT hr=native.SetRenderTarget(target_,depth_);notify(31,pack(target_,depth_),hr);
        if(SUCCEEDED(hr)){target_pending_=false;viewport_pending_=true;}else retain_failure(hr);}
    if(viewport_pending_&&!target_pending_){const HRESULT hr=native.SetViewport(&viewport_);notify(40,pack(&viewport_),hr);
        if(SUCCEEDED(hr))viewport_pending_=false;else retain_failure(hr);}
    if(stream_pending_){const HRESULT hr=native.SetStreamSource(0,stream_,stride_);notify(83,pack(0,stream_,stride_),hr);
        if(SUCCEEDED(hr))stream_pending_=false;else retain_failure(hr);}
    for(size_t i=kReflectionCaptureOps.size();i-- >0;){
        const uint64_t bit=uint64_t(1)<<i;if(!(pending_&bit))continue;
        const HRESULT hr=write(native,i,saved_[i]);if(SUCCEEDED(hr))pending_&=~bit;else retain_failure(hr);
    }
    if(!pending())release();return result;
}
void MixedReflectionCapture::release_resources() noexcept {
    drop(copy_surface_);drop(copy_texture_);drop(mixed_surface_);drop(mixed_texture_);
    layout_={};format_=D3DFMT_UNKNOWN;target_format_=D3DFMT_UNKNOWN;ready_=false;
}
void MixedReflectionCapture::release() noexcept {
    transaction_.release();release_resources();attempted_=false;permanently_unsupported_=false;ready_frame_=attempted_frame_=0;status_={};
}
HRESULT MixedReflectionCapture::repair(IDirect3DDevice8& native) noexcept {
    const HRESULT hr=transaction_.restore(native);status_.restore_hr=hr;
    if(FAILED(hr))ready_=false;return hr;
}
HRESULT MixedReflectionCapture::allocate(IDirect3DDevice8& native,const D3DSURFACE_DESC& desc,const ReflectionCaptureLayout& layout) noexcept {
    if(copy_texture_&&mixed_texture_&&format_==desc.Format&&layout_.source_width==layout.source_width&&
       layout_.source_height==layout.source_height&&layout_.texture_width==layout.texture_width&&layout_.texture_height==layout.texture_height)return S_OK;
    release_resources();HRESULT hr=native.CreateTexture(layout.texture_width,layout.texture_height,1,D3DUSAGE_RENDERTARGET,
        desc.Format,D3DPOOL_DEFAULT,&copy_texture_);
    if(SUCCEEDED(hr)&&!copy_texture_)hr=E_FAIL;
    if(SUCCEEDED(hr))hr=copy_texture_->GetSurfaceLevel(0,&copy_surface_);
    if(SUCCEEDED(hr)&&!copy_surface_)hr=E_FAIL;
    target_format_=prefer_16bit_?D3DFMT_A1R5G5B5:D3DFMT_A8R8G8B8;
    if(SUCCEEDED(hr)){
        hr=native.CreateTexture(64,64,1,D3DUSAGE_RENDERTARGET,target_format_,D3DPOOL_DEFAULT,&mixed_texture_);
        // A failed driver allocation may still return a retained pointer.
        // Release it before the explicit working Mode4 fallback allocation.
        if((FAILED(hr)||!mixed_texture_)&&prefer_16bit_){
            drop(mixed_texture_);target_format_=D3DFMT_A8R8G8B8;
            hr=native.CreateTexture(64,64,1,D3DUSAGE_RENDERTARGET,target_format_,D3DPOOL_DEFAULT,&mixed_texture_);
        }
    }
    if(SUCCEEDED(hr)&&!mixed_texture_)hr=E_FAIL;
    if(SUCCEEDED(hr))hr=mixed_texture_->GetSurfaceLevel(0,&mixed_surface_);
    if(FAILED(hr)||!copy_texture_||!copy_surface_||!mixed_texture_||!mixed_surface_){release_resources();return FAILED(hr)?hr:E_FAIL;}
    format_=desc.Format;layout_=layout;return S_OK;
}
HRESULT MixedReflectionCapture::capture(IDirect3DDevice8& native,IDirect3DTexture8* env,uint64_t frame,bool recording) noexcept {
    if(ready_texture(frame))return S_OK;
    if(permanently_unsupported_)return status_.capture_hr;
    if(attempted_&&attempted_frame_==frame)return status_.capture_hr;
    ready_=false;attempted_=true;attempted_frame_=frame;status_={};status_.frame=frame;
    const auto fail=[&](const char* reason,HRESULT hr){status_.reason=reason;status_.capture_hr=hr;return hr;};
    if(pending())return fail("native_restore_pending",D3DERR_INVALIDCALL);
    if(recording||!env)return fail(recording?"stateblock_recording":"missing_verified_static_source",D3DERR_INVALIDCALL);
    Ref<IDirect3DSurface8> current,back;
    HRESULT hr=native.GetRenderTarget(&current.value);if(FAILED(hr))return fail("get_render_target_failed",hr);
    hr=native.GetBackBuffer(0,D3DBACKBUFFER_TYPE_MONO,&back.value);if(FAILED(hr))return fail("get_backbuffer_failed",hr);
    if(!same_surface(current.value,back.value))return fail("not_main_backbuffer",D3DERR_INVALIDCALL);
    D3DSURFACE_DESC desc{};hr=current.value->GetDesc(&desc);if(FAILED(hr))return fail("surface_description_failed",hr);
    status_.source_format=desc.Format;status_.source_multisample=desc.MultiSampleType;
    if(desc.MultiSampleType!=D3DMULTISAMPLE_NONE){permanently_unsupported_=true;return fail("multisample_copy_unsupported",D3DERR_NOTAVAILABLE);}
    if(desc.Format!=D3DFMT_X8R8G8B8&&desc.Format!=D3DFMT_A8R8G8B8){permanently_unsupported_=true;return fail("source_format_unsupported",D3DERR_NOTAVAILABLE);}
    D3DCAPS8 caps{};hr=native.GetDeviceCaps(&caps);if(FAILED(hr))return fail("device_caps_failed",hr);
    const DWORD required_ops=D3DTEXOPCAPS_MODULATE|D3DTEXOPCAPS_SELECTARG2;
    const DWORD required_filters=D3DPTFILTERCAPS_MAGFLINEAR|D3DPTFILTERCAPS_MINFLINEAR;
    if((caps.TextureOpCaps&required_ops)!=required_ops||!(caps.SrcBlendCaps&D3DPBLENDCAPS_ONE)||!(caps.DestBlendCaps&D3DPBLENDCAPS_ONE)||
       (caps.TextureFilterCaps&required_filters)!=required_filters){permanently_unsupported_=true;return fail("composition_caps_unsupported",D3DERR_NOTAVAILABLE);}
    ReflectionCaptureLayout layout{};if(!reflection_capture_layout(desc.Width,desc.Height,caps,layout)){permanently_unsupported_=true;return fail("copy_texture_budget_or_caps",D3DERR_NOTAVAILABLE);}
    status_.layout=layout;hr=allocate(native,desc,layout);if(FAILED(hr))return fail("private_target_allocation_failed",hr);
    status_.target_format=target_format_;status_.precision_fallback=prefer_16bit_&&target_format_!=D3DFMT_A1R5G5B5;
    const RECT source{0,0,static_cast<LONG>(desc.Width),static_cast<LONG>(desc.Height)};const POINT destination{0,0};
    hr=native.CopyRects(current.value,&source,1,copy_surface_,&destination);status_.copy_hr=hr;
    if(FAILED(hr))return fail("native_copyrects_failed",hr);
    hr=transaction_.capture(native);if(FAILED(hr))return fail("native_state_capture_failed",hr);
    hr=transaction_.apply(native,mixed_surface_,env);
    if(SUCCEEDED(hr)){
        const auto vertices=reflection_capture_quad(1.f,1.f,false,0xffffffffu);transaction_.mark_up();
        hr=native.DrawPrimitiveUP(D3DPT_TRIANGLESTRIP,2,vertices.data(),sizeof(ReflectionCaptureVertex));++status_.private_draws;
        const HRESULT sync=transaction_.sync_up_stream(native);if(SUCCEEDED(hr)&&FAILED(sync))hr=sync;
    }
    if(SUCCEEDED(hr))hr=transaction_.framebuffer_pass(native,copy_texture_);
    if(SUCCEEDED(hr)){
        // 96/255 is the fixed-function RGB approximation of PS2 FIX=48/128.
        // Original GS PSMCT16 quantization and update timing are not reproduced.
        const auto vertices=reflection_capture_quad(float(desc.Width)/layout.texture_width,float(desc.Height)/layout.texture_height,true,0xff606060u);
        transaction_.mark_up();hr=native.DrawPrimitiveUP(D3DPT_TRIANGLESTRIP,2,vertices.data(),sizeof(ReflectionCaptureVertex));++status_.private_draws;
        const HRESULT sync=transaction_.sync_up_stream(native);if(SUCCEEDED(hr)&&FAILED(sync))hr=sync;
    }
    const HRESULT restored=transaction_.restore(native);status_.restore_hr=restored;
    if(FAILED(restored))return fail("native_state_restore_failed",restored);
    if(FAILED(hr))return fail("private_composition_failed",hr);
    ready_=true;ready_frame_=frame;status_.capture_hr=S_OK;status_.reason="mixed_source_ready";return S_OK;
}
} // namespace gfx2::ps2port
