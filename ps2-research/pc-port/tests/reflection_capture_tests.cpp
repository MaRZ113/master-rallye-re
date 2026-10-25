#include "reflection_capture.hpp"
#include "reflection_inspect.hpp"
#include <array>
#include <cmath>
#include <cstring>
#include <iostream>
#include <memory>
#include <vector>

using namespace gfx2;
using namespace gfx2::ps2port;
int failures=0;
#define CHECK(x) do{if(!(x)){std::cerr<<"FAIL "<<__LINE__<<": "#x"\n";++failures;}}while(0)
#include "mock_interfaces.hpp"

namespace {
struct Surface:IDirect3DSurface8 {
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
struct ImageSurface final:Surface {
    std::vector<uint8_t> bits;UINT pitch=0;
    ImageSurface(UINT w,UINT h,D3DFORMAT format):Surface(w,h){desc.Format=format;desc.Type=D3DRTYPE_SURFACE;pitch=w*((format==D3DFMT_A1R5G5B5||format==D3DFMT_R5G6B5)?2u:4u);bits.assign(size_t(pitch)*h,0);}
    HRESULT STDMETHODCALLTYPE LockRect(D3DLOCKED_RECT* r,const RECT*,DWORD) override{r->Pitch=INT(pitch);r->pBits=bits.data();return S_OK;}
    HRESULT STDMETHODCALLTYPE UnlockRect() override{return S_OK;}
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
    Texture original0,original1,env,copied,mixed,late,ps2frame;
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
    // COURSE-RENDER-FIX1 readbacks: image surfaces filled from a synthetic frame (empty ground = bottom third black).
    std::vector<std::unique_ptr<ImageSurface>> images;
    bool ground_black=false;int readbacks=0,image_creates=0,mixed64_in_life=0;
    HRESULT readback_hr=S_OK,image_create_hr=S_OK;
    IDirect3DSurface8* mixed_target=nullptr;
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
        if(creates==null_create){*p=nullptr;return S_OK;}
        Texture* value=&copied;++successful_creates;
        if(w==640&&h==448)value=&ps2frame;
        else if(w==64&&h==64)value=(mixed64_in_life++==0)?&mixed:&late;
        else mixed64_in_life=0;
        value->refs=1;value->surface.desc.Width=w;value->surface.desc.Height=h;value->surface.desc.Format=format;*p=value;return S_OK;}
    HRESULT STDMETHODCALLTYPE CreateImageSurface(UINT w,UINT h,D3DFORMAT format,IDirect3DSurface8** p) override{
        ++image_creates;if(FAILED(image_create_hr)){*p=nullptr;return image_create_hr;}
        images.push_back(std::make_unique<ImageSurface>(w,h,format));*p=images.back().get();return S_OK;}
    void fill(ImageSurface& image,IDirect3DSurface8* src,const RECT& rect){
        const UINT w=UINT(rect.right-rect.left),h=UINT(rect.bottom-rect.top);
        for(UINT y=0;y<h;++y)for(UINT x=0;x<w;++x){
            uint8_t r,g,b;
            if(src==&ps2frame.surface){const bool ground=UINT(rect.top)+y>=298;r=g=b=ground?(ground_black?0:90):200;}
            else if(src==&copied.surface){r=g=b=100;}
            else{r=uint8_t(x*4);g=uint8_t(y*4);b=77;}
            if(image.desc.Format==D3DFMT_A1R5G5B5){const uint16_t v=uint16_t(0x8000|((r>>3)<<10)|((g>>3)<<5)|(b>>3));std::memcpy(image.bits.data()+size_t(y)*image.pitch+x*2,&v,2);}
            else{const uint32_t v=0xff000000u|(uint32_t(r)<<16)|(uint32_t(g)<<8)|b;std::memcpy(image.bits.data()+size_t(y)*image.pitch+x*4,&v,4);}
        }
    }
    HRESULT STDMETHODCALLTYPE CopyRects(IDirect3DSurface8* src,const RECT* rect,UINT n,IDirect3DSurface8* dst,const POINT* point) override{
        for(auto& image:images)if(dst==image.get()){
            ++readbacks;CHECK(n==1&&rect&&point&&point->x==0&&point->y==0);
            if(SUCCEEDED(readback_hr))fill(*image,src,*rect);return readback_hr;}
        CHECK(src==&back&&dst==&copied.surface);
        if(back.desc.MultiSampleType==D3DMULTISAMPLE_NONE)CHECK(n==1&&rect&&point);
        else {CHECK(n==0&&!rect&&!point);CHECK(dst->GetDesc(&copied.surface.desc)==S_OK);
            CHECK(copied.surface.desc.Width==back.desc.Width&&copied.surface.desc.Height==back.desc.Height);
            CHECK(copied.surface.desc.Format==back.desc.Format&&copied.surface.desc.MultiSampleType==D3DMULTISAMPLE_NONE);}
        ++copies;return copy_hr;}
    HRESULT STDMETHODCALLTYPE DrawPrimitiveUP(D3DPRIMITIVETYPE p,UINT n,const void* data,UINT bytes) override{
        CHECK(p==D3DPT_TRIANGLESTRIP&&n==2&&bytes==28&&z==nullptr&&data);CHECK(draws%3==0?target==&ps2frame.surface&&viewport.Width==640&&viewport.Height==448:target==(mixed_target?mixed_target:&mixed.surface)&&viewport.Width==64&&viewport.Height==64);++draws;
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
        CHECK(c.last_status().precision_fallback&&n.creates==4);original.check(n);}
    {Native n;Original original(n);MixedReflectionCapture c;c.set_writer(&n,&Native::callback);
        CHECK(c.capture(n,&n.env,10,false)==S_OK);CHECK(c.ready_texture(10)==&n.mixed);CHECK(c.ready_texture(11)==nullptr);
        CHECK(n.copies==1&&n.draws==3&&n.creates==3&&c.last_status().private_draws==3&&n.ps2frame.surface.desc.Width==640&&n.ps2frame.surface.desc.Height==448);original.check(n);
        CHECK(c.capture(n,&n.env,10,false)==S_OK);CHECK(n.copies==1&&n.draws==3);
        CHECK(c.capture(n,&n.env,11,false)==S_OK);CHECK(n.copies==2&&n.draws==6&&n.creates==3);original.check(n);
        c.release();CHECK(n.copied.refs==0&&n.mixed.refs==0&&n.ps2frame.refs==0&&n.copied.surface.refs==1&&n.mixed.surface.refs==1&&n.ps2frame.surface.refs==1);CHECK(c.ready_texture(11)==nullptr);}
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
    for(auto samples:{D3DMULTISAMPLE_2_SAMPLES,D3DMULTISAMPLE_4_SAMPLES})for(bool precision:{false,true}){
        Native n;n.caps.TextureCaps=0;n.back.desc.MultiSampleType=samples;Original original(n);
        MixedReflectionCapture c;c.prefer_16bit(precision);
        CHECK(c.capture(n,&n.env,1,false)==S_OK);CHECK(n.copies==1&&n.draws==3);
        CHECK(c.last_status().source_multisample==samples);
        CHECK(c.last_status().target_format==(precision?D3DFMT_A1R5G5B5:D3DFMT_A8R8G8B8));original.check(n);
        CHECK(c.capture(n,&n.env,1,false)==S_OK&&n.copies==1);
        c.release();CHECK(c.capture(n,&n.env,2,false)==S_OK);original.check(n);
    }
    {Native n;n.caps.TextureCaps=0;n.back.desc.MultiSampleType=D3DMULTISAMPLE_4_SAMPLES;
        n.copy_hr=D3DERR_INVALIDCALL;Original original(n);MixedReflectionCapture c;
        CHECK(FAILED(c.capture(n,&n.env,1,false))&&n.copies==1&&n.draws==0&&n.sets==0);
        CHECK(FAILED(c.capture(n,&n.env,2,false))&&n.copies==1);original.check(n);
        c.release();n.copy_hr=S_OK;CHECK(c.capture(n,&n.env,3,false)==S_OK);original.check(n);
    }
    {Native n;MixedReflectionCapture c;n.back.desc.MultiSampleType=D3DMULTISAMPLE_2_SAMPLES;
        CHECK(FAILED(c.capture(n,&n.env,1,false)));CHECK(n.copies==0&&n.draws==0&&n.creates==0);}
    {Native n;MixedReflectionCapture c;n.back.desc.Format=D3DFMT_R5G6B5;
        CHECK(FAILED(c.capture(n,&n.env,1,false)));CHECK(n.copies==0&&n.creates==0);}
    {Native n;MixedReflectionCapture c;n.target=&n.other;
        CHECK(FAILED(c.capture(n,&n.env,1,false)));CHECK(n.copies==0&&n.creates==0);}
    {Native n;MixedReflectionCapture c;n.target=&n.other;n.other.null_identity=n.back.null_identity=true;
        CHECK(FAILED(c.capture(n,&n.env,1,false)));CHECK(n.copies==0&&n.creates==0);}
    // ReflectionDebug: the target holds the static (pattern) pass only, no framebuffer term.
    {Native n;Original original(n);MixedReflectionCapture c;c.debug_pattern(true);CHECK(c.capture(n,&n.env,1,false)==S_OK);
        CHECK(n.copies==1&&n.draws==2&&c.last_status().private_draws==2);original.check(n);}
    {Native n;MixedReflectionCapture c;CHECK(FAILED(c.capture(n,&n.env,1,true)));CHECK(n.gets==0&&n.copies==0&&n.creates==0);}
    {Native n;MixedReflectionCapture c;CHECK(FAILED(c.capture(n,nullptr,1,false)));CHECK(n.gets==0&&n.copies==0&&n.creates==0);}
    for(int creation=1;creation<=3;++creation){Native n;MixedReflectionCapture c;n.null_create=creation;
        CHECK(FAILED(c.capture(n,&n.env,1,false)));CHECK(!c.ready_texture(1)&&n.copies==0&&n.draws==0);}
    {Native n;MixedReflectionCapture c;n.copied.null_surface=true;CHECK(FAILED(c.capture(n,&n.env,1,false)));
        CHECK(!c.ready_texture(1)&&n.copies==0&&n.draws==0&&n.copied.refs==0);}
    {Native n;MixedReflectionCapture c;n.mixed.null_surface=true;CHECK(FAILED(c.capture(n,&n.env,1,false)));
        CHECK(!c.ready_texture(1)&&n.copies==0&&n.draws==0&&n.copied.refs==0&&n.mixed.refs==0);}
}
}
// COURSE-RENDER-FIX1: end-of-world capture for the next frame, the per-race timing probe and the stage report.
void timing_gpu_tests(){
    using ps2diag::CaptureTiming;
    {   // Late capture: valid for the NEXT frame only, in its own target; the in-frame capture of that frame does no work.
        Native n;Original original(n);MixedReflectionCapture c;n.mixed_target=&n.late.surface;
        CHECK(c.capture_late(n,&n.env,10,false)==S_OK);
        CHECK(c.ready_texture(11)==&n.late&&!c.ready_texture(10)&&c.last_status().late&&c.last_status().frame==11);
        CHECK(n.copies==1&&n.draws==3&&n.creates==4&&c.late_allocated()&&c.counters().late_ok==1&&c.counters().ok==1);original.check(n);
        CHECK(c.capture(n,&n.env,11,false)==S_OK&&n.copies==1&&n.draws==3);
        CHECK(c.capture_late(n,&n.env,10,false)==S_OK&&n.copies==1);                 // already prepared
        CHECK(c.last_texture()==&n.late&&c.served_total()>=1);
        // The next frame prepares frame 12 (target alternates through the same late slot) and keeps working.
        CHECK(c.capture_late(n,&n.env,11,false)==S_OK&&c.ready_texture(12)==&n.late&&n.copies==2&&n.draws==6);original.check(n);
        // A frame without a prepared target falls back to the original in-frame capture into the mixed target.
        n.mixed_target=&n.mixed.surface;
        CHECK(c.capture(n,&n.env,20,false)==S_OK&&c.ready_texture(20)==&n.mixed&&n.copies==3);original.check(n);
        CHECK(c.last_texture()==&n.mixed);
        c.release();CHECK(n.late.refs==0&&n.mixed.refs==0&&n.copied.refs==0&&!c.ready_texture(12)&&!c.late_allocated());
    }
    {   // Late capture failures never leak state and never poison the in-frame path.
        Native n;Original original(n);MixedReflectionCapture c;
        n.back.desc.Format=D3DFMT_R5G6B5;CHECK(FAILED(c.capture_late(n,&n.env,1,false)));original.check(n);
        Native m;Original original_m(m);MixedReflectionCapture d;
        CHECK(FAILED(d.capture_late(m,&m.env,1,true))&&m.copies==0&&m.creates==0);          // state-block recording
        CHECK(FAILED(d.capture_late(m,nullptr,2,false))&&m.copies==0);
        m.copy_hr=D3DERR_INVALIDCALL;CHECK(FAILED(d.capture_late(m,&m.env,3,false))&&!d.ready_texture(4)&&m.draws==0);original_m.check(m);
        m.copy_hr=S_OK;m.mixed_target=&m.late.surface;CHECK(d.capture_late(m,&m.env,4,false)==S_OK&&d.ready_texture(5));original_m.check(m);
        Native k;MixedReflectionCapture e;k.null_create=4;                                 // the late target cannot be created
        CHECK(FAILED(e.capture_late(k,&k.env,1,false))&&!e.ready_texture(2)&&e.counters().failed==1);
        CHECK(FAILED(e.capture_late(k,&k.env,2,false))&&k.copies==0&&e.counters().failed==1);   // latched: no new attempt per frame
        k.mixed_target=&k.mixed.surface;CHECK(e.capture(k,&k.env,3,false)==S_OK&&e.ready_texture(3)==&k.mixed);
    }
    {   // InFrame (default) never reads a surface back, whatever the number of captures.
        Native n;MixedReflectionCapture c;c.set_race(3);
        for(uint64_t frame=1;frame<=400;++frame)CHECK(c.capture(n,&n.env,frame,false)==S_OK);
        CHECK(n.readbacks==0&&n.image_creates==0&&!c.late_wanted());
    }
    {   // Auto, empty ground (the converted-course draw order): three probes latch the race to the end-of-world capture.
        DeviceInspector inspector;Native n;Original original(n);MixedReflectionCapture c;c.set_inspector(&inspector);c.configure(CaptureTiming::Auto,false);n.ground_black=true;
        c.set_race(7);uint64_t frame=0;
        for(int i=0;i<60&&!c.late_wanted();++i)CHECK(c.capture(n,&n.env,++frame,false)==S_OK);
        CHECK(c.late_wanted()&&c.counters().probes==3&&c.counters().probes_incomplete==3&&c.counters().late_latched_races==1);
        CHECK(n.readbacks==3&&n.image_creates==1);original.check(n);
        c.set_race(8);CHECK(!c.late_wanted());                                           // a new race starts in-frame again
        n.ground_black=false;for(int i=0;i<310;++i)CHECK(c.capture(n,&n.env,++frame,false)==S_OK);
        CHECK(!c.late_wanted()&&c.decision().decided()&&c.counters().probes==6&&c.counters().late_latched_races==1);original.check(n);
    }
    {   // Probe readback failures leave the capture intact and the decision open.
        DeviceInspector inspector;Native n;Original original(n);MixedReflectionCapture c;c.set_inspector(&inspector);c.configure(CaptureTiming::Auto,false);c.set_race(1);
        n.readback_hr=D3DERR_INVALIDCALL;CHECK(c.capture(n,&n.env,1,false)==S_OK&&c.ready_texture(1)&&c.counters().readback_failed==1&&c.counters().probes==0);
        n.readback_hr=S_OK;n.image_create_hr=E_OUTOFMEMORY;CHECK(c.capture(n,&n.env,2,false)==S_OK);original.check(n);
        DeviceInspector inspector_m;Native m;MixedReflectionCapture d;d.set_inspector(&inspector_m);d.configure(CaptureTiming::Auto,false);m.caps.TextureCaps=0;
        d.set_race(1);m.image_create_hr=E_OUTOFMEMORY;CHECK(d.capture(m,&m.env,1,false)==S_OK&&d.counters().readback_failed==1&&!d.late_wanted());
    }
    {   // A failing MSAA resolve is not retried every frame, but a new race gets one fresh attempt (no session-wide latch).
        Native n;n.caps.TextureCaps=0;n.back.desc.MultiSampleType=D3DMULTISAMPLE_4_SAMPLES;n.copy_hr=D3DERR_INVALIDCALL;Original original(n);
        MixedReflectionCapture c;c.set_race(11);
        CHECK(FAILED(c.capture(n,&n.env,1,false))&&n.copies==1&&c.permanently_unsupported());
        CHECK(FAILED(c.capture(n,&n.env,2,false))&&n.copies==1);
        c.set_race(11);CHECK(c.permanently_unsupported());                                  // same race: still latched
        n.copy_hr=S_OK;c.set_race(12);CHECK(!c.permanently_unsupported()&&c.counters().resolve_latch_cleared==1);
        CHECK(c.capture(n,&n.env,3,false)==S_OK&&c.ready_texture(3));original.check(n);
        // Other unsupported reasons are caps/format/size facts and stay latched across races.
        Native m;MixedReflectionCapture d;m.back.desc.Format=D3DFMT_R5G6B5;d.set_race(1);
        CHECK(FAILED(d.capture(m,&m.env,1,false))&&d.permanently_unsupported());d.set_race(2);CHECK(d.permanently_unsupported());
    }
    {   // Without an inspector nothing is read back: the probe stays undecided, the failure is counted, the capture works.
        Native n;Original original(n);MixedReflectionCapture c;c.configure(CaptureTiming::Auto,true);c.set_race(3);
        CHECK(c.capture(n,&n.env,1,false)==S_OK&&c.ready_texture(1)&&n.readbacks==0&&n.image_creates==0&&c.counters().readback_failed==1);original.check(n);
        // The inspector's surfaces go back with the capture (Reset/shutdown).
        DeviceInspector inspector;Native m;MixedReflectionCapture d;d.set_inspector(&inspector);d.configure(CaptureTiming::Auto,false);d.set_race(3);
        CHECK(d.capture(m,&m.env,1,false)==S_OK&&m.image_creates==1&&m.images[0]->refs==1);d.release();CHECK(m.images[0]->refs==0);
    }
    {   // Late timing forced: late from the first frame of a race, none outside a race.
        Native n;MixedReflectionCapture c;c.configure(CaptureTiming::Late,false);
        CHECK(!c.late_wanted());c.set_race(2);CHECK(c.late_wanted());c.set_race(0);CHECK(!c.late_wanted());
    }
    {   // Stage report: every stage, once per scheduled capture, all state restored.
        DeviceInspector inspector;Native n;Original original(n);MixedReflectionCapture c;c.set_inspector(&inspector);c.prefer_16bit(true);c.configure(CaptureTiming::InFrame,true);
        std::vector<DWORD> staticpix(4096,0xff0a0a0au);c.set_static_pixels(staticpix);c.set_race(5);
        ReflectionStageReport r;CHECK(c.capture(n,&n.env,1,false)==S_OK);
        CHECK(c.take_stage_report(r)&&r.valid&&r.readback_ok&&r.ordinal==1&&r.race==5&&r.frame==1&&!r.late&&!c.take_stage_report(r));
        CHECK(r.source.width==1280&&r.source.height==720&&std::abs(r.source.mean[0]-100.f)<.01f&&r.source.black==0.f);
        CHECK(r.ps2frame.width==640&&r.ps2frame.height==448&&r.bottom.width==640&&r.bottom.height==150&&r.bottom.black==0.f);
        CHECK(r.env.width==64&&r.env.height==64&&r.env_format==D3DFMT_A1R5G5B5&&r.static_term.width==64&&r.dynamic.width==64);
        CHECK(r.montage.width==512&&r.montage.height==128&&r.montage.rgb.size()==512u*128u*3u&&!ps2diag::world_incomplete(r.bottom));
        n.ground_black=true;n.mixed_target=nullptr;CHECK(c.capture(n,&n.env,2,false)==S_OK&&c.take_stage_report(r)&&r.ordinal==2&&ps2diag::world_incomplete(r.bottom)&&r.bottom.black==1.f);
        CHECK(c.capture(n,&n.env,3,false)==S_OK&&c.take_stage_report(r)&&r.ordinal==3);
        for(uint64_t frame=4;frame<=29;++frame)CHECK(c.capture(n,&n.env,frame,false)==S_OK&&!c.take_stage_report(r));
        CHECK(c.capture(n,&n.env,30,false)==S_OK&&c.take_stage_report(r)&&r.ordinal==30);
        CHECK(c.counters().stage_reports==4);original.check(n);
        c.set_race(6);CHECK(c.capture(n,&n.env,31,false)==S_OK&&c.take_stage_report(r)&&r.ordinal==1&&r.race==6);        // per race
        n.readback_hr=D3DERR_INVALIDCALL;CHECK(c.capture(n,&n.env,32,false)==S_OK&&!c.take_stage_report(r));original.check(n);
    }
    {   // Stage report of an end-of-world capture.
        DeviceInspector inspector;Native n;MixedReflectionCapture c;c.set_inspector(&inspector);c.configure(CaptureTiming::Late,true);c.set_race(9);n.mixed_target=&n.late.surface;
        ReflectionStageReport r;CHECK(c.capture_late(n,&n.env,40,false)==S_OK&&c.take_stage_report(r)&&r.late&&r.frame==41&&r.valid);
    }
}
int main(){layout_tests();transaction_tests();gpu_tests();timing_gpu_tests();if(failures)std::cerr<<failures<<" failures\n";return failures?1:0;}
