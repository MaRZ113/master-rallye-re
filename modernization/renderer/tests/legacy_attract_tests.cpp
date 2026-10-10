#include "legacy_attract_guard.hpp"
#include "legacy_attract_bytes.hpp"
#include <map>
#include <vector>
#include <cstring>
#include <iostream>
#include <stdexcept>
using namespace gfx2;
#define CHECK(x) do{if(!(x))throw std::runtime_error(#x);}while(0)
struct Memory:PatchMemory {
 std::map<uintptr_t,unsigned char> bytes;unsigned reads=0,writes=0,protects=0,flushes=0;int bad_write=0,bad_protect=0,bad_flush=0;DWORD permission=PAGE_EXECUTE_READ;
 void put(uintptr_t a,const void* data,size_t n){auto* p=static_cast<const unsigned char*>(data);for(size_t i=0;i<n;++i)bytes[a+i]=p[i];}
 void word(uintptr_t a,uint32_t v){put(a,&v,4);}
 Memory(){
  put(0x464e40,ATTRACT_LOADING_BYTES,sizeof(ATTRACT_LOADING_BYTES));word(0x6f6030,0);word(0x6f9d80,0x100000);
  word(0x100000,0x69228c);word(0x100004,1);word(0x100064,0);word(0x100068,0);
  const unsigned char factory[]={0x6a,0x78,0x89,0x6b,0x18,0x89,0x6b,0x64,0x89,0x6b,0x68,0x89,0x6b,0x60,0xc6,0x43,0x24,0x00,0xc6,0x43,0x25,0x00,0x89,0xab,0x60,0x01,0x00,0x00,0xe8,0xe4,0xc1,0x07,0x00};
  const unsigned char thunk[]={0xff,0x25,0x14,0xf4,0x68,0x00};put(0x55903f,factory,sizeof(factory));put(0x5d5244,thunk,sizeof(thunk));
 }
 bool read(void* d,const void* s,size_t n) noexcept override {++reads;auto a=reinterpret_cast<uintptr_t>(s);auto* p=static_cast<unsigned char*>(d);for(size_t i=0;i<n;++i){auto it=bytes.find(a+i);if(it==bytes.end())return false;p[i]=it->second;}return true;}
 bool write(void* d,const void* s,size_t n) noexcept override {++writes;if(bad_write==static_cast<int>(writes)){if(n)put(reinterpret_cast<uintptr_t>(d),s,1);return false;}put(reinterpret_cast<uintptr_t>(d),s,n);return true;}
 bool protect(void* p,size_t n,DWORD value,DWORD& old) noexcept override {CHECK(reinterpret_cast<uintptr_t>(p)==0x464f69&&n==5);++protects;old=permission;if(bad_protect==static_cast<int>(protects))return false;permission=value;return true;}
 bool flush(void* p,size_t n) noexcept override {CHECK(reinterpret_cast<uintptr_t>(p)==0x464f69&&n==5);++flushes;return bad_flush!=static_cast<int>(flushes);}
};
struct Gate:AttractThreadGate {bool safe=true;unsigned enters=0,leaves=0;Memory* change=nullptr;
 bool enter(uintptr_t a,size_t n) noexcept override {CHECK(a==0x464e40&&n==374);++enters;if(change)change->word(0x6f6030,1);return safe;}
 void leave() noexcept override {++leaves;}
};
int main(){try{
 {Memory m;Gate g;auto before=m.bytes;auto r=apply_attract_guard(m,g,0x400000,0x559060,true);
  CHECK(r.applied&&r.owned&&r.quiesced&&r.phase_verified&&r.context_verified&&r.rollback_verified);
  CHECK(m.writes==1&&m.protects==2&&m.flushes==1&&m.permission==PAGE_EXECUTE_READ&&g.enters==1&&g.leaves==1);
  for(auto& entry:before)if(entry.first<0x464f69||entry.first>=0x464f6e)CHECK(m.bytes[entry.first]==entry.second);
  unsigned char jump[5]{};CHECK(m.read(jump,reinterpret_cast<void*>(0x464f69),5));int32_t displacement=0;std::memcpy(&displacement,jump+1,4);
  CHECK(jump[0]==0xe9&&0x464f69+5+displacement==0x464f46);
  auto repeated=apply_attract_guard(m,g,0x400000,0x559060,true);CHECK(!repeated.applied&&m.writes==1&&!std::strcmp(repeated.reason,"already_redirected_unowned_no_overwrite"));
 }
 {Memory m;Gate g;auto r=apply_attract_guard(m,g,0x400000,0x559060,false);CHECK(!r.applied&&m.reads==0&&m.writes==0&&g.enters==0);}
 for(auto caller:{uintptr_t(0),uintptr_t(0x55905b),uintptr_t(0x559061)}){Memory m;Gate g;CHECK(!apply_attract_guard(m,g,0x400000,caller,true).applied&&m.writes==0&&g.enters==0);}
 {Memory m;Gate g;CHECK(!apply_attract_guard(m,g,0x500000,0x559060,true).applied&&m.writes==0);}
 for(auto address:{uintptr_t(0x6f6030),uintptr_t(0x100005),uintptr_t(0x100006),uintptr_t(0x100064),uintptr_t(0x100068),uintptr_t(0x100000)}){
  Memory m;Gate g;m.word(address,1);CHECK(!apply_attract_guard(m,g,0x400000,0x559060,true).applied&&m.writes==0&&g.enters==0);
 }
 for(size_t i=0;i<sizeof(ATTRACT_LOADING_BYTES);++i){Memory m;Gate g;m.bytes[0x464e40+i]^=1;CHECK(!apply_attract_guard(m,g,0x400000,0x559060,true).applied&&m.writes==0&&g.enters==0);}
 {Memory m;Gate g;g.safe=false;CHECK(!apply_attract_guard(m,g,0x400000,0x559060,true).applied&&m.writes==0&&g.enters==1&&g.leaves==1);}
 {Memory m;Gate g;g.change=&m;CHECK(!apply_attract_guard(m,g,0x400000,0x559060,true).applied&&m.writes==0&&g.leaves==1);}
 for(int mode:{0,1,2,3}){Memory m;Gate g;auto before=m.bytes;if(mode==0)m.bad_protect=1;if(mode==1)m.bad_write=1;if(mode==2)m.bad_flush=1;if(mode==3)m.bad_protect=2;
  auto r=apply_attract_guard(m,g,0x400000,0x559060,true);CHECK(!r.applied&&r.rollback_verified&&m.bytes==before&&m.permission==PAGE_EXECUTE_READ&&g.leaves==1);
 }
 {Memory m;Gate g;m.bad_write=1;m.bad_protect=3;auto r=apply_attract_guard(m,g,0x400000,0x559060,true);CHECK(!r.applied&&!r.rollback_verified&&!std::strcmp(r.reason,"install_failed_rollback_unverified_restart_required"));}
 CHECK(install_legacy_attract_guard(0));CHECK(install_legacy_attract_guard(0)); // Unsupported host still allows forwarding, one-time.
 std::cout<<"R-ATTR1 production patch, startup phase, every-byte context, quiescence, rollback and ownership contracts: PASS\n";return 0;
 }catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
