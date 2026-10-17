#include "ps2_color.hpp"
#include <array>
#include <cmath>
#include <cstring>
#include <iostream>

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
struct DrawState { DWORD src,dest,factor,op0,arg1,arg2,op1; IDirect3DBaseTexture8* tex0; D3DVIEWPORT8 vp; bool scene; };
struct Native final:MockDeviceBase {
    std::array<DWORD,256> rs{};
    std::array<std::array<DWORD,64>,3> tss{};
    Texture original0,original1,copied;
    Surface back,other;
    Buffer buffer;
    IDirect3DSurface8* target=&back;
    std::array<IDirect3DBaseTexture8*,2> textures={&original0,&original1};
    IDirect3DVertexBuffer8* stream=&buffer;
    UINT stride=36;
    D3DVIEWPORT8 viewport{1,2,1270,710,.2f,.8f};
    DWORD vertex=0x152,pixel=17;
    D3DCAPS8 caps{};
    int sets=0,fail_set=0,copies=0,creates=0,begins=0,ends=0,draws=0;
    bool scene=false;
    HRESULT copy_hr=S_OK,draw_hr=S_OK;
    std::array<DrawState,4> drawn{};
    Native(){for(size_t i=0;i<rs.size();++i)rs[i]=static_cast<DWORD>(1000+i);
        for(size_t s=0;s<3;++s)for(size_t i=0;i<tss[s].size();++i)tss[s][i]=static_cast<DWORD>(2000+s*64+i);
        caps.MaxTextureWidth=caps.MaxTextureHeight=4096;caps.TextureCaps=D3DPTEXTURECAPS_POW2;caps.MaxTextureBlendStages=8;
        caps.TextureOpCaps=D3DTEXOPCAPS_MODULATE|D3DTEXOPCAPS_SELECTARG1|D3DTEXOPCAPS_SELECTARG2;
        caps.SrcBlendCaps=D3DPBLENDCAPS_ZERO|D3DPBLENDCAPS_ONE;caps.DestBlendCaps=D3DPBLENDCAPS_SRCCOLOR|D3DPBLENDCAPS_ONE;
        caps.TextureFilterCaps=D3DPTFILTERCAPS_MAGFPOINT|D3DPTFILTERCAPS_MINFPOINT;}
    HRESULT write(){++sets;return sets==fail_set?D3DERR_INVALIDCALL:S_OK;}
    HRESULT STDMETHODCALLTYPE GetRenderState(D3DRENDERSTATETYPE k,DWORD* p) override{*p=rs[k];return S_OK;}
    HRESULT STDMETHODCALLTYPE SetRenderState(D3DRENDERSTATETYPE k,DWORD v) override{const auto r=write();rs[k]=v;return r;}
    HRESULT STDMETHODCALLTYPE GetTextureStageState(DWORD s,D3DTEXTURESTAGESTATETYPE k,DWORD* p) override{*p=tss[s][k];return S_OK;}
    HRESULT STDMETHODCALLTYPE SetTextureStageState(DWORD s,D3DTEXTURESTAGESTATETYPE k,DWORD v) override{const auto r=write();tss[s][k]=v;return r;}
    HRESULT STDMETHODCALLTYPE GetVertexShader(DWORD* p) override{*p=vertex;return S_OK;}
    HRESULT STDMETHODCALLTYPE SetVertexShader(DWORD v) override{const auto r=write();vertex=v;return r;}
    HRESULT STDMETHODCALLTYPE GetPixelShader(DWORD* p) override{*p=pixel;return S_OK;}
    HRESULT STDMETHODCALLTYPE SetPixelShader(DWORD v) override{const auto r=write();pixel=v;return r;}
    HRESULT STDMETHODCALLTYPE GetTexture(DWORD s,IDirect3DBaseTexture8** p) override{*p=textures[s];if(*p)(*p)->AddRef();return S_OK;}
    HRESULT STDMETHODCALLTYPE SetTexture(DWORD s,IDirect3DBaseTexture8* p) override{const auto r=write();if(p)p->AddRef();if(textures[s])textures[s]->Release();textures[s]=p;return r;}
    HRESULT STDMETHODCALLTYPE GetRenderTarget(IDirect3DSurface8** p) override{*p=target;(*p)->AddRef();return S_OK;}
    HRESULT STDMETHODCALLTYPE GetBackBuffer(UINT,D3DBACKBUFFER_TYPE,IDirect3DSurface8** p) override{*p=&back;back.AddRef();return S_OK;}
    HRESULT STDMETHODCALLTYPE GetViewport(D3DVIEWPORT8* p) override{*p=viewport;return S_OK;}
    HRESULT STDMETHODCALLTYPE SetViewport(const D3DVIEWPORT8* p) override{const auto r=write();viewport=*p;return r;}
    HRESULT STDMETHODCALLTYPE GetStreamSource(UINT,IDirect3DVertexBuffer8** p,UINT* v) override{*p=stream;*v=stride;if(*p)(*p)->AddRef();return S_OK;}
    HRESULT STDMETHODCALLTYPE SetStreamSource(UINT,IDirect3DVertexBuffer8* p,UINT v) override{const auto r=write();if(p)p->AddRef();if(stream)stream->Release();stream=p;stride=v;return r;}
    HRESULT STDMETHODCALLTYPE GetDeviceCaps(D3DCAPS8* p) override{*p=caps;return S_OK;}
    HRESULT STDMETHODCALLTYPE BeginScene() override{++begins;CHECK(!scene);scene=true;return S_OK;}
    HRESULT STDMETHODCALLTYPE EndScene() override{++ends;CHECK(scene);scene=false;return S_OK;}
    HRESULT STDMETHODCALLTYPE CreateTexture(UINT w,UINT h,UINT levels,DWORD usage,D3DFORMAT format,D3DPOOL pool,IDirect3DTexture8** p) override{
        CHECK(levels==1&&usage==D3DUSAGE_RENDERTARGET&&pool==D3DPOOL_DEFAULT);++creates;
        copied.refs=1;copied.surface.desc.Width=w;copied.surface.desc.Height=h;copied.surface.desc.Format=format;*p=&copied;return S_OK;}
    HRESULT STDMETHODCALLTYPE CopyRects(IDirect3DSurface8* src,const RECT*,UINT,IDirect3DSurface8* dst,const POINT*) override{
        CHECK(src==&back&&dst==&copied.surface&&!scene);++copies;return copy_hr;}
    HRESULT STDMETHODCALLTYPE DrawPrimitiveUP(D3DPRIMITIVETYPE p,UINT n,const void* data,UINT bytes) override{
        CHECK(p==D3DPT_TRIANGLESTRIP&&n==2&&bytes==28&&data&&target==&back);
        const auto* v=static_cast<const PS2ColorVertex*>(data);
        const float uw=float(back.desc.Width)/copied.surface.desc.Width,vh=float(back.desc.Height)/copied.surface.desc.Height;
        CHECK(v[3].x==back.desc.Width-.5f&&v[3].y==back.desc.Height-.5f&&std::abs(v[3].u-uw)<1e-6f&&std::abs(v[3].v-vh)<1e-6f);
        if(draws<4)drawn[draws]={rs[D3DRS_SRCBLEND],rs[D3DRS_DESTBLEND],rs[D3DRS_TEXTUREFACTOR],tss[0][D3DTSS_COLOROP],tss[0][D3DTSS_COLORARG1],
            tss[0][D3DTSS_COLORARG2],tss[1][D3DTSS_COLOROP],textures[0],viewport,scene};
        ++draws;if(stream)stream->Release();stream=nullptr;stride=0;return draw_hr;}
};
struct Original {
    std::array<DWORD,256> rs;std::array<std::array<DWORD,64>,3> tss;D3DVIEWPORT8 viewport;
    Original(const Native& n):rs(n.rs),tss(n.tss),viewport(n.viewport){}
    void check(const Native& n) const{CHECK(rs==n.rs&&tss==n.tss);CHECK(std::memcmp(&viewport,&n.viewport,sizeof(viewport))==0);
        CHECK(n.stream==&n.buffer&&n.stride==36&&n.vertex==0x152&&n.pixel==17&&!n.scene);
        CHECK(n.textures[0]==&n.original0&&n.textures[1]==&n.original1);
        CHECK(n.original0.refs==1&&n.original1.refs==1&&n.buffer.refs==1&&n.back.refs==1);}
};
PS2ColorConfig on(){PS2ColorConfig c;c.enabled=true;c.k={.4f,.2f,0.f};return c;}

void config_tests(){
    std::array<float,3> k{};
    CHECK(parse_ps2_color_curve(L"0.426,0.384,0.364",k)&&std::abs(k[0]-.426f)<1e-6f&&std::abs(k[2]-.364f)<1e-6f);
    CHECK(parse_ps2_color_curve(L" 0 , 1 , 0.5 ",k)&&k[1]==1.f);
    CHECK(!parse_ps2_color_curve(L"0.4,0.4",k));CHECK(!parse_ps2_color_curve(L"0.4,0.4,1.5",k));
    CHECK(!parse_ps2_color_curve(L"-0.1,0.4,0.4",k));CHECK(!parse_ps2_color_curve(L"0.4,0.4,0.4,0.4",k));
    CHECK(!parse_ps2_color_curve(nullptr,k));
    CHECK(ps2_color_factor({1.f,.5f,0.f})==0xffff8000u);CHECK(ps2_color_factor({.6f,.8f,1.f})==0xff99ccffu);
    PS2ColorConfig d;CHECK(!d.enabled&&d.k==kPS2ColorDefaultCurve);
}
void pass_tests(){
    {Native n;Original original(n);PS2ColorGrade g;CHECK(g.apply(n,false,false)==S_FALSE);CHECK(n.sets==0&&n.copies==0&&n.draws==0);original.check(n);}
    {Native n;Original original(n);PS2ColorGrade g(on());
        CHECK(g.apply(n,false,false)==S_OK);CHECK(n.copies==1&&n.draws==2&&n.creates==1&&n.begins==1&&n.ends==1);
        CHECK(n.copied.surface.desc.Width==2048&&n.copied.surface.desc.Height==1024);
        const auto& a=n.drawn[0];const auto& b=n.drawn[1];
        // Pass A: dest *= (1-k).  Pass B: dest += k * copy^2.
        CHECK(a.src==D3DBLEND_ZERO&&a.dest==D3DBLEND_SRCCOLOR&&a.factor==ps2_color_factor({.6f,.8f,1.f})&&a.op0==D3DTOP_SELECTARG2&&a.arg2==D3DTA_TFACTOR&&a.op1==D3DTOP_DISABLE);
        CHECK(b.src==D3DBLEND_ONE&&b.dest==D3DBLEND_ONE&&b.factor==ps2_color_factor({.4f,.2f,0.f})&&b.op0==D3DTOP_MODULATE&&b.arg1==D3DTA_TEXTURE&&b.arg2==D3DTA_TEXTURE&&b.op1==D3DTOP_MODULATE);
        CHECK(a.tex0==&n.copied&&b.tex0==&n.copied&&a.scene&&b.scene);
        CHECK(a.vp.X==0&&a.vp.Y==0&&a.vp.Width==1280&&a.vp.Height==720&&a.vp.MinZ==0.f&&a.vp.MaxZ==1.f);
        CHECK(!g.pending()&&g.status().frames==1);original.check(n);
        CHECK(g.apply(n,false,false)==S_OK);CHECK(n.creates==1&&n.copies==2&&n.draws==4);original.check(n);
        g.before_reset();CHECK(n.copied.refs==0&&n.copied.surface.refs==1);
        CHECK(g.apply(n,false,false)==S_OK);CHECK(n.creates==2);original.check(n);}
    {Native n;Original original(n);PS2ColorGrade g(on());CHECK(g.apply(n,true,false)==S_FALSE);CHECK(n.sets==0&&n.copies==0);
        CHECK(g.apply(n,false,true)==S_FALSE);CHECK(n.sets==0&&n.copies==0);original.check(n);}
    {Native n;Original original(n);PS2ColorGrade g(on());n.target=&n.other;CHECK(g.apply(n,false,false)==S_FALSE);
        CHECK(n.copies==0&&n.creates==0);n.target=&n.back;original.check(n);}
    {Native n;Original original(n);PS2ColorGrade g(on());n.back.desc.Format=D3DFMT_R5G6B5;CHECK(FAILED(g.apply(n,false,false)));
        CHECK(n.copies==0&&n.creates==0);n.back.desc.Format=D3DFMT_X8R8G8B8;CHECK(FAILED(g.apply(n,false,false))&&n.copies==0);original.check(n);}
    {Native n;Original original(n);n.caps.DestBlendCaps=D3DPBLENDCAPS_ONE;PS2ColorGrade g(on());CHECK(FAILED(g.apply(n,false,false)));CHECK(n.copies==0);original.check(n);}
    {Native n;Original original(n);n.copy_hr=E_FAIL;PS2ColorGrade g(on());CHECK(FAILED(g.apply(n,false,false)));CHECK(n.draws==0&&n.sets==0);original.check(n);}
    {Native n;Original original(n);n.draw_hr=E_FAIL;PS2ColorGrade g(on());CHECK(FAILED(g.apply(n,false,false)));
        CHECK(n.draws==1&&!g.pending()&&n.ends==1);original.check(n);}
    // Any failing native write, during the passes or during restore, leaves either the original state or a
    // pending transaction that one explicit restore finishes.
    for(int failure=1;failure<=140;++failure){Native n;Original original(n);PS2ColorGrade g(on());n.fail_set=failure;
        const HRESULT hr=g.apply(n,false,false);CHECK(!n.scene);
        if(FAILED(hr)&&g.pending()){n.fail_set=0;CHECK(g.restore(n)==S_OK);}
        CHECK(!g.pending());original.check(n);}
    {Native n;n.caps.TextureCaps=0;n.back.desc.MultiSampleType=D3DMULTISAMPLE_4_SAMPLES;Original original(n);PS2ColorGrade g(on());
        CHECK(g.apply(n,false,false)==S_OK);CHECK(n.copied.surface.desc.Width==1280);original.check(n);}
    {Native n;n.back.desc.MultiSampleType=D3DMULTISAMPLE_4_SAMPLES;PS2ColorGrade g(on());CHECK(FAILED(g.apply(n,false,false))&&n.copies==0&&n.creates==0);}
}
}
int main(){config_tests();pass_tests();if(failures)std::cerr<<failures<<" failures\n";return failures?1:0;}
