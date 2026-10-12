#include <windows.h>
#include "physics_transaction_model.hpp"
#include "physics_inline_patch.hpp"
#include <array>
#include <cstdint>
#include <cstring>
#define CHECK(c) do { if(!(c)) return __LINE__; } while(0)
extern "C" {
uintptr_t physics_probe_restore_target=0;
uintptr_t abi_target=0;
uint32_t abi_input[8]={},abi_output[9]={},abi_stack=0,abi_flags=0,abi_argument=0x13572468;
uint32_t abi_has_argument=0,abi_seen_argument=0,abi_calls=0,abi_sites[2]={},abi_stages[2]={};
uint32_t abi_observed_flag[2]={},abi_backing_saved=0;
}
extern "C" void __cdecl physics_probe_clear_writer_observe(uint32_t,uint32_t,uint32_t) {
 __asm {
 mov eax,0DEADBEEFh
 mov ecx,0BADF00Dh
 mov edx,0ABCD0123h
 stc
 }
}
extern "C" void __cdecl physics_probe_transaction_observe(const uint32_t* saved,uint32_t site,uint32_t after) {
 if(abi_calls<2) {
  abi_sites[abi_calls]=site;abi_stages[abi_calls]=after;
  uint32_t backing=0;
  if(site==0x4CCFF1 || site==0x4CD131)backing=saved[2];
  else if(site==0x4CB62A)backing=saved[1];
  else if(site==0x591345)backing=saved[7];
  else if(!after) backing=*reinterpret_cast<uint32_t*>(saved[7]+8);
  if(!after) abi_backing_saved=backing;
  abi_observed_flag[abi_calls]=*reinterpret_cast<uint8_t*>(abi_backing_saved+0x33);
 }
 ++abi_calls;
 __asm {
  mov eax,0DEADBEEFh
  mov ecx,0BADF00Dh
  mov edx,0ABCD0123h
  stc
 }
}
extern "C" __declspec(naked) void abi_restore_callee() {
 __asm {
  mov eax,dword ptr [esp+4]
  mov dword ptr [abi_seen_argument],eax
  mov ecx,055667788h
  mov edx,099AABBCCh
  cmp eax,0
  ret 4
 }
}
#include "../src/physics_transaction_bridges.inc"
extern "C" __declspec(naked) void abi_invoke() {
 __asm {
  push ebp
  push ebx
  push esi
  push edi
  mov dword ptr [abi_stack],esp
  cmp dword ptr [abi_has_argument],0
  je no_arg
  push dword ptr [abi_argument]
 no_arg:
  mov edi,dword ptr [abi_input]
  mov esi,dword ptr [abi_input+4]
  mov ebp,dword ptr [abi_input+8]
  mov ebx,dword ptr [abi_input+16]
  mov edx,dword ptr [abi_input+20]
  mov ecx,dword ptr [abi_input+24]
  mov eax,dword ptr [abi_input+28]
  push dword ptr [abi_flags]
  popfd
  call dword ptr [abi_target]
  mov dword ptr [abi_output],edi
  mov dword ptr [abi_output+4],esi
  mov dword ptr [abi_output+8],ebp
  mov dword ptr [abi_output+16],ebx
  mov dword ptr [abi_output+20],edx
  mov dword ptr [abi_output+24],ecx
  mov dword ptr [abi_output+28],eax
  mov dword ptr [abi_output+12],esp
  pushfd
  pop dword ptr [abi_output+32]
  pop edi
  pop esi
  pop ebx
  pop ebp
  ret
 }
}

int test_capture() {
 using namespace gfx2::physics_probe;
 TransactionCapture capture{};TransactionRecord row{};
 row.before.readable=row.after.readable=true;row.before.race_valid=row.after.race_valid=true;
 row.before.race=row.after.race=7;row.before.lifetime=row.after.lifetime=1;
 row.before.backing=row.after.backing=0x10000;row.before.site=INPUT_FLAG_PATCH_VA;
 for(unsigned i=0;i<522;++i)transaction_retain(capture,row);
 CHECK(capture.zero_stores==522 && !capture.count && !capture.overflow);
 row.before.site=PUBLISH_PATCH_VA;row.after.flag=1;transaction_retain(capture,row);
 CHECK(capture.count==1 && capture.important[0].before.candidate==1);
 row.before.site=MATRIX_COMPLETE_PATCH_VA;row.before.flag=1;transaction_retain(capture,row);
 row.kind=1;row.before.site=CONTROLLER_CALL_VA;transaction_retain(capture,row);transaction_retain(capture,row);
 CHECK(capture.count==4 && capture.unknown_transitions==0);
 row.kind=0;row.before.site=INPUT_FLAG_PATCH_VA;row.after.flag=0;transaction_retain(capture,row);
 CHECK(capture.important[4].before.candidate==1);
 row.kind=1;row.before.flag=0;transaction_retain(capture,row);
 for(unsigned i=0;i<500;++i)transaction_retain(capture,row);
 CHECK(capture.count==6 && !capture.overflow && !capture.unknown_transitions);
 // New publication is a distinct invocation even if previous flag was not consumed.
 row.kind=0;row.before.site=PUBLISH_PATCH_VA;row.after.flag=1;transaction_retain(capture,row);
 CHECK(capture.important[6].before.candidate==2);
 row.before.flag=1;transaction_retain(capture,row);CHECK(capture.important[7].before.candidate==3);
 row.before.site=INPUT_FLAG_PATCH_VA;row.before.flag=0;row.after.flag=0;
 transaction_retain(capture,row);CHECK(capture.unknown_transitions==1);
 // Scene generation reuses the pointer without inheriting a candidate.
 row.before.race=row.after.race=8;row.kind=1;transaction_retain(capture,row);
 CHECK(capture.identities[0].candidate==0);
 // Repeated nonzero diagnostics cannot steal important slots.
 capture={};row.kind=0;row.before.site=INPUT_FLAG_PATCH_VA;row.before.flag=row.after.flag=1;
 capture.identities[0]={row.before.backing,row.before.race,row.before.lifetime,0,1,true,false};
 for(unsigned i=0;i<100;++i)transaction_retain(capture,row);
 CHECK(capture.diagnostic_count==16 && capture.diagnostic_overflow==84 && capture.count==0);
 row.before.site=PUBLISH_PATCH_VA;
 for(unsigned i=0;i<129;++i)transaction_retain(capture,row);
 CHECK(capture.count==128 && capture.overflow==1);
 CHECK(matrix_digest(row.before.matrix)==matrix_digest(row.after.matrix));
 row.after.matrix[15]=1;CHECK(matrix_digest(row.before.matrix)!=matrix_digest(row.after.matrix));
 return 0;
}

struct InlineMemory : gfx2::PatchMemory {
 unsigned fail_write=0,writes=0,fail_flush=0,flushes=0,fail_protect=0,protects=0;
 bool read(void* dst,const void* src,size_t n) noexcept override {std::memcpy(dst,src,n);return true;}
 bool write(void* dst,const void* src,size_t n) noexcept override {if(++writes==fail_write)return false;std::memcpy(dst,src,n);return true;}
 bool protect(void*,size_t,DWORD,DWORD& prior) noexcept override {prior=PAGE_EXECUTE_READ;return ++protects!=fail_protect;}
 bool flush(void*,size_t) noexcept override {return ++flushes!=fail_flush;}
};
int test_patches() {
 for(size_t width : {6u,7u,8u}) {
  std::array<uint8_t,8> code={1,2,3,4,5,6,7,8};
  gfx2::InlinePatchUnit unit{};unit.address=code.data();unit.size=width;unit.original=code;unit.replacement.fill(0x90);
  bool rollback=true;InlineMemory m;
  CHECK(gfx2::exchange_physics_inline(m,unit,true,rollback) && unit.owned);
  CHECK(std::memcmp(code.data(),unit.replacement.data(),width)==0);
  CHECK(gfx2::exchange_physics_inline(m,unit,false,rollback) && !unit.owned && code==unit.original);
  for(unsigned failure=0;failure<3;++failure) {
   m={};m.fail_write=failure==0?1:0;m.fail_flush=failure==1?1:0;m.fail_protect=failure==2?2:0;
   rollback=true;CHECK(!gfx2::exchange_physics_inline(m,unit,true,rollback));
   CHECK(!unit.owned && rollback && code==unit.original);
  }
  m={};code[0]=0xff;CHECK(!gfx2::exchange_physics_inline(m,unit,true,rollback) && !m.writes);
  code=unit.original;m={};CHECK(gfx2::exchange_physics_inline(m,unit,true,rollback));
  code[0]=0xff;CHECK(!gfx2::exchange_physics_inline(m,unit,false,rollback) && unit.owned);
 }
 return 0;
}
int main() {
 const int patch_result=test_patches();if(patch_result)return patch_result;
 const int capture_result=test_capture();if(capture_result)return capture_result;
 alignas(4) std::array<uint8_t,256> backing{},entry{},manager{},input{};
 auto p=[](auto& a){return static_cast<uint32_t>(reinterpret_cast<uintptr_t>(a.data()));};
 const uint32_t bp=p(backing),ep=p(entry),mp=p(manager),ip=p(input);
 std::memcpy(entry.data()+8,&bp,4);std::memcpy(input.data()+0x2c,&bp,4);
 const uint32_t marker=0x31415926,table=0x01020304;
 std::memcpy(manager.data()+0x1c,&marker,4);std::memcpy(manager.data()+0x3c,&table,4);
 using Fn=void(*)();
 const Fn bridges[]={physics_probe_clear_gate_bridge,physics_probe_clear_recovery_bridge,physics_probe_clear_timer_bridge,
  physics_probe_publish_bridge,physics_probe_matrix_complete_bridge,physics_probe_input_flag_bridge,physics_probe_restore_flag_bridge};
 const uint32_t sites[]={0x4CCC70,0x4CD1A1,0x4CD1DE,0x4CCFF1,0x4CD131,0x591345,0x4CB62A};
 physics_probe_restore_target=reinterpret_cast<uintptr_t>(&abi_restore_callee);
 for(unsigned iteration=0;iteration<128;++iteration) for(unsigned which=0;which<7;++which) {
  abi_calls=0;abi_seen_argument=0;abi_has_argument=which==6;
  abi_target=reinterpret_cast<uintptr_t>(bridges[which]);backing[0x33]=static_cast<uint8_t>(iteration&1);
  const uint8_t old=backing[0x33];abi_flags=0x202u | ((iteration&1)?0x45u:0u);
  abi_input[0]=0x24681234;abi_input[1]=which==6?bp:mp;abi_input[2]=bp;
  abi_input[4]=4;abi_input[5]=static_cast<uint32_t>(iteration&1);abi_input[6]=which==5?ip:0x12233400u;
  abi_input[7]=which==5?bp:which==6?static_cast<uint32_t>(iteration&1):ep;
  uint32_t expected[8];std::memcpy(expected,abi_input,sizeof(expected));
  uint8_t flag=old;
  switch(which) {
   case 0:expected[7]=bp;flag=0;break;
   case 1:expected[6]=bp;flag=0;break;
   case 2:expected[7]=bp;flag=0;break;
   case 3:expected[6]=marker;flag=1;break;
   case 4:expected[6]=table;expected[5]=table+4;break;
   case 5:expected[7]=bp;flag=static_cast<uint8_t>(iteration&1);break;
   case 6:flag=static_cast<uint8_t>(iteration&1);expected[7]=abi_argument;expected[6]=0x55667788;expected[5]=0x99AABBCC;break;
  }
  abi_invoke();
  CHECK(abi_calls==2 && abi_stages[0]==0 && abi_stages[1]==1);
  CHECK(abi_sites[0]==sites[which] && abi_sites[1]==sites[which]);
  CHECK(abi_observed_flag[0]==old && abi_observed_flag[1]==flag && backing[0x33]==flag);
  CHECK(abi_output[3]==abi_stack);
  for(unsigned reg=0;reg<8;++reg)if(reg!=3)CHECK(abi_output[reg]==expected[reg]);
  constexpr uint32_t arithmetic_flags=0x8d5;
  uint32_t expected_flags=abi_flags;
  if(which==4)expected_flags=(abi_flags & ~arithmetic_flags); // 0x01020304+4 has no arithmetic flags.
  if(which==6)expected_flags=(abi_flags & ~arithmetic_flags); // positive argument CMP 0, odd parity.
  CHECK((abi_output[8] & arithmetic_flags)==(expected_flags & arithmetic_flags));
  if(which==6)CHECK(abi_seen_argument==abi_argument);
 }
 return 0;
}
