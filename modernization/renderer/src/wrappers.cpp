#include "wrappers.hpp"
#include <new>
#include <intrin.h>
#include "menu_freeze.hpp"
namespace gfx2 {
HRESULT STDMETHODCALLTYPE Root8::QueryInterface(REFIID iid,void** out){
 HRESULT hr=real_->QueryInterface(iid,out);
 if(SUCCEEDED(hr)&&out&&*out){
  if(iid==IID_IUnknown||iid==IID_IDirect3D8){adopt();*out=static_cast<IDirect3D8*>(this);}
  else {try{session().write("{\"type\":\"unknown_query_interface\",\"interface\":\"root\",\"raw_escape_possible\":true}");}catch(...){}}
 }return hr;
}
ULONG STDMETHODCALLTYPE Root8::AddRef(){++refs_;return real_->AddRef();}
ULONG STDMETHODCALLTYPE Root8::Release(){ULONG n=real_->Release();if(--refs_==0){try{session().write("{\"type\":\"root_release\"}");}catch(...){}delete this;}return n;}
HRESULT STDMETHODCALLTYPE Root8::CreateDevice(UINT a,D3DDEVTYPE t,HWND w,DWORD f,D3DPRESENT_PARAMETERS* pp,IDirect3DDevice8** out){
 D3DPRESENT_PARAMETERS before{},after{};bool b=pp&&safe_copy(&before,pp,sizeof(before));
 std::lock_guard<std::recursive_mutex> guard(registry_mutex);
 std::unique_ptr<QualityPipeline> policy;
 try {policy=std::make_unique<QualityPipeline>();policy->configure(session().visual_config,session().compatibility.ui.supported(),a,t,w);install_menu_freeze(session().target,session().visual_config.menu_freeze);}catch(...){policy.reset();}
 HRESULT hr=policy?policy->create(*real_,f,pp,out):real_->CreateDevice(a,t,w,f,pp,out);IDirect3DDevice8* raw=nullptr;
 bool post=pp&&safe_copy(&after,pp,sizeof(after));
 if(SUCCEEDED(hr)&&out&&*out){raw=*out;auto it=devices.find(raw);
  if(it!=devices.end()){it->second->adopt();*out=it->second;}
  else {
   Device8* wrapper=new(std::nothrow)Device8(raw,this,std::move(policy));
   if(!wrapper){raw->Release();*out=nullptr;hr=E_OUTOFMEMORY;}
   else {try{devices.emplace(raw,wrapper);*out=wrapper;}catch(...){delete wrapper;raw->Release();*out=nullptr;hr=E_OUTOFMEMORY;}}
  }
 }
 uintptr_t observed_output=0;if(out)safe_copy(&observed_output,out,sizeof(observed_output));
 note_create_device(a,t,w,f,b?&before:nullptr,post?&after:nullptr,hr,reinterpret_cast<uintptr_t>(raw),observed_output);
 return hr;
}
Device8::Device8(IDirect3DDevice8* p,Root8* parent,std::unique_ptr<QualityPipeline> policy) noexcept:quality(std::move(policy)),real_(p),parent_(parent){parent_->AddRef();try{auto& s=session();D3DCAPS8 caps{};HRESULT hr=D3DERR_NOTAVAILABLE;if(s.visual_config.anisotropy)hr=real_->GetDeviceCaps(&caps);visuals.configure(s.visual_config,s.target,SUCCEEDED(hr)?&caps:nullptr,hr);
 if(!quality){quality=std::make_unique<QualityPipeline>();quality->configure(s.visual_config,s.compatibility.ui.supported(),0,D3DDEVTYPE_HAL,nullptr);}
 if(quality->config.interface_mode=="PreserveMargins"&&!ui_margins.install(s.target,true)){quality->config.interface_mode="Stock";quality->config.interface_reason=ui_margins.reason;}
 quality->ui_capability=s.compatibility.ui;
 visuals.effective.interface_mode=quality->config.interface_mode;visuals.effective.interface_reason=quality->config.interface_reason;
 visuals.effective.menu_freeze=s.visual_config.menu_freeze&&s.compatibility.freeze.supported();visuals.effective.freeze_reason=s.compatibility.freeze.reason;
 if(quality->valid){visuals.effective.display_mode=quality->display;visuals.effective.display_reason=quality->display_reason;visuals.effective.aa_mode=quality->effective.MultiSampleType==D3DMULTISAMPLE_NONE?"Stock":"MSAA";visuals.effective.aa_reason=quality->aa_reason;}
 if(quality->valid)ui_margins.dimensions(quality->effective.BackBufferWidth,quality->effective.BackBufferHeight);
 quality_trace();if(visuals.effective.fov&&!game_fov.install(s.compatibility.fov.supported(),visuals.effective)){visuals.effective.fov=false;visuals.effective.fov_reason=game_fov.status().reason;}s.write("{\"type\":\"visual_device_config\",\"requested\":"+config_json(visuals.requested)+",\"effective\":"+config_json(visuals.effective)+",\"caps_result\":"+std::to_string(static_cast<uint32_t>(hr))+",\"caps_max_anisotropy\":"+std::to_string(visuals.caps_max)+",\"min_anisotropy\":"+(visuals.min_supported?"true":"false")+",\"mag_anisotropy\":"+(visuals.mag_supported?"true":"false")+"}");}catch(...){game_fov.disable("device_config_exception");visuals.effective.anisotropy=visuals.effective.fov=visuals.effective.shadow_off=false;}}
Device8::~Device8(){game_fov.disable("device_release");parent_->Release();}
HRESULT STDMETHODCALLTYPE Device8::QueryInterface(REFIID iid,void** out){
 auto guard=trace.guard();auto args=pack(&iid,out);auto pc=reinterpret_cast<uintptr_t>(_ReturnAddress());trace.before(0,args,pc);
 HRESULT hr=real_->QueryInterface(iid,out);
 if(SUCCEEDED(hr)&&out&&*out){
  if(iid==IID_IUnknown||iid==IID_IDirect3DDevice8){adopt();*out=static_cast<IDirect3DDevice8*>(this);}
  else {try{session().write("{\"type\":\"unknown_query_interface\",\"interface\":\"device\",\"raw_escape_possible\":true}");}catch(...){}}
 }trace.after(0,args,static_cast<uint32_t>(hr),pc);return hr;
}
ULONG STDMETHODCALLTYPE Device8::AddRef(){
 auto guard=trace.guard();auto args=pack();auto pc=reinterpret_cast<uintptr_t>(_ReturnAddress());trace.before(1,args,pc);
 ++refs_;ULONG n=real_->AddRef();trace.after(1,args,n,pc);return n;
}
ULONG STDMETHODCALLTYPE Device8::Release(){
 ULONG n;bool last;
 {
  auto observer=trace.guard();auto args=pack();auto pc=reinterpret_cast<uintptr_t>(_ReturnAddress());trace.before(2,args,pc);
  {std::lock_guard<std::recursive_mutex> guard(parent_->registry_mutex);last=(--refs_==0);n=real_->Release();if(last)parent_->devices.erase(real_);}
  trace.after(2,args,n,pc);
 }
 if(last){trace.shutdown(n);delete this;}return n;
}
HRESULT STDMETHODCALLTYPE Device8::GetDirect3D(IDirect3D8** out){
 auto guard=trace.guard();auto args=pack(out);auto pc=reinterpret_cast<uintptr_t>(_ReturnAddress());trace.before(6,args,pc);
 HRESULT hr=real_->GetDirect3D(out);
 if(SUCCEEDED(hr)&&out&&*out==parent_->real()){parent_->adopt();*out=parent_;}
 else if(SUCCEEDED(hr)&&out&&*out){try{session().write("{\"type\":\"parent_mismatch\",\"raw_escape_possible\":true}");}catch(...){}}
 trace.after(6,args,static_cast<uint32_t>(hr),pc);return hr;
}
}
