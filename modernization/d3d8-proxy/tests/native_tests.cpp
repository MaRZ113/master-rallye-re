#include "wrappers.hpp"
#include <iostream>
#include <stdexcept>
#include <thread>
#include <cfenv>
#define CHECK(x) do {if(!(x))throw std::runtime_error(#x);}while(0)
#include "mock_interfaces.hpp"
using namespace gfx2;
struct MockRoot;
struct MockDevice final:MockDeviceBase {
 ULONG refs=1;MockRoot* parent=nullptr;
 HRESULT STDMETHODCALLTYPE QueryInterface(REFIID iid,void** out) override {
  if(!out)return E_POINTER;*out=nullptr;
  if(iid!=IID_IUnknown&&iid!=IID_IDirect3DDevice8)return E_NOINTERFACE;
  *out=this;AddRef();return S_OK;
 }
 ULONG STDMETHODCALLTYPE AddRef() override {return ++refs;}
 ULONG STDMETHODCALLTYPE Release() override {CHECK(refs>0);return --refs;}
 HRESULT STDMETHODCALLTYPE GetDirect3D(IDirect3D8** out) override;
 HRESULT STDMETHODCALLTYPE CreateTexture(UINT w,UINT h,UINT levels,DWORD usage,D3DFORMAT format,D3DPOOL pool,IDirect3DTexture8** out) override {
  if(reinterpret_cast<uintptr_t>(out)<0x10000){last=20;observed=pack(w,h,levels,usage,format,pool,out);return hr;}
  CHECK(w==64&&h==32&&levels==0&&usage==0&&format==D3DFMT_A8R8G8B8&&pool==D3DPOOL_MANAGED);
  *out=reinterpret_cast<IDirect3DTexture8*>(0x11223344);return S_OK;
 }
};
struct MockRoot final:MockRootBase {
 ULONG refs=1;MockDevice* device=nullptr;D3DPRESENT_PARAMETERS* received=nullptr;DWORD flags=0;
 HRESULT STDMETHODCALLTYPE QueryInterface(REFIID iid,void** out) override {
  if(!out)return E_POINTER;*out=nullptr;
  if(iid!=IID_IUnknown&&iid!=IID_IDirect3D8)return E_NOINTERFACE;
  *out=this;AddRef();return S_OK;
 }
 ULONG STDMETHODCALLTYPE AddRef() override {return ++refs;}
 ULONG STDMETHODCALLTYPE Release() override {CHECK(refs>0);return --refs;}
 HRESULT STDMETHODCALLTYPE CreateDevice(UINT a,D3DDEVTYPE t,HWND hwnd,DWORD f,D3DPRESENT_PARAMETERS* pp,IDirect3DDevice8** out) override {
  CHECK(a==2&&t==D3DDEVTYPE_HAL&&hwnd==reinterpret_cast<HWND>(0x1234));received=pp;flags=f;
  if(reinterpret_cast<uintptr_t>(out)<0x10000)return E_POINTER;
  pp->BackBufferCount=1;*out=device;return S_OK;
 }
};
HRESULT MockDevice::GetDirect3D(IDirect3D8** out){if(!out)return E_POINTER;*out=parent;parent->AddRef();return S_OK;}
void com_contracts(){
 MockRoot raw;MockDevice dev;raw.device=&dev;dev.parent=&raw;auto* root=new Root8(&raw);
 void* unknown=nullptr;CHECK(root->QueryInterface(IID_IUnknown,&unknown)==S_OK&&unknown==root);
 CHECK(static_cast<IUnknown*>(unknown)->Release()==1);
 D3DPRESENT_PARAMETERS pp{};pp.BackBufferCount=7;IDirect3DDevice8* device=nullptr;
 CHECK(root->CreateDevice(2,D3DDEVTYPE_HAL,reinterpret_cast<HWND>(0x1234),0x20,&pp,reinterpret_cast<IDirect3DDevice8**>(1))==E_POINTER);
 CHECK(pp.BackBufferCount==7);
 CHECK(root->CreateDevice(2,D3DDEVTYPE_HAL,reinterpret_cast<HWND>(0x1234),0x20,&pp,&device)==S_OK);
 CHECK(raw.received==&pp&&raw.flags==0x20&&pp.BackBufferCount==1&&device!=&dev);
 CHECK(device->QueryInterface(IID_IUnknown,&unknown)==S_OK&&unknown==device);
 CHECK(static_cast<IUnknown*>(unknown)->Release()==1);
 void* same=nullptr;CHECK(device->QueryInterface(IID_IDirect3DDevice8,&same)==S_OK&&same==device);
 static_cast<IDirect3DDevice8*>(same)->Release();
 CHECK(device->QueryInterface(IID_IDirect3D8,&same)==E_NOINTERFACE&&same==nullptr);
 IDirect3D8* returned=nullptr;CHECK(device->GetDirect3D(&returned)==S_OK&&returned==root);returned->Release();
 // Exercise every remaining ABI slot with unique scalar/pointer arguments, no GPU.
 test_all_MockRootBase(root,raw);test_all_MockDeviceBase(device,dev);
 static_cast<Device8*>(device)->trace.control.pending=true;
 CHECK(device->Present(nullptr,nullptr,nullptr,nullptr)==dev.hr);
 CHECK(device->BeginScene()==dev.hr);CHECK(device->DrawPrimitive(D3DPT_TRIANGLELIST,0,1)==dev.hr);CHECK(device->EndScene()==dev.hr);
 CHECK(device->Present(nullptr,nullptr,nullptr,nullptr)==dev.hr);
 IDirect3DTexture8* texture=nullptr;CHECK(device->CreateTexture(64,32,0,0,D3DFMT_A8R8G8B8,D3DPOOL_MANAGED,&texture)==S_OK);
 CHECK(texture==reinterpret_cast<IDirect3DTexture8*>(0x11223344));
 CHECK(static_cast<Device8*>(device)->trace.resources.generation(reinterpret_cast<uintptr_t>(texture))==1);
 // External parent can be released before the device, without invalidating GetDirect3D.
 CHECK(root->Release()==1);CHECK(device->GetDirect3D(&returned)==S_OK&&returned==root);returned->Release();
 CHECK(device->Release()==0&&dev.refs==0&&raw.refs==0);
 std::cout<<"COM identity, parent lifetime, 105 forward-only ABI slots: PASS\n";
}
void shadow_contracts(){
 CHECK(!caller_info(1).known);auto owner=caller_info(reinterpret_cast<uintptr_t>(&shadow_contracts));
 CHECK(owner.known&&owner.base==reinterpret_cast<uintptr_t>(GetModuleHandleW(nullptr)));
 Shadow s;CHECK(!s.rs[7].known);s.update(50,pack(7,1),S_OK);CHECK(s.rs[7].known&&s.rs[7].value==1);
 s.update(50,pack(7,2),0x80004005);CHECK(s.rs[7].value==1);
 D3DMATRIX matrix{};matrix._11=1.25f;matrix._44=1;s.update(37,pack(2,&matrix),S_OK);
 CHECK(s.snapshot().matrices[1].known&&s.snapshot().matrices[1].value._11==1.25f);
 s.update(39,pack(2,&matrix),S_OK);CHECK(!s.matrices[2].known);
 s.update(83,pack(0,reinterpret_cast<IDirect3DVertexBuffer8*>(0x1234),28),S_OK);
 s.update(85,pack(reinterpret_cast<IDirect3DIndexBuffer8*>(0x2345),8),S_OK);
 s.update(73,pack(0,0,0,0,0,0,0,0),S_OK);CHECK(s.bindings.streams[0].known&&s.bindings.streams[0].value.pointer==0&&s.bindings.indices.value.pointer==0);
 s.update(52,pack(),S_OK);s.update(50,pack(7,2),S_OK);CHECK(!s.rs[7].known&&s.recording);
 s.update(53,pack(),S_OK);s.update(50,pack(7,2),S_OK);CHECK(s.rs[7].value==2);
 s.update(54,pack(1),S_OK);CHECK(!s.rs[7].known);
 s.update(50,pack(7,3),S_OK);s.update(14,pack(nullptr),0x88760868);CHECK(s.rs[7].known);
 s.update(14,pack(nullptr),S_OK);CHECK(!s.rs[7].known);
 s.update(83,pack(0,0x1234,28),S_OK);s.update(84,pack(0,1,1),S_OK);CHECK(!s.bindings.streams[0].known);
 uint32_t dst=0;CHECK(!safe_copy(&dst,reinterpret_cast<void*>(1),4));
 ResourceRegistry registry;CHECK(registry.generation(0x100)==0);auto r=registry.add(0x100,20,pack());
 CHECK(registry.add(0x100,20,pack()).serial>r.serial);
 for(uintptr_t i=1;i<9000;++i)registry.add(i,20,pack());CHECK(registry.items.size()<=8192);
 std::cout<<"State failure/reset/state blocks/UP/resource reuse: PASS\n";
}
void capture_contracts(){
 CaptureControl c;c.poll(true);CHECK(c.pending&&!c.active);c.finish_present();CHECK(c.active&&!c.pending);
 c.poll(true);c.finish_present();CHECK(!c.active);c.poll(false);c.poll(true);c.finish_present();CHECK(c.active);
 c.abort();CHECK(!c.active&&!c.pending);
 Trace trace;CHECK(trace.enabled);trace.control.pending=true;
 std::thread workers[4];
 for(auto& worker:workers)worker=std::thread([&](){for(uint32_t i=0;i<1000;++i){auto guard=trace.guard();trace.before(50,pack(7,i),0);trace.after(50,pack(7,i),S_OK,0);}});
 for(auto& worker:workers)worker.join();CHECK(trace.shadow.rs[7].known&&trace.shadow.rs[7].value==999);
 trace.before(15,pack(nullptr,nullptr,nullptr,nullptr),0);trace.after(15,pack(nullptr,nullptr,nullptr,nullptr),S_OK,0);
 CHECK(trace.control.active);
 auto pc=reinterpret_cast<uintptr_t>(&capture_contracts);
 D3DMATRIX m{};m._11=m._22=m._33=m._44=1;
 trace.before(37,pack(2,&m),pc);trace.after(37,pack(2,&m),S_OK,pc);
 fesetround(FE_DOWNWARD);trace.before(70,pack(D3DPT_TRIANGLELIST,0,1),pc);trace.after(70,pack(D3DPT_TRIANGLELIST,0,1),S_OK,pc);CHECK(fegetround()==FE_DOWNWARD);fesetround(FE_TONEAREST);
 trace.before(15,pack(nullptr,nullptr,nullptr,nullptr),pc);trace.after(15,pack(nullptr,nullptr,nullptr,nullptr),S_OK,pc);CHECK(!trace.control.active);
 trace.control.pending=true;trace.after(15,pack(nullptr,nullptr,nullptr,nullptr),S_OK,pc);
 for(size_t i=0;i<MAX_DRAWS+2;++i){trace.before(70,pack(D3DPT_TRIANGLELIST,0,1),pc);trace.after(70,pack(D3DPT_TRIANGLELIST,0,1),S_OK,pc);}
 trace.after(15,pack(nullptr,nullptr,nullptr,nullptr),S_OK,pc);CHECK(!trace.control.active);
 // Output failure cannot change the forwarding/observer control path.
 auto saved=session().directory;session().directory=L"Z:\\R-GFX2-NONEXISTENT\\logs";
 trace.control.pending=true;trace.after(15,pack(nullptr,nullptr,nullptr,nullptr),S_OK,pc);trace.after(15,pack(nullptr,nullptr,nullptr,nullptr),S_OK,pc);session().directory=saved;
 std::cout<<"F10 debounce, complete interval, bounded overflow, failed output, FPU preservation, concurrent observation: PASS\n";
}
int main(){try{com_contracts();shadow_contracts();capture_contracts();std::cout<<"SYNTHETIC ONLY; no game or GPU runtime tested\n";return 0;}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
