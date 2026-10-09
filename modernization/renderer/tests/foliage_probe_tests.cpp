#include "wrappers.hpp"
#include "foliage_probe.hpp"
#include "buffer_provenance.hpp"
#include "quality.hpp"
#include <iostream>
#include <stdexcept>
#include <vector>
#include <type_traits>
#include <limits>
#include <cfenv>
#include <algorithm>
#include <functional>
#define CHECK(x) do{if(!(x))throw std::runtime_error(#x);}while(0)
#include "mock_interfaces.hpp"
using namespace gfx2;
template<class T>struct Buffer:T {
 using Desc=std::conditional_t<std::is_same_v<T,IDirect3DVertexBuffer8>,D3DVERTEXBUFFER_DESC,D3DINDEXBUFFER_DESC>;
 Desc desc{};std::vector<BYTE> bytes;unsigned refs=1,locks=0,unlocks=0;DWORD last_lock_flags=0;bool fail_lock=false,fail_unlock=false,expose_unknown_query=false;
 HRESULT STDMETHODCALLTYPE QueryInterface(REFIID iid,void** p)override{if(!p)return E_POINTER;*p=nullptr;if(iid==IID_IUnknown||iid==IID_IDirect3DResource8){*p=static_cast<T*>(this);AddRef();return S_OK;}if(expose_unknown_query){*p=static_cast<T*>(this);AddRef();return S_OK;}return E_NOINTERFACE;}
 ULONG STDMETHODCALLTYPE AddRef()override{return ++refs;}ULONG STDMETHODCALLTYPE Release()override{return --refs;}
 HRESULT STDMETHODCALLTYPE GetDevice(IDirect3DDevice8**)override{return E_NOTIMPL;}
 HRESULT STDMETHODCALLTYPE SetPrivateData(REFGUID,const void*,DWORD,DWORD)override{return E_NOTIMPL;}
 HRESULT STDMETHODCALLTYPE GetPrivateData(REFGUID,void*,DWORD*)override{return E_NOTIMPL;}
 HRESULT STDMETHODCALLTYPE FreePrivateData(REFGUID)override{return E_NOTIMPL;}
 DWORD STDMETHODCALLTYPE SetPriority(DWORD)override{return 0;}DWORD STDMETHODCALLTYPE GetPriority()override{return 0;}
 void STDMETHODCALLTYPE PreLoad()override{}D3DRESOURCETYPE STDMETHODCALLTYPE GetType()override{return D3DRTYPE_VERTEXBUFFER;}
 HRESULT STDMETHODCALLTYPE Lock(UINT offset,UINT count,BYTE** p,DWORD flags)override{
  last_lock_flags=flags;CHECK(offset<=bytes.size()&&count<=bytes.size()-offset);++locks;if(fail_lock)return E_FAIL;*p=bytes.data()+offset;return S_OK;
 }
 HRESULT STDMETHODCALLTYPE Unlock()override{++unlocks;return fail_unlock?E_FAIL:S_OK;}
 HRESULT STDMETHODCALLTYPE GetDesc(Desc* p)override{*p=desc;return S_OK;}
};
struct Raw:MockDeviceBase {
 Buffer<IDirect3DVertexBuffer8> vb;Buffer<IDirect3DIndexBuffer8> ib;UINT base=1,stride=24;DWORD fvf=0x142;bool expose_unknown_device_query=false;
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
 HRESULT STDMETHODCALLTYPE QueryInterface(REFIID,void** out)override{if(!out)return E_POINTER;*out=nullptr;if(!expose_unknown_device_query)return E_NOINTERFACE;*out=static_cast<IDirect3DDevice8*>(this);return S_OK;}
 HRESULT STDMETHODCALLTYPE DrawIndexedPrimitive(D3DPRIMITIVETYPE,UINT,UINT,UINT,UINT)override{++draws;CHECK(vb.locks==vb.unlocks&&ib.locks==ib.unlocks);return draw_hr;}
};
ResourceRegistry registry(Raw& n){ResourceRegistry r;r.add(reinterpret_cast<uintptr_t>(&n.vb),23,pack(96,0,0x142,D3DPOOL_MANAGED),0x12345678);r.add(reinterpret_cast<uintptr_t>(&n.ib),24,pack(6,0,D3DFMT_INDEX16,D3DPOOL_MANAGED),0x87654321);return r;}
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
 CHECK(e.vertex_creation_caller==0x12345678&&e.index_creation_caller==0x87654321&&e.vertex_creation_method==23&&e.index_creation_method==24);
 CHECK(e.diffuse_alpha_min.value==64&&e.diffuse_alpha_max.value==192&&raw.vb.refs==1&&raw.ib.refs==1&&raw.vb.unlocks==1&&raw.ib.unlocks==1&&!raw.writes);
 CHECK(e.native_rs[0].value==D3DRS_ALPHATESTENABLE+100&&foliage_json(e).find("\"override_applied\":false")!=std::string::npos);
 auto old=e.vertex_generation;r.add(reinterpret_cast<uintptr_t>(&raw.vb),23,pack(96,0,0x142,D3DPOOL_MANAGED));e=probe_foliage(raw,r,args(),2,budget);CHECK(e.vertex_generation!=old);
 r.successful_reset();e=probe_foliage(raw,r,args(),3,budget);CHECK(e.reason=="content_captured_identity_pending"); // Fresh content read; no generation-only cache.
 r.items.clear();e=probe_foliage(raw,r,args(),4,budget);CHECK(e.reason=="missing_creation_identity"&&e.geometry_sha.empty());
 for(DWORD usage:{DWORD(D3DUSAGE_WRITEONLY),DWORD(D3DUSAGE_DYNAMIC)}){Raw n;n.vb.desc.Usage=usage;auto rr=registry(n);FoliageBudget b;e=probe_foliage(n,rr,args(),1,b);CHECK(e.reason=="cpu_upload_mirror_missing_or_incomplete"&&!n.vb.locks);}
 for(bool vertex:{false,true}){Raw n;if(vertex)n.vb.fail_lock=true;else n.ib.fail_lock=true;auto rr=registry(n);FoliageBudget b;e=probe_foliage(n,rr,args(),1,b);CHECK(e.geometry_sha.empty()&&n.vb.refs==1&&n.ib.refs==1);CHECK(n.vb.unlocks==(vertex?0:1));}
 {Raw n;n.ib.fail_unlock=true;auto rr=registry(n);FoliageBudget b;e=probe_foliage(n,rr,args(),1,b);CHECK(e.reason=="unlock_failed_probe_disabled"&&b.disabled&&e.geometry_sha.empty()&&n.vb.unlocks==1);CHECK(!b.take(2,0));}
 {Raw n;n.ib.bytes[0]=9;auto rr=registry(n);FoliageBudget b;e=probe_foliage(n,rr,args(),1,b);CHECK(e.reason=="index_outside_declared_draw"&&e.face_hashes.empty());}
 {Raw n;n.base=UINT_MAX;auto rr=registry(n);FoliageBudget b;e=probe_foliage(n,rr,args(),1,b);CHECK(e.reason=="draw_outside_buffer"&&!n.vb.locks);}
 {Raw n;auto rr=registry(n);FoliageBudget b;e=probe_foliage(n,rr,pack(D3DPT_TRIANGLELIST,0,3,0x80000000u,1),1,b);CHECK(e.reason=="draw_outside_buffer"&&!n.vb.locks);}
 {Raw n;n.vb.desc.Pool=D3DPOOL_DEFAULT;auto rr=registry(n);FoliageBudget b;e=probe_foliage(n,rr,args(),1,b);CHECK(e.reason=="cpu_upload_mirror_missing_or_incomplete"&&!n.vb.locks);}
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
void cpu_write_provenance(){
 MockRootBase root_raw;Root8 root(&root_raw);Raw native;Device8 device(&native,&root);device.visuals.effective.foliage_diagnostics=true;
 Buffer<IDirect3DVertexBuffer8> raw_v;raw_v.desc.Size=32;raw_v.desc.Usage=D3DUSAGE_WRITEONLY;raw_v.desc.Pool=D3DPOOL_DEFAULT;raw_v.bytes.resize(32,0xCC);
 auto serial=device.trace.resources.add(reinterpret_cast<uintptr_t>(&raw_v),23,pack(32,D3DUSAGE_WRITEONLY,0x142,D3DPOOL_DEFAULT)).serial;
 auto* proxy=new VertexBufferProxy(&device,&raw_v,serial);std::vector<BYTE> out;uint64_t revision=0;
 // Duplicate raw identity cannot register a second interface or shadow.
 raw_v.AddRef();auto* duplicate=new VertexBufferProxy(&device,&raw_v,serial);CHECK(!duplicate->core().registered());
 duplicate->Release();CHECK(raw_v.refs==1);
 CHECK(!device.copy_buffer_shadow(&raw_v,BufferKind::Vertex,serial,0,16,out,revision));
 void* qi=nullptr;CHECK(proxy->QueryInterface(IID_IUnknown,&qi)==S_OK&&qi==proxy);static_cast<IUnknown*>(qi)->Release();
 qi=nullptr;CHECK(proxy->QueryInterface(IID_IDirect3DResource8,&qi)==S_OK&&qi==static_cast<IDirect3DResource8*>(proxy));static_cast<IDirect3DResource8*>(qi)->Release();
 BYTE* p=nullptr;CHECK(proxy->Lock(8,8,&p,D3DLOCK_DISCARD)==S_OK&&p);for(unsigned i=0;i<8;++i)p[i]=static_cast<BYTE>(i+1);CHECK(proxy->Unlock()==S_OK);
 CHECK(raw_v.last_lock_flags==D3DLOCK_DISCARD&&device.copy_buffer_shadow(&raw_v,BufferKind::Vertex,serial,8,8,out,revision));CHECK(out==std::vector<BYTE>({1,2,3,4,5,6,7,8}));CHECK(!device.copy_buffer_shadow(&raw_v,BufferKind::Vertex,serial,0,16,out,revision));
 CHECK(proxy->Lock(0,8,&p,0)==S_OK);for(unsigned i=0;i<8;++i)p[i]=static_cast<BYTE>(16+i);CHECK(proxy->Unlock()==S_OK);CHECK(device.copy_buffer_shadow(&raw_v,BufferKind::Vertex,serial,0,16,out,revision));CHECK(out.size()==16&&out[0]==16&&out[15]==8);
 raw_v.fail_unlock=true;CHECK(proxy->Lock(16,8,&p,0)==S_OK);std::memset(p,0x44,8);CHECK(FAILED(proxy->Unlock()));CHECK(!device.copy_buffer_shadow(&raw_v,BufferKind::Vertex,serial,0,16,out,revision));raw_v.fail_unlock=false;
 CHECK(proxy->Lock(0,8,&p,0)==S_OK);std::memset(p,0x55,8);CHECK(proxy->Unlock()==S_OK);raw_v.expose_unknown_query=true;GUID unknown={0x23456789,0x1234,0x5678,{1,2,3,4,5,6,7,8}};void* escaped=nullptr;CHECK(proxy->QueryInterface(unknown,&escaped)==S_OK&&escaped==&raw_v);static_cast<IUnknown*>(escaped)->Release();CHECK(!device.copy_buffer_shadow(&raw_v,BufferKind::Vertex,serial,0,8,out,revision));
 proxy->Release();CHECK(raw_v.refs==0);

 // Unknown write flags and external ProcessVertices writes revoke provenance.
 {MockRootBase rr;Root8 r(&rr);Raw n;n.hr=S_OK;Device8 d(&n,&r);d.visuals.effective.foliage_diagnostics=true;
  Buffer<IDirect3DVertexBuffer8> vb;vb.desc.Size=16;vb.desc.Usage=D3DUSAGE_WRITEONLY;vb.bytes.resize(16);
  auto g=d.trace.resources.add(reinterpret_cast<uintptr_t>(&vb),23,pack(16,D3DUSAGE_WRITEONLY,0,D3DPOOL_DEFAULT)).serial;
  auto* v=new VertexBufferProxy(&d,&vb,g);CHECK(v->Lock(0,16,&p,D3DLOCK_DISCARD)==S_OK);std::memset(p,3,16);CHECK(v->Unlock()==S_OK);CHECK(d.copy_buffer_shadow(&vb,BufferKind::Vertex,g,0,16,out,revision));
  CHECK(v->Lock(0,8,&p,0x80000000u)==S_OK);std::memset(p,4,8);CHECK(v->Unlock()==S_OK);CHECK(!d.copy_buffer_shadow(&vb,BufferKind::Vertex,g,0,16,out,revision));v->Release();}
 {MockRootBase rr;Root8 r(&rr);Raw n;n.hr=S_OK;Device8 d(&n,&r);d.visuals.effective.foliage_diagnostics=true;
  Buffer<IDirect3DVertexBuffer8> vb;vb.desc.Size=16;vb.desc.Usage=D3DUSAGE_WRITEONLY;vb.bytes.resize(16);
  auto g=d.trace.resources.add(reinterpret_cast<uintptr_t>(&vb),23,pack(16,D3DUSAGE_WRITEONLY,0,D3DPOOL_DEFAULT)).serial;
  auto* v=new VertexBufferProxy(&d,&vb,g);CHECK(v->Lock(0,16,&p,D3DLOCK_DISCARD)==S_OK);std::memset(p,3,16);CHECK(v->Unlock()==S_OK);CHECK(d.copy_buffer_shadow(&vb,BufferKind::Vertex,g,0,16,out,revision));
  CHECK(d.ProcessVertices(0,0,3,v,0)==S_OK&&n.last==74);CHECK(!d.copy_buffer_shadow(&vb,BufferKind::Vertex,g,0,16,out,revision));v->Release();}

 // A registry generation change while an old proxy is alive must never reuse
 // the old CPU image for the new resource identity.
 {MockRootBase rr;Root8 r(&rr);Raw n;Device8 d(&n,&r);d.visuals.effective.foliage_diagnostics=true;
  Buffer<IDirect3DVertexBuffer8> vb;vb.desc.Size=8;vb.desc.Usage=D3DUSAGE_WRITEONLY;vb.bytes.resize(8);
  auto g1=d.trace.resources.add(reinterpret_cast<uintptr_t>(&vb),23,pack(8,D3DUSAGE_WRITEONLY,0,D3DPOOL_DEFAULT)).serial;
  auto* v=new VertexBufferProxy(&d,&vb,g1);CHECK(v->Lock(0,8,&p,D3DLOCK_DISCARD)==S_OK);std::memset(p,7,8);CHECK(v->Unlock()==S_OK);CHECK(d.copy_buffer_shadow(&vb,BufferKind::Vertex,g1,0,8,out,revision));
  auto g2=d.trace.resources.add(reinterpret_cast<uintptr_t>(&vb),23,pack(8,D3DUSAGE_WRITEONLY,0,D3DPOOL_DEFAULT)).serial;CHECK(g2!=g1);
  vb.AddRef();CHECK(d.wrap_vertex_buffer(&vb)==&vb);CHECK(!d.copy_buffer_shadow(&vb,BufferKind::Vertex,g2,0,8,out,revision));vb.Release();v->Release();}

 // A bound resource must retain its CPU mirror after the app releases its
 // interface; unbinding releases that copied data without retaining the COM object.
 {MockRootBase rr;Root8 r(&rr);Raw n;n.hr=S_OK;Device8 d(&n,&r);d.visuals.effective.foliage_diagnostics=true;
  Buffer<IDirect3DVertexBuffer8> vb;vb.desc.Size=16;vb.desc.Usage=D3DUSAGE_WRITEONLY;vb.bytes.resize(16);
  auto g=d.trace.resources.add(reinterpret_cast<uintptr_t>(&vb),23,pack(16,D3DUSAGE_WRITEONLY,0,D3DPOOL_DEFAULT)).serial;
  auto* v=new VertexBufferProxy(&d,&vb,g);CHECK(v->Lock(0,16,&p,D3DLOCK_DISCARD)==S_OK);std::memset(p,0x2A,16);CHECK(v->Unlock()==S_OK);
  CHECK(d.SetStreamSource(0,v,4)==S_OK&&n.last==83&&n.observed.a[1]==reinterpret_cast<uintptr_t>(&vb));v->Release();
  CHECK(d.copy_buffer_shadow(&vb,BufferKind::Vertex,g,0,16,out,revision));CHECK(d.SetStreamSource(0,nullptr,0)==S_OK);
  CHECK(!d.copy_buffer_shadow(&vb,BufferKind::Vertex,g,0,16,out,revision));}

 // Index-buffer writes use the same bounded provenance path and Reset revokes it.
 {MockRootBase rr;Root8 r(&rr);Raw n;n.hr=S_OK;Device8 d(&n,&r);d.visuals.effective.foliage_diagnostics=true;
  Buffer<IDirect3DIndexBuffer8> ib;ib.desc.Size=12;ib.desc.Usage=D3DUSAGE_WRITEONLY;ib.desc.Format=D3DFMT_INDEX16;ib.bytes.resize(12);
  auto g=d.trace.resources.add(reinterpret_cast<uintptr_t>(&ib),24,pack(12,D3DUSAGE_WRITEONLY,D3DFMT_INDEX16,D3DPOOL_DEFAULT)).serial;
  auto* i=new IndexBufferProxy(&d,&ib,g);CHECK(i->Lock(0,12,&p,D3DLOCK_DISCARD)==S_OK);for(unsigned k=0;k<12;++k)p[k]=static_cast<BYTE>(k);CHECK(i->Unlock()==S_OK);
  CHECK(d.copy_buffer_shadow(&ib,BufferKind::Index,g,0,12,out,revision));CHECK(d.SetIndices(i,0)==S_OK&&n.last==85&&n.observed.a[0]==reinterpret_cast<uintptr_t>(&ib));
  i->Release();CHECK(d.copy_buffer_shadow(&ib,BufferKind::Index,g,0,12,out,revision));
  CHECK(d.Reset(nullptr)==S_OK);CHECK(!d.copy_buffer_shadow(&ib,BufferKind::Index,g,0,12,out,revision));}

 // Reusing an address with a new resource generation starts with no inherited coverage.
 {MockRootBase rr;Root8 r(&rr);Raw n;Device8 d(&n,&r);d.visuals.effective.foliage_diagnostics=true;
  Buffer<IDirect3DVertexBuffer8> vb;vb.desc.Size=8;vb.desc.Usage=D3DUSAGE_WRITEONLY;vb.bytes.resize(8);
  auto g1=d.trace.resources.add(reinterpret_cast<uintptr_t>(&vb),23,pack(8,D3DUSAGE_WRITEONLY,0,D3DPOOL_DEFAULT)).serial;
  auto* v1=new VertexBufferProxy(&d,&vb,g1);CHECK(v1->Lock(0,8,&p,D3DLOCK_DISCARD)==S_OK);std::memset(p,1,8);CHECK(v1->Unlock()==S_OK);CHECK(d.copy_buffer_shadow(&vb,BufferKind::Vertex,g1,0,8,out,revision));v1->Release();
  auto g2=d.trace.resources.add(reinterpret_cast<uintptr_t>(&vb),23,pack(8,D3DUSAGE_WRITEONLY,0,D3DPOOL_DEFAULT)).serial;CHECK(g2!=g1);
  auto* v2=new VertexBufferProxy(&d,&vb,g2);CHECK(!d.copy_buffer_shadow(&vb,BufferKind::Vertex,g2,0,8,out,revision));v2->Release();}
 // A raw device interface escape disables the provenance path before a later
 // unsupported device interface can create untracked resources.
 {MockRootBase rr;Root8 r(&rr);Raw n;Device8 d(&n,&r);d.visuals.effective.foliage_diagnostics=true;n.expose_unknown_device_query=true;
  GUID escaped_device_iid={0x10293847,0x1234,0x5678,{1,2,3,4,5,6,7,8}};void* escaped_device=nullptr;
  CHECK(d.QueryInterface(escaped_device_iid,&escaped_device)==S_OK&&escaped_device==static_cast<IDirect3DDevice8*>(&n));CHECK(!d.visuals.effective.foliage_diagnostics);
  static_cast<IUnknown*>(escaped_device)->Release();}
 std::cout<<"CPU upload mirrors: partial/discard coverage, failure/escape invalidation, binding retention, Reset and generation reuse: PASS\n";
}
void display_reset_provenance(){
 struct DisplayRaw:Raw {unsigned resets=0;HRESULT STDMETHODCALLTYPE Reset(D3DPRESENT_PARAMETERS*)override{++resets;return hr;}} native;
 struct DisplayRoot:MockRootBase {
  IDirect3DDevice8* device=nullptr;
  HRESULT STDMETHODCALLTYPE GetAdapterDisplayMode(UINT,D3DDISPLAYMODE* p)override{*p={1920,1080,60,D3DFMT_X8R8G8B8};return S_OK;}
  HRESULT STDMETHODCALLTYPE CheckDeviceType(UINT,D3DDEVTYPE,D3DFORMAT,D3DFORMAT,BOOL)override{return S_OK;}
  HRESULT STDMETHODCALLTYPE CreateDevice(UINT,D3DDEVTYPE,HWND,DWORD,D3DPRESENT_PARAMETERS*,IDirect3DDevice8** p)override{*p=device;return S_OK;}
 } raw_root;raw_root.device=&native;Root8 root(&raw_root);
 struct DisplayWindows:WindowApi {
  WindowState s{};std::function<void()> echo;
  DisplayWindows(){s.valid=true;s.hwnd=reinterpret_cast<HWND>(0x1234);s.style=WS_OVERLAPPEDWINDOW;s.client={0,0,640,480};s.monitor=s.work={0,0,1920,1080};}
  bool snapshot(HWND,WindowState& out)noexcept override{out=s;return true;}
  bool apply(const WindowState&,const RECT& r,bool,bool)noexcept override{s.client={0,0,r.right-r.left,r.bottom-r.top};s.outer=r;if(echo)echo();return true;}
  bool restore(const WindowState& in)noexcept override{s=in;return true;}
 } windows;
 auto policy=std::make_unique<QualityPipeline>(windows);VisualConfig config;D3DPRESENT_PARAMETERS pp{};pp.hDeviceWindow=windows.s.hwnd;pp.BackBufferWidth=640;pp.BackBufferHeight=480;pp.BackBufferFormat=D3DFMT_X8R8G8B8;pp.BackBufferCount=1;pp.Windowed=TRUE;pp.SwapEffect=D3DSWAPEFFECT_COPY;
 IDirect3DDevice8* out_device=nullptr;policy->configure(config,true,0,D3DDEVTYPE_HAL,pp.hDeviceWindow);CHECK(policy->create(raw_root,0,&pp,&out_device)==S_OK);
 Device8 device(&native,&root,std::move(policy));device.visuals.effective.foliage_diagnostics=true;
 Buffer<IDirect3DVertexBuffer8> vb;vb.desc.Size=16;vb.desc.Usage=D3DUSAGE_WRITEONLY;vb.desc.Pool=D3DPOOL_MANAGED;vb.bytes.resize(16);
 auto ptr=reinterpret_cast<uintptr_t>(&vb);auto gen=device.trace.resources.add(ptr,23,pack(16,D3DUSAGE_WRITEONLY,0x142,D3DPOOL_MANAGED)).serial;
 auto default_ptr=uintptr_t(0x7654);auto default_gen=device.trace.resources.add(default_ptr,24,pack(12,0,D3DFMT_INDEX16,D3DPOOL_DEFAULT)).serial;
 auto* proxy=new VertexBufferProxy(&device,&vb,gen);BYTE* data=nullptr;CHECK(proxy->Lock(0,16,&data,0)==S_OK);std::memset(data,9,16);CHECK(proxy->Unlock()==S_OK);
 std::vector<BYTE> captured;uint64_t revision=0;CHECK(device.copy_buffer_shadow(&vb,BufferKind::Vertex,gen,0,16,captured,revision));
 config.display_mode="Windowed";config.width=1280;config.height=720;device.quality->configure(config,true,0,D3DDEVTYPE_HAL,pp.hDeviceWindow);
 native.hr=D3DERR_DEVICELOST;CHECK(device.Reset(&pp)==D3DERR_DEVICELOST&&native.resets==1);
 CHECK(device.copy_buffer_shadow(&vb,BufferKind::Vertex,gen,0,16,captured,revision)&&device.trace.resources.generation(default_ptr)==default_gen);
 native.hr=S_OK;windows.echo=[&](){auto same=pp;CHECK(device.Reset(&same)==S_OK&&native.resets==2);
  CHECK(device.copy_buffer_shadow(&vb,BufferKind::Vertex,gen,0,16,captured,revision)&&device.trace.resources.generation(ptr)==gen&&device.trace.resources.generation(default_ptr)==default_gen);};
 CHECK(device.Reset(&pp)==S_OK&&native.resets==2&&device.quality->window_reset_echoes_suppressed==1);
 CHECK(!device.copy_buffer_shadow(&vb,BufferKind::Vertex,gen,0,16,captured,revision)&&device.trace.resources.generation(ptr)==gen&&device.trace.resources.generation(default_ptr)==0);
 CHECK(device.quality->json().find("\"successful_reset_epoch\":1")!=std::string::npos);proxy->Release();CHECK(vb.refs==0);
 std::cout<<"Display wrapper Reset: failure/commit echo preserve upload mirror and generations; real success poisons MANAGED mirror and invalidates DEFAULT metadata: PASS\n";
}
int main(){try{contracts();cpu_write_provenance();display_reset_provenance();return 0;}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
