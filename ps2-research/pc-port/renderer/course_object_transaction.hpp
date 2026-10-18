#pragma once

// Fixed, native-only preview transaction. Integration owns admission, drawing,
// tracing, and repair before any later application submission. No state blocks.
#include "state_tracker.hpp"
#include <array>
#include <cmath>
#include <cstring>
#include <cstdint>

namespace gfx2::ps2port {

enum class CourseObjectStateKind : uint8_t { Render, Stage, Matrix, VertexShader, PixelShader, Texture, Stream };
struct CourseObjectStateOp {
    CourseObjectStateKind kind;
    DWORD key;
    DWORD stage;
    DWORD preview;
};
inline constexpr std::array<CourseObjectStateOp, 34> kCourseObjectStateOps = {{
    {CourseObjectStateKind::Render,D3DRS_ZENABLE,0,D3DZB_TRUE},
    {CourseObjectStateKind::Render,D3DRS_ZWRITEENABLE,0,TRUE},
    {CourseObjectStateKind::Render,D3DRS_ZFUNC,0,D3DCMP_LESSEQUAL},
    {CourseObjectStateKind::Render,D3DRS_ALPHATESTENABLE,0,FALSE},
    {CourseObjectStateKind::Render,D3DRS_ALPHABLENDENABLE,0,TRUE},
    {CourseObjectStateKind::Render,D3DRS_SRCBLEND,0,D3DBLEND_SRCALPHA},
    {CourseObjectStateKind::Render,D3DRS_DESTBLEND,0,D3DBLEND_INVSRCALPHA},
    {CourseObjectStateKind::Render,D3DRS_CULLMODE,0,D3DCULL_NONE},
    {CourseObjectStateKind::Render,D3DRS_LIGHTING,0,FALSE},
    {CourseObjectStateKind::Render,D3DRS_FOGENABLE,0,FALSE},
    {CourseObjectStateKind::Render,D3DRS_STENCILENABLE,0,FALSE},
    {CourseObjectStateKind::Render,D3DRS_CLIPPLANEENABLE,0,0},
    {CourseObjectStateKind::Render,D3DRS_COLORWRITEENABLE,0,15},
    {CourseObjectStateKind::Stage,D3DTSS_COLOROP,0,D3DTOP_MODULATE},
    {CourseObjectStateKind::Stage,D3DTSS_COLORARG1,0,D3DTA_TEXTURE},
    {CourseObjectStateKind::Stage,D3DTSS_COLORARG2,0,D3DTA_DIFFUSE},
    {CourseObjectStateKind::Stage,D3DTSS_ALPHAOP,0,D3DTOP_MODULATE},
    {CourseObjectStateKind::Stage,D3DTSS_ALPHAARG1,0,D3DTA_TEXTURE},
    {CourseObjectStateKind::Stage,D3DTSS_ALPHAARG2,0,D3DTA_DIFFUSE},
    {CourseObjectStateKind::Stage,D3DTSS_TEXCOORDINDEX,0,0},
    {CourseObjectStateKind::Stage,D3DTSS_TEXTURETRANSFORMFLAGS,0,D3DTTFF_DISABLE},
    {CourseObjectStateKind::Stage,D3DTSS_ADDRESSU,0,D3DTADDRESS_WRAP},
    {CourseObjectStateKind::Stage,D3DTSS_ADDRESSV,0,D3DTADDRESS_WRAP},
    {CourseObjectStateKind::Stage,D3DTSS_MAGFILTER,0,D3DTEXF_LINEAR},
    {CourseObjectStateKind::Stage,D3DTSS_MINFILTER,0,D3DTEXF_LINEAR},
    {CourseObjectStateKind::Stage,D3DTSS_MIPFILTER,0,D3DTEXF_NONE},
    {CourseObjectStateKind::Stage,D3DTSS_COLOROP,1,D3DTOP_DISABLE},
    {CourseObjectStateKind::Matrix,D3DTS_WORLD,0,0},
    {CourseObjectStateKind::Matrix,D3DTS_VIEW,0,0},
    {CourseObjectStateKind::Matrix,D3DTS_PROJECTION,0,0},
    {CourseObjectStateKind::VertexShader,0,0,D3DFVF_XYZ|D3DFVF_DIFFUSE|D3DFVF_TEX1},
    {CourseObjectStateKind::PixelShader,0,0,0},
    {CourseObjectStateKind::Texture,0,0,0},
    {CourseObjectStateKind::Stream,0,0,0},
}};
inline constexpr size_t kCourseObjectStreamSlot = kCourseObjectStateOps.size()-1;

struct CourseObjectSavedState {
    DWORD scalar=0;
    D3DMATRIX matrix{};
    IDirect3DBaseTexture8* texture=nullptr;
    IDirect3DVertexBuffer8* stream=nullptr;
    UINT stride=0;
};

// The existing object preview retains its original defaults. Grass explicitly
// selects no depth writes and clamped sprite edges through the same transaction.
struct CourseObjectMaterialState {
    DWORD z_write=TRUE;
    DWORD address_u=D3DTADDRESS_WRAP;
    DWORD address_v=D3DTADDRESS_WRAP;
};

class CourseObjectTransaction {
    std::array<CourseObjectSavedState,kCourseObjectStateOps.size()> saved_{};
    uint64_t pending_=0;
    bool captured_=false;
    // SPLIT-GRASS1: optional viewport slot, used only by split-screen passes. Captured after the fixed states,
    // applied first and restored last; the single-camera transaction never touches it.
    D3DVIEWPORT8 saved_viewport_{};
    bool viewport_captured_=false,viewport_pending_=false;
    template<class Writer>
    HRESULT set_viewport(IDirect3DDevice8& native,const D3DVIEWPORT8& value,Writer& writer) noexcept {
        const Args args=pack(&value);const HRESULT hr=native.SetViewport(&value);
        writer(kSetViewportSlot,args,hr); // method_names.hpp: SetViewport.
        return hr;
    }

    static bool finite(const D3DMATRIX& matrix) noexcept {
        for(const auto& row:matrix.m)for(float value:row)if(!std::isfinite(value))return false;
        return true;
    }
    static D3DMATRIX identity() noexcept {
        D3DMATRIX result{};result._11=result._22=result._33=result._44=1.f;return result;
    }
    template<class Writer>
    HRESULT set(IDirect3DDevice8& native,size_t index,const CourseObjectSavedState& value,Writer& writer) noexcept {
        const auto& op=kCourseObjectStateOps[index];
        Args args{};uint32_t slot=0;HRESULT hr=E_INVALIDARG;
        switch(op.kind){
        case CourseObjectStateKind::Render:
            slot=50;args=pack(op.key,value.scalar);
            hr=native.SetRenderState(static_cast<D3DRENDERSTATETYPE>(op.key),value.scalar);break;
        case CourseObjectStateKind::Stage:
            slot=63;args=pack(op.stage,op.key,value.scalar);
            hr=native.SetTextureStageState(op.stage,static_cast<D3DTEXTURESTAGESTATETYPE>(op.key),value.scalar);break;
        case CourseObjectStateKind::Matrix:
            slot=37;args=pack(op.key,&value.matrix);
            hr=native.SetTransform(static_cast<D3DTRANSFORMSTATETYPE>(op.key),&value.matrix);break;
        case CourseObjectStateKind::VertexShader:
            slot=76;args=pack(value.scalar);hr=native.SetVertexShader(value.scalar);break;
        case CourseObjectStateKind::PixelShader:
            slot=88;args=pack(value.scalar);hr=native.SetPixelShader(value.scalar);break;
        case CourseObjectStateKind::Texture:
            slot=61;args=pack(op.stage,value.texture);hr=native.SetTexture(op.stage,value.texture);break;
        case CourseObjectStateKind::Stream:
            slot=83;args=pack(op.stage,value.stream,value.stride);hr=native.SetStreamSource(op.stage,value.stream,value.stride);break;
        }
        writer(slot,args,hr); // Synchronous, noexcept native-only tracker writer.
        return hr;
    }
public:
    static constexpr uint32_t kSetViewportSlot=40;
    HRESULT last_failure=S_OK;
    CourseObjectTransaction()=default;
    CourseObjectTransaction(const CourseObjectTransaction&)=delete;
    CourseObjectTransaction& operator=(const CourseObjectTransaction&)=delete;
    ~CourseObjectTransaction(){release();}
    bool has_pending() const noexcept {return pending_!=0||viewport_pending_;}
    bool captured() const noexcept {return captured_;}
    bool viewport_captured() const noexcept {return viewport_captured_;}
    bool viewport_pending() const noexcept {return viewport_pending_;}
    uint64_t pending_mask() const noexcept {return pending_;}

    // Explicit abandonment is only for device reset/final shutdown. It does
    // not restore native state; ordinary draw failures must call restore().
    void release() noexcept {
        for(auto& saved:saved_){
            if(saved.texture)saved.texture->Release();
            if(saved.stream)saved.stream->Release();
            saved={};
        }
        pending_=0;captured_=false;
        saved_viewport_={};viewport_captured_=viewport_pending_=false;
    }
    HRESULT capture(IDirect3DDevice8& native) noexcept {
        if(has_pending()){last_failure=D3DERR_INVALIDCALL;return last_failure;}
        release();
        for(size_t i=0;i<kCourseObjectStateOps.size();++i){
            const auto& op=kCourseObjectStateOps[i];auto& value=saved_[i];HRESULT hr=E_INVALIDARG;
            switch(op.kind){
            case CourseObjectStateKind::Render:hr=native.GetRenderState(static_cast<D3DRENDERSTATETYPE>(op.key),&value.scalar);break;
            case CourseObjectStateKind::Stage:hr=native.GetTextureStageState(op.stage,static_cast<D3DTEXTURESTAGESTATETYPE>(op.key),&value.scalar);break;
            case CourseObjectStateKind::Matrix:hr=native.GetTransform(static_cast<D3DTRANSFORMSTATETYPE>(op.key),&value.matrix);break;
            case CourseObjectStateKind::VertexShader:hr=native.GetVertexShader(&value.scalar);break;
            case CourseObjectStateKind::PixelShader:hr=native.GetPixelShader(&value.scalar);break;
            case CourseObjectStateKind::Texture:hr=native.GetTexture(op.stage,&value.texture);break;
            case CourseObjectStateKind::Stream:hr=native.GetStreamSource(op.stage,&value.stream,&value.stride);break;
            }
            if(FAILED(hr)){release();last_failure=hr;return hr;}
        }
        captured_=true;last_failure=S_OK;return S_OK;
    }
    template<class Writer>
    HRESULT restore(IDirect3DDevice8& native,Writer&& writer) noexcept {
        HRESULT result=S_OK;
        for(size_t i=kCourseObjectStateOps.size();i-- >0;){
            const uint64_t bit=uint64_t(1)<<i;
            if(!(pending_&bit))continue;
            const HRESULT hr=set(native,i,saved_[i],writer);
            if(SUCCEEDED(hr))pending_&=~bit;
            else if(SUCCEEDED(result))result=hr;
        }
        if(viewport_pending_){
            const HRESULT hr=set_viewport(native,saved_viewport_,writer);
            if(SUCCEEDED(hr))viewport_pending_=false;
            else if(SUCCEEDED(result))result=hr;
        }
        if(!has_pending())release();
        last_failure=result;return result;
    }
    template<class Writer>
    HRESULT apply(IDirect3DDevice8& native,IDirect3DBaseTexture8* texture,
                  const D3DMATRIX& view,const D3DMATRIX& projection,Writer&& writer,
                  const CourseObjectMaterialState& material={}) noexcept {
        const auto valid_address=[](DWORD v){return v==D3DTADDRESS_WRAP||v==D3DTADDRESS_CLAMP;};
        // A split pass applies its viewport first; only pending fixed states forbid an overlapping apply.
        if(!captured_||pending_||!texture||!finite(view)||!finite(projection)||
           material.z_write>TRUE||!valid_address(material.address_u)||!valid_address(material.address_v)){
            last_failure=E_INVALIDARG;return last_failure;
        }
        for(size_t i=0;i<kCourseObjectStateOps.size();++i){
            const auto& op=kCourseObjectStateOps[i];
            if(op.kind==CourseObjectStateKind::Stream)continue; // UP owns this side effect.
            CourseObjectSavedState desired{};desired.scalar=op.preview;
            if(op.kind==CourseObjectStateKind::Render&&op.key==D3DRS_ZWRITEENABLE)desired.scalar=material.z_write;
            if(op.kind==CourseObjectStateKind::Stage&&op.key==D3DTSS_ADDRESSU)desired.scalar=material.address_u;
            if(op.kind==CourseObjectStateKind::Stage&&op.key==D3DTSS_ADDRESSV)desired.scalar=material.address_v;
            bool changed=saved_[i].scalar!=desired.scalar;
            if(op.kind==CourseObjectStateKind::Matrix){
                desired.matrix=op.key==D3DTS_WORLD?identity():op.key==D3DTS_VIEW?view:projection;
                changed=std::memcmp(&desired.matrix,&saved_[i].matrix,sizeof(D3DMATRIX))!=0;
            }else if(op.kind==CourseObjectStateKind::Texture){
                desired.texture=texture;changed=texture!=saved_[i].texture;
            }
            if(!changed)continue;
            // A failed native setter can still have mutated the slot.
            pending_|=uint64_t(1)<<i;
            const HRESULT hr=set(native,i,desired,writer);
            if(FAILED(hr)){restore(native,writer);last_failure=hr;return hr;}
        }
        last_failure=S_OK;return S_OK;
    }
    // After capture(), before any apply: remembers the native viewport so a split pass can draw into its half.
    HRESULT capture_viewport(IDirect3DDevice8& native) noexcept {
        if(!captured_||has_pending()||viewport_captured_){last_failure=D3DERR_INVALIDCALL;return last_failure;}
        D3DVIEWPORT8 value{};const HRESULT hr=native.GetViewport(&value);
        if(FAILED(hr)){last_failure=hr;return hr;}
        saved_viewport_=value;viewport_captured_=true;last_failure=S_OK;return S_OK;
    }
    // Before apply(): a failed setter can still have mutated the viewport, so it stays pending until restore().
    template<class Writer>
    HRESULT apply_viewport(IDirect3DDevice8& native,const D3DVIEWPORT8& viewport,Writer&& writer) noexcept {
        if(!captured_||!viewport_captured_||has_pending()||!viewport.Width||!viewport.Height||
           !std::isfinite(viewport.MinZ)||!std::isfinite(viewport.MaxZ)){last_failure=E_INVALIDARG;return last_failure;}
        if(!std::memcmp(&viewport,&saved_viewport_,sizeof(viewport))){last_failure=S_OK;return S_OK;}
        viewport_pending_=true;
        const HRESULT hr=set_viewport(native,viewport,writer);
        if(FAILED(hr)){restore(native,writer);last_failure=hr;return hr;}
        last_failure=S_OK;return S_OK;
    }
    // Mark immediately BEFORE the native UP call, including failing draws.
    void mark_up_stream_changed() noexcept {
        if(captured_)pending_|=uint64_t(1)<<kCourseObjectStreamSlot;
    }
};
} // namespace gfx2::ps2port
