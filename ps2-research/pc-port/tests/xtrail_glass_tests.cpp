#include "xtrail_glass.hpp"
#include "brake_glow.hpp"
#include "foliage_probe.hpp"
#include "provenance.hpp"
#include <algorithm>
#include <cstring>
#include <iostream>
#include <limits>
#include <fstream>
#include <cstdlib>
#include <filesystem>
using namespace gfx2;
using namespace gfx2::ps2port;
int failures=0;
#define CHECK(x) do{if(!(x)){std::cerr<<"FAIL "<<__LINE__<<": "#x"\n";++failures;}}while(0)
#include "mock_interfaces.hpp"
namespace {
class Texture final:public IDirect3DTexture8 {
public:
 ULONG refs=1;
 std::array<DWORD,1024> pixels{};UINT side=16;
 HRESULT STDMETHODCALLTYPE QueryInterface(REFIID,void** out) override {if(!out)return E_POINTER;*out=this;AddRef();return S_OK;}
 ULONG STDMETHODCALLTYPE AddRef() override{return ++refs;}
 ULONG STDMETHODCALLTYPE Release() override{return --refs;}
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
 HRESULT STDMETHODCALLTYPE GetLevelDesc(UINT,D3DSURFACE_DESC*) override{return E_NOTIMPL;}
 HRESULT STDMETHODCALLTYPE GetSurfaceLevel(UINT,IDirect3DSurface8**) override{return E_NOTIMPL;}
 HRESULT STDMETHODCALLTYPE LockRect(UINT,D3DLOCKED_RECT* p,const RECT*,DWORD) override{p->pBits=pixels.data();p->Pitch=side*4;return S_OK;}
 HRESULT STDMETHODCALLTYPE UnlockRect(UINT) override{return S_OK;}
 HRESULT STDMETHODCALLTYPE AddDirtyRect(const RECT*) override{return E_NOTIMPL;}
};
class Buffer final:public IDirect3DVertexBuffer8 {
public:
 ULONG refs=1;
 HRESULT STDMETHODCALLTYPE QueryInterface(REFIID,void** out) override {if(!out)return E_POINTER;*out=this;AddRef();return S_OK;}
 ULONG STDMETHODCALLTYPE AddRef() override{return ++refs;}
 ULONG STDMETHODCALLTYPE Release() override{return --refs;}
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
class Index final:public IDirect3DIndexBuffer8 {
public:
 ULONG refs=1;
 HRESULT STDMETHODCALLTYPE QueryInterface(REFIID,void** out) override {if(!out)return E_POINTER;*out=this;AddRef();return S_OK;}
 ULONG STDMETHODCALLTYPE AddRef() override{return ++refs;}
 ULONG STDMETHODCALLTYPE Release() override{return --refs;}
 HRESULT STDMETHODCALLTYPE GetDevice(IDirect3DDevice8**) override{return E_NOTIMPL;}
 HRESULT STDMETHODCALLTYPE SetPrivateData(REFGUID,const void*,DWORD,DWORD) override{return E_NOTIMPL;}
 HRESULT STDMETHODCALLTYPE GetPrivateData(REFGUID,void*,DWORD*) override{return E_NOTIMPL;}
 HRESULT STDMETHODCALLTYPE FreePrivateData(REFGUID) override{return E_NOTIMPL;}
 DWORD STDMETHODCALLTYPE SetPriority(DWORD) override{return 0;}
 DWORD STDMETHODCALLTYPE GetPriority() override{return 0;}
 void STDMETHODCALLTYPE PreLoad() override{}
 D3DRESOURCETYPE STDMETHODCALLTYPE GetType() override{return D3DRTYPE_INDEXBUFFER;}
 HRESULT STDMETHODCALLTYPE Lock(UINT,UINT,BYTE**,DWORD) override{return E_NOTIMPL;}
 HRESULT STDMETHODCALLTYPE Unlock() override{return E_NOTIMPL;}
 HRESULT STDMETHODCALLTYPE GetDesc(D3DINDEXBUFFER_DESC*) override{return E_NOTIMPL;}
};

struct Native:MockDeviceBase {
 std::array<DWORD,15> states{};Texture original,replacement;Buffer vb;Index ib;
 IDirect3DBaseTexture8* texture=&original;IDirect3DVertexBuffer8* stream=&vb;IDirect3DIndexBuffer8* indices=&ib;
 Texture created_primary,created_highlight;unsigned creates=0;bool fail_create=false;
 HRESULT STDMETHODCALLTYPE CreateTexture(UINT w,UINT h,UINT levels,DWORD usage,D3DFORMAT format,D3DPOOL pool,IDirect3DTexture8** out)override{CHECK(w==h&&(w==16||w==32)&&levels==1&&usage==0&&format==D3DFMT_A8R8G8B8&&pool==D3DPOOL_MANAGED);++creates;if(fail_create){*out=nullptr;return E_FAIL;}auto& t=w==16?created_primary:created_highlight;t.refs=1;t.side=w;*out=&t;return S_OK;}
 D3DMATRIX matrix{};UINT stride=36,base=7;unsigned writes=0,fail=0,draws=0,reads=0,read_fail=0;HRESULT draw_hr=S_FALSE;
 Native(){for(unsigned i=0;i<15;++i)states[i]=100+i;states[5]=TRUE;}
 HRESULT set(){return ++writes==fail?E_FAIL:S_OK;}
 int slot(bool render,DWORD stage,DWORD key){for(unsigned i=0;i<15;++i)if(kGlassOps[i].render==render&&kGlassOps[i].stage==stage&&kGlassOps[i].key==key)return i;return -1;}
 HRESULT STDMETHODCALLTYPE GetRenderState(D3DRENDERSTATETYPE key,DWORD* v)override{if(++reads==read_fail)return E_FAIL;auto i=slot(true,0,key);if(i<0)return E_FAIL;*v=states[i];return S_OK;}
 HRESULT STDMETHODCALLTYPE SetRenderState(D3DRENDERSTATETYPE key,DWORD v)override{auto i=slot(true,0,key);if(i<0)return E_FAIL;states[i]=v;return set();}
 HRESULT STDMETHODCALLTYPE GetTextureStageState(DWORD stage,D3DTEXTURESTAGESTATETYPE key,DWORD* v)override{if(++reads==read_fail)return E_FAIL;auto i=slot(false,stage,key);if(i<0)return E_FAIL;*v=states[i];return S_OK;}
 HRESULT STDMETHODCALLTYPE SetTextureStageState(DWORD stage,D3DTEXTURESTAGESTATETYPE key,DWORD v)override{auto i=slot(false,stage,key);if(i<0)return E_FAIL;states[i]=v;return set();}
 HRESULT STDMETHODCALLTYPE GetTexture(DWORD stage,IDirect3DBaseTexture8** p)override{CHECK(stage==0);*p=texture;if(texture)texture->AddRef();return S_OK;}
 HRESULT STDMETHODCALLTYPE SetTexture(DWORD stage,IDirect3DBaseTexture8* p)override{CHECK(stage==0);texture=p;return set();}
 HRESULT STDMETHODCALLTYPE GetTransform(D3DTRANSFORMSTATETYPE,D3DMATRIX* p)override{*p=matrix;return S_OK;}
 HRESULT STDMETHODCALLTYPE SetTransform(D3DTRANSFORMSTATETYPE,const D3DMATRIX* p)override{matrix=*p;return set();}
 HRESULT STDMETHODCALLTYPE GetStreamSource(UINT,IDirect3DVertexBuffer8** p,UINT* s)override{*p=stream;*s=stride;if(stream)stream->AddRef();return S_OK;}
 HRESULT STDMETHODCALLTYPE SetStreamSource(UINT,IDirect3DVertexBuffer8* p,UINT s)override{stream=p;stride=s;return set();}
 HRESULT STDMETHODCALLTYPE GetIndices(IDirect3DIndexBuffer8** p,UINT* b)override{*p=indices;*b=base;if(indices)indices->AddRef();return S_OK;}
 HRESULT STDMETHODCALLTYPE SetIndices(IDirect3DIndexBuffer8* p,UINT b)override{indices=p;base=b;return set();}
 HRESULT STDMETHODCALLTYPE DrawIndexedPrimitive(D3DPRIMITIVETYPE type,UINT,UINT vertices,UINT,UINT count)override{CHECK(type==D3DPT_TRIANGLELIST&&vertices==20&&count==20);++draws;return draw_hr;}
 HRESULT STDMETHODCALLTYPE DrawPrimitiveUP(D3DPRIMITIVETYPE type,UINT count,const void*,UINT s)override{CHECK(type==D3DPT_TRIANGLELIST&&count==18&&s==36);++draws;stream=nullptr;indices=nullptr;return draw_hr;}
};
}
int main(){
 auto notify=[](uint32_t,const Args&,HRESULT){};D3DMATRIX basis{};basis._11=1;
 CHECK(!xtrail_fidelity_opt_in(L"0",L"1",true));CHECK(!xtrail_fidelity_opt_in(L"1",L"2",true));CHECK(!xtrail_fidelity_opt_in(L"1",L"1",false));
 XtrailGlass stock(true,L"nonexistent-test-config.ini");CHECK(!stock.requested());stock.after_reset(false,true);CHECK(!stock.requested());
 DrawSnapshot unknown;CHECK(glass_vertices(unknown,{},"anything").empty());CHECK(stock.prepare(unknown)==nullptr);
 std::vector<GlassSourceVertex> src;std::vector<DWORD> a,b;CHECK(!decode_xtrail_glass({},src,a,b));CHECK(!decode_xtrail_glass(std::vector<uint8_t>(6920),src,a,b));
 for(unsigned fail=0;fail<=15;++fail){Native n;auto saved=n.states;GlassTransaction t;CHECK(SUCCEEDED(t.capture(n)));n.fail=fail;auto hr=t.pass(n,&n.replacement,false,basis,notify);
  if(!fail){CHECK(SUCCEEDED(hr));CHECK(n.states[0]==FALSE&&n.states[1]==TRUE&&n.states[4]==FALSE);t.mark_up();CHECK(n.DrawPrimitiveUP(D3DPT_TRIANGLELIST,18,nullptr,36)==S_FALSE);
   CHECK(SUCCEEDED(t.pass(n,&n.replacement,true,basis,notify)));CHECK(n.states[2]==D3DBLEND_ONE&&n.states[3]==D3DBLEND_ONE&&n.states[5]==FALSE);t.mark_up();CHECK(n.DrawPrimitiveUP(D3DPT_TRIANGLELIST,18,nullptr,36)==S_FALSE);CHECK(n.draws==2);
  }else CHECK(FAILED(hr));
  n.fail=0;CHECK(SUCCEEDED(t.restore(n,notify)));CHECK(!t.pending());CHECK(n.states==saved);CHECK(n.texture==&n.original&&n.stream==&n.vb&&n.indices==&n.ib&&n.base==7&&n.stride==36);CHECK(n.original.refs==1&&n.vb.refs==1&&n.ib.refs==1);CHECK(n.matrix._11==0);
 }
 for(unsigned read=1;read<=15;++read){Native n;n.read_fail=read;GlassTransaction t;CHECK(FAILED(t.capture(n)));CHECK(n.writes==0&&!t.pending());}
 {Native n;GlassTransaction t;CHECK(SUCCEEDED(t.capture(n)));CHECK(SUCCEEDED(t.pass(n,&n.replacement,false,basis,notify)));n.fail=n.writes+1;CHECK(FAILED(t.restore(n,notify)));CHECK(t.pending());n.fail=0;CHECK(SUCCEEDED(t.restore(n,notify)));CHECK(!t.pending());}
 for(unsigned fail=1;fail<=17;++fail){Native n;auto saved=n.states;GlassTransaction t;CHECK(SUCCEEDED(t.capture(n)));CHECK(SUCCEEDED(t.pass(n,&n.replacement,false,basis,notify)));n.fail=n.writes+fail;auto h=t.pass(n,&n.replacement,true,basis,notify);CHECK(FAILED(h));n.fail=0;CHECK(SUCCEEDED(t.restore(n,notify)));CHECK(n.states==saved&&!t.pending());}
 {Native n;XtrailGlass reset(true,L"nonexistent-test-config.ini");CHECK(SUCCEEDED(reset.transaction.capture(n)));CHECK(SUCCEEDED(reset.transaction.pass(n,&n.replacement,false,basis,notify)));reset.before_reset();CHECK(reset.blocked());reset.after_reset(false,true);CHECK(reset.blocked());reset.after_reset(true,false);CHECK(reset.blocked());reset.after_reset(true,true);CHECK(!reset.blocked());CHECK(n.original.refs==1&&n.vb.refs==1&&n.ib.refs==1);}
 DrawSnapshot g;g.supported_build=true;g.device_id=1;g.primitive_type=D3DPT_TRIANGLELIST;g.fvf=0x152;g.stride=36;g.vertex_count=22;g.primitive_count=18;g.index_format=D3DFMT_INDEX16;g.vertex_resource=1;g.index_resource=2;g.vertex_generation=g.index_generation=g.vertex_revision=g.index_revision=1;g.complete_mirror_coverage=true;g.vertex_bytes.resize(22*36);g.index_bytes.resize(54*2);std::vector<GlassSourceVertex> synthetic(22);
 for(unsigned i=0;i<22;++i){float xyz[3]={float(i),float(i*i)*.01f,0};auto* raw=g.vertex_bytes.data()+i*36;std::memcpy(raw,xyz,12);auto hash=sha256_bytes(xyz,12);auto& v=synthetic[i];for(unsigned j=0;j<32;++j)v.position_hash[j]=static_cast<uint8_t>(std::stoul(hash.substr(j*2,2),nullptr,16));v.expected_normal[2]=1;v.expected_uv[0]=float(i)*.01f;v.expected_color=0xff929292;v.normal[2]=1;v.uv[0]=.25f;v.color=0xffffffff;std::memcpy(raw+12,v.expected_normal,12);std::memcpy(raw+24,&v.expected_color,4);std::memcpy(raw+28,v.expected_uv,8);}
 for(unsigned i=0;i<54;++i){uint16_t index=static_cast<uint16_t>(i/3+i%3);std::memcpy(g.index_bytes.data()+i*2,&index,2);}auto faces=vehicle_face_hashes(g);std::sort(faces.begin(),faces.end());std::string joined;for(auto& f:faces)joined+=f;const auto digest=sha256_bytes(joined.data(),joined.size());auto matched=glass_vertices(g,synthetic,digest);CHECK(matched.size()==54);CHECK(matched[0].uv[0]==.25f&&matched[0].diffuse==0xffffffff);CHECK(glass_vertices(g,synthetic,"wrong").empty());
 for(unsigned offset:{12u,24u,28u}){auto bad=g;bad.vertex_bytes[offset]^=1;CHECK(glass_vertices(bad,synthetic,digest).empty());}
 auto bad=g;bad.index_generation=0;CHECK(glass_vertices(bad,synthetic,digest).empty());bad=g;bad.supported_build=false;CHECK(glass_vertices(bad,synthetic,digest).empty());bad=g;bad.index_bytes[0]=255;CHECK(glass_vertices(bad,synthetic,digest).empty());
 for(unsigned fail=0;fail<=15;++fail){Native n;auto saved=n.states;GlassTransaction t;CHECK(SUCCEEDED(t.capture(n)));n.fail=fail;auto h=t.emissive_pass(n,notify);if(!fail){CHECK(SUCCEEDED(h));CHECK(n.states[2]==D3DBLEND_ONE&&n.states[3]==D3DBLEND_ONE&&n.states[4]==FALSE&&n.states[5]==FALSE&&n.states[6]==D3DTOP_SELECTARG1&&n.states[14]==D3DTOP_DISABLE);}else CHECK(FAILED(h));n.fail=0;CHECK(SUCCEEDED(t.restore(n,notify)));CHECK(n.states==saved&&n.texture==&n.original&&!t.pending());}
 {Native n;auto saved=n.states;GlassTransaction t;CHECK(SUCCEEDED(t.capture(n)));CHECK(SUCCEEDED(t.emissive_pass(n,notify)));auto result=n.DrawIndexedPrimitive(D3DPT_TRIANGLELIST,0,20,0,20);CHECK(result==S_FALSE&&n.draws==1);CHECK(SUCCEEDED(t.restore(n,notify)));CHECK(n.states==saved&&n.stream==&n.vb&&n.indices==&n.ib);}
 DrawSnapshot glow;glow.supported_build=true;glow.device_id=1;glow.complete_mirror_coverage=true;glow.primitive_type=D3DPT_TRIANGLELIST;glow.primitive_count=20;glow.vertex_count=20;glow.fvf=0x112;glow.stride=32;glow.index_format=D3DFMT_INDEX16;glow.vertex_resource=1;glow.index_resource=2;glow.vertex_generation=glow.index_generation=glow.vertex_revision=glow.index_revision=1;glow.vertex_bytes.resize(640);glow.index_bytes.resize(120);
 DrawSnapshot norm=glow;norm.fvf=0x152;norm.stride=36;norm.vertex_bytes.resize(720);std::vector<std::string> attrs;
 for(unsigned i=0;i<20;++i){float v[8]={float(i),float(i*i)*.02f,0,0,0,1,float(i)*.01f,.5f};std::memcpy(glow.vertex_bytes.data()+i*32,v,32);attrs.emplace_back(reinterpret_cast<const char*>(v),32);std::memcpy(norm.vertex_bytes.data()+i*36,v,24);std::memcpy(norm.vertex_bytes.data()+i*36+28,v+6,8);}
 for(unsigned i=0;i<60;++i){uint16_t index=static_cast<uint16_t>((i/3)%18+i%3);std::memcpy(glow.index_bytes.data()+i*2,&index,2);}norm.index_bytes=glow.index_bytes;auto gf=vehicle_face_hashes(norm);std::sort(gf.begin(),gf.end());std::string gj;for(auto& f:gf)gj+=f;auto geometry=sha256_bytes(gj.data(),gj.size());std::sort(attrs.begin(),attrs.end());gj.clear();for(auto& r:attrs)gj+=r;auto attribute=sha256_bytes(gj.data(),gj.size());CHECK(terrano_glow_identity(glow,geometry,attribute));CHECK(!terrano_glow_identity(glow));auto invalid_glow=glow;invalid_glow.vertex_bytes[24]^=1;CHECK(!terrano_glow_identity(invalid_glow,geometry,attribute));invalid_glow=glow;invalid_glow.index_generation=0;CHECK(!terrano_glow_identity(invalid_glow,geometry,attribute));
 {Native n;BrakeGlow reset(true,L"nonexistent-test-config.ini");CHECK(SUCCEEDED(reset.transaction.capture(n)));CHECK(SUCCEEDED(reset.transaction.emissive_pass(n,notify)));reset.before_reset();CHECK(reset.blocked());reset.after_reset(false,true);CHECK(reset.blocked());reset.after_reset(true,false);CHECK(reset.blocked());reset.after_reset(true,true);CHECK(!reset.blocked());CHECK(n.original.refs==1&&n.vb.refs==1&&n.ib.refs==1);}
 BrakeGlow glow_stock(true,L"nonexistent-test-config.ini");CHECK(!glow_stock.requested());
 if(const char* path=std::getenv("MRR_XTRAIL_GLASS_ASSET")){std::ifstream f(path,std::ios::binary);std::vector<uint8_t> bytes((std::istreambuf_iterator<char>(f)),{});CHECK(decode_xtrail_glass(bytes,src,a,b));CHECK(src.size()==22&&a.size()==256&&b.size()==1024);wchar_t folder[MAX_PATH]{},ini[MAX_PATH]{};CHECK(GetTempPathW(MAX_PATH,folder)>0);CHECK(GetTempFileNameW(folder,L"xgl",0,ini)!=0);auto wide=std::filesystem::path(path).wstring();CHECK(WritePrivateProfileStringW(L"PS2Port",L"XtrailGlassMode",L"1",ini));CHECK(WritePrivateProfileStringW(L"PS2Port",L"XtrailGlassAsset",wide.c_str(),ini));
 {Native n;XtrailGlass loaded(true,ini);CHECK(loaded.requested());CHECK(loaded.initialize(n));CHECK(n.creates==2);CHECK(loaded.initialize(n)&&n.creates==2);loaded.before_reset();CHECK(n.created_primary.refs==0&&n.created_highlight.refs==0);loaded.after_reset(true,true);CHECK(loaded.initialize(n)&&n.creates==4);loaded.before_reset();}
 {Native n;n.fail_create=true;XtrailGlass loaded(true,ini);CHECK(loaded.requested());CHECK(!loaded.initialize(n)&&!loaded.requested());CHECK(n.creates==1);}
 CHECK(DeleteFileW(ini));bytes.back()^=1;CHECK(!decode_xtrail_glass(bytes,src,a,b));}
 else std::cout<<"External private glass asset NOT PROVIDED; synthetic tests remain active\n";
 std::cout<<"Failures: "<<failures<<"\n";return failures?1:0;
}
