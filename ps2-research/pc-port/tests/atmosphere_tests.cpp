#include "atmosphere.hpp"
#include <iostream>
#include <limits>
#include <map>
using namespace gfx2;
int failures=0;
#define CHECK(x) do{if(!(x)){std::cerr<<"FAIL "<<__LINE__<<": " #x "\n";++failures;}}while(0)
#include "mock_interfaces.hpp"
struct Native:MockDeviceBase {
    int calls=0,fail=0;
    HRESULT result(){return ++calls==fail?D3DERR_INVALIDCALL:S_OK;}
    HRESULT STDMETHODCALLTYPE SetRenderState(D3DRENDERSTATETYPE,DWORD)override{return result();}
    HRESULT STDMETHODCALLTYPE SetTextureStageState(DWORD,D3DTEXTURESTAGESTATETYPE,DWORD)override{return result();}
    HRESULT STDMETHODCALLTYPE SetIndices(IDirect3DIndexBuffer8*,UINT)override{return result();}
    HRESULT STDMETHODCALLTYPE SetStreamSource(UINT,IDirect3DVertexBuffer8*,UINT)override{return result();}
    HRESULT STDMETHODCALLTYPE SetTexture(DWORD,IDirect3DBaseTexture8*)override{return result();}
};
struct SunSurface:IDirect3DSurface8 {
    ULONG refs=1;
    HRESULT STDMETHODCALLTYPE QueryInterface(REFIID,void** p)override{*p=this;AddRef();return S_OK;}
    ULONG STDMETHODCALLTYPE AddRef()override{return ++refs;}
    ULONG STDMETHODCALLTYPE Release()override{return --refs;}
    HRESULT STDMETHODCALLTYPE GetDevice(IDirect3DDevice8**)override{return E_NOTIMPL;}
    HRESULT STDMETHODCALLTYPE SetPrivateData(REFGUID,const void*,DWORD,DWORD)override{return E_NOTIMPL;}
    HRESULT STDMETHODCALLTYPE GetPrivateData(REFGUID,void*,DWORD*)override{return E_NOTIMPL;}
    HRESULT STDMETHODCALLTYPE FreePrivateData(REFGUID)override{return E_NOTIMPL;}
    HRESULT STDMETHODCALLTYPE GetContainer(REFIID,void**)override{return E_NOTIMPL;}
    HRESULT STDMETHODCALLTYPE GetDesc(D3DSURFACE_DESC*)override{return E_NOTIMPL;}
    HRESULT STDMETHODCALLTYPE LockRect(D3DLOCKED_RECT*,const RECT*,DWORD)override{return E_NOTIMPL;}
    HRESULT STDMETHODCALLTYPE UnlockRect()override{return E_NOTIMPL;}
};
struct SunNative:Native {
    SunSurface target,depth;DWORD zwrite=TRUE;
    HRESULT STDMETHODCALLTYPE GetRenderTarget(IDirect3DSurface8** p)override{*p=&target;target.AddRef();return S_OK;}
    HRESULT STDMETHODCALLTYPE GetDepthStencilSurface(IDirect3DSurface8** p)override{*p=&depth;depth.AddRef();return S_OK;}
    HRESULT STDMETHODCALLTYPE GetViewport(D3DVIEWPORT8* p)override{*p={0,0,800,600,0,1};return S_OK;}
    HRESULT STDMETHODCALLTYPE GetStreamSource(UINT,IDirect3DVertexBuffer8** p,UINT* stride)override{*p=nullptr;*stride=0;return S_OK;}
    HRESULT STDMETHODCALLTYPE GetRenderState(D3DRENDERSTATETYPE,DWORD* v)override{*v=zwrite;return S_OK;}
    HRESULT STDMETHODCALLTYPE SetRenderState(D3DRENDERSTATETYPE,DWORD v)override{auto hr=result();if(SUCCEEDED(hr))zwrite=v;return hr;}
    HRESULT STDMETHODCALLTYPE SetRenderTarget(IDirect3DSurface8*,IDirect3DSurface8*)override{return result();}
    HRESULT STDMETHODCALLTYPE SetViewport(const D3DVIEWPORT8*)override{return result();}
};
struct ArtNative:SunNative {
    std::map<DWORD,DWORD> states;std::map<std::pair<DWORD,DWORD>,DWORD> stages;
    DWORD vs=0x112,ps=0;unsigned draws=0,triangles=0;bool draw_fail=false;
    HRESULT STDMETHODCALLTYPE GetRenderState(D3DRENDERSTATETYPE k,DWORD* v)override{*v=states[k];return S_OK;}
    HRESULT STDMETHODCALLTYPE SetRenderState(D3DRENDERSTATETYPE k,DWORD v)override{auto h=result();if(SUCCEEDED(h))states[k]=v;return h;}
    HRESULT STDMETHODCALLTYPE GetTextureStageState(DWORD s,D3DTEXTURESTAGESTATETYPE k,DWORD* v)override{*v=stages[{s,k}];return S_OK;}
    HRESULT STDMETHODCALLTYPE SetTextureStageState(DWORD s,D3DTEXTURESTAGESTATETYPE k,DWORD v)override{auto h=result();if(SUCCEEDED(h))stages[{s,k}]=v;return h;}
    HRESULT STDMETHODCALLTYPE GetTexture(DWORD,IDirect3DBaseTexture8** v)override{*v=nullptr;return S_OK;}
    HRESULT STDMETHODCALLTYPE GetDeviceCaps(D3DCAPS8* c)override{*c={};c->MaxTextureBlendStages=3;c->TextureOpCaps=D3DTEXOPCAPS_MODULATE|D3DTEXOPCAPS_SELECTARG1;return S_OK;}
    HRESULT STDMETHODCALLTYPE GetVertexShader(DWORD* v)override{*v=vs;return S_OK;}
    HRESULT STDMETHODCALLTYPE GetPixelShader(DWORD* v)override{*v=ps;return S_OK;}
    HRESULT STDMETHODCALLTYPE SetVertexShader(DWORD v)override{auto h=result();if(SUCCEEDED(h))vs=v;return h;}
    HRESULT STDMETHODCALLTYPE SetPixelShader(DWORD v)override{auto h=result();if(SUCCEEDED(h))ps=v;return h;}
    HRESULT STDMETHODCALLTYPE DrawPrimitiveUP(D3DPRIMITIVETYPE type,UINT count,const void*,UINT stride)override{++draws;triangles=count;return draw_fail||type!=D3DPT_TRIANGLELIST||stride!=36?E_FAIL:S_OK;}
};
struct UploadTexture {
    std::array<uint8_t,64> bytes{};int locks=0,unlocks=0,pitch=16;bool null_bits=false,fail_lock=false,fail_unlock=false;
    HRESULT LockRect(UINT,D3DLOCKED_RECT* p,const RECT*,DWORD){++locks;p->pBits=null_bits?nullptr:bytes.data();p->Pitch=pitch;return fail_lock?E_FAIL:S_OK;}
    HRESULT UnlockRect(UINT){++unlocks;return fail_unlock?E_FAIL:S_OK;}
};
struct Broker:RaceReadMemory {
    std::map<uint32_t,uint8_t> bytes;
    bool players_key=true,sync_key=true;
    bool read(uint32_t a,void* out,size_t n)noexcept override {
        for(size_t i=0;i<n;++i){auto it=bytes.find(a+uint32_t(i));if(it==bytes.end())return false;static_cast<uint8_t*>(out)[i]=it->second;}return true;
    }
    bool resolve_id(uint32_t,const char* key,uint32_t& id)noexcept override {
        if(!std::strcmp(key,"Race/NumNetworkPlayers")){id=0;return players_key;}
        if(!std::strcmp(key,"Race/NetworkSyncActive")){id=1;return sync_key;}
        const char* keys[]={"FrontEnd/Network/Browse","Race/NumPlayers","Race/Type","Race/PlaybackReplay"};
        for(unsigned i=0;i<4;++i)if(!std::strcmp(key,keys[i])){id=i+2;return true;}return false;
    }
    void word(uint32_t a,uint32_t v){for(unsigned i=0;i<4;++i)bytes[a+i]=uint8_t(v>>(8*i));}
    Broker(){word(0x6f9410,0x20000);word(0x20004,0x21000);word(0x20008,0x210a8);word(0x2000c,0x210a8);
        word(0x21000,0);word(0x21004,0x22000);word(0x21008,2);word(0x22000,0);
        word(0x2101c,1);word(0x21020,0x22004);word(0x21024,0);word(0x22004,0);
        for(unsigned i=2;i<6;++i){word(0x21000+i*28,i);word(0x21004+i*28,0x22000+i*4);
            word(0x21008+i*28,(i==3||i==4)?2:0);word(0x22000+i*4,(i==3||i==4)?1:0);}}
    void pending_sync(){word(0x2101c,0);word(0x21020,0);word(0x21024,12);}
};
int main(){
    using namespace atmosphere;
    CHECK(BodyMaterials::safe("icewin-tga","glass-tga",OpaqueGlazing));
    CHECK(!BodyMaterials::safe("inlights-tga","glass-tga",OpaqueGlazing));
    CHECK(!BodyMaterials::safe("windscreen32-tga","glass-tga",OpaqueGlazing));
    CHECK(!BodyMaterials::safe("body-tga","whitepaint-tga",OpaqueGlazing));
    CHECK(sun_layer_dither(1,.95f)>5&&sun_layer_dither(1,.95f)<6);
    CHECK(sun_layer_dither(0,1)==0&&sun_layer_dither(1,0)==0&&sun_layer_dither(2,.001f)<=16);
    for(unsigned y=0;y<16;++y)for(unsigned x=0;x<16;++x){CHECK(sun_quantize(0,x,y,16)==0);CHECK(sun_quantize(.5f,x,y,8)==sun_quantize(.5f,x+256,y+256,8));CHECK(sun_quantize(.5f,x,y,8)<=255);}
    for(int failed=0;failed<=16;++failed){Pilot p(false,L"Z:\\missing-wheel-energy\\MRRRenderer.ini");p.lighting.mode=Lighting::Mode::GoldenHour;ArtNative n;n.fail=failed;
        auto note=[](uint32_t,const Args&,HRESULT){};const auto hr=native_wheel_energy(p,n,note);n.fail=0;
        if(p.pending.any())CHECK(restore_pending(p,n,note)==S_OK);
        CHECK(!p.pending.any());for(const auto& row:n.states)CHECK(row.second==0);for(const auto& row:n.stages)CHECK(row.second==0);
        if(!failed)CHECK(hr==S_OK);}
    CHECK(world_lighting_before_replacement(0x142,D3DTOP_MODULATE2X,false));
    CHECK(world_lighting_before_replacement(0x152,D3DTOP_MODULATEALPHA_ADDCOLOR,true));
    CHECK(!world_lighting_before_replacement(0x152,D3DTOP_MODULATEALPHA_ADDCOLOR,false));
    CHECK(!world_lighting_before_replacement(0x142,D3DTOP_MODULATE,true));
    CHECK(world_lighting_before_replacement(0x142,D3DTOP_DISABLE,true));
    CHECK(!world_lighting_before_replacement(0x142,D3DTOP_DISABLE,false));
    CHECK(world_lighting_before_replacement(0x102,D3DTOP_DISABLE,true));
    CHECK(!world_lighting_before_replacement(0x102,D3DTOP_DISABLE,false));
    CHECK(!world_lighting_before_replacement(0x252,D3DTOP_ADD,true));
    CHECK(!world_lighting_before_replacement(0x104,D3DTOP_MODULATE,true));
    {
        std::array<float,16> w{},v{};for(unsigned i:{0u,5u,10u,15u}){w[i]=1;v[i]=1;}
        w[0]=w[5]=w[10]=.6f;w[13]=-100;v[13]=-60;
        float uv=0;CHECK(sky_panorama_v(w,v,{1000,400,0},.4001f,uv));CHECK(std::abs(uv-(.003f+.995f*80/600))<1e-5f);
        CHECK(uv<.4001f);CHECK(sky_panorama_v(w,v,{1000,1000,0},.998f,uv)&&uv==.998f);
        auto bad=w;bad[8]=.2f;CHECK(!sky_panorama_v(bad,v,{1000,400,0},.4f,uv));bad=w;bad[3]=.1f;CHECK(!sky_panorama_v(bad,v,{1000,400,0},.4f,uv));
        bad=v;bad[0]=2;CHECK(!sky_panorama_v(w,bad,{1000,400,0},.4f,uv));
        float mean=0;for(unsigned y=0;y<4;++y)for(unsigned x=0;x<4;++x){mean+=ordered_dither(x,y);CHECK(sun_quantize(0,x,y,2)==0);CHECK(sun_quantize(.5f,x,y,1)==sun_quantize(.5f,x+4,y+4,1));}
        CHECK(std::abs(mean)<1e-6f);CHECK(sun_quantize(std::numeric_limits<float>::quiet_NaN(),0,0,1)==0);
        CHECK(rim_amount({0,1,0},{0,1,0},{0,1,0},3)==0);CHECK(rim_amount({0,1,0},{1,0,0},{0,1,0},3)>.99f);
        CHECK(rim_amount({0,1,0},{0,-1,0},{0,1,0},3)==0);CHECK(rim_amount({0,1,0},{1,0,0},{0,-1,0},3)==0);
        UploadTexture texture;uint8_t pixels[64]{};CHECK(sun_upload_pixels(texture,pixels,4,4)==S_OK&&texture.unlocks==1);
        texture.pitch=4;CHECK(FAILED(sun_upload_pixels(texture,pixels,4,4))&&texture.unlocks==2);
        texture.pitch=16;texture.null_bits=true;CHECK(FAILED(sun_upload_pixels(texture,pixels,4,4))&&texture.unlocks==3);
        texture.fail_lock=true;CHECK(FAILED(sun_upload_pixels(texture,pixels,4,4))&&texture.unlocks==3);
        texture.fail_lock=false;texture.null_bits=false;texture.fail_unlock=true;CHECK(FAILED(sun_upload_pixels(texture,pixels,4,4))&&texture.unlocks==4);
        // Every injected setter failure and a failed draw must restore all touched state.
        for(int failure=0;failure<45;++failure){ArtNative n;SunFx fx;fx.proof.world=true;n.fail=failure;
            CHECK(fx.vignette(n,800,600,0,nullptr,nullptr)==S_FALSE&&n.calls==0);
            const auto hr=fx.vignette(n,800,600,.1f,nullptr,nullptr);n.fail=0;
            if(fx.transaction.pending())CHECK(fx.transaction.restore(n)==S_OK);
            CHECK(!fx.transaction.pending()&&n.target.refs==1&&n.depth.refs==1&&n.vs==0x112&&n.ps==0);
            for(const auto& pair:n.states)CHECK(pair.second==0);for(const auto& pair:n.stages)CHECK(pair.second==0);
            if(failure==0)CHECK(hr==S_OK&&n.draws==1&&n.triangles==64);
        }
        ArtNative n;SunFx fx;fx.proof.world=true;n.draw_fail=true;CHECK(fx.vignette(n,800,600,.1f,nullptr,nullptr)==S_FALSE);CHECK(!fx.transaction.pending());
        Lighting s;s.mode=Lighting::Mode::GoldenHour;const auto old=scene_color(0x7f808080,{0,1,0},s);
        s.tone_contrast=1.4f;s.tone_shoulder=2;CHECK(scene_color(0x7f808080,{0,1,0},s)==old);
        s.surface_tone=true;CHECK(scene_color(0x7f000000,{0,1,0},s)==0x7f000000);CHECK(scene_color(0x7fffffff,{0,1,0},s)>>24==0x7f);
        {   // PERF-ATMO2: hoisted body colour is bit-identical to the per-vertex original (every role, random inputs).
            Lighting r=s;r.prelight_contrast=.7f;r.prelight_visibility=.3f;r.direction={.1f,.12f,.79f};uint32_t seed=12345u;unsigned mismatches=0;
            auto rnd=[&]{seed=seed*1664525u+1013904223u;return float(seed>>8)/16777216.f;};
            for(uint32_t role=1;role<=11;++role){const ScenePre pre(vehicle_surface_lighting(r,role));
                for(unsigned i=0;i<4000;++i){const uint32_t c=(uint32_t(rnd()*255)<<24)|(uint32_t(rnd()*255)<<16)|(uint32_t(rnd()*255)<<8)|uint32_t(rnd()*255);
                    const std::array<float,3> nrm{rnd()*2-1,rnd()*2-1,rnd()*2-1};const bool prepared=i%7==0;
                    mismatches+=vehicle_surface_color(c,nrm,r,prepared,role)!=vehicle_surface_color(c,nrm,pre,prepared);}}
            CHECK(mismatches==0);
            const ScenePre plain(s);CHECK(scene_color(0x7f808080,{0,1,0},plain)==scene_color(0x7f808080,{0,1,0},s));
        }
        const auto high=scene_color(0xff808080,{0,1,0},s),low=scene_color(0xff404040,{0,1,0},s);
        for(unsigned shift:{0u,8u,16u})CHECK(std::abs(int((high>>shift)&255)-2*int((low>>shift)&255))<=1);
        const auto factor=world_environment_factor(s);s.surface_tone=false;CHECK(factor==world_environment_factor(s));
        Pilot off(false,L"Z:\\missing-art-test\\MRRRenderer.ini");
        for(int failed=1;failed<=5;++failed){Native device;device.fail=failed;off.pending.sky_pending=31;
            auto notify=[](uint32_t,const Args&,HRESULT){};CHECK(FAILED(restore_pending(off,device,notify)));CHECK(off.pending.sky_pending==(1u<<(failed-1)));
            device.fail=0;CHECK(restore_pending(off,device,notify)==S_OK&&!off.pending.any());}
    }
    {
        CHECK(BodyMaterials::safe("tread-tga","rubber-tga",WheelRubber));CHECK(!BodyMaterials::safe("tread-tga","rubber-tga",Paint));
        CHECK(BodyMaterials::safe("wheelrim-tga","chrome-tga",WheelMetal));CHECK(!BodyMaterials::safe("breaklightson-tga","chrome-tga",WheelMetal));
        CHECK(BodyMaterials::safe("driver-tga","null",OpaquePilot));CHECK(!BodyMaterials::safe("glass-tga","null",OpaquePilot));
        CHECK(!BodyMaterials::safe("window-tga","whitepaint-tga",Paint));
        Lighting s;s.mode=Lighting::Mode::GoldenHour;s.world_brightness=.68f;const uint32_t c=0x7fa0a0a0;
        CHECK(vehicle_surface_color(c,{0,1,0},s,false,Paint)==body_color(c,{0,1,0},s,false));
        CHECK(vehicle_surface_color(c,{0,1,0},s,true,Paint)==body_color(c,{0,1,0},s,true));
        CHECK(vehicle_surface_color(c,{0,1,0},s,false,OpaqueInterior)==vehicle_surface_color(c,{0,-1,0},s,false,OpaqueInterior));
        CHECK((vehicle_surface_color(c,{0,1,0},s,true,WheelRubber)>>24)==0x7f);
        s.mode=Lighting::Mode::Original;CHECK(vehicle_surface_color(c,{0,1,0},s,true,WheelRubber)==c);
        const auto path=std::filesystem::temp_directory_path()/L"atmosphere29-metadata.blm";
        std::vector<uint8_t> b(76+2*390);std::memcpy(b.data(),"BLM3",4);uint32_t v=3,num=2;std::memcpy(b.data()+4,&v,4);std::memcpy(b.data()+8,&num,4);
        for(unsigned i=0;i<2;++i){auto* p=b.data()+76+390*i;std::memcpy(p,"custom",6);std::memcpy(p+32,"wheel",5);std::memcpy(p+64,"wheel-tga",9);std::memcpy(p+160,i?"chrome-tga":"rubber-tga",10);std::memset(p+256,'a',64);std::memset(p+321,i?'c':'b',64);uint32_t role=i?WheelMetal:WheelRubber;std::memcpy(p+386,&role,4);}
        auto write=[&](){const auto h=sha256_bytes(b.data()+76,b.size()-76);std::memcpy(b.data()+12,h.data(),64);std::ofstream f(path,std::ios::binary);f.write(reinterpret_cast<const char*>(b.data()),b.size());};write();
        BodyMaterials m;CHECK(m.load(path)&&m.extended&&m.size()==2);
        CHECK(m.native_capability("custom","wheel-tga","rubber-tga","wheel"));CHECK(!m.native_capability("custom","wheel-tga","rubber-tga"));
        CHECK(m.ps2_capability("custom",std::string(64,'a'),"wheel",std::string(64,'b'))->role==WheelRubber);
        CHECK(m.ps2_capability("custom",std::string(64,'a'),"wheel",std::string(64,'c'))->role==WheelMetal);
        CHECK(!m.ps2_capability("custom",std::string(64,'a'),"wheel"));CHECK(!m.ps2_capability("other",std::string(64,'a'),"wheel",std::string(64,'b')));
        // Shared pixels with different roles close admission; equivalent source
        // aliases of the same class and both textures do not need new hashes.
        auto* second=b.data()+76+390;std::memset(second+321,'b',64);write();BodyMaterials conflict;CHECK(conflict.load(path)&&!conflict.ps2_capability("custom",std::string(64,'a'),"wheel",std::string(64,'b')));
        std::memset(second+64,0,96);std::memcpy(second+64,"wheel643-tga",12);std::memset(second+160,0,96);std::memcpy(second+160,"rubber-tga",10);uint32_t rubber=WheelRubber;std::memcpy(second+386,&rubber,4);write();BodyMaterials alias;CHECK(alias.load(path)&&alias.ps2_capability("custom",std::string(64,'a'),"wheel",std::string(64,'b')));
        b[12]^=1;{std::ofstream f(path,std::ios::binary);f.write(reinterpret_cast<const char*>(b.data()),b.size());}BodyMaterials corrupt;CHECK(!corrupt.load(path));std::filesystem::remove(path);
    }
    {
        RegionalCatalog regions;Lighting base;base.mode=Lighting::Mode::GoldenHour;
        const std::string data="[Regions]\nFranceS1=France\nTurkey2=Turkey\n[Region:France]\nWorldBrightness=0.78\nAmbientR=0.72\nSkyPreset=1\nFogColor=0x8798a4\nSunDirX=-0.42\nSunDirY=0.23\nSunDirZ=0.88\n[Region:Turkey]\nWorldBrightness=0.68\nSkyPreset=3\n[Course:FranceS1]\nWorldBrightness=0.81\nSkyPreset=2\n";
        CHECK(regions.parse(data)&&regions.ready&&regions.bindings()==2&&regions.sha.size()==64);
        auto lit=base;int sky=99;CHECK(regions.apply("RaceTest/FRANCES1",lit,sky)=="france"&&sky==2&&lit.world_brightness==.81f&&lit.fog==0xff8798a4);
        lit=base;CHECK(regions.apply("RaceTest/Turkey2",lit,sky)=="turkey"&&sky==3&&lit.world_brightness==.68f);
        lit=base;CHECK(regions.apply("RaceTest/Unknown",lit,sky).empty()&&sky==-2&&lit.world_brightness==base.world_brightness);
        lit=base;lit.mode=Lighting::Mode::Original;CHECK(regions.apply("RaceTest/Turkey2",lit,sky).empty()&&sky==-2&&lit.world_brightness==base.world_brightness);
        lit=base;CHECK(regions.apply("FrontEnd/Turkey2",lit,sky).empty()&&sky==-2);
        for(const auto& bad:{"[Regions]\nFrance1=Missing\n","[Region:France]\nSkyPreset=6\n","[Region:France]\nExposure=nan\n","[Region:France]\nExposure=2.1\n","[Region:France]\nSunDirX=0\nSunDirY=0\nSunDirZ=0\n","[Region:France]\nSunDirY=1\n","[Region:../France]\nSkyPreset=1\n","[Region:France]\nReflection=4\n","[Region:France]\nAmbientR=1\n[Region:france]\nAmbientR=0\n"}){CHECK(!regions.parse(bad)&&!regions.ready);}
        CHECK(regions.parse(data));CHECK(!regions.load(L"Z:\\missing-region.ini")&&!regions.ready);
        CHECK(regional_scene("racetest/France_S1")=="france_s1"&&regional_scene("RaceTest/../France1").empty());
    }
    D3DMATRIX sun_view{},sun_projection{};sun_view._11=sun_view._22=sun_view._33=sun_view._44=1;
    sun_projection._11=sun_projection._22=1;sun_projection._33=1.01f;sun_projection._43=-1;sun_projection._34=1;
    SunPosition sun_center,sun_translated;
    CHECK(sun_position({0,0,1},sun_view,sun_projection,800,600,sun_center));CHECK(sun_center.x==400&&sun_center.y==300);
    sun_view._41=100000;sun_view._42=-500;CHECK(sun_position({0,0,4},sun_view,sun_projection,800,600,sun_translated));
    CHECK(sun_translated.x==sun_center.x&&sun_translated.radius==sun_center.radius);
    CHECK(!sun_position({0,0,-1},sun_view,sun_projection,800,600,sun_translated));
    CHECK(!sun_position({0,0,0},sun_view,sun_projection,800,600,sun_translated));
    CHECK(!sun_position({10,0,1},sun_view,sun_projection,800,600,sun_translated));
    CHECK(!sun_position({NAN,0,1},sun_view,sun_projection,800,600,sun_translated));
    CHECK(!sun_position({0,0,1},sun_view,sun_view,800,600,sun_translated));
    {   // ATMOSPHERE2.5 sun style: angular sizes, no 32 px cap, procedural layers.
        CHECK(std::abs(sun_center.pixels_per_tan-300.f)<1e-3f);
        CHECK(std::abs(sun_center.radius-std::tan(.9f*.017453293f)*300.f)<1e-3f);
        SunPosition wide;CHECK(sun_position({0,0,1},sun_view,sun_projection,3840,2160,wide,3.f));CHECK(wide.radius>32.f);
        CHECK(SunFx::sprite_intensity(0,0,0,0)==1.f&&SunFx::sprite_intensity(0,.99f,0,0)<.1f&&SunFx::sprite_intensity(0,1,0,0)==0);
        CHECK(SunFx::sprite_intensity(1,0,0,0)>.99f&&SunFx::sprite_intensity(3,0,0,0)==1.f&&SunFx::sprite_intensity(3,.999f,0,0)<.01f);
        const float sector=6.2831853f/72.f;
        CHECK(sun_ray_profile(.2f,0,72)>sun_ray_profile(.2f,sector*.5f,72));   // spoke brighter than the gap
        CHECK(sun_ray_profile(.5f,sector*.5f,72)>0);                          // faint haze between spokes
        CHECK(sun_ray_profile(1.f,0,72)==0&&sun_ray_profile(.5f,0,0)==0&&sun_ray_profile(0,0,72)==0);
        CHECK(std::abs(sun_ray_profile(.3f,6.2831853f-1e-4f,72)-sun_ray_profile(.3f,1e-4f,72))<.02f); // seamless wrap
        float shortest=1,longest=0;for(unsigned k=0;k<72;++k){const float l=.3f+.7f*std::pow(sun_ray_hash(k,1),.7f);shortest=std::min(shortest,l);longest=std::max(longest,l);}
        CHECK(shortest<.6f&&longest>.9f);                                    // irregular lengths, not a cartoon star
        const auto defaults=read_sun_style(L"Z:\\missing\\Atmosphere.ini");
        CHECK(defaults.ray_count==72&&defaults.ray_texture.empty()&&defaults.core_degrees==.9f&&defaults.glow_degrees>defaults.core_degrees&&defaults.ray_count%2==0);
        // ATMOSPHERE6 P1: moon defaults (no spokes/flare, cool core) and stars.
        const auto moon=read_sun_style(L"Z:\\missing\\Atmosphere.ini",true);
        CHECK(moon.rays==0&&moon.flare==0&&moon.core>0&&moon.core_rgb[2]>=moon.core_rgb[0]&&moon.glow<defaults.glow);
        CHECK(read_star_style(L"Z:\\missing\\Atmosphere.ini").count==0&&read_star_style(L"Z:\\missing\\Atmosphere.ini",true).count==1400);
        const auto field=star_field(500,6),again=star_field(500,6);bool upper=true,unit=true,same=true;float bright=0;
        for(size_t i=0;i<field.size();++i){const auto& v=field[i].direction;upper=upper&&v[1]>=0;unit=unit&&std::abs(v[0]*v[0]+v[1]*v[1]+v[2]*v[2]-1)<1e-4f;
            same=same&&v==again[i].direction&&field[i].magnitude==again[i].magnitude;bright=std::max(bright,field[i].magnitude);}
        CHECK(field.size()==500&&upper&&unit&&same&&bright>.5f);
        // ATMOSPHERE6.3 P2 headlight projector math.
        CHECK(headlight_cookie(0,.5f)==0&&headlight_cookie(.5f,1)==0&&headlight_cookie(.5f,.55f)>.4f&&headlight_cookie(.5f,.2f)<headlight_cookie(.5f,.55f));
        CHECK(headlight_ramp(0)==0&&headlight_ramp(1)==0&&headlight_ramp(.05f)>headlight_ramp(.6f)&&headlight_ramp(.6f)>0);
        CHECK(tail_cookie(.5f,.5f)>.9f&&tail_cookie(.02f,.02f)==0);
        const Mat4 identity_car{1,0,0,0, 0,1,0,0, 0,0,1,0, 0,0,0,1};Projector flat;flat.pitch_degrees=0;
        const auto beam=light_frame(identity_car,flat);
        CHECK(beam.valid&&std::abs(beam.forward[2]-1)<1e-5f&&std::abs(beam.right[0]-1)<1e-5f&&std::abs(beam.up[1]-1)<1e-5f&&std::abs(beam.position[2]-2.1f)<1e-5f);
        Mat4 inverse_view{};CHECK(mat_inverse(identity_car,inverse_view));
        const auto cookie=cookie_matrix(inverse_view,beam,flat),ramp=ramp_matrix(inverse_view,beam,flat);
        auto apply=[](const Mat4& m,float x,float y,float z){std::array<float,4> o{};for(unsigned j=0;j<4;++j)o[j]=x*m[j]+y*m[4+j]+z*m[8+j]+m[12+j];return o;};
        const auto ahead=apply(cookie,0,.65f,12.1f);CHECK(ahead[2]>0&&std::abs(ahead[0]/ahead[2]-.5f)<1e-4f&&std::abs(ahead[1]/ahead[2]-.5f)<1e-4f);
        const auto right=apply(cookie,3,.65f,12.1f);CHECK(right[0]/right[2]>.5f);
        const auto r=apply(ramp,0,.65f,12.1f);CHECK(std::abs(r[0]-10/flat.range)<1e-4f&&std::abs(r[1]-.5f)<1e-5f);
        CHECK(apply(ramp,0,.65f,-5)[0]<0);                                  // behind the lamp -> black ramp texel
        CHECK(light_reaches(beam,flat,{0,0,20},2)&&!light_reaches(beam,flat,{0,0,-20},2)&&!light_reaches(beam,flat,{0,0,200},2));
        CHECK(!read_glint_style(L"Z:\missing\Atmosphere.ini").enabled&&read_glint_style(L"Z:\missing\Atmosphere.ini",true).enabled);
        CHECK(read_headlight_style(L"Z:\missing\Atmosphere.ini",true).enabled&&read_headlight_style(L"Z:\missing\Atmosphere.ini",true).lamp_emissive>1);
        Mat4 m{2,0,0,0, 0,3,0,0, 0,0,4,0, 1,2,3,1},mi{};CHECK(mat_inverse(m,mi));const auto e=mat_mul(m,mi);CHECK(std::abs(e[0]-1)<1e-5f&&std::abs(e[13])<1e-5f&&std::abs(e[15]-1)<1e-5f);
    }
    {   // A rig seed follows the SAME lens triangle under damage, including its normal.
        std::vector<LampVec> lens{{-.2f,.5f,2},{.2f,.5f,2},{0,.9f,2}};
        const std::vector<uint32_t> topology{0,1,2};LampSurfaceAnchor anchor;
        CHECK(bind_lamp_surface({0,.65f,2.01f},true,lens,topology,anchor));
        LampVec initial{},axis{};CHECK(anchor.evaluate(lens,initial,axis));
        CHECK(std::abs(initial[1]-.65f)<1e-5f&&std::abs(initial[2]-2.01f)<1e-5f&&axis[2]>.99f);
        auto damaged=lens;for(auto& point:damaged){point[0]+=.3f;point[1]-=.12f;point[2]-=.25f;}
        LampVec moved{};CHECK(anchor.evaluate(damaged,moved,axis));
        CHECK(std::abs(moved[0]-initial[0]-.3f)<1e-5f&&std::abs(moved[1]-initial[1]+.12f)<1e-5f&&std::abs(moved[2]-initial[2]+.25f)<1e-5f);
        // A rotated/dented lamp also changes the emission direction.
        for(size_t i=0;i<lens.size();++i)damaged[i]={lens[i][2],lens[i][1],-lens[i][0]};
        CHECK(anchor.evaluate(damaged,moved,axis)&&axis[0]>.99f&&std::abs(axis[2])<1e-5f);
        CHECK(!anchor.evaluate(std::vector<LampVec>(3,LampVec{0,0,0}),moved,axis));
        CHECK(!anchor.evaluate(std::vector<LampVec>(2),moved,axis));
        CHECK(!bind_lamp_surface({0,.65f,-2},false,lens,topology,anchor)); // another lamp is not a substitute
        CHECK(!bind_lamp_surface({0,.65f,2},true,lens,{0,1,99},anchor));
        auto invalid=lens;invalid[0][0]=std::numeric_limits<float>::quiet_NaN();
        CHECK(!bind_lamp_surface({0,.65f,2},true,invalid,topology,anchor));
    }
    {   // Switch-node attachments identify topology by expanded UVs, not VB-local numbering or damaged positions.
        std::vector<uint8_t> bytes(3*24);const float xyz[3][3]={{0,0,-2},{1,0,-2},{0,1,-2}},uv[3][2]={{-0.f,0},{1,0},{0,1}};
        for(unsigned i=0;i<3;++i){std::memcpy(bytes.data()+i*24,xyz[i],12);std::memcpy(bytes.data()+i*24+16,uv[i],8);}
        std::vector<LampVec> positions;std::string signature;
        // Native compiler swaps the source first pair. Sidecar UVs, weights
        // and normal remain in source-DX order, including asymmetric weights.
        CHECK(lamp_attachment_geometry(bytes,24,{1,0,2},positions,signature));
        const float normalized_uv[6]={0,0,1,0,0,1};CHECK(signature==sha256_bytes(normalized_uv,sizeof(normalized_uv)));
        auto moved_bytes=bytes;for(unsigned i=0;i<3;++i){float x=0;std::memcpy(&x,moved_bytes.data()+i*24,4);x+=.4f;std::memcpy(moved_bytes.data()+i*24,&x,4);}
        std::vector<LampVec> moved;std::string moved_signature;CHECK(lamp_attachment_geometry(moved_bytes,24,{1,0,2},moved,moved_signature)&&moved_signature==signature);
        auto reordered=bytes;std::memcpy(reordered.data(),bytes.data()+24,48);std::memcpy(reordered.data()+48,bytes.data(),24);
        CHECK(lamp_attachment_geometry(reordered,24,{0,2,1},moved,moved_signature)&&moved_signature==signature&&moved==positions);
        CHECK(lamp_attachment_geometry(bytes,24,{0,1,2},moved,moved_signature)&&moved_signature!=signature); // old probe input was wrong
        std::vector<uint8_t> normals_layout(3*36);
        for(unsigned i=0;i<3;++i){std::memcpy(normals_layout.data()+i*36,bytes.data()+i*24,12);std::memcpy(normals_layout.data()+i*36+28,bytes.data()+i*24+16,8);}
        CHECK(lamp_attachment_geometry(normals_layout,36,{1,0,2},moved,moved_signature)&&moved_signature==signature&&moved==positions);
        CHECK(!lamp_attachment_geometry(bytes,24,{0,1,99},moved,moved_signature));
        CHECK(!lamp_attachment_geometry(bytes,32,{0,1,2},moved,moved_signature));
        LampRigs rigs;rigs.sha=std::string(64,'a');LampRig rig;rig.car="Fixture";rig.points.resize(2);rig.points[0].kind=2;rig.points[0].tail=true;rig.points[1].kind=3;rigs.rigs.push_back(rig);
        const auto texture=std::string(64,'b');
        const auto payload="Fixture 0 "+texture+" "+signature+" 3 0 .2 .3 .5 0 -1 0\nFixture 1 "+texture+" "+signature+" 3 0 .2 .3 .5 0 -1 0\n";
        const auto path=std::filesystem::temp_directory_path()/("mrr-lamp-attachment-"+std::to_string(GetCurrentProcessId())+".lpa");
        auto write=[&](const std::string& contents,const std::string& rig_sha){std::ofstream file(path,std::ios::binary);file<<"LPA1 "<<rig_sha<<" "<<sha256_bytes(contents.data(),contents.size())<<"\n"<<contents;};
        write(payload,rigs.sha);LampAttachments attachments;CHECK(attachments.load(path,rigs)&&attachments.ready&&attachments.rows.size()==2);
        CHECK(attachments.manages(0,0)&&attachments.manages(0,1)&&!attachments.manages(1,0));
        CHECK(attachments.signature_known(texture,signature,3)&&!attachments.signature_known(texture,signature,6));
        Pilot p(false,L"Z:\\missing\\MRRRenderer.ini");p.lamp_rigs=rigs;p.lamp_attachments=attachments;p.rig_race=22;
        const Mat4 identity{1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1};
        LampAttachmentDraw draw;draw.texture=texture;draw.uv=signature;draw.world=identity;draw.positions=positions;
        p.lamp_attachment_queue.begin(10,22,3);CHECK(p.lamp_attachment_queue.push(draw)); // owner arrives AFTER switch draw
        p.observe_car(0x1000,identity,10);auto* owner=p.rig_owner(0x1000,10,true);owner->rig=0;
        resolve_lamp_attachments(p,10,22,3);CHECK(p.lamp_points.size()==2&&p.lamp_points[0].kind==1&&p.lamp_points[1].kind==3);
        CHECK(std::abs(p.lamp_points[0].world[0]-.3f)<1e-5f&&std::abs(p.lamp_points[0].world[1]-.5f)<1e-5f);
        resolve_lamp_attachments(p,10,22,3);CHECK(p.lamp_points.size()==2); // drain is once per frame
        p.lamp_attachment_queue.begin(11,22,3);draw.positions[0][0]+=.6f;CHECK(p.lamp_attachment_queue.push(draw));
        p.observe_car(0x1000,identity,11);owner->braking=11;resolve_lamp_attachments(p,11,22,3);
        CHECK(p.lamp_points.size()==2&&p.lamp_points[0].kind==2&&std::abs(p.lamp_points[0].world[0]-.42f)<1e-5f);
        for(unsigned failure=0;failure<6;++failure){const uint64_t frame=20+failure;p.lamp_points.clear();p.lamp_points_frame=frame;
            p.lamp_attachment_queue.begin(frame,22,3);auto invalid=draw;
            p.car_poses={};p.observe_car(0x1000,identity,failure==0?frame-1:frame);
            if(failure==1)p.observe_car(0x2000,identity,frame); // ambiguous identical WORLD
            if(failure==2)invalid.owner=0x3000; // explicit owner must agree too
            if(failure==3)invalid.uv=std::string(64,'c');
            if(failure==4)invalid.texture=std::string(64,'c');
            if(failure==5)invalid.positions.assign(3,LampVec{});
            CHECK(p.lamp_attachment_queue.push(invalid));resolve_lamp_attachments(p,frame,22,3);CHECK(p.lamp_points.empty());}
        p.lamp_points.clear();p.lamp_attachment_queue.begin(30,22,3);CHECK(p.lamp_attachment_queue.push(draw));p.observe_car(0x1000,identity,30);
        resolve_lamp_attachments(p,30,23,3);CHECK(p.lamp_points.empty());resolve_lamp_attachments(p,30,22,4);CHECK(p.lamp_points.empty());
        write(payload,std::string(64,'c'));CHECK(!attachments.load(path,rigs)&&!attachments.ready&&!attachments.manages(0,0));
        write(payload+"Fixture 99 "+texture+" "+signature+" 3 0 .2 .3 .5 0 -1 0\n",rigs.sha);
        CHECK(!attachments.load(path,rigs)&&!attachments.manages(0,0)); // no partial admission
        write(payload,rigs.sha);{std::ofstream file(path,std::ios::binary|std::ios::app);file<<"tamper";}
        CHECK(!attachments.load(path,rigs)&&!attachments.ready);std::filesystem::remove(path);
    }
    SunFx no_depth_sun;Native missing_depth;
    CHECK(no_depth_sun.render(missing_depth,sun_center,true,true,true,nullptr,nullptr)==S_FALSE);CHECK(missing_depth.calls==0);
    SunNative sun_restore;SunTransaction sun_transaction;
    CHECK(sun_transaction.capture(sun_restore,nullptr,nullptr)==S_OK);
    CHECK(sun_transaction.set(sun_restore,0,0,D3DRS_ZWRITEENABLE,FALSE)==S_OK);
    sun_restore.fail=sun_restore.calls+1;CHECK(FAILED(sun_transaction.restore(sun_restore)));CHECK(sun_transaction.pending());
    CHECK(sun_transaction.capture(sun_restore,nullptr,nullptr)==D3DERR_DEVICELOST);
    sun_restore.fail=0;CHECK(sun_transaction.restore(sun_restore)==S_OK);CHECK(sun_restore.zwrite==TRUE);CHECK(!sun_transaction.pending());CHECK(sun_restore.target.refs==1&&sun_restore.depth.refs==1);
    CHECK(sun_transaction.capture(sun_restore,nullptr,nullptr)==S_OK);D3DVIEWPORT8 sun_viewport{0,0,800,600,0,1};
    CHECK(sun_transaction.target(sun_restore,&sun_restore.target,&sun_restore.depth,sun_viewport)==S_OK);
    sun_restore.fail=sun_restore.calls+1;CHECK(FAILED(sun_transaction.restore(sun_restore)));CHECK(sun_transaction.pending());
    sun_restore.fail=0;CHECK(sun_transaction.restore(sun_restore)==S_OK);CHECK(!sun_transaction.pending());
    CHECK(pc_water_factor(Lighting{})==0xffffffff);
    CHECK(environment_texel(0x003579ab,0xffffffff)==0x003579ab);
    CHECK(environment_texel(0x7f80ff00,0xff808080)==0x7f408000);

    CHECK(pc_water_secondary("2cc07bb39117f1f0c102e6007a9dfb2245a7f6180a578352d6b7ba09b2f705f6"));
    CHECK(!pc_water_secondary(std::string(64,'0')));
    Lighting sunset_water;sunset_water.mode=Lighting::Mode::GoldenHour;sunset_water.world_brightness=.68f;
    const auto water_factor=pc_water_factor(sunset_water);CHECK(water_factor>>24==255);CHECK((water_factor&255)>((water_factor>>16)&255));CHECK((water_factor&255)<255);
    CHECK(pc_water_factor(sunset_water,0x7f123456)>>24==0x7f);
    {auto dark=sunset_water;dark.ambient_strength=.06f;const auto d=pc_water_factor(dark);CHECK((d&255)*4<(water_factor&255));} // ATMOSPHERE5.11 night water
    CHECK(parse_preset(L"Auto")==-1&&parse_preset(nullptr)==-1);
    CHECK(parse_preset(L"0")==0&&parse_preset(L"5")==5);
    CHECK(parse_preset(L"6")==-1&&parse_preset(L"-1")==-1&&parse_preset(L"3x")==-1&&parse_preset(L" 3")==-1);
    CHECK(tint(0x7f80a0c0,1,1,1)==0x7f80a0c0);
    CHECK((tint(0x2580a0c0,1,.86f,.68f,.4f)>>24)==0x25);
    CHECK((tint(0x25ffffff,1,1,1,.4f)&0xffffff)==0xffffff);
    CHECK(point_light(0,0,0,0,0,0,12)>.39f);
    CHECK(point_light(12,0,0,0,0,0,12)==0&&point_light(20,0,0,0,0,0,12)==0);
    CHECK(point_light(0,0,0,0,0,0,0)==0);
    CHECK(point_light(6,0,0,0,0,0,12)>0&&point_light(6,0,0,0,0,0,12)<point_light(0,0,0,0,0,0,12));
    // A movable source actually changes vertex illumination; no hardware light
    // or normal field is assumed on the prelit road mesh.
    CHECK(point_light(0,0,0,24,0,0,12)==0&&point_light(0,0,0,0,0,0,12)>0);
    D3DMATRIX v{},p{};v._11=v._22=v._33=v._44=1;p._11=p._22=p._34=1;p._33=1.001f;p._43=-.1f;
    CHECK(project_sun(v,p,0,0,1).inside);
    CHECK(!project_sun(v,p,0,0,-1).inside&&!project_sun(v,p,4,0,1).inside);
    CHECK(!sun_visible(true,false,1)&&!sun_visible(true,true,.9f));
    CHECK(!sun_visible(true,true,std::numeric_limits<float>::quiet_NaN()));
    CHECK(sun_visible(true,true,1)&&!sun_visible(false,true,1));
    Pixels pix;CHECK(!decode_sky({},pix));
    std::vector<uint8_t> bytes(20+256*256*4,0);uint32_t h[5]={0xfeed,0,0,256,256};std::memcpy(bytes.data(),h,20);
    CHECK(decode_sky(bytes,pix)&&pix.bgra.size()==256*256);
    bytes.push_back(0);CHECK(!decode_sky(bytes,pix)&&pix.bgra.empty());bytes.pop_back();bytes[0]=0;CHECK(!decode_sky(bytes,pix));
    Pilot off(false,L"Z:\\nonexistent-atmosphere-test\\MRRRenderer.ini");
    CHECK(!off.enabled()&&!off.custom()&&!off.pending.any()&&!off.scratch);
    CHECK(!off.pc_noise_identity.requested());
    Broker broker;CHECK(readiness(broker).accepted);
    broker.players_key=false;CHECK(!readiness(broker).accepted&&std::string(readiness(broker).reason)=="network_players_key_absent");
    broker.players_key=true;broker.word(0x21008,0);CHECK(!readiness(broker).accepted);broker.word(0x21008,2);
    broker.word(0x22000,1);CHECK(!readiness(broker).accepted);broker.word(0x22000,0);
    broker.sync_key=false;CHECK(!readiness(broker).accepted);broker.sync_key=true;
    broker.word(0x21024,2);CHECK(!readiness(broker).accepted);broker.word(0x21024,0);
    broker.word(0x22004,1);CHECK(!readiness(broker).accepted);broker.word(0x22004,0);CHECK(readiness(broker).accepted);
    // Early acceptance requires an exact unconstructed slot AND positive native
    // upstream/context proofs. A missing/wrong-type source is never false.
    broker.pending_sync();CHECK(!readiness(broker).accepted);CHECK(readiness(broker,true).accepted);
    CHECK(readiness(broker,true).sync.unpublished);
    for(auto mutation:std::vector<std::pair<uint32_t,uint32_t>>{{0x2101c,1},{0x21020,0x22004},{0x21024,0},
        {0x21040,2},{0x22008,1},{0x2200c,0},{0x2200c,2},{0x22010,9},{0x22014,1},{0x21094,2}}){
        Broker bad;bad.pending_sync();bad.word(mutation.first,mutation.second);CHECK(!readiness(bad,true).accepted);}
    Broker unreadable;unreadable.pending_sync();unreadable.bytes.erase(0x2101c);CHECK(!readiness(unreadable,true).accepted);
    Broker missing_source;missing_source.pending_sync();missing_source.bytes.erase(0x22008);CHECK(!readiness(missing_source,true).accepted);
    Broker native_default;native_default.pending_sync();native_default.word(0x2103c,0);native_default.word(0x21040,12);
    CHECK(readiness(native_default,true).accepted&&readiness(native_default,true).browse.native_null);
    CHECK(!readiness(native_default,false).accepted);
    for(auto mutation:std::vector<std::pair<uint32_t,uint32_t>>{{0x21038,0},{0x21038,99},{0x2103c,0x22008},
        {0x21040,0},{0x21040,2},{0x21040,13},{0x22000,1},{0x2200c,2},{0x22010,9},{0x22014,1}}){
        auto bad=native_default;bad.word(mutation.first,mutation.second);CHECK(!readiness(bad,true).accepted);}
    for(int preset:{0,3,5}){CHECK(choose(0,preset,true,true,true)==preset);CHECK(choose(0,preset,true,false,true)==0);
        CHECK(choose(0,preset,false,true,true)==0);CHECK(choose(4,preset,true,true,false)==4);}
    CHECK(choose(4,-1,true,true,true)==4);
    // Diagnostic lifetimes revoke cached texture evidence on Reset.
    off.diagnostic_epoch(1,0);off.sky_cache[0].pointer=42;off.diagnostic_epoch(1,1);CHECK(!off.sky_cache[0].pointer);
    for(int failed=0;failed<=4;++failed){
        Native native;native.fail=failed;auto& saved=off.pending;
        saved.texture_changed=saved.stream_changed=saved.indices_changed=saved.fog_changed=true;
        std::vector<uint32_t> slots;
        auto note=[&](uint32_t slot,const Args&,HRESULT){slots.push_back(slot);};
        const auto hr=restore_pending(off,native,note);
        CHECK((failed?FAILED(hr):SUCCEEDED(hr))&&native.calls==4);
        CHECK(slots==std::vector<uint32_t>({50,85,83,61}));
        CHECK(saved.any()==(failed!=0));
        // Failed restore survives, then only that slot is retried. The next
        // game draw is blocked until this repair succeeds.
        if(failed){slots.clear();native.fail=0;CHECK(SUCCEEDED(restore_pending(off,native,note)));CHECK(slots.size()==1&&!saved.any());}
    }
    {Native native;native.fail=1;off.pending.environment_changed=true;
        auto note=[](uint32_t slot,const Args& args,HRESULT){CHECK(slot==61&&args.a[0]==1);};
        CHECK(FAILED(restore_pending(off,native,note))&&off.pending.environment_changed);
        native.fail=0;CHECK(SUCCEEDED(restore_pending(off,native,note))&&!off.pending.any());}
    // Each environment state survives a failed restoration and is retried.
    for(unsigned failed=1;failed<=8;++failed){Native native;native.fail=failed;off.pending.body_pending=255;
        auto note=[](uint32_t,const Args&,HRESULT){};CHECK(FAILED(restore_pending(off,native,note)));
        CHECK(off.pending.body_pending==(1u<<(failed-1)));native.fail=0;
        CHECK(SUCCEEDED(restore_pending(off,native,note))&&!off.pending.any());}
    Lighting scene;scene.mode=Lighting::Mode::GoldenHour;
    const DWORD gray=0x7fa0a0a0;const auto lit=scene_color(gray,scene.direction,scene);
    std::array<float,3> away{};for(unsigned i=0;i<3;++i)away[i]=-scene.direction[i];
    const auto shaded=scene_color(gray,away,scene);
    CHECK((lit>>24)==0x7f&&(shaded>>24)==0x7f);
    CHECK(((lit>>16)&255)>(lit&255));CHECK(((shaded>>16)&255)<(shaded&255));
    scene.strength=0;CHECK(scene_color(gray,away,scene)==gray);
    scene.strength=1;scene.mode=Lighting::Mode::Original;CHECK(scene_color(gray,away,scene)==gray);
    scene.mode=Lighting::Mode::GoldenHour;scene.fog_enabled=true;scene.fog=0xffc86432;scene.fog_strength=.5f;
    CHECK(scene_fog(0x7f000000,scene)==0x7f643219);
    scene.fog_enabled=false;CHECK(scene_fog(0x7f123456,scene)==0x7f123456);
    SceneColors cached;std::vector<uint32_t> indices{0,1,0};
    std::vector<std::array<float,3>> source_normals{scene.direction,away,scene.direction};
    CHECK(cached.bake(source_normals,indices,{gray,gray,0x12345678},scene));
    CHECK(cached.matches(indices,3,scene));
    CHECK(cached.colors[0]==lit&&cached.colors[1]==shaded&&cached.colors[2]==0x12345678&&!cached.used[2]);
    auto exposure=scene;exposure.exposure=1.25f;CHECK(!cached.matches(indices,3,exposure));
    CHECK(!cached.matches({1,0,0},3,scene));
    CHECK(!cached.bake(source_normals,{0,1,3},{gray,gray,gray},scene)&&!cached.ready);
    CHECK(!cached.bake({},indices,{gray,gray,gray},scene));
    // Universal resolver: topology can change without a source object digest.
    Lighting evening=scene;evening.direction={0,1,0};evening.world_brightness=.6f;
    ResolvedGeometry mesh;mesh.original.resize(4*24);const float positions[4][3]={{0,0,0},{1,0,0},{0,0,1},{1,0,1}};
    for(unsigned i=0;i<4;++i){std::memcpy(mesh.original.data()+24*i,positions[i],12);std::memcpy(mesh.original.data()+24*i+12,&gray,4);}
    const uint16_t tri[3]={7,8,9};mesh.index_bytes.resize(6);std::memcpy(mesh.index_bytes.data(),tri,6);
    CHECK(light_geometry(mesh,24,7,4,2,nullptr,true,true,false,true,evening)&&mesh.category==2&&mesh.changed==3);
    CHECK(!std::memcmp(mesh.original.data()+72,mesh.lit.data()+72,24)); // unreferenced vertex remains native
    CHECK(mesh.original!=mesh.lit);
    const uint16_t altered[6]={7,8,9,8,10,9};mesh.index_bytes.resize(12);std::memcpy(mesh.index_bytes.data(),altered,12);
    CHECK(light_geometry(mesh,24,7,4,2,nullptr,true,true,false,true,evening)&&mesh.changed==4);
    CHECK(!light_geometry(mesh,24,7,4,2,nullptr,false,true,false,true,evening));
    CHECK(!light_geometry(mesh,24,7,4,2,nullptr,true,false,false,true,evening));
    CHECK(!light_geometry(mesh,24,7,4,2,nullptr,true,true,true,true,evening));
    SceneMaterial water;water.category=0;water.flags=Deny;
    CHECK(!light_geometry(mesh,24,7,4,2,&water,true,true,false,true,evening));
    SceneMaterial leaves;leaves.category=3;leaves.flags=Plain|AlphaTest|TwoSided;
    CHECK(light_geometry(mesh,24,7,4,2,&leaves,false,false,true,false,evening));
    SceneMaterial panel;panel.category=4;panel.flags=Plain|AlphaTest;
    CHECK(source_opaque_pass(&panel,false,false,true));
    CHECK(!source_opaque_pass(&panel,false,true,true));
    CHECK(light_geometry(mesh,24,7,4,2,&panel,false,true,true,false,evening));
    for(unsigned i=0;i<4;++i){CHECK(mesh.original[i*24+15]==mesh.lit[i*24+15]);
        CHECK(!std::memcmp(mesh.original.data()+i*24+16,mesh.lit.data()+i*24+16,8));}
    {   // Instanced props: a translated WORLD lights like identity; a mirrored or
        // rotated matrix turns the face; malformed matrices fail closed.
        Lighting side=evening;side.direction={0,0,1};
        ResolvedGeometry wall;wall.original.resize(3*24);const float upright[3][3]={{0,0,0},{0,1,0},{1,0,0}};
        for(unsigned i=0;i<3;++i){std::memcpy(wall.original.data()+24*i,upright[i],12);std::memcpy(wall.original.data()+24*i+12,&gray,4);}
        const uint16_t face[3]={0,1,2};wall.index_bytes.resize(6);std::memcpy(wall.index_bytes.data(),face,6);
        SceneMaterial board;board.category=4;board.flags=Plain|AlphaTest;board.winding=-1;
        CHECK(light_geometry(wall,24,0,3,2,&board,false,true,false,false,side)&&!wall.has_world);
        const auto native=wall.lit;const auto native_normal=wall.effective_normals[0];
        std::array<float,16> moved{1,0,0,0, 0,1,0,0, 0,0,1,0, 2805.6f,45.7f,-248.9f,1};
        CHECK(light_geometry(wall,24,0,3,2,&board,false,true,false,false,side,nullptr,"",{},false,&moved));
        CHECK(wall.lit==native&&wall.has_world&&wall.lit_for(&moved)&&!wall.lit_for(nullptr));
        std::array<float,16> turned{-1,0,0,0, 0,1,0,0, 0,0,-1,0, 0,0,0,1};   // 180 degrees about Y
        CHECK(light_geometry(wall,24,0,3,2,&board,false,true,false,false,side,nullptr,"",{},false,&turned)&&wall.lit!=native);
        CHECK(std::abs(wall.effective_normals[0][2]+native_normal[2])<1e-5f&&std::abs(native_normal[2])>.99f);
        std::array<float,16> mirror{-1,0,0,0, 0,1,0,0, 0,0,1,0, 0,0,0,1};    // det<0 keeps the outward face
        CHECK(light_geometry(wall,24,0,3,2,&board,false,true,false,false,side,nullptr,"",{},false,&mirror)&&wall.lit==native);
        std::array<float,16> projective=moved;projective[3]=.5f;
        CHECK(!light_geometry(wall,24,0,3,2,&board,false,true,false,false,side,nullptr,"",{},false,&projective));
        std::array<float,16> flat{};flat[15]=1;
        CHECK(!light_geometry(wall,24,0,3,2,&board,false,true,false,false,side,nullptr,"",{},false,&flat));
    }
    panel.flags=Plain;CHECK(!light_geometry(mesh,24,7,4,2,&panel,false,true,true,false,evening));
    panel.flags=Plain|AlphaTest|Deny;CHECK(!source_opaque_pass(&panel,false,false,true));
    const uint16_t two_sided[]={7,8,9,9,8,7};mesh.index_bytes.resize(12);std::memcpy(mesh.index_bytes.data(),two_sided,12);
    CHECK(light_geometry(mesh,24,7,4,2,&leaves,false,false,true,false,evening));
    SceneMaterial paired_ground;paired_ground.category=2;paired_ground.flags=Noise;
    CHECK(light_geometry(mesh,24,7,4,2,&paired_ground,true,true,false,false,evening));
    CHECK(mesh.duplicate_faces==1&&mesh.opposite_faces==1);
    {   // Paired thin static props mix sun- and shadow-side colour; leaves do not.
        CHECK(mix_color(0xff646464,0xff000000,.5f)==0xff323232&&mix_color(0x80ffffff,0xff000000,1)==0x80ffffff);
        SceneMaterial rail;rail.category=4;rail.flags=Plain|AlphaTest;
        CHECK(light_geometry(mesh,24,7,4,2,&rail,false,true,false,false,evening));const auto rail_lit=mesh.lit;
        CHECK(light_geometry(mesh,24,7,4,2,&leaves,false,false,true,false,evening));const auto leaf_lit=mesh.lit;
        uint32_t r=0,l=0;std::memcpy(&r,rail_lit.data()+12,4);std::memcpy(&l,leaf_lit.data()+12,4);
        CHECK(((r>>16)&255)<((l>>16)&255));                    // rail is no longer fully sun-lit
        CHECK(light_geometry(mesh,24,7,4,2,&paired_ground,true,true,false,false,evening)); // restore for the order check below
    }
    const auto paired_colors=mesh.lit;
    const uint16_t back_first[]={9,8,7,7,8,9};std::memcpy(mesh.index_bytes.data(),back_first,12);
    CHECK(light_geometry(mesh,24,7,4,2,&paired_ground,true,true,false,false,evening));
    CHECK(mesh.lit==paired_colors&&mesh.opposite_faces==1); // no index-order dependence
    for(const auto& normal:mesh.effective_normals)for(float x:normal)CHECK(std::isfinite(x));
    CHECK(!light_geometry(mesh,24,8,4,2,&leaves,false,false,true,false,evening));
    mesh.original[0]=0;const float invalid_position=std::numeric_limits<float>::quiet_NaN();std::memcpy(mesh.original.data(),&invalid_position,4);
    CHECK(!light_geometry(mesh,24,7,4,2,&leaves,false,false,true,false,evening));
    ResolvedGeometry evidence;evidence.original={1,2,3};evidence.index_bytes={4,5};evidence.vertex_revision=7;evidence.index_revision=8;
    bool compared=false;const uint8_t same_v[]={1,2,3},same_i[]={4,5},changed_v[]={1,9,3},changed_i[]={4,6};
    CHECK(evidence.same_source(same_v,3,same_i,2,7,8,compared)&&!compared);
    CHECK(evidence.same_source(same_v,3,same_i,2,9,10,compared)&&compared);
    CHECK(!evidence.same_source(changed_v,3,same_i,2,9,10,compared)&&compared);
    CHECK(!evidence.same_source(same_v,3,changed_i,2,9,10,compared)&&compared);
    CHECK(!evidence.same_source(same_v,2,same_i,2,7,8,compared));
    std::array<float,16> world{};world[0]=2;world[5]=1;world[10]=.5f;world[15]=1;std::array<float,3> normal{};
    CHECK(transformed_normal({1,1,0},world,normal)&&normal[1]>normal[0]);
    world[10]=0;CHECK(!transformed_normal({0,1,0},world,normal));
    SceneResolver bounded;CHECK(bounded.room(1024));bounded.bytes=SceneResolver::max_bytes;CHECK(!bounded.room(1));bounded.clear();CHECK(bounded.bytes==0&&bounded.cache_resets==1);
    const auto metadata_test=std::filesystem::temp_directory_path()/L"atmosphere21-metadata-test.lsm";
    std::vector<uint8_t> metadata_bytes(76+237);std::memcpy(metadata_bytes.data(),"LSM1",4);uint32_t version=1,one=1,cat=2,flags=Noise;int32_t winding=-1;
    std::memcpy(metadata_bytes.data()+4,&version,4);std::memcpy(metadata_bytes.data()+8,&one,4);auto* row=metadata_bytes.data()+76;
    std::memcpy(row,"CustomLayout",12);std::memcpy(row+64,"custom_ground",13);std::memset(row+160,'a',64);
    std::memcpy(row+225,&cat,4);std::memcpy(row+229,&flags,4);std::memcpy(row+233,&winding,4);
    const auto metadata_sha=sha256_bytes(row,237);std::memcpy(metadata_bytes.data()+12,metadata_sha.data(),64);
    {std::ofstream f(metadata_test,std::ios::binary);f.write(reinterpret_cast<const char*>(metadata_bytes.data()),metadata_bytes.size());}
    LightingMetadata custom;CHECK(custom.load(metadata_test)&&custom.size()==1&&custom.find("CustomLayout",std::string(64,'a')));
    CHECK(!custom.find("OtherLayout",std::string(64,'a')));
    {auto common_bytes=metadata_bytes;auto* common_row=common_bytes.data()+76;std::memset(common_row,0,64);std::memcpy(common_row,"Common",6);
        const auto hash=sha256_bytes(common_row,237);std::memcpy(common_bytes.data()+12,hash.data(),64);
        {std::ofstream f(metadata_test,std::ios::binary);f.write(reinterpret_cast<const char*>(common_bytes.data()),common_bytes.size());}
        LightingMetadata shared;CHECK(shared.load(metadata_test)&&shared.find("AnyLayout",std::string(64,'a'))&&!shared.only_course("AnyLayout"));}

    CHECK(custom.find("customlayout",std::string(64,'a'))&&custom.only_course("CUSTOMLAYOUT")&&!custom.only_course("OtherLayout"));
    CHECK(canonical_course("../outside").empty()&&canonical_course("RaceTest/Layout").empty());
    {
        const auto packages=std::filesystem::temp_directory_path()/(L"mrr-atmo27-"+std::to_wstring(GetCurrentProcessId()));
        std::filesystem::create_directories(packages/L"customlayout");std::filesystem::create_directories(packages/L"otherlayout");
        for(const auto* folder:{L"customlayout",L"otherlayout"}){std::ofstream f(packages/folder/L"materials.lsm",std::ios::binary);f.write(reinterpret_cast<const char*>(metadata_bytes.data()),metadata_bytes.size());}
        off.package_root=packages;off.course_dirty=true;CHECK(off.select_course("CustomLayout"));const auto reload=off.package_reloads;
        off.resolver.entries.emplace(ResolverKey{},ResolvedGeometry{});CHECK(off.select_course("CustomLayout")&&off.package_reloads==reload&&off.resolver.entries.size()==1);
        off.course_dirty=true;CHECK(off.select_course("CustomLayout")&&off.resolver.entries.empty()&&off.package_reloads==reload+1);
        CHECK(!off.select_course("../outside"));CHECK(!off.select_course("OtherLayout")&&!off.metadata.ready);
        CHECK(off.select_course("CUSTOMLAYOUT")&&off.normal_hints.records==0);off.package_root.clear();
        for(const auto* folder:{L"customlayout",L"otherlayout"}){std::filesystem::remove(packages/folder/L"materials.lsm");std::filesystem::remove(packages/folder);}std::filesystem::remove(packages);
    }
    {
        const auto packages=std::filesystem::temp_directory_path()/(L"mrr-atmo-reuse-"+std::to_wstring(GetCurrentProcessId()));
        auto write_package=[&](const char* id,uint32_t category,uint32_t capability,int32_t orientation=-1,char texture='a'){
            auto bytes=metadata_bytes;auto* r=bytes.data()+76;std::memset(r,0,64);std::memcpy(r,id,std::strlen(id));
            std::memset(r+160,texture,64);
            if(capability==(Deny|EnvironmentTexture)){std::memset(r+64,0,96);std::memcpy(r+64,"aluminium-tga",13);}
            std::memcpy(r+225,&category,4);std::memcpy(r+229,&capability,4);std::memcpy(r+233,&orientation,4);
            const auto hash=sha256_bytes(r,237);std::memcpy(bytes.data()+12,hash.data(),64);
            std::filesystem::create_directories(packages/id);std::ofstream f(packages/id/L"materials.lsm",std::ios::binary);
            f.write(reinterpret_cast<const char*>(bytes.data()),bytes.size());
        };
        write_package("donor",2,Noise);off.package_root=packages;off.course_dirty=true;
        CHECK(off.select_course("IndependentNative")&&!off.metadata.shared_sha.empty()&&off.metadata.only_course("Common")&&!off.metadata.only_course("IndependentNative"));
        const auto* reused=off.metadata.find("IndependentNative",std::string(64,'a'));
        CHECK(reused&&reused->category==2&&reused->flags==Noise&&!off.normal_hints.ready&&off.normal_hints.records==0);
        CHECK(reused->course=="Common"&&reused==off.metadata.find("UnseenFutureLayout",std::string(64,'a')));
        CHECK(off.select_course("UnseenFutureLayout")&&off.metadata.find("UnseenFutureLayout",std::string(64,'a'))->course=="Common");
        CHECK(off.select_course("IndependentNative"));
        CHECK(!off.metadata.find("IndependentNative",std::string(64,'b'))); // new/edited texture is never inferred
        const auto reloads=off.package_reloads;CHECK(off.select_course("IndependentNative")&&off.package_reloads==reloads);
        write_package("second",2,Noise);off.course_dirty=true;CHECK(off.select_course("IndependentNative"));
        CHECK(off.metadata.find("IndependentNative",std::string(64,'a'))->category==2);
        for(const auto conflict:{1,3}){
            write_package("second",conflict==1?1:2,conflict==2?Plain:Noise,conflict==3?1:-1);
            off.course_dirty=true;CHECK(off.select_course("IndependentNative"));
            CHECK(off.metadata.find("IndependentNative",std::string(64,'a'))->flags==Deny);
        }
        write_package("donor",2,Noise|Plain);write_package("second",2,Noise);
        off.course_dirty=true;CHECK(off.select_course("IndependentNative"));
        CHECK((off.metadata.find("IndependentNative",std::string(64,'a'),Noise)->flags&Noise)==Noise);
        CHECK((off.metadata.find("IndependentNative",std::string(64,'a'),Plain)->flags&Plain)==Plain);
        write_package("donor",2,Noise);write_package("second",2,Plain);off.course_dirty=true;CHECK(off.select_course("IndependentNative"));
        CHECK(off.metadata.find("IndependentNative",std::string(64,'a'),Noise)->flags==Noise);
        CHECK(off.metadata.find("IndependentNative",std::string(64,'a'),Plain)->flags==Plain);
        write_package("donor",4,Plain|AlphaTest);write_package("second",4,Noise);off.course_dirty=true;CHECK(off.select_course("IndependentNative"));
        CHECK(off.metadata.find("IndependentNative",std::string(64,'a'),Plain|AlphaTest)->flags==(Plain|AlphaTest));
        CHECK(off.metadata.find("IndependentNative",std::string(64,'a'),Noise)->flags==Noise);
        CHECK((off.metadata.find("IndependentNative",std::string(64,'a'),Noise|AlphaTest)->flags&(Noise|AlphaTest))!=(Noise|AlphaTest));
        write_package("donor",4,Plain|AlphaTest|Environment);write_package("second",4,Plain|AlphaTest);
        off.course_dirty=true;CHECK(off.select_course("IndependentNative"));
        CHECK((off.metadata.find("IndependentNative",std::string(64,'a'),Plain|AlphaTest)->flags&(Plain|AlphaTest))==(Plain|AlphaTest));
        write_package("donor",0,Deny|EnvironmentTexture);write_package("second",0,Deny|EnvironmentTexture);
        off.course_dirty=true;CHECK(off.select_course("IndependentNative"));
        CHECK(off.metadata.find("IndependentNative",std::string(64,'a'))->flags==(Deny|EnvironmentTexture));
        write_package("donor",2,Noise);
        write_package("second",0,Deny);off.course_dirty=true;CHECK(off.select_course("IndependentNative"));
        CHECK(off.metadata.find("IndependentNative",std::string(64,'a'))->flags==Deny);
        write_package("third",2,Noise);off.course_dirty=true;CHECK(off.select_course("IndependentNative"));
        CHECK(off.metadata.find("IndependentNative",std::string(64,'a'))->flags==Deny);
        // The new scene's explicit authored package wins over donor conflicts.
        write_package("independentnative",2,Noise);off.course_dirty=true;CHECK(off.select_course("IndependentNative")&&!off.metadata.shared_sha.empty());
        CHECK(off.metadata.only_course("IndependentNative")&&off.metadata.find("IndependentNative",std::string(64,'a'))->flags==Noise);
        CHECK(off.metadata.find("IndependentNative",std::string(64,'a'),Plain)->flags==Noise); // explicit row priority includes pass mismatch
        // Missing rows in an existing explicit package inherit Common too.
        write_package("second",2,Noise);write_package("independentnative",4,Plain,-1,'b');off.course_dirty=true;
        CHECK(off.select_course("IndependentNative")&&off.metadata.only_course("IndependentNative"));
        CHECK(off.metadata.find("IndependentNative",std::string(64,'a'))->course=="Common");
        CHECK(off.metadata.find("IndependentNative",std::string(64,'b'))->course=="independentnative");
        CHECK(!off.metadata.find("IndependentNative",std::string(64,'c')));
        // An explicit exclusion wins over a conflicting generic role.
        write_package("independentnative",0,Deny);off.course_dirty=true;CHECK(off.select_course("IndependentNative"));
        CHECK(off.metadata.find("IndependentNative",std::string(64,'a'))->flags==Deny);
        // Presence of a broken package is not permission to fall back.
        {std::ofstream f(packages/L"independentnative/materials.lsm",std::ios::binary);f<<"broken";}
        off.course_dirty=true;CHECK(!off.select_course("IndependentNative"));
        LightingMetadata invalid_source;CHECK(!invalid_source.load_reused_materials(packages));
        CHECK(!invalid_source.ready&&!invalid_source.find("AnotherNewId",std::string(64,'a')));
        LightingMetadata missing_sources;CHECK(!missing_sources.load_reused_materials(packages/L"missing"));
        off.package_root.clear();std::filesystem::remove_all(packages);
    }
    {CourseCapture capture;D3DMATRIX v{},p{};v._11=v._22=v._33=v._44=1;p=v;
        capture.observe(10,v,p);capture.reference_view=v;capture.reference_projection=p;CHECK(capture.same_camera(10));
        p._11=2;capture.observe(10,v,p);CHECK(!capture.same_camera(10)&&capture.ambiguous);
        capture.observe(11,v,v);CHECK(capture.same_camera(11));
        for(size_t i=0;i<CourseCapture::max_rows+1;++i)capture.append("{}");CHECK(capture.overflow&&capture.ledger.size()==CourseCapture::max_rows);
        bool world=true;capture.original_world=false;capture.stage=1;capture.cancel(world);CHECK(!world&&!capture.stage&&capture.ledger.empty());
        v._11=NAN;capture.observe(12,v,p);CHECK(capture.ambiguous);
        auto altered=evening;altered.fog_enabled=!evening.fog_enabled;CHECK(!CourseCapture::same_lighting(evening,altered));
    }

    metadata_bytes.back()^=1;{std::ofstream f(metadata_test,std::ios::binary);f.write(reinterpret_cast<const char*>(metadata_bytes.data()),metadata_bytes.size());}
    LightingMetadata corrupted;CHECK(!corrupted.load(metadata_test));std::filesystem::remove(metadata_test);
    // Original authored normals are looked up across independent draw ranges,
    // while unknown geometry / opposite faces / authored hard-edge ties fall back.
    const auto hints_path=std::filesystem::temp_directory_path()/L"atmosphere22-normals-test.lnh";
    std::vector<uint8_t> hints_bytes(76+2*153);std::memcpy(hints_bytes.data(),"LNH1",4);
    uint32_t two=2;std::memcpy(hints_bytes.data()+4,&version,4);std::memcpy(hints_bytes.data()+8,&two,4);
    for(unsigned row_index=0;row_index<2;++row_index){auto* r=hints_bytes.data()+76+153*row_index;std::memcpy(r,"CustomLayout",12);std::memset(r+64,'a',64);
        const float xyz[3]={float(row_index),0,0},source_normal[3]={0,.8f,.6f};std::memcpy(r+129,xyz,12);std::memcpy(r+141,source_normal,12);}
    auto hint_sha=sha256_bytes(hints_bytes.data()+76,hints_bytes.size()-76);std::memcpy(hints_bytes.data()+12,hint_sha.data(),64);
    {std::ofstream f(hints_path,std::ios::binary);f.write(reinterpret_cast<const char*>(hints_bytes.data()),hints_bytes.size());}
    NormalHints hints;CHECK(hints.load(hints_path)&&hints.records==2);std::array<float,3> resolved_a{},resolved_b{};
    CHECK(hints.resolve("CustomLayout",std::string(64,'a'),{0,0,0},{0,1,0},resolved_a));
    CHECK(hints.resolve("CustomLayout",std::string(64,'a'),{1,0,0},{0,.6f,.8f},resolved_b));CHECK(resolved_a==resolved_b);
    CHECK(!hints.resolve("CustomLayout",std::string(64,'b'),{0,0,0},{0,1,0},resolved_a));
    CHECK(!hints.resolve("CustomLayout",std::string(64,'a'),{0,0,0},{0,-1,0},resolved_a));
    CHECK(!hints.resolve("CustomLayout",std::string(64,'a'),{0,1,0},{0,1,0},resolved_a));
    const float coincident[3]={0,0,0},hard_normal[3]={0,.8f,-.6f};
    std::memcpy(hints_bytes.data()+76+153+129,coincident,12);std::memcpy(hints_bytes.data()+76+153+141,hard_normal,12);
    hint_sha=sha256_bytes(hints_bytes.data()+76,hints_bytes.size()-76);std::memcpy(hints_bytes.data()+12,hint_sha.data(),64);
    {std::ofstream f(hints_path,std::ios::binary);f.write(reinterpret_cast<const char*>(hints_bytes.data()),hints_bytes.size());}
    NormalHints hard_hints;CHECK(hard_hints.load(hints_path));
    CHECK(!hard_hints.resolve("CustomLayout",std::string(64,'a'),{0,0,0},{0,1,0},resolved_a));
    CHECK(hard_hints.resolve("CustomLayout",std::string(64,'a'),{0,0,0},{0,.8f,.6f},resolved_a)&&resolved_a[2]>.59f);
    hints_bytes.back()^=1;{std::ofstream f(hints_path,std::ios::binary);f.write(reinterpret_cast<const char*>(hints_bytes.data()),hints_bytes.size());}
    NormalHints broken_hints;CHECK(!broken_hints.load(hints_path));std::filesystem::remove(hints_path);
    // A world normal contributes once: different VL1 model-Y prepared colours
    // become the same colour for the same world normal, retaining source alpha.
    CHECK(body_color(0xfe303030,{0,1,0},evening,true)==body_color(0xfec0c0c0,{0,1,0},evening,true));
    CHECK((body_color(0x7f303030,{0,1,0},evening,true)>>24)==0x7f);
    CHECK(body_color(gray,{0,1,0},evening,false)==scene_color(gray,{0,1,0},body_lighting(evening)));
    {auto dark=evening;dark.ambient_strength=.06f;dark.sun_strength=0;CHECK(body_lighting(dark).ambient_strength<.1f);auto day=evening;day.ambient_strength=.6f;CHECK(body_lighting(day).ambient_strength>=.95f);}
    CHECK(body_color(0x7f123456,{0,1,0},Lighting{},true)==0x7f123456);
    auto dark_body=evening;dark_body.world_brightness=.3f;dark_body.direction={0,1,0};
    const auto shadow_body=body_color(0x7f666666,{0,-1,0},dark_body,false);
    CHECK((shadow_body&255)>45);CHECK((shadow_body&255)>((shadow_body>>16)&255));
    CHECK((shadow_body>>24)==0x7f);CHECK((body_color(0x7f666666,{0,1,0},dark_body,false)&0xffffff)>(shadow_body&0xffffff));
    CHECK((body_color(0x7f000000,{0,1,0},dark_body,false)&0xffffff)==0);
    // Authored normal-bearing world metal: only explicit opaque environment
    // capability can reach this layout; RGB only, normal/UV/alpha retained.
    CHECK(world_environment_factor(Lighting{})==0xffffffffu);
    auto low_environment=evening;low_environment.ambient={.4f,.5f,.6f};low_environment.world_brightness=.2f;
    const auto environment_gain=world_environment_factor(low_environment);
    auto prelight_only=low_environment;prelight_only.prelight_contrast=0;prelight_only.prelight_visibility=1;CHECK(world_environment_factor(prelight_only)==environment_gain);
    CHECK((environment_gain&255)<180&&((environment_gain>>16)&255)<(environment_gain&255));
    CHECK((environment_texel(0x7f808080,environment_gain)>>24)==0x7f);
    CHECK(environment_texel(0x12000000,environment_gain)==0x12000000);
    CHECK(environment_texel(0x7f123456,0xffffffffu)==0x7f123456);
    SceneMaterial metal;metal.category=4;metal.flags=Plain|Environment;
    CHECK(source_opaque_pass(&metal,false,false,false));
    CHECK(!source_opaque_pass(nullptr,false,false,false));
    CHECK(!source_opaque_pass(&metal,false,true,false));
    CHECK(!source_opaque_pass(&metal,false,false,true));
    SceneMaterial excluded_surface;excluded_surface.flags=Deny;CHECK(!source_opaque_pass(&excluded_surface,false,false,false));
    ResolvedGeometry metal_geometry;metal_geometry.original.resize(3*36);
    const float metal_positions[3][3]={{0,0,0},{0,0,1},{1,0,0}};
    for(unsigned i=0;i<3;++i){auto* v=metal_geometry.original.data()+36*i;std::memcpy(v,metal_positions[i],12);const float normal[3]={0,1,0};std::memcpy(v+12,normal,12);const uint32_t color=0x7f808080;std::memcpy(v+24,&color,4);}
    const uint16_t metal_indices[3]={0,1,2};metal_geometry.index_bytes.resize(6);std::memcpy(metal_geometry.index_bytes.data(),metal_indices,6);
    CHECK(light_geometry(metal_geometry,36,0,3,2,&metal,false,true,false,false,evening,nullptr,"","",true));
    for(unsigned i=0;i<3;++i){CHECK(!std::memcmp(metal_geometry.original.data()+i*36,metal_geometry.lit.data()+i*36,24));CHECK(!std::memcmp(metal_geometry.original.data()+i*36+28,metal_geometry.lit.data()+i*36+28,8));CHECK(metal_geometry.lit[i*36+27]==0x7f);}
    CHECK(!light_geometry(metal_geometry,36,0,3,2,nullptr,false,true,false,false,evening,nullptr,"","",true));
    CHECK(!light_geometry(metal_geometry,36,0,3,2,&metal,false,true,true,false,evening,nullptr,"","",true));
    metal.flags=Plain|Environment|AlphaTest;
    CHECK(source_opaque_pass(&metal,false,false,true));
    CHECK(light_geometry(metal_geometry,36,0,3,2,&metal,false,true,true,false,evening,nullptr,"","",true));
    for(unsigned i=0;i<3;++i){CHECK(!std::memcmp(metal_geometry.original.data()+i*36,metal_geometry.lit.data()+i*36,24));CHECK(!std::memcmp(metal_geometry.original.data()+i*36+28,metal_geometry.lit.data()+i*36+28,8));CHECK(metal_geometry.lit[i*36+27]==0x7f);}
    CHECK(!light_geometry(metal_geometry,36,0,3,2,&metal,false,false,true,false,evening,nullptr,"","",true));
    metal.flags|=Deny;CHECK(!light_geometry(metal_geometry,36,0,3,2,&metal,false,true,true,false,evening,nullptr,"","",true));
    // ATMOSPHERE5.5: the game assigns reflection passes to plain static roles too;
    // the certified secondary is proven by the caller. A detail-only role is not enough.
    metal.flags=Plain;CHECK(light_geometry(metal_geometry,36,0,3,2,&metal,false,true,false,false,evening,nullptr,"","",true));
    metal.flags=Noise;CHECK(!light_geometry(metal_geometry,36,0,3,2,&metal,false,true,false,false,evening,nullptr,"","",true));
    auto reduced=scene;reduced.prelight_contrast=.35f;
    CHECK((scene_color(0x7f000000,{0,1,0},reduced)&0xffffff)==0);
    CHECK((scene_color(gray,{0,1,0},reduced)>>24)==0x7f);
    // Original RGB/texture compensation must receive the SAME gain at a seam.
    const auto hi=scene_color(0xffa0a0a0,{0,1,0},evening),lo=scene_color(0xff505050,{0,1,0},evening);
    for(unsigned shift:{0u,8u,16u})CHECK(std::abs(int((hi>>shift)&255)-2*int((lo>>shift)&255))<=1);
    CHECK(BodyMaterials::safe("mastersticker243-tga","perspex-tga",OpaquePanel));
    CHECK(!BodyMaterials::safe("mastersticker243-tga","perspex-tga",OpaqueTrim));
    CHECK(BodyMaterials::safe("tatawheelcover-tga","perspex-tga",OpaqueCover));
    CHECK(BodyMaterials::safe("tatawheelcoverside-tga","perspex-tga",OpaqueCover));
    CHECK(!BodyMaterials::safe("wheel-tga","perspex-tga",OpaqueCover));
    CHECK(!BodyMaterials::safe("wheelcover-tga","rubber-tga",OpaqueCover));
    CHECK(!BodyMaterials::safe("lampsticker-tga","perspex-tga",OpaquePanel));
    CHECK(BodyMaterials::safe("pfgrill64-tga","null",OpaqueFlat));
    CHECK(!BodyMaterials::safe("lamp-tga","null",OpaqueFlat));
    CHECK(!BodyMaterials::safe("pfgrill64-tga","whitepaint-tga",OpaqueFlat));
    auto flat_settings=evening;const auto flat_a=flat_body_color(0x7fa0a0a0,flat_settings);
    flat_settings.direction={0,-1,0};CHECK(flat_a==flat_body_color(0x7fa0a0a0,flat_settings));
    CHECK((flat_a>>24)==0x7f);
    CHECK(BodyMaterials::safe("mhelmet32-tga","whitepaint-tga",OpaqueHelmet));
    CHECK(!BodyMaterials::safe("mhelmet32-tga","whitepaint-tga",Paint));
    CHECK(!BodyMaterials::safe("driverhelmet-tga","whitepaint-tga",OpaqueHelmet));
    CHECK(!BodyMaterials::safe("helmetlamp-tga","whitepaint-tga",OpaqueHelmet));
    CHECK(!BodyMaterials::safe("mhelmet32-tga","glass-tga",OpaqueHelmet));
    CHECK(BodyMaterials::safe("patrols128-tga","whitepaint-tga"));
    CHECK(!BodyMaterials::safe("wheel-tga","whitepaint-tga"));CHECK(!BodyMaterials::safe("body-tga","glass-tga"));
    CHECK(!BodyMaterials::safe("breaklightson-tga","whitepaint-tga"));
    const auto body_path=std::filesystem::temp_directory_path()/L"atmosphere22-body-test.blm";
    std::vector<uint8_t> body_bytes(76+289);std::memcpy(body_bytes.data(),"BLM1",4);std::memcpy(body_bytes.data()+4,&version,4);std::memcpy(body_bytes.data()+8,&one,4);
    auto* body_row=body_bytes.data()+76;std::memcpy(body_row,"custom",6);std::memcpy(body_row+32,"body-tga",8);std::memcpy(body_row+128,"whitepaint-tga",14);std::memset(body_row+224,'a',64);
    auto body_sha=sha256_bytes(body_row,289);std::memcpy(body_bytes.data()+12,body_sha.data(),64);
    {std::ofstream f(body_path,std::ios::binary);f.write(reinterpret_cast<const char*>(body_bytes.data()),body_bytes.size());}
    BodyMaterials body_metadata;CHECK(body_metadata.load(body_path)&&body_metadata.native("custom","body-tga","whitepaint-tga")&&body_metadata.ps2("custom",std::string(64,'a')));
    CHECK(!body_metadata.native("custom","body-tga","rubber-tga")&&!body_metadata.ps2("other",std::string(64,'a')));
    std::memset(body_row+32,0,96);std::memcpy(body_row+32,"wheel-tga",9);body_sha=sha256_bytes(body_row,289);std::memcpy(body_bytes.data()+12,body_sha.data(),64);
    {std::ofstream f(body_path,std::ios::binary);f.write(reinterpret_cast<const char*>(body_bytes.data()),body_bytes.size());}
    BodyMaterials unsafe_body;CHECK(!unsafe_body.load(body_path));std::filesystem::remove(body_path);
    // Typed trim capability is opt-in and cannot relabel paint, glass or wheels.
    CHECK(BodyMaterials::safe("logowhite64-tga","whitepaint-tga",Paint));
    CHECK(!BodyMaterials::safe("tataplasticbump-tga","perspex-tga",Paint));
    CHECK(BodyMaterials::safe("tataplasticbump-tga","perspex-tga",OpaqueTrim));
    CHECK(!BodyMaterials::safe("wheel-tga","perspex-tga",OpaqueTrim));
    CHECK(!BodyMaterials::safe("lights-tga","perspex-tga",OpaqueTrim));
    CHECK(!BodyMaterials::safe("bumper-tga","glass-tga",OpaqueTrim));
    body_bytes.assign(76+293,0);std::memcpy(body_bytes.data(),"BLM2",4);uint32_t version_two=2,trim_role=OpaqueTrim;
    std::memcpy(body_bytes.data()+4,&version_two,4);std::memcpy(body_bytes.data()+8,&one,4);body_row=body_bytes.data()+76;
    std::memcpy(body_row,"custom",6);std::memcpy(body_row+32,"bumper-tga",10);std::memcpy(body_row+128,"perspex-tga",11);std::memset(body_row+224,'b',64);std::memcpy(body_row+289,&trim_role,4);
    body_sha=sha256_bytes(body_row,293);std::memcpy(body_bytes.data()+12,body_sha.data(),64);
    {std::ofstream f(body_path,std::ios::binary);f.write(reinterpret_cast<const char*>(body_bytes.data()),body_bytes.size());}
    BodyMaterials typed_trim;CHECK(typed_trim.load(body_path)&&typed_trim.native("custom","bumper-tga","perspex-tga"));
    trim_role=99;std::memcpy(body_row+289,&trim_role,4);body_sha=sha256_bytes(body_row,293);std::memcpy(body_bytes.data()+12,body_sha.data(),64);
    {std::ofstream f(body_path,std::ios::binary);f.write(reinterpret_cast<const char*>(body_bytes.data()),body_bytes.size());}
    BodyMaterials bad_role;CHECK(!bad_role.load(body_path));std::filesystem::remove(body_path);
    SceneAtlas missing;CHECK(!missing.load(L"Z:\\nonexistent-atmosphere-test\\scene.atlas"));
    wchar_t atlas_path[32768]{};if(GetEnvironmentVariableW(L"MRR_ATMOSPHERE_ATLAS",atlas_path,32768)){
        SceneAtlas original;CHECK(original.load(atlas_path)&&original.ready&&original.size()==kSceneAtlasRecords);
        const auto tmp=std::filesystem::temp_directory_path()/L"atmosphere-invalid-atlas-test.bin";
        {std::ofstream f(tmp,std::ios::binary);f.write("ATS2bad!",8);}
        SceneAtlas invalid;CHECK(!invalid.load(tmp));std::filesystem::remove(tmp);
    }
    // A PC CALL preimage and RET-4 getter ABI are independently byte-checked by
    // the Python binary contract test against the exact executable corpus.
    CHECK(kSkyReadBytes[0]==0xe8&&kSkyIdentities[6].preset==3);
    return failures?1:0;
}
