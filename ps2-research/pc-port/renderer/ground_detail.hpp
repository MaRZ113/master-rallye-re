#pragma once
// Opt-in GroundDetail (default 0): the PS2 ground detail contract on PC `shader/base_noise` draws.
//
// PS2 ground (shader mode 4) = fog(texture x prelight) - CommonTextures/NOISE (second GS pass, DECAL,
// ALPHA Cd-Cs, unfogged); PC base_noise = texture x diffuse x 2 x noise-tga (stage1 MODULATE2X).
// Evidence: ps2-research/course-light1/findings.md (EE 312610 mode 4, PC 585ac0, PCSX2 GS dumps).
// The draw keeps its own geometry, UV sets, fog and depth; only the noise term changes:
//   pass 1: original states with stage1 disabled
//   pass 2: same geometry, PS2 noise in stage0 on the PC noise UV set, dest - src, no fog, no Z write
#include "sdk.hpp"
#include "state_tracker.hpp"
#include "provenance.hpp"
#include "ps2_config.hpp"
#include <array>
#include <cstdint>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <string>
#include <vector>

namespace gfx2::ps2port {

// \TNG\DATAPSM\COMMONTEXTURES\NOISE.GXI (tools/prepare_ground_noise_asset.py).
inline constexpr char kGroundNoiseGxiSha[]="a9311356c962bb241fcdd5fd806b8733e513e62c637537109bf669ce9a482e92";
inline constexpr size_t kGroundNoiseGxiSize=8+128*128*4;
// PC DataGx/Course/*/noise-tga.dxt (identical on all 36 courses): level 0 as BGRA rows, alpha 0xff.
inline constexpr char kPcNoiseLevel0Sha[]="4325c7d4c3a8c00da87b1cbf65e0338ffbf35948f32596d1fb32bf8a0a6ce339";
inline constexpr UINT kGroundNoiseSize=128;

// GXI 0x13039 RGBA -> D3D A8R8G8B8 words; the alpha is unused by the pass and set opaque.
inline bool decode_ground_noise(const std::vector<uint8_t>& gxi,std::vector<DWORD>& out) noexcept {
    try {
        out.clear();
        if(gxi.size()!=kGroundNoiseGxiSize||sha256_bytes(gxi.data(),gxi.size())!=kGroundNoiseGxiSha)return false;
        uint32_t magic=0;uint16_t w=0,h=0;std::memcpy(&magic,gxi.data(),4);std::memcpy(&w,gxi.data()+4,2);std::memcpy(&h,gxi.data()+6,2);
        if(magic!=0x13039||w!=kGroundNoiseSize||h!=kGroundNoiseSize)return false;
        out.resize(size_t(w)*h);
        for(size_t i=0;i<out.size();++i){const auto* c=gxi.data()+8+4*i;out[i]=0xff000000u|(DWORD(c[0])<<16)|(DWORD(c[1])<<8)|c[2];}
        return true;
    } catch(...) { out.clear(); return false; }
}

// 2x2 box reduction; the subtracted mean stays the same on every level.
inline std::vector<DWORD> ground_noise_half(const std::vector<DWORD>& src,UINT w) {
    const UINT h=w/2;std::vector<DWORD> dst(size_t(h)*h);
    for(UINT y=0;y<h;++y)for(UINT x=0;x<h;++x){
        DWORD sum[3]{};
        for(UINT dy=0;dy<2;++dy)for(UINT dx=0;dx<2;++dx){const DWORD p=src[size_t(2*y+dy)*w+2*x+dx];sum[0]+=(p>>16)&0xff;sum[1]+=(p>>8)&0xff;sum[2]+=p&0xff;}
        dst[size_t(y)*h+x]=0xff000000u|(((sum[0]+2)/4)<<16)|(((sum[1]+2)/4)<<8)|((sum[2]+2)/4);
    }
    return dst;
}

// Hash of a locked 128x128 32-bit level in the PC file layout (BGRA bytes, alpha forced for X8R8G8B8).
inline std::string pc_noise_level0_sha(const BYTE* bits,INT pitch,D3DFORMAT format) noexcept {
    try {
        if(!bits||pitch<INT(kGroundNoiseSize*4)||(format!=D3DFMT_A8R8G8B8&&format!=D3DFMT_X8R8G8B8))return {};
        std::vector<BYTE> rows(size_t(kGroundNoiseSize)*kGroundNoiseSize*4);
        for(UINT y=0;y<kGroundNoiseSize;++y)std::memcpy(rows.data()+size_t(y)*kGroundNoiseSize*4,bits+size_t(y)*pitch,kGroundNoiseSize*4);
        if(format==D3DFMT_X8R8G8B8)for(size_t i=3;i<rows.size();i+=4)rows[i]=0xff;
        return sha256_bytes(rows.data(),rows.size());
    } catch(...) { return {}; }
}

enum class GroundStateKind : uint8_t { Render, Stage, Texture };
struct GroundStateOp { GroundStateKind kind; DWORD stage, key; };
inline constexpr std::array<GroundStateOp,22> kGroundOps={{
    {GroundStateKind::Stage,1,D3DTSS_COLOROP},{GroundStateKind::Stage,1,D3DTSS_ALPHAOP},
    {GroundStateKind::Render,0,D3DRS_ALPHABLENDENABLE},{GroundStateKind::Render,0,D3DRS_SRCBLEND},
    {GroundStateKind::Render,0,D3DRS_DESTBLEND},{GroundStateKind::Render,0,D3DRS_BLENDOP},
    {GroundStateKind::Render,0,D3DRS_ZWRITEENABLE},{GroundStateKind::Render,0,D3DRS_ZFUNC},
    {GroundStateKind::Render,0,D3DRS_FOGENABLE},{GroundStateKind::Render,0,D3DRS_SPECULARENABLE},
    {GroundStateKind::Stage,0,D3DTSS_COLOROP},{GroundStateKind::Stage,0,D3DTSS_COLORARG1},
    {GroundStateKind::Stage,0,D3DTSS_ALPHAOP},{GroundStateKind::Stage,0,D3DTSS_ALPHAARG1},
    {GroundStateKind::Stage,0,D3DTSS_TEXCOORDINDEX},{GroundStateKind::Stage,0,D3DTSS_ADDRESSU},
    {GroundStateKind::Stage,0,D3DTSS_ADDRESSV},{GroundStateKind::Stage,0,D3DTSS_MAGFILTER},
    {GroundStateKind::Stage,0,D3DTSS_MINFILTER},{GroundStateKind::Stage,0,D3DTSS_MIPFILTER},
    {GroundStateKind::Stage,0,D3DTSS_TEXTURETRANSFORMFLAGS},{GroundStateKind::Texture,0,0},
}};
inline constexpr size_t kGroundPass1Ops=2;  // stage1 COLOROP/ALPHAOP

using GroundWriter=void(*)(void*,uint32_t,const Args&,HRESULT) noexcept;

// Captures every touched native state once, writes pass values, restores in reverse order. A failed
// restore keeps the transaction pending; repair() (native_states_pending chain) finishes it.
class GroundDetailTransaction {
    struct Saved { DWORD scalar=0; IDirect3DBaseTexture8* texture=nullptr; };
    std::array<Saved,kGroundOps.size()> saved_{};
    uint32_t pending_=0;
    bool captured_=false;
    void* context_=nullptr; GroundWriter writer_=nullptr;
    void notify(uint32_t slot,const Args& a,HRESULT hr) noexcept {if(writer_)writer_(context_,slot,a,hr);}
    HRESULT write(IDirect3DDevice8& n,size_t i,DWORD scalar,IDirect3DBaseTexture8* texture) noexcept {
        const auto& op=kGroundOps[i];HRESULT hr=E_INVALIDARG;
        switch(op.kind){
        case GroundStateKind::Render:hr=n.SetRenderState(static_cast<D3DRENDERSTATETYPE>(op.key),scalar);notify(50,pack(op.key,scalar),hr);break;
        case GroundStateKind::Stage:hr=n.SetTextureStageState(op.stage,static_cast<D3DTEXTURESTAGESTATETYPE>(op.key),scalar);notify(63,pack(op.stage,op.key,scalar),hr);break;
        case GroundStateKind::Texture:hr=n.SetTexture(op.stage,texture);notify(61,pack(op.stage,texture),hr);break;
        }
        return hr;
    }
public:
    GroundDetailTransaction()=default;
    ~GroundDetailTransaction(){release();}
    GroundDetailTransaction(const GroundDetailTransaction&)=delete;
    GroundDetailTransaction& operator=(const GroundDetailTransaction&)=delete;
    void set_writer(void* context,GroundWriter writer) noexcept {context_=context;writer_=writer;}
    bool pending() const noexcept {return pending_!=0;}
    DWORD saved(size_t i) const noexcept {return saved_[i].scalar;}
    void release() noexcept {for(auto& s:saved_){if(s.texture)s.texture->Release();s={};}pending_=0;captured_=false;}
    HRESULT capture(IDirect3DDevice8& n) noexcept {
        if(pending())return D3DERR_INVALIDCALL;
        release();HRESULT hr=S_OK;
        for(size_t i=0;i<kGroundOps.size()&&SUCCEEDED(hr);++i){
            const auto& op=kGroundOps[i];auto& v=saved_[i];
            switch(op.kind){
            case GroundStateKind::Render:hr=n.GetRenderState(static_cast<D3DRENDERSTATETYPE>(op.key),&v.scalar);break;
            case GroundStateKind::Stage:hr=n.GetTextureStageState(op.stage,static_cast<D3DTEXTURESTAGESTATETYPE>(op.key),&v.scalar);break;
            case GroundStateKind::Texture:hr=n.GetTexture(op.stage,&v.texture);break;
            }
        }
        if(FAILED(hr)){release();return hr;}
        captured_=true;return S_OK;
    }
    HRESULT set(IDirect3DDevice8& n,size_t i,DWORD scalar,IDirect3DBaseTexture8* texture=nullptr) noexcept {
        if(!captured_||i>=kGroundOps.size())return E_INVALIDARG;
        pending_|=1u<<i; // a failed call may still have changed native state
        return write(n,i,scalar,texture);
    }
    HRESULT restore(IDirect3DDevice8& n) noexcept {
        HRESULT result=S_OK;
        for(size_t i=kGroundOps.size();i-- >0;){
            const uint32_t bit=1u<<i;if(!(pending_&bit))continue;
            const HRESULT hr=write(n,i,saved_[i].scalar,saved_[i].texture);
            if(SUCCEEDED(hr))pending_&=~bit;else if(SUCCEEDED(result))result=hr;
        }
        if(!pending_)release();
        return result;
    }
};

struct GroundNoiseIdentity { uintptr_t texture=0; uint64_t generation=0; bool match=false; const char* reason=""; };

class GroundDetail {
    bool requested_=false,disabled_=false,diagnostics_=false;
    std::vector<DWORD> pixels_;
    IDirect3DTexture8* texture_=nullptr;
    std::array<GroundNoiseIdentity,8> identities_{};
    size_t next_identity_=0;
    std::array<const char*,32> logged_{};
    size_t logged_count_=0;
    uint64_t passes_=0;
    const char* startup_reason_=nullptr;
public:
    GroundDetailTransaction transaction;
    GroundDetail(bool supported,const std::wstring& ini) noexcept {
        if(!supported)return;
        try{
            if(config::read_int(L"GroundDetail",0,ini.c_str())!=1)return;
            diagnostics_=config::read_int(L"Diagnostics",0,ini.c_str())==1;
            wchar_t filename[32768]{};
            config::read_string(L"GroundDetailAsset",L"PS2Grass\\PS2GroundNoise.gxi",filename,32768,ini.c_str());
            auto path=std::filesystem::path(filename);if(path.is_relative())path=std::filesystem::path(ini).parent_path()/path;
            std::ifstream file(path,std::ios::binary);std::vector<uint8_t> bytes((std::istreambuf_iterator<char>(file)),{});
            requested_=decode_ground_noise(bytes,pixels_);
            if(!requested_)startup_reason_="ground_noise_asset_missing_or_mismatch";
        }catch(...){requested_=false;pixels_.clear();}
    }
    ~GroundDetail(){transaction.release();if(texture_)texture_->Release();}
    GroundDetail(const GroundDetail&)=delete;
    GroundDetail& operator=(const GroundDetail&)=delete;
    bool requested() const noexcept {return requested_&&!disabled_;}
    void disable() noexcept {disabled_=true;}
    uint64_t passes() const noexcept {return passes_;}
    void count_pass() noexcept {++passes_;}
    IDirect3DTexture8* texture() const noexcept {return texture_;}
    // The first occurrence of each outcome is reported once (bounded).
    bool note_reason(const char* reason) noexcept {
        if(!reason)return false;
        for(size_t i=0;i<logged_count_;++i)if(logged_[i]==reason||!std::strcmp(logged_[i],reason))return false;
        if(logged_count_>=logged_.size())return false;
        logged_[logged_count_++]=reason;return true;
    }
    bool initialize(IDirect3DDevice8& n) noexcept {
        if(texture_)return true;
        if(!requested())return false;
        if(FAILED(n.CreateTexture(kGroundNoiseSize,kGroundNoiseSize,0,0,D3DFMT_A8R8G8B8,D3DPOOL_MANAGED,&texture_))||!texture_){texture_=nullptr;disable();return false;}
        try{
            std::vector<DWORD> level=pixels_;UINT w=kGroundNoiseSize;
            const DWORD levels=texture_->GetLevelCount();
            for(DWORD l=0;l<levels&&w>0;++l){
                D3DLOCKED_RECT lock{};if(FAILED(texture_->LockRect(l,&lock,nullptr,0))){texture_->Release();texture_=nullptr;disable();return false;}
                const bool good=lock.pBits&&lock.Pitch>=INT(w*4);
                if(good)for(UINT y=0;y<w;++y)std::memcpy(static_cast<BYTE*>(lock.pBits)+size_t(y)*lock.Pitch,level.data()+size_t(y)*w,w*4);
                const HRESULT unlocked=texture_->UnlockRect(l);
                if(!good||FAILED(unlocked)){texture_->Release();texture_=nullptr;disable();return false;}
                if(w>1){level=ground_noise_half(level,w);w/=2;}
            }
        }catch(...){if(texture_)texture_->Release();texture_=nullptr;disable();return false;}
        return true;
    }
    // Content identity of the PC noise texture bound to stage1, cached per resource generation.
    GroundNoiseIdentity identify(IDirect3DBaseTexture8* base,uint64_t generation) noexcept {
        const auto id=reinterpret_cast<uintptr_t>(base);
        if(!base||!generation)return {id,generation,false,"stage1_texture_untracked"};
        for(const auto& c:identities_)if(c.texture==id&&c.generation==generation)return c;
        GroundNoiseIdentity result{id,generation,false,"pc_noise_content_mismatch"};
        if(base->GetType()!=D3DRTYPE_TEXTURE)result.reason="stage1_not_2d_texture";
        else{
            auto* t=static_cast<IDirect3DTexture8*>(base);D3DSURFACE_DESC desc{};
            if(FAILED(t->GetLevelDesc(0,&desc)))result.reason="stage1_level_desc_failed";
            else if(desc.Width!=kGroundNoiseSize||desc.Height!=kGroundNoiseSize)result.reason="stage1_not_128x128";
            else if(desc.Format!=D3DFMT_A8R8G8B8&&desc.Format!=D3DFMT_X8R8G8B8)result.reason="pc_noise_format_not_32bit";
            else if(desc.Pool==D3DPOOL_DEFAULT)result.reason="pc_noise_not_lockable";
            else{
                D3DLOCKED_RECT lock{};
                if(FAILED(t->LockRect(0,&lock,nullptr,D3DLOCK_READONLY)))result.reason="pc_noise_lock_failed";
                else{
                    const auto sha=pc_noise_level0_sha(static_cast<const BYTE*>(lock.pBits),lock.Pitch,desc.Format);
                    t->UnlockRect(0);
                    if(sha==kPcNoiseLevel0Sha){result.match=true;result.reason="exact_pc_noise_tga";}
                }
            }
        }
        identities_[next_identity_]=result;next_identity_=(next_identity_+1)%identities_.size();
        return result;
    }
    bool diagnostics() const noexcept {return diagnostics_;}
    // Set when GroundDetail=1 but the PS2 asset is unusable; reported once by the native layer.
    const char* take_startup_reason() noexcept {const char* r=startup_reason_;startup_reason_=nullptr;return r;}
};

}  // namespace gfx2::ps2port
