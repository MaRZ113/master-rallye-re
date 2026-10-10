#include "race_epoch.hpp"
#include <iostream>
#include <stdexcept>
#include <cstring>
#include <map>
#include <vector>
#define CHECK(x) do{if(!(x))throw std::runtime_error(#x);}while(0)
using namespace gfx2;
void complete(RaceEpoch& e,uint32_t job=100,uint32_t actor=200){
 e.request(8);e.queue(job,8,11,true);e.begin(job,true);e.attach(actor,actor+8,true);
 e.initialized(actor,actor+8,true);e.commit(8,true);CHECK(e.successful_generation==0);
 e.end(job);e.admitted(actor,true);CHECK(e.correlated_owner_candidate()==(!e.poisoned&&!e.find(job)->reused));CHECK(!e.authorizes_camera_writes());
}
void epochs(){
 RaceEpoch e;CHECK(!e.correlated_owner_candidate()&&!e.authorizes_camera_writes());e.begin(100,true);CHECK(e.generation==0&&e.successful_generation==0);
 e=RaceEpoch{};complete(e);auto old_lifetime=e.owner.lifetime;auto old_generation=e.generation;
 e.request(8);CHECK(e.generation==old_generation+1&&e.successful_generation==0&&!e.correlated_owner_candidate());
 e.queue(101,8,11,true);e.error(101,false);CHECK(e.phase==RacePhase::Failed&&e.committed_scene==8&&!e.correlated_owner_candidate());
 // Relocation/countdown/old participant flags have no event capable of making success.
 e.admitted(200,true);CHECK(!e.correlated_owner_candidate());
 e.request(8);e.queue(102,8,11,true);e.begin(102,true);e.retire(200,true);CHECK(e.phase==RacePhase::Executing);
 e.attach(200,208,true);CHECK(e.owner.lifetime>old_lifetime&&e.owner.generation==e.generation);
 e.initialized(200,208,true);e.commit(8,true);e.end(102);e.admitted(200,true);CHECK(e.correlated_owner_candidate());
 e.retire(200,false);CHECK(!e.correlated_owner_candidate());
 // Completed fallback is not completed supported success.
 e=RaceEpoch{};e.request(8);e.queue(100,8,11,true);e.begin(100,true);e.commit(9,false);e.end(100);CHECK(e.phase==RacePhase::Failed&&e.successful_generation==0);
 e=RaceEpoch{};e.request(8);e.queue(100,8,11,true);e.begin(100,true);e.commit(8,true);e.error(100,true);e.end(100);CHECK(e.phase==RacePhase::Failed&&!e.successful_generation);
 e=RaceEpoch{};e.request(8);e.queue(100,8,11,true);e.begin(100,true);e.begin(100,true);CHECK(e.poisoned&&!e.successful_generation);
 // An old completion after a newer request rejects; a fresh fully observed request recovers.
 e=RaceEpoch{};e.request(8);e.queue(100,8,11,true);e.request(8);e.queue(101,8,11,true);e.begin(100,true);e.commit(8,true);e.end(100);CHECK(!e.successful_generation);
 complete(e,102,200);CHECK(e.correlated_owner_candidate());e.end(102);CHECK(!e.successful_generation); // Duplicate completion.
 e=RaceEpoch{};e.request(8);e.queue(100,8,11,false);CHECK(!e.find(100));
 e=RaceEpoch{};e.request(8);e.queue(100,8,11,true);e.queue(100,8,11,true);CHECK(!e.successful_generation);
 // Reused job address gets a new serial but cannot inherit the old proof.
 e=RaceEpoch{};complete(e);auto serial=e.job_serial;e.retire(200,true);complete(e,100,201);
 CHECK(e.job_serial>serial&&e.find(100)->reused&&!e.correlated_owner_candidate());
}
void ordering(){
 RaceEpoch e;e.request(8);e.queue(100,8,11,true);e.begin(100,true);e.commit(8,true);e.end(100);
 e.attach(200,208,true);e.initialized(200,208,true);e.admitted(200,true);
 CHECK(!e.correlated_owner_candidate()&&!e.owner.execution_job_lifetime); // Later update is NOT guessed current owner.
 e=RaceEpoch{};e.request(8);e.queue(100,8,11,true);e.begin(100,true);e.attach(200,208,true);e.commit(8,true);e.end(100);e.admitted(200,true);CHECK(!e.correlated_owner_candidate());
 e.initialized(200,208,true);CHECK(e.correlated_owner_candidate());
 e.cancel(RaceEvent::Reset,"reset");CHECK(!e.correlated_owner_candidate());e.admitted(200,true);CHECK(!e.correlated_owner_candidate());
 e.cancel(RaceEvent::Release,"release");CHECK(!e.authorizes_camera_writes());
 e=RaceEpoch{};complete(e);e.request(9);e.queue(101,9,12,true);e.begin(101,true);e.request(8);CHECK(e.poisoned&&!e.correlated_owner_candidate());
 e=RaceEpoch{};e.generation=UINT64_MAX;e.request(8);CHECK(e.poisoned&&e.generation==UINT64_MAX);
 e=RaceEpoch{};e.job_serial=UINT64_MAX;e.request(8);e.queue(100,8,11,true);CHECK(e.poisoned);
 e=RaceEpoch{};for(unsigned i=0;i<200;++i)e.request(i);CHECK(e.events_used==128&&e.chronological(0).serial==73&&e.chronological(127).serial==200);
 e=RaceEpoch{};for(unsigned i=0;i<65;++i){e.request(8);e.queue(i+1,8,11,true);e.error(i+1,false);}CHECK(e.poisoned&&e.jobs_used==64);
 e=RaceEpoch{};CHECK(e.validate_thread(7,7));CHECK(!e.validate_thread(7,8)&&e.poisoned);e.request(8);e.queue(100,8,11,true);CHECK(!e.correlated_owner_candidate());
}
void context(){
 std::array<RaceScalar,9> f{};for(size_t i=0;i<f.size();++i)f[i]={true,RACE_CONTEXT_TAGS[i],0};
 f[0].value=2;f[1].value=1;f[8].value=4;RaceOwnerRead owner{};owner.valid=owner.arrays_ready=owner.participant_states_ready=true;owner.count=4;
 CHECK(check_race_context(f,owner).supported);
 for(size_t i=0;i<f.size();++i){auto bad=f;bad[i].present=false;CHECK(!check_race_context(bad,owner).supported);bad=f;bad[i].tag=99;CHECK(!check_race_context(bad,owner).supported);}
 for(size_t i=3;i<=6;++i){auto bad=f;bad[i].value=1;CHECK(!check_race_context(bad,owner).supported);}
 for(auto pair:{std::pair<size_t,int>{0,1},{1,2},{2,1},{7,1},{8,9},{8,3}}){auto bad=f;bad[pair.first].value=pair.second;CHECK(!check_race_context(bad,owner).supported);}
 owner.participant_states_ready=false;CHECK(!check_race_context(f,owner).supported);owner.participant_states_ready=true;owner.valid=false;CHECK(!check_race_context(f,owner).supported);
}
struct ReadFixture:RaceReadMemory {
 std::map<uint32_t,uint8_t> bytes;uint32_t cursor=0x10000000;size_t array_reads=0;
 std::vector<std::pair<uint32_t,uint32_t>> arrays;
 bool read(uint32_t p,void* out,size_t n) noexcept override {
  for(auto a:arrays)if(p>=a.first&&p<a.first+a.second)++array_reads;
  for(size_t i=0;i<n;++i)if(!bytes.count(p+static_cast<uint32_t>(i)))return false;
  for(size_t i=0;i<n;++i)static_cast<uint8_t*>(out)[i]=bytes[p+static_cast<uint32_t>(i)];return true;
 }
 uint32_t alloc(size_t n){auto p=cursor;cursor+=static_cast<uint32_t>((n+15)&~15);for(size_t i=0;i<n;++i)bytes[p+static_cast<uint32_t>(i)]=0;return p;}
 void put(uint32_t p,uint32_t v){for(unsigned i=0;i<4;++i)bytes[p+i]=static_cast<uint8_t>(v>>(i*8));}
 uint32_t text(const char* s){auto n=std::strlen(s)+1;auto p=alloc(n);for(size_t i=0;i<n;++i)bytes[p+static_cast<uint32_t>(i)]=s[i];return p;}
 void vector(uint32_t p,uint32_t data,uint32_t size){put(p+4,data);put(p+8,data+size);put(p+12,data+size);}
 void sentinel(uint32_t p){put(p,0);put(p+4,p);put(p+8,p);}
 void member(uint32_t head,uint32_t actor){auto node=actor+0x60;put(head+4,node);put(head+8,node);put(node,actor);put(node+4,head);put(node+8,head);}
};
struct OwnerFixture:ReadFixture {
 uint32_t manager,actor,ai,registry,bucket,broker,broker_data,pool_data,live_head;
 RaceOwner identity{};
 OwnerFixture(){
  auto pool=alloc(12),ids=alloc(16);pool_data=alloc(4*3);put(0x6f93d4,pool);put(pool+4,ids);vector(ids,pool_data,12);
  put(pool_data,text("unused"));put(pool_data+4,text("RaceLimits"));put(pool_data+8,text("Race/Car0/RaceState"));
  broker=alloc(16);broker_data=alloc(0x1c*3);put(0x6f9410,broker);vector(broker,broker_data,0x1c*3);auto payload=alloc(4);put(payload,2);put(broker_data+0x38,2);put(broker_data+0x3c,payload);put(broker_data+0x40,2);
  manager=alloc(0x7c);put(0x6f96fc,manager);registry=alloc(16);put(manager+0x1c,registry);auto data=alloc(8);vector(registry,data,8);bucket=alloc(16);put(data+4,bucket);
  actor=alloc(0x78);ai=alloc(0x48);identity={actor,ai,1,1,1,true,true,false};put(actor+0x5c,1);auto registered=alloc(4);put(registered,actor);vector(bucket,registered,4);
  sentinel(manager+0x10);for(unsigned i=0;i<7;++i)sentinel(manager+0x24+i*12);live_head=manager+0x24;member(live_head,actor);
  put(actor+4,ai);put(ai,0x69152c);put(ai+0x2c,1);
  for(uint32_t offset:{0x20u,0x24u,0x30u,0x34u,0x38u,0x3cu,0x40u}){auto a=alloc(4);put(ai+offset,a);arrays.push_back({a,4});}
  for(uint32_t offset:{0x10u,0x14u,0x18u,0x1cu})put(ai+offset,alloc(4));
 }
};
void reads(){
 OwnerFixture m;char text[64]{};CHECK(race_pool_text(m,0x400000,1,text,64)&&!std::strcmp(text,"RaceLimits"));uint32_t id=0;CHECK(race_pool_id(m,0x400000,"RaceLimits",id)&&id==1);
 auto v=race_broker_scalar(m,0x400000,2,2);CHECK(v.present&&v.value==2);CHECK(!race_broker_scalar(m,0x400000,2,0).present);CHECK(!race_broker_scalar(m,0x400000,99,2).present);
 auto r=read_race_owner(m,0x400000,m.identity,1);CHECK(r.valid&&r.arrays_ready&&r.participant_states_ready&&r.count==1&&r.live_memberships==1);
 m.array_reads=0;CHECK(!read_race_owner(m,0x400000,m.identity,2).valid&&!m.array_reads);m.bytes[m.actor]=2;r=read_race_owner(m,0x400000,m.identity,1);CHECK(!r.valid&&m.array_reads==0);
 m.bytes[m.actor]=0;m.put(m.bucket+8,0); // malformed registry fails before arrays.
 m.array_reads=0;r=read_race_owner(m,0x400000,m.identity,1);CHECK(!r.valid&&!m.array_reads);
 OwnerFixture pending;pending.sentinel(pending.live_head);pending.member(pending.manager+0x10,pending.actor);r=read_race_owner(pending,0x400000,pending.identity,1);CHECK(!r.valid&&r.pending_memberships==1&&pending.array_reads==0);
 OwnerFixture wrong;wrong.put(wrong.ai,0x68f490);r=read_race_owner(wrong,0x400000,wrong.identity,1);CHECK(!r.valid&&!wrong.array_reads);
 OwnerFixture reused;auto identity=reused.identity;identity.retired=true;r=read_race_owner(reused,0x400000,identity,1);CHECK(!r.valid&&!reused.array_reads);
 OwnerFixture missing;missing.put(missing.ai+0x20,0);r=read_race_owner(missing,0x400000,missing.identity,1);CHECK(!r.valid);
 OwnerFixture duplicate;auto data=duplicate.alloc(8);duplicate.put(data,duplicate.actor);duplicate.put(data+4,duplicate.actor);duplicate.vector(duplicate.bucket,data,8);r=read_race_owner(duplicate,0x400000,duplicate.identity,1);CHECK(!r.valid&&!duplicate.array_reads);
 OwnerFixture changed;changed.put(changed.actor+4,changed.ai+4);r=read_race_owner(changed,0x400000,changed.identity,1);CHECK(!r.valid&&!changed.array_reads);
 OwnerFixture absent;absent.put(absent.broker_data+0x40,0);CHECK(!read_race_owner(absent,0x400000,absent.identity,1).participant_states_ready);
 OwnerFixture loop;loop.put(loop.actor+0x64,loop.actor+0x60);r=read_race_owner(loop,0x400000,loop.identity,1);CHECK(!r.valid&&!loop.array_reads);
 CHECK(!race_pool_text(loop,0x400000,999,text,64));CHECK(!race_pool_id(loop,0x400000,"absent",id));
}
struct PatchFixture:PatchMemory {
 std::array<std::array<unsigned char,5>,3> bytes{};std::array<DWORD,3> permissions{PAGE_EXECUTE_READ,PAGE_EXECUTE_READ,PAGE_READONLY};
 int writes=0,protects=0,flushes=0,fail_write=0,fail_protect=0,fail_flush=0;
 size_t index(const void* p){return (reinterpret_cast<uintptr_t>(p)-0x100000)/16;}
 bool read(void* d,const void* p,size_t n) noexcept override{std::memcpy(d,bytes[index(p)].data(),n);return true;}
 bool write(void* p,const void* s,size_t n) noexcept override{if(++writes==fail_write){std::memcpy(bytes[index(p)].data(),s,2);return false;}std::memcpy(bytes[index(p)].data(),s,n);return true;}
 bool protect(void* p,size_t,DWORD v,DWORD& old) noexcept override{if(++protects==fail_protect)return false;auto i=index(p);old=permissions[i];permissions[i]=v;return true;}
 bool flush(void*,size_t) noexcept override{return ++flushes!=fail_flush;}
 RacePatchBatch batch(){RacePatchBatch b;b.count=3;for(size_t i=0;i<3;++i){b.sites[i].address=reinterpret_cast<void*>(0x100000+i*16);b.sites[i].size=i==2?4:5;b.sites[i].original={0xe8,1,2,3,4};b.sites[i].replacement={0xe8,9,8,7,6};bytes[i]=b.sites[i].original;}return b;}
};
void patches(){
 for(int kind=0;kind<4;++kind){PatchFixture m;auto b=m.batch();auto before=m.bytes;if(kind==0)m.fail_write=2;if(kind==1)m.fail_protect=3;if(kind==2)m.fail_flush=2;if(kind==3)m.fail_protect=4;
  CHECK(!b.install(m)&&b.rollback_verified&&!b.owned());CHECK(m.bytes==before);for(size_t i=0;i<3;++i)CHECK(m.permissions[i]==(i==2?PAGE_READONLY:PAGE_EXECUTE_READ));}
 PatchFixture m;auto b=m.batch();CHECK(b.install(m)&&b.owned());auto before=m.bytes;m.bytes[2][2]^=1;auto changed=m.bytes;CHECK(!b.remove(m)&&m.bytes==changed);m.bytes=before;CHECK(b.remove(m)&&!b.owned());
 auto mismatch=m.batch();auto writes=m.writes;auto protects=m.protects;m.bytes[1][0]^=1;CHECK(!mismatch.install(m)&&m.writes==writes&&m.protects==protects); // Batch preflight is nonmutating.
 CHECK(!install_race_observer(false,true));CHECK(!install_race_observer(true,false));
 CHECK(!install_race_observer(true,true));release_race_observer(); // Real host cannot bypass expected game bytes.
}
struct AnchorFixture:PatchMemory {
 std::map<uintptr_t,std::vector<unsigned char>> bytes;
 AnchorFixture(){for(auto& a:RACE_OBSERVER_CONTEXTS){std::vector<unsigned char> b;for(size_t i=0;i<std::strlen(a.bytes);i+=2){char h[3]={a.bytes[i],a.bytes[i+1],0};b.push_back(static_cast<unsigned char>(std::stoul(h,nullptr,16)));}bytes[a.va]=b;}}
 bool read(void* d,const void* s,size_t n) noexcept override {auto i=bytes.find(reinterpret_cast<uintptr_t>(s));if(i==bytes.end()||n!=i->second.size())return false;std::memcpy(d,i->second.data(),n);return true;}
 bool write(void*,const void*,size_t) noexcept override{return false;}
 bool protect(void*,size_t,DWORD,DWORD&) noexcept override{return false;}
 bool flush(void*,size_t) noexcept override{return false;}
};
void anchors(){
 AnchorFixture m;CHECK(race_observer_context_valid(m,0x400000));CHECK(!race_observer_context_valid(m,0x500000));
 for(auto& a:RACE_OBSERVER_CONTEXTS){m.bytes[a.va][0]^=1;CHECK(!race_observer_context_valid(m,0x400000));m.bytes[a.va][0]^=1;}
}
namespace {
uint32_t native_calls=0,callbacks=0,callback_alignment=0,last_kind=0,native_ecx=0,native_edx=0,native_flags=0,output_flags=0;
uint32_t native_ebx=0,native_esi=0,native_edi=0,native_ebp=0,args[3]{},after_eax=0,after_edx=0,after_flags=0,stack_before=0,stack_after=0;
alignas(16) unsigned char host_fp[512],input_fp[512],native_fp[512],output_fp[512],after_fp[512];
alignas(16) unsigned int mxcsr_input=0x3f80,mxcsr_output=0x5f80;
uintptr_t selected_bridge=0;bool callback_enabled=true,want_reentry=false,in_reentry=false;
race_bridge::Saved callback_input{};
void __stdcall callback_body(uint32_t kind,const race_bridge::Saved* input){++callbacks;last_kind=kind;if(callback_enabled)callback_input=*input;
 if(kind==12&&want_reentry&&!in_reentry){in_reentry=true;race_bridge::execute();in_reentry=false;}
 __asm {fninit} __asm {fldz} __asm {pxor xmm0,xmm0} __asm {pxor xmm7,xmm7} __asm {clc}
}
__declspec(naked) void callback_fixture(){__asm {mov eax,esp} __asm {and eax,15} __asm {mov callback_alignment,eax} __asm {jmp callback_body}}
#define NATIVE_BODY \
 __asm {mov native_ecx,ecx} __asm {mov native_edx,edx} \
 __asm {mov native_ebx,ebx} __asm {mov native_esi,esi} __asm {mov native_edi,edi} __asm {mov native_ebp,ebp} \
 __asm {pushfd} __asm {pop native_flags} __asm {fxsave native_fp} \
 __asm {inc native_calls} __asm {fninit} __asm {fldlg2} __asm {ldmxcsr mxcsr_output} \
 __asm {pxor xmm0,xmm0} __asm {pcmpeqd xmm7,xmm7} \
 __asm {mov eax,012345678h} __asm {mov edx,0aabbccddh} \
 __asm {cmp eax,eax} __asm {pushfd} __asm {pop output_flags} __asm {fxsave output_fp}
__declspec(naked) void original0(){NATIVE_BODY __asm {ret}}
__declspec(naked) void original1(){__asm {mov eax,[esp+4]} __asm {mov args,eax} NATIVE_BODY __asm {ret 4}}
__declspec(naked) void original2(){__asm {mov eax,[esp+4]} __asm {mov args,eax} __asm {mov eax,[esp+8]} __asm {mov args+4,eax} NATIVE_BODY __asm {ret 8}}
__declspec(naked) void original3(){__asm {mov eax,[esp+4]} __asm {mov args,eax} __asm {mov eax,[esp+8]} __asm {mov args+4,eax} __asm {mov eax,[esp+12]} __asm {mov args+8,eax} NATIVE_BODY __asm {ret 12}}
#define START \
 __asm {pushfd} __asm {pushad} __asm {mov stack_before,esp} __asm {fxsave host_fp} \
 __asm {fninit} __asm {fld1} __asm {fldpi} __asm {ldmxcsr mxcsr_input} \
 __asm {pcmpeqd xmm0,xmm0} __asm {pxor xmm7,xmm7} __asm {fxsave input_fp} \
 __asm {mov ecx,011223344h} __asm {mov edx,055667788h} __asm {mov ebx,010203040h} \
 __asm {mov esi,020304050h} __asm {mov edi,030405060h} __asm {mov ebp,040506070h} __asm {stc}
#define FINISH \
 __asm {mov after_eax,eax} __asm {mov after_edx,edx} __asm {pushfd} __asm {pop after_flags} \
 __asm {fxsave after_fp} __asm {mov stack_after,esp} __asm {fxrstor host_fp} __asm {popad} __asm {popfd} __asm {ret}
__declspec(naked) void run0(){START __asm {call selected_bridge} FINISH}
__declspec(naked) void run1(){START __asm {push 03f123456h} __asm {call selected_bridge} FINISH}
__declspec(naked) void run2(){START __asm {push 055aa55aah} __asm {push 03f123456h} __asm {call selected_bridge} FINISH}
__declspec(naked) void run3(){START __asm {push 022332233h} __asm {push 055aa55aah} __asm {push 03f123456h} __asm {call selected_bridge} FINISH}
bool fp_equal(const unsigned char* a,const unsigned char* b){
 if(std::memcmp(a,b,5)||std::memcmp(a+6,b+6,8)||std::memcmp(a+16,b+16,6)||std::memcmp(a+24,b+24,8))return false;
 for(unsigned i=0;i<8;++i)if(std::memcmp(a+32+i*16,b+32+i*16,10))return false;
 return !std::memcmp(a+160,b+160,128);
}
void bridge_case(uintptr_t bridge,uintptr_t& target,uintptr_t original,void(*run)(),uint32_t kind,uint32_t expected_callbacks,unsigned nargs){
 selected_bridge=bridge;target=original;native_calls=callbacks=0;race_bridge::callback=reinterpret_cast<race_bridge::Callback>(&callback_fixture);run();
 CHECK(native_calls==(want_reentry?2u:1u)&&callbacks==expected_callbacks&&last_kind==kind&&callback_alignment==12);
 CHECK(native_ecx==0x11223344&&native_edx==0x55667788&&(native_flags&1));
 CHECK(native_ebx==0x10203040&&native_esi==0x20304050&&native_edi==0x30405060&&native_ebp==0x40506070);
 CHECK(after_eax==0x12345678&&after_edx==0xaabbccdd&&after_flags==output_flags&&stack_before==stack_after);
 CHECK(fp_equal(input_fp,native_fp)&&fp_equal(output_fp,after_fp));
 if(nargs)CHECK(args[0]==0x3f123456);if(nargs>1)CHECK(args[1]==0x55aa55aa);if(nargs>2)CHECK(args[2]==0x22332233);
 if(callback_enabled){CHECK(callback_input.ecx==0x11223344&&callback_input.edx==0x55667788);if(nargs)CHECK(callback_input.args[0]==0x3f123456);}
}
void bridges(){
 using namespace race_bridge;
 for(bool enabled:{true,false}){callback_enabled=enabled;
  for(unsigned frame=0;frame<3;++frame){
   bridge_case(reinterpret_cast<uintptr_t>(&execute),execute_original,reinterpret_cast<uintptr_t>(&original0),&run0,13,2,0);
   bridge_case(reinterpret_cast<uintptr_t>(&commit),commit_original,reinterpret_cast<uintptr_t>(&original1),&run1,3,2,1);
   bridge_case(reinterpret_cast<uintptr_t>(&attach),attach_original,reinterpret_cast<uintptr_t>(&original2),&run2,5,2,2);
   bridge_case(reinterpret_cast<uintptr_t>(&live),live_original,reinterpret_cast<uintptr_t>(&original1),&run1,6,2,1);
   bridge_case(reinterpret_cast<uintptr_t>(&request),request_original,reinterpret_cast<uintptr_t>(&original1),&run1,0,1,1);
   bridge_case(reinterpret_cast<uintptr_t>(&queue),queue_original,reinterpret_cast<uintptr_t>(&original3),&run3,1,1,3);
   bridge_case(reinterpret_cast<uintptr_t>(&retire),retire_original,reinterpret_cast<uintptr_t>(&original0),&run0,8,1,0);
   bridge_case(reinterpret_cast<uintptr_t>(&destroy),destroy_original,reinterpret_cast<uintptr_t>(&original0),&run0,9,1,0);
   bridge_case(reinterpret_cast<uintptr_t>(&open_error),open_error_original,reinterpret_cast<uintptr_t>(&original0),&run0,10,1,0);
   bridge_case(reinterpret_cast<uintptr_t>(&read_error),read_error_original,reinterpret_cast<uintptr_t>(&original0),&run0,11,1,0);
  }
 }
 callback_enabled=true;want_reentry=true;
 bridge_case(reinterpret_cast<uintptr_t>(&execute),execute_original,reinterpret_cast<uintptr_t>(&original0),&run0,13,4,0);
 want_reentry=false;
}
}
int main(int argc,char** argv){try{
 if(argc==2&&!std::strcmp(argv[1],"--snapshot-json")){std::cout<<race_epoch_capture_json(17,42)<<'\n';return 0;}
 epochs();ordering();reads();context();patches();anchors();bridges();std::cout<<"Race epochs / stale success and failure / owner lifetime and pending/live lists / readonly Broker / patch rollback / 61 real x86 ABI cases: PASS\n";return 0;
}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
