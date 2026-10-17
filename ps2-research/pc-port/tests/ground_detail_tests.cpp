#include "ground_detail.hpp"
#include <array>
#include <cstring>
#include <iostream>
#include <vector>

using namespace gfx2;
using namespace gfx2::ps2port;
int failures=0;
#define CHECK(x) do{if(!(x)){std::cerr<<"FAIL "<<__LINE__<<": "#x"\n";++failures;}}while(0)
#include "mock_interfaces.hpp"

namespace {
struct Texture final:IDirect3DTexture8 {
    ULONG refs=1;D3DSURFACE_DESC desc{};std::vector<BYTE> bits;INT pitch=0;int locks=0;HRESULT lock_hr=S_OK;DWORD last_flags=0;
    Texture(UINT w=128,UINT h=128,D3DFORMAT f=D3DFMT_A8R8G8B8,D3DPOOL pool=D3DPOOL_MANAGED,INT pad=0){
        desc.Width=w;desc.Height=h;desc.Format=f;desc.Pool=pool;desc.Type=D3DRTYPE_TEXTURE;pitch=INT(w*4)+pad;bits.assign(size_t(pitch)*h,0);}
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
    HRESULT STDMETHODCALLTYPE LockRect(UINT,D3DLOCKED_RECT* l,const RECT*,DWORD flags) override{++locks;last_flags=flags;if(FAILED(lock_hr))return lock_hr;l->pBits=bits.data();l->Pitch=pitch;return S_OK;}
    HRESULT STDMETHODCALLTYPE UnlockRect(UINT) override{return S_OK;}
    HRESULT STDMETHODCALLTYPE AddDirtyRect(const RECT*) override{return E_NOTIMPL;}
};
struct Native final:MockDeviceBase {
    std::array<DWORD,256> rs{};std::array<std::array<DWORD,32>,3> tss{};Texture original0,other;
    IDirect3DBaseTexture8* tex0=&original0;int sets=0,fail_set=0;
    Native(){for(size_t i=0;i<rs.size();++i)rs[i]=DWORD(1000+i);for(size_t s=0;s<3;++s)for(size_t i=0;i<32;++i)tss[s][i]=DWORD(2000+s*32+i);}
    HRESULT w(){++sets;return sets==fail_set?D3DERR_INVALIDCALL:S_OK;}
    HRESULT STDMETHODCALLTYPE GetRenderState(D3DRENDERSTATETYPE k,DWORD* p) override{*p=rs[k];return S_OK;}
    HRESULT STDMETHODCALLTYPE SetRenderState(D3DRENDERSTATETYPE k,DWORD v) override{const auto r=w();rs[k]=v;return r;}
    HRESULT STDMETHODCALLTYPE GetTextureStageState(DWORD s,D3DTEXTURESTAGESTATETYPE k,DWORD* p) override{*p=tss[s][k];return S_OK;}
    HRESULT STDMETHODCALLTYPE SetTextureStageState(DWORD s,D3DTEXTURESTAGESTATETYPE k,DWORD v) override{const auto r=w();tss[s][k]=v;return r;}
    HRESULT STDMETHODCALLTYPE GetTexture(DWORD,IDirect3DBaseTexture8** p) override{*p=tex0;if(*p)(*p)->AddRef();return S_OK;}
    HRESULT STDMETHODCALLTYPE SetTexture(DWORD,IDirect3DBaseTexture8* p) override{const auto r=w();if(p)p->AddRef();if(tex0)tex0->Release();tex0=p;return r;}
};

std::vector<uint8_t> fake_gxi(){std::vector<uint8_t> g(kGroundNoiseGxiSize,7);const uint32_t magic=0x13039;const uint16_t s=128;std::memcpy(g.data(),&magic,4);std::memcpy(g.data()+4,&s,2);std::memcpy(g.data()+6,&s,2);return g;}

void asset_tests(){
    std::vector<DWORD> out{1};
    CHECK(!decode_ground_noise(fake_gxi(),out)&&out.empty());           // right layout, wrong identity
    CHECK(!decode_ground_noise(std::vector<uint8_t>(10,0),out));
    std::vector<DWORD> src(128*128);for(size_t i=0;i<src.size();++i){const DWORD v=DWORD(i*37%55);src[i]=0xff000000u|(v<<16)|(v<<8)|v;}
    auto half=ground_noise_half(src,128);CHECK(half.size()==64*64);
    double a=0,b=0;for(auto p:src)a+=p&0xff;for(auto p:half)b+=p&0xff;a/=double(src.size());b/=double(half.size());
    CHECK(std::abs(a-b)<0.6);                                             // the subtracted mean survives mipmapping
    CHECK((half[0]>>24)==0xff);
}
void identity_hash_tests(){
    std::vector<BYTE> plain(128*512),padded(128*520,0xcd);
    for(size_t i=0;i<plain.size();++i)plain[i]=BYTE((i*13)&0xff);
    for(size_t y=0;y<128;++y)std::memcpy(padded.data()+y*520,plain.data()+y*512,512);
    const auto h1=pc_noise_level0_sha(plain.data(),512,D3DFMT_A8R8G8B8);
    CHECK(!h1.empty()&&h1==pc_noise_level0_sha(padded.data(),520,D3DFMT_A8R8G8B8));
    auto opaque=plain;for(size_t i=3;i<opaque.size();i+=4)opaque[i]=0xff;auto garbage=plain;for(size_t i=3;i<garbage.size();i+=4)garbage[i]=0x12;
    CHECK(pc_noise_level0_sha(garbage.data(),512,D3DFMT_X8R8G8B8)==pc_noise_level0_sha(opaque.data(),512,D3DFMT_A8R8G8B8));
    CHECK(pc_noise_level0_sha(plain.data(),511,D3DFMT_A8R8G8B8).empty());
    CHECK(pc_noise_level0_sha(plain.data(),512,D3DFMT_R5G6B5).empty());
    CHECK(pc_noise_level0_sha(nullptr,512,D3DFMT_A8R8G8B8).empty());
}
void identify_tests(){
    GroundDetail g(false,L"");CHECK(!g.requested());
    Texture content;auto r=g.identify(&content,5);CHECK(!r.match&&!std::strcmp(r.reason,"pc_noise_content_mismatch"));
    CHECK(content.locks==1&&content.last_flags==D3DLOCK_READONLY);
    r=g.identify(&content,5);CHECK(content.locks==1&&!r.match);                 // cached per generation
    r=g.identify(&content,6);CHECK(content.locks==2);                            // new generation re-checks
    Texture tiny(64,64);r=g.identify(&tiny,1);CHECK(!std::strcmp(r.reason,"stage1_not_128x128")&&tiny.locks==0);
    Texture dxt(128,128,D3DFMT_DXT1);r=g.identify(&dxt,1);CHECK(!std::strcmp(r.reason,"pc_noise_format_not_32bit"));
    Texture def(128,128,D3DFMT_A8R8G8B8,D3DPOOL_DEFAULT);r=g.identify(&def,1);CHECK(!std::strcmp(r.reason,"pc_noise_not_lockable")&&def.locks==0);
    Texture fails;fails.lock_hr=E_FAIL;r=g.identify(&fails,1);CHECK(!std::strcmp(r.reason,"pc_noise_lock_failed"));
    r=g.identify(&content,0);CHECK(!std::strcmp(r.reason,"stage1_texture_untracked"));
    CHECK(content.refs==1&&tiny.refs==1);
}
struct Original {
    std::array<DWORD,256> rs;std::array<std::array<DWORD,32>,3> tss;
    explicit Original(const Native& n):rs(n.rs),tss(n.tss){}
    void check(const Native& n) const{CHECK(rs==n.rs&&tss==n.tss);CHECK(n.tex0==&n.original0&&n.original0.refs==1&&n.other.refs==1);}
};
void transaction_tests(){
    {Native n;Original o(n);GroundDetailTransaction t;CHECK(t.capture(n)==S_OK);
        CHECK(t.saved(14)==n.tss[0][D3DTSS_TEXCOORDINDEX]);
        CHECK(t.set(n,0,D3DTOP_DISABLE)==S_OK&&n.tss[1][D3DTSS_COLOROP]==D3DTOP_DISABLE);
        CHECK(t.set(n,5,D3DBLENDOP_REVSUBTRACT)==S_OK&&n.rs[D3DRS_BLENDOP]==D3DBLENDOP_REVSUBTRACT);
        CHECK(t.set(n,21,0,&n.other)==S_OK&&n.tex0==&n.other);
        CHECK(t.pending()&&t.capture(n)==D3DERR_INVALIDCALL);
        CHECK(t.restore(n)==S_OK&&!t.pending());o.check(n);}
    for(int failure=1;failure<=48;++failure){
        Native n;Original o(n);GroundDetailTransaction t;CHECK(t.capture(n)==S_OK);n.fail_set=failure;
        HRESULT hr=S_OK;for(size_t i=0;i<kGroundOps.size()&&SUCCEEDED(hr);++i)hr=kGroundOps[i].kind==GroundStateKind::Texture?t.set(n,i,0,&n.other):t.set(n,i,0x77);
        hr=t.restore(n);if(FAILED(hr)){CHECK(t.pending());n.fail_set=0;CHECK(t.restore(n)==S_OK);}
        CHECK(!t.pending());o.check(n);}
    {Native n;GroundDetailTransaction t;CHECK(t.set(n,0,1)==E_INVALIDARG);CHECK(n.sets==0);}
    {Native n;Original o(n);GroundDetailTransaction t;CHECK(t.capture(n)==S_OK);CHECK(t.set(n,kGroundOps.size(),1)==E_INVALIDARG);t.release();o.check(n);}
}
}
int main(){asset_tests();identity_hash_tests();identify_tests();transaction_tests();if(failures)std::cerr<<failures<<" failures\n";return failures?1:0;}
