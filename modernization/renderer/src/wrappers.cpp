#include "wrappers.hpp"
#include "buffer_provenance.hpp"
#include <new>
#include <intrin.h>
#include "menu_freeze.hpp"
#include "free_camera.hpp"
namespace gfx2 {
HRESULT STDMETHODCALLTYPE Root8::QueryInterface(REFIID iid,void** out){
 HRESULT hr=real_->QueryInterface(iid,out);
 if(SUCCEEDED(hr)&&out&&*out){
  if(iid==IID_IUnknown||iid==IID_IDirect3D8){adopt();*out=static_cast<IDirect3D8*>(this);}
  else {
   auto& s=session();s.foliage_provenance_available.store(false,std::memory_order_relaxed);
   {std::lock_guard<std::recursive_mutex> guard(registry_mutex);for(auto& item:devices)if(item.second)item.second->visuals.effective.foliage_diagnostics=false;}
   try{s.write("{\"type\":\"unknown_query_interface\",\"interface\":\"root\",\"raw_escape_possible\":true,\"foliage_provenance_disabled\":true}");}catch(...){}
  }
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
 visuals.effective.fov=s.visual_config.fov&&s.compatibility.fov.supported();visuals.effective.fov_reason=s.compatibility.fov.reason;
 visuals.effective.reflection_mode=s.compatibility.vehicle.supported()?s.visual_config.reflection_mode:"Stock";visuals.effective.reflection_reason=s.compatibility.vehicle.reason;
 if(!quality){quality=std::make_unique<QualityPipeline>();quality->configure(s.visual_config,s.compatibility.ui.supported(),0,D3DDEVTYPE_HAL,nullptr);}
 if(quality->config.interface_mode=="PreserveMargins"&&!ui_margins.install(s.compatibility.margins.supported(),true)){quality->config.interface_mode="Stock";quality->config.interface_reason=ui_margins.reason;}
 // The accepted row signature is exact-retail only; ordinary margins
 // keep their existing feature-local compatibility on modified executables.
 ui_margins.configure_carousel_alignment(quality->config.interface_mode=="PreserveMargins",s.target);
 quality->ui_capability=s.compatibility.ui;quality->preview_capability=s.compatibility.preview;quality->preview_capability.candidate_rva=GAMEPLAY_PROJECTION_RETURN_RVA;
 visuals.effective.interface_mode=quality->config.interface_mode;visuals.effective.interface_reason=quality->config.interface_reason;
 visuals.effective.menu_freeze=s.visual_config.menu_freeze&&s.compatibility.freeze.supported();visuals.effective.freeze_reason=s.compatibility.freeze.reason;
 if(!s.foliage_provenance_available.load(std::memory_order_relaxed))visuals.effective.foliage_diagnostics=false;
 if(quality->valid){visuals.effective.display_mode=quality->display;visuals.effective.display_reason=quality->display_reason;visuals.effective.aa_mode=quality->effective.MultiSampleType==D3DMULTISAMPLE_NONE?"Stock":"MSAA";visuals.effective.aa_reason=quality->aa_reason;}
 if(quality->valid)ui_margins.dimensions(quality->effective.BackBufferWidth,quality->effective.BackBufferHeight);
 quality_trace();bool flight=parse_free_camera_config(s.visual_config.raw_fields).enabled&&s.target&&s.visual_config.version_ok;if(s.target&&(s.enabled||flight)){install_race_observer(true,true);race_observer_attached=true;}if((visuals.effective.fov||flight)&&!game_fov.install(s.compatibility.fov.supported()||s.target,visuals.effective,quality->effective.hDeviceWindow?quality->effective.hDeviceWindow:quality->focus,s.target)){visuals.effective.fov=false;visuals.effective.fov_reason=game_fov.status().reason;}s.write("{\"type\":\"visual_device_config\",\"requested\":"+config_json(visuals.requested)+",\"effective\":"+config_json(visuals.effective)+",\"caps_result\":"+std::to_string(static_cast<uint32_t>(hr))+",\"caps_max_anisotropy\":"+std::to_string(visuals.caps_max)+",\"min_anisotropy\":"+(visuals.min_supported?"true":"false")+",\"mag_anisotropy\":"+(visuals.mag_supported?"true":"false")+"}");}catch(...){game_fov.disable("device_config_exception");visuals.effective.anisotropy=visuals.effective.fov=visuals.effective.shadow_off=false;}}
Device8::~Device8(){game_fov.disable("device_release");if(race_observer_attached)release_race_observer();parent_->Release();}
IDirect3DVertexBuffer8* Device8::wrap_vertex_buffer(IDirect3DVertexBuffer8* raw) noexcept {
 if(!raw||!visuals.effective.foliage_diagnostics)return raw;
 std::lock_guard<std::recursive_mutex> l(buffer_mutex_);auto i=buffer_proxies_.find(raw);if(i!=buffer_proxies_.end()&&i->second&&i->second->kind()==BufferKind::Vertex){auto* p=static_cast<VertexBufferProxy*>(i->second->proxy_pointer());if(p->core().generation()!=trace.resources.generation(reinterpret_cast<uintptr_t>(raw))){invalidate_buffer_shadow(raw,"buffer_generation_changed_raw_escape");return raw;}p->AddRef();raw->Release();return p;}
 if(buffer_proxies_.size()>=8192){invalidate_buffer_shadow(raw,"buffer_proxy_count_limit_raw_escape");return raw;}
 auto* p=new(std::nothrow)VertexBufferProxy(this,raw,trace.resources.generation(reinterpret_cast<uintptr_t>(raw)));
 if(!p){invalidate_buffer_shadow(raw,"buffer_proxy_allocation_failed_raw_escape");return raw;}
 if(!p->core().registered()) { raw->AddRef(); p->Release(); invalidate_buffer_shadow(raw,"buffer_proxy_registration_failed_raw_escape"); return raw; }
 return static_cast<IDirect3DVertexBuffer8*>(p);
}
IDirect3DIndexBuffer8* Device8::wrap_index_buffer(IDirect3DIndexBuffer8* raw) noexcept {
 if(!raw||!visuals.effective.foliage_diagnostics)return raw;
 std::lock_guard<std::recursive_mutex> l(buffer_mutex_);auto i=buffer_proxies_.find(raw);if(i!=buffer_proxies_.end()&&i->second&&i->second->kind()==BufferKind::Index){auto* p=static_cast<IndexBufferProxy*>(i->second->proxy_pointer());if(p->core().generation()!=trace.resources.generation(reinterpret_cast<uintptr_t>(raw))){invalidate_buffer_shadow(raw,"buffer_generation_changed_raw_escape");return raw;}p->AddRef();raw->Release();return p;}
 if(buffer_proxies_.size()>=8192){invalidate_buffer_shadow(raw,"buffer_proxy_count_limit_raw_escape");return raw;}
 auto* p=new(std::nothrow)IndexBufferProxy(this,raw,trace.resources.generation(reinterpret_cast<uintptr_t>(raw)));
 if(!p){invalidate_buffer_shadow(raw,"buffer_proxy_allocation_failed_raw_escape");return raw;}
 if(!p->core().registered()) { raw->AddRef(); p->Release(); invalidate_buffer_shadow(raw,"buffer_proxy_registration_failed_raw_escape"); return raw; }
 return static_cast<IDirect3DIndexBuffer8*>(p);
}
IDirect3DVertexBuffer8* Device8::unwrap_vertex_buffer(IDirect3DVertexBuffer8* buffer) noexcept {if(!buffer)return nullptr;std::lock_guard<std::recursive_mutex> l(buffer_mutex_);auto i=buffer_proxy_interfaces_.find(buffer);if(i==buffer_proxy_interfaces_.end()||!i->second||i->second->kind()!=BufferKind::Vertex)return buffer;return static_cast<VertexBufferProxy*>(i->second->proxy_pointer())->raw();}
IDirect3DIndexBuffer8* Device8::unwrap_index_buffer(IDirect3DIndexBuffer8* buffer) noexcept {if(!buffer)return nullptr;std::lock_guard<std::recursive_mutex> l(buffer_mutex_);auto i=buffer_proxy_interfaces_.find(buffer);if(i==buffer_proxy_interfaces_.end()||!i->second||i->second->kind()!=BufferKind::Index)return buffer;return static_cast<IndexBufferProxy*>(i->second->proxy_pointer())->raw();}
bool Device8::register_buffer_proxy(void* raw,BufferProxyCore* p) noexcept {
 if(!raw||!p)return false;
 try {
  std::lock_guard<std::recursive_mutex> l(buffer_mutex_);
  if(buffer_proxies_.count(raw)||buffer_proxy_interfaces_.count(p->proxy_pointer()))return false;
  auto raw_entry=buffer_proxies_.emplace(raw,p);
  if(!raw_entry.second)return false;
  try {
   auto proxy_entry=buffer_proxy_interfaces_.emplace(p->proxy_pointer(),p);
   if(!proxy_entry.second){buffer_proxies_.erase(raw_entry.first);return false;}
  } catch(...) {
   buffer_proxies_.erase(raw_entry.first);
   return false;
  }
  return true;
 } catch(...) { return false; }
}
void Device8::forget_buffer_proxy(void* raw,BufferProxyCore* p) noexcept {std::lock_guard<std::recursive_mutex> l(buffer_mutex_);auto i=buffer_proxies_.find(raw);if(i!=buffer_proxies_.end()&&i->second==p)buffer_proxies_.erase(i);auto q=buffer_proxy_interfaces_.find(p?p->proxy_pointer():nullptr);if(q!=buffer_proxy_interfaces_.end()&&q->second==p)buffer_proxy_interfaces_.erase(q);discard_unbound_buffer_mirror_locked(raw);}
std::shared_ptr<BufferMirror> Device8::open_buffer_mirror(void* raw,BufferKind kind,uint64_t gen,UINT bytes,DWORD usage,D3DPOOL pool) noexcept {
 if(!raw||!gen||!bytes)return {};
 std::lock_guard<std::recursive_mutex> l(buffer_mutex_);auto i=buffer_mirrors_.find(raw);
 if(i!=buffer_mirrors_.end()&&i->second&&i->second->kind==kind&&i->second->generation==gen&&i->second->bytes==bytes&&i->second->usage==usage&&i->second->pool==pool)return i->second;
 if(i!=buffer_mirrors_.end()){
  if(i->second&&i->second->available)buffer_shadow_bytes_=i->second->bytes>buffer_shadow_bytes_?0:buffer_shadow_bytes_-i->second->bytes;
  buffer_mirrors_.erase(i);
 }
 if(buffer_mirrors_.size()>=8192)return {};
 std::shared_ptr<BufferMirror> mirror;bool accounted=false;
 try{
  mirror=std::make_shared<BufferMirror>();mirror->kind=kind;mirror->generation=gen;mirror->bytes=bytes;mirror->usage=usage;mirror->pool=pool;
  constexpr uint64_t MAX_BUFFER_MIRROR_BYTES=8ull*1024*1024,MAX_DEVICE_MIRROR_BYTES=32ull*1024*1024;
  if(bytes<=MAX_BUFFER_MIRROR_BYTES&&buffer_shadow_bytes_<=MAX_DEVICE_MIRROR_BYTES-bytes){
   mirror->data.resize(bytes);mirror->available=true;buffer_shadow_bytes_+=bytes;accounted=true;
  }else{mirror->poisoned=true;mirror->poison_reason="cpu_mirror_capacity_exceeded";}
  buffer_mirrors_.emplace(raw,mirror);return mirror;
 }catch(...){if(accounted)buffer_shadow_bytes_=bytes>buffer_shadow_bytes_?0:buffer_shadow_bytes_-bytes;return {};}
}
bool Device8::copy_buffer_shadow(void* raw,BufferKind kind,uint64_t gen,uint64_t offset,size_t size,std::vector<BYTE>& out,uint64_t& revision) noexcept {
 std::lock_guard<std::recursive_mutex> l(buffer_mutex_);auto i=buffer_mirrors_.find(raw);if(i==buffer_mirrors_.end()||!i->second)return false;
 auto& mirror=*i->second;std::lock_guard<std::mutex> m(mirror.mutex);revision=mirror.revision;
 if(!mirror.available||mirror.poisoned||mirror.kind!=kind||mirror.generation!=gen||offset>mirror.bytes||size>mirror.bytes-offset)return false;
 const uint64_t end=offset+size;bool covered=size==0;
 for(const auto& r:mirror.initialized)if(offset>=r.begin&&end<=r.end){covered=true;break;}
 if(!covered)return false;
 try{out.assign(mirror.data.begin()+static_cast<size_t>(offset),mirror.data.begin()+static_cast<size_t>(end));return true;}catch(...){out.clear();return false;}
}
void Device8::invalidate_buffer_shadow(void* raw,const char* reason) noexcept {std::lock_guard<std::recursive_mutex> l(buffer_mutex_);auto i=buffer_mirrors_.find(raw);if(i==buffer_mirrors_.end()||!i->second)return;auto& mirror=*i->second;std::lock_guard<std::mutex> m(mirror.mutex);mirror.poisoned=true;mirror.initialized.clear();if(mirror.revision!=UINT64_MAX)++mirror.revision;try{mirror.poison_reason=reason?reason:"external_gpu_write";}catch(...){mirror.poison_reason.clear();}}
void Device8::invalidate_all_buffer_shadows(const char* reason) noexcept {std::lock_guard<std::recursive_mutex> l(buffer_mutex_);for(auto& entry:buffer_mirrors_){if(!entry.second)continue;auto& mirror=*entry.second;std::lock_guard<std::mutex> m(mirror.mutex);mirror.poisoned=true;mirror.initialized.clear();if(mirror.revision!=UINT64_MAX)++mirror.revision;try{mirror.poison_reason=reason?reason:"device_reset";}catch(...){mirror.poison_reason.clear();}}stream_buffers_.fill(nullptr);index_buffer_=nullptr;for(auto i=buffer_mirrors_.begin();i!=buffer_mirrors_.end();){if(!buffer_proxies_.count(i->first)){auto raw=i->first;++i;discard_unbound_buffer_mirror_locked(raw);}else ++i;}}
void Device8::discard_unbound_buffer_mirror_locked(void* raw) noexcept {if(!raw||buffer_proxies_.count(raw))return;bool bound=index_buffer_==raw;for(auto p:stream_buffers_)bound=bound||p==raw;if(bound)return;auto i=buffer_mirrors_.find(raw);if(i==buffer_mirrors_.end())return;if(i->second&&i->second->available)buffer_shadow_bytes_=i->second->bytes>buffer_shadow_bytes_?0:buffer_shadow_bytes_-i->second->bytes;buffer_mirrors_.erase(i);}
void Device8::note_stream_buffer_binding(UINT stream,void* raw,HRESULT result) noexcept {if(FAILED(result)||stream>=stream_buffers_.size())return;std::lock_guard<std::recursive_mutex> l(buffer_mutex_);void* old=stream_buffers_[stream];stream_buffers_[stream]=raw;if(old!=raw)discard_unbound_buffer_mirror_locked(old);}
void Device8::note_index_buffer_binding(void* raw,HRESULT result) noexcept {if(FAILED(result))return;std::lock_guard<std::recursive_mutex> l(buffer_mutex_);void* old=index_buffer_;index_buffer_=raw;if(old!=raw)discard_unbound_buffer_mirror_locked(old);}
bool Device8::reserve_buffer_copy_bytes(size_t n) noexcept {std::lock_guard<std::recursive_mutex> l(buffer_mutex_);uint64_t frame=trace.frame_number();if(buffer_copy_frame_!=frame){buffer_copy_frame_=frame;buffer_copy_bytes_=0;}if(n>16ull*1024*1024||buffer_copy_bytes_>16ull*1024*1024-n)return false;buffer_copy_bytes_+=n;return true;}
HRESULT STDMETHODCALLTYPE Device8::QueryInterface(REFIID iid,void** out){
 auto guard=trace.guard();auto args=pack(&iid,out);auto pc=reinterpret_cast<uintptr_t>(_ReturnAddress());trace.before(0,args,pc);
 HRESULT hr=real_->QueryInterface(iid,out);
 if(SUCCEEDED(hr)&&out&&*out){
  if(iid==IID_IUnknown||iid==IID_IDirect3DDevice8){adopt();*out=static_cast<IDirect3DDevice8*>(this);}
  else {if(visuals.effective.foliage_diagnostics){visuals.effective.foliage_diagnostics=false;session().foliage_provenance_available.store(false,std::memory_order_relaxed);invalidate_all_buffer_shadows("device_unknown_query_interface_raw_escape");}try{session().write("{\"type\":\"unknown_query_interface\",\"interface\":\"device\",\"raw_escape_possible\":true,\"foliage_provenance_disabled\":true}");}catch(...){}}
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
  {std::lock_guard<std::recursive_mutex> guard(parent_->registry_mutex);last=(--refs_==0);if(last&&quality)quality->begin_shutdown();n=real_->Release();if(last)parent_->devices.erase(real_);}
  trace.after(2,args,n,pc);
 }
 if(last){trace.shutdown(n);ui_margins.capture_window(false,trace.frame_number(),trace.device_id(),"device_release");delete this;}return n;
}
HRESULT STDMETHODCALLTYPE Device8::GetDirect3D(IDirect3D8** out){
 auto guard=trace.guard();auto args=pack(out);auto pc=reinterpret_cast<uintptr_t>(_ReturnAddress());trace.before(6,args,pc);
 HRESULT hr=real_->GetDirect3D(out);
 if(SUCCEEDED(hr)&&out&&*out==parent_->real()){parent_->adopt();*out=parent_;}
 else if(SUCCEEDED(hr)&&out&&*out){try{session().write("{\"type\":\"parent_mismatch\",\"raw_escape_possible\":true}");}catch(...){}}
 trace.after(6,args,static_cast<uint32_t>(hr),pc);return hr;
}
}
