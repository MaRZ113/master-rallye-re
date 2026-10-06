#include "reflection_scope.hpp"
#include <cstring>
namespace gfx2 {
ReflectionScope::ReflectionScope(IDirect3DDevice8& native,Trace& trace,VisualPolicy& policy,
 const DrawClassification& draw,uintptr_t pc,uint32_t triangles) noexcept
 :native_(native),trace_(trace),policy_(policy),pc_(pc),triangles_(triangles){
 outcome_.requested_tci=trace.shadow.tss[1][11];outcome_.effective_tci=trace.effective_shadow.tss[1][11];
 outcome_.mode=policy.effective.reflection_mode=="ViewDependent2D"?"ViewDependent2D":"Stock";
 outcome_.reason=reflection_exclusion(draw);outcome_.candidate=std::strcmp(outcome_.reason,"eligible")==0;
 if(!outcome_.candidate)return;
 if(policy.effective.reflection_mode!="ViewDependent2D"){outcome_.reason="stock_mode";return;}
 if(trace.reflection_disabled||trace.reflection_restore_pending.known){outcome_.reason="disabled_after_restore_failure";return;}
 if(!outcome_.effective_tci.known||(outcome_.effective_tci.value&0xffff0000u)!=D3DTSS_TCI_CAMERASPACENORMAL){outcome_.reason="unknown_or_nonstock_effective_tci";return;}
 original_=outcome_.effective_tci.value;DWORD temporary=(original_&0xffffu)|D3DTSS_TCI_CAMERASPACEREFLECTIONVECTOR;
 if(temporary==original_){outcome_.reason="already_effective";return;}
 auto args=pack(1,D3DTSS_TEXCOORDINDEX,temporary);HRESULT hr=native_.SetTextureStageState(1,D3DTSS_TEXCOORDINDEX,temporary);++outcome_.native_writes;
 trace_.after(63,args,static_cast<uint32_t>(hr),pc_,&args,8,false,true);
 if(FAILED(hr)){outcome_.reason="temporary_set_failed_stock_draw";return;}
 changed_=true;outcome_.applied=true;outcome_.effective_tci.set(temporary);outcome_.reason="view_dependent_body";
}
ReflectionScope::~ReflectionScope() noexcept {
 if(changed_){auto args=pack(1,D3DTSS_TEXCOORDINDEX,original_);HRESULT hr=native_.SetTextureStageState(1,D3DTSS_TEXCOORDINDEX,original_);++outcome_.native_writes;
  outcome_.restore_attempted=true;outcome_.restore_success=SUCCEEDED(hr);
  trace_.after(63,args,static_cast<uint32_t>(hr),pc_,&args,8,false,true);
  if(FAILED(hr)){trace_.reflection_restore_pending.set(original_);trace_.reflection_disabled=true;outcome_.reason="restore_failed_feature_disabled";
   try{policy_.effective.reflection_mode="Stock";policy_.effective.reflection_reason="native_restore_failed";session().write("{\"type\":\"reflection_restore_failure\",\"hresult\":"+std::to_string(static_cast<uint32_t>(hr))+",\"stock_tci\":"+std::to_string(original_)+"}");}catch(...){}
  }
 }
 trace_.reflection_result(outcome_,triangles_);
}
}
