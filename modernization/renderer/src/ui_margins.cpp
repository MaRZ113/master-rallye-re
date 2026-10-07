#include "ui_margins.hpp"
#include "margin_rules.hpp"
#include "provenance.hpp"
#include <cmath>
#include <cstring>
#include <sstream>
#include <cfenv>
namespace gfx2 {
namespace {struct MarginFP {fenv_t saved;MarginFP(){fegetenv(&saved);}~MarginFP(){fesetenv(&saved);}};}
int margin_direction(float x,float y,float z) noexcept {
 if(z!=0||!std::isfinite(x)||!std::isfinite(y))return 0;
 for(const auto& rule:MARGIN_RULES)if(x==rule.x&&y==rule.y)return rule.direction;
 if(x>=25&&x<=106&&((y>=19&&y<100)||(y>=259&&y<340)))return -1;return 0;
}
bool eligible_ui_packet(uintptr_t entity,uintptr_t coordinates) noexcept {
 uintptr_t packet=0;uint32_t mode=0;
 return entity&&safe_copy(&packet,reinterpret_cast<void*>(entity+0x4c),4)&&packet&&
  coordinates==packet+0x24&&safe_copy(&mode,reinterpret_cast<void*>(packet+0x68),4)&&(mode==1||mode==2);
}
bool UiJumpPatch::exchange(PatchMemory& m,const std::array<unsigned char,5>& from,const std::array<unsigned char,5>& to) noexcept {
 std::array<unsigned char,5> seen{};DWORD old=0,ignored=0;
 if(!m.read(seen.data(),site_,5)||seen!=from||!m.protect(site_,5,PAGE_EXECUTE_READWRITE,old))return false;
 bool okay=m.write(site_,to.data(),5)&&m.flush(site_,5)&&m.read(seen.data(),site_,5)&&seen==to;
 bool protected_ok=m.protect(site_,5,old,ignored);
 if(!okay||!protected_ok){DWORD roll=0;if(m.protect(site_,5,PAGE_EXECUTE_READWRITE,roll)){m.write(site_,from.data(),5);m.flush(site_,5);m.protect(site_,5,old,ignored);}okay=false;}
 if(m.read(seen.data(),site_,5))installed_=seen==after_;return okay;
}
bool UiJumpPatch::install(PatchMemory& m,void* site,uintptr_t destination) noexcept {
 if(installed_||!site||!destination)return false;site_=site;after_[0]=0xe9;
 uint32_t relative=static_cast<uint32_t>(destination)-static_cast<uint32_t>(reinterpret_cast<uintptr_t>(site)+5);std::memcpy(after_.data()+1,&relative,4);return exchange(m,UI_SORT_BYTES,after_);
}
bool UiJumpPatch::remove(PatchMemory& m) noexcept{return !installed_||exchange(m,after_,UI_SORT_BYTES);}
bool MarginFrame::shift(float* xyz,float half) noexcept {
 if(!std::isfinite(half)||half==0)return false;
 for(size_t i=0;i<count_;++i)if(edits_[i].x==xyz)return false;
 float point[3]{};if(!xyz||!safe_copy(point,xyz,sizeof(point)))return false;
 int direction=margin_direction(point[0],point[1],point[2]);if(!direction)return false;
 if(count_==edits_.size()){++overflow;return false;}
 float value=point[0]+half*direction;if(!std::isfinite(value))return false;
 auto& e=edits_[count_++];e={xyz,point[0],value,point[1],point[2]};float check=0;
 if(!safe_copy(xyz,&value,4)||!safe_copy(&check,xyz,4)||std::memcmp(&check,&value,4)){
  ++failures;safe_copy(xyz,&point[0],4);return false;
 }
 ++changed;return true;
}
bool MarginFrame::restore() noexcept {
 bool okay=true;for(size_t i=0;i<count_;++i){auto& e=edits_[i];float seen[3]{};
  if(!safe_copy(seen,e.x,sizeof(seen))){okay=false;continue;}
  // An intervening engine write owns its new coordinates. Never overwrite it.
  if(std::memcmp(seen,&e.effective,4)||std::memcmp(seen+1,&e.y,4)||std::memcmp(seen+2,&e.z,4))continue;
  if(!safe_copy(e.x,&e.original,4)||!safe_copy(seen,e.x,4)||std::memcmp(seen,&e.original,4))okay=false;
 }count_=0;if(!okay)++failures;return okay;
}
namespace {
class NativeMemory final:public PatchMemory {public:
 bool read(void* d,const void* s,size_t n) noexcept override{return safe_copy(d,s,n);}
 bool write(void* d,const void* s,size_t n) noexcept override{return safe_copy(d,s,n);}
 bool protect(void* p,size_t n,DWORD v,DWORD& old) noexcept override{return VirtualProtect(p,n,v,&old)!=FALSE;}
 bool flush(void* p,size_t n) noexcept override{return FlushInstructionCache(GetCurrentProcess(),p,n)!=FALSE;}
} memory;
UiMargins* active=nullptr;
bool multiple=false;
uintptr_t sort_return=0;
void __stdcall shift_packet(uintptr_t entity,uintptr_t coordinates) noexcept {if(active)active->before_sort(entity,coordinates);}
// Preserve flags, integer registers, stack, x87 and SSE. Replay exactly the two
// overwritten instructions with the original x87 stack before returning.
__declspec(naked) void sort_bridge(){__asm {
 pushfd
 pushad
 mov ebp,esp
 and esp,-16
 sub esp,528
 fxsave [esp]
 fninit
 mov dword ptr [esp+512],01f80h
 ldmxcsr [esp+512]
 cld
 push dword ptr [ebp+28]
 push dword ptr [ebp+24]
 call shift_packet
 fxrstor [esp]
 mov esp,ebp
 popad
 popfd
 fsub dword ptr [eax+30h]
 fld st(0)
 jmp dword ptr [sort_return]
}}
}
bool UiMargins::install(bool exact,bool requested) noexcept {
 if(!requested||!exact){reason=exact?"disabled":"unsupported_build";return false;}
 if(active||multiple){multiple=true;if(active)active->disable("multiple_devices");reason="multiple_devices";return false;}
 uintptr_t base=reinterpret_cast<uintptr_t>(GetModuleHandleW(nullptr));
 constexpr unsigned char expected[]={0xd9,0x87,0xb8,0,0,0,0xd8,0x60,0x30,0xd9,0xc0,0xd8,0xc9,0xd9,0xc2,0xd8,0xcb};unsigned char seen[sizeof(expected)]{};
 if(base!=0x400000||!IsProcessorFeaturePresent(PF_XMMI64_INSTRUCTIONS_AVAILABLE)||!safe_copy(seen,reinterpret_cast<void*>(base+UI_SORT_RVA-6),sizeof(seen))||std::memcmp(seen,expected,sizeof(seen))){reason="ui_sort_signature_or_placement_mismatch";return false;}
 HMODULE pin=nullptr;if(!GetModuleHandleExW(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS|GET_MODULE_HANDLE_EX_FLAG_PIN,reinterpret_cast<LPCWSTR>(&sort_bridge),&pin)){reason="module_pin_failed";return false;}
 sort_return=base+UI_SORT_RVA+5;thread_=GetCurrentThreadId();active=this;
 enabled_=patch_.install(memory,reinterpret_cast<void*>(base+UI_SORT_RVA),reinterpret_cast<uintptr_t>(&sort_bridge));
 reason=enabled_?"ui_packet_sort_installed":"ui_jump_patch_failed";if(!enabled_){active=nullptr;patch_.remove(memory);}return enabled_;
}
void UiMargins::dimensions(UINT w,UINT h) noexcept {MarginFP fp;half_=0;if(w&&h&&double(w)/h>=1.&&double(w)/h<=4.)half_=static_cast<float>((480.*double(w)/h-640.)*.5);}
void UiMargins::before_sort(uintptr_t entity,uintptr_t coordinates) noexcept {
 if(!enabled_||GetCurrentThreadId()!=thread_)return;
 // EAX == packet+0x24 in the proven packet branch; static fallback is excluded.
 if(!eligible_ui_packet(entity,coordinates))return;
 frame_.shift(reinterpret_cast<float*>(coordinates+0x30),half_);
}
bool UiMargins::finish_frame() noexcept {bool okay=frame_.restore();if(!okay)disable("ui_coordinate_restore_failed");return okay;}
void UiMargins::disable(const char* why) noexcept {enabled_=false;half_=0;frame_.restore();if(active==this)active=nullptr;patch_.remove(memory);reason=why;}
UiMargins::~UiMargins(){disable("device_release");}
std::string UiMargins::json() const {MarginFP fp;std::ostringstream o;o<<"{\"installed\":"<<(patch_.installed()?"true":"false")<<",\"enabled\":"<<(enabled_?"true":"false")<<",\"reason\":"<<quote(reason)<<",\"half_extra\":"<<half_<<",\"packet_shifts\":"<<frame_.changed<<",\"restore_failures\":"<<frame_.failures<<",\"overflow\":"<<frame_.overflow<<'}';return o.str();}
uintptr_t detail::ui_bridge_for_contract(uintptr_t address) noexcept {if(active)return 0;sort_return=address;return reinterpret_cast<uintptr_t>(&sort_bridge);}
}
