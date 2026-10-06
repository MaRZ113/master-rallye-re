#include "wrappers.hpp"
#include <intrin.h>
#include <cstring>
namespace gfx2 {
namespace {
bool site(uintptr_t pc,uint32_t& rva) noexcept {
 HMODULE module=nullptr;
 if(!GetModuleHandleExW(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS|GET_MODULE_HANDLE_EX_FLAG_UNCHANGED_REFCOUNT,reinterpret_cast<LPCWSTR>(pc),&module)||module!=GetModuleHandleW(nullptr))return false;
 auto base=reinterpret_cast<uintptr_t>(module);if(pc<base||pc-base>UINT32_MAX)return false;rva=static_cast<uint32_t>(pc-base);return true;
}
}
HRESULT STDMETHODCALLTYPE Device8::SetTextureStageState(DWORD stage,D3DTEXTURESTAGESTATETYPE type,DWORD value){
 auto guard=trace.guard();auto args=pack(stage,type,value);auto pc=reinterpret_cast<uintptr_t>(_ReturnAddress());trace.before(63,args,pc);
 DWORD effective=visuals.filter(stage,type,value);
 if(effective!=value&&(type==D3DTSS_MINFILTER||type==D3DTSS_MAGFILTER)){
  auto& max=trace.effective_shadow.tss[0][D3DTSS_MAXANISOTROPY];
  if(!max.known||max.value!=visuals.effective.max_anisotropy){
   DWORD requested_max=visuals.effective.max_anisotropy;HRESULT extra=real_->SetTextureStageState(0,D3DTSS_MAXANISOTROPY,requested_max);
   auto native=pack(0,D3DTSS_MAXANISOTROPY,requested_max);trace.after(63,native,static_cast<uint32_t>(extra),pc,&native,1,false,true);
   if(SUCCEEDED(extra)&&!trace.shadow.tss[0][D3DTSS_MAXANISOTROPY].known)trace.shadow.tss[0][D3DTSS_MAXANISOTROPY].set(1); // D3D8 initial/reset default; not a game setter.
   if(FAILED(extra)){effective=value;visuals.effective.anisotropy=false;try{visuals.effective.af_reason="native_max_anisotropy_rejected";session().write("{\"type\":\"visual_feature_disabled\",\"effective\":"+config_json(visuals.effective)+"}");}catch(...){}} // Original setter still runs stock.
  }
 }
 auto native=pack(stage,type,effective);HRESULT hr=real_->SetTextureStageState(stage,type,effective);
 if(FAILED(hr)&&effective!=value){trace.after(63,native,static_cast<uint32_t>(hr),pc,&native,1,false,true);effective=value;native=args;hr=real_->SetTextureStageState(stage,type,value);}
 trace.after(63,args,static_cast<uint32_t>(hr),pc,&native,effective!=value?1:0);return hr;
}
HRESULT STDMETHODCALLTYPE Device8::GetTextureStageState(DWORD stage,D3DTEXTURESTAGESTATETYPE type,DWORD* value){
 auto guard=trace.guard();auto args=pack(stage,type,value);auto pc=reinterpret_cast<uintptr_t>(_ReturnAddress());trace.before(62,args,pc);
 HRESULT hr=real_->GetTextureStageState(stage,type,value);DWORD native_value=0;bool virtualized=false;
 if(SUCCEEDED(hr)&&stage<8&&type<64&&safe_copy(&native_value,value,4)){
  const auto& logical=trace.shadow.tss[stage][type];const auto& native=trace.effective_shadow.tss[stage][type];
  if(logical.known&&native.known&&logical.value!=native.value)virtualized=safe_copy(value,&logical.value,4);
 }
 auto effective_args=virtualized?pack(stage,type,&native_value):args;
 trace.after(62,args,static_cast<uint32_t>(hr),pc,&effective_args,virtualized?1:0);return hr;
}
HRESULT STDMETHODCALLTYPE Device8::SetTransform(D3DTRANSFORMSTATETYPE type,const D3DMATRIX* input){
 auto guard=trace.guard();auto args=pack(type,input);auto pc=reinterpret_cast<uintptr_t>(_ReturnAddress());trace.before(37,args,pc);
 D3DMATRIX changed{};uint32_t rva=0;bool exe=site(pc,rva);bool rewritten=visuals.effective.fov&&visuals.projection(type,input,changed,exe,rva);
 const D3DMATRIX* forwarded=rewritten?&changed:input;auto native=pack(type,forwarded);
 HRESULT hr=real_->SetTransform(type,forwarded);if(FAILED(hr)&&rewritten){trace.after(37,native,static_cast<uint32_t>(hr),pc,&native,2,false,true);native=args;hr=real_->SetTransform(type,input);rewritten=false;}trace.after(37,args,static_cast<uint32_t>(hr),pc,&native,rewritten?2:0);return hr;
}
HRESULT STDMETHODCALLTYPE Device8::GetTransform(D3DTRANSFORMSTATETYPE type,D3DMATRIX* out){
 auto guard=trace.guard();auto args=pack(type,out);auto pc=reinterpret_cast<uintptr_t>(_ReturnAddress());trace.before(38,args,pc);
 HRESULT hr=real_->GetTransform(type,out);D3DMATRIX native_value{};bool virtualized=false;
 if(SUCCEEDED(hr)&&type<512&&safe_copy(&native_value,out,sizeof(native_value))){
  const auto& logical=trace.shadow.matrices[type];const auto& native=trace.effective_shadow.matrices[type];
  if(logical.known&&native.known&&std::memcmp(&logical.value,&native.value,sizeof(native_value)))virtualized=safe_copy(out,&logical.value,sizeof(native_value));
 }
 auto effective_args=virtualized?pack(type,&native_value):args;
 trace.after(38,args,static_cast<uint32_t>(hr),pc,&effective_args,virtualized?2:0);return hr;
}
HRESULT STDMETHODCALLTYPE Device8::DrawPrimitive(D3DPRIMITIVETYPE type,UINT start,UINT count){
 auto guard=trace.guard();auto args=pack(type,start,count);auto pc=reinterpret_cast<uintptr_t>(_ReturnAddress());trace.before(70,args,pc);
 uint32_t rva=0;bool exe=site(pc,rva);bool skip=visuals.suppress(70,exe,rva,trace.shadow,type);
 HRESULT hr=skip?S_OK:real_->DrawPrimitive(type,start,count);
 trace.after(70,args,static_cast<uint32_t>(hr),pc,nullptr,skip?4:0,skip);return hr;
}
HRESULT Device8::stock_for_unmapped(const char* reason) noexcept {
 if(!visuals.active())return S_OK;
 // Canonical tested path uses no state blocks. Restore before entering an unreviewed block/multiply path,
 // then keep this device stock. If restoration fails, report that real HRESULT rather than hide leakage.
 const DWORD keys[]={16,17,18,21};
 for(DWORD key:keys){auto& logical=trace.shadow.tss[0][key];auto& native=trace.effective_shadow.tss[0][key];
  if(logical.known&&native.known&&logical.value!=native.value){auto args=pack(0,key,logical.value);HRESULT hr=real_->SetTextureStageState(0,static_cast<D3DTEXTURESTAGESTATETYPE>(key),logical.value);trace.after(63,args,static_cast<uint32_t>(hr),0,&args,1,false,true);if(FAILED(hr))return hr;}
 }
 auto& logical=trace.shadow.matrices[3];auto& native=trace.effective_shadow.matrices[3];
 if(logical.known&&native.known&&std::memcmp(&logical.value,&native.value,sizeof(D3DMATRIX))){auto args=pack(D3DTS_PROJECTION,&logical.value);HRESULT hr=real_->SetTransform(D3DTS_PROJECTION,&logical.value);trace.after(37,args,static_cast<uint32_t>(hr),0,&args,2,false,true);if(FAILED(hr))return hr;}
 visuals.effective.anisotropy=visuals.effective.fov=visuals.effective.shadow_off=false;
 try{session().write("{\"type\":\"visual_fallback_stock\",\"reason\":"+quote(reason)+"}");}catch(...){}
 return S_OK;
}
}
