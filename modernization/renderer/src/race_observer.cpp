#include "race_epoch.hpp"
#include "provenance.hpp"
#include <tlhelp32.h>
#include <cstring>
#include <cstdio>
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
 struct Key {std::array<char,64> name{};uint32_t id=0;};std::array<Key,32> keys{};size_t keys_used=0;
 bool resolve_id(uint32_t base,const char* key,uint32_t& id) noexcept override {
  if(!key||std::strlen(key)>63)return false;
  for(size_t i=0;i<keys_used;++i)if(!std::strcmp(keys[i].name.data(),key)){
   char text[192]{};if(race_pool_text(*this,base,keys[i].id,text,sizeof(text))&&!std::strcmp(text,key)){id=keys[i].id;return true;}
   if(!race_pool_id(*this,base,key,id))return false;keys[i].id=id;return true;
  }
  if(!race_pool_id(*this,base,key,id))return false;
  if(keys_used<keys.size()){auto& k=keys[keys_used++];std::memcpy(k.name.data(),key,std::strlen(key)+1);k.id=id;}return true;
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
   uint32_t origin=0;bool origin_read=race_bridge::request_origin(memory,s,origin);
   bool text_read=race_pool_text(memory,observer.base,target,text,sizeof(text));e.request(target,text,origin);if(!origin_read)e.reject("request_origin_unreadable");if(!text_read)e.reject("request_name_unreadable");}
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
 case 6:if(s.esi==e.owner.actor){auto r=read_race_owner(memory,observer.base,e.owner,e.race_generation);e.admitted(s.esi,r.valid);}break;
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
 case RaceEvent::OpenError:return "open_error";case RaceEvent::ReadError:return "read_or_decode_error";case RaceEvent::OwnerAttach:return "owner_attach";case RaceEvent::OwnerInitialized:return "owner_initializer_return";case RaceEvent::OwnerLive:return "owner_live_admission";case RaceEvent::Retire:return "owner_retire";case RaceEvent::Destroy:return "owner_destroy";case RaceEvent::DeviceReset:return "device_reset";case RaceEvent::Reset:return "reset";case RaceEvent::Release:return "device_release";default:return "rejected";}
}
const char* phase_name(RacePhase p) noexcept {switch(p){case RacePhase::Requested:return "REQUESTED";case RacePhase::Executing:return "EXECUTING";case RacePhase::AwaitingOwner:return "AWAITING_RACE_OWNER";case RacePhase::Failed:return "FAILED";case RacePhase::Revoked:return "REVOKED";default:return "UNKNOWN";}}
uint32_t event_va(RaceEvent e) noexcept {
 switch(e){case RaceEvent::Request:return 0x5223d3;case RaceEvent::Queue:return 0x522455;case RaceEvent::ExecuteBegin:case RaceEvent::ExecuteEnd:return 0x52d620;
 case RaceEvent::Commit:return 0x52d6a4;case RaceEvent::OpenError:return 0x52d5e0;case RaceEvent::ReadError:return 0x52d600;
 case RaceEvent::OwnerAttach:case RaceEvent::OwnerInitialized:return 0x48e717;case RaceEvent::OwnerLive:return 0x4f6202;case RaceEvent::Retire:return 0x4f584e;case RaceEvent::Destroy:return 0x4f5786;default:return 0;}
}
void installation_record() noexcept {
 try{session().write("{\"type\":\"race_epoch_observer\",\"phase\":\"R-CAM1-A3d\",\"read_only\":true,\"installed\":"+std::string(observer.installed?"true":"false")+",\"camera_writes_authorized\":false,\"reason\":"+quote(observer.install_reason.load())+",\"rollback_verified\":"+(observer.batch.rollback_verified?"true":"false")+"}");}catch(...){}
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
  if(threads.freeze(observer.batch)&&race_observer_context_valid(memory,observer.base)&&observer.batch.install(memory)){observer.installed.store(true);observer.enabled.store(true);observer.install_reason="hierarchical_native_lifecycle_installed";}
  else observer.install_reason=observer.batch.rollback_verified?"install_rejected_rollback_verified":"install_failed_rollback_unverified_restart_required";
 }
 installation_record();return observer.installed;
}
bool device_reset_race_observer() noexcept {
 bool retained=false;const char* reason="observer_unavailable";uint64_t generation=0,owner_lifetime=0;
 AcquireSRWLockExclusive(&observer.lock);
 if(observer.enabled){
  if(GetCurrentThreadId()!=observer.thread){observer.epoch.reject("device_reset_wrong_thread",true);reason="device_reset_wrong_thread";}
  else {retained=observer.epoch.device_reset();reason=observer.epoch.reason;}
  generation=observer.epoch.race_generation;owner_lifetime=observer.epoch.owner.lifetime;
 }
 ReleaseSRWLockExclusive(&observer.lock);
 try{session().write(std::string("{\"type\":\"race_epoch_device_reset\",\"proof_preserved\":")+(retained?"true":"false")+",\"race_generation\":"+std::to_string(generation)+",\"owner_lifetime\":"+std::to_string(owner_lifetime)+",\"reason\":"+quote(reason)+"}");}catch(...){}
 return retained;
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
RaceCertificate live_race_certificate(uintptr_t expected_camera) noexcept {
 RaceCertificate c;AcquireSRWLockExclusive(&observer.lock);
 auto& e=observer.epoch;c.race_generation=e.race_generation;c.owner_lifetime=e.owner.lifetime;c.actor=e.owner.actor;c.ai=e.owner.ai;
 if(!observer.enabled||!observer.installed)c.reason="observer_unavailable";
 else if(!e.validate_thread(observer.thread,GetCurrentThreadId()))c.reason="wrong_thread";
 else if(!owned_sites_intact()){e.reject("observer_hook_ownership_lost",true);c.reason="hook_ownership_lost";}
 else {
  auto owner=read_race_owner(memory,observer.base,e.owner,e.race_generation);
  std::array<RaceScalar,9> fields{};
  for(size_t i=0;i<fields.size();++i){uint32_t id=0;if(memory.resolve_id(observer.base,RACE_CONTEXT_KEYS[i],id))fields[i]=race_broker_scalar(memory,observer.base,id,RACE_CONTEXT_TAGS[i]);}
  uint32_t cam_manager=0,count=0,selected=0,holder=0,current=0;
  bool camera_valid=word(observer.base+CAMERA_MANAGER_RVA,cam_manager)&&word(cam_manager+16,count)&&count==1&&word(cam_manager,selected)&&selected&&selected==expected_camera&&
   word(observer.base+RENDERER_HOLDER_RVA,holder)&&word(holder+0x38,holder)&&word(holder+4,current)&&current==selected;
  c=check_live_race_certificate(e,owner,fields,camera_valid,current);
  if(c.valid&&c.single_human_car_race&&c.participant_count==1&&c.human_participant_index==0){
   uint32_t player_type_id=0;
   if(memory.resolve_id(observer.base,"Race/Car0/PlayerType",player_type_id)){
    const auto player_type=race_broker_scalar(memory,observer.base,player_type_id,2);
    if(player_type.present){c.human_participant_player_type=player_type.value;
     c.human_participant_identity_verified=player_type.value==1;}
   }
  }
 }
 ReleaseSRWLockExclusive(&observer.lock);return c;
}
RaceHudContext live_race_hud_context() noexcept {
 RaceHudContext result;
 if(!observer.enabled||!observer.installed){result.reason="observer_unavailable";return result;}
 if(observer.base!=0x400000){result.reason="unsupported_image_base";return result;}
 if(GetCurrentThreadId()!=observer.thread){result.reason="wrong_render_thread";return result;}
 if(!TryAcquireSRWLockExclusive(&observer.lock)){result.reason="observer_busy";return result;}
 auto& e=observer.epoch;result.race_generation=e.race_generation;result.owner_lifetime=e.owner.lifetime;
 if(!observer.enabled||!observer.installed)result.reason="observer_unavailable";
 else if(observer.base!=0x400000)result.reason="unsupported_image_base";
 else if(GetCurrentThreadId()!=observer.thread)result.reason="wrong_render_thread";
 else if(!owned_sites_intact())result.reason="observer_hook_ownership_lost";
 else if(!e.correlated_owner_candidate()||!race_hud_scene_proven(e))result.reason="race_hud_lifecycle_not_proven";
 else {
  uint32_t scene_manager=0,committed_scene=0;char committed_name[192]{};
  if(!word(observer.base+0x2f9aa0,scene_manager)||!scene_manager||!word(scene_manager,committed_scene)||
     !race_pool_text(memory,observer.base,committed_scene,committed_name,sizeof(committed_name))||std::strcmp(committed_name,"Hud/Hud0")){
   result.reason="committed_scene_not_race_hud";ReleaseSRWLockExclusive(&observer.lock);return result;
  }
  auto owner=read_race_owner(memory,observer.base,e.owner,e.race_generation);
  std::array<RaceScalar,9> fields{};
  for(size_t i=0;i<fields.size();++i){uint32_t id=0;if(memory.resolve_id(observer.base,RACE_CONTEXT_KEYS[i],id))fields[i]=race_broker_scalar(memory,observer.base,id,RACE_CONTEXT_TAGS[i]);}
  const auto context=check_race_hud_context(fields,owner);
  if(!context.supported)result.reason=context.reason;
  else {
   unsigned local_players=0,local_player_index=UINT32_MAX;bool player_types_valid=true;
   for(uint32_t i=0;i<owner.count;++i){char key[64]{};std::snprintf(key,sizeof(key),"Race/Car%u/PlayerType",i);uint32_t id=0;
    if(!memory.resolve_id(observer.base,key,id)){player_types_valid=false;break;}
    const auto value=race_broker_scalar(memory,observer.base,id,2);
    if(!value.present){player_types_valid=false;break;}if(value.value==1){++local_players;local_player_index=i;}
   }
   if(!player_types_valid||local_players!=1)result.reason="single_local_player_identity_unproven";
   else if(!race_hud_player_running(owner,local_player_index))result.reason="local_player_not_in_running_race_state";
   else {
    const auto pause=race_broker_bool(memory,observer.base,"Race/PauseMenu/Enabled");
    if(!pause.present||pause.tag!=0)result.reason="pause_state_unknown";
    else {result.valid=true;result.pause_known=true;result.paused=pause.value!=0;result.replay=context.replay;
     result.reason=result.replay?(result.paused?"certified_paused_replay":"certified_active_replay"):(result.paused?"certified_paused_race":"certified_active_race");}
   }
  }
 }
 ReleaseSRWLockExclusive(&observer.lock);return result;
}
RaceScalar read_pause_menu_state_readonly() noexcept {
 if(GetCurrentThreadId()!=observer.thread||observer.base!=0x400000||!observer.installed||!observer.enabled||!owned_sites_intact())return {};
 if(!TryAcquireSRWLockExclusive(&observer.lock))return {};
 RaceScalar value{};
 if(observer.thread==GetCurrentThreadId()&&observer.base==0x400000&&observer.installed&&observer.enabled&&owned_sites_intact())
  value=race_broker_bool(memory,observer.base,"Race/PauseMenu/Enabled");
 ReleaseSRWLockExclusive(&observer.lock);return value;
}
std::string race_epoch_capture_json(uint64_t device,uint64_t frame,bool input_observed,
 bool toggle_focused,bool toggle_pressed,bool toggle_edge,unsigned toggle_key) {
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
  owner=read_race_owner(memory,base,e.owner,e.race_generation);
  for(size_t i=0;i<context.size();++i){uint32_t id=0;if(memory.resolve_id(base,RACE_CONTEXT_KEYS[i],id))context[i]=race_broker_scalar(memory,base,id,RACE_CONTEXT_TAGS[i]);}
  camera_read=word(base+0x2f94dc,cam_mgr)&&word(cam_mgr+16,cameras)&&word(base+0x2f9cf0,cam_mgr)&&word(cam_mgr+0x38,cam_mgr)&&word(cam_mgr+4,camera);
 }
 RaceScalar pause_menu_enabled{};const char* pause_menu_status=!installed?"race_observer_not_installed":!same_thread?"wrong_thread":base!=0x400000?"unsupported_build":"key_not_read";
 if(installed&&same_thread&&base==0x400000){pause_menu_enabled=race_broker_bool(memory,base,"Race/PauseMenu/Enabled");pause_menu_status=pause_menu_enabled.present?"typed_bool_read_only":"missing_wrong_type_or_unreadable";}
 const auto context_check=check_race_context(context,owner);
 const auto certificate=camera_read?live_race_certificate(camera):RaceCertificate{};
 const RaceJob* root=e.lifetime(e.owner.execution_job_lifetime);const RaceJob* hud=nullptr;
 if(root)for(size_t i=0;i<e.jobs_used;++i)if(e.jobs[i].supported_hud&&e.jobs[i].parent_lifetime==root->lifetime){hud=&e.jobs[i];break;}
 auto write_job=[](std::ostringstream& out,const RaceJob* j){if(!j){out<<"null";return;}out<<"{\"lifetime\":"<<j->lifetime<<",\"parent_job_lifetime\":"<<j->parent_lifetime<<",\"scene\":"<<quote(j->scene_text.data())<<",\"source\":"<<quote(j->source_text.data())<<",\"flag21\":"<<static_cast<unsigned>(j->flag21)<<",\"flag22\":"<<static_cast<unsigned>(j->flag22)<<",\"manager_scene_after_commit\":"<<j->manager_scene_after_commit<<",\"commit_seen\":"<<(j->commit_seen?"true":"false")<<",\"commit_success\":"<<(j->commit_success?"true":"false")<<",\"terminal\":"<<(j->terminal?"true":"false")<<",\"failed\":"<<(j->failed?"true":"false")<<"}";};
 std::ostringstream o;o<<"{\"type\":\"race_epoch_snapshot\",\"phase\":\"R-CAM1-A3e\",\"device\":"<<device<<",\"frame\":"<<frame<<",\"capture_id\":"<<((device||frame)?quote(trace_capture_id(device,frame)):"null")<<",\"read_only\":true,\"installed\":"<<(installed?"true":"false")<<",\"install_reason\":"<<quote(install_reason)<<",\"observing\":"<<(observing?"true":"false")<<",\"hook_ownership_intact\":"<<(intact?"true":"false")<<",\"camera_writes_authorized\":false,\"status\":"<<quote(certificate.valid?"LIVE_RACE_CERTIFIED":"AWAITING_LIVE_RACE_CERTIFICATE")<<",\"live_certificate_valid\":"<<(certificate.valid?"true":"false")<<",\"live_certificate_reason\":"<<quote(certificate.reason)<<",\"reason\":"<<quote(e.reason)<<",\"offline_context_supported\":"<<(context_check.supported?"true":"false")<<",\"offline_context_reason\":"<<quote(context_check.reason)<<",\"course_identity_verified\":"<<(e.course_identity_verified()?"true":"false")<<",\"state\":"<<quote(phase_name(e.phase))<<",\"poisoned\":"<<(e.poisoned?"true":"false")<<",\"request_generation\":"<<e.generation<<",\"race_lifecycle_generation\":"<<e.race_generation<<",\"successful_race_generation\":"<<e.successful_race_generation<<",\"execution_depth\":"<<e.execution_depth<<",\"successful_generation\":"<<e.successful_generation<<",\"correlated_owner_candidate\":"<<(e.correlated_owner_candidate()?"true":"false")<<",\"root_job_success\":";write_job(o,root);o<<",\"hud_job_success\":";write_job(o,hud);o<<",\"scene\":{\"read_complete\":"<<(scene_read?"true":"false")<<",\"requested_id\":"<<native_requested<<",\"committed_id\":"<<native_committed<<",\"requested_name\":"<<quote(requested)<<",\"committed_name\":"<<quote(committed)<<",\"job_source\":"<<quote(source)<<",\"countdown\":"<<countdown<<"},\"owner\":{\"actor\":"<<e.owner.actor<<",\"ai\":"<<e.owner.ai<<",\"generation\":"<<e.owner.generation<<",\"race_lifecycle_generation\":"<<e.owner.race_generation<<",\"storage_readable\":"<<(owner.storage_readable?"true":"false")<<",\"native_live_unique\":"<<(owner.native_live_unique?"true":"false")<<",\"temporal_match\":"<<(owner.temporal_match?"true":"false")<<",\"lifetime\":"<<e.owner.lifetime<<",\"execution_job_lifetime\":"<<e.owner.execution_job_lifetime<<",\"initialized\":"<<(e.owner.initialized?"true":"false")<<",\"valid_native_owner\":"<<(owner.valid?"true":"false")<<",\"reason\":"<<quote(owner.reason)<<",\"registrations\":"<<owner.registrations<<",\"live_memberships\":"<<owner.live_memberships<<",\"pending_memberships\":"<<owner.pending_memberships<<",\"retired\":"<<(owner.retired?"true":"false")<<",\"participant_count\":"<<owner.count<<",\"arrays_ready\":"<<(owner.arrays_ready?"true":"false")<<",\"participant_states_ready\":"<<(owner.participant_states_ready?"true":"false")<<",\"participant_states_reason\":"<<quote(owner.participant_states_reason)<<",\"participant_states\":[";
 for(uint32_t i=0;i<owner.count&&i<8;++i){if(i)o<<',';o<<owner.participant_states[i];}
 o<<"]},\"camera\":{\"read_complete\":"<<(camera_read?"true":"false")<<",\"count\":"<<cameras<<",\"pointer\":"<<camera<<"},\"context\":{";
 for(size_t i=0;i<context.size();++i){if(i)o<<',';const auto& v=context[i];o<<quote(RACE_CONTEXT_KEYS[i])<<":{\"present\":"<<(v.present?"true":"false")<<",\"tag\":"<<v.tag<<",\"value\":";if(v.present)o<<v.value;else o<<"null";o<<'}';}
 o<<"},\"pause_menu\":{\"key\":\"Race/PauseMenu/Enabled\",\"available\":"<<(pause_menu_enabled.present?"true":"false")<<",\"enabled\":";if(pause_menu_enabled.present)o<<(pause_menu_enabled.value?"true":"false");else o<<"null";o<<",\"tag\":";if(pause_menu_enabled.present)o<<pause_menu_enabled.tag;else o<<"null";o<<",\"read_only\":true,\"source\":\"existing_typed_race_broker_reader\",\"status\":"<<quote(pause_menu_status)<<"},\"jobs\":[";for(size_t i=0;i<e.jobs_used;++i){if(i)o<<',';auto& j=e.jobs[i];o<<"{\"pointer\":"<<j.pointer<<",\"generation\":"<<j.generation<<",\"lifetime\":"<<j.lifetime<<",\"parent_job_lifetime\":"<<j.parent_lifetime<<",\"race_lifecycle_generation\":"<<j.race_generation<<",\"supported_hud_child\":"<<(j.supported_hud?"true":"false")<<",\"failed\":"<<(j.failed?"true":"false")<<",\"manager_scene_after_commit\":"<<j.manager_scene_after_commit<<",\"scene\":"<<j.scene<<",\"source_id\":"<<j.source<<",\"scene_name_at_queue\":"<<quote(j.scene_text.data())<<",\"source_name_at_queue\":"<<quote(j.source_text.data())<<",\"flag21\":"<<static_cast<unsigned>(j.flag21)<<",\"flag22\":"<<static_cast<unsigned>(j.flag22)<<",\"commit_seen\":"<<(j.commit_seen?"true":"false")<<",\"commit_success\":"<<(j.commit_success?"true":"false")<<",\"terminal\":"<<(j.terminal?"true":"false")<<",\"pointer_reused\":"<<(j.reused?"true":"false")<<"}";}
 o<<"],\"ring_overwritten\":"<<(e.event_serial>RaceEpoch::MAX_EVENTS?e.event_serial-RaceEpoch::MAX_EVENTS:0)<<",\"events\":[";
 for(size_t i=0;i<e.events_used;++i){if(i)o<<',';const auto& t=e.chronological(i);o<<"{\"serial\":"<<t.serial<<",\"event\":"<<quote(event_name(t.event))<<",\"generation\":"<<t.generation<<",\"race_lifecycle_generation\":"<<t.race_generation<<",\"parent_job_lifetime\":"<<t.parent_job_lifetime<<",\"job\":"<<t.job<<",\"job_lifetime\":"<<t.job_lifetime<<",\"actor\":"<<t.actor<<",\"ai\":"<<t.ai<<",\"owner_lifetime\":"<<t.owner_lifetime<<",\"scene\":"<<t.scene<<",\"thread\":"<<t.thread<<",\"native_va\":"<<event_va(t.event)<<",\"native_rva\":"<<(event_va(t.event)?event_va(t.event)-0x400000:0)<<",\"reason\":"<<quote(t.reason)<<"}";}
 o<<"],\"input_observation\":";if(input_observed)o<<"{\"toggle_key_vk\":"<<toggle_key<<",\"focused\":"<<(toggle_focused?"true":"false")<<",\"toggle_pressed_while_focused\":"<<((toggle_focused&&toggle_pressed)?"true":"false")<<",\"controller_toggle_edge\":"<<(toggle_edge?"true":"false")<<"}";else o<<"null";
 o<<",\"free_camera\":"<<free_camera_snapshot_json()<<"}";return o.str();
}
}
