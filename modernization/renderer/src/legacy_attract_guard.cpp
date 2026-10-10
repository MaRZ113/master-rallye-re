#include "legacy_attract_guard.hpp"
#include "legacy_attract_bytes.hpp"
#include "provenance.hpp"
#include <array>
#include <cstring>
#include <mutex>
#include <tlhelp32.h>
namespace gfx2 {
namespace {
bool word(PatchMemory& m,uintptr_t address,uint32_t& out) noexcept {
 return address>=0x10000&&address<=0x7ffffffb&&m.read(&out,reinterpret_cast<void*>(address),4);
}
bool initial_factory_phase(PatchMemory& m,uintptr_t base,uintptr_t caller) noexcept {
 if(base!=0x400000||caller!=base+0x159060)return false;
 uint32_t owner=0,vtable=0,counter=0,d3d=0,device=0;unsigned char flags[3]{};
 return word(m,base+0x2f9d80,owner)&&owner>=0x10000&&owner<=0x7fffff00
  &&word(m,owner,vtable)&&vtable==base+0x29228c
  &&m.read(flags,reinterpret_cast<void*>(owner+4),3)&&flags[0]==1&&flags[1]==0&&flags[2]==0
  &&word(m,owner+0x64,d3d)&&d3d==0&&word(m,owner+0x68,device)&&device==0
  &&word(m,base+0x2f6030,counter)&&counter==0;
}
bool startup_code(PatchMemory& m,uintptr_t base) noexcept {
 // PUSH SDK120; clear native COM pointers; CALL 005D5244; return 00559060.
 const unsigned char factory[]={0x6a,0x78,0x89,0x6b,0x18,0x89,0x6b,0x64,0x89,0x6b,0x68,0x89,0x6b,0x60,0xc6,0x43,0x24,0x00,0xc6,0x43,0x25,0x00,0x89,0xab,0x60,0x01,0x00,0x00,0xe8,0xe4,0xc1,0x07,0x00};
 const unsigned char thunk[]={0xff,0x25,0x14,0xf4,0x68,0x00};
 unsigned char got[sizeof(factory)]{};
 if(!m.read(got,reinterpret_cast<void*>(base+0x15903f),sizeof(factory))||std::memcmp(got,factory,sizeof(factory)))return false;
 return m.read(got,reinterpret_cast<void*>(base+0x1d5244),sizeof(thunk))&&!std::memcmp(got,thunk,sizeof(thunk));
}
class NativeMemory final:public PatchMemory {public:
 bool read(void* d,const void* s,size_t n) noexcept override{return safe_copy(d,s,n);}
 bool write(void* d,const void* s,size_t n) noexcept override{return safe_copy(d,s,n);}
 bool protect(void* p,size_t n,DWORD v,DWORD& old) noexcept override{return VirtualProtect(p,n,v,&old)!=FALSE;}
 bool flush(void* p,size_t n) noexcept override{return FlushInstructionCache(GetCurrentProcess(),p,n)!=FALSE;}
};
class NativeThreads final:public AttractThreadGate {
 std::array<HANDLE,64> handles{};std::array<DWORD,64> ids{};size_t count=0;
public:
 ~NativeThreads(){leave();}
 void leave() noexcept override {while(count){auto h=handles[--count];ResumeThread(h);CloseHandle(h);}}
 bool enter(uintptr_t begin,size_t size) noexcept override {
  HANDLE snapshot=CreateToolhelp32Snapshot(TH32CS_SNAPTHREAD,0);if(snapshot==INVALID_HANDLE_VALUE)return false;
  THREADENTRY32 e{};e.dwSize=sizeof(e);bool okay=Thread32First(snapshot,&e)!=FALSE;
  if(okay)do{if(e.th32OwnerProcessID!=GetCurrentProcessId()||e.th32ThreadID==GetCurrentThreadId())continue;
   if(count==handles.size()){okay=false;break;}
   HANDLE h=OpenThread(THREAD_SUSPEND_RESUME|THREAD_GET_CONTEXT|THREAD_QUERY_INFORMATION,FALSE,e.th32ThreadID);
   if(!h){okay=false;break;}if(SuspendThread(h)==DWORD(-1)){CloseHandle(h);okay=false;break;}
   handles[count]=h;ids[count++]=e.th32ThreadID;CONTEXT c{};c.ContextFlags=CONTEXT_CONTROL;
   if(!GetThreadContext(h,&c)||(c.Eip>=begin&&c.Eip<begin+size)){okay=false;break;}
  }while(Thread32Next(snapshot,&e));CloseHandle(snapshot);
  if(!okay)return false;
  // Recheck inventory after suspension: a newly appeared peer rejects the attempt.
  snapshot=CreateToolhelp32Snapshot(TH32CS_SNAPTHREAD,0);if(snapshot==INVALID_HANDLE_VALUE)return false;
  e.dwSize=sizeof(e);okay=Thread32First(snapshot,&e)!=FALSE;
  if(okay)do{if(e.th32OwnerProcessID!=GetCurrentProcessId()||e.th32ThreadID==GetCurrentThreadId())continue;
   bool found=false;for(size_t i=0;i<count;++i)found=found||ids[i]==e.th32ThreadID;if(!found){okay=false;break;}
  }while(Thread32Next(snapshot,&e));CloseHandle(snapshot);return okay;
 }
};
}
AttractGuardResult apply_attract_guard(PatchMemory& m,AttractThreadGate& threads,uintptr_t base,uintptr_t caller,bool exact) noexcept {
 AttractGuardResult r;if(!exact)return r;
 if(!initial_factory_phase(m,base,caller)||!startup_code(m,base)){r.reason="not_verified_initial_factory_phase";return r;}r.phase_verified=true;
 std::array<unsigned char,sizeof(ATTRACT_LOADING_BYTES)> function{};
 if(!m.read(function.data(),reinterpret_cast<void*>(base+ATTRACT_LOADING_RVA),function.size())){r.reason="loading_context_unreadable";return r;}
 constexpr size_t offset=ATTRACT_PATCH_RVA-ATTRACT_LOADING_RVA;
 if(!std::memcmp(function.data()+offset,ATTRACT_REDIRECT,5)){r.reason="already_redirected_unowned_no_overwrite";return r;}
 if(std::memcmp(function.data(),ATTRACT_LOADING_BYTES,function.size())){r.reason="original_loading_bytes_mismatch";return r;}r.context_verified=true;
 if(!threads.enter(base+ATTRACT_LOADING_RVA,function.size())){threads.leave();r.reason="thread_quiescence_unavailable_or_loading_active";return r;}r.quiesced=true;
 if(!initial_factory_phase(m,base,caller)||!startup_code(m,base)||!m.read(function.data(),reinterpret_cast<void*>(base+ATTRACT_LOADING_RVA),function.size())||std::memcmp(function.data(),ATTRACT_LOADING_BYTES,function.size())){threads.leave();r.reason="phase_or_bytes_changed_after_quiescence";return r;}
 void* site=reinterpret_cast<void*>(base+ATTRACT_PATCH_RVA);DWORD old=0,ignored=0;unsigned char readback[5]{};
 if(!m.protect(site,5,PAGE_EXECUTE_READWRITE,old)){threads.leave();r.reason="protect_failed_no_write";return r;}
 bool okay=m.write(site,ATTRACT_REDIRECT,5)&&m.read(readback,site,5)&&!std::memcmp(readback,ATTRACT_REDIRECT,5)&&m.flush(site,5);
 bool restored=m.protect(site,5,old,ignored);
 if(okay&&restored){r.applied=r.owned=true;r.reason="applied_initial_factory_process_memory_only";}
 else{
  DWORD rollback=0;bool writable=m.protect(site,5,PAGE_EXECUTE_READWRITE,rollback);
  bool bytes=writable&&m.write(site,ATTRACT_LOADING_BYTES+offset,5)&&m.read(readback,site,5)&&!std::memcmp(readback,ATTRACT_LOADING_BYTES+offset,5)&&m.flush(site,5);
  bool protection=m.protect(site,5,old,ignored);r.rollback_verified=bytes&&protection;
  r.reason=r.rollback_verified?"install_failed_rollback_verified":"install_failed_rollback_unverified_restart_required";
 }
 threads.leave();return r;
}
bool install_legacy_attract_guard(uintptr_t caller) noexcept {
 static std::once_flag once;
 static bool safe_to_continue=true;
 try{std::call_once(once,[&]() noexcept {try{NativeMemory memory;NativeThreads threads;
  auto& s=session();uintptr_t base=reinterpret_cast<uintptr_t>(GetModuleHandleW(nullptr));
  auto r=apply_attract_guard(memory,threads,base,caller,s.target);
  safe_to_continue=r.rollback_verified; // Never execute Loading after an unverified partial overwrite.
  s.write("{\"type\":\"legacy_loading_attract_guard\",\"phase\":\"R-ATTR1\",\"exact_retail\":"+std::string(s.target?"true":"false")+",\"rva\":413545,\"expected_bytes\":\"68841f6b00\",\"replacement_bytes\":\"e9d8ffffff\",\"continuation_rva\":413510,\"phase_verified\":"+(r.phase_verified?"true":"false")+",\"context_verified\":"+(r.context_verified?"true":"false")+",\"quiesced\":"+(r.quiesced?"true":"false")+",\"applied\":"+(r.applied?"true":"false")+",\"owned\":"+(r.owned?"true":"false")+",\"rollback_verified\":"+(r.rollback_verified?"true":"false")+",\"reason\":"+quote(r.reason)+"}");
  }catch(...){}});}catch(...){return false;}
 return safe_to_continue;
}
}
