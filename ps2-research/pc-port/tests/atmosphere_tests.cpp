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
        CHECK(std::abs(sun_center.radius-std::tan(1.f*.017453293f)*300.f)<1e-3f);
        SunPosition wide;CHECK(sun_position({0,0,1},sun_view,sun_projection,3840,2160,wide,3.f));CHECK(wide.radius>32.f);
        CHECK(SunFx::sprite_intensity(0,0,0,0)==1.f&&SunFx::sprite_intensity(0,.99f,0,0)<.1f&&SunFx::sprite_intensity(0,1,0,0)==0);
        CHECK(SunFx::sprite_intensity(1,0,0,0)>.99f&&SunFx::sprite_intensity(3,0,0,0)==1.f&&SunFx::sprite_intensity(3,.999f,0,0)<.01f);
        const float sector=6.2831853f/36.f;
        CHECK(sun_ray_profile(.8f,0,36)>.0f);                    // long spoke (even index)
        CHECK(sun_ray_profile(.8f,sector,36)==0);               // short spoke ends at .62
        CHECK(sun_ray_profile(.4f,sector,36)>0);
        CHECK(sun_ray_profile(.5f,sector*.5f,36)<1e-6f);        // between spokes
        CHECK(sun_ray_profile(1.f,0,36)==0&&sun_ray_profile(.5f,0,0)==0);
        const auto defaults=read_sun_style(L"Z:\\missing\\Atmosphere.ini");
        CHECK(defaults.ray_count==36&&defaults.core_degrees==1.f&&defaults.glow_degrees>defaults.core_degrees&&defaults.ray_count%2==0);
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
    CHECK(pc_water_secondary("2cc07bb39117f1f0c102e6007a9dfb2245a7f6180a578352d6b7ba09b2f705f6"));
    CHECK(!pc_water_secondary(std::string(64,'0')));
    Lighting sunset_water;sunset_water.mode=Lighting::Mode::GoldenHour;sunset_water.world_brightness=.68f;
    const auto water_factor=pc_water_factor(sunset_water);CHECK(water_factor>>24==255);CHECK((water_factor&255)>((water_factor>>16)&255));CHECK((water_factor&255)<255);
    CHECK(pc_water_factor(sunset_water,0x7f123456)>>24==0x7f);
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
    CHECK(body_color(0x7f123456,{0,1,0},Lighting{},true)==0x7f123456);
    auto dark_body=evening;dark_body.world_brightness=.3f;dark_body.direction={0,1,0};
    const auto shadow_body=body_color(0x7f666666,{0,-1,0},dark_body,false);
    CHECK((shadow_body&255)>45);CHECK((shadow_body&255)>((shadow_body>>16)&255));
    CHECK((shadow_body>>24)==0x7f);CHECK((body_color(0x7f666666,{0,1,0},dark_body,false)&0xffffff)>(shadow_body&0xffffff));
    CHECK((body_color(0x7f000000,{0,1,0},dark_body,false)&0xffffff)==0);
    // Authored normal-bearing world metal: only explicit opaque environment
    // capability can reach this layout; RGB only, normal/UV/alpha retained.
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
    metal.flags=Plain;CHECK(!light_geometry(metal_geometry,36,0,3,2,&metal,false,true,false,false,evening,nullptr,"","",true));
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
