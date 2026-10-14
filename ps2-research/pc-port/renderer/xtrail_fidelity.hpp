#pragma once
#include "vehicle_partition.hpp"
#include "xtrail_decal_registry.hpp"
#include <array>
namespace gfx2::ps2port {
constexpr bool xtrail_fidelity_opt_in(std::wstring_view mode,std::wstring_view version,bool supported) noexcept {
    return supported&&mode==L"1"&&version==L"1";
}
struct XtrailDecalVertex {float xyz[3],normal[3];DWORD diffuse;float uv[2];};
static_assert(sizeof(XtrailDecalVertex)==36);
std::vector<XtrailDecalVertex> prepare_xtrail_decal(const DrawSnapshot&);
std::vector<XtrailDecalVertex> prepare_decal_vertices(const DrawSnapshot&,std::string_view digest,
    const XtrailDecalNormal*,size_t entries);
class XtrailTransaction {
    std::array<DWORD,8> stages_{};DWORD fvf_=0;UINT stride_=0,base_=0;
    IDirect3DBaseTexture8* texture_=nullptr;
    IDirect3DVertexBuffer8* stream_=nullptr;
    IDirect3DIndexBuffer8* indices_=nullptr;
    uint32_t pending_=0;bool captured_=false;
public:
    ~XtrailTransaction(){release();}
    bool pending() const noexcept{return pending_!=0;}
    void release() noexcept;
    HRESULT capture(IDirect3DDevice8&) noexcept;
    template<class Write>HRESULT apply(IDirect3DDevice8& n,IDirect3DTexture8* texture,Write&& notify) noexcept {
        if(!captured_||pending_||!texture)return E_INVALIDARG;
        constexpr std::array<DWORD,8> values={D3DTOP_ADD,D3DTA_CURRENT,D3DTA_TEXTURE,
            D3DTOP_MODULATE,D3DTA_CURRENT,D3DTA_TEXTURE,D3DTSS_TCI_CAMERASPACENORMAL,D3DTTFF_COUNT2};
        for(size_t i=0;i<values.size();++i){
            if(values[i]==stages_[i])continue;pending_|=1u<<i;
            auto args=pack(1,kReflectionStageStates[i],values[i]);
            const auto hr=n.SetTextureStageState(1,kReflectionStageStates[i],values[i]);notify(63,args,hr);
            if(FAILED(hr))return hr;
        }
        pending_|=1u<<8;auto args=pack(1,texture);auto hr=n.SetTexture(1,texture);notify(61,args,hr);
        if(FAILED(hr))return hr;
        pending_|=1u<<9;args=pack(0x152);hr=n.SetVertexShader(0x152);notify(76,args,hr);return hr;
    }
    // UP side effects are retained even when the driver returns failure.
    void mark_up() noexcept {if(captured_)pending_|=(1u<<10)|(1u<<11);}
    template<class Write>HRESULT restore(IDirect3DDevice8& n,Write&& notify) noexcept {
        HRESULT result=S_OK;
        for(int i=11;i>=0;--i){if(!(pending_&(1u<<i)))continue;
            HRESULT hr=E_FAIL;Args args{};uint32_t slot=0;
            if(i==11){slot=85;args=pack(indices_,base_);hr=n.SetIndices(indices_,base_);}
            else if(i==10){slot=83;args=pack(0,stream_,stride_);hr=n.SetStreamSource(0,stream_,stride_);}
            else if(i==9){slot=76;args=pack(fvf_);hr=n.SetVertexShader(fvf_);}
            else if(i==8){slot=61;args=pack(1,texture_);hr=n.SetTexture(1,texture_);}
            else{slot=63;args=pack(1,kReflectionStageStates[i],stages_[i]);hr=n.SetTextureStageState(1,kReflectionStageStates[i],stages_[i]);}
            notify(slot,args,hr);if(SUCCEEDED(hr))pending_&=~(1u<<i);else if(SUCCEEDED(result))result=hr;
        }
        if(!pending_)release();return result;
    }
};
class XtrailFidelity {
    struct Cache {std::array<uint64_t,15> key{};std::vector<XtrailDecalVertex> vertices;bool valid=false;};
    std::array<Cache,16> cache_{};size_t next_=0;
    bool requested_=false,diagnostics_=false,disabled_=false,blocked_=false;
    uint32_t logged_=0;
public:
    XtrailTransaction transaction;
    XtrailFidelity(bool supported,const std::wstring& ini) noexcept;
    bool requested() const noexcept{return requested_&&!disabled_;}
    bool blocked() const noexcept{return blocked_;}
    void disable() noexcept{disabled_=true;}
    bool claim(bool success) noexcept{const uint32_t bit=success?2u:1u;if(!diagnostics_||(logged_&bit))return false;logged_|=bit;return true;}
    const std::vector<XtrailDecalVertex>* prepare(const DrawSnapshot&) noexcept;
    void before_reset() noexcept {if(transaction.pending())blocked_=true;transaction.release();for(auto& c:cache_)c={};next_=0;}
    void after_reset(bool called,bool successful) noexcept {if(called&&successful){blocked_=false;logged_=0;}}
};
} // namespace gfx2::ps2port
