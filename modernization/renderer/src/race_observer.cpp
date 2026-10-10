#include "race_epoch.hpp"
#include "provenance.hpp"
#include <tlhelp32.h>
#include <cstring>
#include <sstream>
#include <atomic>
namespace gfx2 {
namespace {
class NativeMemory final:public PatchMemory,public RaceReadMemory {
public:
 bool read(void* d,const void* s,size_t n) noexcept override{return safe_copy(d,s,n);}
 bool read(uint32_t p,void* d,size_t n) noexcept override {
  return p>=0x10000&&n<=4096&&n<=UINT32_MAX-p&&safe_copy(d,reinterpret_cast<void*>(p),n);
 }
 bool write(void* d,const void* s,size_t n) noexcept override{return safe_copy(d,s,n);}
 bool protect(void* p,size_t n,DWORD v,DWORD& old) noexcept override{return VirtualProtect(p,n,v,&old)!=FALSE;}
 bool flush(void* p,size_t n) noexcept override{return FlushInstructionCache(GetCurrentProcess(),p,n)!=FALSE;}
} memory;
struct Observer {
 SRWLOCK lock=SRWLOCK_INIT;RaceEpoch epoch;RacePatchBatch batch;
 std::atomic<uint32_t> base{0};std::atomic<DWORD> thread{0};std::atomic_size_t devices{0};
 std::atomic_bool enabled{false},installed{false};unsigned callback_depth=0,execution_depth=0;
 std::atomic<const char*> install_reason{"not_installed"};
} observer;
bool word(uint32_t p,uint32_t& v) noexcept{return memory.read(p,&v,4);}
bool job_type(uint32_t p) noexcept {uint32_t v=0;return p&&word(p,v)&&v==observer.base+0x291b10;}
bool manager(uint32_t p) noexcept {uint32_t actual=0;return word(observer.base+0x2f9aa0,actual)&&actual==p&&p;}
bool owned_sites_intact() noexcept {
 if(observer.batch.count!=10)return false;
 for(size_t i=0;i<observer.batch.count;++i){const auto& s=observer.batch.sites[i];std::array<unsigned char,5> bytes{};
  if(!s.owned||!memory.read(bytes.data(),s.address,s.size)||std::memcmp(bytes.data(),s.replacement.data(),s.size))return false;
 }return true;
}

// Only the read-only callbacks hold this lock. It is never held across original
// native execution, device calls, thread suspension, logging, or allocation.
void __stdcall observe(uint32_t kind,const race_bridge::Saved* input) noexcept {
 AcquireSRWLockExclusive(&observer.lock);
 auto& e=observer.epoch;
 if(!observer.enabled){ReleaseSRWLockExclusive(&observer.lock);return;}
 if(!e.validate_thread(observer.thread,GetCurrentThreadId())){ReleaseSRWLockExclusive(&observer.lock);return;}
 if(!owned_sites_intact()){e.reject("observer_hook_ownership_lost",true);ReleaseSRWLockExclusive(&observer.lock);return;}
 if(observer.callback_depth++){e.reject("observer_callback_reentry",true);--observer.callback_depth;ReleaseSRWLockExclusive(&observer.lock);return;}
 const auto& s=*input;
 switch(kind){
 case 0:{ // Call immediately after SceneManager+4 store; ESI manager, EDI ID address.
  uint32_t stored=0,target=0;char text[192]{};
  if(manager(s.esi)&&word(s.esi+4,stored)&&word(s.edi,target)&&stored==target){
   bool text_read=race_pool_text(memory,observer.base,target,text,sizeof(text));e.request(target,text);if(!text_read)e.reject("request_name_unreadable");}
  else e.reject("request_manager_or_target_mismatch",true);break;}
 case 1:{uint32_t target=0,source=0,mgr=0;char text[192]{};
  if(word(observer.base+0x2f9aa0,mgr)&&word(mgr+4,target)&&word(s.args[0],source)&&race_pool_text(memory,observer.base,source,text,sizeof(text)))e.queue(s.ecx,target,source,job_type(s.ecx),static_cast<uint8_t>(s.args[2]),static_cast<uint8_t>(s.args[1]),text);
  else e.reject("queue_inputs_unreadable",true);break;}
 case 2:if(!manager(s.ecx))e.reject("commit_wrong_manager",true);break;
 case 3:{uint32_t scene=0;if(manager(s.ecx)&&word(s.ecx,scene))e.commit(scene,(s.args[0]&0xff)!=0);else e.reject("commit_result_unreadable",true);break;}
 case 4:e.attach(s.ecx,s.args[1],s.args[0]==0);break;
 case 5:{uint32_t ai=0,vtable=0;uint8_t flags=2;
  bool valid=word(s.ecx+4,ai)&&ai==s.args[1]&&word(ai,vtable)&&vtable==observer.base+0x29152c&&memory.read(s.ecx,&flags,1)&&!(flags&2);
  e.initialized(s.ecx,s.args[1],valid);break;}
 case 6:if(s.esi==e.owner.actor){auto r=read_race_owner(memory,observer.base,e.owner,e.generation);e.admitted(s.esi,r.valid);}break;
 case 7:break; // Native live-list transfer hasn't completed yet.
 case 8:if(s.esi>=0x18)e.retire(s.esi-0x18,false);break;
 case 9:e.retire(s.esi,true);break;
 case 10:e.error(s.ecx,false);break;
 case 11:e.error(s.ecx,true);break;
 case 12:{++observer.execution_depth;auto* j=e.find(s.ecx);uint32_t source=0;uint8_t flag21=0,flag22=0;
  bool payload=j&&word(s.ecx+0x1c,source)&&memory.read(s.ecx+0x21,&flag21,1)&&memory.read(s.ecx+0x22,&flag22,1)&&j->source==source&&j->flag21==flag21&&j->flag22==flag22;
  e.begin(s.ecx,job_type(s.ecx)&&payload);break;}
 case 13:e.end(s.ecx);if(observer.execution_depth)--observer.execution_depth;else e.reject("execute_depth_underflow",true);break;
 default:e.reject("invalid_observer_event",true);break;
 }
 --observer.callback_depth;ReleaseSRWLockExclusive(&observer.lock);
}
struct SuspendedThreads {
 std::array<HANDLE,64> handles{};size_t count=0;
 ~SuspendedThreads(){for(size_t i=count;i>0;--i){ResumeThread(handles[i-1]);CloseHandle(handles[i-1]);}}
 bool freeze(const RacePatchBatch& batch) noexcept {
  HANDLE snapshot=CreateToolhelp32Snapshot(TH32CS_SNAPTHREAD,0);if(snapshot==INVALID_HANDLE_VALUE)return false;
  bool okay=true;THREADENTRY32 entry{};entry.dwSize=sizeof(entry);
  if(!Thread32First(snapshot,&entry)){CloseHandle(snapshot);return false;}
  do{if(entry.th32OwnerProcessID!=GetCurrentProcessId()||entry.th32ThreadID==GetCurrentThreadId())continue;
   if(count==handles.size()){okay=false;break;}
   HANDLE thread=OpenThread(THREAD_SUSPEND_RESUME|THREAD_GET_CONTEXT|THREAD_QUERY_INFORMATION,FALSE,entry.th32ThreadID);
   if(!thread){okay=false;break;}if(SuspendThread(thread)==DWORD(-1)){CloseHandle(thread);okay=false;break;}
   handles[count++]=thread;CONTEXT context{};context.ContextFlags=CONTEXT_CONTROL;
   if(!GetThreadContext(thread,&context)){okay=false;break;}
   for(size_t i=0;i<batch.count;++i){auto& s=batch.sites[i];auto pc=reinterpret_cast<uintptr_t>(s.address);
    if(context.Eip>=pc&&context.Eip<pc+s.size){okay=false;break;}}
   if(!okay)break;
  }while(Thread32Next(snapshot,&entry));CloseHandle(snapshot);return okay;
 }
};
void call_site(size_t i,uint32_t va,uint32_t target,uintptr_t bridge) noexcept {
 auto& s=observer.batch.sites[i];s.address=reinterpret_cast<void*>(observer.base+va-0x400000);s.size=5;s.original[0]=s.replacement[0]=0xe8;
 uint32_t original=target-va-5,replacement=static_cast<uint32_t>(bridge-reinterpret_cast<uintptr_t>(s.address)-5);
 std::memcpy(s.original.data()+1,&original,4);std::memcpy(s.replacement.data()+1,&replacement,4);
}
void virtual_site(size_t i,uint32_t va,uint32_t target,uintptr_t bridge) noexcept {
 auto& s=observer.batch.sites[i];s.address=reinterpret_cast<void*>(observer.base+va-0x400000);s.size=4;
 target+=observer.base-0x400000;uint32_t replacement=static_cast<uint32_t>(bridge);
 std::memcpy(s.original.data(),&target,4);std::memcpy(s.replacement.data(),&replacement,4);
}
const char* event_name(RaceEvent e) noexcept {
 switch(e){case RaceEvent::Request:return "request";case RaceEvent::Queue:return "queue";case RaceEvent::ExecuteBegin:return "execute_begin";case RaceEvent::Commit:return "commit_return";case RaceEvent::ExecuteEnd:return "execute_return";
 case RaceEvent::OpenError:return "open_error";case RaceEvent::ReadError:return "read_or_decode_error";case RaceEvent::OwnerAttach:return "owner_attach";case RaceEvent::OwnerInitialized:return "owner_initializer_return";case RaceEvent::OwnerLive:return "owner_live_admission";case RaceEvent::Retire:return "owner_retire";case RaceEvent::Destroy:return "owner_destroy";case RaceEvent::Reset:return "reset";case RaceEvent::Release:return "device_release";default:return "rejected";}
}
const char* phase_name(RacePhase p) noexcept {switch(p){case RacePhase::Requested:return "REQUESTED";case RacePhase::Executing:return "EXECUTING";case RacePhase::AwaitingOwner:return "AWAITING_RACE_OWNER";case RacePhase::Failed:return "FAILED";case RacePhase::Revoked:return "REVOKED";default:return "UNKNOWN";}}
uint32_t event_va(RaceEvent e) noexcept {
 switch(e){case RaceEvent::Request:return 0x5223d3;case RaceEvent::Queue:return 0x522455;case RaceEvent::ExecuteBegin:case RaceEvent::ExecuteEnd:return 0x52d620;
 case RaceEvent::Commit:return 0x52d6a4;case RaceEvent::OpenError:return 0x52d5e0;case RaceEvent::ReadError:return 0x52d600;
 case RaceEvent::OwnerAttach:case RaceEvent::OwnerInitialized:return 0x48e717;case RaceEvent::OwnerLive:return 0x4f6202;case RaceEvent::Retire:return 0x4f584e;case RaceEvent::Destroy:return 0x4f5786;default:return 0;}
}
void installation_record() noexcept {
 try{session().write("{\"type\":\"race_epoch_observer\",\"phase\":\"R-CAM1-A3c\",\"read_only\":true,\"installed\":"+std::string(observer.installed?"true":"false")+",\"camera_writes_authorized\":false,\"reason\":"+quote(observer.install_reason.load())+",\"rollback_verified\":"+(observer.batch.rollback_verified?"true":"false")+"}");}catch(...){}
}
}
bool install_race_observer(bool exact,bool enabled) noexcept {
 if(!exact||!enabled)return false;
 if(observer.devices++){AcquireSRWLockExclusive(&observer.lock);observer.epoch.reject("multiple_devices",true);ReleaseSRWLockExclusive(&observer.lock);return false;}
 if(observer.batch.owned()){observer.install_reason="previous_hook_ownership_requires_process_restart";installation_record();return false;}
 observer.thread=GetCurrentThreadId();observer.base=static_cast<uint32_t>(reinterpret_cast<uintptr_t>(GetModuleHandleW(nullptr)));
 if(observer.base!=0x400000||!IsProcessorFeaturePresent(PF_XMMI_INSTRUCTIONS_AVAILABLE)){observer.install_reason="base_or_sse_unsupported";installation_record();return false;}
 if(!race_observer_context_valid(memory,observer.base)){observer.install_reason="native_context_bytes_mismatch";installation_record();return false;}
 using namespace race_bridge;
 request_original=0x4d11d0;queue_original=0x52d550;commit_original=0x522680;attach_original=0x4f5950;
 live_original=0x4f62e0;retire_original=destroy_original=0x4f6310;
 open_error_original=0x52d5e0;read_error_original=0x52d600;execute_original=0x52d620;callback=&observe;
 observer.batch.count=10;
 call_site(0,0x5223d3,0x4d11d0,reinterpret_cast<uintptr_t>(&race_bridge::request));
 call_site(1,0x522455,0x52d550,reinterpret_cast<uintptr_t>(&race_bridge::queue));
 call_site(2,0x52d6a4,0x522680,reinterpret_cast<uintptr_t>(&race_bridge::commit));
 call_site(3,0x48e717,0x4f5950,reinterpret_cast<uintptr_t>(&race_bridge::attach));
 call_site(4,0x4f6202,0x4f62e0,reinterpret_cast<uintptr_t>(&race_bridge::live));
 call_site(5,0x4f584e,0x4f6310,reinterpret_cast<uintptr_t>(&race_bridge::retire));
 call_site(6,0x4f5786,0x4f6310,reinterpret_cast<uintptr_t>(&race_bridge::destroy));
 virtual_site(7,0x691b14,0x52d5e0,reinterpret_cast<uintptr_t>(&race_bridge::open_error));
 virtual_site(8,0x691b18,0x52d600,reinterpret_cast<uintptr_t>(&race_bridge::read_error));
 virtual_site(9,0x691b1c,0x52d620,reinterpret_cast<uintptr_t>(&race_bridge::execute));
 HMODULE pin=nullptr;
 if(!GetModuleHandleExW(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS|GET_MODULE_HANDLE_EX_FLAG_PIN,reinterpret_cast<LPCWSTR>(&install_race_observer),&pin)){observer.install_reason="module_pin_failed";installation_record();return false;}
 {SuspendedThreads threads;
  if(threads.freeze(observer.batch)&&race_observer_context_valid(memory,observer.base)&&observer.batch.install(memory)){observer.installed.store(true);observer.enabled.store(true);observer.install_reason="read_only_native_lifecycle_installed";}
  else observer.install_reason=observer.batch.rollback_verified?"install_rejected_rollback_verified":"install_failed_rollback_unverified_restart_required";
 }
 installation_record();return observer.installed;
}
void reset_race_observer() noexcept {
 AcquireSRWLockExclusive(&observer.lock);if(observer.enabled){observer.epoch.cancel(RaceEvent::Reset,"reset_requires_new_lifecycle");if(GetCurrentThreadId()!=observer.thread)observer.epoch.reject("reset_wrong_thread",true);}ReleaseSRWLockExclusive(&observer.lock);
}
void release_race_observer() noexcept {
 if(!observer.devices)return;if(--observer.devices)return;
 bool removable=false;
 AcquireSRWLockExclusive(&observer.lock);observer.epoch.cancel(RaceEvent::Release,"device_release");observer.enabled=false;
 removable=GetCurrentThreadId()==observer.thread&&!observer.callback_depth&&!observer.execution_depth;
 ReleaseSRWLockExclusive(&observer.lock);
 if(removable){SuspendedThreads threads;if(threads.freeze(observer.batch)&&observer.batch.remove(memory)){observer.installed=false;observer.install_reason="removed_owned_sites";}else observer.install_reason="remove_failed_pinned_passthrough";}
 else observer.install_reason="remove_unsafe_thread_or_active_execution_pinned_passthrough";
 installation_record(); // Static forwarding originals and pinned code remain valid on failed removal.
}
std::string race_epoch_capture_json(uint64_t device,uint64_t frame) {
 RaceEpoch e;bool installed=false,observing=false,intact=false;const char* install_reason=nullptr;uint32_t base=0;bool same_thread=false;
 AcquireSRWLockExclusive(&observer.lock);
 same_thread=GetCurrentThreadId()==observer.thread;
 if(observer.enabled&&!same_thread)observer.epoch.reject("capture_wrong_thread",true);
 if(observer.enabled&&same_thread){intact=owned_sites_intact();if(!intact)observer.epoch.reject("observer_hook_ownership_lost",true);}
 observing=observer.enabled;
 e=observer.epoch;installed=observer.installed;install_reason=observer.install_reason.load();base=observer.base;
 ReleaseSRWLockExclusive(&observer.lock);
 // Do not retain native storage addresses beyond this snapshot, or read unsupported builds.
 char requested[192]{},committed[192]{},source[192]{};RaceOwnerRead owner{};uint32_t native_requested=0,native_committed=0,countdown=0,cameras=0,camera=0;
 bool scene_read=false,camera_read=false;std::array<RaceScalar,9> context{};
 if(installed&&same_thread&&base==0x400000){uint32_t mgr=0,cam_mgr=0;
  scene_read=word(base+0x2f9aa0,mgr)&&word(mgr+4,native_requested)&&word(mgr,native_committed)&&word(mgr+12,countdown);
  race_pool_text(memory,base,native_requested,requested,sizeof(requested));race_pool_text(memory,base,native_committed,committed,sizeof(committed));
  if(auto* job=e.find(e.executing_job))race_pool_text(memory,base,job->source,source,sizeof(source));
  else for(size_t i=0;i<e.jobs_used;++i)if(e.jobs[i].generation==e.generation)race_pool_text(memory,base,e.jobs[i].source,source,sizeof(source));
  owner=read_race_owner(memory,base,e.owner,e.generation);
  for(size_t i=0;i<context.size();++i){uint32_t id=0;if(race_pool_id(memory,base,RACE_CONTEXT_KEYS[i],id))context[i]=race_broker_scalar(memory,base,id,RACE_CONTEXT_TAGS[i]);}
  camera_read=word(base+0x2f94dc,cam_mgr)&&word(cam_mgr+16,cameras)&&word(base+0x2f9cf0,cam_mgr)&&word(cam_mgr+0x38,cam_mgr)&&word(cam_mgr+4,camera);
 }
 const auto context_check=check_race_context(context,owner);
 std::ostringstream o;o<<"{\"type\":\"race_epoch_snapshot\",\"phase\":\"R-CAM1-A3c\",\"device\":"<<device<<",\"frame\":"<<frame<<",\"capture_id\":"<<quote(trace_capture_id(device,frame))<<",\"read_only\":true,\"installed\":"<<(installed?"true":"false")<<",\"install_reason\":"<<quote(install_reason)<<",\"observing\":"<<(observing?"true":"false")<<",\"hook_ownership_intact\":"<<(intact?"true":"false")<<",\"camera_writes_authorized\":false,\"status\":\"BLOCKED_ON_RACE_EPOCH_CORRELATION\",\"reason\":"<<quote(e.reason)<<",\"offline_context_supported\":"<<(context_check.supported?"true":"false")<<",\"offline_context_reason\":"<<quote(context_check.reason)<<",\"course_identity_verified\":false,\"state\":"<<quote(phase_name(e.phase))<<",\"poisoned\":"<<(e.poisoned?"true":"false")<<",\"request_generation\":"<<e.generation<<",\"successful_generation\":"<<e.successful_generation<<",\"correlated_owner_candidate\":"<<(e.correlated_owner_candidate()?"true":"false")<<",\"scene\":{\"read_complete\":"<<(scene_read?"true":"false")<<",\"requested_id\":"<<native_requested<<",\"committed_id\":"<<native_committed<<",\"requested_name\":"<<quote(requested)<<",\"committed_name\":"<<quote(committed)<<",\"job_source\":"<<quote(source)<<",\"countdown\":"<<countdown<<"},\"owner\":{\"actor\":"<<e.owner.actor<<",\"ai\":"<<e.owner.ai<<",\"generation\":"<<e.owner.generation<<",\"lifetime\":"<<e.owner.lifetime<<",\"execution_job_lifetime\":"<<e.owner.execution_job_lifetime<<",\"initialized\":"<<(e.owner.initialized?"true":"false")<<",\"valid_native_owner\":"<<(owner.valid?"true":"false")<<",\"reason\":"<<quote(owner.reason)<<",\"registrations\":"<<owner.registrations<<",\"live_memberships\":"<<owner.live_memberships<<",\"pending_memberships\":"<<owner.pending_memberships<<",\"retired\":"<<(owner.retired?"true":"false")<<",\"participant_count\":"<<owner.count<<",\"arrays_ready\":"<<(owner.arrays_ready?"true":"false")<<",\"participant_states_ready\":"<<(owner.participant_states_ready?"true":"false")<<",\"participant_states\":[";
 for(uint32_t i=0;i<owner.count&&i<8;++i){if(i)o<<',';o<<owner.participant_states[i];}
 o<<"]},\"camera\":{\"read_complete\":"<<(camera_read?"true":"false")<<",\"count\":"<<cameras<<",\"pointer\":"<<camera<<"},\"context\":{";
 for(size_t i=0;i<context.size();++i){if(i)o<<',';const auto& v=context[i];o<<quote(RACE_CONTEXT_KEYS[i])<<":{\"present\":"<<(v.present?"true":"false")<<",\"tag\":"<<v.tag<<",\"value\":";if(v.present)o<<v.value;else o<<"null";o<<'}';}
 o<<"},\"jobs\":[";for(size_t i=0;i<e.jobs_used;++i){if(i)o<<',';auto& j=e.jobs[i];o<<"{\"pointer\":"<<j.pointer<<",\"generation\":"<<j.generation<<",\"lifetime\":"<<j.lifetime<<",\"scene\":"<<j.scene<<",\"source_id\":"<<j.source<<",\"scene_name_at_queue\":"<<quote(j.scene_text.data())<<",\"source_name_at_queue\":"<<quote(j.source_text.data())<<",\"flag21\":"<<static_cast<unsigned>(j.flag21)<<",\"flag22\":"<<static_cast<unsigned>(j.flag22)<<",\"commit_seen\":"<<(j.commit_seen?"true":"false")<<",\"commit_success\":"<<(j.commit_success?"true":"false")<<",\"terminal\":"<<(j.terminal?"true":"false")<<",\"pointer_reused\":"<<(j.reused?"true":"false")<<"}";}
 o<<"],\"ring_overwritten\":"<<(e.event_serial>RaceEpoch::MAX_EVENTS?e.event_serial-RaceEpoch::MAX_EVENTS:0)<<",\"events\":[";
 for(size_t i=0;i<e.events_used;++i){if(i)o<<',';const auto& t=e.chronological(i);o<<"{\"serial\":"<<t.serial<<",\"event\":"<<quote(event_name(t.event))<<",\"generation\":"<<t.generation<<",\"job\":"<<t.job<<",\"job_lifetime\":"<<t.job_lifetime<<",\"actor\":"<<t.actor<<",\"ai\":"<<t.ai<<",\"owner_lifetime\":"<<t.owner_lifetime<<",\"scene\":"<<t.scene<<",\"thread\":"<<t.thread<<",\"native_va\":"<<event_va(t.event)<<",\"native_rva\":"<<(event_va(t.event)?event_va(t.event)-0x400000:0)<<",\"reason\":"<<quote(t.reason)<<"}";}
 o<<"]}";return o.str();
}
}
