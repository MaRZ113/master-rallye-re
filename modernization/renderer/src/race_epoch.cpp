#include "race_epoch.hpp"
#include <cstring>
#include <cstdio>
namespace gfx2 {
bool RaceEpoch::next(uint64_t& n) noexcept {if(n==UINT64_MAX){poisoned=true;phase=RacePhase::Revoked;reason="generation_overflow";return false;}++n;return true;}
void RaceEpoch::note(RaceEvent e,const char* why,uint32_t job) noexcept {
 if(!next(event_serial))return;
 auto* j=find_mutable(job?job:executing_job);
 events[event_head]={event_serial,generation,j?j->lifetime:0,owner.lifetime,e,job?job:executing_job,owner.actor,owner.ai,requested_scene,why};
 events[event_head].thread=observed_thread;
 event_head=(event_head+1)%MAX_EVENTS;if(events_used<MAX_EVENTS)++events_used;
}
const RaceTransition& RaceEpoch::chronological(size_t i) const noexcept {return events[(event_head+MAX_EVENTS-events_used+i)%MAX_EVENTS];}
RaceJob* RaceEpoch::find_mutable(uint32_t p) noexcept {for(size_t i=0;i<jobs_used;++i)if(jobs[i].pointer==p)return &jobs[i];return nullptr;}
const RaceJob* RaceEpoch::find(uint32_t p) const noexcept {for(size_t i=0;i<jobs_used;++i)if(jobs[i].pointer==p)return &jobs[i];return nullptr;}
void RaceEpoch::reject(const char* why,bool permanent,uint32_t observed_job) noexcept {reason=why;phase=RacePhase::Revoked;successful_generation=0;poisoned=poisoned||permanent;note(RaceEvent::Rejected,why,observed_job);}
void RaceEpoch::request(uint32_t scene,const char* text) noexcept {
 // Revoke first, even for the same ID. Never infer an epoch from pre-existing storage.
 successful_generation=0;owner.live=false;requested_scene=scene;phase=RacePhase::Requested;reason="request_revoked_previous_epoch";
 request_text.fill(0);if(text&&std::strlen(text)<request_text.size())std::memcpy(request_text.data(),text,std::strlen(text)+1);
 if(!next(generation))return;
 if(executing_job){reject("request_during_execute",true);return;}
 note(RaceEvent::Request,reason);
}
void RaceEpoch::queue(uint32_t p,uint32_t scene,uint32_t source,bool type_ok,uint8_t flag21,uint8_t flag22,const char* source_text) noexcept {
 if(poisoned||!generation||phase!=RacePhase::Requested||!p||scene!=requested_scene||!type_ok){reject("queue_without_matching_request");return;}
 for(size_t i=0;i<jobs_used;++i)if(jobs[i].generation==generation){reject("duplicate_queue");return;}
 auto* j=find_mutable(p);bool reused=j!=nullptr;
 if(j&&!j->terminal){reject("live_job_pointer_reused",true);return;}
 if(!j){if(jobs_used==MAX_JOBS){reject("job_capacity_exceeded",true);return;}j=&jobs[jobs_used++];}
 if(!next(job_serial))return;
 *j={p,scene,source,generation,job_serial,false,false,false,false,reused};
 j->flag21=flag21;j->flag22=flag22;
 j->scene_text=request_text;if(source_text&&std::strlen(source_text)<j->source_text.size())std::memcpy(j->source_text.data(),source_text,std::strlen(source_text)+1);
 reason=reused?"job_pointer_reused_requires_lifetime_proof":"current_request_queued";note(RaceEvent::Queue,reason,p);
}
void RaceEpoch::begin(uint32_t p,bool type_ok) noexcept {
 auto* j=find_mutable(p);
 if(poisoned||executing_job||!type_ok||!j||j->terminal||j->generation!=generation||phase!=RacePhase::Requested){reject("unknown_old_duplicate_or_reentrant_execute",executing_job!=0,p);return;}
 j->executing=true;executing_job=p;phase=RacePhase::Executing;reason="native_callback_entered_not_success";note(RaceEvent::ExecuteBegin,reason,p);
}
void RaceEpoch::commit(uint32_t scene,bool success) noexcept {
 auto* j=find_mutable(executing_job);
 if(poisoned||!j||!j->executing||j->generation!=generation||j->commit_seen){reject("commit_without_current_execution");return;}
 j->commit_seen=true;j->commit_success=success&&scene==j->scene;committed_scene=scene;
 reason=j->commit_success?"commit_completed_await_callback_return":"default_or_failed_commit";note(RaceEvent::Commit,reason);
}
void RaceEpoch::end(uint32_t p) noexcept {
 auto* j=find_mutable(p);
 if(poisoned||!j||executing_job!=p||!j->executing||j->terminal||j->generation!=generation){reject("unmatched_execute_return",false,p);executing_job=0;return;}
 j->executing=false;j->terminal=true;executing_job=0;
 if(j->commit_seen&&j->commit_success&&phase==RacePhase::Executing){successful_generation=generation;phase=RacePhase::AwaitingOwner;reason="completed_success_owner_correlation_pending";}
 else {successful_generation=0;phase=RacePhase::Failed;reason="callback_return_without_success";}
 note(RaceEvent::ExecuteEnd,reason,p);
}
void RaceEpoch::error(uint32_t p,bool read_error) noexcept {
 auto* j=find_mutable(p);
 if(!j||j->generation!=generation||j->terminal){reject("unknown_old_or_duplicate_error",false,p);return;}
 j->commit_success=false;
 // A decode error is called *inside* execute before its RET; preserve execution bookkeeping.
 if(!j->executing)j->terminal=true;
 successful_generation=0;phase=RacePhase::Failed;reason=read_error?"native_read_or_decode_error":"native_file_open_error";
 note(read_error?RaceEvent::ReadError:RaceEvent::OpenError,reason,p);
}
void RaceEpoch::attach(uint32_t actor,uint32_t ai,bool slot_ok) noexcept {
 if(!actor||!ai||!slot_ok||!generation){reject("owner_attach_invalid_or_no_epoch");return;}
 if(owner.actor&&!owner.retired&&owner.generation==generation){reject("multiple_owner_lifetimes",true);return;}
 if(!next(owner_serial))return;
 auto* j=find_mutable(executing_job);
 owner={actor,ai,generation,owner_serial,j&&j->generation==generation?j->lifetime:0,false,false,false};
 note(RaceEvent::OwnerAttach,owner.execution_job_lifetime?"owner_constructed_inside_job":"owner_constructed_outside_job_correlation_unknown");
}
void RaceEpoch::initialized(uint32_t actor,uint32_t ai,bool valid) noexcept {
 if(actor!=owner.actor||ai!=owner.ai){reject("initializer_identity_changed");return;}
 owner.initialized=valid&&!owner.retired;note(RaceEvent::OwnerInitialized,owner.initialized?"native_initializer_returned":"native_initializer_failed_or_retired");
}
void RaceEpoch::admitted(uint32_t actor,bool valid) noexcept {
 if(actor!=owner.actor)return;
 owner.live=valid&&!owner.retired;note(RaceEvent::OwnerLive,owner.live?"unique_native_live_membership":"live_membership_rejected");
}
void RaceEpoch::retire(uint32_t actor,bool destroyed) noexcept {
 if(actor!=owner.actor||!actor)return;
 owner.retired=true;owner.live=false;
 if(owner.generation==generation){successful_generation=0;phase=RacePhase::Revoked;reason=destroyed?"owner_destroyed":"owner_retired";}
 note(destroyed?RaceEvent::Destroy:RaceEvent::Retire,owner.generation==generation?reason:"previous_epoch_owner_removed");
}
void RaceEpoch::cancel(RaceEvent e,const char* why) noexcept {successful_generation=0;phase=RacePhase::Revoked;reason=why;owner.live=false;note(e,why);}
bool RaceEpoch::correlated_owner_candidate() const noexcept {
 if(poisoned||!generation||successful_generation!=generation||phase!=RacePhase::AwaitingOwner||owner.generation!=generation||!owner.initialized||!owner.live||owner.retired||!owner.execution_job_lifetime)return false;
 for(size_t i=0;i<jobs_used;++i){const auto& j=jobs[i];if(j.generation==generation&&j.lifetime==owner.execution_job_lifetime)return j.terminal&&j.commit_success&&!j.reused;}
 return false;
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
RaceScalar race_broker_scalar(RaceReadMemory& m,uint32_t base,uint32_t id,uint32_t tag) noexcept {
 RaceScalar r;uint32_t manager=0,begin=0,count=0,payload=0,native_id=0;
 if(!word(m,base+0x2f9410,manager)||!vector(m,manager,0x1c,32768,begin,count)||id>=count)return r;
 uint32_t p=begin+id*0x1c;if(!word(m,p,native_id)||native_id!=id||!word(m,p+8,r.tag)||r.tag!=tag||!word(m,p+4,payload)||!payload)return r;
 if(tag==0){uint8_t v=0;if(!m.read(payload,&v,1)||v>1)return r;r.value=v;}
 else if(tag==2){if(!m.read(payload,&r.value,4))return r;}else return r;
 r.present=true;return r;
}
RaceOwnerRead read_race_owner(RaceReadMemory& m,uint32_t base,const RaceOwner& identity,uint64_t current_generation) noexcept {
 RaceOwnerRead r;r.actor=identity.actor;r.ai=identity.ai;
 if(!r.actor||!r.ai||identity.retired||!identity.lifetime||!current_generation||identity.generation!=current_generation){r.reason="no_current_owner_lifetime";return r;}
 uint32_t manager=0,registry=0,name=0,begin=0,count=0,bucket=0,id=0;
 if(!word(m,base+0x2f96fc,manager)||!word(m,manager+0x1c,registry)||!race_pool_id(m,base,"RaceLimits",id)||!word(m,r.actor+0x5c,name)||name!=id||!vector(m,registry,4,32768,begin,count)||id>=count||!word(m,begin+id*4,bucket)||!vector(m,bucket,4,64,begin,count)){r.reason="registry_read_or_name_failed";return r;}
 r.registrations=count;if(count!=1){r.reason="nonunique_registration";return r;}
 uint32_t registered=0;if(!word(m,begin,registered)||registered!=r.actor){r.reason="registered_owner_replaced";return r;}
 uint8_t flags=0;if(!m.read(r.actor,&flags,1)){r.reason="flags_unreadable";return r;}r.retired=(flags&2)!=0;if(r.retired){r.reason="retirement_flag";return r;}
 if(!list_count(m,manager+0x10,r.actor,r.pending_memberships)){r.reason="pending_list_malformed";return r;}
 for(uint32_t p=0;p<7;++p)if(!list_count(m,manager+0x24+p*12,r.actor,r.live_memberships)){r.reason="live_list_malformed";return r;}
 if(r.pending_memberships||r.live_memberships!=1){r.reason="pending_or_nonunique_live_membership";return r;}
 uint32_t ai=0,vtable=0;if(!word(m,r.actor+4,ai)||ai!=r.ai||!word(m,ai,vtable)||vtable!=base+0x29152c){r.reason="ai_slot_or_type_changed";return r;}r.type_ok=true;
 // Only now, after live registry/lifetime/retirement checks, probe participant allocations.
 if(!word(m,ai+0x2c,r.count)||r.count<1||r.count>8){r.reason="participant_count_invalid";return r;}
 for(uint32_t offset:{0x20u,0x24u,0x30u,0x34u,0x38u,0x3cu,0x40u}){uint32_t data=0;std::array<uint32_t,8> values{};
  if(!word(m,ai+offset,data)||!data||!m.read(data,values.data(),r.count*4)){r.reason="participant_array_unreadable";return r;}}
 for(uint32_t offset:{0x10u,0x14u,0x18u,0x1cu}){uint32_t resource=0;if(!word(m,ai+offset,resource)||!resource){r.reason="boundary_resource_missing";return r;}}
 r.arrays_ready=true;r.participant_states_ready=true;
 for(uint32_t i=0;i<r.count;++i){char key[64];std::snprintf(key,sizeof(key),"Race/Car%u/RaceState",i);uint32_t key_id=0;
  if(!race_pool_id(m,base,key,key_id)){r.participant_states_ready=false;break;}auto state=race_broker_scalar(m,base,key_id,2);
  if(!state.present){r.participant_states_ready=false;break;}r.participant_states[i]=state.value;if(state.value!=2)r.participant_states_ready=false;
 }
 r.valid=true;r.reason="unique_live_owner_arrays_readable_not_race_certificate";return r;
}
RaceContextCheck check_race_context(const std::array<RaceScalar,9>& f,const RaceOwnerRead& owner) noexcept {
 for(size_t i=0;i<f.size();++i)if(!f[i].present||f[i].tag!=RACE_CONTEXT_TAGS[i])return {false,"missing_or_wrong_type_broker_entry"};
 if(f[0].value!=2||f[1].value!=1||f[2].value!=0||f[7].value!=0)return {false,"unsupported_race_or_player_configuration"};
 for(size_t i=3;i<=6;++i)if(f[i].value!=0)return {false,"network_attract_ghost_or_replay"};
 if(!owner.valid||!owner.arrays_ready||!owner.participant_states_ready||f[8].value<1||f[8].value>8||static_cast<uint32_t>(f[8].value)!=owner.count)return {false,"participants_not_currently_ready"};
 return {true,"offline_one_player_supporting_context_not_certificate"};
}
bool RacePatchBatch::owned() const noexcept {for(size_t i=0;i<count;++i)if(sites[i].owned)return true;return false;}
bool race_observer_context_valid(PatchMemory& m,uintptr_t base) noexcept {
 if(base!=0x400000)return false;
 for(const auto& anchor:RACE_OBSERVER_CONTEXTS){std::array<unsigned char,32> expected{},actual{};size_t chars=std::strlen(anchor.bytes),n=chars/2;
  if(chars%2||n>expected.size())return false;
  auto digit=[](char c){return c>='0'&&c<='9'?c-'0':c>='a'&&c<='f'?c-'a'+10:-1;};
  for(size_t i=0;i<n;++i){auto a=digit(anchor.bytes[i*2]),b=digit(anchor.bytes[i*2+1]);if(a<0||b<0)return false;expected[i]=static_cast<unsigned char>((a<<4)|b);}
  if(!m.read(actual.data(),reinterpret_cast<void*>(base+anchor.va-0x400000),n)||std::memcmp(actual.data(),expected.data(),n))return false;
 }return true;
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
