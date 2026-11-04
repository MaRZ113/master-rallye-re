#pragma once
// Shared per-draw state transaction for emissive vehicle passes: brake lamps of every fleet car and the X-Trail glass
// pilot. Captures the 15 scalar states of kLampOps plus texture 0 / TEXTURE0 transform / stream 0 / indices and restores
// exactly what it changed (in reverse order), including after a partial failure.
#include "state_tracker.hpp"
#include <array>
#include <d3d8.h>
#include <iterator>
#include <string_view>
namespace gfx2::ps2port {
// Two-switch opt-in shared by the vehicle features (mode=1 and version=1 on a supported build).
constexpr bool feature_opt_in(std::wstring_view mode,std::wstring_view version,bool supported) noexcept {
    return supported&&mode==L"1"&&version==L"1";
}
struct LampOp {bool render;DWORD stage,key;};
inline constexpr LampOp kLampOps[]={
    {true,0,D3DRS_ALPHATESTENABLE},{true,0,D3DRS_ALPHABLENDENABLE},{true,0,D3DRS_SRCBLEND},
    {true,0,D3DRS_DESTBLEND},{true,0,D3DRS_ZWRITEENABLE},{true,0,D3DRS_FOGENABLE},
    {false,0,D3DTSS_COLOROP},{false,0,D3DTSS_COLORARG1},{false,0,D3DTSS_COLORARG2},
    {false,0,D3DTSS_ALPHAOP},{false,0,D3DTSS_ALPHAARG1},{false,0,D3DTSS_ALPHAARG2},
    {false,0,D3DTSS_TEXCOORDINDEX},{false,0,D3DTSS_TEXTURETRANSFORMFLAGS},{false,1,D3DTSS_COLOROP}
};
class LampTransaction {
    std::array<DWORD,std::size(kLampOps)> scalar_{};
    IDirect3DBaseTexture8* texture_=nullptr;IDirect3DVertexBuffer8* stream_=nullptr;IDirect3DIndexBuffer8* indices_=nullptr;
    D3DMATRIX tex0_{};UINT stride_=0,base_=0;uint32_t pending_=0;bool captured_=false;
    template<class Writer>HRESULT write(IDirect3DDevice8& n,size_t i,DWORD value,Writer&& notify)noexcept{
        const auto& op=kLampOps[i];HRESULT hr;
        if(op.render){hr=n.SetRenderState(static_cast<D3DRENDERSTATETYPE>(op.key),value);notify(50,pack(op.key,value),hr);}
        else{hr=n.SetTextureStageState(op.stage,static_cast<D3DTEXTURESTAGESTATETYPE>(op.key),value);notify(63,pack(op.stage,op.key,value),hr);}
        return hr;
    }
    // Writes only the scalars that differ from the captured originals.
    template<class Writer>HRESULT apply_changed(IDirect3DDevice8& n,const std::array<DWORD,std::size(kLampOps)>& v,Writer&& notify)noexcept{
        for(size_t i=0;i<v.size();++i){if(v[i]==scalar_[i])continue;pending_|=1u<<i;const auto hr=write(n,i,v[i],notify);if(FAILED(hr))return hr;}
        return S_OK;
    }
public:
    ~LampTransaction(){release();}
    bool pending()const noexcept{return pending_!=0;}
    void release()noexcept{
        if(texture_)texture_->Release();if(stream_)stream_->Release();if(indices_)indices_->Release();
        texture_=nullptr;stream_=nullptr;indices_=nullptr;pending_=0;captured_=false;
    }
    HRESULT capture(IDirect3DDevice8& n)noexcept{
        if(pending_)return D3DERR_INVALIDCALL;release();
        for(size_t i=0;i<std::size(kLampOps);++i){const auto& op=kLampOps[i];const auto hr=op.render?n.GetRenderState(static_cast<D3DRENDERSTATETYPE>(op.key),&scalar_[i]):n.GetTextureStageState(op.stage,static_cast<D3DTEXTURESTAGESTATETYPE>(op.key),&scalar_[i]);if(FAILED(hr))return hr;}
        auto hr=n.GetTexture(0,&texture_);if(SUCCEEDED(hr))hr=n.GetTransform(D3DTS_TEXTURE0,&tex0_);
        if(SUCCEEDED(hr))hr=n.GetStreamSource(0,&stream_,&stride_);if(SUCCEEDED(hr))hr=n.GetIndices(&indices_,&base_);
        if(FAILED(hr)||!stream_||!indices_){release();return FAILED(hr)?hr:E_POINTER;}captured_=true;return S_OK;
    }
    // X-Trail glass: blended glass pass, or additive camera-space highlight pass.
    template<class Writer>HRESULT pass(IDirect3DDevice8& n,IDirect3DTexture8* texture,bool highlight,const D3DMATRIX& normal_matrix,Writer&& notify)noexcept {
        if(!captured_||!texture)return E_INVALIDARG;
        const std::array<DWORD,std::size(kLampOps)> v={FALSE,TRUE,highlight?D3DBLEND_ONE:D3DBLEND_SRCALPHA,
            highlight?D3DBLEND_ONE:D3DBLEND_INVSRCALPHA,FALSE,highlight?FALSE:scalar_[5],
            highlight?D3DTOP_SELECTARG1:D3DTOP_MODULATE,D3DTA_TEXTURE,D3DTA_DIFFUSE,
            D3DTOP_MODULATE,D3DTA_TEXTURE,D3DTA_DIFFUSE,
            highlight?D3DTSS_TCI_CAMERASPACENORMAL:0,highlight?D3DTTFF_COUNT2:D3DTTFF_DISABLE,D3DTOP_DISABLE};
        for(size_t i=0;i<v.size();++i){
            // On the second pass values are compared to saved originals, but
            // pending slots MUST be written even when restoring the original.
            if(!(pending_&(1u<<i))&&v[i]==scalar_[i])continue;
            pending_|=1u<<i;const auto hr=write(n,i,v[i],notify);if(FAILED(hr))return hr;
        }
        pending_|=1u<<15;auto hr=n.SetTexture(0,texture);notify(61,pack(0,texture),hr);if(FAILED(hr))return hr;
        if(highlight){pending_|=1u<<16;hr=n.SetTransform(D3DTS_TEXTURE0,&normal_matrix);notify(37,pack(D3DTS_TEXTURE0,&normal_matrix),hr);}
        return hr;
    }
    // Additive glow halo: ONE/ONE, no Z write, no fog, texture colour and alpha.
    template<class Writer>HRESULT emissive_pass(IDirect3DDevice8& n,Writer&& notify)noexcept{
        if(!captured_||pending_)return E_INVALIDARG;
        return apply_changed(n,{FALSE,TRUE,D3DBLEND_ONE,D3DBLEND_ONE,FALSE,FALSE,D3DTOP_SELECTARG1,D3DTA_TEXTURE,D3DTA_DIFFUSE,D3DTOP_SELECTARG1,D3DTA_TEXTURE,D3DTA_DIFFUSE,0,D3DTTFF_DISABLE,D3DTOP_DISABLE},notify);
    }
    // PS2 mode1 brake-lamp ON core (BREAKLIGHTSON, identical on every PS2 car): opaque source RGB, no glow blending,
    // no environment stage.
    template<class Writer>HRESULT brake_on_pass(IDirect3DDevice8& n,Writer&& notify)noexcept{
        if(!captured_||pending_)return E_INVALIDARG;
        auto v=scalar_;v[1]=FALSE;v[6]=D3DTOP_SELECTARG1;v[7]=D3DTA_TEXTURE;v[9]=D3DTOP_SELECTARG1;v[10]=D3DTA_TEXTURE;v[12]=0;v[13]=D3DTTFF_DISABLE;v[14]=D3DTOP_DISABLE;
        return apply_changed(n,v,notify);
    }
    template<class Writer>HRESULT bind_primary(IDirect3DDevice8& n,IDirect3DTexture8* texture,Writer&& notify)noexcept{if(!captured_||!texture)return E_INVALIDARG;pending_|=1u<<15;const auto hr=n.SetTexture(0,texture);notify(61,pack(0,texture),hr);return hr;}
    void mark_up()noexcept{if(captured_)pending_|=(1u<<17)|(1u<<18);}
    template<class Writer>HRESULT restore(IDirect3DDevice8& n,Writer&& notify)noexcept{
        HRESULT result=S_OK;
        for(int i=18;i>=0;--i){if(!(pending_&(1u<<i)))continue;HRESULT hr=E_FAIL;
            if(i==18){hr=n.SetIndices(indices_,base_);notify(85,pack(indices_,base_),hr);}
            else if(i==17){hr=n.SetStreamSource(0,stream_,stride_);notify(83,pack(0,stream_,stride_),hr);}
            else if(i==16){hr=n.SetTransform(D3DTS_TEXTURE0,&tex0_);notify(37,pack(D3DTS_TEXTURE0,&tex0_),hr);}
            else if(i==15){hr=n.SetTexture(0,texture_);notify(61,pack(0,texture_),hr);}
            else hr=write(n,size_t(i),scalar_[size_t(i)],notify);
            if(SUCCEEDED(hr))pending_&=~(1u<<i);else if(SUCCEEDED(result))result=hr;
        }
        if(!pending_)release();return result;
    }
};
} // namespace gfx2::ps2port
