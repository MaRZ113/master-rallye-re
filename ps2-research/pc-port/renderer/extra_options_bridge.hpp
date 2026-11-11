#pragma once
#ifndef NOMINMAX
#define NOMINMAX
#endif
#ifndef WIN32_LEAN_AND_MEAN
#define WIN32_LEAN_AND_MEAN
#endif
#include <windows.h>
#include <tlhelp32.h>
#include <atomic>
#include <cstdint>
#include <cstring>
#include <cstdlib>

// Optional, query-only Extra Options ABI. Never LoadLibrary a gameplay proxy:
// dinput8 owns selection/persistence; absence keeps the renderer's own policy.
namespace mrextra {
inline constexpr unsigned kAbi = 0x45583201u;
struct API {
 using Abi = unsigned(WINAPI*)();
 using Query = unsigned(WINAPI*)(const char*, int, unsigned);
 using Texture = BOOL(WINAPI*)(const char*, unsigned, unsigned, unsigned, const void*, void*, unsigned, int, unsigned);
 Query visual=nullptr, revision=nullptr, visual_v2=nullptr;
 Texture texture=nullptr;
 bool complete() const noexcept { return visual && revision && texture; }
 unsigned variant(const char* family,int participant,unsigned phase) const noexcept {
  return complete() && family && visual_v2 ? visual_v2(family,participant,phase) : 0;
 }
 bool native(const char* family,int participant,unsigned phase) const noexcept {
  if(!complete() || !family)return false;
  const auto v=variant(family,participant,phase);
  return v ? v==1 : visual(family,participant,phase)==1;
 }
 unsigned generation(const char* family,int participant,unsigned phase) const noexcept {
  return complete() && family ? revision(family,participant,phase) : 0;
 }
 bool replace(const char* family,unsigned index,unsigned w,unsigned h,const void* src,void* dst,unsigned bytes,int participant,unsigned phase) const noexcept {
  return complete() && family && src && dst && texture(family,index,w,h,src,dst,bytes,participant,phase)!=FALSE;
 }
};
inline API from_module(HMODULE module) noexcept {
 if(!module)return {};
 const auto abi=reinterpret_cast<API::Abi>(GetProcAddress(module,"MRExtraOptionsAbi"));
 if(!abi || abi()!=kAbi)return {};
 API a;
 a.visual=reinterpret_cast<API::Query>(GetProcAddress(module,"MRExtraVisualV1"));
 a.visual_v2=reinterpret_cast<API::Query>(GetProcAddress(module,"MRExtraVisualV2"));
 a.revision=reinterpret_cast<API::Query>(GetProcAddress(module,"MRExtraRevisionV1"));
 a.texture=reinterpret_cast<API::Texture>(GetProcAddress(module,"MRExtraTextureV1"));
 return a.complete()?a:API{};
}
// Hold the selected provider for process lifetime before publishing callable
// pointers. A normal and a proxy dinput8 can coexist under the same basename.
inline API retain_module(HMODULE module) noexcept {
 HMODULE retained=nullptr;
 if(!module || !GetModuleHandleExW(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS,
      reinterpret_cast<LPCWSTR>(module),&retained))return {};
 const auto a=from_module(retained);
 if(!a.complete())FreeLibrary(retained);
 return a;
}
inline API discover() noexcept {
 auto module=GetModuleHandleW(L"dinput8.dll");
 auto result=retain_module(module);if(result.complete())return result;
 const auto snapshot=CreateToolhelp32Snapshot(TH32CS_SNAPMODULE,GetCurrentProcessId());
 if(snapshot==INVALID_HANDLE_VALUE)return {};
 MODULEENTRY32W entry{};entry.dwSize=sizeof(entry);
 if(Module32FirstW(snapshot,&entry))do{
  if(!_wcsicmp(entry.szModule,L"dinput8.dll")){
   result=retain_module(entry.hModule);if(result.complete())break;
  }
 }while(Module32NextW(snapshot,&entry));
 CloseHandle(snapshot);return result;
}
// Release/acquire publishes one immutable table, never a partially populated
// set of function pointers. Retry late input loading, at most every 250ms;
// standalone renderer draws must not enumerate modules on every draw.
class Cache {
 API value_{};
 std::atomic_bool ready_{false};
 std::atomic_flag probing_=ATOMIC_FLAG_INIT;
 std::atomic<uint64_t> retry_{0};
public:
 template<class Probe> API get(uint64_t now,Probe probe) noexcept {
  if(ready_.load(std::memory_order_acquire))return value_;
  if(now<retry_.load(std::memory_order_relaxed) || probing_.test_and_set(std::memory_order_acquire))return {};
  if(!ready_.load(std::memory_order_acquire) && now>=retry_.load(std::memory_order_relaxed)){
   const auto next=probe();
   if(next.complete()){value_=next;ready_.store(true,std::memory_order_release);}
   else retry_.store(now+250,std::memory_order_relaxed);
  }
  probing_.clear(std::memory_order_release);
  return ready_.load(std::memory_order_acquire)?value_:API{};
 }
};
inline API api() noexcept {static Cache cache;return cache.get(GetTickCount64(),discover);}
inline unsigned variant(const char* family,int participant,unsigned phase) noexcept {return api().variant(family,participant,phase);}
inline bool native(const char* family,int participant,unsigned phase) noexcept {return api().native(family,participant,phase);}

// VEHICLE-FIX2: per-draw gates ask for the same (family, participant, phase)
// thousands of times a frame. One answer per key is reused for 50 ms; a MODEL
// change in the menu is visible on the next refresh.
inline unsigned cached_variant(const char* family,int participant,unsigned phase) noexcept {
 struct Entry{char family[48]{};int participant=-2;unsigned phase=~0u,value=0;uint64_t tick=0;};
 static thread_local Entry entries[8];static thread_local unsigned next=0;
 if(!family)return 0;const uint64_t now=GetTickCount64();
 for(auto& e:entries)if(e.participant==participant&&e.phase==phase&&now-e.tick<50&&!strncmp(e.family,family,sizeof(e.family)-1))return e.value;
 auto& e=entries[next++%8];strncpy_s(e.family,family,_TRUNCATE);e.participant=participant;e.phase=phase;e.tick=now;
 const auto a=api();e.value=a.variant(family,participant,phase);
 if(!e.value&&a.complete()&&!a.visual_v2)e.value=a.visual(family,participant,phase)==1?1u:0u;   // V1-only provider: PC or nothing
 return e.value;
}
// ModelChoice=1 (PS2Port.ini [Vehicles], default): the PS2 vehicle pipeline is
// always loaded and the MODEL row decides per car (1 = PC, 2 = PS2). Without a
// selection (AI cars, no Extra Options dinput8) the owner's INI switches decide.
struct UserPolicy{std::atomic_bool race{true},all_cars{true},menu{true};};
inline UserPolicy& user_policy() noexcept {static UserPolicy p;return p;}
// human = a local driver's car in a race; phase 0 = the menu car.
inline bool ps2_allowed(const char* family,int participant,unsigned phase,bool human) noexcept {
 const auto v=cached_variant(family,participant,phase);if(v==1)return false;if(v==2||v==3)return true;
 auto& u=user_policy();return phase?u.race.load()&&(human||u.all_cars.load()):u.menu.load();
}

// A FrontendModel is reused across menu/race participants. Selection revision
// alone cannot identify a texture upload: phase and participant matter too.
struct UploadKey {
 unsigned generation=0,variant=0,phase=0;int participant=-1;
 bool operator==(const UploadKey& b)const noexcept{return generation==b.generation&&variant==b.variant&&phase==b.phase&&participant==b.participant;}
 bool operator!=(const UploadKey& b)const noexcept{return !(*this==b);}
};
inline UploadKey upload_key(const API& a,const char* family,int participant,unsigned phase) noexcept {
 const auto v=a.variant(family,participant,phase);
 // Only V2 kind3 can replace pixels in this ABI. PC/PS2 selection and absent
 // providers reuse the original texture upload, including shared AI models.
 if(v!=3)return {};
 return {a.generation(family,participant,phase),v,phase,participant};
}
}
