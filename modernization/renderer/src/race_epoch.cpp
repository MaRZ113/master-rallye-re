#include "race_epoch.hpp"
#include <cstring>
#include <cstdio>
namespace gfx2 {
namespace {
bool ascii_equal(const char* a,const char* b,bool fold_case=false) noexcept {
 if(!a||!b)return false;
 while(*a&&*b){char x=*a++,y=*b++;if(fold_case){if(x>='A'&&x<='Z')x=static_cast<char>(x-'A'+'a');if(y>='A'&&y<='Z')y=static_cast<char>(y-'A'+'a');}if(x!=y)return false;}
 return *a==*b;
}
bool valid_race_root(const RaceJob& root,bool fold_case) noexcept {
 if(root.parent_lifetime||!root.terminal||!root.commit_seen||!root.commit_success||root.failed||root.flag21!=1||root.flag22!=1)return false;
 constexpr char prefix[]="RaceTest/";const char* scene=root.scene_text.data();
 for(size_t i=0;i<sizeof(prefix)-1;++i){char a=scene[i],b=prefix[i];if(fold_case&&a>='A'&&a<='Z')a=static_cast<char>(a-'A'+'a');if(fold_case&&b>='A'&&b<='Z')b=static_cast<char>(b-'A'+'a');if(a!=b)return false;}
 const char* course=scene+sizeof(prefix)-1;const size_t n=std::strlen(course);if(!n||n>96)return false;
 for(size_t i=0;i<n;++i){const char c=course[i];if(!((c>='A'&&c<='Z')||(c>='a'&&c<='z')||(c>='0'&&c<='9')||c=='_'||c=='-'))return false;}
 char source[128]{};const int written=std::snprintf(source,sizeof(source),"DataScene/RaceTest/%s.xml",course);
 return written>0&&static_cast<size_t>(written)<sizeof(source)&&ascii_equal(root.source_text.data(),source,fold_case);
}
bool race_hud_scene_proven_as(const RaceEpoch& e,bool attract) noexcept {
 if(!e.correlated_owner_candidate())return false;
 const auto* root=e.lifetime(e.owner.execution_job_lifetime);if(!root||!valid_race_root(*root,true))return false;
 const char* scene=attract?"Hud/AttractMode":"Hud/Hud0";const char* source=attract?"DataScene/Hud/AttractMode.xml":"DataScene/Hud/Hud0.xml";
 unsigned matching=0;
 for(size_t i=0;i<e.jobs_used;++i){const auto& job=e.jobs[i];if(job.race_generation!=e.race_generation||job.lifetime==root->lifetime)continue;
  if(!job.supported_hud||job.parent_lifetime!=root->lifetime||job.failed||!job.terminal||!job.commit_seen||!job.commit_success||job.flag21!=1||job.flag22!=0||
     !ascii_equal(job.scene_text.data(),scene)||!ascii_equal(job.source_text.data(),source))return false;
  ++matching;
 }
 return matching==1;
}
}
bool race_bridge::request_origin(RaceReadMemory& m,const Saved& s,uint32_t& origin) noexcept {
 // 522330 pushes ECX/ESI/EDI, then the message argument before CALL5223D3.
 // Saved PUSHAD.ESP points below PUSHFD: outer RET is at savedESP+24.
 return s.esp<=UINT32_MAX-24&&m.read(s.esp+24,&origin,4);
}

bool RaceEpoch::next(uint64_t& n) noexcept {if(n==UINT64_MAX){poisoned=true;phase=RacePhase::Revoked;reason="generation_overflow";return false;}++n;return true;}
void RaceEpoch::note(RaceEvent e,const char* why,uint32_t job) noexcept {
 if(!next(event_serial))return;
 auto* j=find_mutable(job?job:executing_job);
 events[event_head]={event_serial,generation,j?j->lifetime:0,owner.lifetime,e,job?job:executing_job,owner.actor,owner.ai,requested_scene,why};
 auto& t=events[event_head];t.thread=observed_thread;t.race_generation=j?j->race_generation:race_generation;t.parent_job_lifetime=e==RaceEvent::Request?request_parent_lifetime:j?j->parent_lifetime:0;
 t.request_origin=e==RaceEvent::Request?request_origin:j?j->request_origin:0;
 event_head=(event_head+1)%MAX_EVENTS;if(events_used<MAX_EVENTS)++events_used;
}
const RaceTransition& RaceEpoch::chronological(size_t i) const noexcept {return events[(event_head+MAX_EVENTS-events_used+i)%MAX_EVENTS];}
RaceJob* RaceEpoch::find_mutable(uint32_t p) noexcept {for(size_t i=jobs_used;i>0;--i)if(jobs[i-1].pointer==p)return &jobs[i-1];return nullptr;}
const RaceJob* RaceEpoch::find(uint32_t p) const noexcept {for(size_t i=jobs_used;i>0;--i)if(jobs[i-1].pointer==p)return &jobs[i-1];return nullptr;}
const RaceJob* RaceEpoch::lifetime(uint64_t serial) const noexcept {for(size_t i=0;i<jobs_used;++i)if(jobs[i].lifetime==serial)return &jobs[i];return nullptr;}
void RaceEpoch::reject(const char* why,bool permanent,uint32_t observed_job) noexcept {
 revoked_race_generation=race_generation;reason=why;phase=RacePhase::Revoked;successful_generation=successful_race_generation=0;poisoned|=permanent;note(RaceEvent::Rejected,why,observed_job);
}
void RaceEpoch::request(uint32_t scene,const char* text,uint32_t origin) noexcept {
 if(!next(generation))return;
 requested_scene=scene;request_origin=origin;request_queued=false;
 request_text.fill(0);if(text&&std::strlen(text)<request_text.size())std::memcpy(request_text.data(),text,std::strlen(text)+1);
 auto* parent=find(executing_job);request_parent_lifetime=parent&&parent->executing?parent->lifetime:0;
 // Hud0 remains tied to the exact native selector caller. AttractMode is a
 // distinct scene request; its separate runtime certificate requires the
 // committed Attract scene, typed AttractMode context, and this same owner ancestry.
 const bool supported_hud_name=text&&
  ((!std::strcmp(text,"Hud/Hud0")&&origin==0x004aa0c1)||!std::strcmp(text,"Hud/AttractMode"));
 request_supported_hud=parent&&parent->executing&&supported_hud_name&&
  owner.initialized&&!owner.retired&&owner.execution_job_lifetime==parent->lifetime&&owner.race_generation==race_generation;
 if(!request_supported_hud){if(!next(race_generation))return;successful_generation=successful_race_generation=0;}
 request_race_generation=race_generation;
 phase=RacePhase::Requested;reason=request_supported_hud?"native_hud_child_request":"new_lifecycle_request_revoked_previous_certificate";
 note(RaceEvent::Request,reason);
}
void RaceEpoch::queue(uint32_t p,uint32_t scene,uint32_t source,bool type_ok,uint8_t flag21,uint8_t flag22,const char* source_text) noexcept {
 if(poisoned||!generation||request_queued||!p||scene!=requested_scene||!type_ok){reject("queue_without_matching_request");return;}
 auto* old=find(p);bool reused=old!=nullptr;
 if(old&&!old->terminal){reject("live_job_pointer_reused",true);return;}
 if(request_supported_hud&&(flag21!=1||flag22!=0)){reject("hud_child_native_flags_mismatch");return;}
 if(jobs_used==MAX_JOBS){
  size_t remove=MAX_JOBS;
  for(size_t i=0;i<jobs_used;++i){auto& j=jobs[i];bool referenced=j.lifetime==owner.execution_job_lifetime||j.lifetime==request_parent_lifetime;
   for(size_t k=0;k<execution_depth;++k)referenced|=execution_stack[k]==j.lifetime;
   for(size_t k=0;k<jobs_used;++k)referenced|=!jobs[k].terminal&&jobs[k].parent_lifetime==j.lifetime;
   if(j.terminal&&!referenced){remove=i;break;}}
  if(remove==MAX_JOBS){reject("active_job_capacity_exceeded");return;}
  for(size_t i=remove;i+1<jobs_used;++i)jobs[i]=jobs[i+1];--jobs_used;
 }
 if(!next(job_serial))return;
 auto& j=jobs[jobs_used++];j={};j.pointer=p;j.scene=scene;j.source=source;j.generation=generation;j.lifetime=job_serial;j.reused=reused;
 j.parent_lifetime=request_parent_lifetime;j.race_generation=request_race_generation;j.supported_hud=request_supported_hud;j.request_origin=request_origin;
 j.flag21=flag21;j.flag22=flag22;j.scene_text=request_text;
 if(source_text&&std::strlen(source_text)<j.source_text.size())std::memcpy(j.source_text.data(),source_text,std::strlen(source_text)+1);
 request_queued=true;reason="native_request_queued_with_lifetime";note(RaceEvent::Queue,reason,p);
}
void RaceEpoch::begin(uint32_t p,bool type_ok) noexcept {
 auto* j=find_mutable(p);
 if(poisoned||!type_ok||!j||j->terminal||j->executing){reject("unknown_duplicate_or_invalid_execute",j&&j->executing,p);return;}
 if(execution_depth==execution_stack.size()){reject("execution_stack_overflow",true,p);return;}
 if(execution_depth&&j->parent_lifetime!=execution_stack[execution_depth-1]){reject("unproven_nested_execution",true,p);return;}
 j->executing=true;execution_stack[execution_depth++]=j->lifetime;executing_job=p;
 phase=RacePhase::Executing;reason="native_callback_entered_not_success";note(RaceEvent::ExecuteBegin,reason,p);
}
void RaceEpoch::commit(uint32_t scene,bool success) noexcept {
 auto* j=find_mutable(executing_job);
 if(poisoned||!execution_depth||!j||!j->executing||j->lifetime!=execution_stack[execution_depth-1]||j->commit_seen){reject("commit_without_matching_execution");return;}
 j->commit_seen=true;j->manager_scene_after_commit=scene;manager_scene_after_commit=scene;
 // Native 522680's boolean is this executing parser job's result. The scene
 // argument we can observe is SceneManager+4, which a nested HUD request may
 // already have changed; it is diagnostic only and cannot qualify the job.
 j->commit_success=success&&!j->failed;
 reason=j->commit_success?"native_parse_success_await_callback_return":"default_or_failed_commit";note(RaceEvent::Commit,reason);
}
void RaceEpoch::end(uint32_t p) noexcept {
 auto* j=find_mutable(p);
 if(!j||!execution_depth||execution_stack[execution_depth-1]!=j->lifetime||!j->executing||j->terminal){reject("unmatched_execute_return",true,p);return;}
 j->executing=false;j->terminal=true;
 --execution_depth;auto* parent=execution_depth?lifetime(execution_stack[execution_depth-1]):nullptr;executing_job=parent?parent->pointer:0;
 if(j->commit_seen&&j->commit_success&&!j->failed&&!poisoned){
  if(j->race_generation==race_generation){successful_generation=j->generation;successful_race_generation=race_generation;phase=RacePhase::AwaitingOwner;reason="job_success_temporal_checks_pending";}
  else reason="older_job_completed_without_current_permission";
 }else{j->failed=true;if(j->race_generation==race_generation){successful_generation=successful_race_generation=0;revoked_race_generation=race_generation;phase=RacePhase::Failed;}reason="callback_return_without_success";}
 note(RaceEvent::ExecuteEnd,reason,p);
}
void RaceEpoch::error(uint32_t p,bool read_error) noexcept {
 auto* j=find_mutable(p);if(!j||j->terminal){reject("unknown_or_duplicate_error",false,p);return;}
 j->failed=true;j->commit_success=false;if(!j->executing)j->terminal=true;
 if(j->race_generation==race_generation){successful_generation=successful_race_generation=0;revoked_race_generation=race_generation;phase=RacePhase::Failed;}
 reason=read_error?"native_read_or_decode_error":"native_file_open_error";note(read_error?RaceEvent::ReadError:RaceEvent::OpenError,reason,p);
}
void RaceEpoch::attach(uint32_t actor,uint32_t ai,bool slot_ok) noexcept {
 auto* j=find(executing_job);
 if(!actor||!ai||!slot_ok||!generation||!j||!j->executing){reject("owner_attach_without_execution_lifetime");return;}
 if(owner.actor&&!owner.retired&&owner.race_generation==j->race_generation){reject("multiple_owner_lifetimes");return;}
 if(!next(owner_serial))return;
 owner={actor,ai,j->generation,owner_serial,j->lifetime,false,false,false};owner.race_generation=j->race_generation;
 note(RaceEvent::OwnerAttach,"owner_constructed_inside_native_job");
}
void RaceEpoch::initialized(uint32_t actor,uint32_t ai,bool valid) noexcept {
 if(actor!=owner.actor||ai!=owner.ai){reject("initializer_identity_changed");return;}
 owner.initialized=valid&&!owner.retired;note(RaceEvent::OwnerInitialized,owner.initialized?"native_initializer_returned":"native_initializer_failed_or_retired");
}
void RaceEpoch::admitted(uint32_t actor,bool valid) noexcept {
 if(actor!=owner.actor)return;owner.live=valid&&!owner.retired;note(RaceEvent::OwnerLive,owner.live?"unique_native_live_membership":"live_membership_rejected");
}
void RaceEpoch::retire(uint32_t actor,bool destroyed) noexcept {
 if(actor!=owner.actor||!actor)return;owner.retired=true;owner.live=false;
 if(owner.race_generation==race_generation){successful_generation=successful_race_generation=0;revoked_race_generation=race_generation;phase=RacePhase::Revoked;}
 reason=destroyed?"owner_destroyed":"owner_retired";note(destroyed?RaceEvent::Destroy:RaceEvent::Retire,reason);
}
bool RaceEpoch::device_reset() noexcept {
 if(execution_depth==0&&correlated_owner_candidate()){
  reason="completed_race_proof_retained_across_device_reset";
  note(RaceEvent::DeviceReset,reason);
  return correlated_owner_candidate();
 }
 cancel(RaceEvent::DeviceReset,execution_depth?"device_reset_during_native_lifecycle":"device_reset_without_completed_race_proof");
 return false;
}
void RaceEpoch::cancel(RaceEvent e,const char* why) noexcept {revoked_race_generation=race_generation;successful_generation=successful_race_generation=0;phase=RacePhase::Revoked;reason=why;note(e,why);}
bool RaceEpoch::correlated_owner_candidate() const noexcept {
 if(poisoned||!race_generation||revoked_race_generation==race_generation||successful_race_generation!=race_generation||owner.race_generation!=race_generation||!owner.initialized||!owner.live||owner.retired)return false;
 auto* root=lifetime(owner.execution_job_lifetime);
 if(!root||root->race_generation!=race_generation||!root->terminal||!root->commit_success||root->failed)return false;
 // Every job of this lifecycle must have succeeded; HUD alone can never certify.
 for(size_t i=0;i<jobs_used;++i){auto& j=jobs[i];if(j.race_generation!=race_generation)continue;
  if(!j.terminal||!j.commit_seen||!j.commit_success||j.failed)return false;
  if(j.lifetime!=root->lifetime&&(!j.supported_hud||j.parent_lifetime!=root->lifetime))return false;
 }
 return true;
}
bool RaceEpoch::course_identity_verified() const noexcept {
 auto* j=lifetime(owner.execution_job_lifetime);if(!j)return false;
 return valid_race_root(*j,true);
}
bool race_course_is_france1(std::string_view course_id) noexcept {
 constexpr std::string_view france="RaceTest/France1";if(course_id.size()!=france.size())return false;
 for(size_t i=0;i<france.size();++i){char a=course_id[i],b=france[i];
  if(a>='A'&&a<='Z')a=static_cast<char>(a-'A'+'a');if(b>='A'&&b<='Z')b=static_cast<char>(b-'A'+'a');
  if(a!=b)return false;}
 return true;
}
bool race_hud_scene_proven(const RaceEpoch& e) noexcept {
 return race_hud_scene_proven_as(e,false);
}
bool race_attract_hud_scene_proven(const RaceEpoch& e) noexcept {
 return race_hud_scene_proven_as(e,true);
}
bool race_hud_player_running(const RaceOwnerRead& owner,uint32_t participant) noexcept {
 return owner.valid&&owner.arrays_ready&&owner.participant_states_ready&&participant<owner.count&&participant<owner.participant_states.size()&&
  owner.participant_states[participant]==0;
}
bool race_hud_startup_phase(const RaceOwnerRead& owner) noexcept {
 if(!owner.valid||!owner.arrays_ready||!owner.count||owner.count>owner.participant_states.size())return false;
 bool startup=false;
 for(uint32_t i=0;i<owner.count;++i){const auto state=owner.participant_states[i];if(state==1)startup=true;else if(state!=0&&state!=2)return false;}
 return startup&&(!owner.participant_states_ready&&owner.participant_states_reason&&
  !std::strcmp(owner.participant_states_reason,"race_state_1_startup_transition"));
}
bool race_hud_player_drawable(const RaceOwnerRead& owner,uint32_t participant) noexcept {
 if(!owner.valid||!owner.arrays_ready||participant>=owner.count||participant>=owner.participant_states.size())return false;
 const auto state=owner.participant_states[participant];return state==0||state==1||state==2;
}
bool RaceEpoch::validate_thread(uint32_t expected,uint32_t actual) noexcept {
 observed_thread=actual;
 if(!expected||expected!=actual){reject("native_event_wrong_thread",true);return false;}return true;
}
namespace {
bool word(RaceReadMemory& m,uint32_t p,uint32_t& v) noexcept{return p&&m.read(p,&v,4);}
bool vector(RaceReadMemory& m,uint32_t p,uint32_t stride,uint32_t limit,uint32_t& begin,uint32_t& count) noexcept {
 uint32_t end=0,capacity=0;if(!word(m,p+4,begin)||!word(m,p+8,end)||!word(m,p+12,capacity)||!begin||end<begin||capacity<end||(end-begin)%stride)return false;
 count=(end-begin)/stride;return count<=limit;
}
bool pool(RaceReadMemory& m,uint32_t base,uint32_t& begin,uint32_t& count) noexcept {
 uint32_t manager=0,v=0;return word(m,base+0x2f93d4,manager)&&word(m,manager+4,v)&&vector(m,v,4,32768,begin,count);
}
bool list_count(RaceReadMemory& m,uint32_t head,uint32_t actor,uint32_t& found) noexcept {
 uint32_t node=0,previous=head;if(!word(m,head+4,node))return false;
 for(uint32_t n=0;n<8192;++n){if(node==head){uint32_t tail=0;return word(m,head+8,tail)&&tail==previous;}
  uint32_t payload=0,next_node=0,back=0;
  if(!node||!word(m,node,payload)||!word(m,node+4,next_node)||!word(m,node+8,back)||back!=previous)return false;
  if(payload==actor){if(node!=actor+0x60)return false;++found;}
  previous=node;node=next_node;
 }return false;
}
}
bool race_pool_text(RaceReadMemory& m,uint32_t base,uint32_t id,char* out,size_t capacity) noexcept {
 if(!out||!capacity||capacity>192)return false;out[0]=0;uint32_t begin=0,count=0,record=0;
 if(!pool(m,base,begin,count)||id>=count||!word(m,begin+id*4,record)||!record||record>UINT32_MAX-200)return false;
 // 4D44F0 passes header+8 to 4D4D00; the ID vector stores that TEXT pointer.
 for(size_t i=0;i<capacity;++i){if(!m.read(record+static_cast<uint32_t>(i),out+i,1)){out[0]=0;return false;}if(!out[i])return true;}
 out[0]=0;return false;
}
bool race_pool_id(RaceReadMemory& m,uint32_t base,const char* text,uint32_t& id) noexcept {
 if(!text)return false;size_t n=std::strlen(text);if(n>191)return false;
 uint32_t begin=0,count=0;if(!pool(m,base,begin,count))return false;bool found=false;
 for(uint32_t i=0;i<count;++i){uint32_t record=0;if(!word(m,begin+i*4,record)||!record||record>UINT32_MAX-200)return false;
  bool match=true;for(size_t j=0;j<=n;++j){char c=0;if(!m.read(record+static_cast<uint32_t>(j),&c,1))return false;if(c!=text[j]){match=false;break;}}
  if(match){if(found)return false;found=true;id=i;}
 }return found;
}
bool RaceReadMemory::resolve_id(uint32_t base,const char* key,uint32_t& id) noexcept {return race_pool_id(*this,base,key,id);}
RaceScalar race_broker_scalar(RaceReadMemory& m,uint32_t base,uint32_t id,uint32_t tag) noexcept {
 RaceScalar r;uint32_t manager=0,begin=0,count=0,payload=0,native_id=0;
 if(!word(m,base+0x2f9410,manager)||!vector(m,manager,0x1c,32768,begin,count)||id>=count)return r;
 uint32_t p=begin+id*0x1c;if(!word(m,p,native_id)||native_id!=id||!word(m,p+8,r.tag)||r.tag!=tag||!word(m,p+4,payload)||!payload)return r;
 if(tag==0){uint8_t v=0;if(!m.read(payload,&v,1)||v>1)return r;r.value=v;}
 else if(tag==2){if(!m.read(payload,&r.value,4))return r;}else return r;
 r.present=true;return r;
}
RaceScalar race_broker_bool(RaceReadMemory& m,uint32_t base,const char* key) noexcept {
 uint32_t id=0;if(!key||!m.resolve_id(base,key,id))return {};return race_broker_scalar(m,base,id,0);
}
RaceOwnerRead read_race_owner(RaceReadMemory& m,uint32_t base,const RaceOwner& identity,uint64_t current_generation) noexcept {
 RaceOwnerRead r;r.actor=identity.actor;r.ai=identity.ai;
 if(!r.actor||!r.ai||identity.retired||!identity.lifetime||!current_generation){r.reason="no_current_owner_lifetime";return r;}
 uint32_t manager=0,registry=0,name=0,begin=0,count=0,bucket=0,id=0;
 if(!word(m,base+0x2f96fc,manager)||!word(m,manager+0x1c,registry)||!m.resolve_id(base,"RaceLimits",id)||!word(m,r.actor+0x5c,name)||name!=id||!vector(m,registry,4,32768,begin,count)||id>=count||!word(m,begin+id*4,bucket)||!vector(m,bucket,4,64,begin,count)){r.reason="registry_read_or_name_failed";return r;}
 r.registrations=count;if(count!=1){r.reason="nonunique_registration";return r;}
 uint32_t registered=0;if(!word(m,begin,registered)||registered!=r.actor){r.reason="registered_owner_replaced";return r;}
 uint8_t flags=0;if(!m.read(r.actor,&flags,1)){r.reason="flags_unreadable";return r;}r.retired=(flags&2)!=0;if(r.retired){r.reason="retirement_flag";return r;}
 uint32_t ai=0,vtable=0;if(!word(m,r.actor+4,ai)||ai!=r.ai||!word(m,ai,vtable)||vtable!=base+0x29152c){r.reason="ai_slot_or_type_changed";return r;}r.type_ok=true;
 r.storage_readable=true;
 if(!list_count(m,manager+0x10,r.actor,r.pending_memberships)){r.reason="pending_list_malformed";return r;}
 for(uint32_t p=0;p<7;++p)if(!list_count(m,manager+0x24+p*12,r.actor,r.live_memberships)){r.reason="live_list_malformed";return r;}
 if(r.pending_memberships||r.live_memberships!=1){r.reason="pending_or_nonunique_live_membership";return r;}
 r.native_live_unique=true;r.temporal_match=identity.race_generation==current_generation;
 // Only now, after live registry/lifetime/retirement checks, probe participant allocations.
 if(!word(m,ai+0x2c,r.count)||r.count<1||r.count>8){r.reason="participant_count_invalid";return r;}
 for(uint32_t offset:{0x20u,0x24u,0x30u,0x34u,0x38u,0x3cu,0x40u}){uint32_t data=0;std::array<uint32_t,8> values{};
  if(!word(m,ai+offset,data)||!data||!m.read(data,values.data(),r.count*4)){r.reason="participant_array_unreadable";return r;}}
 for(uint32_t offset:{0x10u,0x14u,0x18u,0x1cu}){uint32_t resource=0;if(!word(m,ai+offset,resource)||!resource){r.reason="boundary_resource_missing";return r;}}
 r.arrays_ready=true;r.participant_states_ready=true;r.participant_states_reason="native_phase_0_or_2";
 for(uint32_t i=0;i<r.count;++i){char key[64];std::snprintf(key,sizeof(key),"Race/Car%u/RaceState",i);uint32_t key_id=0;
  if(!m.resolve_id(base,key,key_id)){r.participant_states_ready=false;r.participant_states_reason="race_state_key_missing";break;}auto state=race_broker_scalar(m,base,key_id,2);
  if(!state.present){r.participant_states_ready=false;r.participant_states_reason="race_state_value_unreadable_or_wrong_type";break;}
  r.participant_states[i]=state.value;
  // RaceStarter 0x0048E820 has a native zero-writing branch as well as the
  // staged 1/2 path. Zero is accepted only under the independent completed
  // supported RaceTest job, current live RaceLimits owner, typed offline context and
  // single-camera checks below. Phase 1 stays rejected by race/camera proof;
  // the HUD-only path can admit it only alongside a live SceneManager countdown.
  if(state.value!=0&&state.value!=2){r.participant_states_ready=false;
   r.participant_states_reason=state.value==1?"race_state_1_startup_transition":state.value==3?"race_state_3_finished":"race_state_unsupported_value";}
 }
 r.valid=true;r.reason="unique_live_owner_arrays_readable_not_race_certificate";return r;
}
RaceContextCheck check_race_context(const std::array<RaceScalar,9>& f,const RaceOwnerRead& owner) noexcept {
 for(size_t i=0;i<f.size();++i)if(!f[i].present||f[i].tag!=RACE_CONTEXT_TAGS[i])return {false,"missing_or_wrong_type_broker_entry"};
 if((f[0].value!=1&&f[0].value!=2)||f[1].value!=1||f[2].value!=0||f[7].value!=0)return {false,"unsupported_race_or_player_configuration"};
 for(size_t i=3;i<=6;++i)if(f[i].value!=0)return {false,"network_attract_ghost_or_replay"};
 if(f[0].value==1&&f[8].value!=1)return {false,"mode1_without_verified_single_car"};
 if(!owner.valid||!owner.arrays_ready||f[8].value<1||f[8].value>8||static_cast<uint32_t>(f[8].value)!=owner.count)return {false,"participants_not_currently_ready"};
 if(!owner.participant_states_ready)return {false,"participant_race_state_not_active_or_starting"};
 return {true,"offline_one_player_supporting_context_not_certificate"};
}
RaceHudContextCheck check_race_hud_context(const std::array<RaceScalar,9>& f,const RaceOwnerRead& owner,bool countdown_active) noexcept {
 if(!f[6].present||f[6].tag!=RACE_CONTEXT_TAGS[6])return {false,false,"missing_or_wrong_type_broker_entry"};
 if(f[6].value!=0&&f[6].value!=1)return {false,false,"unsupported_replay_flag_value"};
 const bool replay=f[6].value==1;
 // HUD suppression may cover native phases 0, 1 (the verified startup
 // transition), and 2. Camera/physics certification continues to require the
 // stricter participant_states_ready check in check_race_context().
 const bool startup=race_hud_startup_phase(owner);
 if((startup&&!countdown_active)||(!owner.participant_states_ready&&!startup))return {false,false,"participant_race_state_not_active_or_starting"};
 for(uint32_t i=0;i<owner.count&&i<owner.participant_states.size();++i){const auto state=owner.participant_states[i];
  if(state!=0&&state!=2&&!(state==1&&startup&&countdown_active))return {false,false,"participant_race_state_not_active_or_starting"};}
 auto hud_owner=owner;hud_owner.participant_states_ready=true;
 auto checked_fields=f;if(replay)checked_fields[6].value=0;
 const auto ordinary=check_race_context(checked_fields,hud_owner);
 if(!ordinary.supported)return {false,false,ordinary.reason};
 return replay?RaceHudContextCheck{true,true,"certified_single_player_replay_hud_context"}:
  RaceHudContextCheck{true,false,startup&&countdown_active?"certified_start_countdown_hud_context":"offline_one_player_hud_context"};
}
bool check_race_attract_hud_context(const std::array<RaceScalar,9>& f,const RaceOwnerRead& owner) noexcept {
 for(size_t i=0;i<f.size();++i)if(!f[i].present||f[i].tag!=RACE_CONTEXT_TAGS[i])return false;
 if(f[0].value!=14||f[1].value!=0||f[2].value!=0||f[3].value!=0||f[4].value!=1||
    f[5].value!=0||f[6].value!=0||f[7].value!=0||f[8].value<1||f[8].value>8)return false;
 if(!owner.valid||!owner.arrays_ready||!owner.participant_states_ready||static_cast<uint32_t>(f[8].value)!=owner.count)return false;
 for(uint32_t i=0;i<owner.count&&i<owner.participant_states.size();++i)
  if(owner.participant_states[i]!=0&&owner.participant_states[i]!=2)return false;
 return true;
}
RaceCertificate check_live_race_certificate(const RaceEpoch& e,const RaceOwnerRead& owner,const std::array<RaceScalar,9>& fields,bool camera_valid,uint32_t camera) noexcept {
 RaceCertificate c;c.race_generation=e.race_generation;c.owner_lifetime=e.owner.lifetime;c.actor=e.owner.actor;c.ai=e.owner.ai;
 c.single_human_car_race=fields[0].present&&fields[0].tag==RACE_CONTEXT_TAGS[0]&&fields[0].value==1&&
  fields[1].present&&fields[1].tag==RACE_CONTEXT_TAGS[1]&&fields[1].value==1&&
  fields[8].present&&fields[8].tag==RACE_CONTEXT_TAGS[8]&&fields[8].value==1;
 if(fields[8].present&&fields[8].tag==RACE_CONTEXT_TAGS[8]&&fields[8].value>0)
  c.participant_count=static_cast<uint32_t>(fields[8].value);
 if(c.single_human_car_race)c.human_participant_index=0;
 if(!owner.valid||!owner.storage_readable||!owner.native_live_unique)c.reason=owner.reason;
 else if(!owner.temporal_match||!e.correlated_owner_candidate())c.reason="lifecycle_ancestry_or_completion_unproven";
 else if(!e.course_identity_verified())c.reason="supported_course_job_not_verified";
 else {auto context=check_race_context(fields,owner);if(!context.supported)c.reason=context.reason;
  else if(!camera_valid)c.reason="single_camera_identity_not_verified";
  else {const auto* root=e.lifetime(e.owner.execution_job_lifetime);
   const int copied=root?std::snprintf(c.course_id.data(),c.course_id.size(),"%s",root->scene_text.data()):-1;
   if(!root||copied<0||static_cast<size_t>(copied)>=c.course_id.size())c.reason="course_identity_copy_failed";
   else {c.valid=true;c.camera=camera;c.reason="live_supported_course_offline_race_certificate";}}}
 return c;
}
bool RacePatchBatch::owned() const noexcept {for(size_t i=0;i<count;++i)if(sites[i].owned)return true;return false;}
bool race_observer_context_valid(PatchMemory& m,uintptr_t base) noexcept {
 if(base!=0x400000)return false;
 auto verify=[&](const RaceNativeAnchor& anchor){std::array<unsigned char,32> expected{},actual{};size_t chars=std::strlen(anchor.bytes),n=chars/2;
  if(chars%2||n>expected.size())return false;
  auto digit=[](char c){return c>='0'&&c<='9'?c-'0':c>='a'&&c<='f'?c-'a'+10:-1;};
  for(size_t i=0;i<n;++i){auto a=digit(anchor.bytes[i*2]),b=digit(anchor.bytes[i*2+1]);if(a<0||b<0)return false;expected[i]=static_cast<unsigned char>((a<<4)|b);}
  if(!m.read(actual.data(),reinterpret_cast<void*>(base+anchor.va-0x400000),n)||std::memcmp(actual.data(),expected.data(),n))return false;
  return true;
 };
 for(const auto& anchor:RACE_OBSERVER_CONTEXTS)if(!verify(anchor))return false;
 for(const auto& anchor:RACE_A3D_CONTEXTS)if(!verify(anchor))return false;
 return true;
}
bool RacePatchBatch::exchange(PatchMemory& m,RacePatchUnit& s,bool installing) noexcept {
 auto& from=installing?s.original:s.replacement;auto& to=installing?s.replacement:s.original;std::array<unsigned char,5> got{};
 if(!m.read(got.data(),s.address,s.size)||std::memcmp(got.data(),from.data(),s.size))return false;
 DWORD old=0,ignored=0;if(!m.protect(s.address,s.size,PAGE_EXECUTE_READWRITE,old))return false;
 bool okay=m.write(s.address,to.data(),s.size)&&m.read(got.data(),s.address,s.size)&&!std::memcmp(got.data(),to.data(),s.size)&&m.flush(s.address,s.size);
 bool protection=m.protect(s.address,s.size,old,ignored);
 if(okay&&protection){s.owned=installing;return true;}
 DWORD recovery=0;bool restored=m.protect(s.address,s.size,PAGE_EXECUTE_READWRITE,recovery);
 restored=restored&&m.write(s.address,from.data(),s.size)&&m.read(got.data(),s.address,s.size)&&!std::memcmp(got.data(),from.data(),s.size)&&m.flush(s.address,s.size);
 bool permissions=m.protect(s.address,s.size,old,ignored);rollback_verified=rollback_verified&&restored&&permissions;
 // If rollback cannot be proven, retain ownership and pinned bridge/original storage.
 if(!restored||!permissions)s.owned=true;
 return false;
}
bool RacePatchBatch::install(PatchMemory& m) noexcept {
 if(!count||count>MAX_SITES||owned())return false;rollback_verified=true;
 for(size_t i=0;i<count;++i){auto& s=sites[i];std::array<unsigned char,5> got{};
  if(!s.address||!s.size||s.size>5||!m.read(got.data(),s.address,s.size)||std::memcmp(got.data(),s.original.data(),s.size))return false;
  for(size_t j=0;j<i;++j){auto p=reinterpret_cast<uintptr_t>(s.address),q=reinterpret_cast<uintptr_t>(sites[j].address);if(p<q+sites[j].size&&q<p+s.size)return false;}}
 for(size_t i=0;i<count;++i)if(!exchange(m,sites[i],true)){for(size_t j=i;j>0;--j)rollback_verified=exchange(m,sites[j-1],false)&&rollback_verified;return false;}
 return true;
}
bool RacePatchBatch::remove(PatchMemory& m) noexcept {
 // Preflight all owned bytes before touching any, including foreign-hook rejection.
 for(size_t i=0;i<count;++i)if(sites[i].owned){std::array<unsigned char,5> got{};if(!m.read(got.data(),sites[i].address,sites[i].size)||std::memcmp(got.data(),sites[i].replacement.data(),sites[i].size))return false;}
 for(size_t i=count;i>0;--i)if(sites[i-1].owned&&!exchange(m,sites[i-1],false))return false;
 return true;
}
}
