#pragma once
#include <windows.h>
#include <atomic>
#include <tlhelp32.h>
// Included by the existing graphics proxy only in the private Extra Options
// build. All state belongs to dinput8; absence preserves the original renderer.
namespace mrextra {
struct API {
 using Query=unsigned(WINAPI*)(const char*,int,unsigned);
 using Texture=BOOL(WINAPI*)(const char*,unsigned,unsigned,unsigned,const void*,void*,unsigned,int,unsigned);
 Query visual=nullptr,revision=nullptr,visual_v2=nullptr;Texture texture=nullptr;
 void resolve() noexcept {
  auto module=GetModuleHandleW(L"dinput8.dll");
  // The real system DLL and the proxy can both be loaded under this basename.
  // Select the one advertising our ABI, never assume module load order.
  if(!module||!GetProcAddress(module,"MRExtraOptionsAbi")){
   module=nullptr;const auto snapshot=CreateToolhelp32Snapshot(TH32CS_SNAPMODULE,GetCurrentProcessId());
   if(snapshot!=INVALID_HANDLE_VALUE){MODULEENTRY32W entry{};entry.dwSize=sizeof(entry);
    if(Module32FirstW(snapshot,&entry))do{if(!_wcsicmp(entry.szModule,L"dinput8.dll")&&GetProcAddress(entry.hModule,"MRExtraOptionsAbi")){module=entry.hModule;break;}}while(Module32NextW(snapshot,&entry));
    CloseHandle(snapshot);
   }
  }
  if(!module)return;
  const auto version=reinterpret_cast<unsigned(WINAPI*)()>(GetProcAddress(module,"MRExtraOptionsAbi"));
  if(!version||version()!=0x45583201u)return;
  visual=reinterpret_cast<Query>(GetProcAddress(module,"MRExtraVisualV1"));
  visual_v2=reinterpret_cast<Query>(GetProcAddress(module,"MRExtraVisualV2"));
  revision=reinterpret_cast<Query>(GetProcAddress(module,"MRExtraRevisionV1"));
  texture=reinterpret_cast<Texture>(GetProcAddress(module,"MRExtraTextureV1"));
 }
};
// D3D8 may be initialized before the game's input proxy. A failed early
// lookup is transient: only publish the table when all exports are present.
inline API api() noexcept {
 static std::atomic<API::Query> visual{nullptr},revision{nullptr},visual_v2{nullptr};
 static std::atomic<API::Texture> texture{nullptr};
 API value;value.visual=visual.load();value.revision=revision.load();value.visual_v2=visual_v2.load();value.texture=texture.load();
 if(!value.visual||!value.revision||!value.texture){
  API next;next.resolve();
  if(next.visual&&next.revision&&next.texture){visual.store(next.visual);revision.store(next.revision);visual_v2.store(next.visual_v2);texture.store(next.texture);value=next;}
 }
 return value;
}
inline unsigned variant(const char* family,int participant,unsigned phase) noexcept {const auto f=api().visual_v2;return f?f(family,participant,phase):0;}
// Preserve V1 diagnostics and fallback when an older input DLL has no V2.
inline bool native(const char* family,int participant,unsigned phase) noexcept {const auto a=api();const bool old=a.visual&&a.visual(family,participant,phase)==1;const auto v=a.visual_v2?a.visual_v2(family,participant,phase):0;return v?v==1:old;}
inline unsigned revision(const char* family,int participant,unsigned phase) noexcept {const auto f=api().revision;return f?f(family,participant,phase):0;}
inline bool texture(const char* family,unsigned index,unsigned w,unsigned h,const void* src,void* dst,unsigned bytes,int participant,unsigned phase) noexcept {const auto f=api().texture;return f&&f(family,index,w,h,src,dst,bytes,participant,phase);}
}
