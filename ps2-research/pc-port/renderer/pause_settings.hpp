#pragma once
// PAUSE-MENU1 (docs/pause-menu1/RECON_RU.md): a SETTINGS submenu in the native race pause, first item CAMERA FOV.
//
// The pause is gaFrontendPauseMenuAI (retail MRallye.exe). It shows the Broker string list Race/PauseMenu/List, moves
// Race/PauseMenu/Index with up/down (wrapping by the current list length) and its accept 0x455210 hardwires index 1 =
// Controller/QuitRace, everything else = continue. Four CALL sites inside the AI are redirected (verified E8 rel32 and
// target, written once, kept for the process lifetime):
//   0x4551a7 Show(1) when the pause opens  -> the main list becomes  <CONTINUE> SETTINGS <QUIT>
//   0x4551d6 per-tick input                 -> keyboard Left/Right change the selected setting
//   0x455600 accept                         -> SETTINGS opens the submenu, QUIT keeps working (index 2 -> native 1)
//   0x45560c back                           -> leaves the submenu instead of closing the pause
//   0x531105 enUITileBox draw (Width +0x18 / Height +0x1c are read every frame) -> while the pause ticks, the frame
//            (the only enUITileBox of Hud0/Hud1, Width 18) gets 2*rows+1 tiles: 5 for the native 2 rows, 7 for 3.
// The chosen FOV is written to MRRRenderer.ini ([Quality] VerticalFOVDegrees; [Camera] for a v1 file) when SETTINGS is
// left or the pause closes, so it survives a restart (the renderer reads that file at start).
// Lists are built with the game's own allocator (0x5c1cb4) because Broker frees the previous list (strings, vector
// buffer, object; 0x4de1c0 type 9) with 0x5b4c00 when a new one is set; a pointer is never reused after it is handed over.
// The FOV is applied live through g_live_vfov (patch 0001, game_fov.cpp); it only acts with [Quality] GameplayFOV on.
#include "ps2_config.hpp"
#include "ps2_diag.hpp"
#include <windows.h>
#include <array>
#include <atomic>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <string>
#include <vector>

namespace gfx2 { extern std::atomic<float> g_live_vfov,g_configured_vfov; }

namespace gfx2::ps2port::pause {

// ---- Pure model (unit-tested) -------------------------------------------------------------------------------------
enum class Mode : uint8_t { Main, Settings };
enum class Action : uint8_t { Native, NativeQuit, Stay };
inline constexpr int kFovMin=50,kFovMax=100,kFovStep=5;

struct Menu {
    Mode mode=Mode::Main;
    std::vector<std::string> original;   // the game's own (localised) CONTINUE / QUIT
    float configured=0.f;                // [Quality] VerticalFOVDegrees when GameplayFOV is on, else 0
    float live=0.f;                      // 0 = configured
    bool usable() const noexcept { return original.size()==2; }
    int fov() const noexcept { const float v=live>0.f?live:configured; return int(std::lround(v)); }
    std::vector<std::string> labels() const {
        if(mode==Mode::Main) return {original[0],"SETTINGS",original[1]};
        char fov[32];
        if(configured>0.f) std::snprintf(fov,sizeof(fov),"CAMERA FOV %d",this->fov()); else std::snprintf(fov,sizeof(fov),"CAMERA FOV STOCK");
        return {fov,"BACK"};
    }
    // dir +1/-1; wrap=true for accept (cycles), false for Left/Right (stops at the ends). False = nothing changed.
    bool step(int dir,bool wrap) noexcept {
        if(configured<=0.f||!dir)return false;
        int v=fov();v=(v/kFovStep)*kFovStep+dir*kFovStep;
        if(v>kFovMax)v=wrap?kFovMin:kFovMax; if(v<kFovMin)v=wrap?kFovMax:kFovMin;
        if(v==fov())return false;
        live=float(v);return true;
    }
    Action accept(int index,int& next_index) noexcept {
        next_index=index;
        if(mode==Mode::Main){
            if(index==1){mode=Mode::Settings;next_index=0;return Action::Stay;}
            return index==2?Action::NativeQuit:Action::Native;
        }
        if(index==0){step(+1,true);return Action::Stay;}
        mode=Mode::Main;next_index=1;return Action::Stay;
    }
    // True = handled here (submenu -> main); false = native back (closes the pause).
    bool back(int& next_index) noexcept { if(mode!=Mode::Settings)return false; mode=Mode::Main;next_index=1;return true; }
};

// ---- Native glue ---------------------------------------------------------------------------------------------------
struct CallSite { const char* name; uint32_t site, target; };
inline constexpr CallSite kOpen{"pause_show_open",0x4551a7,0x455280};
inline constexpr CallSite kInput{"pause_input",0x4551d6,0x455570};
inline constexpr CallSite kAccept{"pause_accept",0x455600,0x455210};
inline constexpr CallSite kBack{"pause_back",0x45560c,0x455560};
inline constexpr CallSite kTile{"tilebox_draw",0x531105,0x531110};
inline constexpr uint32_t kTileWidth=0x18,kTileHeight=0x1c;
// Pure: frame height in tiles for n rows (native: 2 rows in 5 tiles).
inline constexpr int frame_tiles(size_t rows) noexcept { return int(rows)*2+1; }
// Pure: the INI section of the gameplay FOV in MRRRenderer.ini.
inline const wchar_t* fov_section(int config_version) noexcept { return config_version==2?L"Quality":L"Camera"; }
inline constexpr uint32_t kImageBase=0x400000;
inline constexpr uint32_t kGameNew=0x5c1cb4,kBrokerGet=0x4d8ec0,kSetList=0x4d8880,kSetInt=0x4d8000,kGetInt=0x4d6760,
    kGetList=0x4d6ea0,kUpdateText=0x4557b0;
inline constexpr uint32_t kListHandle=0x28,kIndexHandle=0x2c;   // gaFrontendPauseMenuAI fields (Broker key ids)

// Pure: the 5 bytes of a CALL rel32 from site to target.
inline std::array<uint8_t,5> call_bytes(uint32_t site,uint32_t target) noexcept {
    const uint32_t rel=target-(site+5);std::array<uint8_t,5> b{0xe8};std::memcpy(b.data()+1,&rel,4);return b;
}

struct State {
    Menu menu; bool configured=false,installed=false; const char* reason="not_requested"; bool left=false,right=false;
    std::wstring renderer_ini; bool dirty=false; int saved=0; ULONGLONG last_input=0; int frame=0;
};
inline State& state() noexcept { static State s; return s; }

namespace native {
using GameNew=void*(__cdecl*)(size_t);
using BrokerGet=void*(__cdecl*)();
using SetList=void(__thiscall*)(void*,uint32_t*,void*);
using SetInt=void(__thiscall*)(void*,uint32_t*,int);
using GetInt=int(__thiscall*)(void*,uint32_t*);
using GetList=void*(__thiscall*)(void*,uint32_t*);
using AiVoid=void(__thiscall*)(void*);
using AiInt=void(__thiscall*)(void*,int);
template<class F> inline F fn(uint32_t va) noexcept { return reinterpret_cast<F>(static_cast<uintptr_t>(va)); }
inline uint32_t* handle(void* ai,uint32_t offset) noexcept { return reinterpret_cast<uint32_t*>(static_cast<uint8_t*>(ai)+offset); }
inline void* broker() noexcept { return fn<BrokerGet>(kBrokerGet)(); }
inline int index(void* ai) noexcept { return fn<GetInt>(kGetInt)(broker(),handle(ai,kIndexHandle)); }

// The current list's strings, or false when it is missing / malformed.
inline bool read_list(void* ai,std::vector<std::string>& out) noexcept {
    try{
        out.clear();auto* list=static_cast<uint8_t*>(fn<GetList>(kGetList)(broker(),handle(ai,kListHandle)));if(!list)return false;
        char** begin=nullptr;char** end=nullptr;std::memcpy(&begin,list+4,4);std::memcpy(&end,list+8,4);
        if(!begin||end<begin||end-begin>32)return false;
        for(auto** p=begin;p!=end;++p){if(!*p)return false;out.emplace_back(*p);}
        return true;
    }catch(...){return false;}
}
// A Broker string list (type 9) built with the game's allocator; ownership passes to Broker.
inline void* make_list(const std::vector<std::string>& labels) noexcept {
    auto game_new=fn<GameNew>(kGameNew);
    auto* list=static_cast<uint8_t*>(game_new(0x10));if(!list)return nullptr;std::memset(list,0,0x10);
    const size_t n=labels.size();auto** buffer=static_cast<char**>(game_new(n*4));if(!buffer)return nullptr;
    for(size_t i=0;i<n;++i){auto* s=static_cast<char*>(game_new(labels[i].size()+1));if(!s)return nullptr;std::memcpy(s,labels[i].c_str(),labels[i].size()+1);buffer[i]=s;}
    char** end=buffer+n;std::memcpy(list+4,&buffer,4);std::memcpy(list+8,&end,4);std::memcpy(list+0xc,&end,4);
    return list;
}
inline bool show(void* ai,const Menu& menu,int idx) noexcept {
    try{
        void* list=make_list(menu.labels());if(!list)return false;
        fn<SetList>(kSetList)(broker(),handle(ai,kListHandle),list);
        fn<SetInt>(kSetInt)(broker(),handle(ai,kIndexHandle),idx);
        fn<AiVoid>(kUpdateText)(ai);   // CurrentText = List[Index]
        return true;
    }catch(...){return false;}
}
inline void publish_fov(State& s) noexcept { g_live_vfov.store(s.menu.live,std::memory_order_relaxed);if(s.menu.live>0.f)s.dirty=true; }
// Writes the chosen FOV into MRRRenderer.ini (only the one key; comments and the rest stay).
inline void save(State& s) noexcept {
    try{
        if(!s.dirty||s.renderer_ini.empty()||s.menu.configured<=0.f)return;s.dirty=false;
        const int v=s.menu.fov();if(v==s.saved)return;
        const int version=int(GetPrivateProfileIntW(L"General",L"ConfigVersion",0,s.renderer_ini.c_str()));
        const std::wstring value=std::to_wstring(v);
        if(WritePrivateProfileStringW(fov_section(version),L"VerticalFOVDegrees",value.c_str(),s.renderer_ini.c_str()))s.saved=v;
        else ps2diag::disable_log().note("pause_settings","renderer_ini_write_failed");
    }catch(...){}
}
inline bool key_edge(int vk,bool& was) noexcept {
    const bool down=(GetAsyncKeyState(vk)&0x8000)!=0;const bool edge=down&&!was;was=down;return edge;
}
inline bool game_has_focus() noexcept {
    DWORD pid=0;const HWND w=GetForegroundWindow();if(!w)return false;GetWindowThreadProcessId(w,&pid);return pid==GetCurrentProcessId();
}

inline void __fastcall on_open(void* ai,void*,int visible) {
    auto& s=state();
    if(visible){
        std::vector<std::string> now;
        // The AI init writes its own 2-entry list; our 3-entry main list stays between pauses.
        if(read_list(ai,now)&&now.size()==2)s.menu.original=now;
        s.menu.mode=Mode::Main;s.menu.configured=g_configured_vfov.load(std::memory_order_relaxed);
        if(s.menu.usable())show(ai,s.menu,0);
    }
    fn<AiInt>(kOpen.target)(ai,visible);
}
inline void __fastcall on_input(void* ai,void*,int arg) {
    auto& s=state();
    const bool focus=game_has_focus();
    const bool l=focus&&key_edge(VK_LEFT,s.left),r=focus&&key_edge(VK_RIGHT,s.right);
    if(s.menu.usable()&&s.menu.mode==Mode::Settings&&(l||r)&&index(ai)==0&&s.menu.step(r?+1:-1,false)){publish_fov(s);show(ai,s.menu,0);}
    s.last_input=GetTickCount64();s.frame=s.menu.usable()?frame_tiles(s.menu.labels().size()):0;
    fn<AiInt>(kInput.target)(ai,arg);
}
inline void __fastcall on_accept(void* ai,void*) {
    auto& s=state();
    if(!s.menu.usable()){fn<AiVoid>(kAccept.target)(ai);return;}
    int next=0;const auto action=s.menu.accept(index(ai),next);
    if(action==Action::Stay){publish_fov(s);if(s.menu.mode==Mode::Main)save(s);show(ai,s.menu,next);return;}
    save(s);s.frame=0;
    if(action==Action::NativeQuit)fn<SetInt>(kSetInt)(broker(),handle(ai,kIndexHandle),1);   // native: 1 = QuitRace
    else fn<SetInt>(kSetInt)(broker(),handle(ai,kIndexHandle),0);
    fn<AiVoid>(kAccept.target)(ai);
}
inline void __fastcall on_back(void* ai,void*) {
    auto& s=state();int next=0;
    if(s.menu.usable()&&s.menu.back(next)){save(s);show(ai,s.menu,next);return;}
    save(s);s.frame=0;
    fn<AiVoid>(kBack.target)(ai);
}

// enUITileBox draw (thiscall, 1 argument). Only while the pause input ticked within the last 250 ms.
inline void __fastcall on_tile(void* box,void*,int arg) {
    auto& s=state();
    if(s.frame>0&&GetTickCount64()-s.last_input<250){
        auto* width=reinterpret_cast<int*>(static_cast<uint8_t*>(box)+kTileWidth);auto* height=reinterpret_cast<int*>(static_cast<uint8_t*>(box)+kTileHeight);
        if(*width==18&&*height!=s.frame&&*height>=3&&*height<=15)*height=s.frame;
    }
    fn<AiInt>(kTile.target)(box,arg);
}
inline bool read(uint32_t va,uint8_t* out,size_t n) noexcept {
    __try{std::memcpy(out,reinterpret_cast<const void*>(static_cast<uintptr_t>(va)),n);return true;}
    __except(EXCEPTION_EXECUTE_HANDLER){return false;}
}
inline bool write(uint32_t va,const std::array<uint8_t,5>& bytes) noexcept {
    auto* target=reinterpret_cast<uint8_t*>(static_cast<uintptr_t>(va));DWORD old=0;
    if(!VirtualProtect(target,5,PAGE_EXECUTE_READWRITE,&old))return false;
    bool ok=true;__try{std::memcpy(target,bytes.data(),5);}__except(EXCEPTION_EXECUTE_HANDLER){ok=false;}
    DWORD ignored=0;VirtualProtect(target,5,old,&ignored);FlushInstructionCache(GetCurrentProcess(),target,5);return ok;
}
}  // namespace native

// Once per process, from the PS2PortExtension constructor (before any race, so the AI is not running).
inline void configure(bool supported,const std::wstring& ini) noexcept {
    auto& s=state();if(s.configured)return;s.configured=true;
    try{
        if(!supported||config::read_int(L"PauseSettings",0,ini.c_str())!=1)return;
        if(reinterpret_cast<uintptr_t>(GetModuleHandleW(nullptr))!=kImageBase){s.reason="unexpected_image_base";ps2diag::disable_log().note("pause_settings",s.reason);return;}
        { auto dir=ini;const auto slash=dir.find_last_of(L"/\\");dir=slash==std::wstring::npos?std::wstring():dir.substr(0,slash+1);
          const auto path=dir+L"MRRRenderer.ini";if(GetFileAttributesW(path.c_str())!=INVALID_FILE_ATTRIBUTES)s.renderer_ini=path; }
        const std::array<std::pair<CallSite,uint32_t>,5> sites{{
            {kOpen,uint32_t(reinterpret_cast<uintptr_t>(&native::on_open))},{kInput,uint32_t(reinterpret_cast<uintptr_t>(&native::on_input))},
            {kAccept,uint32_t(reinterpret_cast<uintptr_t>(&native::on_accept))},{kBack,uint32_t(reinterpret_cast<uintptr_t>(&native::on_back))},
            {kTile,uint32_t(reinterpret_cast<uintptr_t>(&native::on_tile))}}};
        for(const auto& [site,hook]:sites){std::array<uint8_t,5> seen{};
            if(!native::read(site.site,seen.data(),5)||seen!=call_bytes(site.site,site.target)){s.reason="original_call_mismatch_untouched";ps2diag::disable_log().note("pause_settings",s.reason);return;}}
        for(const auto& [site,hook]:sites)if(!native::write(site.site,call_bytes(site.site,hook))){s.reason="code_write_failed";ps2diag::disable_log().note("pause_settings",s.reason);return;}
        s.installed=true;s.reason="installed";
    }catch(...){}
}

}  // namespace gfx2::ps2port::pause
