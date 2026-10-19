#pragma once
// COURSE-WATER1 (opt-in PS2Water=1, docs/course-water1): the PS2 water system on the native course draws.
//
// A native course draw whose triangles are exactly one asset key (triangle count + order-free SHA-256 of its positions,
// tools/prepare_ps2_water.py) is not submitted; the matched PS2 water triangles are drawn in its place with the two PS2
// passes of their shader (ps2_water.hpp). Same position in the frame, same depth buffer, transforms and fog as the
// native draw, so terrain/objects drawn later (cars, splashes, COURSE-ALIVE1 boats at the pre-UI boundary) are depth
// tested against the PS2 water exactly as PS2 draws them after the landscape. Draws that do not match stay native, so
// every surface has one path: PC base_water (PS2Water=0 or no key) or PS2 water.
#include "sdk.hpp"
#include "state_tracker.hpp"
#include "provenance.hpp"
#include "ps2_config.hpp"
#include "ps2_water.hpp"
#include "ps2_spline_motion.hpp"
#include <algorithm>
#include <array>
#include <cstdint>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <string>
#include <unordered_map>
#include <vector>

namespace gfx2::ps2port {

// .assets/course/PS2Water.ps2wtr (tools/prepare_ps2_water.py, 36 courses).
inline constexpr char kPS2WaterArtifactSha[]="2480f84d3120716ba9244eeeee0677e8ecffbb758e914c07087bbba2cb1c74c9";

enum class WaterStateKind : uint8_t { Render, Stage, Texture, VertexShader, Stream };
struct WaterStateOp { WaterStateKind kind; DWORD stage, key; };
inline constexpr std::array<WaterStateOp,31> kWaterOps={{
    {WaterStateKind::Render,0,D3DRS_ALPHABLENDENABLE},{WaterStateKind::Render,0,D3DRS_SRCBLEND},
    {WaterStateKind::Render,0,D3DRS_DESTBLEND},{WaterStateKind::Render,0,D3DRS_BLENDOP},
    {WaterStateKind::Render,0,D3DRS_ZWRITEENABLE},{WaterStateKind::Render,0,D3DRS_ZFUNC},
    {WaterStateKind::Render,0,D3DRS_ALPHATESTENABLE},{WaterStateKind::Render,0,D3DRS_CULLMODE},
    {WaterStateKind::Render,0,D3DRS_LIGHTING},{WaterStateKind::Render,0,D3DRS_FOGENABLE},
    {WaterStateKind::Render,0,D3DRS_SPECULARENABLE},{WaterStateKind::Render,0,D3DRS_TEXTUREFACTOR},
    {WaterStateKind::Stage,0,D3DTSS_COLOROP},{WaterStateKind::Stage,0,D3DTSS_COLORARG1},{WaterStateKind::Stage,0,D3DTSS_COLORARG2},
    {WaterStateKind::Stage,0,D3DTSS_ALPHAOP},{WaterStateKind::Stage,0,D3DTSS_ALPHAARG1},{WaterStateKind::Stage,0,D3DTSS_ALPHAARG2},
    {WaterStateKind::Stage,0,D3DTSS_TEXCOORDINDEX},{WaterStateKind::Stage,0,D3DTSS_TEXTURETRANSFORMFLAGS},
    {WaterStateKind::Stage,0,D3DTSS_ADDRESSU},{WaterStateKind::Stage,0,D3DTSS_ADDRESSV},
    {WaterStateKind::Stage,0,D3DTSS_MAGFILTER},{WaterStateKind::Stage,0,D3DTSS_MINFILTER},{WaterStateKind::Stage,0,D3DTSS_MIPFILTER},
    {WaterStateKind::Stage,1,D3DTSS_COLOROP},{WaterStateKind::Stage,1,D3DTSS_ALPHAOP},
    {WaterStateKind::Texture,0,0},{WaterStateKind::VertexShader,0,0},{WaterStateKind::Stream,0,0},
    {WaterStateKind::Render,0,D3DRS_ZENABLE},
}};
inline constexpr size_t kWaterStreamOp=29;
inline size_t water_op(WaterStateKind kind,DWORD stage,DWORD key) noexcept {
    for(size_t i=0;i<kWaterOps.size();++i)if(kWaterOps[i].kind==kind&&kWaterOps[i].stage==stage&&kWaterOps[i].key==key)return i;
    return SIZE_MAX;
}

using WaterWriter=void(*)(void*,uint32_t,const Args&,HRESULT) noexcept;

// Captures every touched native state once (tracked shadow first), writes pass values, restores in reverse order.
// A failed restore keeps the transaction pending; repair() (native_states_pending chain) finishes it.
class WaterTransaction {
    struct Saved { DWORD scalar=0; IDirect3DBaseTexture8* texture=nullptr; IDirect3DVertexBuffer8* stream=nullptr; UINT stride=0; };
    std::array<Saved,kWaterOps.size()> saved_{};
    uint64_t pending_=0; bool captured_=false;
    void* context_=nullptr; WaterWriter writer_=nullptr;
    void notify(uint32_t slot,const Args& a,HRESULT hr) noexcept {if(writer_)writer_(context_,slot,a,hr);}
    HRESULT write(IDirect3DDevice8& n,size_t i,const Saved& v) noexcept {
        const auto& op=kWaterOps[i];HRESULT hr=E_INVALIDARG;
        switch(op.kind){
        case WaterStateKind::Render:hr=n.SetRenderState(static_cast<D3DRENDERSTATETYPE>(op.key),v.scalar);notify(50,pack(op.key,v.scalar),hr);break;
        case WaterStateKind::Stage:hr=n.SetTextureStageState(op.stage,static_cast<D3DTEXTURESTAGESTATETYPE>(op.key),v.scalar);notify(63,pack(op.stage,op.key,v.scalar),hr);break;
        case WaterStateKind::Texture:hr=n.SetTexture(op.stage,v.texture);notify(61,pack(op.stage,v.texture),hr);break;
        case WaterStateKind::VertexShader:hr=n.SetVertexShader(v.scalar);notify(76,pack(v.scalar),hr);break;
        case WaterStateKind::Stream:hr=n.SetStreamSource(op.stage,v.stream,v.stride);notify(83,pack(op.stage,v.stream,v.stride),hr);break;
        }
        return hr;
    }
public:
    WaterTransaction()=default;
    ~WaterTransaction(){release();}
    WaterTransaction(const WaterTransaction&)=delete;
    WaterTransaction& operator=(const WaterTransaction&)=delete;
    void set_writer(void* context,WaterWriter writer) noexcept {context_=context;writer_=writer;}
    bool pending() const noexcept {return pending_!=0;}
    DWORD saved(size_t i) const noexcept {return i<saved_.size()?saved_[i].scalar:0;}
    void release() noexcept {for(auto& s:saved_){if(s.texture)s.texture->Release();if(s.stream)s.stream->Release();s={};}pending_=0;captured_=false;}
    HRESULT capture(IDirect3DDevice8& n,const Shadow* shadow) noexcept {
        if(pending())return D3DERR_INVALIDCALL;
        release();HRESULT hr=S_OK;
        for(size_t i=0;i<kWaterOps.size()&&SUCCEEDED(hr);++i){
            const auto& op=kWaterOps[i];auto& v=saved_[i];
            switch(op.kind){
            case WaterStateKind::Render:
                if(shadow&&op.key<shadow->rs.size()&&shadow->rs[op.key].known)v.scalar=shadow->rs[op.key].value;
                else hr=n.GetRenderState(static_cast<D3DRENDERSTATETYPE>(op.key),&v.scalar);
                break;
            case WaterStateKind::Stage:
                if(shadow&&op.stage<shadow->tss.size()&&op.key<shadow->tss[op.stage].size()&&shadow->tss[op.stage][op.key].known)v.scalar=shadow->tss[op.stage][op.key].value;
                else hr=n.GetTextureStageState(op.stage,static_cast<D3DTEXTURESTAGESTATETYPE>(op.key),&v.scalar);
                break;
            case WaterStateKind::Texture:hr=n.GetTexture(op.stage,&v.texture);break;
            case WaterStateKind::VertexShader:hr=n.GetVertexShader(&v.scalar);break;
            case WaterStateKind::Stream:hr=n.GetStreamSource(op.stage,&v.stream,&v.stride);break;
            }
        }
        if(FAILED(hr)){release();return hr;}
        captured_=true;return S_OK;
    }
    HRESULT set(IDirect3DDevice8& n,size_t i,DWORD scalar,IDirect3DBaseTexture8* texture=nullptr) noexcept {
        if(!captured_||i>=kWaterOps.size()||kWaterOps[i].kind==WaterStateKind::Stream)return E_INVALIDARG;
        const bool is_texture=kWaterOps[i].kind==WaterStateKind::Texture;
        // Not written yet and already the captured value: nothing to set or restore.
        if(!(pending_&(uint64_t(1)<<i))&&(is_texture?saved_[i].texture==texture:saved_[i].scalar==scalar))return S_OK;
        pending_|=uint64_t(1)<<i; // a failed call may still have changed native state
        Saved v{};v.scalar=scalar;v.texture=texture;
        return write(n,i,v);
    }
    // Immediately BEFORE DrawPrimitiveUP (also for a failing draw): UP resets stream 0.
    void mark_up_stream_changed() noexcept {if(captured_)pending_|=uint64_t(1)<<kWaterStreamOp;}
    HRESULT restore(IDirect3DDevice8& n) noexcept {
        HRESULT result=S_OK;
        for(size_t i=kWaterOps.size();i-- >0;){
            const uint64_t bit=uint64_t(1)<<i;if(!(pending_&bit))continue;
            const HRESULT hr=write(n,i,saved_[i]);
            if(SUCCEEDED(hr))pending_&=~bit;else if(SUCCEEDED(result))result=hr;
        }
        if(!pending_)release();
        return result;
    }
};

// Native draw identity -> asset key, valid while the buffers keep their generation and revision.
struct WaterDrawIdentity {
    uintptr_t vb=0,ib=0;uint64_t vb_generation=0,vb_revision=0,ib_generation=0,ib_revision=0;
    UINT base=0,min_index=0,vertices=0,start=0,count=0;DWORD fvf=0;UINT stride=0;size_t course=SIZE_MAX;
    uint64_t hash() const noexcept {
        uint64_t h=1469598103934665603ull;
        for(const uint64_t v:{uint64_t(vb),uint64_t(ib),vb_generation,vb_revision,ib_generation,ib_revision,uint64_t(base),uint64_t(min_index),
                              uint64_t(vertices),uint64_t(start),uint64_t(count),uint64_t(fvf),uint64_t(stride),uint64_t(course)}){h^=v;h*=1099511628211ull;}
        return h;
    }
    bool operator==(const WaterDrawIdentity& o) const noexcept {
        return vb==o.vb&&ib==o.ib&&vb_generation==o.vb_generation&&vb_revision==o.vb_revision&&ib_generation==o.ib_generation&&
            ib_revision==o.ib_revision&&base==o.base&&min_index==o.min_index&&vertices==o.vertices&&start==o.start&&count==o.count&&
            fvf==o.fvf&&stride==o.stride&&course==o.course;
    }
};

class PS2WaterPilot {
    bool requested_=false,verified_=false,disabled_=false,blocked_=false,diagnostics_=false;
    const char* reason_="stock_default";
    ps2water::Asset asset_;
    std::vector<IDirect3DTexture8*> textures_;
    std::vector<uint8_t> counts_;                        // triangle count -> 1 when any key has it (cheap pre-filter)
    std::vector<std::vector<uint32_t>> course_counts_;   // sorted triangle counts of each course's keys
    struct CacheEntry { WaterDrawIdentity id; size_t key=SIZE_MAX; };
    // Every native draw identity seen with a candidate triangle count (water or not); static course buffers keep their
    // revision, so each is hashed once per course load.
    std::unordered_map<uint64_t,CacheEntry> cache_;
    ps2water::Clock clock_;
    uint64_t clock_frame_=UINT64_MAX,last_qpc_=0;
    uint64_t owned_race_=0;size_t owned_course_=SIZE_MAX;
    std::array<const char*,48> logged_{};size_t logged_count_=0;
    std::vector<uint8_t> course_logged_;
    uint64_t replaced_=0,passes_=0;
    IDirect3DDevice8* caps_device_=nullptr;bool caps_ok_=false;
    void release_textures() noexcept {for(auto* t:textures_)if(t)t->Release();textures_.clear();}
public:
    WaterTransaction transaction;
    std::vector<ps2water::PassVertex> first,second;     // per part scratch, reused
    std::vector<float> positions;std::vector<uint8_t> canonical;

    PS2WaterPilot(bool supported,const std::wstring& ini) noexcept {
        if(!supported){reason_="unsupported_build_stock";return;}
        try{
            if(config::read_int(L"PS2Water",0,ini.c_str())!=1)return;
            requested_=true;
            diagnostics_=config::read_int(L"Diagnostics",0,ini.c_str())==1||config::read_int(L"PS2WaterDiagnostics",0,ini.c_str())==1;
            wchar_t dir[32768]{},path[32768]{};
            config::read_string(L"GrassAssetDirectory",L".",dir,32768,ini.c_str());
            const std::wstring fallback=std::wstring(dir)+L"\\PS2Water.ps2wtr";
            const auto count=config::read_string(L"PS2WaterAsset",fallback.c_str(),path,32768,ini.c_str());
            if(!count||count>=32767){reason_="invalid_water_asset_path";return;}
            std::filesystem::path input(path);if(input.is_relative())input=std::filesystem::path(ini).parent_path()/input;
            std::ifstream file(input,std::ios::binary|std::ios::ate);
            if(!file){reason_="missing_water_asset";return;}
            const auto size=static_cast<std::streamoff>(file.tellg());
            if(size<=0||static_cast<uint64_t>(size)>ps2water::kMaximumAssetBytes){reason_="wrong_size_water_asset";return;}
            std::vector<uint8_t> bytes(static_cast<size_t>(size));file.seekg(0);file.read(reinterpret_cast<char*>(bytes.data()),size);
            verified_=file&&sha256_bytes(bytes.data(),bytes.size())==kPS2WaterArtifactSha&&ps2water::decode_asset(bytes.data(),bytes.size(),asset_);
            reason_=verified_?"verified_water_waiting_for_device":"water_asset_hash_or_layout_mismatch";
            if(verified_){
                counts_.assign(65536,0);for(const auto& k:asset_.keys)counts_[k.triangles]=1;
                for(const auto& c:asset_.courses){
                    std::vector<uint32_t> v;for(uint32_t i=0;i<c.keys;++i)v.push_back(asset_.keys[c.first_key+i].triangles);
                    std::sort(v.begin(),v.end());v.erase(std::unique(v.begin(),v.end()),v.end());course_counts_.push_back(std::move(v));
                }
                course_logged_.assign(asset_.courses.size(),0);
            }
        }catch(...){verified_=false;asset_={};reason_="water_asset_load_failed_stock";}
    }
    ~PS2WaterPilot(){shutdown();}
    PS2WaterPilot(const PS2WaterPilot&)=delete;
    PS2WaterPilot& operator=(const PS2WaterPilot&)=delete;
    bool requested() const noexcept {return requested_;}
    bool identity_requested() const noexcept {return requested_&&verified_&&!disabled_;}
    bool active() const noexcept {return identity_requested()&&!blocked_&&!textures_.empty();}
    bool blocked() const noexcept {return blocked_;}
    bool diagnostics() const noexcept {return diagnostics_;}
    const char* reason() const noexcept {return reason_;}
    const ps2water::Asset& asset() const noexcept {return asset_;}
    IDirect3DTexture8* texture(uint32_t i) const noexcept {return i<textures_.size()?textures_[i]:nullptr;}
    bool candidate(UINT triangles) const noexcept {return triangles<counts_.size()&&counts_[triangles];}
    bool course_candidate(size_t c,UINT triangles) const noexcept {
        return c<course_counts_.size()&&std::binary_search(course_counts_[c].begin(),course_counts_[c].end(),uint32_t(triangles));
    }
    uint64_t replaced() const noexcept {return replaced_;}
    uint64_t passes() const noexcept {return passes_;}
    void count(uint64_t passes) noexcept {++replaced_;passes_+=passes;}
    float phase() const noexcept {return clock_.t();}
    uint32_t counter() const noexcept {return clock_.counter();}
    void disable(const char* reason) noexcept {disabled_=true;reason_=reason;}

    bool caps_ok(IDirect3DDevice8& n) noexcept {
        if(caps_device_!=&n){
            D3DCAPS8 caps{};caps_device_=&n;
            caps_ok_=SUCCEEDED(n.GetDeviceCaps(&caps))&&(caps.SrcBlendCaps&D3DPBLENDCAPS_SRCALPHA)&&(caps.DestBlendCaps&D3DPBLENDCAPS_INVSRCALPHA)&&
                (caps.DestBlendCaps&D3DPBLENDCAPS_ONE)&&(caps.TextureOpCaps&D3DTEXOPCAPS_MODULATE)&&(caps.TextureOpCaps&D3DTEXOPCAPS_SELECTARG1)&&
                caps.MaxPrimitiveCount>=65535&&caps.MaxTextureWidth>=512&&caps.MaxTextureHeight>=512;
        }
        return caps_ok_;
    }
    // Managed textures with a box-filtered mip chain; they survive Reset.
    bool initialize(IDirect3DDevice8& n) noexcept {
        if(!identity_requested())return false;
        if(!textures_.empty())return true;
        if(!caps_ok(n)){disable("unsupported_water_device_caps");return false;}
        try{
            for(const auto& t:asset_.textures){
                IDirect3DTexture8* texture=nullptr;
                if(FAILED(n.CreateTexture(t.width,t.height,0,0,D3DFMT_A8R8G8B8,D3DPOOL_MANAGED,&texture))||!texture){
                    if(texture)texture->Release();release_textures();disable("water_texture_creation_failed");return false;}
                textures_.push_back(texture);
                std::vector<uint32_t> level=t.argb;uint32_t w=t.width,h=t.height;
                const DWORD levels=texture->GetLevelCount();
                for(DWORD l=0;l<levels;++l){
                    D3DLOCKED_RECT lock{};if(FAILED(texture->LockRect(l,&lock,nullptr,0))){release_textures();disable("water_texture_upload_failed");return false;}
                    const bool good=lock.pBits&&lock.Pitch>=INT(w*4);
                    if(good)for(uint32_t y=0;y<h;++y)std::memcpy(static_cast<uint8_t*>(lock.pBits)+size_t(y)*lock.Pitch,level.data()+size_t(y)*w,size_t(w)*4);
                    const HRESULT unlocked=texture->UnlockRect(l);
                    if(!good||FAILED(unlocked)){release_textures();disable("water_texture_upload_failed");return false;}
                    if(w>1||h>1){level=ps2water::half_level(level,w,h);w=w>1?w/2:1;h=h>1?h/2:1;}
                }
            }
        }catch(...){release_textures();disable("water_texture_creation_failed");return false;}
        reason_="water_ready";return true;
    }
    size_t course(std::string_view id) const noexcept {return ps2water::course_index(asset_,id);}
    // Cached key of a native draw, or SIZE_MAX for a known miss; found=false when the identity was not seen yet.
    size_t cached(const WaterDrawIdentity& id,bool& found) const noexcept {
        const auto i=cache_.find(id.hash());
        found=i!=cache_.end()&&i->second.id==id;return found?i->second.key:SIZE_MAX;
    }
    void remember(const WaterDrawIdentity& id,size_t key) noexcept {
        try{if(cache_.size()>=16384)cache_.clear();cache_[id.hash()]={id,key};}catch(...){cache_.clear();}
    }
    // The key of course c with this triangle count and SHA-256 (hex), or SIZE_MAX.
    size_t match(size_t c,UINT triangles,const std::string& sha_hex) const noexcept {
        if(c>=asset_.courses.size()||sha_hex.size()!=64)return SIZE_MAX;
        const auto& course=asset_.courses[c];
        for(uint32_t i=0;i<course.keys;++i){
            const auto& k=asset_.keys[course.first_key+i];if(k.triangles!=triangles)continue;
            static constexpr char hex[]="0123456789abcdef";bool same=true;
            for(size_t b=0;b<32&&same;++b)same=sha_hex[2*b]==hex[k.sha[b]>>4]&&sha_hex[2*b+1]==hex[k.sha[b]&15];
            if(same)return course.first_key+i;
        }
        return SIZE_MAX;
    }
    // Once per frame: host time -> PS2 renderer counter (frozen while paused).
    void advance(uint64_t frame,bool paused) noexcept {
        if(clock_frame_==frame)return;
        clock_frame_=frame;
        LARGE_INTEGER now{},frequency{};QueryPerformanceCounter(&now);QueryPerformanceFrequency(&frequency);
        const uint64_t previous=last_qpc_;last_qpc_=static_cast<uint64_t>(now.QuadPart);
        if(!previous||frequency.QuadPart<=0)return;
        clock_.advance(double(static_cast<uint64_t>(now.QuadPart)-previous)/double(frequency.QuadPart),paused);
    }
    // COURSE-ALIVE1 / course objects: the PS2 water of this course and race is drawn by this pilot.
    void note_owned(size_t c,uint64_t race) noexcept {owned_course_=c;owned_race_=race;}
    bool owns(std::string_view course_id,uint64_t race) const noexcept {
        return active()&&race&&owned_race_==race&&owned_course_!=SIZE_MAX&&owned_course_==course(course_id);
    }
    bool claim_course_log(size_t c) noexcept {if(!diagnostics_||c>=course_logged_.size()||course_logged_[c])return false;course_logged_[c]=1;return true;}
    bool note_reason(const char* reason) noexcept {
        if(!reason||!diagnostics_)return false;
        for(size_t i=0;i<logged_count_;++i)if(logged_[i]==reason||!std::strcmp(logged_[i],reason))return false;
        if(logged_count_>=logged_.size())return false;
        logged_[logged_count_++]=reason;return true;
    }
    void before_reset() noexcept {
        if(transaction.pending())blocked_=true;
        transaction.release();
        cache_.clear();               // buffers are re-proved after a reset
    }
    void after_reset(IDirect3DDevice8& n,bool called,bool success) noexcept {
        if(!called)return;
        if(success){blocked_=false;initialize(n);}
    }
    void shutdown() noexcept {transaction.release();release_textures();disabled_=true;}
};

} // namespace gfx2::ps2port
