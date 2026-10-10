#include "wrappers.hpp"
#include "reflection_scope.hpp"
#include "camera_probe.hpp"
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
 if(effective!=value&&type==D3DTSS_MINFILTER){
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
 return set_transform_at(type,input,reinterpret_cast<uintptr_t>(_ReturnAddress()));
}
HRESULT Device8::set_transform_at(D3DTRANSFORMSTATETYPE type,const D3DMATRIX* input,uintptr_t pc){
 auto guard=trace.guard();HRESULT repair=ui_margins.repair_world(*real_,trace,pc);if(FAILED(repair))return repair;auto args=pack(type,input);trace.before(37,args,pc);
 D3DMATRIX changed{};uint32_t rva=0;bool exe=site(pc,rva);bool rewritten=visuals.effective.fov&&visuals.projection(type,input,changed,exe,rva);
 if(quality&&quality->preview_capability.supported()&&type==D3DTS_PROJECTION&&exe&&rva==quality->preview_capability.candidate_rva){
  D3DMATRIX source{};if(safe_copy(&source,input,sizeof(source))){int family=camera_scene_family(source);if(family>=0)ui_margins.scene_context(family==1);}
 }
 if(rewritten){D3DMATRIX original{};rewritten=safe_copy(&original,input,sizeof(original))&&game_fov.allows(original);} // No D3D-only widening fallback.
 bool preview_rewritten=false;
 if(!rewritten&&!preview_rewritten&&quality&&quality->config.interface_mode!="Stock"&&quality->preview_capability.supported()&&type==D3DTS_PROJECTION&&exe&&rva==quality->preview_capability.candidate_rva){D3DMATRIX original{};preview_rewritten=safe_copy(&original,input,sizeof(original))&&frontend_preview_projection(original,changed);}
 bool ui_rewritten=false;
 if(!rewritten&&!preview_rewritten&&quality&&quality->config.interface_mode!="Stock"&&type==D3DTS_PROJECTION&&ui_owner(quality->ui_capability,exe,rva)){
  D3DMATRIX original{};auto& viewport=trace.effective_shadow.bindings.viewport;
  UINT width=viewport.known?viewport.value.Width:quality->valid?quality->effective.BackBufferWidth:0;
  UINT height=viewport.known?viewport.value.Height:quality->valid?quality->effective.BackBufferHeight:0;
  ui_rewritten=safe_copy(&original,input,sizeof(original))&&ui_projection_dimensions(original,width,height,changed);
 }
 trace.culling=game_fov.status();
 const D3DMATRIX* forwarded=(rewritten||ui_rewritten||preview_rewritten)?&changed:input;auto native=pack(type,forwarded);
HRESULT hr=real_->SetTransform(type,forwarded);if(FAILED(hr)&&(rewritten||ui_rewritten||preview_rewritten)){trace.after(37,native,static_cast<uint32_t>(hr),pc,&native,rewritten?2:preview_rewritten?64:32,false,true);if(rewritten){game_fov.disable("native_projection_rejected");visuals.effective.fov=false;}if(preview_rewritten){quality->preview_capability.status="UNSUPPORTED";quality->preview_capability.reason="native_preview_projection_rejected";}if(ui_rewritten){quality->config.interface_mode="Stock";ui_margins.disable("native_ui_projection_rejected");}native=args;hr=real_->SetTransform(type,input);rewritten=ui_rewritten=preview_rewritten=false;}if(SUCCEEDED(hr)&&quality&&type==D3DTS_PROJECTION)quality->ui_projection_live=ui_rewritten;trace.after(37,args,static_cast<uint32_t>(hr),pc,&native,rewritten?2:ui_rewritten?32:preview_rewritten?64:0);
 if(type==D3DTS_VIEW&&exe){
 CameraProbeGateInput probe_input{};probe_input.transform_type=type;probe_input.exe_caller=exe;probe_input.caller_rva=rva;
 probe_input.native_result=hr;probe_input.trace_enabled=trace.enabled;probe_input.capture_active=trace.control.active;
 probe_input.profile_supported=trace.camera_probe_profile_supported();
 probe_input.observation_already_claimed=trace.camera_probe_diagnostic.observation_claimed;
 const auto& requested_projection=trace.shadow.matrices[D3DTS_PROJECTION];
 const auto& effective_projection=trace.effective_shadow.matrices[D3DTS_PROJECTION];
 probe_input.requested_projection_known=requested_projection.known;probe_input.effective_projection_known=effective_projection.known;
 if(requested_projection.known)probe_input.requested_projection=requested_projection.value;
 if(effective_projection.known)probe_input.effective_projection=effective_projection.value;
 const CameraProbeGateResult probe_gate=camera_probe_gate(probe_input);
 if(probe_gate.gameplay_view_site){
  trace.camera_probe_diagnostic.record_gate(probe_gate,rva);
  if(probe_gate.status==CameraProbeStatus::ReadyForObservation){
   D3DMATRIX observed_view{};
   if(!safe_copy(&observed_view,input,sizeof(observed_view)))
    trace.camera_probe_diagnostic.record_outcome(CameraProbeStatus::ViewMatrixReadIncomplete,false);
   else if(!trace.claim_camera_observation_frame()){
    CameraProbeGateResult duplicate{CameraProbeStatus::DuplicateSuppressed,true};trace.camera_probe_diagnostic.record_gate(duplicate,rva);
   }else{
    CameraOwnerObservation owner{};const uintptr_t base=reinterpret_cast<uintptr_t>(GetModuleHandleW(nullptr));
    if(base==0x00400000)read_camera_owner_observation(base,owner);
    game_fov.submission_snapshot(owner.current_camera,owner.pre_submission);
    const bool reads_complete=camera_owner_reads_complete(owner);
    try{
     auto& runtime=session();
     const auto record=camera_owner_observation_json(owner,trace.device_id(),trace.frame_number(),rva,
      requested_projection.value,effective_projection.value,observed_view);
     const bool emitted=runtime.write(record);
     trace.camera_probe_diagnostic.record_outcome(emitted?(reads_complete?CameraProbeStatus::ObservationEmitted:CameraProbeStatus::OwnerReadIncomplete):CameraProbeStatus::SessionWriteFailed,
      emitted,true,reads_complete);
    }catch(...){trace.camera_probe_diagnostic.record_outcome(CameraProbeStatus::SerializationFailure,false,true,reads_complete);}
   }
  }
 }
 }
 return hr;
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
 return draw_primitive_at(type,start,count,reinterpret_cast<uintptr_t>(_ReturnAddress()));
}
HRESULT Device8::draw_primitive_at(D3DPRIMITIVETYPE type,UINT start,UINT count,uintptr_t pc){
 auto guard=trace.guard();auto args=pack(type,start,count);
 uint32_t rva=0;bool exe=site(pc,rva);bool skip=visuals.suppress(70,exe,rva,trace.shadow,type);
 HRESULT repair=repair_reflection();if(FAILED(repair)){trace.before(70,args,pc);trace.after(70,args,static_cast<uint32_t>(repair),pc,nullptr,8,true);return repair;}
 const auto& view=trace.effective_shadow.matrices[D3DTS_VIEW];D3DMATRIX identity{};identity._11=identity._22=identity._33=identity._44=1;
 bool allowed=!skip&&quality&&quality->config.interface_mode=="PreserveMargins"&&quality->ui_projection_live&&exe&&rva==UI_DRAW_RETURN_RVA&&type==D3DPT_TRIANGLELIST&&trace.shadow.bindings.vertex_shader.known&&trace.shadow.bindings.vertex_shader.value==0x142&&view.known&&!std::memcmp(&view.value,&identity,sizeof(identity));
 UiWorldScope ui(*real_,trace,ui_margins,pc,allowed);trace.before(70,args,pc);HRESULT hr=skip?S_OK:real_->DrawPrimitive(type,start,count);
 trace.after(70,args,static_cast<uint32_t>(hr),pc,nullptr,skip?4:ui.changed()?128:0,skip);return hr;
}
HRESULT STDMETHODCALLTYPE Device8::DrawIndexedPrimitive(D3DPRIMITIVETYPE type,UINT min_index,UINT vertices,UINT start,UINT count){
 return draw_indexed_at(type,min_index,vertices,start,count,reinterpret_cast<uintptr_t>(_ReturnAddress()));
}
HRESULT Device8::draw_indexed_at(D3DPRIMITIVETYPE type,UINT min_index,UINT vertices,UINT start,UINT count,uintptr_t pc){
 auto guard=trace.guard();auto args=pack(type,min_index,vertices,start,count);
 auto classification=trace.before(71,args,pc);HRESULT repair=repair_reflection();
 if(FAILED(repair)){trace.after(71,args,static_cast<uint32_t>(repair),pc,nullptr,8,true);return repair;}
 if(visuals.effective.foliage_diagnostics&&trace.enabled&&trace.control.active)
  trace.foliage_result(probe_foliage(*real_,trace.resources,args,trace.frame_number(),trace.foliage_budget,this));
 HRESULT hr;
 {ReflectionScope reflection(*real_,trace,visuals,classification,pc,count);
  hr=real_->DrawIndexedPrimitive(type,min_index,vertices,start,count); // Exactly once; original HRESULT survives restoration.
  trace.after(71,args,static_cast<uint32_t>(hr),pc);
 }
 return hr;
}
HRESULT Device8::repair_reflection() noexcept {
 HRESULT world=ui_margins.repair_world(*real_,trace,0);if(FAILED(world))return world;
 if(!trace.reflection_restore_pending.known)return S_OK;
 auto args=pack(1,D3DTSS_TEXCOORDINDEX,trace.reflection_restore_pending.value);
 HRESULT hr=real_->SetTextureStageState(1,D3DTSS_TEXCOORDINDEX,static_cast<DWORD>(args.a[2]));
 trace.after(63,args,static_cast<uint32_t>(hr),0,&args,8,false,true);return hr;
}
HRESULT Device8::stock_for_unmapped(const char* reason) noexcept {
 HRESULT repair=repair_reflection();if(FAILED(repair))return repair;
 if(!visuals.active()&&(!quality||quality->config.interface_mode=="Stock"))return S_OK;
 // Canonical tested path uses no state blocks. Restore before entering an unreviewed block/multiply path,
 // then keep this device stock. If restoration fails, report that real HRESULT rather than hide leakage.
 const DWORD keys[]={16,17,18,21};
 for(DWORD key:keys){auto& logical=trace.shadow.tss[0][key];auto& native=trace.effective_shadow.tss[0][key];
  if(logical.known&&native.known&&logical.value!=native.value){auto args=pack(0,key,logical.value);HRESULT hr=real_->SetTextureStageState(0,static_cast<D3DTEXTURESTAGESTATETYPE>(key),logical.value);trace.after(63,args,static_cast<uint32_t>(hr),0,&args,1,false,true);if(FAILED(hr))return hr;}
 }
 auto& logical=trace.shadow.matrices[3];auto& native=trace.effective_shadow.matrices[3];
 if(logical.known&&native.known&&std::memcmp(&logical.value,&native.value,sizeof(D3DMATRIX))){auto args=pack(D3DTS_PROJECTION,&logical.value);HRESULT hr=real_->SetTransform(D3DTS_PROJECTION,&logical.value);trace.after(37,args,static_cast<uint32_t>(hr),0,&args,2,false,true);if(FAILED(hr))return hr;}
 visuals.effective.anisotropy=visuals.effective.fov=visuals.effective.shadow_off=false;visuals.effective.reflection_mode="Stock";
 game_fov.disable(reason);ui_margins.disable(reason);if(quality)quality->config.interface_mode="Stock";
 try{session().write("{\"type\":\"visual_fallback_stock\",\"reason\":"+quote(reason)+"}");}catch(...){}
 return S_OK;
}
}
