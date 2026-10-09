#include "wrappers.hpp"
#include "foliage_probe.hpp"
#include <iostream>
#include <stdexcept>
#include <vector>
#include <type_traits>
#include <limits>
#include <cfenv>
#include <algorithm>
#define CHECK(x) do{if(!(x))throw std::runtime_error(#x);}while(0)
#include "mock_interfaces.hpp"
using namespace gfx2;
template<class T>struct Buffer:T {
 using Desc=std::conditional_t<std::is_same_v<T,IDirect3DVertexBuffer8>,D3DVERTEXBUFFER_DESC,D3DINDEXBUFFER_DESC>;
 Desc desc{};std::vector<BYTE> bytes;unsigned refs=1,locks=0,unlocks=0;bool fail_lock=false,fail_unlock=false;
 HRESULT STDMETHODCALLTYPE QueryInterface(REFIID,void**)override{return E_NOINTERFACE;}
 ULONG STDMETHODCALLTYPE AddRef()override{return ++refs;}ULONG STDMETHODCALLTYPE Release()override{return --refs;}
 HRESULT STDMETHODCALLTYPE GetDevice(IDirect3DDevice8**)override{return E_NOTIMPL;}
 HRESULT STDMETHODCALLTYPE SetPrivateData(REFGUID,const void*,DWORD,DWORD)override{return E_NOTIMPL;}
 HRESULT STDMETHODCALLTYPE GetPrivateData(REFGUID,void*,DWORD*)override{return E_NOTIMPL;}
 HRESULT STDMETHODCALLTYPE FreePrivateData(REFGUID)override{return E_NOTIMPL;}
 DWORD STDMETHODCALLTYPE SetPriority(DWORD)override{return 0;}DWORD STDMETHODCALLTYPE GetPriority()override{return 0;}
 void STDMETHODCALLTYPE PreLoad()override{}D3DRESOURCETYPE STDMETHODCALLTYPE GetType()override{return D3DRTYPE_VERTEXBUFFER;}
 HRESULT STDMETHODCALLTYPE Lock(UINT offset,UINT count,BYTE** p,DWORD flags)override{
  CHECK(flags==D3DLOCK_READONLY);CHECK(offset<=bytes.size()&&count<=bytes.size()-offset);++locks;if(fail_lock)return E_FAIL;*p=bytes.data()+offset;return S_OK;
 }
 HRESULT STDMETHODCALLTYPE Unlock()override{++unlocks;return fail_unlock?E_FAIL:S_OK;}
 HRESULT STDMETHODCALLTYPE GetDesc(Desc* p)override{*p=desc;return S_OK;}
};
struct Raw:MockDeviceBase {
 Buffer<IDirect3DVertexBuffer8> vb;Buffer<IDirect3DIndexBuffer8> ib;UINT base=1,stride=24;DWORD fvf=0x142;
 unsigned draws=0,writes=0,queries=0;HRESULT draw_hr=D3DERR_INVALIDCALL;
 Raw(){
  vb.desc.Size=96;vb.desc.Pool=D3DPOOL_MANAGED;vb.bytes.resize(96);
  const float xyz[]={0,0,0,1,0,0,0,1,0};for(int i=0;i<3;++i){std::memcpy(vb.bytes.data()+(i+1)*24,xyz+3*i,12);DWORD c=(64u+64*i)<<24;std::memcpy(vb.bytes.data()+(i+1)*24+12,&c,4);}
  ib.desc.Size=6;ib.desc.Pool=D3DPOOL_MANAGED;ib.desc.Format=D3DFMT_INDEX16;ib.bytes={0,0,1,0,2,0};
 }
 HRESULT STDMETHODCALLTYPE GetRenderState(D3DRENDERSTATETYPE key,DWORD* p)override{++queries;*p=static_cast<DWORD>(key)+100;return S_OK;}
 HRESULT STDMETHODCALLTYPE GetTextureStageState(DWORD stage,D3DTEXTURESTAGESTATETYPE key,DWORD* p)override{*p=static_cast<DWORD>(key)+stage*100;return S_OK;}
 HRESULT STDMETHODCALLTYPE GetVertexShader(DWORD* p)override{*p=fvf;return S_OK;}
 HRESULT STDMETHODCALLTYPE GetTexture(DWORD,IDirect3DBaseTexture8** p)override{*p=nullptr;return S_OK;}
 HRESULT STDMETHODCALLTYPE GetStreamSource(UINT,IDirect3DVertexBuffer8** p,UINT* s)override{*p=&vb;vb.AddRef();*s=stride;return S_OK;}
 HRESULT STDMETHODCALLTYPE GetIndices(IDirect3DIndexBuffer8** p,UINT* b)override{*p=&ib;ib.AddRef();*b=base;return S_OK;}
 HRESULT STDMETHODCALLTYPE GetTransform(D3DTRANSFORMSTATETYPE,D3DMATRIX* p)override{*p={};p->_11=p->_22=p->_33=p->_44=1;return S_OK;}
 HRESULT STDMETHODCALLTYPE GetMaterial(D3DMATERIAL8* p)override{*p={};p->Diffuse.a=.75f;return S_OK;}
 HRESULT STDMETHODCALLTYPE SetRenderState(D3DRENDERSTATETYPE,DWORD)override{++writes;return E_FAIL;}
 HRESULT STDMETHODCALLTYPE DrawIndexedPrimitive(D3DPRIMITIVETYPE,UINT,UINT,UINT,UINT)override{++draws;CHECK(vb.locks==vb.unlocks&&ib.locks==ib.unlocks);return draw_hr;}
};
ResourceRegistry registry(Raw& n){ResourceRegistry r;r.add(reinterpret_cast<uintptr_t>(&n.vb),23,pack(96,0,0x142,D3DPOOL_MANAGED));r.add(reinterpret_cast<uintptr_t>(&n.ib),24,pack(6,0,D3DFMT_INDEX16,D3DPOOL_MANAGED));return r;}
Args args(){return pack(D3DPT_TRIANGLELIST,0,3,0,1);}
void contracts(){
 auto missing=parse_visual_config({},false);CHECK(!missing.foliage_mode&&!missing.foliage_diagnostics);
 auto defaults=parse_visual_config({{"Renderer.ConfigVersion","1"}},true);CHECK(!defaults.foliage_mode&&!defaults.foliage_diagnostics);
 auto c=parse_visual_config({{"Renderer.ConfigVersion","1"},{"PS2FoliagePilot.Mode","1"},{"PS2FoliagePilot.Diagnostics","1"}},true);
 CHECK(c.foliage_mode==1&&c.foliage_diagnostics);VisualPolicy p;p.configure(c,true,nullptr,E_FAIL);CHECK(!p.effective.foliage_mode&&p.effective.foliage_diagnostics&&p.effective.foliage_reason=="blocked_on_draw_identity");
 p.configure(c,false,nullptr,E_FAIL);CHECK(!p.effective.foliage_mode&&!p.effective.foliage_diagnostics);
 for(const char* invalid:{"2","-1","garbage","nan","1.0"})CHECK(!parse_visual_config({{"Renderer.ConfigVersion","1"},{"PS2FoliagePilot.Mode",invalid}},true).foliage_mode);
 CHECK(!parse_visual_config({{"Renderer.ConfigVersion","2"},{"PS2FoliagePilot.Diagnostics","1"}},true).foliage_diagnostics);
 UINT diffuse;CHECK(foliage_layout(0x142,24,diffuse)&&diffuse==12);CHECK(!foliage_layout(0x142,28,diffuse)&&!foliage_layout(0x144,24,diffuse));
 float xyz[]={0,0,0,1,0,0,0,1,0};auto h=foliage_face_hash(xyz);CHECK(h=="b2afe5ee233688b94630b58778b6b4e92c6af902cc9f61ae448b4bca1090420a");
 std::swap_ranges(xyz,xyz+3,xyz+6);CHECK(foliage_face_hash(xyz)==h);xyz[0]=-0.f;CHECK(foliage_face_hash(xyz)==h);xyz[0]=std::numeric_limits<float>::quiet_NaN();CHECK(foliage_face_hash(xyz).empty());
 Raw raw;auto r=registry(raw);FoliageBudget budget;auto e=probe_foliage(raw,r,args(),1,budget);
 CHECK(e.reason=="content_captured_identity_pending"&&e.face_hashes.size()==1&&e.face_hashes[0]==h);
 CHECK(e.diffuse_alpha_min.value==64&&e.diffuse_alpha_max.value==192&&raw.vb.refs==1&&raw.ib.refs==1&&raw.vb.unlocks==1&&raw.ib.unlocks==1&&!raw.writes);
 CHECK(e.native_rs[0].value==D3DRS_ALPHATESTENABLE+100&&foliage_json(e).find("\"override_applied\":false")!=std::string::npos);
 auto old=e.vertex_generation;r.add(reinterpret_cast<uintptr_t>(&raw.vb),23,pack(96,0,0x142,D3DPOOL_MANAGED));e=probe_foliage(raw,r,args(),2,budget);CHECK(e.vertex_generation!=old);
 r.successful_reset();e=probe_foliage(raw,r,args(),3,budget);CHECK(e.reason=="content_captured_identity_pending"); // Fresh content read; no generation-only cache.
 r.items.clear();e=probe_foliage(raw,r,args(),4,budget);CHECK(e.reason=="missing_creation_identity"&&e.geometry_sha.empty());
 for(DWORD usage:{DWORD(D3DUSAGE_WRITEONLY),DWORD(D3DUSAGE_DYNAMIC)}){Raw n;n.vb.desc.Usage=usage;auto rr=registry(n);FoliageBudget b;e=probe_foliage(n,rr,args(),1,b);CHECK(e.reason=="buffer_not_safe_for_readonly_probe"&&!n.vb.locks);}
 for(bool vertex:{false,true}){Raw n;if(vertex)n.vb.fail_lock=true;else n.ib.fail_lock=true;auto rr=registry(n);FoliageBudget b;e=probe_foliage(n,rr,args(),1,b);CHECK(e.geometry_sha.empty()&&n.vb.refs==1&&n.ib.refs==1);CHECK(n.vb.unlocks==(vertex?0:1));}
 {Raw n;n.ib.fail_unlock=true;auto rr=registry(n);FoliageBudget b;e=probe_foliage(n,rr,args(),1,b);CHECK(e.reason=="unlock_failed_probe_disabled"&&b.disabled&&e.geometry_sha.empty()&&n.vb.unlocks==1);CHECK(!b.take(2,0));}
 {Raw n;n.ib.bytes[0]=9;auto rr=registry(n);FoliageBudget b;e=probe_foliage(n,rr,args(),1,b);CHECK(e.reason=="index_outside_declared_draw"&&e.face_hashes.empty());}
 {Raw n;n.base=UINT_MAX;auto rr=registry(n);FoliageBudget b;e=probe_foliage(n,rr,args(),1,b);CHECK(e.reason=="draw_outside_buffer"&&!n.vb.locks);}
 {Raw n;auto rr=registry(n);FoliageBudget b;e=probe_foliage(n,rr,pack(D3DPT_TRIANGLELIST,0,3,0x80000000u,1),1,b);CHECK(e.reason=="draw_outside_buffer"&&!n.vb.locks);}
 {Raw n;n.vb.desc.Pool=D3DPOOL_DEFAULT;auto rr=registry(n);FoliageBudget b;e=probe_foliage(n,rr,args(),1,b);CHECK(e.reason=="buffer_not_safe_for_readonly_probe"&&!n.vb.locks);}
 {Raw n;n.ib.desc.Size=12;n.ib.desc.Format=D3DFMT_INDEX32;n.ib.bytes={0,0,0,0,1,0,0,0,2,0,0,0};auto rr=registry(n);FoliageBudget b;e=probe_foliage(n,rr,args(),1,b);CHECK(e.geometry_sha.size()==64&&e.face_hashes[0]==h);}
 FoliageBudget b;for(unsigned i=0;i<FOLIAGE_PROBE_LIMIT;++i)CHECK(b.take(7,0));CHECK(!b.take(7,0)&&b.take(8,FOLIAGE_BYTE_LIMIT)&&!b.take(8,1));
 MockRootBase root_raw;Root8 root(&root_raw);Raw n;Device8 wrapper(&n,&root);wrapper.trace.resources=registry(n);wrapper.visuals.configure(c,true,nullptr,E_FAIL);
 wrapper.trace.enabled=true;wrapper.trace.control.active=true;auto original=wrapper.trace.shadow.snapshot();
 CHECK(wrapper.draw_indexed_at(D3DPT_TRIANGLELIST,0,3,0,1,0)==n.draw_hr&&n.draws==1&&n.writes==0&&n.queries==12);
 CHECK(wrapper.trace.shadow.snapshot().rs[0].known==original.rs[0].known);wrapper.trace.control.active=false;
 CHECK(wrapper.draw_indexed_at(D3DPT_TRIANGLELIST,0,3,0,1,0)==n.draw_hr&&n.draws==2&&n.queries==12);
 wrapper.trace.control.active=true;wrapper.visuals.configure(c,false,nullptr,E_FAIL);
 CHECK(wrapper.draw_indexed_at(D3DPT_TRIANGLELIST,0,3,0,1,0)==n.draw_hr&&n.draws==3&&n.queries==12);
 wrapper.visuals.configure(c,true,nullptr,E_FAIL);wrapper.trace.control.pending=true;wrapper.trace.after(15,pack(),S_OK,0);
 CHECK(wrapper.draw_indexed_at(D3DPT_TRIANGLELIST,0,3,0,1,0)==n.draw_hr&&n.draws==4&&n.writes==0);
 wrapper.trace.after(15,pack(),S_OK,0); // Real production F10 serializer, synthetic native backend.
 std::cout<<"Foliage diagnostic config/hash/base/index/read-only cleanup/generation/budget/Stock once/HRESULT: PASS\n";
}
int main(){try{contracts();return 0;}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
