#pragma once
// PAUSE-MENU1 (docs/pause-menu1/RECON_RU.md): a SETTINGS submenu in the native race pause.
//
// The pause is gaFrontendPauseMenuAI (retail MRallye.exe). It shows the Broker string list Race/PauseMenu/List, moves
// Race/PauseMenu/Index with up/down (wrapping by the current list length), scrolls a window of +0x14 (XML Height, 3)
// visible rows and its accept 0x455210 hardwires index 1 = Controller/QuitRace, everything else = continue.
// Five CALL sites are redirected (verified E8 rel32 and target, written once, kept for the process lifetime):
//   0x4551a7 Show(1) when the pause opens  -> the main list becomes  <CONTINUE> SETTINGS <QUIT>
//   0x4551d6 per-tick input                 -> keyboard Left/Right change the selected setting
//   0x455600 accept                         -> SETTINGS opens the submenu, QUIT keeps working (index 2 -> native 1)
//   0x45560c back                           -> leaves the submenu instead of closing the pause
//   0x531105 enUITileBox draw (Width +0x18 / Height +0x1c are read every frame; the egg's en2d matrix row 3 is the
//            bottom-left corner, y up) -> while the pause ticks, the pause frame (the only enUITileBox of Hud0/Hud1,
//            authored Width 18 / Height 5) gets 2*visible_rows+1 tiles, 22 tiles wide in SETTINGS, and its corner moves
//            down / left by the added tiles so the top edge and the centre stay where they were.
// SETTINGS: CAMERA FOV (live through g_live_vfov, patch 0001; only with [Quality] GameplayFOV on) and on/off switches of
// draw-time PS2 effects (live_settings.hpp; the same skip points as the F7 bypass). An effect that was off in PS2Port.ini
// at start is not loaded; its switch only edits the INI and is marked "*" (after a restart).
// Saving: on leaving SETTINGS or closing the pause, MRRRenderer.ini [Quality] VerticalFOVDegrees ([Camera] for v1) and the
// changed PS2Port.ini v3 keys ([Course] / [Picture]) are written with WritePrivateProfileString (one key each, comments stay).
// Lists are built with the game's own allocator (0x5c1cb4) because Broker frees the previous list (strings, vector
// buffer, object; 0x4de1c0 type 9) with 0x5b4c00 when a new one is set; a pointer is never reused after it is handed over.
#include "ps2_config.hpp"
#include "ps2_diag.hpp"
#include "live_settings.hpp"
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

// One on/off switch of a PS2Port.ini effect. keys[0] decides the state; every key is written on save.
struct Toggle {
    const char* label; unsigned bit; const wchar_t* section; std::array<const wchar_t*,2> keys;
    std::array<int,2> on_value{1,1};     // the value written for ON (keeps GroundDetail 2 / ForestFix 2)
    bool loaded=false;                   // >0 in PS2Port.ini at start (assets/state exist)
    bool on=false,dirty=false;
};
inline std::vector<Toggle> default_toggles() {
    return {
        {"GRASS",live::Grass,L"Course",{L"Grass",L"Shrubs"}},
        {"GROUND DETAIL",live::Ground,L"Course",{L"GroundDetail",nullptr}},
        {"FOREST FIX",live::Forest,L"Course",{L"ForestFix",nullptr}},
        {"WATER",live::Water,L"Course",{L"Water",nullptr}},
        {"BIRDS",live::Birds,L"Course",{L"Birds",nullptr}},
        {"MOTION BLUR",live::Blur,L"Picture",{L"MotionBlur",nullptr}},
        {"COLOUR",live::Color,L"Picture",{L"Color",nullptr}},
        {"TV OUTPUT",live::Output,L"Picture",{L"Output",nullptr}},
    };
}

struct Menu {
    Mode mode=Mode::Main;
    std::vector<std::string> original;   // the game's own (localised) CONTINUE / QUIT
    std::vector<Toggle> toggles;
    float configured=0.f;                // [Quality] VerticalFOVDegrees when GameplayFOV is on, else 0
    float live=0.f;                      // 0 = configured
    bool usable() const noexcept { return original.size()==2; }
    int fov() const noexcept { const float v=live>0.f?live:configured; return int(std::lround(v)); }
    size_t back_index() const noexcept { return toggles.size()+1; }
    std::vector<std::string> labels() const {
        if(mode==Mode::Main) return {original[0],"SETTINGS",original[1]};
        std::vector<std::string> out;char text[48];
        if(configured>0.f) std::snprintf(text,sizeof(text),"CAMERA FOV %d",fov()); else std::snprintf(text,sizeof(text),"CAMERA FOV STOCK");
        out.emplace_back(text);
        for(const auto& t:toggles){std::snprintf(text,sizeof(text),"%s %s%s",t.label,t.on?"ON":"OFF",t.loaded?"":" *");out.emplace_back(text);}
        out.emplace_back("BACK");
        return out;
    }
    // dir +1/-1; wrap=true for accept (cycles), false for Left/Right (stops at the ends). False = nothing changed.
    bool step(int dir,bool wrap) noexcept {
        if(configured<=0.f||!dir)return false;
        int v=fov();v=(v/kFovStep)*kFovStep+dir*kFovStep;
        if(v>kFovMax)v=wrap?kFovMin:kFovMax; if(v<kFovMin)v=wrap?kFovMax:kFovMin;
        if(v==fov())return false;
        live=float(v);return true;
    }
    // Settings row i: 0 = FOV, 1..n = toggles, n+1 = BACK. dir: 0 = flip (accept), -1 = OFF, +1 = ON.
    bool change(size_t row,int dir,bool wrap) noexcept {
        if(row==0)return step(dir?dir:+1,wrap);
        if(row-1>=toggles.size())return false;
        auto& t=toggles[row-1];const bool next=dir==0?!t.on:dir>0;
        if(next==t.on)return false;
        t.on=next;t.dirty=true;return true;
    }
    Action accept(int index,int& next_index) noexcept {
        next_index=index;
        if(mode==Mode::Main){
            if(index==1){mode=Mode::Settings;next_index=0;return Action::Stay;}
            return index==2?Action::NativeQuit:Action::Native;
        }
        if(index>=0&&size_t(index)<back_index()){change(size_t(index),0,true);return Action::Stay;}
        mode=Mode::Main;next_index=1;return Action::Stay;
    }
    // True = handled here (submenu -> main); false = native back (closes the pause).
    bool back(int& next_index) noexcept { if(mode!=Mode::Settings)return false; mode=Mode::Main;next_index=1;return true; }
    unsigned live_off_bits() const noexcept { unsigned b=0; for(const auto& t:toggles)if(t.loaded&&!t.on)b|=t.bit; return b; }
};

// ---- Frame geometry (pure) ------------------------------------------------------------------------------------------
inline constexpr int kAuthoredWidth=18,kAuthoredHeight=5,kSettingsWidth=22,kTileUnits=16;
// Frame height in tiles for n rows shown (native: 2 rows in 5 tiles).
inline constexpr int frame_tiles(size_t rows) noexcept { return int(rows)*2+1; }
inline constexpr size_t shown_rows(size_t rows,int visible) noexcept { return visible>0&&rows>size_t(visible)?size_t(visible):rows; }
// Corner of the frame for a size, from the authored corner: the top edge and the horizontal centre stay.
inline constexpr float frame_x(float authored_x,int width) noexcept { return authored_x-float((width-kAuthoredWidth)*kTileUnits)/2.f; }
inline constexpr float frame_y(float authored_y,int height) noexcept { return authored_y-float((height-kAuthoredHeight)*kTileUnits); }
// The INI section of the gameplay FOV in MRRRenderer.ini.
inline const wchar_t* fov_section(int config_version) noexcept { return config_version==2?L"Quality":L"Camera"; }

// ---- Native glue ---------------------------------------------------------------------------------------------------
struct CallSite { const char* name; uint32_t site, target; };
inline constexpr CallSite kOpen{"pause_show_open",0x4551a7,0x455280};
inline constexpr CallSite kInput{"pause_input",0x4551d6,0x455570};
inline constexpr CallSite kAccept{"pause_accept",0x455600,0x455210};
inline constexpr CallSite kBack{"pause_back",0x45560c,0x455560};
inline constexpr CallSite kTile{"tilebox_draw",0x531105,0x531110};
inline constexpr uint32_t kTileWidth=0x18,kTileHeight=0x1c,kEggEn2d=0x4c;
inline constexpr uint32_t kImageBase=0x400000;
inline constexpr uint32_t kGameNew=0x5c1cb4,kBrokerGet=0x4d8ec0,kSetList=0x4d8880,kSetInt=0x4d8000,kGetInt=0x4d6760,
    kGetList=0x4d6ea0,kUpdateText=0x4557b0;
inline constexpr uint32_t kListHandle=0x28,kIndexHandle=0x2c,kVisibleRows=0x14;   // gaFrontendPauseMenuAI fields

// Pure: the 5 bytes of a CALL rel32 from site to target.
inline std::array<uint8_t,5> call_bytes(uint32_t site,uint32_t target) noexcept {
    const uint32_t rel=target-(site+5);std::array<uint8_t,5> b{0xe8};std::memcpy(b.data()+1,&rel,4);return b;
}

struct FrameCorner { void* box=nullptr; float* corner=nullptr; float x=0,y=0; bool searched=false; };
struct State {
    Menu menu; bool configured=false,installed=false; const char* reason="not_requested"; bool left=false,right=false;
    std::wstring renderer_ini,port_ini; bool fov_dirty=false; int fov_saved=0;
    ULONGLONG last_input=0; int frame_height=0,frame_width=0; FrameCorner corner;
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

inline bool read(const void* address,void* out,size_t n) noexcept {
    __try{std::memcpy(out,address,n);return true;}
    __except(EXCEPTION_EXECUTE_HANDLER){return false;}
}
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
inline void apply_live(State& s) noexcept {
    g_live_vfov.store(s.menu.live,std::memory_order_relaxed);if(s.menu.live>0.f)s.fov_dirty=true;
    live::off_bits().store(s.menu.live_off_bits(),std::memory_order_relaxed);
}
// Writes the changed settings (one key each; comments and the rest of each file stay).
inline void save(State& s) noexcept {
    try{
        if(s.fov_dirty&&!s.renderer_ini.empty()&&s.menu.configured>0.f){
            s.fov_dirty=false;const int v=s.menu.fov();
            if(v!=s.fov_saved){
                const int version=int(GetPrivateProfileIntW(L"General",L"ConfigVersion",0,s.renderer_ini.c_str()));
                if(WritePrivateProfileStringW(fov_section(version),L"VerticalFOVDegrees",std::to_wstring(v).c_str(),s.renderer_ini.c_str()))s.fov_saved=v;
                else ps2diag::disable_log().note("pause_settings","renderer_ini_write_failed");
            }
        }
        if(s.port_ini.empty())return;
        for(auto& t:s.menu.toggles){
            if(!t.dirty)continue;t.dirty=false;
            for(size_t k=0;k<t.keys.size();++k){if(!t.keys[k])continue;
                const std::wstring value=std::to_wstring(t.on?t.on_value[k]:0);
                if(!WritePrivateProfileStringW(t.section,t.keys[k],value.c_str(),s.port_ini.c_str()))ps2diag::disable_log().note("pause_settings","ps2port_ini_write_failed");}
        }
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
    if(s.menu.usable()&&s.menu.mode==Mode::Settings&&(l||r)){
        const int row=index(ai);
        if(row>=0&&s.menu.change(size_t(row),r?+1:-1,false)){apply_live(s);show(ai,s.menu,row);}
    }
    int visible=3;native::read(static_cast<uint8_t*>(ai)+kVisibleRows,&visible,4);
    s.last_input=GetTickCount64();
    s.frame_height=s.menu.usable()?frame_tiles(shown_rows(s.menu.labels().size(),visible)):0;
    s.frame_width=s.menu.usable()&&s.menu.mode==Mode::Settings?kSettingsWidth:kAuthoredWidth;
    fn<AiInt>(kInput.target)(ai,arg);
}
inline void __fastcall on_accept(void* ai,void*) {
    auto& s=state();
    if(!s.menu.usable()){fn<AiVoid>(kAccept.target)(ai);return;}
    int next=0;const auto action=s.menu.accept(index(ai),next);
    if(action==Action::Stay){apply_live(s);if(s.menu.mode==Mode::Main)save(s);show(ai,s.menu,next);return;}
    save(s);s.frame_height=0;
    fn<SetInt>(kSetInt)(broker(),handle(ai,kIndexHandle),action==Action::NativeQuit?1:0);   // native: 1 = QuitRace
    fn<AiVoid>(kAccept.target)(ai);
}
inline void __fastcall on_back(void* ai,void*) {
    auto& s=state();int next=0;
    if(s.menu.usable()&&s.menu.back(next)){save(s);show(ai,s.menu,next);return;}
    save(s);s.frame_height=0;
    fn<AiVoid>(kBack.target)(ai);
}

// The egg's en2d matrix row 3 (authored 170 / 290 / 0 / 1): searched once per frame object in the en2d object and the egg.
inline float* find_corner(void* egg) noexcept {
    const float want[4]={170.f,290.f,0.f,1.f};
    void* en2d=nullptr;if(!read(static_cast<uint8_t*>(egg)+kEggEn2d,&en2d,4))en2d=nullptr;
    for(void* base:{en2d,egg}){
        if(!base)continue;uint8_t bytes[0x400];if(!read(base,bytes,sizeof(bytes)))continue;
        float* found=nullptr;unsigned hits=0;
        for(size_t o=0;o+16<=sizeof(bytes);o+=4)if(!std::memcmp(bytes+o,want,16)){++hits;found=reinterpret_cast<float*>(static_cast<uint8_t*>(base)+o);}
        if(hits==1)return found;
    }
    return nullptr;
}
// enUITileBox draw (thiscall, 1 argument = the egg). Only while the pause input ticked within the last 250 ms.
inline void __fastcall on_tile(void* box,void*,int egg) {
    auto& s=state();
    int width=0,height=0;
    const bool active=s.frame_height>0&&GetTickCount64()-s.last_input<250;
    // While the pause ticks the drawn enUITileBox is the pause frame (the only one in Hud0/Hud1); afterwards only that
    // remembered frame is put back. Frontend frames are never touched.
    if((active||box==s.corner.box)&&read(static_cast<uint8_t*>(box)+kTileWidth,&width,4)&&read(static_cast<uint8_t*>(box)+kTileHeight,&height,4)&&
       (width==kAuthoredWidth||width==kSettingsWidth)&&height>=3&&height<=15){
        if(s.corner.box!=box){s.corner={};s.corner.box=box;}
        const int want_h=active?s.frame_height:kAuthoredHeight,want_w=active?s.frame_width:kAuthoredWidth;
        auto* w=reinterpret_cast<int*>(static_cast<uint8_t*>(box)+kTileWidth);auto* h=reinterpret_cast<int*>(static_cast<uint8_t*>(box)+kTileHeight);
        if(!s.corner.searched&&egg){s.corner.searched=true;s.corner.corner=find_corner(reinterpret_cast<void*>(static_cast<uintptr_t>(egg)));
            if(s.corner.corner){s.corner.x=s.corner.corner[0];s.corner.y=s.corner.corner[1];}else ps2diag::disable_log().note("pause_settings","frame_corner_not_found");}
        // Without the corner the frame keeps its authored size (it would otherwise grow upward).
        if(s.corner.corner){*w=want_w;*h=want_h;s.corner.corner[0]=frame_x(s.corner.x,want_w);s.corner.corner[1]=frame_y(s.corner.y,want_h);}
    }
    fn<AiInt>(kTile.target)(box,egg);
}
inline bool read_code(uint32_t va,uint8_t* out,size_t n) noexcept { return read(reinterpret_cast<const void*>(static_cast<uintptr_t>(va)),out,n); }
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
        // PS2Port.ini switches are written back only into a v3 file (section/key names of the v3 template).
        if(GetPrivateProfileIntW(L"General",L"ConfigVersion",0,ini.c_str())==3)s.port_ini=ini;
        s.menu.toggles=default_toggles();
        for(auto& t:s.menu.toggles){
            for(size_t k=0;k<t.keys.size();++k)if(t.keys[k]){const int v=int(config::read_int(t.keys[k],0,ini.c_str()));
                if(k==0){t.loaded=v>0;if(v>0)t.on_value[0]=v;}else t.on_value[k]=v;}   // secondary keys keep their value
            t.on=t.loaded;
        }
        const std::array<std::pair<CallSite,uint32_t>,5> sites{{
            {kOpen,uint32_t(reinterpret_cast<uintptr_t>(&native::on_open))},{kInput,uint32_t(reinterpret_cast<uintptr_t>(&native::on_input))},
            {kAccept,uint32_t(reinterpret_cast<uintptr_t>(&native::on_accept))},{kBack,uint32_t(reinterpret_cast<uintptr_t>(&native::on_back))},
            {kTile,uint32_t(reinterpret_cast<uintptr_t>(&native::on_tile))}}};
        for(const auto& [site,hook]:sites){std::array<uint8_t,5> seen{};
            if(!native::read_code(site.site,seen.data(),5)||seen!=call_bytes(site.site,site.target)){s.reason="original_call_mismatch_untouched";ps2diag::disable_log().note("pause_settings",s.reason);return;}}
        for(const auto& [site,hook]:sites)if(!native::write(site.site,call_bytes(site.site,hook))){s.reason="code_write_failed";ps2diag::disable_log().note("pause_settings",s.reason);return;}
        s.installed=true;s.reason="installed";
    }catch(...){}
}

}  // namespace gfx2::ps2port::pause
