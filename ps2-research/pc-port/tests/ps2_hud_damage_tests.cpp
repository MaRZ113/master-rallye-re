#include "ps2_hud_damage.hpp"
#include "ps2_hud_damage_feed.hpp"
#include "ps2_hud_map.hpp"
#include "ps2_hud_template.hpp"
#include "ps2_hud_eggs.hpp"
#include "ps2_hud_timediffs.hpp"
#include "ps2_hud_splitflash.hpp"
#include "ps2_race_certificate.hpp"
#include <array>
#include <cmath>
#include <cstring>
#include <iostream>
#include <map>
#include <string>
#include <vector>

using namespace gfx2;
using namespace gfx2::ps2port;
int failures=0;
#define CHECK(x) do{if(!(x)){std::cerr<<"FAIL "<<__LINE__<<": "#x"\n";++failures;}}while(0)
#include "mock_interfaces.hpp"

namespace {
struct Surface final:IDirect3DSurface8 {
    ULONG refs=1;D3DSURFACE_DESC desc{};
    Surface(UINT w=1280,UINT h=720){desc.Width=w;desc.Height=h;desc.Format=D3DFMT_X8R8G8B8;desc.Type=D3DRTYPE_SURFACE;desc.MultiSampleType=D3DMULTISAMPLE_NONE;}
    HRESULT STDMETHODCALLTYPE QueryInterface(REFIID,void** p) override{if(!p)return E_POINTER;*p=this;AddRef();return S_OK;}
    ULONG STDMETHODCALLTYPE AddRef() override{return ++refs;}
    ULONG STDMETHODCALLTYPE Release() override{CHECK(refs);return --refs;}
    HRESULT STDMETHODCALLTYPE GetDevice(IDirect3DDevice8**) override{return E_NOTIMPL;}
    HRESULT STDMETHODCALLTYPE SetPrivateData(REFGUID,const void*,DWORD,DWORD) override{return E_NOTIMPL;}
    HRESULT STDMETHODCALLTYPE GetPrivateData(REFGUID,void*,DWORD*) override{return E_NOTIMPL;}
    HRESULT STDMETHODCALLTYPE FreePrivateData(REFGUID) override{return E_NOTIMPL;}
    HRESULT STDMETHODCALLTYPE GetContainer(REFIID,void**) override{return E_NOTIMPL;}
    HRESULT STDMETHODCALLTYPE GetDesc(D3DSURFACE_DESC* p) override{*p=desc;return S_OK;}
    HRESULT STDMETHODCALLTYPE LockRect(D3DLOCKED_RECT*,const RECT*,DWORD) override{return E_NOTIMPL;}
    HRESULT STDMETHODCALLTYPE UnlockRect() override{return E_NOTIMPL;}
};
struct Texture final:IDirect3DTexture8 {
    ULONG refs=1;Surface surface;
    HRESULT STDMETHODCALLTYPE QueryInterface(REFIID,void** p) override{if(!p)return E_POINTER;*p=this;AddRef();return S_OK;}
    ULONG STDMETHODCALLTYPE AddRef() override{return ++refs;}
    ULONG STDMETHODCALLTYPE Release() override{CHECK(refs);return --refs;}
    HRESULT STDMETHODCALLTYPE GetDevice(IDirect3DDevice8**) override{return E_NOTIMPL;}
    HRESULT STDMETHODCALLTYPE SetPrivateData(REFGUID,const void*,DWORD,DWORD) override{return E_NOTIMPL;}
    HRESULT STDMETHODCALLTYPE GetPrivateData(REFGUID,void*,DWORD*) override{return E_NOTIMPL;}
    HRESULT STDMETHODCALLTYPE FreePrivateData(REFGUID) override{return E_NOTIMPL;}
    DWORD STDMETHODCALLTYPE SetPriority(DWORD) override{return 0;}
    DWORD STDMETHODCALLTYPE GetPriority() override{return 0;}
    void STDMETHODCALLTYPE PreLoad() override{}
    D3DRESOURCETYPE STDMETHODCALLTYPE GetType() override{return D3DRTYPE_TEXTURE;}
    DWORD STDMETHODCALLTYPE SetLOD(DWORD) override{return 0;}
    DWORD STDMETHODCALLTYPE GetLOD() override{return 0;}
    DWORD STDMETHODCALLTYPE GetLevelCount() override{return 1;}
    HRESULT STDMETHODCALLTYPE GetLevelDesc(UINT,D3DSURFACE_DESC* p) override{*p=surface.desc;return S_OK;}
    HRESULT STDMETHODCALLTYPE GetSurfaceLevel(UINT,IDirect3DSurface8** p) override{*p=&surface;surface.AddRef();return S_OK;}
    HRESULT STDMETHODCALLTYPE LockRect(UINT,D3DLOCKED_RECT*,const RECT*,DWORD) override{return E_NOTIMPL;}
    HRESULT STDMETHODCALLTYPE UnlockRect(UINT) override{return E_NOTIMPL;}
    HRESULT STDMETHODCALLTYPE AddDirtyRect(const RECT*) override{return E_NOTIMPL;}
};
struct Buffer final:IDirect3DVertexBuffer8 {
    ULONG refs=1;
    HRESULT STDMETHODCALLTYPE QueryInterface(REFIID,void** p) override{*p=this;AddRef();return S_OK;}
    ULONG STDMETHODCALLTYPE AddRef() override{return ++refs;}
    ULONG STDMETHODCALLTYPE Release() override{CHECK(refs);return --refs;}
    HRESULT STDMETHODCALLTYPE GetDevice(IDirect3DDevice8**) override{return E_NOTIMPL;}
    HRESULT STDMETHODCALLTYPE SetPrivateData(REFGUID,const void*,DWORD,DWORD) override{return E_NOTIMPL;}
    HRESULT STDMETHODCALLTYPE GetPrivateData(REFGUID,void*,DWORD*) override{return E_NOTIMPL;}
    HRESULT STDMETHODCALLTYPE FreePrivateData(REFGUID) override{return E_NOTIMPL;}
    DWORD STDMETHODCALLTYPE SetPriority(DWORD) override{return 0;}
    DWORD STDMETHODCALLTYPE GetPriority() override{return 0;}
    void STDMETHODCALLTYPE PreLoad() override{}
    D3DRESOURCETYPE STDMETHODCALLTYPE GetType() override{return D3DRTYPE_VERTEXBUFFER;}
    HRESULT STDMETHODCALLTYPE Lock(UINT,UINT,BYTE**,DWORD) override{return E_NOTIMPL;}
    HRESULT STDMETHODCALLTYPE Unlock() override{return E_NOTIMPL;}
    HRESULT STDMETHODCALLTYPE GetDesc(D3DVERTEXBUFFER_DESC*) override{return E_NOTIMPL;}
};
// A lockable 32x32 managed texture for the identity matcher.
struct LockTexture final:IDirect3DTexture8 {
    ULONG refs=1;D3DSURFACE_DESC desc{};std::vector<DWORD> pixels;int locks=0;
    LockTexture(){desc.Width=desc.Height=32;desc.Format=D3DFMT_A8R8G8B8;desc.Pool=D3DPOOL_MANAGED;desc.Type=D3DRTYPE_TEXTURE;pixels.assign(32*32,0);}
    HRESULT STDMETHODCALLTYPE QueryInterface(REFIID,void** p) override{*p=this;AddRef();return S_OK;}
    ULONG STDMETHODCALLTYPE AddRef() override{return ++refs;}
    ULONG STDMETHODCALLTYPE Release() override{CHECK(refs);return --refs;}
    HRESULT STDMETHODCALLTYPE GetDevice(IDirect3DDevice8**) override{return E_NOTIMPL;}
    HRESULT STDMETHODCALLTYPE SetPrivateData(REFGUID,const void*,DWORD,DWORD) override{return E_NOTIMPL;}
    HRESULT STDMETHODCALLTYPE GetPrivateData(REFGUID,void*,DWORD*) override{return E_NOTIMPL;}
    HRESULT STDMETHODCALLTYPE FreePrivateData(REFGUID) override{return E_NOTIMPL;}
    DWORD STDMETHODCALLTYPE SetPriority(DWORD) override{return 0;}
    DWORD STDMETHODCALLTYPE GetPriority() override{return 0;}
    void STDMETHODCALLTYPE PreLoad() override{}
    D3DRESOURCETYPE STDMETHODCALLTYPE GetType() override{return D3DRTYPE_TEXTURE;}
    DWORD STDMETHODCALLTYPE SetLOD(DWORD) override{return 0;}
    DWORD STDMETHODCALLTYPE GetLOD() override{return 0;}
    DWORD STDMETHODCALLTYPE GetLevelCount() override{return 1;}
    HRESULT STDMETHODCALLTYPE GetLevelDesc(UINT,D3DSURFACE_DESC* p) override{*p=desc;return S_OK;}
    HRESULT STDMETHODCALLTYPE GetSurfaceLevel(UINT,IDirect3DSurface8**) override{return E_NOTIMPL;}
    HRESULT STDMETHODCALLTYPE LockRect(UINT,D3DLOCKED_RECT* r,const RECT*,DWORD) override{++locks;r->pBits=pixels.data();r->Pitch=32*4;return S_OK;}
    HRESULT STDMETHODCALLTYPE UnlockRect(UINT) override{return S_OK;}
    HRESULT STDMETHODCALLTYPE AddDirtyRect(const RECT*) override{return E_NOTIMPL;}
};
struct Native final:MockDeviceBase {
    std::array<DWORD,256> rs{};std::array<std::array<DWORD,64>,2> tss{};
    Texture original0,original1,page0,page1;Buffer buffer;
    std::array<IDirect3DBaseTexture8*,2> textures={&original0,&original1};
    IDirect3DVertexBuffer8* stream=&buffer;UINT stride=36;D3DVIEWPORT8 viewport{1,2,1270,710,.2f,.8f};DWORD vertex=0x152,pixel=17;
    int sets=0,fail_set=0,draws=0,begins=0,ends=0;bool scene=false;HRESULT draw_hr=S_OK;
    std::vector<IDirect3DBaseTexture8*> drawn_textures;std::vector<DWORD> drawn_colors;
    Native(){for(size_t i=0;i<rs.size();++i)rs[i]=DWORD(1000+i);for(size_t s=0;s<2;++s)for(size_t i=0;i<64;++i)tss[s][i]=DWORD(2000+s*64+i);}
    HRESULT w(){++sets;return sets==fail_set?D3DERR_INVALIDCALL:S_OK;}
    HRESULT STDMETHODCALLTYPE GetRenderState(D3DRENDERSTATETYPE k,DWORD* p) override{*p=rs[k];return S_OK;}
    HRESULT STDMETHODCALLTYPE SetRenderState(D3DRENDERSTATETYPE k,DWORD v) override{const auto r=w();rs[k]=v;return r;}
    HRESULT STDMETHODCALLTYPE GetTextureStageState(DWORD s,D3DTEXTURESTAGESTATETYPE k,DWORD* p) override{*p=tss[s][k];return S_OK;}
    HRESULT STDMETHODCALLTYPE SetTextureStageState(DWORD s,D3DTEXTURESTAGESTATETYPE k,DWORD v) override{const auto r=w();tss[s][k]=v;return r;}
    HRESULT STDMETHODCALLTYPE GetVertexShader(DWORD* p) override{*p=vertex;return S_OK;}
    HRESULT STDMETHODCALLTYPE SetVertexShader(DWORD v) override{const auto r=w();vertex=v;return r;}
    HRESULT STDMETHODCALLTYPE GetPixelShader(DWORD* p) override{*p=pixel;return S_OK;}
    HRESULT STDMETHODCALLTYPE SetPixelShader(DWORD v) override{const auto r=w();pixel=v;return r;}
    HRESULT STDMETHODCALLTYPE GetTexture(DWORD s,IDirect3DBaseTexture8** p) override{*p=textures[s];if(*p)(*p)->AddRef();return S_OK;}
    HRESULT STDMETHODCALLTYPE SetTexture(DWORD s,IDirect3DBaseTexture8* p) override{const auto r=w();if(p)p->AddRef();if(textures[s])textures[s]->Release();textures[s]=p;return r;}
    HRESULT STDMETHODCALLTYPE GetViewport(D3DVIEWPORT8* p) override{*p=viewport;return S_OK;}
    HRESULT STDMETHODCALLTYPE SetViewport(const D3DVIEWPORT8* p) override{const auto r=w();viewport=*p;return r;}
    HRESULT STDMETHODCALLTYPE GetStreamSource(UINT,IDirect3DVertexBuffer8** p,UINT* v) override{*p=stream;*v=stride;if(*p)(*p)->AddRef();return S_OK;}
    HRESULT STDMETHODCALLTYPE SetStreamSource(UINT,IDirect3DVertexBuffer8* p,UINT v) override{const auto r=w();if(p)p->AddRef();if(stream)stream->Release();stream=p;stride=v;return r;}
    HRESULT STDMETHODCALLTYPE BeginScene() override{++begins;CHECK(!scene);scene=true;return S_OK;}
    HRESULT STDMETHODCALLTYPE EndScene() override{++ends;CHECK(scene);scene=false;return S_OK;}
    HRESULT STDMETHODCALLTYPE DrawPrimitiveUP(D3DPRIMITIVETYPE p,UINT n,const void* data,UINT bytes) override{
        CHECK(p==D3DPT_TRIANGLESTRIP&&n==2&&bytes==28&&data&&scene);
        CHECK(rs[D3DRS_ALPHABLENDENABLE]==TRUE&&rs[D3DRS_SRCBLEND]==D3DBLEND_SRCALPHA&&rs[D3DRS_DESTBLEND]==D3DBLEND_INVSRCALPHA);
        CHECK(tss[0][D3DTSS_COLOROP]==D3DTOP_MODULATE&&tss[0][D3DTSS_ALPHAOP]==D3DTOP_MODULATE&&tss[0][D3DTSS_MAGFILTER]==D3DTEXF_LINEAR);
        CHECK(vertex==(D3DFVF_XYZRHW|D3DFVF_DIFFUSE|D3DFVF_TEX1)&&viewport.X==0);
        drawn_textures.push_back(textures[0]);drawn_colors.push_back(static_cast<const HudVertex*>(data)->color);
        ++draws;if(stream)stream->Release();stream=nullptr;stride=0;return draw_hr;}
};
struct Original {
    std::array<DWORD,256> rs;std::array<std::array<DWORD,64>,2> tss;D3DVIEWPORT8 viewport;
    explicit Original(const Native& n):rs(n.rs),tss(n.tss),viewport(n.viewport){}
    void check(const Native& n) const{CHECK(rs==n.rs&&tss==n.tss);CHECK(std::memcmp(&viewport,&n.viewport,sizeof(viewport))==0);
        CHECK(n.stream==&n.buffer&&n.stride==36&&n.vertex==0x152&&n.pixel==17&&!n.scene);
        CHECK(n.textures[0]==&n.original0&&n.textures[1]==&n.original1&&n.original0.refs==1&&n.original1.refs==1&&n.buffer.refs==1&&n.page0.refs==1&&n.page1.refs==1);}
};
// PC UI placement from the F10 trace: WORLD translate(x,y), VIEW I, PROJ ortho 640x480 bottom-origin.
HudPlacement pc_placement(float x,float y,float margin=0.f){
    HudMatrix world,proj;for(int i=0;i<4;++i)world.m[i][i]=1.f;world.m[3][0]=x+margin;world.m[3][1]=y;
    proj.m[0][0]=1.f/320.f;proj.m[1][1]=1.f/240.f;proj.m[2][2]=-.0005f;proj.m[3][0]=-1.f;proj.m[3][1]=-1.f;proj.m[3][2]=.5f;proj.m[3][3]=1.f;
    HudPlacement p;p.wvp=hud_multiply(world,proj);p.vw=640.f;p.vh=480.f;p.valid=true;return p;
}
bool near_f(float a,float b,float e=1e-3f){return std::fabs(a-b)<=e;}

void band_tests(){
    CHECK(ps2_damage_band(0.f)==0&&ps2_damage_band(.19f)==0);
    CHECK(ps2_damage_band(.21f)==1&&ps2_damage_band(.39f)==1);
    CHECK(ps2_damage_band(.41f)==2&&ps2_damage_band(.59f)==2);
    CHECK(ps2_damage_band(.61f)==3&&ps2_damage_band(.79f)==3);
    CHECK(ps2_damage_band(.81f)==4&&ps2_damage_band(1.f)==4&&ps2_damage_band(7.f)==4&&ps2_damage_band(-1.f)==0);
    CHECK(hud_colour(kPS2DamageColours[3],1.f)==0xffffbf4du&&hud_colour(kPS2DamageColours[4],.5f)==0x80ff0000u);
}
void state_tests(){
    HudDamageState s;
    s.update({0.f,0.f,0.f,0.f,0.f});CHECK(s.notices().empty()&&s.band(0)==0);
    s.update({.3f,0.f,0.f,0.f,0.f});CHECK(s.band(0)==1&&s.notices().size()==1&&s.notices()[0].image==0&&s.notices()[0].band==1);
    s.update({.1f,0.f,0.f,0.f,0.f});CHECK(s.band(0)==1&&s.notices().size()==1);   // PS2 never lowers the applied value
    s.update({.3005f,0.f,0.f,0.f,0.f});CHECK(s.notices().size()==1);              // below the 0.001 step
    s.update({.3f,.95f,0.f,0.f,0.f});CHECK(s.band(1)==4&&s.notices().size()==2&&s.notices()[1].image==1);
    float a=0,dy=0;
    s.advance(.25f);CHECK(s.notices()[0].phase==0&&notice_pose(s.notices()[0],a,dy)&&near_f(a,.5f)&&dy==0.f&&s.notices()[1].phase<0);
    s.advance(.25f);s.advance(.25f);s.advance(.25f);s.advance(.1f);               // 1.1 s = birth .5 + life .6
    CHECK(s.notices()[0].phase==2&&s.notices()[1].phase==0);
    s.advance(.25f);CHECK(notice_pose(s.notices()[0],a,dy)&&near_f(a,.5f,.02f)&&near_f(dy,-37.5f,1.5f));
    s.advance(.25f);CHECK(s.notices().size()==1&&s.notices()[0].image==1);
    for(int i=0;i<8;++i)s.advance(.25f);
    CHECK(s.notices().empty());
    s.reset();CHECK(s.band(1)==0&&s.notices().empty());
}
void placement_tests(){
    const auto p=pc_placement(440.f,390.f);HudRect r;
    CHECK(hud_slot_rect(p,1.f,0.f,0.f,r));
    CHECK(near_f(r.l,439.5f)&&near_f(r.r,471.5f)&&near_f(r.t,480.f-404.5f)&&near_f(r.b,480.f-374.5f));
    const auto m=pc_placement(440.f,390.f,64.f);HudRect s;CHECK(hud_slot_rect(m,1.f,0.f,0.f,s)&&near_f(s.l,503.5f));
    const auto t=pc_placement(580.f,390.f);HudRect n;CHECK(hud_slot_rect(t,kNotifyScale,kNotifyOffsetX,kNotifyOffsetY,n));
    CHECK(near_f(n.r-n.l,48.f)&&near_f(n.b-n.t,45.f)&&near_f(n.l,565.f-.75f));
    HudPlacement none;CHECK(!hud_slot_rect(none,1.f,0.f,0.f,r));
}
void identity_tests(){
    for(int i=0;i<6;++i)CHECK(pc_hud_damage_index(kPcHudDamageSha[i])==i);
    CHECK(pc_hud_damage_index("00")==-1);
    std::vector<DWORD> wide(40*32,0x11223344u),tight(32*32,0x11223344u);
    CHECK(pc_hud_level0_sha(reinterpret_cast<const BYTE*>(wide.data()),40*4,D3DFMT_A8R8G8B8)==sha256_bytes(tight.data(),tight.size()*4));
    CHECK(pc_hud_level0_sha(nullptr,128,D3DFMT_A8R8G8B8).empty()&&pc_hud_level0_sha(reinterpret_cast<const BYTE*>(tight.data()),128,D3DFMT_DXT1).empty());
    PS2HudDamage off(true,L"nonexistent-dir\\PS2Port.ini");CHECK(!off.requested());
    std::vector<uint8_t> bad(kHudDamageGxiSize,0);std::vector<DWORD> out;
    CHECK(!decode_hud_damage_page(bad,0,out)&&out.empty()&&!decode_hud_damage_page(bad,2,out));
    PS2HudDamage h(false,L"x");LockTexture t;
    auto id=h.identify(&t,0);CHECK(id.index<0&&t.locks==0);
    id=h.identify(&t,7);CHECK(id.index<0&&t.locks==1);
    id=h.identify(&t,7);CHECK(t.locks==1);                                            // cached per generation
    t.desc.Pool=D3DPOOL_DEFAULT;id=h.identify(&t,8);CHECK(id.index<0&&t.locks==1);
}
void layer_tests(){
    std::vector<HudQuad> quads;const HudRect r{10,20,42,50};
    quads.push_back({r,0,0xff00ff00u});quads.push_back({r,5,0xffffffffu});quads.push_back({r,2,0xffffff00u});
    {Native n;Original o(n);PS2HudLayer l;const std::array<IDirect3DTexture8*,2> pages{&n.page0,&n.page1};
        CHECK(l.draw(n,pages,quads,1280,720,false,false)==S_OK&&n.draws==3&&n.begins==1&&n.ends==1);
        CHECK(n.drawn_textures.size()==3&&n.drawn_textures[0]==&n.page1&&n.drawn_textures[1]==&n.page0&&n.drawn_textures[2]==&n.page0);
        CHECK(n.drawn_colors[0]==0xff00ff00u);o.check(n);CHECK(!l.pending());
        CHECK(l.draw(n,pages,{},1280,720,false,false)==S_FALSE&&n.draws==3);
        CHECK(l.draw(n,pages,quads,1280,720,true,false)==S_FALSE&&n.draws==3);o.check(n);
        n.draw_hr=E_FAIL;CHECK(FAILED(l.draw(n,pages,quads,1280,720,false,false))&&!l.pending()&&!n.scene);o.check(n);}
    for(int failure=1;failure<=80;++failure){Native n;Original o(n);PS2HudLayer l;const std::array<IDirect3DTexture8*,2> pages{&n.page0,&n.page1};
        n.fail_set=failure;const HRESULT hr=l.draw(n,pages,quads,1280,720,false,false);CHECK(!n.scene);
        if(FAILED(hr)&&l.pending()){n.fail_set=0;CHECK(l.restore(n)==S_OK);}CHECK(!l.pending());o.check(n);}
    // UV of the steering icon: PSB page 1 (0.5,0.5)-(1,0.96875), inset half a texel; screen top gets v1.
    const auto v=hud_quad_vertices({r,0,0});
    CHECK(near_f(v[0].u,.5f+.5f/64.f)&&near_f(v[0].v,.96875f-.5f/64.f)&&near_f(v[3].u,1.f-.5f/64.f)&&near_f(v[3].v,.5f+.5f/64.f)&&v[0].y<v[3].y);
}
void frame_tests(){
    PS2HudDamage h(false,L"x");
    CHECK(h.frame(true,{0,0,0,0,0},1,false,.02f).empty());                          // PC drew no damage row
    for(int i=0;i<5;++i)h.note_pc_draw(i,pc_placement(440.f+35.f*i,390.f));
    h.note_pc_draw(5,pc_placement(440.f,390.f));
    auto q=h.frame(true,{.3f,0,0,0,0},1,false,.02f);
    CHECK(q.size()==12&&q[0].image==0&&q[0].color==hud_colour(kPS2DamageColours[1],1.f)&&q[5].image==5&&q[10].image==0&&q[11].image==5);
    CHECK(h.frame(true,{.3f,0,0,0,0},1,false,.02f).empty());                        // captures are per frame
    for(int i=0;i<5;++i)h.note_pc_draw(i,pc_placement(440.f+35.f*i,390.f));
    CHECK(h.frame(true,{0,0,0,0,0},2,false,.02f).size()==10&&h.state().band(0)==0);  // a new race resets
    CHECK(h.suppressed()==11&&h.feed_ok());
    h.frame(false,{},2,false,.02f);CHECK(!h.feed_ok());
}
// Fake memory: string pool, Broker and one vehicle output object.
struct FakeMemory final:RaceReadMemory {
    std::map<uint32_t,uint8_t> bytes;
    void put(uint32_t a,const void* p,size_t n){for(size_t i=0;i<n;++i)bytes[a+uint32_t(i)]=static_cast<const uint8_t*>(p)[i];}
    void u32(uint32_t a,uint32_t v){put(a,&v,4);}
    void f32(uint32_t a,float v){put(a,&v,4);}
    bool read(uint32_t a,void* out,size_t n) noexcept override{
        for(size_t i=0;i<n;++i){auto it=bytes.find(a+uint32_t(i));if(it==bytes.end())return false;static_cast<uint8_t*>(out)[i]=it->second;}
        return true;}
    std::map<std::string,uint32_t> ids;
    bool resolve_id(uint32_t,const char* key,uint32_t& id) noexcept override{auto it=ids.find(key);if(it==ids.end())return false;id=it->second;return true;}
};
void feed_tests(){
    HudDamageFeedReader r;FakeMemory m;
    CHECK(!r.read(m,0x400000,0).ok);
    auto f=r.read(m,0x400000,1);CHECK(!f.ok&&!std::strcmp(f.reason,"single_local_player_unproven"));
}

// ---- PS2HudMap
void map_math_tests(){
    MapHeading h;CHECK(h.update(0.f,1.f,0.f,0.f)&&near_f(h.x(),0.f)&&near_f(h.z(),-1.f));        // H = -forward
    CHECK(h.update(1.f,0.f,0.f,0.f));                                                          // 90 deg turn: filtered
    CHECK(near_f(std::sqrt(h.x()*h.x()+h.z()*h.z()),1.f)&&h.x()<0.f);
    MapHeading g;CHECK(!g.update(0.f,0.f,0.f,0.f));
    const auto a=map_local(0.f,10.f,0.f,0.f,0.f,-1.f);CHECK(near_f(a.x,0.f)&&near_f(a.y,-4.f));   // ahead is up
    const auto b=map_local(10.f,0.f,0.f,0.f,0.f,-1.f);CHECK(near_f(b.x,-4.f)&&near_f(b.y,0.f));
    MapPoint p{0.f,0.f},q{100.f,0.f};CHECK(map_clip(p,q)&&near_f(q.x,45.f)&&near_f(p.x,0.f));
    MapPoint r{50.f,50.f},t{60.f,60.f};CHECK(!map_clip(r,t));
    MapPoint u{-100.f,-100.f},v{100.f,100.f};CHECK(map_clip(u,v)&&near_f(u.y,-43.f)&&near_f(v.y,43.f));
    const auto seg=map_segment({0.f,0.f},{0.f,-10.f},6.f);CHECK(seg.size()==4&&near_f(std::fabs(seg[0].x-seg[1].x),6.f));
    float sx=0,sy=0;CHECK(map_screen(pc_placement(65.f,60.f),kMapCx,kMapCy,sx,sy)&&near_f(sx,74.f)&&near_f(sy,392.f));
    CHECK(map_colour(50,150,25,125)==0xfa329619u&&map_colour(250,250,250,200)==0xfffafafau);
}
void map_frame_tests(){
    PS2HudMap m(false,L"x");MapInput in;in.ok=true;in.fz=1.f;in.last=5;in.finish=8;in.first=0;
    for(int i=0;i<8;++i)in.points.push_back({0.f,10.f*i});
    CHECK(m.frame(in,1).empty()&&m.feed_ok());                                                    // PC drew no radar
    m.note_pc_draw(1,pc_placement(43.f,83.f));CHECK(m.frame(in,1).empty());                     // pointer only
    m.note_pc_draw(0,pc_placement(65.f,60.f));auto s=m.frame(in,1);
    // background + 7 shadow + 7 front + finish + 2 chevron + 2 frame
    CHECK(s.size()==1+7+7+1+4);
    CHECK(s.front().size()==4&&near_f(s.front()[0].x,29.f-.5f)&&near_f(s.front()[0].y,352.97f-.5f));
    CHECK(s.back().size()==10&&(s.back()[0].color>>24)==250u);
    MapInput off;CHECK(m.frame(off,1).empty()&&!m.feed_ok());
    CHECK(m.suppressed()==2);
}
void map_feed_tests(){
    FakeMemory m;const uint32_t base=0x400000;
    m.ids={{"Race/Car0/PlayerType",0},{"Car0",1},{"Race/Car0/LastMarker",2},{"RaceLine",3},{"FinishArea",4}};
    // Broker: [id, payload, tag] x 6 at 0x100000.
    const uint32_t broker=0x90000,records=0x100000;m.u32(base+kHudBrokerRva,broker);m.u32(broker+4,records);m.u32(broker+8,records+6*0x1c);m.u32(broker+12,records+6*0x1c);
    for(uint32_t i=0;i<6;++i){m.u32(records+i*0x1c,i);m.u32(records+i*0x1c+8,0);m.u32(records+i*0x1c+4,0x200000+i*0x100);}
    m.u32(records+8,2);m.u32(0x200000,1);                       // PlayerType = 1
    m.u32(records+0x1c+8,kHudBrokerObjectTag);                  // Car0 object
    m.u32(records+2*0x1c+8,2);m.u32(0x200200,5);                // LastMarker = 5
    const uint32_t car=0x200100,vehicle=0x300000,wheels=0x310000;m.u32(car+4,5);m.u32(car+8,vehicle);m.u32(car+0xc,wheels);
    // Pool text: id 5 = "gaVehicleOutputData".
    const uint32_t pm=0x91000,pv=0x92000,texts=0x93000,name=0x94000;m.u32(base+0x2f93d4,pm);m.u32(pm+4,pv);m.u32(pv+4,texts);m.u32(pv+8,texts+6*4);m.u32(pv+12,texts+6*4);
    for(uint32_t i=0;i<6;++i)m.u32(texts+i*4,name);
    const char type[]="gaVehicleOutputData";m.put(name,type,sizeof(type));
    for(uint32_t o:{0xdcu,0xe0u,0xe4u,0xecu,0xf0u,0xf4u,0x18u,0x1cu,0x20u,0x100u,0x104u,0x108u})m.f32(vehicle+o,0.f);
    m.f32(vehicle+0xe4,1.f);m.f32(vehicle+0x104,.65f);
    for(uint32_t o:{0x9cu,0x48u,0x144u,0xf0u,0xa0u,0x4cu,0x148u,0xf4u})m.f32(wheels+o,0.f);
    // Marker manager: list 3 RaceLine (10 points along z), list 4 FinishArea (0,70).
    const uint32_t mm=0x95000,lists=0x96000,rl=0x97000,fa=0x98000,rp=0x400000+0x500000,fp=rp+0x2000;
    m.u32(base+0x2f94e4,mm);m.u32(mm+4,lists);m.u32(mm+8,lists+5*4);for(uint32_t i=0;i<5;++i)m.u32(lists+i*4,i==3?rl:i==4?fa:rl);
    m.u32(rl+4,rp);m.u32(rl+8,rp+10*0x48);for(uint32_t i=0;i<10;++i){m.f32(rp+i*0x48+0x38,0.f);m.f32(rp+i*0x48+0x40,10.f*float(i));}
    m.u32(fa+4,fp);m.u32(fa+8,fp+0x48);m.f32(fp+0x38,0.f);m.f32(fp+0x40,70.f);
    HudDamageFeedReader r;
    auto f=r.read(m,base,7);CHECK(f.ok&&near_f(f.values[0],.65f));
    MapInput in;const char* reason=nullptr;
    CHECK(r.read_map(m,base,7,kMapWindow,in,reason)&&in.ok&&!std::strcmp(reason,"live_raceline"));
    CHECK(in.last==5&&in.finish==8&&in.first==0&&in.points.size()==8&&near_f(in.points[7].y,70.f)&&near_f(in.fz,1.f));
    m.u32(car+8,0);CHECK(!r.read(m,base,7).ok&&!r.read_map(m,base,7,kMapWindow,in,reason));     // vehicle pointer gone
}

// ---- PS2HudTemplate / PS2HudHidePcOnly (HUD-PORT4)
void template_tests(){
    for(size_t i=0;i<kHudTemplateCount;++i){const auto& e=kHudTemplateImages[i];CHECK(hud_template_index(e.pc_sha,e.pc_width,e.pc_height)==int(i));}
    CHECK(hud_template_index(kHudTemplateImages[0].pc_sha,64,64)==-1&&hud_template_index("00",128,128)==-1);
    std::vector<DWORD> wide(40*32,0x11223344u);
    CHECK(hud_level0_sha(reinterpret_cast<const BYTE*>(wide.data()),40*4,32,32,D3DFMT_A8R8G8B8)==pc_hud_level0_sha(reinterpret_cast<const BYTE*>(wide.data()),40*4,D3DFMT_A8R8G8B8));
    CHECK(hud_level0_sha(reinterpret_cast<const BYTE*>(wide.data()),16,8,8,D3DFMT_A8R8G8B8).empty());
    std::array<std::vector<DWORD>,kHudTemplateCount> out;
    std::vector<uint8_t> pack={'M','R','H','T',2,0,0,0,uint8_t(kHudTemplateCount),0,0,0};
    CHECK(!decode_hud_template_pack(pack,out));                                                // truncated
    pack[4]=1;CHECK(!decode_hud_template_pack(pack,out));                                      // v1 (doubled alpha) rejected
    // Only the progress car (image 3) is remapped: PC box (-5,-3)..(11,5) onto the PS2 arrow box (-5,-6)..(8,10).
    for(const auto& e:kHudTemplateImages){const auto& r=e.remap;
        if(e.image!=3)CHECK(r.sx==1.f&&r.tx==0.f&&r.sy==1.f&&r.ty==0.f&&e.width==e.pc_width&&e.height==e.pc_height);
        else CHECK(r.sx*-5.f+r.tx==-5.f&&r.sx*11.f+r.tx==8.f&&r.sy*-3.f+r.ty==-6.f&&r.sy*5.f+r.ty==10.f&&e.width==16&&e.height==16);}
    PS2HudTemplate off(true,L"nonexistent-dir\\PS2Port.ini");CHECK(!off.requested());
    PS2HudTemplate t(false,L"x");LockTexture tex;CHECK(!t.ready()&&t.substitute(&tex,7)==nullptr&&tex.locks==0);
}
void egg_tests(){
    CHECK(hud_egg_role_for_name("SpeedVelocityText")==HudEggRole::PcOnly&&hud_egg_role_for_name("TimeDiffs")==HudEggRole::PcOnly&&
          hud_egg_role_for_name("TimeDiffArrow")==HudEggRole::PcOnly);
    CHECK(hud_egg_role_for_name("SpeedVelocity")==HudEggRole::Named&&hud_egg_role_for_name("")==HudEggRole::Unknown&&hud_egg_role_for_name(nullptr)==HudEggRole::Unknown);
    FakeMemory m;const uint32_t base=0x400000;
    // Pool text ids 0..3.
    const uint32_t pm=0x91000,pv=0x92000,texts=0x93000;m.u32(base+0x2f93d4,pm);m.u32(pm+4,pv);m.u32(pv+4,texts);m.u32(pv+8,texts+4*4);m.u32(pv+12,texts+4*4);
    const char* names[4]={"Null","SpeedVelocityText","GameTimer","TimeDiffs"};
    for(uint32_t i=0;i<4;++i){m.u32(texts+i*4,0x94000+i*0x40);m.put(0x94000+i*0x40,names[i],std::strlen(names[i])+1);}
    // Egg registry: buckets by name id.
    const uint32_t mgr=0x95000,reg=0x95100,rb=0x95200,bucket=0x95300,eggs=0x95400;
    m.u32(base+kHudEggManagerRva,mgr);m.u32(mgr+0x1c,reg);m.u32(reg+4,rb);m.u32(reg+8,rb+4*4);
    const uint32_t kph=0x210000,timer=0x211000,stray=0x212000;
    for(uint32_t id=0;id<4;++id){m.u32(rb+id*4,bucket+id*0x10);m.u32(bucket+id*0x10+4,eggs+id*0x10);m.u32(bucket+id*0x10+8,eggs+id*0x10+4);}
    m.u32(eggs+1*0x10,kph);m.u32(eggs+2*0x10,timer);m.u32(eggs+3*0x10,0x213000);
    for(uint32_t e:{kph,timer,stray}){uint8_t f=0;m.put(e,&f,1);}
    m.u32(kph+0x5c,1);m.u32(timer+0x5c,2);m.u32(stray+0x5c,3);
    HudEggNames n;
    auto a=n.resolve(m,base,kph);CHECK(a.role==HudEggRole::PcOnly&&!std::strcmp(a.name,"SpeedVelocityText"));
    auto b=n.resolve(m,base,timer);CHECK(b.role==HudEggRole::Named&&!std::strcmp(b.name,"GameTimer"));
    CHECK(n.resolve(m,base,stray).role==HudEggRole::Unknown);                                  // not the registered egg
    CHECK(n.resolve(m,base,0).role==HudEggRole::Unknown&&n.resolve(m,base,kph+1).role==HudEggRole::Unknown);
    std::string json;CHECK(n.take_seen_json(json)&&json.find("\"SpeedVelocityText\",\"GameTimer\"")!=std::string::npos&&!n.take_seen_json(json));
    uint8_t retired=2;m.put(kph,&retired,1);CHECK(n.resolve(m,base,kph).role==HudEggRole::Unknown);
    retired=0;m.put(kph,&retired,1);m.u32(kph+0x5c,2);CHECK(n.resolve(m,base,kph).role==HudEggRole::Unknown);   // id moved to another name
}

// ---- PS2HudTimeDiffs (gaHudTimeDiffs2Ai)
void timediffs_text_tests(){
    CHECK(time_diff_text(0,0,1.f)=="--.--"&&time_diff_text(1,0,0.f)=="--.--"&&time_diff_text(1,0,.17f)=="0.17"&&time_diff_text(2,0,-1.256f)=="-1.26");
    CHECK(time_diff_colour(1,0,.5f)==0xff7fff7fu&&time_diff_colour(1,0,-.5f)==0xffff7f7fu&&time_diff_colour(0,0,.5f)==0xffffffffu);
    HudTimeDiffsArt art;std::vector<uint8_t> bad(64,0);CHECK(!decode_hud_timediffs_pack(bad,art)&&art.pages.empty());
    PS2HudTimeDiffs off(true,L"nonexistent-dir\\PS2Port.ini");CHECK(!off.requested()&&!off.hide_rows());
    CHECK(kPs2CarSmallImage[0]==9&&kPs2CarSmallImage[17]==0&&kPs2CarSmallImage[28]==23);
}
void timediffs_model_tests(){
    // Two cars, local car 0 (rank 2), car 1 ahead (rank 1); 10 markers.
    TimeDiffsInput in;in.ok=true;in.count=2;in.local=0;in.markers=10;
    for(auto& c:in.cars)c.exists=true;
    in.cars[0]={1.f,2,1,0,true};in.cars[1]={3.f,1,3,5,true};
    TimeDiffsModel m;
    in.local_time=10.f;for(int f=0;f<20;++f)m.update(in,1,.0201f);   // 20 frames: car1 stamps marker 3, car0 marker 1 at t=10
    CHECK(!m.shown());
    in.cars[0].last_marker=3;in.local_time=12.5f;for(int f=0;f<20;++f)m.update(in,1,.0201f);   // car0 reaches marker 3 at 12.5 (first stamp there)
    CHECK(m.shown()&&m.count()==2);
    auto rows=m.rows(in);CHECK(rows.size()==2&&rows[0].car==1&&rows[1].car==0);
    // car 1 ahead: T - stamp(1, marker of local=3) = 12.5 - 10 = 2.5 (green); local row "--.--".
    CHECK(near_f(rows[0].value,2.5f)&&time_diff_text(rows[1].car,in.local,rows[1].value)=="--.--");
    TimeDiffsInput solo=in;solo.count=1;TimeDiffsModel s;s.update(solo,1,1.f);CHECK(!s.shown()&&s.rows(solo).empty());
    TimeDiffsInput broken=in;broken.ok=false;m.update(broken,1,1.f);CHECK(!m.shown());
}
void timediffs_rows_tests(){
    FakeMemory m;const uint32_t base=0x400000;
    m.ids={{"TimeDiffs",3}};
    const uint32_t mgr=0x95000,reg=0x95100,rb=0x95200,bucket=0x95300,eggs=0x95400,egg=0x210000,ai=0x220000;
    m.u32(base+kHudEggManagerRva,mgr);m.u32(mgr+0x1c,reg);m.u32(reg+4,rb);m.u32(reg+8,rb+4*4);
    m.u32(rb+3*4,bucket);m.u32(bucket+4,eggs);m.u32(bucket+8,eggs+4);m.u32(eggs,egg);
    uint8_t flags=0;m.put(egg,&flags,1);m.u32(egg+0x5c,3);m.u32(egg+4,ai);m.u32(ai,base+kPcTimeDiffsAiVtableRva);
    m.u32(ai+0xc,0x230000);m.u32(ai+0x10,0x231000);m.u32(ai+0x14,0x232000);
    PcTimeDiffsRows r;CHECK(r.refresh(m,base,5)&&r.row_of(0x231000)==1&&r.row_of(0x232000)==2&&r.row_of(egg)==-1&&r.row_of(0)==-1);
    m.u32(ai,base+0x291000);CHECK(!r.refresh(m,base,5)&&r.row_of(0x231000)==-1&&!std::strcmp(r.reason(),"time_diffs_ai_type_mismatch"));
    m.u32(ai,base+kPcTimeDiffsAiVtableRva);m.u32(bucket+8,eggs+8);CHECK(!r.refresh(m,base,5));   // name not unique
}
void timediffs_feed_tests(){
    FakeMemory m;const uint32_t base=0x400000;
    // Broker records [id, payload, tag] at 0x100000; ids 0..13.
    const char* keys[]={"Race/NumCars","Race/Car0/PlayerType","Race/Car1/PlayerType","Car0","Race/Car0/Progress","Race/Car0/Rank","Race/Car0/LastMarker","Race/Car0/CarType",
                        "Car1","Race/Car1/Progress","Race/Car1/Rank","Race/Car1/LastMarker","Race/Car1/CarType","Race/Car0/Time","RaceLine"};
    for(uint32_t i=0;i<15;++i)m.ids[keys[i]]=i;
    const uint32_t broker=0x90000,records=0x100000;m.u32(base+kHudBrokerRva,broker);m.u32(broker+4,records);m.u32(broker+8,records+15*0x1c);m.u32(broker+12,records+15*0x1c);
    auto rec=[&](uint32_t id,uint32_t tag,uint32_t value){m.u32(records+id*0x1c,id);m.u32(records+id*0x1c+4,0x200000+id*0x10);m.u32(records+id*0x1c+8,tag);m.u32(0x200000+id*0x10,value);};
    auto realv=[](float f){uint32_t v=0;std::memcpy(&v,&f,4);return v;};
    rec(0,2,2);rec(1,2,1);rec(2,2,0);rec(3,10,0x300000);rec(4,1,realv(.4f));rec(5,2,2);rec(6,2,7);rec(7,4,2);
    rec(8,10,0x300100);rec(9,1,realv(.6f));rec(10,2,1);rec(11,2,9);rec(12,4,3);rec(13,1,realv(31.5f));
    // Pool text: id 2 = "astero" (any case), id 3 = "NoSuchCar".
    const uint32_t pm=0x91000,pv=0x92000,texts=0x93000;m.u32(base+0x2f93d4,pm);m.u32(pm+4,pv);m.u32(pv+4,texts);m.u32(pv+8,texts+4*4);m.u32(pv+12,texts+4*4);
    const char* names[4]={"x","y","astero","NoSuchCar"};
    for(uint32_t i=0;i<4;++i){m.u32(texts+i*4,0x94000+i*0x40);m.put(0x94000+i*0x40,names[i],std::strlen(names[i])+1);}
    const uint32_t mm=0x95000,lists=0x96000,rl=0x97000;m.u32(base+0x2f94e4,mm);m.u32(mm+4,lists);m.u32(mm+8,lists+15*4);
    for(uint32_t i=0;i<15;++i)m.u32(lists+i*4,rl);m.u32(rl+4,0x400000+0x600000);m.u32(rl+8,0x400000+0x600000+20*0x48);
    TimeDiffsFeedReader r;auto in=r.read(m,base,7);
    CHECK(in.ok&&in.count==2&&in.local==0&&in.markers==20&&near_f(in.local_time,31.5f)&&in.cars[1].rank==1&&in.cars[0].car_type==17&&in.cars[1].car_type==-1&&in.cars[1].exists);
    CHECK(ps2_car_id("SEATBUGGY")==22&&ps2_car_id("Tank")==28&&ps2_car_id("Tan")==-1&&ps2_car_id(nullptr)==-1);
    m.u32(records+4*0x1c+8,2);CHECK(!r.read(m,base,7).ok);                    // Progress no longer a float
}

// ---- HUD-PORT6: split flash, map splits/opponents, deferred ticks/finish
void split_flash_tests(){
    SplitFlashModel f;CHECK(near_f(f.colour(),1.f)&&!f.active());
    f.update(0,.0201f);CHECK(f.active()&&near_f(f.colour(),1.f));                         // first SplitPoint arms (last -1)
    f.update(0,.0201f);CHECK(near_f(f.colour(),std::fabs(std::sin(90.f))));               // |sinf(90 rad)| = 0.894
    f.update(0,.0201f);CHECK(near_f(f.colour(),std::fabs(std::sin(96.f))));
    for(int i=0;i<70;++i)f.update(0,.0201f);CHECK(!f.active()&&near_f(f.colour(),1.f));     // 60 steps then white
    f.update(1,.0201f);CHECK(f.active());                                                   // next split
    PS2HudSplitFlash off(false,L"x");CHECK(!off.requested()&&near_f(off.factor(),1.f));
}
void map_extra_tests(){
    MapInput in;in.ok=true;in.fz=1.f;in.first=0;in.finish=8;in.last=2;
    for(int i=0;i<8;++i)in.points.push_back({0.f,10.f*i});
    std::vector<MapPoint> bar;
    CHECK(map_crossbar(in,3,0.f,0.f,0.f,-1.f,10.f,bar)&&bar.size()==4);
    const float len=std::sqrt((bar[0].x-bar[2].x)*(bar[0].x-bar[2].x)+(bar[0].y-bar[2].y)*(bar[0].y-bar[2].y));
    CHECK(near_f(len,20.f)&&!map_crossbar(in,0,0.f,0.f,0.f,-1.f,10.f,bar)&&!map_crossbar(in,8,0.f,0.f,0.f,-1.f,10.f,bar));
    std::vector<std::vector<MapPoint>> x;map_cross({0.f,0.f},0.f,x);CHECK(x.size()==2);
    std::vector<std::vector<MapPoint>> outside;map_cross({200.f,0.f},0.f,outside);CHECK(outside.empty());          // clipped away
    CHECK(map_byte(.24f,250.f)==60u&&map_byte(.24f,40.f)==9u&&map_byte(2.f,250.f)==255u);
    PS2HudMap m(false,L"x");in.splits={3};in.opponents.push_back({0.f,20.f,.24f,.33f,.61f});
    m.note_pc_draw(0,pc_placement(65.f,60.f));
    auto s=m.frame(in,1);
    // background + 7+7 route + split + finish + chevron shadow + 2 shadow X + 2 X + chevron + 2 frame
    CHECK(s.size()==1+7+7+1+1+1+2+2+1+2);
}
void template_defer_tests(){
    CHECK(hud_template_deferred(6)&&hud_template_deferred(5)&&hud_template_deferred(4)&&!hud_template_deferred(0)&&!hud_template_deferred(3));
    PS2HudTemplate t(false,L"x");
    CHECK(!t.defer(kHudTemplateImages[0],pc_placement(480.f,30.f)));                            // dial is not deferred
    CHECK(t.defer(kHudTemplateImages[4],pc_placement(480.f,30.f))&&t.defer(kHudTemplateImages[3],pc_placement(240.f,30.f)));
    auto q=t.take_deferred();CHECK(q.size()==2&&q[0].page==4&&q[1].page==3&&near_f(q[0].v0,1.f)&&near_f(q[0].u1,.5f)&&near_f(q[1].u1,1.f)&&q[0].rect.r>q[0].rect.l);
    CHECK(t.take_deferred().empty());
}

// ---- RACE-CERT2 overlay race certificate
#include "ps2_race_certificate_contracts.hpp"
}
int main(){band_tests();state_tests();placement_tests();identity_tests();layer_tests();frame_tests();feed_tests();map_math_tests();map_frame_tests();map_feed_tests();
    template_tests();egg_tests();timediffs_text_tests();timediffs_model_tests();timediffs_rows_tests();timediffs_feed_tests();split_flash_tests();map_extra_tests();template_defer_tests();
    race_certificate_parse_tests();race_certificate_finished_tests();race_certificate_attract_tests();race_certificate_hud_tests();
    if(failures)std::cerr<<failures<<" failures\n";return failures?1:0;}
