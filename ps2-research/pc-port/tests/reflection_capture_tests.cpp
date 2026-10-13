#include "reflection_capture.hpp"
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
    ULONG refs=1;D3DSURFACE_DESC desc{};bool null_identity=false;
    Surface(UINT w=1280,UINT h=720){desc.Width=w;desc.Height=h;desc.Format=D3DFMT_X8R8G8B8;desc.Type=D3DRTYPE_SURFACE;desc.MultiSampleType=D3DMULTISAMPLE_NONE;}
    HRESULT STDMETHODCALLTYPE QueryInterface(REFIID,void** p) override{if(!p)return E_POINTER;if(null_identity){*p=nullptr;return S_OK;}*p=this;AddRef();return S_OK;}
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
    bool null_surface=false;
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
    HRESULT STDMETHODCALLTYPE GetSurfaceLevel(UINT,IDirect3DSurface8** p) override{if(null_surface){*p=nullptr;return S_OK;}*p=&surface;surface.AddRef();return S_OK;}
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
    std::array<DWORD,256> rs{};
    std::array<std::array<DWORD,64>,2> tss{};
    Texture original0,original1,env,copied,mixed;
    Surface back,depth,other;
    Buffer buffer;
    IDirect3DSurface8* target=&back;
    IDirect3DSurface8* z=&depth;
    std::array<IDirect3DBaseTexture8*,2> textures={&original0,&original1};
    IDirect3DVertexBuffer8* stream=&buffer;
    UINT stride=36;
    D3DVIEWPORT8 viewport{1,2,1270,710,.2f,.8f};
    DWORD vertex=0x152,pixel=17;
    D3DCAPS8 caps{};
    int gets=0,sets=0,fail_get=0,fail_set=0,fail_set_again=0;
    int copies=0,draws=0,creates=0,callback_writes=0;
    int successful_creates=0;
    int null_create=0;
    HRESULT copy_hr=S_OK,draw_hr=S_OK;
    bool mutate_failure=true;
    bool fail_16bit=false;
    Native(){for(size_t i=0;i<rs.size();++i)rs[i]=static_cast<DWORD>(1000+i);
        for(size_t s=0;s<2;++s)for(size_t i=0;i<tss[s].size();++i)tss[s][i]=static_cast<DWORD>(2000+s*64+i);
        caps.MaxTextureWidth=caps.MaxTextureHeight=4096;caps.MaxTextureAspectRatio=16;
        caps.TextureCaps=D3DPTEXTURECAPS_POW2;caps.TextureOpCaps=D3DTEXOPCAPS_MODULATE|D3DTEXOPCAPS_SELECTARG2;
        caps.SrcBlendCaps=caps.DestBlendCaps=D3DPBLENDCAPS_ONE;
        caps.TextureFilterCaps=D3DPTFILTERCAPS_MAGFLINEAR|D3DPTFILTERCAPS_MINFLINEAR;}
    bool read(){return ++gets!=fail_get;}
    HRESULT write(){++sets;return sets==fail_set||sets==fail_set_again?D3DERR_INVALIDCALL:S_OK;}
    static void callback(void* ctx,uint32_t,const Args&,HRESULT) noexcept {++static_cast<Native*>(ctx)->callback_writes;}
    HRESULT STDMETHODCALLTYPE GetRenderState(D3DRENDERSTATETYPE k,DWORD* p) override{if(!read())return E_FAIL;*p=rs[k];return S_OK;}
    HRESULT STDMETHODCALLTYPE SetRenderState(D3DRENDERSTATETYPE k,DWORD v) override{const auto hr=write();if(SUCCEEDED(hr)||mutate_failure)rs[k]=v;return hr;}
    HRESULT STDMETHODCALLTYPE GetTextureStageState(DWORD s,D3DTEXTURESTAGESTATETYPE k,DWORD* p) override{if(!read())return E_FAIL;*p=tss[s][k];return S_OK;}
    HRESULT STDMETHODCALLTYPE SetTextureStageState(DWORD s,D3DTEXTURESTAGESTATETYPE k,DWORD v) override{const auto hr=write();if(SUCCEEDED(hr)||mutate_failure)tss[s][k]=v;return hr;}
    HRESULT STDMETHODCALLTYPE GetVertexShader(DWORD* p) override{if(!read())return E_FAIL;*p=vertex;return S_OK;}
    HRESULT STDMETHODCALLTYPE SetVertexShader(DWORD v) override{const auto hr=write();if(SUCCEEDED(hr)||mutate_failure)vertex=v;return hr;}
    HRESULT STDMETHODCALLTYPE GetPixelShader(DWORD* p) override{if(!read())return E_FAIL;*p=pixel;return S_OK;}
    HRESULT STDMETHODCALLTYPE SetPixelShader(DWORD v) override{const auto hr=write();if(SUCCEEDED(hr)||mutate_failure)pixel=v;return hr;}
    HRESULT STDMETHODCALLTYPE GetTexture(DWORD s,IDirect3DBaseTexture8** p) override{if(!read())return E_FAIL;*p=textures[s];if(*p)(*p)->AddRef();return S_OK;}
    HRESULT STDMETHODCALLTYPE SetTexture(DWORD s,IDirect3DBaseTexture8* p) override{const auto hr=write();if(SUCCEEDED(hr)||mutate_failure){if(p)p->AddRef();if(textures[s])textures[s]->Release();textures[s]=p;}return hr;}
    HRESULT STDMETHODCALLTYPE GetRenderTarget(IDirect3DSurface8** p) override{if(!read())return E_FAIL;*p=target;if(*p)(*p)->AddRef();return S_OK;}
    HRESULT STDMETHODCALLTYPE GetDepthStencilSurface(IDirect3DSurface8** p) override{if(!read())return E_FAIL;*p=z;if(*p)(*p)->AddRef();return *p?S_OK:D3DERR_NOTFOUND;}
    HRESULT STDMETHODCALLTYPE GetBackBuffer(UINT n,D3DBACKBUFFER_TYPE,IDirect3DSurface8** p) override{CHECK(n==0);if(!read())return E_FAIL;*p=&back;back.AddRef();return S_OK;}
    HRESULT STDMETHODCALLTYPE SetRenderTarget(IDirect3DSurface8* t,IDirect3DSurface8* d) override{const auto hr=write();if(SUCCEEDED(hr)||mutate_failure){target=t;z=d;D3DSURFACE_DESC desc{};t->GetDesc(&desc);viewport={0,0,desc.Width,desc.Height,0.f,1.f};}return hr;}
    HRESULT STDMETHODCALLTYPE GetViewport(D3DVIEWPORT8* p) override{if(!read())return E_FAIL;*p=viewport;return S_OK;}
    HRESULT STDMETHODCALLTYPE SetViewport(const D3DVIEWPORT8* p) override{const auto hr=write();if(SUCCEEDED(hr)||mutate_failure)viewport=*p;return hr;}
    HRESULT STDMETHODCALLTYPE GetStreamSource(UINT n,IDirect3DVertexBuffer8** p,UINT* v) override{CHECK(n==0);if(!read())return E_FAIL;*p=stream;*v=stride;if(*p)(*p)->AddRef();return S_OK;}
    HRESULT STDMETHODCALLTYPE SetStreamSource(UINT n,IDirect3DVertexBuffer8* p,UINT v) override{CHECK(n==0);const auto hr=write();if(SUCCEEDED(hr)||mutate_failure){if(p)p->AddRef();if(stream)stream->Release();stream=p;stride=v;}return hr;}
    HRESULT STDMETHODCALLTYPE GetDeviceCaps(D3DCAPS8* p) override{*p=caps;return S_OK;}
    HRESULT STDMETHODCALLTYPE CreateTexture(UINT w,UINT h,UINT levels,DWORD usage,D3DFORMAT format,D3DPOOL pool,IDirect3DTexture8** p) override{
        if(format==D3DFMT_A1R5G5B5&&fail_16bit){++creates;*p=nullptr;return D3DERR_NOTAVAILABLE;}
        CHECK(levels==1&&usage==D3DUSAGE_RENDERTARGET&&pool==D3DPOOL_DEFAULT);++creates;
        if(creates==null_create){*p=nullptr;return S_OK;}Texture* value=successful_creates++%2==0?&copied:&mixed;
        value->refs=1;value->surface.desc.Width=w;value->surface.desc.Height=h;value->surface.desc.Format=format;*p=value;return S_OK;}
    HRESULT STDMETHODCALLTYPE CopyRects(IDirect3DSurface8* src,const RECT* rect,UINT n,IDirect3DSurface8* dst,const POINT* point) override{
        CHECK(src==&back&&dst==&copied.surface&&n==1&&rect&&point);++copies;return copy_hr;}
    HRESULT STDMETHODCALLTYPE DrawPrimitiveUP(D3DPRIMITIVETYPE p,UINT n,const void* data,UINT bytes) override{
        CHECK(p==D3DPT_TRIANGLESTRIP&&n==2&&bytes==28&&target==&mixed.surface&&z==nullptr&&data);++draws;
        if(stream)stream->Release();stream=nullptr;stride=0;return draw_hr;}
};
struct Original {
    std::array<DWORD,256> rs;
    std::array<std::array<DWORD,64>,2> tss;
    D3DVIEWPORT8 viewport;
    Original(const Native& n):rs(n.rs),tss(n.tss),viewport(n.viewport){}
    void check(const Native& n) const{CHECK(rs==n.rs&&tss==n.tss);CHECK(std::memcmp(&viewport,&n.viewport,sizeof(viewport))==0);
        CHECK(n.target==&n.back&&n.z==&n.depth&&n.stream==&n.buffer&&n.stride==36&&n.vertex==0x152&&n.pixel==17);
        CHECK(n.textures[0]==&n.original0&&n.textures[1]==&n.original1);
        CHECK(n.original0.refs==1&&n.original1.refs==1&&n.buffer.refs==1&&n.back.refs==1&&n.depth.refs==1);}
};
void layout_tests(){D3DCAPS8 caps{};caps.MaxTextureWidth=caps.MaxTextureHeight=4096;caps.TextureCaps=D3DPTEXTURECAPS_POW2;
    ReflectionCaptureLayout l{};CHECK(reflection_capture_layout(1920,1080,caps,l));CHECK(l.texture_width==2048&&l.texture_height==2048&&l.bytes==16777216);
    CHECK(!reflection_capture_layout(3840,2160,caps,l));CHECK(!reflection_capture_layout(0,100,caps,l));
    caps.TextureCaps=0;CHECK(reflection_capture_layout(1280,720,caps,l));CHECK(l.texture_width==1280&&l.texture_height==720);
    caps.TextureCaps=D3DPTEXTURECAPS_SQUAREONLY;CHECK(reflection_capture_layout(1280,720,caps,l));CHECK(l.texture_width==1280&&l.texture_height==1280);
    caps.MaxTextureWidth=32;CHECK(!reflection_capture_layout(1280,720,caps,l));
    const auto q=reflection_capture_quad(.75f,.5f,true,0xff606060);CHECK(q[0].v==.5f&&q[2].v==0.f&&q[1].u==.75f&&q[0].x==-.5f&&q[3].y==63.5f);
    CHECK(std::abs(96.f/255.f-48.f/128.f)<.002f);CHECK(96.f/255.f!=48.f/128.f);
}
void transaction_tests(){
    {Native n;Original original(n);ReflectionCaptureTransaction t;t.set_writer(&n,&Native::callback);CHECK(t.capture(n)==S_OK);
        CHECK(t.apply(n,&n.mixed.surface,&n.env)==S_OK);CHECK(t.framebuffer_pass(n,&n.copied)==S_OK);
        t.mark_up();CHECK(t.sync_up_stream(n)==S_OK);CHECK(t.pending());CHECK(t.restore(n)==S_OK);CHECK(!t.pending());original.check(n);CHECK(n.callback_writes==n.sets);}
    for(int failure=1;failure<=45;++failure){Native n;Original original(n);ReflectionCaptureTransaction t;CHECK(t.capture(n)==S_OK);
        n.fail_set=failure;const HRESULT hr=t.apply(n,&n.mixed.surface,&n.env);if(FAILED(hr))CHECK(t.pending());
        n.fail_set=0;CHECK(t.restore(n)==S_OK);original.check(n);}
    for(int failure=1;failure<=46;++failure){Native n;Original original(n);ReflectionCaptureTransaction t;CHECK(t.capture(n)==S_OK);
        CHECK(t.apply(n,&n.mixed.surface,&n.env)==S_OK);t.mark_up();CHECK(t.sync_up_stream(n)==S_OK);
        n.fail_set=n.sets+failure;const HRESULT hr=t.restore(n);
        if(FAILED(hr))CHECK(t.pending());n.fail_set=0;CHECK(t.restore(n)==S_OK);original.check(n);}
    for(int failure=1;failure<=46;++failure){Native n;Original original(n);ReflectionCaptureTransaction t;n.fail_get=failure;
        const auto hr=t.capture(n);if(FAILED(hr))CHECK(!t.pending());t.release();original.check(n);CHECK(n.sets==0);}
}
void gpu_tests(){
    {Native n;Original original(n);MixedReflectionCapture c;c.prefer_16bit(true);
        CHECK(c.capture(n,&n.env,1,false)==S_OK);CHECK(c.last_status().target_format==D3DFMT_A1R5G5B5);
        CHECK(!c.last_status().precision_fallback);original.check(n);c.release();
        CHECK(c.capture(n,&n.env,2,false)==S_OK);CHECK(c.last_status().target_format==D3DFMT_A1R5G5B5);original.check(n);}
    {Native n;Original original(n);n.fail_16bit=true;MixedReflectionCapture c;c.prefer_16bit(true);
        CHECK(c.capture(n,&n.env,1,false)==S_OK);CHECK(c.last_status().target_format==D3DFMT_A8R8G8B8);
        CHECK(c.last_status().precision_fallback&&n.creates==3);original.check(n);}
    {Native n;Original original(n);MixedReflectionCapture c;c.set_writer(&n,&Native::callback);
        CHECK(c.capture(n,&n.env,10,false)==S_OK);CHECK(c.ready_texture(10)==&n.mixed);CHECK(c.ready_texture(11)==nullptr);
        CHECK(n.copies==1&&n.draws==2&&n.creates==2&&c.last_status().private_draws==2);original.check(n);
        CHECK(c.capture(n,&n.env,10,false)==S_OK);CHECK(n.copies==1&&n.draws==2);
        CHECK(c.capture(n,&n.env,11,false)==S_OK);CHECK(n.copies==2&&n.draws==4&&n.creates==2);original.check(n);
        c.release();CHECK(n.copied.refs==0&&n.mixed.refs==0&&n.copied.surface.refs==1&&n.mixed.surface.refs==1);CHECK(c.ready_texture(11)==nullptr);}
    {Native n;Original original(n);MixedReflectionCapture c;n.copy_hr=D3DERR_INVALIDCALL;
        CHECK(FAILED(c.capture(n,&n.env,10,false)));CHECK(!c.ready_texture(10)&&n.draws==0&&n.copies==1&&n.sets==0);
        CHECK(FAILED(c.capture(n,&n.env,10,false)));CHECK(n.copies==1);original.check(n);}
    {Native n;Original original(n);MixedReflectionCapture c;n.draw_hr=E_FAIL;
        CHECK(FAILED(c.capture(n,&n.env,10,false)));CHECK(!c.ready_texture(10)&&n.draws==1);CHECK(!c.pending());original.check(n);}
    {Native n;Original original(n);MixedReflectionCapture c;n.fail_set=1;
        CHECK(FAILED(c.capture(n,&n.env,10,false)));CHECK(n.draws==0&&!c.pending());original.check(n);}
    {Native n;Original original(n);MixedReflectionCapture c;n.fail_set=1;n.fail_set_again=2;
        CHECK(FAILED(c.capture(n,&n.env,10,false)));CHECK(c.pending()&&!c.ready_texture(10));
        n.fail_set=n.fail_set_again=0;CHECK(c.repair(n)==S_OK);CHECK(!c.pending());original.check(n);}
    {Native n;MixedReflectionCapture c;n.back.desc.MultiSampleType=D3DMULTISAMPLE_2_SAMPLES;
        CHECK(FAILED(c.capture(n,&n.env,1,false)));CHECK(n.copies==0&&n.draws==0&&n.creates==0);}
    {Native n;MixedReflectionCapture c;n.back.desc.Format=D3DFMT_R5G6B5;
        CHECK(FAILED(c.capture(n,&n.env,1,false)));CHECK(n.copies==0&&n.creates==0);}
    {Native n;MixedReflectionCapture c;n.target=&n.other;
        CHECK(FAILED(c.capture(n,&n.env,1,false)));CHECK(n.copies==0&&n.creates==0);}
    {Native n;MixedReflectionCapture c;n.target=&n.other;n.other.null_identity=n.back.null_identity=true;
        CHECK(FAILED(c.capture(n,&n.env,1,false)));CHECK(n.copies==0&&n.creates==0);}
    {Native n;MixedReflectionCapture c;CHECK(FAILED(c.capture(n,&n.env,1,true)));CHECK(n.gets==0&&n.copies==0&&n.creates==0);}
    {Native n;MixedReflectionCapture c;CHECK(FAILED(c.capture(n,nullptr,1,false)));CHECK(n.gets==0&&n.copies==0&&n.creates==0);}
    for(int creation=1;creation<=2;++creation){Native n;MixedReflectionCapture c;n.null_create=creation;
        CHECK(FAILED(c.capture(n,&n.env,1,false)));CHECK(!c.ready_texture(1)&&n.copies==0&&n.draws==0);}
    {Native n;MixedReflectionCapture c;n.copied.null_surface=true;CHECK(FAILED(c.capture(n,&n.env,1,false)));
        CHECK(!c.ready_texture(1)&&n.copies==0&&n.draws==0&&n.copied.refs==0);}
    {Native n;MixedReflectionCapture c;n.mixed.null_surface=true;CHECK(FAILED(c.capture(n,&n.env,1,false)));
        CHECK(!c.ready_texture(1)&&n.copies==0&&n.draws==0&&n.copied.refs==0&&n.mixed.refs==0);}
}
}
int main(){layout_tests();transaction_tests();gpu_tests();if(failures)std::cerr<<failures<<" failures\n";return failures?1:0;}
