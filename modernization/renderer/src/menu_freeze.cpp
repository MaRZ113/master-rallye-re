#include "menu_freeze.hpp"
#include "provenance.hpp"
#include <cstring>
#include <mutex>
namespace gfx2 {
FreezeResult apply_freeze_patch(PatchMemory& memory,void* context,bool exact,bool enabled) noexcept {
 FreezeResult r;if(!enabled)return r;if(!exact){r.reason="unsupported_build";return r;}
 unsigned char observed[sizeof(FREEZE_CONTEXT)]{};
 if(!context||!memory.read(observed,context,sizeof(observed))){r.reason="context_read_failed";return r;}
 bool patched=observed[3]==0;observed[3]=FREEZE_CONTEXT[3];
 if(std::memcmp(observed,FREEZE_CONTEXT,sizeof(observed))){r.reason="original_bytes_or_context_mismatch";return r;}
 r.context_validated=true;
 if(patched){r.already=true;r.reason="already_patched_no_ownership";return r;}
 auto* site=static_cast<unsigned char*>(context)+3;DWORD old=0,ignored=0;unsigned char zero=0,readback=0xff;
 if(!memory.protect(site,1,PAGE_EXECUTE_READWRITE,old)){r.reason="protect_failed";return r;}
 bool okay=memory.write(site,&zero,1)&&memory.read(&readback,site,1)&&readback==0&&memory.flush(site,1);
 bool restored=memory.protect(site,1,old,ignored);
 if(okay&&restored){r.applied=r.owned=true;r.reason="applied_process_memory_only";return r;}
 DWORD rollback=0;
 if(memory.protect(site,1,PAGE_EXECUTE_READWRITE,rollback)){
  unsigned char original=0x11;
  bool write_ok=memory.write(site,&original,1)&&memory.flush(site,1)&&memory.read(&readback,site,1)&&readback==original;
  r.rollback_verified=memory.protect(site,1,old,ignored)&&write_ok;
 }
 r.reason=r.rollback_verified?"patch_failed_rolled_back":"patch_failed_rollback_unverified";return r;
}
void install_menu_freeze(bool exact,bool enabled) noexcept {
 static std::once_flag once;
 try{std::call_once(once,[&](){
  class NativeMemory final:public PatchMemory {public:
   bool read(void* d,const void* s,size_t n) noexcept override{return safe_copy(d,s,n);}
   bool write(void* d,const void* s,size_t n) noexcept override{return safe_copy(d,s,n);}
   bool protect(void* p,size_t n,DWORD v,DWORD& old) noexcept override{return VirtualProtect(p,n,v,&old)!=FALSE;}
   bool flush(void* p,size_t n) noexcept override{return FlushInstructionCache(GetCurrentProcess(),p,n)!=FALSE;}
  } memory;
  uintptr_t base=reinterpret_cast<uintptr_t>(GetModuleHandleW(nullptr));
  auto result=apply_freeze_patch(memory,reinterpret_cast<void*>(base+FREEZE_CONTEXT_RVA),exact&&base==0x400000,enabled);
  session().write("{\"type\":\"menu_freeze_fix\",\"expected_exe_sha256\":"+quote(TARGET_SHA)+",\"rva\":1769820,\"expected_bytes\":\"7511\",\"replacement_bytes\":\"7500\",\"context_validated\":"+std::string(result.context_validated?"true":"false")+",\"applied\":"+(result.applied?"true":"false")+",\"already_patched\":"+(result.already?"true":"false")+",\"ownership\":"+(result.owned?"true":"false")+",\"rollback_verified\":"+(result.rollback_verified?"true":"false")+",\"reason\":"+quote(result.reason)+"}");
 });}catch(...){}
}
}
