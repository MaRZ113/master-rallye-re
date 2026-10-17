#include "ps2_output.hpp"
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
struct Drawn { IDirect3DSurface8* target; IDirect3DBaseTexture8* texture; D3DVIEWPORT8 vp; ReflectionCaptureVertex v[4]; bool scene; };
struct Native final:MockDeviceBase {
    std::array<DWORD,256> rs{};std::array<std::array<DWORD,64>,2> tss{};
    std::array<Texture,8> pool;size_t used=0;
    Texture original0,original1;Surface back,depth,other;Buffer buffer;
    IDirect3DSurface8* target=&back;IDirect3DSurface8* z=&depth;
    std::array<IDirect3DBaseTexture8*,2> textures={&original0,&original1};
    IDirect3DVertexBuffer8* stream=&buffer;UINT stride=36;
    D3DVIEWPORT8 viewport{1,2,1270,710,.2f,.8f};DWORD vertex=0x152,pixel=17;D3DCAPS8 caps{};
    int sets=0,fail_set=0,copies=0,creates=0,begins=0,ends=0;bool scene=false;HRESULT copy_hr=S_OK,draw_hr=S_OK;
    std::vector<Drawn> drawn;
    Native(){for(size_t i=0;i<rs.size();++i)rs[i]=DWORD(1000+i);for(size_t s=0;s<2;++s)for(size_t i=0;i<64;++i)tss[s][i]=DWORD(2000+s*64+i);
        caps.MaxTextureWidth=caps.MaxTextureHeight=4096;caps.MaxTextureAspectRatio=16;caps.TextureCaps=D3DPTEXTURECAPS_POW2;
        caps.TextureOpCaps=D3DTEXOPCAPS_MODULATE|D3DTEXOPCAPS_SELECTARG2;caps.SrcBlendCaps=caps.DestBlendCaps=D3DPBLENDCAPS_ONE;
        caps.TextureFilterCaps=D3DPTFILTERCAPS_MAGFLINEAR|D3DPTFILTERCAPS_MINFLINEAR;}
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
    HRESULT STDMETHODCALLTYPE GetDepthStencilSurface(IDirect3DSurface8** p) override{*p=z;if(*p)(*p)->AddRef();return *p?S_OK:D3DERR_NOTFOUND;}
    HRESULT STDMETHODCALLTYPE GetBackBuffer(UINT,D3DBACKBUFFER_TYPE,IDirect3DSurface8** p) override{*p=&back;back.AddRef();return S_OK;}
    HRESULT STDMETHODCALLTYPE SetRenderTarget(IDirect3DSurface8* t,IDirect3DSurface8* d) override{const auto r=w();target=t;z=d;D3DSURFACE_DESC desc{};t->GetDesc(&desc);viewport={0,0,desc.Width,desc.Height,0.f,1.f};return r;}
    HRESULT STDMETHODCALLTYPE GetViewport(D3DVIEWPORT8* p) override{*p=viewport;return S_OK;}
    HRESULT STDMETHODCALLTYPE SetViewport(const D3DVIEWPORT8* p) override{const auto r=w();viewport=*p;return r;}
    HRESULT STDMETHODCALLTYPE GetStreamSource(UINT,IDirect3DVertexBuffer8** p,UINT* v) override{*p=stream;*v=stride;if(*p)(*p)->AddRef();return S_OK;}
    HRESULT STDMETHODCALLTYPE SetStreamSource(UINT,IDirect3DVertexBuffer8* p,UINT v) override{const auto r=w();if(p)p->AddRef();if(stream)stream->Release();stream=p;stride=v;return r;}
    HRESULT STDMETHODCALLTYPE GetDeviceCaps(D3DCAPS8* p) override{*p=caps;return S_OK;}
    HRESULT STDMETHODCALLTYPE BeginScene() override{++begins;CHECK(!scene);scene=true;return S_OK;}
    HRESULT STDMETHODCALLTYPE EndScene() override{++ends;CHECK(scene);scene=false;return S_OK;}
    HRESULT STDMETHODCALLTYPE CreateTexture(UINT wd,UINT h,UINT levels,DWORD usage,D3DFORMAT f,D3DPOOL pool_,IDirect3DTexture8** p) override{
        CHECK(levels==1&&usage==D3DUSAGE_RENDERTARGET&&pool_==D3DPOOL_DEFAULT);++creates;if(used>=pool.size()){*p=nullptr;return E_OUTOFMEMORY;}
        auto& t=pool[used++];t.refs=1;t.surface.refs=1;t.surface.desc.Width=wd;t.surface.desc.Height=h;t.surface.desc.Format=f;*p=&t;return S_OK;}
    HRESULT STDMETHODCALLTYPE CopyRects(IDirect3DSurface8* src,const RECT*,UINT,IDirect3DSurface8* dst,const POINT*) override{CHECK(src==&back&&dst==&pool[0].surface&&!scene);++copies;return copy_hr;}
    HRESULT STDMETHODCALLTYPE DrawPrimitiveUP(D3DPRIMITIVETYPE p,UINT n,const void* data,UINT bytes) override{
        CHECK(p==D3DPT_TRIANGLESTRIP&&n==2&&bytes==28&&z==nullptr);Drawn d{target,textures[0],viewport,{},scene};std::memcpy(d.v,data,sizeof(d.v));drawn.push_back(d);
        if(stream)stream->Release();stream=nullptr;stride=0;return draw_hr;}
};
struct Original {
    std::array<DWORD,256> rs;std::array<std::array<DWORD,64>,2> tss;D3DVIEWPORT8 viewport;
    explicit Original(const Native& n):rs(n.rs),tss(n.tss),viewport(n.viewport){}
    void check(const Native& n) const{CHECK(rs==n.rs&&tss==n.tss);CHECK(std::memcmp(&viewport,&n.viewport,sizeof(viewport))==0);
        CHECK(n.target==&n.back&&n.z==&n.depth&&n.stream==&n.buffer&&n.stride==36&&n.vertex==0x152&&n.pixel==17&&!n.scene);
        CHECK(n.textures[0]==&n.original0&&n.textures[1]==&n.original1&&n.original0.refs==1&&n.original1.refs==1&&n.buffer.refs==1&&n.back.refs==1&&n.depth.refs==1);}
};
bool close_to(float a,float b){return std::abs(a-b)<1e-6f;}

void quad_tests(){
    auto q=ps2_output_quad(640,512,1024,512);CHECK(q.u0==0.f&&q.v0==0.f&&close_to(q.u1,.625f)&&close_to(q.v1,1.f));
    q=ps2_output_quad(640,512,1024,512,.5f);CHECK(close_to(q.v0,.5f/512)&&close_to(q.v1,1.f+.5f/512));
    // Field row r samples exactly between source rows r and r+1: v(r) = (r+1)/512.
    const auto v=ps2_output_vertices(q,512,512);for(int r:{0,100,511}){const float t=(float(r)+.5f)/512.f;CHECK(close_to(v[0].v+(v[2].v-v[0].v)*t,(float(r)+1.f)/512.f));}
    CHECK(v[3].x==511.5f&&v[3].y==511.5f&&v[0].x==-.5f);
}
void pass_tests(){
    {Native n;Original o(n);PS2OutputFilter f;CHECK(f.apply(n,false,false)==S_FALSE);CHECK(n.sets==0&&n.copies==0);o.check(n);}
    // 1280x720: no intermediate; copy, ps2 640x512, field 512x512, back.
    {Native n;Original o(n);PS2OutputFilter f;f.configure(true);
        CHECK(f.apply(n,false,false)==S_OK);CHECK(n.copies==1&&n.creates==3&&n.drawn.size()==3&&n.begins==1&&n.ends==1);
        CHECK(n.drawn[0].target==&n.pool[1].surface&&n.drawn[0].texture==&n.pool[0]&&n.drawn[0].vp.Width==640&&n.drawn[0].vp.Height==512);
        CHECK(n.drawn[1].target==&n.pool[2].surface&&n.drawn[1].texture==&n.pool[1]&&n.drawn[1].vp.Width==512&&n.drawn[1].vp.Height==512);
        CHECK(n.drawn[2].target==&n.back&&n.drawn[2].texture==&n.pool[2]&&n.drawn[2].vp.Width==1280&&n.drawn[2].vp.Height==720);
        CHECK(close_to(n.drawn[0].v[3].u,1280.f/2048.f)&&close_to(n.drawn[0].v[3].v,720.f/1024.f));
        CHECK(close_to(n.drawn[1].v[0].v,.5f/512.f)&&close_to(n.drawn[1].v[3].u,640.f/1024.f));
        for(const auto& d:n.drawn)CHECK(d.scene);
        CHECK(!f.pending()&&f.status().frames==1&&f.status().draws==3);o.check(n);
        CHECK(f.apply(n,false,false)==S_OK&&n.creates==3&&n.drawn.size()==6);o.check(n);
        f.before_reset();for(size_t i=0;i<3;++i)CHECK(n.pool[i].refs==0&&n.pool[i].surface.refs==1);}
    // 1920x1080: intermediate 960x540 first.
    {Native n;n.back.desc.Width=1920;n.back.desc.Height=1080;Original o(n);PS2OutputFilter f;f.configure(true);
        CHECK(f.apply(n,false,false)==S_OK);CHECK(n.creates==4&&n.drawn.size()==4);
        CHECK(n.drawn[0].vp.Width==960&&n.drawn[0].vp.Height==540&&n.drawn[1].vp.Width==640&&n.drawn[2].vp.Width==512&&n.drawn[3].target==&n.back);
        CHECK(n.drawn[1].texture==&n.pool[1]&&close_to(n.drawn[1].v[3].u,960.f/1024.f)&&close_to(n.drawn[1].v[3].v,540.f/1024.f));o.check(n);}
    {Native n;Original o(n);PS2OutputFilter f;f.configure(true);CHECK(f.apply(n,true,false)==S_FALSE&&f.apply(n,false,true)==S_FALSE);CHECK(n.sets==0&&n.copies==0);o.check(n);}
    {Native n;PS2OutputFilter f;f.configure(true);n.target=&n.other;CHECK(f.apply(n,false,false)==S_FALSE&&n.copies==0);n.target=&n.back;}
    {Native n;Original o(n);PS2OutputFilter f;f.configure(true);n.back.desc.Format=D3DFMT_R5G6B5;CHECK(FAILED(f.apply(n,false,false))&&n.creates==0);
        n.back.desc.Format=D3DFMT_X8R8G8B8;CHECK(FAILED(f.apply(n,false,false))&&n.creates==0);o.check(n);}
    {Native n;Original o(n);PS2OutputFilter f;f.configure(true);n.copy_hr=E_FAIL;CHECK(FAILED(f.apply(n,false,false)));CHECK(n.drawn.empty()&&n.sets==0);o.check(n);}
    {Native n;Original o(n);PS2OutputFilter f;f.configure(true);n.draw_hr=E_FAIL;CHECK(FAILED(f.apply(n,false,false)));CHECK(n.drawn.size()==1&&!f.pending()&&!n.scene);o.check(n);}
    for(int failure=1;failure<=200;++failure){Native n;Original o(n);PS2OutputFilter f;f.configure(true);n.fail_set=failure;
        const HRESULT hr=f.apply(n,false,false);CHECK(!n.scene);if(FAILED(hr)&&f.pending()){n.fail_set=0;CHECK(f.restore(n)==S_OK);}
        CHECK(!f.pending());o.check(n);}
    {Native n;n.caps.TextureCaps=0;n.back.desc.MultiSampleType=D3DMULTISAMPLE_4_SAMPLES;Original o(n);PS2OutputFilter f;f.configure(true);
        CHECK(f.apply(n,false,false)==S_OK);o.check(n);}
    {Native n;n.back.desc.MultiSampleType=D3DMULTISAMPLE_4_SAMPLES;PS2OutputFilter f;f.configure(true);CHECK(FAILED(f.apply(n,false,false))&&n.copies==0);}
}
}
int main(){quad_tests();pass_tests();if(failures)std::cerr<<failures<<" failures\n";return failures?1:0;}
