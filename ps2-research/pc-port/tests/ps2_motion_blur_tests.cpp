#include "ps2_motion_blur.hpp"
#include "reflection_pilot.hpp"
#include <array>
#include <cmath>
#include <cstring>
#include <iostream>
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
struct Native final:MockDeviceBase {
    std::array<DWORD,256> rs{};std::array<std::array<DWORD,64>,2> tss{};
    Texture original0,original1,history;Surface back,other;Buffer buffer;
    IDirect3DSurface8* target=&back;std::array<IDirect3DBaseTexture8*,2> textures={&original0,&original1};
    IDirect3DVertexBuffer8* stream=&buffer;UINT stride=36;D3DVIEWPORT8 viewport{1,2,1270,710,.2f,.8f};DWORD vertex=0x152,pixel=17;D3DCAPS8 caps{};
    int sets=0,fail_set=0,copies=0,creates=0,draws=0,begins=0,ends=0;bool scene=false;HRESULT copy_hr=S_OK,draw_hr=S_OK;
    DWORD drawn_factor=0,drawn_src=0,drawn_dest=0,drawn_blend=0;IDirect3DBaseTexture8* drawn_tex=nullptr;
    Native(){for(size_t i=0;i<rs.size();++i)rs[i]=DWORD(1000+i);for(size_t s=0;s<2;++s)for(size_t i=0;i<64;++i)tss[s][i]=DWORD(2000+s*64+i);
        caps.MaxTextureWidth=caps.MaxTextureHeight=4096;caps.TextureCaps=D3DPTEXTURECAPS_POW2;caps.TextureOpCaps=D3DTEXOPCAPS_SELECTARG1;
        caps.SrcBlendCaps=D3DPBLENDCAPS_SRCALPHA;caps.DestBlendCaps=D3DPBLENDCAPS_INVSRCALPHA;caps.TextureFilterCaps=D3DPTFILTERCAPS_MAGFPOINT|D3DPTFILTERCAPS_MINFPOINT;}
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
    HRESULT STDMETHODCALLTYPE GetRenderTarget(IDirect3DSurface8** p) override{*p=target;(*p)->AddRef();return S_OK;}
    HRESULT STDMETHODCALLTYPE GetBackBuffer(UINT,D3DBACKBUFFER_TYPE,IDirect3DSurface8** p) override{*p=&back;back.AddRef();return S_OK;}
    HRESULT STDMETHODCALLTYPE GetViewport(D3DVIEWPORT8* p) override{*p=viewport;return S_OK;}
    HRESULT STDMETHODCALLTYPE SetViewport(const D3DVIEWPORT8* p) override{const auto r=w();viewport=*p;return r;}
    HRESULT STDMETHODCALLTYPE GetStreamSource(UINT,IDirect3DVertexBuffer8** p,UINT* v) override{*p=stream;*v=stride;if(*p)(*p)->AddRef();return S_OK;}
    HRESULT STDMETHODCALLTYPE SetStreamSource(UINT,IDirect3DVertexBuffer8* p,UINT v) override{const auto r=w();if(p)p->AddRef();if(stream)stream->Release();stream=p;stride=v;return r;}
    HRESULT STDMETHODCALLTYPE GetDeviceCaps(D3DCAPS8* p) override{*p=caps;return S_OK;}
    HRESULT STDMETHODCALLTYPE BeginScene() override{++begins;CHECK(!scene);scene=true;return S_OK;}
    HRESULT STDMETHODCALLTYPE EndScene() override{++ends;CHECK(scene);scene=false;return S_OK;}
    HRESULT STDMETHODCALLTYPE CreateTexture(UINT wd,UINT h,UINT levels,DWORD usage,D3DFORMAT f,D3DPOOL pool,IDirect3DTexture8** p) override{
        CHECK(levels==1&&usage==D3DUSAGE_RENDERTARGET&&pool==D3DPOOL_DEFAULT);++creates;history.refs=1;history.surface.desc.Width=wd;history.surface.desc.Height=h;history.surface.desc.Format=f;*p=&history;return S_OK;}
    HRESULT STDMETHODCALLTYPE CopyRects(IDirect3DSurface8* src,const RECT*,UINT,IDirect3DSurface8* dst,const POINT*) override{CHECK(src==&back&&dst==&history.surface&&!scene);++copies;return copy_hr;}
    HRESULT STDMETHODCALLTYPE DrawPrimitiveUP(D3DPRIMITIVETYPE p,UINT n,const void* data,UINT bytes) override{
        CHECK(p==D3DPT_TRIANGLESTRIP&&n==2&&bytes==28&&data&&scene&&target==&back);
        drawn_factor=rs[D3DRS_TEXTUREFACTOR];drawn_src=rs[D3DRS_SRCBLEND];drawn_dest=rs[D3DRS_DESTBLEND];drawn_tex=textures[0];drawn_blend=rs[D3DRS_ALPHABLENDENABLE];
        CHECK(tss[0][D3DTSS_ALPHAARG1]==D3DTA_TFACTOR&&tss[0][D3DTSS_COLOROP]==D3DTOP_SELECTARG1&&viewport.X==0);
        ++draws;if(stream)stream->Release();stream=nullptr;stride=0;return draw_hr;}
};
struct Original {
    std::array<DWORD,256> rs;std::array<std::array<DWORD,64>,2> tss;D3DVIEWPORT8 viewport;
    explicit Original(const Native& n):rs(n.rs),tss(n.tss),viewport(n.viewport){}
    void check(const Native& n) const{CHECK(rs==n.rs&&tss==n.tss);CHECK(std::memcmp(&viewport,&n.viewport,sizeof(viewport))==0);
        CHECK(n.stream==&n.buffer&&n.stride==36&&n.vertex==0x152&&n.pixel==17&&!n.scene);
        CHECK(n.textures[0]==&n.original0&&n.textures[1]==&n.original1&&n.original0.refs==1&&n.original1.refs==1&&n.buffer.refs==1&&n.back.refs==1);}
};
void config_tests(){
    CHECK(parse_motion_blur_strength(L"0.1")>0.099f&&parse_motion_blur_strength(L"0.1")<0.101f);
    CHECK(parse_motion_blur_strength(L"")==kPS2ChaseMotionBlur&&parse_motion_blur_strength(L"x")==kPS2ChaseMotionBlur);
    CHECK(parse_motion_blur_strength(L"0")==0.f&&parse_motion_blur_strength(L"-1")==0.f&&parse_motion_blur_strength(L"5")==0.9f);
    // Same trail in time as the PS2 50 Hz frame weight: two 10 ms frames decay like one 20 ms frame.
    CHECK(std::fabs(motion_blur_frame_weight(.195f,.02f)-.195f)<1e-5f);
    const float half=motion_blur_frame_weight(.195f,.01f);CHECK(std::fabs(half*half-.195f)<1e-4f&&half>.43f&&half<.45f);
    CHECK(motion_blur_frame_weight(0.f,.01f)==0.f&&std::fabs(motion_blur_frame_weight(.195f,0.f)-.195f)<1e-5f);
    CHECK(motion_blur_factor(0.195f)==(DWORD(50)<<24));
    PS2MotionBlur b;CHECK(!b.enabled());b.configure(0.195f);CHECK(b.enabled());
}
void pass_tests(){
    {Native n;Original o(n);PS2MotionBlur b;CHECK(b.apply(n,false,false)==S_FALSE&&n.sets==0&&n.copies==0);o.check(n);}
    {Native n;Original o(n);PS2MotionBlur b;b.configure(0.195f);
        CHECK(b.apply(n,false,false)==S_FALSE);CHECK(n.copies==1&&n.draws==0&&n.creates==1&&!std::strcmp(b.status().reason,"history_primed"));o.check(n);
        CHECK(b.apply(n,false,false)==S_OK);CHECK(n.copies==2&&n.draws==1&&n.begins==1&&n.ends==1);
        CHECK(n.drawn_factor==(DWORD(50)<<24)&&n.drawn_src==D3DBLEND_SRCALPHA&&n.drawn_dest==D3DBLEND_INVSRCALPHA&&n.drawn_tex==&n.history&&n.drawn_blend==TRUE);
        CHECK(!b.pending()&&b.status().blended==1);o.check(n);
        CHECK(b.apply(n,false,false,.01f)==S_OK&&n.draws==2&&n.drawn_factor==(DWORD(113)<<24));o.check(n);n.copies=2;n.draws=1;
        CHECK(b.apply(n,false,false,.5f)==S_FALSE&&n.draws==1&&n.copies==3);o.check(n);n.copies=2;
        b.interrupt();CHECK(b.apply(n,false,false)==S_FALSE&&n.draws==1&&n.copies==3);o.check(n);
        n.back.desc.Width=1920;CHECK(b.apply(n,false,false)==S_FALSE&&n.creates==2&&n.draws==1);n.back.desc.Width=1280;
        b.before_reset();CHECK(n.history.refs==0&&n.history.surface.refs==1);}
    {Native n;Original o(n);PS2MotionBlur b;b.configure(.2f);CHECK(b.apply(n,true,false)==S_FALSE&&n.copies==0);CHECK(b.apply(n,false,true)==S_FALSE&&n.copies==0);o.check(n);}
    {Native n;PS2MotionBlur b;b.configure(.2f);n.target=&n.other;CHECK(b.apply(n,false,false)==S_FALSE&&n.copies==0);}
    {Native n;Original o(n);PS2MotionBlur b;b.configure(.2f);n.caps.DestBlendCaps=0;CHECK(FAILED(b.apply(n,false,false))&&n.copies==0);o.check(n);}
    {Native n;Original o(n);PS2MotionBlur b;b.configure(.2f);CHECK(b.apply(n,false,false)==S_FALSE);n.draw_hr=E_FAIL;CHECK(FAILED(b.apply(n,false,false)));CHECK(!b.pending()&&!n.scene);o.check(n);
        n.draw_hr=S_OK;CHECK(b.apply(n,false,false)==S_FALSE);}
    for(int failure=1;failure<=120;++failure){Native n;Original o(n);PS2MotionBlur b;b.configure(.2f);CHECK(b.apply(n,false,false)==S_FALSE);
        n.fail_set=n.sets+failure;const HRESULT hr=b.apply(n,false,false);CHECK(!n.scene);if(FAILED(hr)&&b.pending()){n.fail_set=0;CHECK(b.restore(n)==S_OK);}
        CHECK(!b.pending());o.check(n);}
}
void overlay_tests(){
    {Native n;Original o(n);PS2MotionBlur b;CHECK(b.overlay(n,nullptr,1280,720,512,16,256,false,false)==S_FALSE&&n.draws==0);o.check(n);
        CHECK(b.overlay(n,&n.history,1280,720,512,16,256,true,false)==S_FALSE&&n.draws==0);o.check(n);
        CHECK(b.overlay(n,&n.history,1280,720,512,16,256,false,false)==S_OK&&n.draws==1&&n.drawn_tex==&n.history&&n.drawn_blend==FALSE&&!b.pending());o.check(n);}
    for(int failure=1;failure<=60;++failure){Native n;Original o(n);PS2MotionBlur b;n.fail_set=failure;b.overlay(n,&n.history,1280,720,512,16,256,false,false);
        CHECK(!n.scene);if(b.pending()){n.fail_set=0;CHECK(b.restore(n)==S_OK);}CHECK(!b.pending());o.check(n);}
}
void debug_pattern_tests(){
    std::vector<DWORD> p;reflection_debug_pattern(p);CHECK(p.size()==4096);
    CHECK(p[0]==0xffc80000u&&p[63]==0xffc8c800u&&p[63*64]==0xff0000c8u&&p[4095]==0xff00c8c8u&&p[31*64+31]==0xffc80000u&&p[32*64+32]==0xff00c8c8u);
}
}
int main(){config_tests();pass_tests();overlay_tests();debug_pattern_tests();if(failures)std::cerr<<failures<<" failures\n";return failures?1:0;}
