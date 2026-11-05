#pragma once
// ATMOSPHERE2.4: current-frame GPU depth visibility. No depth readback,
// temporal visibility, geometry allowlist, query extension or dinput dependency.
#include "sdk.hpp"
#include "state_tracker.hpp"
#include "atmosphere_scene.hpp"
#include <bitset>
#include <filesystem>
#include <fstream>

namespace gfx2::atmosphere {
template<class T> inline void sun_drop(T*& p)noexcept{if(p)p->Release();p=nullptr;}
// ATMOSPHERE2.5 GT3-inspired sun look (procedural, no GT3 assets): a hot
// near-white core, a warm glow, a wide soft bloom and a thin radial starburst.
// Sizes are angular (degrees of view), so the sun keeps its size at any
// resolution/FOV. Intensities are additive weights. All values are tunable
// in Atmosphere.ini and re-read by LiveTuning.
struct SunStyle {
    float core_degrees=.9f,glow_degrees=9.f,bloom_degrees=28.f,ray_degrees=22.f;
    float core=1.f,glow=.95f,bloom=.55f,rays=.45f,flare=.35f;
    unsigned ray_count=72;std::wstring ray_texture;   // optional 256x256 BGRA sprite (SDK tools/atmosphere_sun_sprite.py)
    std::array<float,3> core_rgb{1.f,.98f,.9f},glow_rgb{1.f,.8f,.4f},bloom_rgb{1.f,.6f,.26f};
    float dither=0,vignette=0;bool soft_ghosts=false;
};
inline SunStyle read_sun_style(const std::wstring& ini) {
    SunStyle s;
    auto number=[&](const wchar_t* key,float fallback,float lo,float hi){wchar_t b[64]{};GetPrivateProfileStringW(L"Atmosphere",key,L"",b,64,ini.c_str());
        wchar_t* end=nullptr;const float v=std::wcstof(b,&end);return end!=b&&*end==0&&std::isfinite(v)?std::clamp(v,lo,hi):fallback;};
    s.core_degrees=number(L"SunCoreSize",s.core_degrees,.1f,10.f);s.glow_degrees=number(L"SunGlowSize",s.glow_degrees,.2f,30.f);
    s.bloom_degrees=number(L"SunBloomSize",s.bloom_degrees,.5f,60.f);s.ray_degrees=number(L"SunRaySize",s.ray_degrees,.5f,60.f);
    s.core=number(L"SunCoreIntensity",s.core,0.f,2.f);s.glow=number(L"SunGlowIntensity",s.glow,0.f,2.f);s.bloom=number(L"SunBloomIntensity",s.bloom,0.f,2.f);
    s.rays=number(L"SunRayIntensity",s.rays,0.f,2.f);s.flare=number(L"SunFlareIntensity",s.flare,0.f,2.f);
    s.ray_count=2u*unsigned(std::lround(number(L"SunRays",float(s.ray_count),4.f,128.f)*.5f)); // even: alternating spokes stay seamless
    s.dither=GetPrivateProfileIntW(L"Atmosphere",L"SunHaloDither",0,ini.c_str())==1?number(L"SunDitherStrength",1,0,2):0;
    s.soft_ghosts=GetPrivateProfileIntW(L"Atmosphere",L"LensSoftGhosts",0,ini.c_str())==1;
    s.vignette=GetPrivateProfileIntW(L"Atmosphere",L"Vignette",0,ini.c_str())==1?number(L"VignetteStrength",.10f,0,.3f):0;
    const wchar_t* keys[3][3]={{L"SunCoreR",L"SunCoreG",L"SunCoreB"},{L"SunGlowR",L"SunGlowG",L"SunGlowB"},{L"SunBloomR",L"SunBloomG",L"SunBloomB"}};
    for(unsigned i=0;i<3;++i){s.core_rgb[i]=number(keys[0][i],s.core_rgb[i],0.f,1.f);s.glow_rgb[i]=number(keys[1][i],s.glow_rgb[i],0.f,1.f);s.bloom_rgb[i]=number(keys[2][i],s.bloom_rgb[i],0.f,1.f);}
    wchar_t path[512]{};GetPrivateProfileStringW(L"Atmosphere",L"SunRaysTexture",L"",path,512,ini.c_str());
    if(path[0]){std::filesystem::path p(path);if(p.is_relative())p=std::filesystem::path(ini).parent_path()/p;s.ray_texture=p.wstring();}
    return s;
}
// Starburst profile: many soft spokes with pseudo-random length and strength
// plus a faint radial haze (GT3 Miata reference: rays read as a warm fan, not
// as evenly spaced lines). r and angle in sprite space (r=1 at the edge).
inline float sun_ray_hash(unsigned k,float salt)noexcept{const float x=std::sin(float(k)*12.9898f+salt*78.233f)*43758.5453f;return x-std::floor(x);}
inline float sun_ray_profile(float r,float angle,unsigned rays)noexcept {
    if(r>=1||r<=0||!rays)return 0;
    const float sector=6.2831853f/float(rays);const float k=std::floor(angle/sector+.5f);
    const float offset=std::abs(angle-k*sector)/sector;                  // 0 at the spoke centre, .5 between spokes
    const unsigned spoke=unsigned(int(k)%int(rays)+int(rays))%rays;      // seamless at the 0/2pi wrap
    const float length=.3f+.7f*std::pow(sun_ray_hash(spoke,1),.7f),strength=.3f+.7f*sun_ray_hash(spoke,2);
    const float haze=.18f*std::pow(1-r,3.f);
    const float spike=r<length?strength*std::exp(-offset*offset*30.f)*std::pow(1-r/length,2.2f):0.f;
    return (spike+haze)*std::clamp(r*10.f,0.f,1.f);                      // core region left to the disk
}
struct SunPosition {float x=0,y=0,radius=0,edge=0,pixels_per_tan=0;
    float pixels(float degrees)const noexcept{return std::tan(degrees*.017453293f)*pixels_per_tan;}};
inline bool sun_position(const std::array<float,3>& direction,const D3DMATRIX& view,const D3DMATRIX& projection,UINT width,UINT height,SunPosition& out,float core_degrees=.9f)noexcept {
    out={};if(!width||!height)return false;
    const auto* v=&view._11;const auto* p=&projection._11;for(unsigned i=0;i<16;++i)if(!std::isfinite(v[i])||!std::isfinite(p[i]))return false;
    if(projection._11<=0||projection._22<=0||projection._34!=1||projection._44!=0)return false;
    float length=0;for(float x:direction){if(!std::isfinite(x))return false;length+=x*x;}if(length<1e-8f)return false;
    const float x=direction[0]*view._11+direction[1]*view._21+direction[2]*view._31;
    const float y=direction[0]*view._12+direction[1]*view._22+direction[2]*view._32;
    const float z=direction[0]*view._13+direction[1]*view._23+direction[2]*view._33;
    if(z<=.01f*std::sqrt(length))return false;
    const float w=x*projection._14+y*projection._24+z*projection._34;if(!std::isfinite(w)||w<=0)return false;
    const float nx=(x*projection._11+y*projection._21+z*projection._31)/w,ny=(x*projection._12+y*projection._22+z*projection._32)/w;
    if(!std::isfinite(nx)||!std::isfinite(ny)||std::abs(nx)>=.98f||std::abs(ny)>=.98f)return false;
    out.x=(nx+1)*width*.5f;out.y=(1-ny)*height*.5f;
    out.pixels_per_tan=height*.5f*projection._22;
    out.radius=std::clamp(out.pixels(core_degrees),2.f,height*.2f);
    out.edge=std::clamp((1-std::max(std::abs(nx),std::abs(ny)))*6.f,0.f,1.f);
    return out.x>out.radius+2&&out.y>out.radius+2&&out.x+out.radius+2<width&&out.y+out.radius+2<height;
}
struct SunProof {
    uint64_t frame=UINT64_MAX,race=0,owner=0,reset=0;uintptr_t camera=0;
    D3DMATRIX view{},projection{};IDirect3DSurface8 *target=nullptr,*depth=nullptr;
    bool world=false;
    void clear()noexcept{sun_drop(target);sun_drop(depth);world=false;frame=UINT64_MAX;}
    ~SunProof(){clear();}
};

// Every touched state is individually retained until successful restoration.
// A failed restore blocks forwarding through the existing repair chain.
using SunWriter=void(*)(void*,uint32_t,const Args&,HRESULT)noexcept;
class SunTransaction {
    struct Op {unsigned kind,stage,key;DWORD value=0;IDirect3DBaseTexture8* texture=nullptr;bool pending=false;};
    std::vector<Op> ops_;
    IDirect3DSurface8 *target_=nullptr,*depth_=nullptr;IDirect3DVertexBuffer8* stream_=nullptr;
    D3DVIEWPORT8 viewport_{};UINT stride_=0;
    bool target_pending_=false,viewport_pending_=false,stream_pending_=false,captured_=false;
    void* context_=nullptr;SunWriter writer_=nullptr;
    void notify(uint32_t slot,const Args& args,HRESULT hr)noexcept{if(writer_)writer_(context_,slot,args,hr);}
    HRESULT write(IDirect3DDevice8& n,const Op& o,DWORD v,IDirect3DBaseTexture8* t=nullptr)noexcept{
        HRESULT hr=E_FAIL;switch(o.kind){
        case 0:hr=n.SetRenderState(D3DRENDERSTATETYPE(o.key),v);notify(50,pack(o.key,v),hr);break;
        case 1:hr=n.SetTextureStageState(o.stage,D3DTEXTURESTAGESTATETYPE(o.key),v);notify(63,pack(o.stage,o.key,v),hr);break;
        case 2:hr=n.SetTexture(o.stage,t);notify(61,pack(o.stage,t),hr);break;
        case 3:hr=n.SetVertexShader(v);notify(76,pack(v),hr);break;
        case 4:hr=n.SetPixelShader(v);notify(88,pack(v),hr);break;
        }return hr;
    }
public:
    ~SunTransaction(){release();}
    bool pending()const noexcept{if(target_pending_||viewport_pending_||stream_pending_)return true;for(const auto& o:ops_)if(o.pending)return true;return false;}
    void release()noexcept{for(auto& o:ops_)sun_drop(o.texture);ops_.clear();sun_drop(target_);sun_drop(depth_);sun_drop(stream_);captured_=false;target_pending_=viewport_pending_=stream_pending_=false;}
    HRESULT capture(IDirect3DDevice8& n,void* context,SunWriter writer){
        if(pending())return D3DERR_DEVICELOST;release();ops_.reserve(80);context_=context;writer_=writer;
        HRESULT hr=n.GetRenderTarget(&target_);if(SUCCEEDED(hr))hr=n.GetDepthStencilSurface(&depth_);
        if(SUCCEEDED(hr))hr=n.GetViewport(&viewport_);if(SUCCEEDED(hr))hr=n.GetStreamSource(0,&stream_,&stride_);
        if(FAILED(hr)||!target_||!depth_){release();return E_FAIL;}captured_=true;return S_OK;
    }
    HRESULT set(IDirect3DDevice8& n,unsigned kind,unsigned stage,unsigned key,DWORD value,IDirect3DBaseTexture8* texture=nullptr){
        if(!captured_)return E_FAIL;Op* found=nullptr;for(auto& o:ops_)if(o.kind==kind&&o.stage==stage&&o.key==key){found=&o;break;}
        if(!found){Op o{kind,stage,key};HRESULT hr=E_FAIL;
            if(kind==0)hr=n.GetRenderState(D3DRENDERSTATETYPE(key),&o.value);
            if(kind==1)hr=n.GetTextureStageState(stage,D3DTEXTURESTAGESTATETYPE(key),&o.value);
            if(kind==2)hr=n.GetTexture(stage,&o.texture);
            if(kind==3)hr=n.GetVertexShader(&o.value);if(kind==4)hr=n.GetPixelShader(&o.value);
            if(FAILED(hr)){sun_drop(o.texture);return hr;}ops_.push_back(o);found=&ops_.back();}
        found->pending=true;return write(n,*found,value,texture);
    }
    HRESULT target(IDirect3DDevice8& n,IDirect3DSurface8* surface,IDirect3DSurface8* depth,const D3DVIEWPORT8& viewport)noexcept{
        target_pending_=viewport_pending_=true;auto hr=n.SetRenderTarget(surface,depth);notify(31,pack(surface,depth),hr);
        if(SUCCEEDED(hr)){hr=n.SetViewport(&viewport);notify(40,pack(&viewport),hr);}return hr;
    }
    HRESULT draw(IDirect3DDevice8& n,const void* vertices,unsigned stride)noexcept{
        stream_pending_=true;return n.DrawPrimitiveUP(D3DPT_TRIANGLESTRIP,2,vertices,stride);
    }
    HRESULT triangles(IDirect3DDevice8& n,const void* vertices,unsigned stride,unsigned count)noexcept{stream_pending_=true;return n.DrawPrimitiveUP(D3DPT_TRIANGLELIST,count,vertices,stride);}
    HRESULT restore(IDirect3DDevice8& n)noexcept{
        HRESULT result=S_OK;auto check=[&](HRESULT hr,bool& bit){if(SUCCEEDED(hr))bit=false;else if(SUCCEEDED(result))result=hr;};
        if(target_pending_){auto hr=n.SetRenderTarget(target_,depth_);notify(31,pack(target_,depth_),hr);check(hr,target_pending_);}
        if(viewport_pending_&&!target_pending_){auto hr=n.SetViewport(&viewport_);notify(40,pack(&viewport_),hr);check(hr,viewport_pending_);}
        if(stream_pending_){auto hr=n.SetStreamSource(0,stream_,stride_);notify(83,pack(0,stream_,stride_),hr);check(hr,stream_pending_);}
        for(auto it=ops_.rbegin();it!=ops_.rend();++it)if(it->pending){auto hr=write(n,*it,it->value,it->texture);check(hr,it->pending);}
        if(!pending())release();return result;
    }
};
struct SunVertex {float x,y,z,rhw;DWORD color;float u,v,mask_u,mask_v;};
template<class Texture> inline HRESULT sun_upload_pixels(Texture& texture,const uint8_t* pixels,unsigned width,unsigned height){
    D3DLOCKED_RECT lock{};const auto hr=texture.LockRect(0,&lock,nullptr,0);if(FAILED(hr))return hr;
    const bool valid=pixels&&lock.pBits&&width&&height&&width<=4096&&height<=4096&&lock.Pitch>=INT(width*4);
    if(valid)for(unsigned y=0;y<height;++y)std::memcpy(static_cast<uint8_t*>(lock.pBits)+size_t(y)*lock.Pitch,pixels+size_t(y)*width*4,width*4);
    const auto unlocked=texture.UnlockRect(0);return !valid?E_FAIL:unlocked;
}
static_assert(sizeof(SunVertex)==36);
inline std::array<SunVertex,4> sun_quad(float x,float y,float radius,DWORD color,float mu,float mv){
    const float far_depth=std::nextafter(1.f,0.f);
    return {{{x-radius-.5f,y-radius-.5f,far_depth,1,color,0,0,mu,mv},{x+radius-.5f,y-radius-.5f,far_depth,1,color,1,0,mu,mv},
             {x-radius-.5f,y+radius-.5f,far_depth,1,color,0,1,mu,mv},{x+radius-.5f,y+radius-.5f,far_depth,1,color,1,1,mu,mv}}};
}
// Rotated quad for the starburst; it turns slowly with the sun's screen
// position so the spokes shimmer as the camera pans, like GT3.
inline std::array<SunVertex,4> sun_rotated_quad(float x,float y,float radius,float angle,DWORD color,float mu,float mv){
    const float far_depth=std::nextafter(1.f,0.f),c=std::cos(angle)*radius,s=std::sin(angle)*radius;
    auto at=[&](float u,float v){const float dx=(u*2-1),dy=(v*2-1);return SunVertex{x+dx*c-dy*s-.5f,y+dx*s+dy*c-.5f,far_depth,1,color,u,v,mu,mv};};
    return {{at(0,0),at(1,0),at(0,1),at(1,1)}};
}
class SunFx {
    IDirect3DSurface8 *mask_=nullptr,*resolved_=nullptr;IDirect3DTexture8 *mask_texture_=nullptr,*disk_=nullptr,*halo_=nullptr,*ghost_=nullptr,*bloom_=nullptr,*rays_=nullptr;
    UINT width_=0,height_=0,tw_=0,th_=0;D3DFORMAT format_=D3DFMT_UNKNOWN;D3DMULTISAMPLE_TYPE msaa_=D3DMULTISAMPLE_NONE;
    uint64_t latched_race_=UINT64_MAX,latched_reset_=UINT64_MAX;unsigned ray_count_=0;std::wstring ray_file_;
    float sprite_dither_=-1,sprite_bloom_dither_=-1;bool sprite_soft_=false;
public:
    // Procedural sprite intensity, r=1 at the sprite edge. kind: 0 core,
    // 1 glow, 2 ghost, 3 bloom, 4 starburst.
    static float sprite_intensity(unsigned kind,float dx,float dy,unsigned rays,bool soft=false)noexcept {
        const float r=std::sqrt(dx*dx+dy*dy);if(r>=1)return 0;
        switch(kind){
        case 0:return std::clamp((1-r)*7.f,0.f,1.f);                                  // hot disk, soft limb
        case 1:return std::max(0.f,std::exp(-r*r*4.5f)-std::exp(-4.5f))/(1-std::exp(-4.5f));
        case 2:return soft?std::pow(std::max(0.f,1-r*r),2.f)*.22f+std::exp(-std::pow((r-.68f)/.17f,2.f))*.10f:std::max(0.f,1-std::abs(r-.65f)*8)*.5f+std::max(0.f,1-r)*.16f;
        case 3:return std::pow(1-r,2.4f);                                             // wide soft bloom
        case 4:return sun_ray_profile(r,std::atan2(dy,dx)+3.1415927f,rays);
        }return 0;
    }
private:
    HRESULT sprite(IDirect3DDevice8& n,IDirect3DTexture8*& texture,unsigned kind,unsigned rays=0,float dither=0,bool soft=false){
        const unsigned size=kind==4?256:((kind==1||kind==3)&&dither>0?512:128);
        auto hr=n.CreateTexture(size,size,1,0,D3DFMT_A8R8G8B8,D3DPOOL_MANAGED,&texture);if(FAILED(hr)||!texture)return E_FAIL;
        D3DLOCKED_RECT lock{};hr=texture->LockRect(0,&lock,nullptr,0);if(FAILED(hr))return hr;
        if(!lock.pBits||lock.Pitch<INT(size*4)){texture->UnlockRect(0);return E_FAIL;}
        const float half=size*.5f;
        for(unsigned y=0;y<size;++y)for(unsigned x=0;x<size;++x){
            const float intensity=sprite_intensity(kind,(x+.5f-half)/half,(y+.5f-half)/half,rays,soft);
            DWORD c=sun_quantize(intensity,x,y,dither);c=0xff000000u|c<<16|c<<8|c;
            std::memcpy(static_cast<uint8_t*>(lock.pBits)+size_t(y)*lock.Pitch+x*4,&c,4);}
        return texture->UnlockRect(0);
    }
    HRESULT allocate(IDirect3DDevice8& n,const D3DSURFACE_DESC& desc){
        if(mask_&&desc.Width==width_&&desc.Height==height_&&desc.Format==format_&&desc.MultiSampleType==msaa_)return S_OK;
        resources();D3DCAPS8 caps{};if(FAILED(n.GetDeviceCaps(&caps))||caps.MaxSimultaneousTextures<2||caps.MaxTextureBlendStages<2)return E_FAIL;
        if(!desc.Width||!desc.Height||uint64_t(desc.Width)*desc.Height>4194304||uint64_t(desc.Width)*desc.Height*4*std::max(1u,unsigned(desc.MultiSampleType))>96*1024*1024||(desc.Format!=D3DFMT_X8R8G8B8&&desc.Format!=D3DFMT_A8R8G8B8))return E_FAIL;
        width_=desc.Width;height_=desc.Height;format_=desc.Format;msaa_=desc.MultiSampleType;tw_=width_;th_=height_;
        if(caps.TextureCaps&D3DPTEXTURECAPS_POW2){tw_=th_=1;while(tw_<width_)tw_*=2;while(th_<height_)th_*=2;}
        if(caps.TextureCaps&D3DPTEXTURECAPS_SQUAREONLY)tw_=th_=std::max(tw_,th_);
        if(tw_>caps.MaxTextureWidth||th_>caps.MaxTextureHeight||uint64_t(tw_)*th_*4>32*1024*1024)return E_FAIL;
        auto hr=n.CreateRenderTarget(width_,height_,format_,msaa_,FALSE,&mask_);
        if(SUCCEEDED(hr))hr=n.CreateTexture(tw_,th_,1,D3DUSAGE_RENDERTARGET,format_,D3DPOOL_DEFAULT,&mask_texture_);
        if(SUCCEEDED(hr)&&mask_texture_)hr=mask_texture_->GetSurfaceLevel(0,&resolved_);
        if(SUCCEEDED(hr))hr=sprite(n,disk_,0);if(SUCCEEDED(hr))hr=sprite(n,halo_,1);if(SUCCEEDED(hr))hr=sprite(n,ghost_,2);if(SUCCEEDED(hr))hr=sprite(n,bloom_,3);
        if(FAILED(hr)||!mask_||!resolved_||!disk_||!halo_||!ghost_||!bloom_){resources();return E_FAIL;}sprite_dither_=sprite_bloom_dither_=0;sprite_soft_=false;return S_OK;
    }
    // The starburst depends on the (live-tunable) spoke count.
    // Procedural spokes, or an author-supplied 256x256 BGRA sprite (same 20-byte
    // header as the custom sky layers). An unreadable file falls back to procedural.
    HRESULT ray_sprite(IDirect3DDevice8& n,unsigned rays,const std::wstring& file){
        if(rays_&&ray_count_==rays&&ray_file_==file)return S_OK;sun_drop(rays_);ray_count_=0;ray_file_.clear();ray_from_file=false;
        if(!file.empty())try{
            std::ifstream f(std::filesystem::path(file),std::ios::binary|std::ios::ate);
            if(f&&f.tellg()==std::streamoff(20+256*256*4)){f.seekg(0);std::vector<uint8_t> bytes(20+256*256*4);
                uint32_t h[5]{};if(f.read(reinterpret_cast<char*>(bytes.data()),bytes.size())){std::memcpy(h,bytes.data(),20);
                    if(h[0]==0xfeed&&h[3]==256&&h[4]==256&&SUCCEEDED(n.CreateTexture(256,256,1,0,D3DFMT_A8R8G8B8,D3DPOOL_MANAGED,&rays_))&&rays_){
                        if(SUCCEEDED(sun_upload_pixels(*rays_,bytes.data()+20,256,256))){ray_count_=rays;ray_file_=file;ray_from_file=true;return S_OK;}
                        sun_drop(rays_);}}}
        }catch(...){sun_drop(rays_);}
        const auto hr=sprite(n,rays_,4,rays);if(FAILED(hr)||!rays_){sun_drop(rays_);return E_FAIL;}ray_count_=rays;ray_file_=file;return S_OK;
    }
public:
    SunProof proof;SunTransaction transaction;bool ray_from_file=false;
    uint64_t drawn_frame=UINT64_MAX,gate_frame=UINT64_MAX,unsafe_frame=UINT64_MAX,attempts=0,rendered=0,failures=0,cpu_ticks=0;const char* reason="not_requested";HRESULT last_hr=S_OK;
    ~SunFx(){resources();}
    void resources()noexcept{sun_drop(mask_);sun_drop(resolved_);sun_drop(mask_texture_);sun_drop(disk_);sun_drop(halo_);sun_drop(ghost_);sun_drop(bloom_);sun_drop(rays_);ray_count_=0;ray_file_.clear();sprite_dither_=sprite_bloom_dither_=-1;width_=height_=tw_=th_=0;}
    void clear()noexcept{proof.clear();}
    void reset()noexcept{proof.clear();transaction.release();resources();latched_race_=latched_reset_=UINT64_MAX;drawn_frame=UINT64_MAX;}
    HRESULT vignette(IDirect3DDevice8& n,UINT width,UINT height,float strength,void* context,SunWriter writer){
        if(!proof.world||!width||!height||!std::isfinite(strength)||strength<=0)return S_FALSE;
        auto hr=transaction.capture(n,context,writer);if(FAILED(hr))return S_FALSE;
        auto rs=[&](DWORD k,DWORD v){if(SUCCEEDED(hr))hr=transaction.set(n,0,0,k,v);};
        auto ts=[&](unsigned stage,DWORD k,DWORD v){if(SUCCEEDED(hr))hr=transaction.set(n,1,stage,k,v);};
        rs(D3DRS_ZENABLE,D3DZB_FALSE);rs(D3DRS_ZWRITEENABLE,FALSE);rs(D3DRS_ALPHATESTENABLE,FALSE);rs(D3DRS_ALPHABLENDENABLE,TRUE);
        rs(D3DRS_SRCBLEND,D3DBLEND_SRCALPHA);rs(D3DRS_DESTBLEND,D3DBLEND_INVSRCALPHA);rs(D3DRS_BLENDOP,D3DBLENDOP_ADD);
        rs(D3DRS_LIGHTING,FALSE);rs(D3DRS_FOGENABLE,FALSE);rs(D3DRS_STENCILENABLE,FALSE);rs(D3DRS_SPECULARENABLE,FALSE);
        rs(D3DRS_CULLMODE,D3DCULL_NONE);rs(D3DRS_FILLMODE,D3DFILL_SOLID);rs(D3DRS_COLORWRITEENABLE,7);rs(D3DRS_CLIPPLANEENABLE,0);
        if(SUCCEEDED(hr))hr=transaction.set(n,3,0,0,D3DFVF_XYZRHW|D3DFVF_DIFFUSE|D3DFVF_TEX2);if(SUCCEEDED(hr))hr=transaction.set(n,4,0,0,0);
        for(unsigned i=0;i<2;++i)if(SUCCEEDED(hr))hr=transaction.set(n,2,i,0,0,nullptr);
        ts(0,D3DTSS_COLOROP,D3DTOP_SELECTARG2);ts(0,D3DTSS_COLORARG2,D3DTA_DIFFUSE);ts(0,D3DTSS_ALPHAOP,D3DTOP_SELECTARG1);ts(0,D3DTSS_ALPHAARG1,D3DTA_DIFFUSE);
        ts(0,D3DTSS_RESULTARG,D3DTA_CURRENT);ts(1,D3DTSS_COLOROP,D3DTOP_DISABLE);ts(1,D3DTSS_ALPHAOP,D3DTOP_DISABLE);ts(2,D3DTSS_COLOROP,D3DTOP_DISABLE);
        std::array<SunVertex,192> vertices{};size_t at=0;const DWORD edge=DWORD(std::lround(std::clamp(strength,0.f,.3f)*255))<<24;
        auto point=[&](unsigned index,float radius,DWORD color){const float angle=6.2831853f*float(index)/32;return SunVertex{width*.5f*(1+radius*std::cos(angle))-.5f,height*.5f*(1+radius*std::sin(angle))-.5f,0,1,color,0,0,0,0};};
        for(unsigned i=0;i<32;++i){const auto a=point(i,.55f,0),b=point(i+1,.55f,0),c=point(i,1.5f,edge),d=point(i+1,1.5f,edge);for(const auto& p:{a,b,c,c,b,d})vertices[at++]=p;}
        if(SUCCEEDED(hr))hr=transaction.triangles(n,vertices.data(),sizeof(SunVertex),64);const auto restored=transaction.restore(n);return FAILED(restored)?restored:FAILED(hr)?S_FALSE:S_OK;
    }
    HRESULT render(IDirect3DDevice8& n,const SunPosition& position,bool disk,bool halo,bool flare,void* context,SunWriter writer,const Lighting* lighting=nullptr,const SunStyle& style=SunStyle{}){
        struct Timer{uint64_t& ticks;LARGE_INTEGER start{};Timer(uint64_t& t):ticks(t){QueryPerformanceCounter(&start);}~Timer(){LARGE_INTEGER end{};QueryPerformanceCounter(&end);ticks+=end.QuadPart-start.QuadPart;}}timer(cpu_ticks);
        if(!proof.world||!proof.target||!proof.depth||!(disk||halo||flare)||!std::isfinite(position.x)||!std::isfinite(position.y)||!std::isfinite(position.radius)||position.radius<=0){reason="missing_scene_proof";return S_FALSE;}
        if(latched_race_==proof.race&&latched_reset_==proof.reset){reason="driver_failure_latched_for_race";return S_FALSE;}
        ++attempts;D3DSURFACE_DESC desc{},depth_desc{};auto hr=proof.target->GetDesc(&desc);if(SUCCEEDED(hr))hr=proof.depth->GetDesc(&depth_desc);
        if(SUCCEEDED(hr)&&(desc.Width!=depth_desc.Width||desc.Height!=depth_desc.Height||desc.MultiSampleType!=depth_desc.MultiSampleType||
           (depth_desc.Format!=D3DFMT_D24S8&&depth_desc.Format!=D3DFMT_D24X8)))hr=E_FAIL;
        if(SUCCEEDED(hr))hr=allocate(n,desc);
        const float halo_dither=sun_layer_dither(style.dither,style.glow*std::max({style.glow_rgb[0],style.glow_rgb[1],style.glow_rgb[2]}));
        const float bloom_dither=sun_layer_dither(style.dither,style.bloom*std::max({style.bloom_rgb[0],style.bloom_rgb[1],style.bloom_rgb[2]}));
        if(SUCCEEDED(hr)&&(sprite_dither_!=halo_dither||sprite_bloom_dither_!=bloom_dither||sprite_soft_!=style.soft_ghosts)){sun_drop(halo_);sun_drop(ghost_);sun_drop(bloom_);
            hr=sprite(n,halo_,1,0,halo_dither);if(SUCCEEDED(hr))hr=sprite(n,bloom_,3,0,bloom_dither);if(SUCCEEDED(hr))hr=sprite(n,ghost_,2,0,0,style.soft_ghosts);
            if(SUCCEEDED(hr)){sprite_dither_=halo_dither;sprite_bloom_dither_=bloom_dither;sprite_soft_=style.soft_ghosts;}else resources();}
        if(SUCCEEDED(hr)&&halo&&style.rays>0)hr=ray_sprite(n,style.ray_count,style.ray_texture);
        if(FAILED(hr)){reason="mask_allocation_or_depth_incompatible";last_hr=hr;latched_race_=proof.race;latched_reset_=proof.reset;++failures;return S_FALSE;}
        hr=transaction.capture(n,context,writer);if(FAILED(hr)){reason="state_capture_failed";last_hr=hr;return S_FALSE;}
        auto rs=[&](DWORD key,DWORD value){if(SUCCEEDED(hr))hr=transaction.set(n,0,0,key,value);};
        auto ts=[&](unsigned stage,DWORD key,DWORD value){if(SUCCEEDED(hr))hr=transaction.set(n,1,stage,key,value);};
        auto tex=[&](unsigned stage,IDirect3DTexture8* t){if(SUCCEEDED(hr))hr=transaction.set(n,2,stage,0,0,t);};
        rs(D3DRS_ZENABLE,D3DZB_TRUE);rs(D3DRS_ZWRITEENABLE,FALSE);rs(D3DRS_ZFUNC,D3DCMP_LESSEQUAL);rs(D3DRS_ZBIAS,0);
        rs(D3DRS_ALPHATESTENABLE,FALSE);rs(D3DRS_ALPHABLENDENABLE,FALSE);rs(D3DRS_SRCBLEND,D3DBLEND_ONE);rs(D3DRS_DESTBLEND,D3DBLEND_ONE);rs(D3DRS_BLENDOP,D3DBLENDOP_ADD);
        rs(D3DRS_CULLMODE,D3DCULL_NONE);rs(D3DRS_FILLMODE,D3DFILL_SOLID);rs(D3DRS_CLIPPING,TRUE);rs(D3DRS_LIGHTING,FALSE);rs(D3DRS_FOGENABLE,FALSE);rs(D3DRS_STENCILENABLE,FALSE);
        rs(D3DRS_CLIPPLANEENABLE,0);rs(D3DRS_COLORWRITEENABLE,7);rs(D3DRS_SPECULARENABLE,FALSE);rs(D3DRS_VERTEXBLEND,D3DVBF_DISABLE);rs(D3DRS_INDEXEDVERTEXBLENDENABLE,FALSE);
        rs(D3DRS_WRAP0,0);rs(D3DRS_WRAP1,0);rs(D3DRS_MULTISAMPLEMASK,0xffffffffu);rs(D3DRS_MULTISAMPLEANTIALIAS,TRUE);
        if(SUCCEEDED(hr))hr=transaction.set(n,3,0,0,D3DFVF_XYZRHW|D3DFVF_DIFFUSE|D3DFVF_TEX2);
        if(SUCCEEDED(hr))hr=transaction.set(n,4,0,0,0);
        for(unsigned stage=0;stage<2;++stage){ts(stage,D3DTSS_COLORARG1,D3DTA_TEXTURE);ts(stage,D3DTSS_COLORARG2,stage?D3DTA_CURRENT:D3DTA_DIFFUSE);
            ts(stage,D3DTSS_ALPHAOP,D3DTOP_SELECTARG1);ts(stage,D3DTSS_ALPHAARG1,D3DTA_CURRENT);ts(stage,D3DTSS_RESULTARG,D3DTA_CURRENT);
            ts(stage,D3DTSS_TEXCOORDINDEX,stage);ts(stage,D3DTSS_TEXTURETRANSFORMFLAGS,D3DTTFF_DISABLE);ts(stage,D3DTSS_ADDRESSU,D3DTADDRESS_CLAMP);ts(stage,D3DTSS_ADDRESSV,D3DTADDRESS_CLAMP);
            ts(stage,D3DTSS_MINFILTER,D3DTEXF_POINT);ts(stage,D3DTSS_MAGFILTER,D3DTEXF_POINT);ts(stage,D3DTSS_MIPFILTER,D3DTEXF_NONE);ts(stage,D3DTSS_MAXMIPLEVEL,0);}
        ts(2,D3DTSS_COLOROP,D3DTOP_DISABLE);ts(2,D3DTSS_ALPHAOP,D3DTOP_DISABLE);
        ts(0,D3DTSS_COLOROP,D3DTOP_SELECTARG2);ts(1,D3DTSS_COLOROP,D3DTOP_DISABLE);tex(0,nullptr);tex(1,nullptr);
        const D3DVIEWPORT8 viewport{0,0,width_,height_,0,1};
        if(SUCCEEDED(hr))hr=transaction.target(n,mask_,proof.depth,viewport);
        // Never clear depth/stencil. Every visibility sample is tested against
        // the actual completed scene, including alpha-tested leaves/fences.
        if(SUCCEEDED(hr))hr=n.Clear(0,nullptr,D3DCLEAR_TARGET,0,1,0);
        auto quad=sun_quad(position.x,position.y,position.radius+2,0xffffffffu,0,0);
        if(SUCCEEDED(hr))hr=transaction.draw(n,quad.data(),sizeof(SunVertex));
        if(SUCCEEDED(hr))hr=transaction.target(n,proof.target,proof.depth,viewport);
        const RECT source{0,0,LONG(width_),LONG(height_)};const POINT destination{0,0};
        if(SUCCEEDED(hr))hr=n.CopyRects(mask_,&source,1,resolved_,&destination);
        const bool mask_ready=SUCCEEDED(hr);
        rs(D3DRS_ALPHABLENDENABLE,TRUE);ts(0,D3DTSS_COLOROP,D3DTOP_MODULATE);ts(0,D3DTSS_MAGFILTER,D3DTEXF_LINEAR);ts(0,D3DTSS_MINFILTER,D3DTEXF_LINEAR);
        auto color=[](float r,float g,float b,float intensity){DWORD c=0xff000000;for(auto pair:{std::pair<unsigned,float>{16,r},{8,g},{0,b}})c|=DWORD(std::clamp(std::lround(pair.second*intensity*255),0l,255l))<<pair.first;return c;};
        // Warm layers follow the world sunlight colour; the core stays near-white.
        std::array<float,3> tint{1,.87f,.62f};if(lighting){const float maximum=std::max({lighting->sun[0],lighting->sun[1],lighting->sun[2],.01f});for(unsigned i=0;i<3;++i)tint[i]=std::clamp(lighting->sun[i]/maximum,0.f,1.f);}
        auto warm=[&](const std::array<float,3>& rgb,unsigned i){return rgb[i]*(.55f+.45f*tint[i]);};
        // The core alone is depth-tested at the far plane: geometry cuts it crisply.
        if(disk&&style.core>0){tex(0,disk_);quad=sun_quad(position.x,position.y,position.radius,color(style.core_rgb[0],style.core_rgb[1],style.core_rgb[2],style.core),0,0);if(SUCCEEDED(hr))hr=transaction.draw(n,quad.data(),sizeof(SunVertex));}
        ts(1,D3DTSS_COLOROP,D3DTOP_MODULATE);tex(1,mask_texture_);
        // Glow, bloom and spokes overlay nearby geometry like GT3, but each of the
        // five current-frame depth samples adds 1/5: fully hidden sun = no light.
        const float limit=float(std::max(width_,height_));
        const float glow_radius=std::min(limit,std::max(position.radius*1.5f,position.pixels(style.glow_degrees)));
        const float bloom_radius=std::min(limit,std::max(glow_radius,position.pixels(style.bloom_degrees)));
        const float ray_radius=std::min(limit,std::max(glow_radius,position.pixels(style.ray_degrees)));
        const float spin=.35f*(position.x/float(width_)-.5f)+.2f*(position.y/float(height_)-.5f);
        const float offsets[5][2]={{0,0},{-.55f,0},{.55f,0},{0,-.55f},{0,.55f}};
        rs(D3DRS_ZENABLE,D3DZB_FALSE);
        for(const auto& offset:offsets){const float mu=(std::floor(position.x+offset[0]*position.radius)+.5f)/tw_,mv=(std::floor(position.y+offset[1]*position.radius)+.5f)/th_;
            const float share=.2f*position.edge;
            if(halo&&style.bloom>0){tex(0,bloom_);quad=sun_quad(position.x,position.y,bloom_radius,color(warm(style.bloom_rgb,0),warm(style.bloom_rgb,1),warm(style.bloom_rgb,2),style.bloom*share),mu,mv);if(SUCCEEDED(hr))hr=transaction.draw(n,quad.data(),sizeof(SunVertex));}
            if(halo&&style.glow>0){tex(0,halo_);quad=sun_quad(position.x,position.y,glow_radius,color(warm(style.glow_rgb,0),warm(style.glow_rgb,1),warm(style.glow_rgb,2),style.glow*share),mu,mv);if(SUCCEEDED(hr))hr=transaction.draw(n,quad.data(),sizeof(SunVertex));}
            if(halo&&style.rays>0&&rays_){tex(0,rays_);auto spokes=sun_rotated_quad(position.x,position.y,ray_radius,spin,color(style.core_rgb[0]*.5f+warm(style.glow_rgb,0)*.5f,style.core_rgb[1]*.5f+warm(style.glow_rgb,1)*.5f,style.core_rgb[2]*.5f+warm(style.glow_rgb,2)*.5f,style.rays*share),mu,mv);if(SUCCEEDED(hr))hr=transaction.draw(n,spokes.data(),sizeof(SunVertex));}
            if(flare&&style.flare>0){tex(0,ghost_);for(unsigned i=0;i<4;++i){const float t=.45f+i*.43f,x=position.x+(width_*.5f-position.x)*t,y=position.y+(height_*.5f-position.y)*t;
                quad=sun_quad(x,y,glow_radius*(.35f+i*.12f),color(i&1?.45f:1.f,i&1?.7f:.52f,i&1?1.f:.25f,.12f*style.flare*share),mu,mv);if(SUCCEEDED(hr))hr=transaction.draw(n,quad.data(),sizeof(SunVertex));}}
        }
        last_hr=hr;const auto restore=transaction.restore(n);
        if(FAILED(restore)){reason="restore_pending";return restore;}
        if(FAILED(hr)||!mask_ready){reason="mask_or_draw_failed_no_visibility_fallback";latched_race_=proof.race;latched_reset_=proof.reset;++failures;return S_FALSE;}
        ++rendered;reason="current_frame_gpu_depth_mask";return S_OK;
    }
};
}
