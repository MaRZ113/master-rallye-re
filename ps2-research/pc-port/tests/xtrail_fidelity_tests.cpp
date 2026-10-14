#include "xtrail_fidelity.hpp"
#include "foliage_probe.hpp"
#include "provenance.hpp"
#include <algorithm>
#include <cstring>
#include <iostream>
#include <limits>
using namespace gfx2;
using namespace gfx2::ps2port;
int failures=0;
#define CHECK(x) do{if(!(x)){std::cerr<<"FAIL "<<__LINE__<<": "#x"\n";++failures;}}while(0)
#include "mock_interfaces.hpp"
namespace {
class Texture final:public IDirect3DTexture8 {
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
 D3DRESOURCETYPE STDMETHODCALLTYPE GetType() override{return D3DRTYPE_TEXTURE;}
 DWORD STDMETHODCALLTYPE SetLOD(DWORD) override{return 0;}
 DWORD STDMETHODCALLTYPE GetLOD() override{return 0;}
 DWORD STDMETHODCALLTYPE GetLevelCount() override{return 1;}
 HRESULT STDMETHODCALLTYPE GetLevelDesc(UINT,D3DSURFACE_DESC*) override{return E_NOTIMPL;}
 HRESULT STDMETHODCALLTYPE GetSurfaceLevel(UINT,IDirect3DSurface8**) override{return E_NOTIMPL;}
 HRESULT STDMETHODCALLTYPE LockRect(UINT,D3DLOCKED_RECT*,const RECT*,DWORD) override{return E_NOTIMPL;}
 HRESULT STDMETHODCALLTYPE UnlockRect(UINT) override{return E_NOTIMPL;}
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
 std::array<DWORD,8> stages={D3DTOP_DISABLE,D3DTA_CURRENT,D3DTA_TEXTURE,D3DTOP_MODULATE,D3DTA_CURRENT,D3DTA_TEXTURE,0,0};
 Texture original,replacement;Buffer vb;Index ib;IDirect3DBaseTexture8* texture=&original;
 IDirect3DVertexBuffer8* stream=&vb;IDirect3DIndexBuffer8* indices=&ib;
 DWORD fvf=0x142;UINT stride=24,base=7;unsigned writes=0,fail=0,draws=0,rs_writes=0;
 HRESULT draw_hr=S_FALSE;
 HRESULT setter(){return ++writes==fail?E_FAIL:S_OK;}
 HRESULT STDMETHODCALLTYPE GetTextureStageState(DWORD stage,D3DTEXTURESTAGESTATETYPE key,DWORD* v)override {
  CHECK(stage==1);for(size_t i=0;i<8;++i)if(kReflectionStageStates[i]==key){*v=stages[i];return S_OK;}return E_FAIL;
 }
 HRESULT STDMETHODCALLTYPE SetTextureStageState(DWORD stage,D3DTEXTURESTAGESTATETYPE key,DWORD v)override {
  CHECK(stage==1);for(size_t i=0;i<8;++i)if(kReflectionStageStates[i]==key){stages[i]=v;return setter();}return E_FAIL;
 }
 HRESULT STDMETHODCALLTYPE GetTexture(DWORD stage,IDirect3DBaseTexture8** p)override{CHECK(stage==1);*p=texture;if(texture)texture->AddRef();return S_OK;}
 HRESULT STDMETHODCALLTYPE SetTexture(DWORD stage,IDirect3DBaseTexture8* p)override{CHECK(stage==1);texture=p;return setter();}
 HRESULT STDMETHODCALLTYPE GetVertexShader(DWORD* p)override{*p=fvf;return S_OK;}
 HRESULT STDMETHODCALLTYPE SetVertexShader(DWORD v)override{fvf=v;return setter();}
 HRESULT STDMETHODCALLTYPE GetStreamSource(UINT,IDirect3DVertexBuffer8** p,UINT* s)override{*p=stream;*s=stride;if(stream)stream->AddRef();return S_OK;}
 HRESULT STDMETHODCALLTYPE SetStreamSource(UINT,IDirect3DVertexBuffer8* p,UINT s)override{stream=p;stride=s;return setter();}
 HRESULT STDMETHODCALLTYPE GetIndices(IDirect3DIndexBuffer8** p,UINT* b)override{*p=indices;*b=base;if(indices)indices->AddRef();return S_OK;}
 HRESULT STDMETHODCALLTYPE SetIndices(IDirect3DIndexBuffer8* p,UINT b)override{indices=p;base=b;return setter();}
 HRESULT STDMETHODCALLTYPE SetRenderState(D3DRENDERSTATETYPE,DWORD)override{++rs_writes;return E_FAIL;}
 HRESULT STDMETHODCALLTYPE DrawPrimitiveUP(D3DPRIMITIVETYPE type,UINT count,const void*,UINT s)override {
  CHECK(type==D3DPT_TRIANGLELIST&&count==14&&s==36);CHECK(fvf==0x152&&texture==&replacement);
  ++draws;stream=nullptr;indices=nullptr;return draw_hr;
 }
};
}
int main(){
 CHECK(!xtrail_fidelity_opt_in(L"0",L"1",true));CHECK(!xtrail_fidelity_opt_in(L"1",L"2",true));
 CHECK(!xtrail_fidelity_opt_in(L"1",L"1",false));CHECK(xtrail_fidelity_opt_in(L"1",L"1",true));
 XtrailFidelity stock(true,L"Z:\\nonexistent.ini");CHECK(!stock.requested());
 const auto notify=[](uint32_t,const Args&,HRESULT)noexcept{};
 {XtrailTransaction uncaptured;uncaptured.mark_up();CHECK(!uncaptured.pending());}
 for(unsigned fail=0;fail<6;++fail){
  Native n;const auto original=n.stages;XtrailTransaction t;CHECK(t.capture(n)==S_OK);
  n.fail=fail;const auto applied=t.apply(n,&n.replacement,notify);
  if(SUCCEEDED(applied)){t.mark_up();const auto result=n.DrawPrimitiveUP(D3DPT_TRIANGLELIST,14,nullptr,36);CHECK(result==S_FALSE&&n.draws==1);}
  CHECK(SUCCEEDED(t.restore(n,notify)));CHECK(!t.pending());
  CHECK(n.stages==original&&n.fvf==0x142&&n.texture==&n.original&&n.stream==&n.vb&&n.indices==&n.ib&&n.base==7);
  CHECK(!n.rs_writes);CHECK(n.original.refs==1&&n.vb.refs==1&&n.ib.refs==1);
 }
 {
  Native n;XtrailTransaction t;CHECK(t.capture(n)==S_OK);CHECK(t.apply(n,&n.replacement,notify)==S_OK);
  t.mark_up();n.draw_hr=D3DERR_INVALIDCALL;const auto h=n.DrawPrimitiveUP(D3DPT_TRIANGLELIST,14,nullptr,36);
  n.fail=n.writes+1;CHECK(FAILED(t.restore(n,notify)));CHECK(t.pending());
  n.fail=0;CHECK(SUCCEEDED(t.restore(n,notify)));CHECK(!t.pending()&&n.draws==1&&h==D3DERR_INVALIDCALL);
 }
 for(unsigned fail=1;fail<=10;++fail){
  Native n;n.stages.fill(0xdead);const auto original=n.stages;XtrailTransaction t;
  CHECK(t.capture(n)==S_OK);n.fail=fail;CHECK(FAILED(t.apply(n,&n.replacement,notify)));
  CHECK(SUCCEEDED(t.restore(n,notify)));CHECK(!t.pending()&&n.stages==original&&n.fvf==0x142);
  CHECK(!n.draws&&!n.rs_writes&&n.original.refs==1&&n.vb.refs==1&&n.ib.refs==1);
 }
 {
  Native n;XtrailFidelity reset(true,L"Z:\\nonexistent.ini");CHECK(reset.transaction.capture(n)==S_OK);
  CHECK(reset.transaction.apply(n,&n.replacement,notify)==S_OK);
  reset.before_reset();CHECK(reset.blocked());
  reset.after_reset(false,true);CHECK(reset.blocked());
  reset.after_reset(true,false);CHECK(reset.blocked());
  reset.after_reset(true,true);CHECK(!reset.blocked());
  CHECK(n.original.refs==1&&n.vb.refs==1&&n.ib.refs==1);
 }
 // Corpus-independent positive source-normal reconstruction with a synthetic registry.
 DrawSnapshot g;g.supported_build=true;g.device_id=1;g.reset_generation=2;g.primitive_type=D3DPT_TRIANGLELIST;
 g.fvf=0x142;g.stride=24;g.vertex_count=20;g.primitive_count=14;g.index_format=D3DFMT_INDEX16;
 g.vertex_resource=1;g.index_resource=2;g.vertex_generation=g.index_generation=g.vertex_revision=g.index_revision=1;
 g.complete_mirror_coverage=true;g.vertex_bytes.resize(20*24);g.index_bytes.resize(42*2);
 std::array<std::string,20> position_hashes;std::array<XtrailDecalNormal,20> normals;
 for(unsigned i=0;i<20;++i){
  float xyz[3]={float(i),float(i*i)*.01f,0};float uv[2]={float(i)*.01f,.5f};DWORD color=0xff929292;
  auto* v=g.vertex_bytes.data()+i*24;std::memcpy(v,xyz,12);std::memcpy(v+12,&color,4);std::memcpy(v+16,uv,8);
  position_hashes[i]=sha256_bytes(xyz,12);normals[i].position_sha=position_hashes[i].c_str();
  normals[i].normal_bits={0,0,0x3f800000};std::memcpy(normals[i].uv_bits.data(),uv,8);normals[i].diffuse=color;
 }
 std::sort(normals.begin(),normals.end(),[](const auto& a,const auto& b){return std::string_view(a.position_sha)<b.position_sha;});
 for(unsigned i=0;i<42;++i){uint16_t v=static_cast<uint16_t>((i/3)+(i%3));std::memcpy(g.index_bytes.data()+i*2,&v,2);}
 auto faces=vehicle_face_hashes(g);std::sort(faces.begin(),faces.end());std::string joined;for(auto& f:faces)joined+=f;
 const auto digest=sha256_bytes(joined.data(),joined.size());
 auto result=prepare_decal_vertices(g,digest,normals.data(),20);CHECK(result.size()==42);
 CHECK(result[0].normal[2]==1&&result[0].diffuse==0xff929292);CHECK(prepare_xtrail_decal(g).empty());
 auto modified=g;modified.vertex_bytes[16]^=1;CHECK(prepare_decal_vertices(modified,digest,normals.data(),20).empty());
 modified=g;modified.vertex_bytes[12]^=1;CHECK(prepare_decal_vertices(modified,digest,normals.data(),20).empty());
 modified=g;modified.index_generation=0;CHECK(prepare_decal_vertices(modified,digest,normals.data(),20).empty());
 modified=g;modified.supported_build=false;CHECK(prepare_decal_vertices(modified,digest,normals.data(),20).empty());
 stock.after_reset(false,true);CHECK(!stock.blocked());stock.before_reset();stock.after_reset(true,true);CHECK(!stock.blocked());
 std::cout<<"Xtrail focused contracts: "<<(failures?"FAIL":"PASS")<<"\n";return failures?1:0;
}
