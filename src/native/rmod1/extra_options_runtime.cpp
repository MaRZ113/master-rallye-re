#define WIN32_LEAN_AND_MEAN
#define NOMINMAX
#include <windows.h>
#include "extra_options_runtime.hpp"
#include "extra_options.hpp"
#include "extra_options_package.hpp"
#include <array>
#include <atomic>
#include <cstdio>
#include <cstring>
#include <cwchar>
#include <filesystem>
#include <fstream>
#include <string>
#include <vector>

namespace extra_runtime {
namespace {
namespace fs=std::filesystem;
#if defined(EXTRA_OPTIONS_TEST)
template<class T>T fn(uintptr_t va){return reinterpret_cast<T>(extra_test_resolve(va));}
#else
template<class T>T fn(uintptr_t va){return reinterpret_cast<T>(va);}
#endif
using Init=void(__thiscall*)(void*,void*);
using Tick=uintptr_t(__thiscall*)(void*,uint32_t);
using Command=int(__thiscall*)(void*,unsigned);
using Writer=void(__thiscall*)(void*,void*,void*);
constexpr uintptr_t kInitSlot=0x690b74,kTickSlot=0x690b70,kCommandCall=0x483e23;
constexpr uintptr_t kInit=0x4839d0,kTick=0x483d20,kCommand=0x45d930;
constexpr uintptr_t kFrontCall=0x493935,kRearCall=0x493942,kFront=0x496d20,kRear=0x498090;
std::array<std::atomic_uint,256> paints{},tires{};
std::atomic_int menu_car{-1},race_car{-1};
std::atomic_uint generation{1};
extra_options::Config options{};
bool installed=false,lists_ready=false;
fs::path directory;
int editing=-1;unsigned draft_paint=0,draft_tire=0;
struct Pixels {std::vector<unsigned char> original,derived;};
std::vector<Pixels> pixels;
void log(const char* text) noexcept {try {std::ofstream f(directory/"MRallyeExtraOptions.log",std::ios::app);f<<text<<'\n';}catch(...) {}}
bool read(uintptr_t p,void* data,size_t n) noexcept {SIZE_T done=0;return ReadProcessMemory(GetCurrentProcess(),reinterpret_cast<const void*>(p),data,n,&done)&&done==n;}
uint32_t key(const char* s){uint32_t result=0;fn<void(__thiscall*)(uint32_t*,const char*)>(0x4d0580)(&result,s);return result;}
void* broker(){return fn<void*(__cdecl*)()>(0x4d8ec0)();}
int integer(const char* s){auto k=key(s);return fn<int(__thiscall*)(void*,uint32_t*)>(0x4d6760)(broker(),&k);}
bool boolean(const char* s){auto k=key(s);return fn<bool(__thiscall*)(void*,uint32_t*)>(0x4d6520)(broker(),&k);}
void put_int(const char* s,int value){auto k=key(s);fn<void(__thiscall*)(void*,uint32_t*,int)>(0x4d8000)(broker(),&k,value);}
void put_name(const char* s,const char* value){auto k=key(s),v=key(value);fn<void(__thiscall*)(void*,uint32_t*,uint32_t*)>(0x4d85f0)(broker(),&k,&v);}
// UI Text* is a Name datum. 0x4d8720 is the String-path overload and
// re-interns both arguments; passing a Name ID there dereferences that ID.
std::string native_label(const char* value){std::string text(value);for(auto& c:text)if(c>='a'&&c<='z')c=char(c-'a'+'A');return text;}
void put_text(const char* s,const char* value){const auto text=native_label(value);put_name(s,text.c_str());}
const extra_package::Vehicle* vehicle(int id){for(const auto& v:extra_package::vehicles)if(v.id==id)return &v;return nullptr;}
unsigned paint_count(int id){auto* v=vehicle(id);return options.enabled&&options.liveries&&v?v->paint_count:1u;}
bool frontend_scope(){return boolean("Frontend/InQuickRaceMode")&&!boolean("Frontend/SplitScreen")&&integer("Frontend/CarSetup/PlayerID")==0;}
int selected_car(){if(!frontend_scope())return -1;return integer("Frontend/QuickRace/Car0");}
bool race_scope(){return integer("Race/Type")==2&&integer("Race/NumPlayers")==1&&integer("Race/Car0/PlayerType")==1&&!boolean("Race/AttractMode")&&!boolean("Race/PlaybackReplay");}

// Native string vector layout from the original Gearbox initializer. Allocate
// using the game's allocator; Broker owns the published list for this process.
void list(const char* path,const std::vector<const char*>& values){
 auto* v=static_cast<uint32_t*>(fn<void*(__cdecl*)(size_t)>(0x5c1cb4)(16));if(!v)throw 1;
 std::memset(v,0,16);
 for(const auto* text:values){const auto label=native_label(text);uint32_t s=0;fn<void(__thiscall*)(uint32_t*,const char*)>(0x4d11d0)(&s,label.c_str());
  fn<void(__thiscall*)(void*,uintptr_t,unsigned,uint32_t*)>(0x407b30)(v,v[2],1,&s);
  fn<void(__cdecl*)(uintptr_t)>(0x5b4c00)(s);
 }
 auto k=key(path);fn<void(__thiscall*)(void*,uint32_t*,void*)>(0x4d8880)(broker(),&k,v);
}
void refresh_labels(){
 auto* v=vehicle(editing);unsigned count=paint_count(editing);
 if(draft_paint>=count)draft_paint=0;
 if(draft_tire>5||!options.enabled||!options.tires)draft_tire=0;
 const auto* paint=(!options.enabled||!options.liveries)?"Disabled":v?v->paint_labels[draft_paint]:"Current appearance";
 static constexpr const char* tire_labels[]={"Stock","Tarmac","Hard Dirt","Gravel","Grass","Mud"};
 put_text("Frontend/ExtraOptions/PaintText",paint);
 put_text("Frontend/ExtraOptions/TireText",(!options.enabled||!options.tires)?"Stock (disabled)":tire_labels[draft_tire]);
 put_int("Frontend/ExtraOptions/PaintLeftArrow",draft_paint>0);
 put_int("Frontend/ExtraOptions/PaintRightArrow",draft_paint+1<count);
 put_int("Frontend/ExtraOptions/TireLeftArrow",draft_tire>0);
 put_int("Frontend/ExtraOptions/TireRightArrow",options.enabled&&options.tires&&draft_tire<5);
}
void publish_draft(){put_int("Frontend/ExtraOptions/Paint",int(draft_paint));put_int("Frontend/ExtraOptions/Tire",int(draft_tire));refresh_labels();}
void begin_edit(){
 editing=selected_car();menu_car=editing;race_car=editing;
 if(editing<0||editing>=256){editing=-1;draft_paint=draft_tire=0;}else{draft_paint=paints[editing];draft_tire=tires[editing];}
 // Replace lists only for a different menu visit, using native ownership.
 auto* v=vehicle(editing);std::vector<const char*> labels;
 if(options.enabled&&options.liveries&&v)for(unsigned i=0;i<v->paint_count;++i)labels.push_back(v->paint_labels[i]);
 else labels.push_back(options.enabled?"Current appearance":"Disabled");
 list("Frontend/ExtraOptions/PaintList",labels);
 std::vector<const char*> tire_labels={"Stock"};
 if(options.enabled&&options.tires)tire_labels={"Stock","Tarmac","Hard Dirt","Gravel","Grass","Mud"};
 list("Frontend/ExtraOptions/TireList",tire_labels);lists_ready=true;publish_draft();
}
void sync_draft(){
 if(!lists_ready)return;
 const int p=integer("Frontend/ExtraOptions/Paint"),t=integer("Frontend/ExtraOptions/Tire");
 draft_paint=p>=0&&unsigned(p)<paint_count(editing)?unsigned(p):0;
 draft_tire=t>=0&&t<=5&&options.enabled&&options.tires?unsigned(t):0;
 refresh_labels();
}
bool save(){
 if(editing<0||editing>=256||!frontend_scope())return false;
 const auto path=(directory/"MRallyeExtraOptions.state.ini").wstring();wchar_t section[32]{},number[16]{};
 std::swprintf(section,32,L"Car%d",editing);
 std::swprintf(number,16,L"%u",draft_paint);if(!WritePrivateProfileStringW(section,L"Paint",number,path.c_str()))return false;
 std::swprintf(number,16,L"%u",draft_tire);if(!WritePrivateProfileStringW(section,L"Tire",number,path.c_str()))return false;
 paints[editing]=draft_paint;tires[editing]=draft_tire;++generation;
 char message[160]{};std::snprintf(message,sizeof(message),"APPLY CarID=%d paint=%u tire=%u; next instance; AI unchanged",editing,draft_paint,draft_tire);log(message);return true;
}
void __fastcall setup_init(void* self,void*,void* argument){
 fn<Init>(kInit)(self,argument);try{begin_edit();}catch(...){log("MENU_INIT_FAILED");}
}
uintptr_t __fastcall setup_tick(void* self,void*,uint32_t argument){
 const auto result=fn<Tick>(kTick)(self,argument);
 try{if(editing!=selected_car())begin_edit();else sync_draft();}catch(...){log("MENU_UPDATE_FAILED");}
 return result;
}
#if defined(EXTRA_STARTUP_DIAGNOSTIC)
uintptr_t __fastcall title_tick(void* self,void*,uint32_t argument){
 const auto result=fn<Tick>(0x47fc80)(self,argument);
 static bool once=false;if(!once){once=true;char line[220]{};
 std::snprintf(line,sizeof(line),"TITLE_STATE videos=%d mode=%d editors=%d attract=%d menus=%d",boolean("Frontend/VideosHavePlayed"),integer("Frontend/TitleMode"),integer("Editing/EditorsOpen"),boolean("Race/AttractMode"),boolean("Menues/Enabled"));log(line);}
 return result;
}
#endif
int __fastcall setup_command(void* manager,void*,unsigned sound){
 const int command=fn<Command>(kCommand)(manager,sound);
 try{
  if(command>=5&&command<=9){sync_draft();
   if(command==7){if(save())return -3;log("APPLY_NOT_AVAILABLE: requires player 1 single-player Quick Race");}
   if(command==8){if(editing>=0&&editing<256){draft_paint=paints[editing];draft_tire=tires[editing];}publish_draft();log("CANCEL draft restored");return -3;}
   if(command==9){draft_paint=draft_tire=0;publish_draft();log("DEFAULTS draft only");}
   return -1; // original Gearbox handles only its unchanged IDs 1..4
  }
  if(command==-3){ // native Back cancels an unapplied Extra Options draft
   if(editing>=0&&editing<256){draft_paint=paints[editing];draft_tire=tires[editing];}publish_draft();
  }
 }catch(...){log("MENU_EVENT_FAILED");}
 return command;
}
bool player_prefix(void* prefix){uintptr_t p=0;char text[sizeof("Vehicles/Car0")]{};return prefix&&read(reinterpret_cast<uintptr_t>(prefix)+4,&p,4)&&p&&read(p,text,sizeof(text))&&!std::memcmp(text,"Vehicles/Car0",sizeof(text));}
void apply_tire(void* prefix,const char* axle){
 if(!player_prefix(prefix)||!race_scope())return;
 const int id=integer("Race/Car0/CarID");race_car=id;if(id<0||id>=256)return;
 if(!options.enabled||!options.tires)return;
 const unsigned choice=tires[id];if(!choice||choice>5)return;
 const auto* type=extra_options::kTireNames[choice];char path[128]{};
 std::snprintf(path,sizeof(path),"Vehicles/Car0/Suspension/%s/TyreType",axle);put_name(path,type);
 // A name chooses the already-loaded complete native five-record family.
 // No shared table or live solver structure is modified.
 char message[180]{};std::snprintf(message,sizeof(message),"TIRE_PUBLISHED CarID=%d axle=%s family=%s stage=before_vehicle_initialization",id,axle,type);log(message);
}
void __fastcall front(void* self,void*,void* prefix,void* data){fn<Writer>(kFront)(self,prefix,data);try{apply_tire(prefix,"Front");}catch(...){log("FRONT_TIRE_FAILED");}}
void __fastcall rear(void* self,void*,void* prefix,void* data){fn<Writer>(kRear)(self,prefix,data);try{apply_tire(prefix,"Rear");}catch(...){log("REAR_TIRE_FAILED");}}
bool patch(uintptr_t va,const void* p,size_t size){DWORD previous=0,ignored=0;if(!VirtualProtect(reinterpret_cast<void*>(va),size,PAGE_EXECUTE_READWRITE,&previous))return false;std::memcpy(reinterpret_cast<void*>(va),p,size);const bool ok=FlushInstructionCache(GetCurrentProcess(),reinterpret_cast<void*>(va),size)!=FALSE;return VirtualProtect(reinterpret_cast<void*>(va),size,previous,&ignored)&&ok;}
bool call_is(uintptr_t site,uintptr_t target){std::array<unsigned char,5> b{};if(!read(site,b.data(),b.size())||b[0]!=0xe8)return false;int32_t offset=0;std::memcpy(&offset,b.data()+1,4);return site+5+offset==target;}
std::vector<unsigned char> load(const char* name,size_t bytes){std::ifstream f(directory/name,std::ios::binary|std::ios::ate);if(!f||f.tellg()!=std::streamoff(bytes))return {};std::vector<unsigned char> p(bytes);f.seekg(0);f.read(reinterpret_cast<char*>(p.data()),std::streamsize(bytes));if(!f)return {};return p;}
}

bool initialize() noexcept {try{
 wchar_t exe[32768]{};if(!GetModuleFileNameW(nullptr,exe,32768))return false;directory=fs::path(exe).parent_path();
 std::ifstream f(directory/"MRallyeExtraOptions.ini",std::ios::binary);std::string ini((std::istreambuf_iterator<char>(f)),{});
 const auto parsed=extra_options::parse_config(ini);if(parsed.accepted)options=parsed.config;else log("CONFIG absent/invalid; customization disabled; existing Randomizer settings unchanged");
 const auto state=(directory/"MRallyeExtraOptions.state.ini").wstring();
 for(unsigned i=0;i<256;++i){wchar_t s[32]{};std::swprintf(s,32,L"Car%u",i);auto p=GetPrivateProfileIntW(s,L"Paint",0,state.c_str()),t=GetPrivateProfileIntW(s,L"Tire",0,state.c_str());paints[i]=p<paint_count(int(i))?p:0;tires[i]=t<=5?t:0;}
 pixels.resize(extra_package::binding_count);for(unsigned i=0;i<extra_package::binding_count;++i){const auto& b=extra_package::bindings[i];const size_t size=size_t(b.width)*b.height*4;pixels[i].original=load(b.original,size);pixels[i].derived=load(b.derived,size);}
 for(const auto& api:extra_package::apis){std::array<unsigned char,8> observed{};if(!read(api.va,observed.data(),observed.size())||observed!=api.bytes){log("API_LAYOUT_UNSUPPORTED: no Extra Options hooks installed");return false;}}
 uintptr_t init=0,tick=0;
 if(!read(kInitSlot,&init,4)||init!=kInit||!read(kTickSlot,&tick,4)||tick!=kTick||!call_is(kCommandCall,kCommand)||!call_is(kFrontCall,kFront)||!call_is(kRearCall,kRear)) {log("HOOK_CONFLICT: Extra Options not installed; selected call/vtable mismatch");return false;}
 struct Write{uintptr_t address;std::array<unsigned char,5> before,after;unsigned size;};std::array<Write,5> writes{};
 const uintptr_t sites[]={kInitSlot,kTickSlot,kCommandCall,kFrontCall,kRearCall};
 const uintptr_t targets[]={reinterpret_cast<uintptr_t>(&setup_init),reinterpret_cast<uintptr_t>(&setup_tick),reinterpret_cast<uintptr_t>(&setup_command),reinterpret_cast<uintptr_t>(&front),reinterpret_cast<uintptr_t>(&rear)};
 for(unsigned i=0;i<5;++i){auto& w=writes[i];w.address=sites[i];w.size=i<2?4:5;if(!read(w.address,w.before.data(),w.size))return false;if(i<2)std::memcpy(w.after.data(),&targets[i],4);else{w.after[0]=0xe8;const auto offset=int32_t(targets[i]-w.address-5);std::memcpy(w.after.data()+1,&offset,4);}}
 for(unsigned i=0;i<5;++i)if(!patch(writes[i].address,writes[i].after.data(),writes[i].size)){for(unsigned j=0;j<=i;++j)patch(writes[j].address,writes[j].before.data(),writes[j].size);log("HOOK_INSTALL_FAILED rolled back");return false;}
#if defined(EXTRA_STARTUP_DIAGNOSTIC)
 uintptr_t title=0;if(read(0x690abc,&title,4)&&title==0x47fc80){title=reinterpret_cast<uintptr_t>(&title_tick);patch(0x690abc,&title,4);}
#endif
 installed=true;log("READY EXTRA-SET1 native Gearbox Paint/Tires/Apply/Cancel/Defaults; G1 runtime retained");return true;
 }catch(...){log("INITIALIZATION_FAILED");return false;}}

} // namespace extra_runtime

// The renderer asks this module; it never owns or rewrites customization state.
extern "C" unsigned WINAPI MRExtraOptionsAbi(){return 0x45583201u;}
// V2 identifies the selected appearance independently of renderer lighting.
// 0=no applicable selection, 1=PC bundle, 2=PS2 bundle, 3=PS2 with PC textures.
extern "C" unsigned WINAPI MRExtraVisualV2(const char* family,int participant,unsigned phase){
 using namespace extra_runtime;
 if(!installed||!options.enabled||!options.liveries||!family||(phase!=0&&participant!=0))return 0;
 const int id=phase==0?menu_car.load():race_car.load();
 if(id<0||id>=256)return 0;
 const auto* v=vehicle(id);if(!v||_stricmp(family,v->family))return 0;
 const unsigned choice=paints[id];if(choice>=v->paint_count)return 0;
 return v->paint_kinds[choice];
}
extern "C" unsigned WINAPI MRExtraVisualV1(const char* family,int participant,unsigned phase){
 using namespace extra_runtime;
 if(!installed||!options.enabled||!options.liveries||!family||!extra_package::family_enabled(family))return 0;
 const int id=phase==0?menu_car.load():race_car.load();if(id<0||id>=256||(phase!=0&&participant!=0))return 0;
 const auto* v=vehicle(id);if(!v||_stricmp(family,v->family))return 0;
 const unsigned choice=paints[id];const unsigned native=choice==v->native_paint?1u:0u;
 static std::atomic<unsigned> last{~0u};const unsigned event=unsigned(id)|(phase<<8)|(choice<<16);
 if(last.exchange(event)!=event){char message[200]{};std::snprintf(message,sizeof(message),"VISUAL_REQUEST family=%s CarID=%d phase=%u paint=%u decision=%s",family,id,phase,choice,native?"pc-native":"ps2-derived");log(message);}
 return native; // 1: retain complete original native visual bundle
}
extern "C" unsigned WINAPI MRExtraRevisionV1(const char* family,int participant,unsigned phase){
 using namespace extra_runtime;if(!family||(phase&&participant!=0))return 0;return generation.load();
}
extern "C" BOOL WINAPI MRExtraTextureV1(const char* family,unsigned index,unsigned width,unsigned height,const void* original,void* output,unsigned bytes,int participant,unsigned phase){
 using namespace extra_runtime;
 if(!installed||!options.enabled||!options.liveries||!family||!original||!output||(phase&&participant!=0))return FALSE;
 const int id=phase==0?menu_car.load():race_car.load();auto* v=vehicle(id);if(!v||_stricmp(v->family,family)||paints[id]==v->native_paint||paints[id]!=1)return FALSE;
 for(unsigned i=0;i<extra_package::binding_count;++i){const auto& b=extra_package::bindings[i];if(index==b.index&&width==b.width&&height==b.height&&bytes==pixels[i].original.size()&&bytes==pixels[i].derived.size()&&!std::memcmp(original,pixels[i].original.data(),bytes)){std::memcpy(output,pixels[i].derived.data(),bytes);char message[180]{};std::snprintf(message,sizeof(message),"TEXTURE_ACCEPTED family=%s CarID=%d phase=%u index=%u size=%ux%u",family,id,phase,index,width,height);log(message);return TRUE;}}
 char message[180]{};std::snprintf(message,sizeof(message),"TEXTURE_REJECTED family=%s CarID=%d phase=%u index=%u size=%ux%u bytes=%u",family,id,phase,index,width,height,bytes);log(message);
 return FALSE;
}
