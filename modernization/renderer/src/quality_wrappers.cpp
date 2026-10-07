#include "wrappers.hpp"
#include <intrin.h>
#include <cstring>
namespace gfx2 {
void Device8::quality_trace() noexcept {
 try{if(quality){trace.quality_metadata=quality->json();trace.ui_metadata=ui_margins.json();session().write("{\"type\":\"quality_pipeline\",\"descriptor\":"+trace.quality_metadata+",\"ui_margins\":"+trace.ui_metadata+"}");}}catch(...){}
}
HRESULT Device8::stock_ui(const char* reason) noexcept {
 if(quality){quality->config.interface_mode="Stock";quality->config.interface_reason=reason;}
 ui_margins.disable(reason);HRESULT hr=S_OK;
 const auto& logical=trace.shadow.matrices[D3DTS_PROJECTION];const auto& effective=trace.effective_shadow.matrices[D3DTS_PROJECTION];
 if(logical.known&&effective.known&&stock_ui_projection(logical.value)&&std::memcmp(&logical.value,&effective.value,sizeof(D3DMATRIX))){
  auto args=pack(D3DTS_PROJECTION,&logical.value);hr=real_->SetTransform(D3DTS_PROJECTION,&logical.value);trace.after(37,args,static_cast<uint32_t>(hr),0,&args,32,false,true);
 }
 quality_trace();return hr;
}
HRESULT STDMETHODCALLTYPE Device8::Reset(D3DPRESENT_PARAMETERS* pp){
 auto guard=trace.guard();const auto args=pack(pp);auto pc=reinterpret_cast<uintptr_t>(_ReturnAddress());trace.before(14,args,pc);
 game_fov.finish_frame();if(!ui_margins.finish_frame())stock_ui("ui_coordinate_restore_failed");
 HRESULT hr=quality?quality->reset(*parent_->real(),*real_,pp):real_->Reset(pp);
 trace.after(14,args,static_cast<uint32_t>(hr),pc);
 if(SUCCEEDED(hr)&&quality){ui_margins.dimensions(quality->effective.BackBufferWidth,quality->effective.BackBufferHeight);quality_trace();}
 return hr;
}
HRESULT STDMETHODCALLTYPE Device8::Present(const RECT* source,const RECT* destination,HWND window,const RGNDATA* dirty){
 auto guard=trace.guard();const auto args=pack(source,destination,window,dirty);auto pc=reinterpret_cast<uintptr_t>(_ReturnAddress());trace.before(15,args,pc);
 trace.culling=game_fov.status();game_fov.finish_frame();trace.culling.restored=game_fov.status().restored;
 if(!ui_margins.finish_frame())stock_ui("ui_coordinate_restore_failed");try{trace.ui_metadata=ui_margins.json();}catch(...){}
 if(quality&&quality->valid&&quality->effective.MultiSampleType!=D3DMULTISAMPLE_NONE&&(source||destination||window||dirty)&&!quality->aa_hazard){
  quality->aa_hazard=true;try{session().write("{\"type\":\"msaa_present_hazard\",\"reason\":\"non_null_present_arguments_native_hresult_preserved\"}");}catch(...){}
 }
 HRESULT hr=real_->Present(source,destination,window,dirty);trace.after(15,args,static_cast<uint32_t>(hr),pc);return hr;
}
HRESULT STDMETHODCALLTYPE Device8::SetViewport(const D3DVIEWPORT8* input){
 auto guard=trace.guard();auto args=pack(input);auto pc=reinterpret_cast<uintptr_t>(_ReturnAddress());trace.before(40,args,pc);
 D3DVIEWPORT8 original{},changed{};bool rewrite=quality&&safe_copy(&original,input,sizeof(original))&&quality->viewport(original,changed)&&std::memcmp(&original,&changed,sizeof(original));
 const auto* forwarded=rewrite?&changed:input;auto native=pack(forwarded);HRESULT hr=real_->SetViewport(forwarded);
 if(FAILED(hr)&&rewrite){trace.after(40,native,static_cast<uint32_t>(hr),pc,&native,16,false,true);native=args;rewrite=false;hr=real_->SetViewport(input);}
 trace.after(40,args,static_cast<uint32_t>(hr),pc,&native,rewrite?16:0);
 if(SUCCEEDED(hr)&&trace.effective_shadow.bindings.viewport.known){auto v=trace.effective_shadow.bindings.viewport.value;ui_margins.dimensions(v.Width,v.Height);
  // The game caches a constant UI matrix. Recompute its effective counterpart when only viewport/aspect changes.
  auto& logical=trace.shadow.matrices[D3DTS_PROJECTION];D3DMATRIX ui{};
  if(quality&&quality->config.interface_mode!="Stock"&&logical.known&&ui_projection(logical.value,double(v.Width)/v.Height,ui)){
   auto setter=pack(D3DTS_PROJECTION,&ui);HRESULT extra=real_->SetTransform(D3DTS_PROJECTION,&ui);trace.after(37,setter,static_cast<uint32_t>(extra),pc,&setter,32,false,true);
   if(FAILED(extra))stock_ui("native_ui_viewport_projection_rejected");
  }
 }
 return hr;
}
HRESULT STDMETHODCALLTYPE Device8::GetViewport(D3DVIEWPORT8* out){
 auto guard=trace.guard();auto args=pack(out);auto pc=reinterpret_cast<uintptr_t>(_ReturnAddress());trace.before(41,args,pc);
 HRESULT hr=real_->GetViewport(out);D3DVIEWPORT8 native{};bool virtualized=false;
 if(SUCCEEDED(hr)&&safe_copy(&native,out,sizeof(native))&&trace.shadow.bindings.viewport.known&&trace.effective_shadow.bindings.viewport.known&&std::memcmp(&trace.shadow.bindings.viewport.value,&trace.effective_shadow.bindings.viewport.value,sizeof(native)))virtualized=safe_copy(out,&trace.shadow.bindings.viewport.value,sizeof(native));
 auto effective=virtualized?pack(&native):args;trace.after(41,args,static_cast<uint32_t>(hr),pc,&effective,virtualized?16:0);return hr;
}
}
