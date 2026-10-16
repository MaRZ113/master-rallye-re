#pragma once
#include "xtrail_fidelity.hpp"
#include <vector>
namespace gfx2::ps2port {
struct GlassSourceVertex {std::array<uint8_t,32> position_hash;float expected_normal[3],expected_uv[2];DWORD expected_color;float normal[3],uv[2];DWORD color;};
static_assert(sizeof(GlassSourceVertex)==80);
bool decode_xtrail_glass(const std::vector<uint8_t>&,std::vector<GlassSourceVertex>&,std::vector<DWORD>&,std::vector<DWORD>&) noexcept;
std::vector<XtrailDecalVertex> glass_vertices(const DrawSnapshot&,const std::vector<GlassSourceVertex>&,std::string_view expected);
struct GlassOp {bool render;DWORD stage,key;};
inline constexpr GlassOp kGlassOps[]={
    {true,0,D3DRS_ALPHATESTENABLE},{true,0,D3DRS_ALPHABLENDENABLE},{true,0,D3DRS_SRCBLEND},
    {true,0,D3DRS_DESTBLEND},{true,0,D3DRS_ZWRITEENABLE},{true,0,D3DRS_FOGENABLE},
    {false,0,D3DTSS_COLOROP},{false,0,D3DTSS_COLORARG1},{false,0,D3DTSS_COLORARG2},
    {false,0,D3DTSS_ALPHAOP},{false,0,D3DTSS_ALPHAARG1},{false,0,D3DTSS_ALPHAARG2},
    {false,0,D3DTSS_TEXCOORDINDEX},{false,0,D3DTSS_TEXTURETRANSFORMFLAGS},{false,1,D3DTSS_COLOROP}
};
class GlassTransaction {
    std::array<DWORD,std::size(kGlassOps)> scalar_{};
    IDirect3DBaseTexture8* texture_=nullptr;IDirect3DVertexBuffer8* stream_=nullptr;IDirect3DIndexBuffer8* indices_=nullptr;
    D3DMATRIX tex0_{};UINT stride_=0,base_=0;uint32_t pending_=0;bool captured_=false;
public:
    ~GlassTransaction(){release();}
    bool pending()const noexcept{return pending_!=0;}
    void release()noexcept;
    HRESULT capture(IDirect3DDevice8&)noexcept;
    template<class Writer>HRESULT pass(IDirect3DDevice8& n,IDirect3DTexture8* texture,bool highlight,const D3DMATRIX& normal_matrix,Writer&& notify)noexcept {
        if(!captured_||!texture)return E_INVALIDARG;
        const std::array<DWORD,std::size(kGlassOps)> v={FALSE,TRUE,highlight?D3DBLEND_ONE:D3DBLEND_SRCALPHA,
            highlight?D3DBLEND_ONE:D3DBLEND_INVSRCALPHA,FALSE,highlight?FALSE:scalar_[5],
            highlight?D3DTOP_SELECTARG1:D3DTOP_MODULATE,D3DTA_TEXTURE,D3DTA_DIFFUSE,
            D3DTOP_MODULATE,D3DTA_TEXTURE,D3DTA_DIFFUSE,
            highlight?D3DTSS_TCI_CAMERASPACENORMAL:0,highlight?D3DTTFF_COUNT2:D3DTTFF_DISABLE,D3DTOP_DISABLE};
        for(size_t i=0;i<v.size();++i){
            // On the second pass values are compared to saved originals, but
            // pending slots MUST be written even when restoring the original.
            if(!(pending_&(1u<<i))&&v[i]==scalar_[i])continue;
            pending_|=1u<<i;const auto& op=kGlassOps[i];HRESULT hr;
            if(op.render){auto a=pack(op.key,v[i]);hr=n.SetRenderState(static_cast<D3DRENDERSTATETYPE>(op.key),v[i]);notify(50,a,hr);}
            else{auto a=pack(op.stage,op.key,v[i]);hr=n.SetTextureStageState(op.stage,static_cast<D3DTEXTURESTAGESTATETYPE>(op.key),v[i]);notify(63,a,hr);}
            if(FAILED(hr))return hr;
        }
        pending_|=1u<<15;auto hr=n.SetTexture(0,texture);notify(61,pack(0,texture),hr);if(FAILED(hr))return hr;
        if(highlight){pending_|=1u<<16;hr=n.SetTransform(D3DTS_TEXTURE0,&normal_matrix);notify(37,pack(D3DTS_TEXTURE0,&normal_matrix),hr);}
        return hr;
    }
    template<class Writer>HRESULT emissive_pass(IDirect3DDevice8& n,Writer&& notify)noexcept{
        if(!captured_||pending_)return E_INVALIDARG;
        const std::array<DWORD,15> v={FALSE,TRUE,D3DBLEND_ONE,D3DBLEND_ONE,FALSE,FALSE,D3DTOP_SELECTARG1,D3DTA_TEXTURE,D3DTA_DIFFUSE,D3DTOP_SELECTARG1,D3DTA_TEXTURE,D3DTA_DIFFUSE,0,D3DTTFF_DISABLE,D3DTOP_DISABLE};
        for(size_t i=0;i<v.size();++i){if(v[i]==scalar_[i])continue;pending_|=1u<<i;const auto& op=kGlassOps[i];HRESULT hr;
            if(op.render){hr=n.SetRenderState(static_cast<D3DRENDERSTATETYPE>(op.key),v[i]);notify(50,pack(op.key,v[i]),hr);}
            else{hr=n.SetTextureStageState(op.stage,static_cast<D3DTEXTURESTAGESTATETYPE>(op.key),v[i]);notify(63,pack(op.stage,op.key,v[i]),hr);}if(FAILED(hr))return hr;
        }return S_OK;
    }
    // Kia PS2 mode1 ON core: opaque source RGB; no glow blending or environment stage.
    template<class Writer>HRESULT kia_lamp_on_pass(IDirect3DDevice8& n,Writer&& notify)noexcept{
        if(!captured_||pending_)return E_INVALIDARG;
        auto v=scalar_;v[1]=FALSE;v[6]=D3DTOP_SELECTARG1;v[7]=D3DTA_TEXTURE;v[9]=D3DTOP_SELECTARG1;v[10]=D3DTA_TEXTURE;v[12]=0;v[13]=D3DTTFF_DISABLE;v[14]=D3DTOP_DISABLE;
        for(size_t i=0;i<v.size();++i){if(v[i]==scalar_[i])continue;pending_|=1u<<i;const auto& op=kGlassOps[i];HRESULT hr;if(op.render){hr=n.SetRenderState(static_cast<D3DRENDERSTATETYPE>(op.key),v[i]);notify(50,pack(op.key,v[i]),hr);}else{hr=n.SetTextureStageState(op.stage,static_cast<D3DTEXTURESTAGESTATETYPE>(op.key),v[i]);notify(63,pack(op.stage,op.key,v[i]),hr);}if(FAILED(hr))return hr;}return S_OK;
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
            else{const auto& op=kGlassOps[i];if(op.render){hr=n.SetRenderState(static_cast<D3DRENDERSTATETYPE>(op.key),scalar_[i]);notify(50,pack(op.key,scalar_[i]),hr);}
                else{hr=n.SetTextureStageState(op.stage,static_cast<D3DTEXTURESTAGESTATETYPE>(op.key),scalar_[i]);notify(63,pack(op.stage,op.key,scalar_[i]),hr);}}
            if(SUCCEEDED(hr))pending_&=~(1u<<i);else if(SUCCEEDED(result))result=hr;
        }
        if(!pending_)release();return result;
    }
};
class XtrailGlass {
    bool requested_=false,diagnostics_=false,disabled_=false,blocked_=false,ready_=false;
    struct Cache {std::array<uint64_t,15> key{};std::vector<XtrailDecalVertex> vertices;bool valid=false;};
    std::array<Cache,16> cache_{};size_t next_=0;
    uint32_t logged_=0;std::vector<GlassSourceVertex> vertices_;std::vector<DWORD> primary_,highlight_;
    IDirect3DTexture8* primary_texture_=nullptr;IDirect3DTexture8* highlight_texture_=nullptr;
public:
    GlassTransaction transaction;
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
