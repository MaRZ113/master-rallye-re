#include "broker_null_guard.hpp"
#include <algorithm>
#include <array>
#include <cstring>
#include <iostream>
#include <map>
#include <stdexcept>

#define CHECK(x) do { if (!(x)) throw std::runtime_error(#x); } while (0)
using namespace gfx2;

namespace {
constexpr uintptr_t BASE=0x00400000;
constexpr std::array<unsigned char,8> STRING_CONTEXT={0x8b,0x7b,0x04,0x3b,0x7b,0x08,0x74,0x1a};
constexpr std::array<unsigned char,6> STRING_EMPTY={0x8b,0x15,0x84,0x7b,0x6f,0x00};
constexpr std::array<unsigned char,13> XML_CONTEXT={0x8b,0x10,0x8b,0xc8,0xff,0x52,0x0c,0x8b,0xf8,0x85,0xff,0x74,0x2e};
constexpr std::array<unsigned char,5> XML_NULL={0x8b,0x4c,0x24,0x0c,0x51};
int32_t i32(const unsigned char* p){int32_t v=0;std::memcpy(&v,p,4);return v;}
uintptr_t rel_target(uintptr_t next,const unsigned char* p){return static_cast<uintptr_t>(static_cast<int64_t>(next)+i32(p));}

struct Memory final : PatchMemory, BrokerCodeMemory {
 std::map<uintptr_t,unsigned char> bytes;
 uintptr_t next_code=0x10001000;
 uintptr_t fail_write_address=0,fail_protect_address=0;
 bool fail_write_once=false,fail_flush_once=false;
 unsigned writes=0,allocations=0,seals=0,discards=0,flushes=0;
 bool read(void* out,const void* from,size_t size) noexcept override {
  uintptr_t p=reinterpret_cast<uintptr_t>(from);auto* dst=static_cast<unsigned char*>(out);
  for(size_t i=0;i<size;++i){auto found=bytes.find(p+i);if(found==bytes.end())return false;dst[i]=found->second;}return true;
 }
 bool write(void* to,const void* in,size_t size) noexcept override {
  ++writes;uintptr_t p=reinterpret_cast<uintptr_t>(to);const auto* src=static_cast<const unsigned char*>(in);
  if(fail_write_once&&p==fail_write_address){for(size_t i=0;i<std::min<size_t>(2,size);++i)bytes[p+i]=src[i];fail_write_once=false;return false;}
  for(size_t i=0;i<size;++i)bytes[p+i]=src[i];return true;
 }
 bool protect(void* at,size_t,DWORD,DWORD& old) noexcept override {
  if(reinterpret_cast<uintptr_t>(at)==fail_protect_address)return false;old=PAGE_EXECUTE_READ;return true;
 }
 bool flush(void*,size_t) noexcept override {++flushes;if(fail_flush_once){fail_flush_once=false;return false;}return true;}
 uintptr_t allocate(size_t size) noexcept override {++allocations;uintptr_t p=next_code;next_code+=0x1000;for(size_t i=0;i<size;++i)bytes[p+i]=0;return p;}
 bool seal(uintptr_t,size_t) noexcept override {++seals;return true;}
 void discard(uintptr_t p) noexcept override {++discards;for(size_t i=0;i<0x1000;++i)bytes.erase(p+i);}
 template<size_t N> void put(uintptr_t address,const std::array<unsigned char,N>& data){for(size_t i=0;i<N;++i)bytes[address+i]=data[i];}
 template<size_t N> bool equals(uintptr_t address,const std::array<unsigned char,N>& data) const {
  for(size_t i=0;i<N;++i){auto found=bytes.find(address+i);if(found==bytes.end()||found->second!=data[i])return false;}return true;
 }
};
struct Threads final : AttractThreadGate {
 bool accept=true;unsigned enters=0,leaves=0;uintptr_t begin=0;size_t size=0;
 bool enter(uintptr_t p,size_t n) noexcept override {++enters;begin=p;size=n;return accept;}
 void leave() noexcept override {++leaves;}
};
void seed_string(Memory& m){m.put(BROKER_STRINGLIST_SITE_VA,STRING_CONTEXT);m.put(BROKER_STRINGLIST_EMPTY_VA,STRING_EMPTY);}
void seed_xml(Memory& m){m.put(BROKER_XMLDATA_SITE_VA,XML_CONTEXT);m.put(BROKER_XMLDATA_NULL_VA,XML_NULL);}

void stubs(){
 BrokerNullStub s{};constexpr uintptr_t string_stub=0x10001000,counter=0x10002000;
 CHECK(build_broker_null_stub(BrokerNullSite::StringList,string_stub,counter,s)&&s.size==33);
 CHECK(s.bytes[0]==0x85&&s.bytes[1]==0xdb&&s.bytes[2]==0x0f&&s.bytes[3]==0x85);
 CHECK(static_cast<uintptr_t>(static_cast<int64_t>(string_stub+8)+i32(s.bytes.data()+4))==string_stub+22);
 CHECK(s.bytes[8]==0x9c&&s.bytes[9]==0xf0&&s.bytes[10]==0xff&&s.bytes[11]==0x05&&s.bytes[16]==0x9d&&s.bytes[17]==0xe9);
 CHECK(rel_target(string_stub+22,s.bytes.data()+18)==BROKER_STRINGLIST_EMPTY_VA);
 constexpr unsigned char original_ops[]={0x8b,0x7b,0x04,0x3b,0x7b,0x08};CHECK(!std::memcmp(s.bytes.data()+22,original_ops,sizeof(original_ops)));
 CHECK(s.bytes[28]==0xe9&&rel_target(string_stub+33,s.bytes.data()+29)==BROKER_STRINGLIST_SITE_VA+6);

 constexpr uintptr_t xml_stub=0x10003000;CHECK(build_broker_null_stub(BrokerNullSite::XmlData,xml_stub,counter,s)&&s.size==37);
 CHECK(s.bytes[0]==0x9c&&s.bytes[1]==0x85&&s.bytes[2]==0xc0&&s.bytes[3]==0x0f&&s.bytes[4]==0x84);
 CHECK(static_cast<uintptr_t>(static_cast<int64_t>(xml_stub+9)+i32(s.bytes.data()+5))==xml_stub+22);
 CHECK(s.bytes[9]==0x9d&&s.bytes[10]==0x8b&&s.bytes[11]==0x10&&s.bytes[12]==0x8b&&s.bytes[13]==0xc8);
 CHECK(s.bytes[14]==0x68&&*reinterpret_cast<uint32_t*>(s.bytes.data()+15)==BROKER_XMLDATA_CONTINUE_VA);
 CHECK(s.bytes[19]==0xff&&s.bytes[20]==0x62&&s.bytes[21]==0x0c);
 CHECK(s.bytes[22]==0x9d&&s.bytes[23]==0x9c&&s.bytes[24]==0xf0&&s.bytes[31]==0x9d&&s.bytes[32]==0xe9);
 CHECK(rel_target(xml_stub+37,s.bytes.data()+33)==BROKER_XMLDATA_NULL_VA);
 CHECK(BASE+ATTRACT_PATCH_RVA!=BROKER_STRINGLIST_SITE_VA&&BASE+ATTRACT_PATCH_RVA!=BROKER_XMLDATA_SITE_VA);
}
void install_restore(){
 Memory m;Threads t;seed_string(m);BrokerNullSiteState state;
 CHECK(apply_broker_null_guard(m,m,t,BrokerNullSite::StringList,BASE,true,0x10002000,state));
 CHECK(state.context_verified&&state.installed&&state.reason==std::string("installed")&&t.enters==1&&t.leaves==1);
 std::array<unsigned char,6> detour{};CHECK(m.read(detour.data(),reinterpret_cast<void*>(BROKER_STRINGLIST_SITE_VA),detour.size()));
 CHECK(detour[0]==0xe9&&detour[5]==0x90&&rel_target(BROKER_STRINGLIST_SITE_VA+5,detour.data()+1)==state.stub);
 CHECK(restore_broker_null_guard(m,t,state)&&!state.installed&&state.original_bytes_restored&&state.reason==std::string("restored"));
 CHECK(m.equals(BROKER_STRINGLIST_SITE_VA,STRING_CONTEXT)&&t.enters==2&&t.leaves==2);

 Memory xml;Threads xml_threads;seed_xml(xml);BrokerNullSiteState xml_state;
 CHECK(apply_broker_null_guard(xml,xml,xml_threads,BrokerNullSite::XmlData,BASE,true,0x10002000,xml_state));
 CHECK(xml_state.context_verified&&xml_state.installed&&xml_state.patch_size==7);
 CHECK(restore_broker_null_guard(xml,xml_threads,xml_state)&&xml.equals(BROKER_XMLDATA_SITE_VA,XML_CONTEXT));
}
void independent_fail_closed(){
 Memory m;Threads threads;seed_string(m);BrokerNullSiteState s;
 m.bytes[BROKER_STRINGLIST_SITE_VA+1]=0x72;
 CHECK(apply_broker_null_guard(m,m,threads,BrokerNullSite::StringList,BASE,true,0x10002000,s));
 CHECK(!s.context_verified&&!s.installed&&s.reason==std::string("exact_context_or_continuation_mismatch")&&m.allocations==0&&m.writes==0);
 seed_xml(m);BrokerNullSiteState x;CHECK(apply_broker_null_guard(m,m,threads,BrokerNullSite::XmlData,BASE,true,0x10002000,x));CHECK(x.installed);
 CHECK(restore_broker_null_guard(m,threads,x));

 Memory refused;Threads no_quiescence;seed_string(refused);no_quiescence.accept=false;BrokerNullSiteState q;
 CHECK(apply_broker_null_guard(refused,refused,no_quiescence,BrokerNullSite::StringList,BASE,true,0x10002000,q));
 CHECK(!q.installed&&q.reason==std::string("thread_quiescence_unavailable_or_site_active")&&refused.equals(BROKER_STRINGLIST_SITE_VA,STRING_CONTEXT)&&no_quiescence.leaves==1&&refused.discards==1);
}
void rollback_and_ownership(){
 Memory m;Threads t;seed_xml(m);BrokerNullSiteState s;m.fail_write_address=BROKER_XMLDATA_SITE_VA;m.fail_write_once=true;
 CHECK(apply_broker_null_guard(m,m,t,BrokerNullSite::XmlData,BASE,true,0x10002000,s));
 CHECK(!s.installed&&s.rollback_performed&&s.rollback_verified&&s.reason==std::string("install_failed_rollback_verified")&&m.equals(BROKER_XMLDATA_SITE_VA,XML_CONTEXT));

 Memory owned;Threads threads;seed_string(owned);BrokerNullSiteState state;
 CHECK(apply_broker_null_guard(owned,owned,threads,BrokerNullSite::StringList,BASE,true,0x10002000,state)&&state.installed);
 owned.bytes[BROKER_STRINGLIST_SITE_VA+1]^=1;
 CHECK(!restore_broker_null_guard(owned,threads,state)&&state.installed&&state.reason==std::string("restore_refused_patch_ownership_lost"));
}
}
int main(){try{stubs();install_restore();independent_fail_closed();rollback_and_ownership();std::cout<<"Broker NULL guard stub control flow / exact contexts / independent installation / quiescence / rollback / owned restoration / AttractMode separation: PASS\n";return 0;}catch(const std::exception& e){std::cerr<<e.what()<<"\n";return 1;}}
