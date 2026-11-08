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

// EXTRA-SET2: TYRE TYPE row on the native Vehicle Setup GENERAL page (any mode with a setup
// screen, every human player and physical CarID) and a PS2/PC appearance row on Vehicle Select
// with immediate preview. The GEARBOX page is no longer touched.
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
using Wheel=void(__thiscall*)(void*);
// GENERAL page (VehicleSetup3) and Vehicle Select screen vtable slots, GENERAL command call, wheel update call.
constexpr uintptr_t kGeneralInitSlot=0x690b50,kGeneralTickSlot=0x690b4c,kGeneralInit=0x482f30,kGeneralTick=0x4830c0;
constexpr uintptr_t kSelectInitSlot=0x690b1c,kSelectTickSlot=0x690b18,kSelectInit=0x480b60,kSelectTick=0x481340;
constexpr uintptr_t kGeneralCommandCall=0x483151,kCommand=0x45d930,kWheelCall=0x44385b,kWheel=0x440fe0;
// Vehicle Select Left/Right: focus 1 changes class, any other focus scrolls the car carousel (0x481f50).
constexpr uintptr_t kSelectScrollCall=0x4818c5,kSelectScroll=0x481f50;
constexpr int kModelButton=3;
constexpr unsigned kPlayers=2,kCars=256,kRaceCars=8;
constexpr int kTyreButton=6; // GENERAL rows are 1..5; the native tick ignores IDs above 5.
std::array<std::array<std::atomic_uint,kCars>,kPlayers> paints{},tires{};
std::atomic_int menu_car{-1},menu_player{0};
std::array<std::atomic_int,kRaceCars> race_player{},race_car{};
std::atomic_uint generation{1};
extra_options::Config options{};
bool installed=false;
fs::path directory;
std::array<std::array<char,32>,kCars> families{};
struct Pixels {std::vector<unsigned char> original,derived;};
std::vector<Pixels> pixels;
void log(const char* text) noexcept {try {std::ofstream f(directory/"MRallyeExtraOptions.log",std::ios::app);f<<text<<'\n';}catch(...) {}}
bool read(uintptr_t p,void* data,size_t n) noexcept {SIZE_T done=0;return p&&ReadProcessMemory(GetCurrentProcess(),reinterpret_cast<const void*>(p),data,n,&done)&&done==n;}
uint32_t key(const char* s){uint32_t result=0;fn<void(__thiscall*)(uint32_t*,const char*)>(0x4d0580)(&result,s);return result;}
void* broker(){return fn<void*(__cdecl*)()>(0x4d8ec0)();}
int integer(const char* s){auto k=key(s);return fn<int(__thiscall*)(void*,uint32_t*)>(0x4d6760)(broker(),&k);}
bool boolean(const char* s){auto k=key(s);return fn<bool(__thiscall*)(void*,uint32_t*)>(0x4d6520)(broker(),&k);}
float real(const char* s){auto k=key(s);return fn<float(__thiscall*)(void*,uint32_t*)>(0x4d6650)(broker(),&k);}
void put_int(const char* s,int value){auto k=key(s);fn<void(__thiscall*)(void*,uint32_t*,int)>(0x4d8000)(broker(),&k,value);}
void put_name(const char* s,const char* value){auto k=key(s),v=key(value);fn<void(__thiscall*)(void*,uint32_t*,uint32_t*)>(0x4d85f0)(broker(),&k,&v);}
// Broker child lookup (gaIContDriverLookUp uses it for Controller/Car%d + ControllerCarBrokerAccess).
void* find(const char* parent,const char* child){auto a=key(parent),b=key(child);return fn<void*(__thiscall*)(void*,uint32_t*,uint32_t*)>(0x4d6fb0)(broker(),&a,&b);}
// UI Text* is a Name datum. 0x4d8720 is the String-path overload and
// re-interns both arguments; passing a Name ID there dereferences that ID.
std::string native_label(const char* value){std::string text(value);for(auto& c:text)if(c>='a'&&c<='z')c=char(c-'a'+'A');return text;}
void put_text(const char* s,const char* value){const auto text=native_label(value);put_name(s,text.c_str());}
const extra_package::Vehicle* vehicle(int id){for(const auto& v:extra_package::vehicles)if(v.id==id)return &v;return nullptr;}

// Appearance: the same PS2/PC pair for every car (owner decision; per-car texture variants retired).
constexpr const char* kLabels[]={"PS2","PC"};
constexpr unsigned kKinds[]={2,1}; // MRExtraVisualV2: 1 = PC bundle, 2 = PS2 bundle
unsigned paint_count(int){return 2u;}
const char* paint_label(int,unsigned i){return kLabels[i<2?i:0];}
unsigned paint_kind(int,unsigned i){return kKinds[i<2?i:0];}
// EXTRA-SET1 state stored preset indexes; keep only whether the preset was the PC bundle.
unsigned migrate_paint(int id,unsigned stored){auto* v=vehicle(id);if(v)return stored<v->paint_count&&v->paint_kinds[stored]==1?1u:0u;return stored<2?stored:0u;}
int clamp_player(int p){return p==1?1:0;}

// Folder name of a physical CarID: native registry 0x45a3c0, 0x34-byte rows, C string at +0x24
// (the setup loader 0x44d720 copies it with 0x4d1990). Live check: IDs 0..32 incl. SDK cars.
// Rows past the roster belong to other tables, so path-like or empty strings are rejected.
const char* family(int id){
 if(id<0||id>=int(kCars))return "";
 auto& slot=families[id];
 if(!slot[0]){
  const auto table=reinterpret_cast<uintptr_t>(fn<void*(__cdecl*)()>(0x45a3c0)());uintptr_t text=0;char copy[32]{};
  if(table&&read(table+0x24+uintptr_t(id)*0x34,&text,4)&&text&&read(text,copy,sizeof(copy)-1)&&copy[0]&&!std::strpbrk(copy,"/\\"))
   std::memcpy(slot.data(),copy,sizeof(copy));
 }
 return slot.data();
}

void list(const char* path,const std::vector<const char*>& values){
 // Native string vector layout from the original Gearbox initializer. Allocate
 // using the game's allocator; Broker owns the published list for this process.
 auto* v=static_cast<uint32_t*>(fn<void*(__cdecl*)(size_t)>(0x5c1cb4)(16));if(!v)throw 1;
 std::memset(v,0,16);
 for(const auto* text:values){const auto label=native_label(text);uint32_t s=0;fn<void(__thiscall*)(uint32_t*,const char*)>(0x4d11d0)(&s,label.c_str());
  fn<void(__thiscall*)(void*,uintptr_t,unsigned,uint32_t*)>(0x407b30)(v,v[2],1,&s);
  fn<void(__cdecl*)(uintptr_t)>(0x5b4c00)(s);
 }
 auto k=key(path);fn<void(__thiscall*)(void*,uint32_t*,void*)>(0x4d8880)(broker(),&k,v);
}
void save(int player,int id){
 const auto path=(directory/"MRallyeExtraOptions.state.ini").wstring();wchar_t section[32]{},number[16]{};
 std::swprintf(section,32,player?L"Player2Car%d":L"Car%d",id);
 std::swprintf(number,16,L"%u",paints[player][id].load());WritePrivateProfileStringW(section,L"Paint",number,path.c_str());
 std::swprintf(number,16,L"%u",tires[player][id].load());WritePrivateProfileStringW(section,L"Tire",number,path.c_str());
}

// --- GENERAL page: TYRE TYPE ---------------------------------------------------------------
struct Row {int player=-1,car=-1;unsigned value=0;};
Row tyre_row,look_row;
// The setup screens resolve the car exactly like the native setup loader 0x44d720.
int setup_car(int player){
 if(boolean("Frontend/InQuickRaceMode")){void* q=fn<void*(__cdecl*)()>(0x4ada50)();return q?fn<int(__thiscall*)(void*,int)>(0x4ac660)(q,player):-1;}
 void* c=fn<void*(__cdecl*)()>(0x4b0af0)();return c?fn<int(__thiscall*)(void*,int)>(0x4b0630)(c,player):-1;
}
void publish_tyre(){
 const unsigned v=tyre_row.value;
 put_text("Frontend/ExtraOptions/TireText",extra_options::kTireLabels[v]);
 put_int("Frontend/ExtraOptions/Tire",int(v));
 put_int("Frontend/ExtraOptions/TireLeftArrow",v>0);
 put_int("Frontend/ExtraOptions/TireRightArrow",v+1<extra_options::kTireCount);
}
void tyre_sync(bool force){
 const int player=clamp_player(integer("Frontend/CarSetup/PlayerID")),car=setup_car(player);
 if(car<0||car>=int(kCars)){tyre_row={};return;}
 if(force||player!=tyre_row.player||car!=tyre_row.car){
  tyre_row={player,car,tires[player][car].load()};if(tyre_row.value>=extra_options::kTireCount)tyre_row.value=0;
  list("Frontend/ExtraOptions/TireList",{extra_options::kTireLabels.begin(),extra_options::kTireLabels.end()});
  publish_tyre();return;
 }
 const int v=integer("Frontend/ExtraOptions/Tire");
 if(v>=0&&unsigned(v)<extra_options::kTireCount&&unsigned(v)!=tyre_row.value){
  tyre_row.value=unsigned(v);tires[player][car]=tyre_row.value;save(player,car);publish_tyre();
  char line[160]{};std::snprintf(line,sizeof(line),"TIRE_SELECTED player=%d CarID=%d compound=%s",player+1,car,extra_options::kTireLabels[v]);log(line);
 }
}
void __fastcall general_init(void* self,void*,void* argument){fn<Init>(kGeneralInit)(self,argument);try{tyre_sync(true);}catch(...){log("TIRE_MENU_INIT_FAILED");}}
uintptr_t __fastcall general_tick(void* self,void*,uint32_t argument){
 const auto result=fn<Tick>(kGeneralTick)(self,argument);
 try{tyre_sync(false);}catch(...){log("TIRE_MENU_UPDATE_FAILED");}
 return result;
}
// Confirm on TYRE TYPE behaves like confirm on the four native rows.
int __fastcall general_command(void* manager,void*,unsigned sound){const int c=fn<Command>(kCommand)(manager,sound);return c==kTyreButton?1:c;}

// --- Vehicle Select: MODEL (PS2/PC), applied immediately -------------------------------------
void publish_look(){
 const unsigned v=look_row.value,n=paint_count(look_row.car);
 put_text("Frontend/ExtraOptions/PaintText",paint_label(look_row.car,v));
 put_int("Frontend/ExtraOptions/Paint",int(v));
 put_int("Frontend/ExtraOptions/PaintLeftArrow",v>0);
 put_int("Frontend/ExtraOptions/PaintRightArrow",v+1<n);
}
void look_sync(bool force){
 const int player=clamp_player(integer("Frontend/VehicleSelect/PlayerID")),car=integer("Frontend/VehicleSelect/CarModel");
 if(car<0||car>=int(kCars)){look_row={};menu_car=-1;return;}
 menu_player=player;menu_car=car;family(car);
 if(force||player!=look_row.player||car!=look_row.car){
  look_row={player,car,paints[player][car].load()};if(look_row.value>=paint_count(car))look_row.value=0;
  std::vector<const char*> labels;for(unsigned i=0;i<paint_count(car);++i)labels.push_back(paint_label(car,i));
  list("Frontend/ExtraOptions/PaintList",labels);publish_look();return;
 }
 const int v=integer("Frontend/ExtraOptions/Paint");
 if(v>=0&&unsigned(v)<paint_count(car)&&unsigned(v)!=look_row.value){
  look_row.value=unsigned(v);paints[player][car]=look_row.value;++generation;save(player,car);publish_look();
  char line[180]{};std::snprintf(line,sizeof(line),"APPEARANCE_SELECTED player=%d CarID=%d family=%s choice=%s",player+1,car,family(car),paint_label(car,v));log(line);
 }
}
void __fastcall select_init(void* self,void*,void* argument){fn<Init>(kSelectInit)(self,argument);try{look_sync(true);}catch(...){log("APPEARANCE_MENU_INIT_FAILED");}}
// Left/Right on MODEL changes only the model, never the carousel.
void __fastcall select_scroll(void* self,void*,int direction){
 try{void* buttons=fn<void*(__cdecl*)()>(0x525a80)();if(buttons&&fn<int(__thiscall*)(void*)>(0x525800)(buttons)==kModelButton)return;}catch(...){}
 fn<void(__thiscall*)(void*,int)>(kSelectScroll)(self,direction);
}
uintptr_t __fastcall select_tick(void* self,void*,uint32_t argument){
 const auto result=fn<Tick>(kSelectTick)(self,argument);
 try{look_sync(false);}catch(...){log("APPEARANCE_MENU_UPDATE_FAILED");}
 return result;
}

// --- Race: human wheels -----------------------------------------------------------------------
struct Human {int car_index=-1,player=0,car=-1;uintptr_t controller=0;unsigned compound=0;bool logged=false;};
struct RaceCache {
 ULONGLONG stamp=0;bool attract=true;unsigned count=0;std::array<Human,kRaceCars> humans{};
 float stock[extra_options::kSurfaceCount][extra_options::kTyreFields]{};bool unbound_logged=false;
} race;
void refresh_race(){
 race.stamp=GetTickCount64();race.attract=boolean("Race/AttractMode");race.count=0;
 int player=0;char path[64]{};
 const int cars=integer("Race/NumCars");
 for(unsigned n=0;n<kRaceCars;++n){
  race_player[n]=-1;race_car[n]=-1;
  if(int(n)>=cars)continue;
  std::snprintf(path,sizeof(path),"Race/Car%u/PlayerType",n);if(integer(path)!=1)continue;
  std::snprintf(path,sizeof(path),"Race/Car%u/CarID",n);const int id=integer(path);
  Human h;h.car_index=int(n);h.player=clamp_player(player++);h.car=id;
  race_player[n]=h.player;race_car[n]=id;if(id>=0&&id<int(kCars)){family(id);h.compound=tires[h.player][id].load();}
  std::snprintf(path,sizeof(path),"Controller/Car%u",n);
  uintptr_t entry=reinterpret_cast<uintptr_t>(find(path,"ControllerCarBrokerAccess")),object=0;
  if(entry&&read(entry+8,&object,4))h.controller=object;
  for(const auto& old:race.humans)if(old.car_index==h.car_index&&old.controller==h.controller&&old.car==h.car)h.logged=old.logged;
  race.humans[race.count++]=h;
 }
 for(unsigned s=0;s<extra_options::kSurfaceCount;++s)for(unsigned f=0;f<extra_options::kTyreFields;++f){
  std::snprintf(path,sizeof(path),"Vehicles/Tyres/%s0/%s",extra_options::kSurfaces[s],extra_options::kTyreFieldNames[f]);
  race.stock[s][f]=real(path);
 }
}
void apply_wheel(void* wheel){
 if(!options.enabled||!options.tires)return;
 if(!race.stamp||GetTickCount64()-race.stamp>500)refresh_race();
 if(race.attract||!race.count)return;
 uintptr_t car=0,controller=0;
 if(!read(reinterpret_cast<uintptr_t>(wheel)+0x18,&car,4)||!read(car+0x14,&controller,4))return;
 for(unsigned i=0;i<race.count;++i){
  auto& h=race.humans[i];
  // The wheel's controller pointer is a sub-object of enController_Car (0x5c vs AI +0x74).
  if(!h.controller||controller<h.controller||controller-h.controller>0x80)continue;
  const extra_options::Participant p{1,h.car,race.attract};
  if(!extra_options::tire_applies(options,p)||!h.compound)return;
  uintptr_t begin=0,end=0;
  if(!read(reinterpret_cast<uintptr_t>(wheel)+0x170,&begin,4)||!read(reinterpret_cast<uintptr_t>(wheel)+0x174,&end,4)||end<=begin)return;
  const unsigned count=unsigned((end-begin)/0x30);if(count==0||count>16||(end-begin)%0x30)return;
  float records[16*extra_options::kTyreFields]{};if(!read(begin,records,count*0x30))return;
  const unsigned changed=extra_options::apply_compound(records,count,static_cast<extra_options::Tire>(h.compound),race.stock);
  if(changed)std::memcpy(reinterpret_cast<void*>(begin),records,count*0x30);
  if(changed&&!h.logged){h.logged=true;char line[220]{};
   std::snprintf(line,sizeof(line),"TIRE_APPLIED Car%d player=%d CarID=%d compound=%s records=%u/%u controller_offset=0x%x",
                 h.car_index,h.player+1,h.car,extra_options::kTireLabels[h.compound],changed,count,unsigned(controller-h.controller));log(line);}
  return;
 }
 if(!race.unbound_logged){
  for(unsigned i=0;i<race.count;++i)if(race.humans[i].compound&&!race.humans[i].logged){
   race.unbound_logged=true;char line[200]{};
   std::snprintf(line,sizeof(line),"TIRE_BINDING_PENDING Car%d controller=0x%08x wheel_controller=0x%08x",race.humans[i].car_index,unsigned(race.humans[i].controller),unsigned(controller));log(line);break;}
 }
}
void __fastcall wheel_update(void* wheel,void*){
 fn<Wheel>(kWheel)(wheel);
 try{apply_wheel(wheel);}catch(...){}
}

bool patch(uintptr_t va,const void* p,size_t size){DWORD previous=0,ignored=0;if(!VirtualProtect(reinterpret_cast<void*>(va),size,PAGE_EXECUTE_READWRITE,&previous))return false;std::memcpy(reinterpret_cast<void*>(va),p,size);const bool ok=FlushInstructionCache(GetCurrentProcess(),reinterpret_cast<void*>(va),size)!=FALSE;return VirtualProtect(reinterpret_cast<void*>(va),size,previous,&ignored)&&ok;}
bool call_is(uintptr_t site,uintptr_t target){std::array<unsigned char,5> b{};if(!read(site,b.data(),b.size())||b[0]!=0xe8)return false;int32_t offset=0;std::memcpy(&offset,b.data()+1,4);return site+5+offset==target;}
bool slot_is(uintptr_t slot,uintptr_t target){uintptr_t v=0;return read(slot,&v,4)&&v==target;}
std::vector<unsigned char> load(const char* name,size_t bytes){std::ifstream f(directory/name,std::ios::binary|std::ios::ate);if(!f||f.tellg()!=std::streamoff(bytes))return {};std::vector<unsigned char> p(bytes);f.seekg(0);f.read(reinterpret_cast<char*>(p.data()),std::streamsize(bytes));if(!f)return {};return p;}
}

bool initialize() noexcept {try{
 wchar_t exe[32768]{};if(!GetModuleFileNameW(nullptr,exe,32768))return false;directory=fs::path(exe).parent_path();
 std::ifstream f(directory/"MRallyeExtraOptions.ini",std::ios::binary);std::string ini((std::istreambuf_iterator<char>(f)),{});
 const auto parsed=extra_options::parse_config(ini);if(parsed.accepted)options=parsed.config;else log("CONFIG absent/invalid; customization disabled; existing Randomizer settings unchanged");
 if(!options.enabled||(!options.tires&&!options.liveries)){log("CUSTOMIZATION_DISABLED no menu or wheel hooks installed");return true;}
 const auto state=(directory/"MRallyeExtraOptions.state.ini").wstring();
 for(unsigned p=0;p<kPlayers;++p)for(unsigned i=0;i<kCars;++i){wchar_t s[32]{};std::swprintf(s,32,p?L"Player2Car%u":L"Car%u",i);
  const auto paint=GetPrivateProfileIntW(s,L"Paint",0,state.c_str()),tire=GetPrivateProfileIntW(s,L"Tire",0,state.c_str());
  paints[p][i]=migrate_paint(int(i),paint);tires[p][i]=tire<extra_options::kTireCount?tire:0;}
 pixels.resize(extra_package::binding_count);for(unsigned i=0;i<extra_package::binding_count;++i){const auto& b=extra_package::bindings[i];const size_t size=size_t(b.width)*b.height*4;pixels[i].original=load(b.original,size);pixels[i].derived=load(b.derived,size);}
 for(const auto& api:extra_package::apis){std::array<unsigned char,8> observed{};if(!read(api.va,observed.data(),observed.size())||observed!=api.bytes){log("API_LAYOUT_UNSUPPORTED: no Extra Options hooks installed");return false;}}
 struct Write{uintptr_t address;std::array<unsigned char,5> before,after;unsigned size;};std::vector<Write> writes;
 const auto slot=[&](uintptr_t at,uintptr_t original,void* target){if(!slot_is(at,original))throw 2;Write w{at,{},{},4};read(at,w.before.data(),4);const auto v=reinterpret_cast<uintptr_t>(target);std::memcpy(w.after.data(),&v,4);writes.push_back(w);};
 const auto call=[&](uintptr_t at,uintptr_t original,void* target){if(!call_is(at,original))throw 2;Write w{at,{},{},5};read(at,w.before.data(),5);w.after[0]=0xe8;const auto o=int32_t(reinterpret_cast<uintptr_t>(target)-at-5);std::memcpy(w.after.data()+1,&o,4);writes.push_back(w);};
 try{
  if(options.tires){
   slot(kGeneralInitSlot,kGeneralInit,reinterpret_cast<void*>(&general_init));slot(kGeneralTickSlot,kGeneralTick,reinterpret_cast<void*>(&general_tick));
   call(kGeneralCommandCall,kCommand,reinterpret_cast<void*>(&general_command));call(kWheelCall,kWheel,reinterpret_cast<void*>(&wheel_update));
  }
  if(options.liveries){slot(kSelectInitSlot,kSelectInit,reinterpret_cast<void*>(&select_init));slot(kSelectTickSlot,kSelectTick,reinterpret_cast<void*>(&select_tick));
   call(kSelectScrollCall,kSelectScroll,reinterpret_cast<void*>(&select_scroll));}
 }catch(int){log("HOOK_CONFLICT: Extra Options not installed; selected call/vtable mismatch");return false;}
 for(size_t i=0;i<writes.size();++i)if(!patch(writes[i].address,writes[i].after.data(),writes[i].size)){for(size_t j=0;j<=i;++j)patch(writes[j].address,writes[j].before.data(),writes[j].size);log("HOOK_INSTALL_FAILED rolled back");return false;}
 for(unsigned n=0;n<kRaceCars;++n){race_player[n]=-1;race_car[n]=-1;}
 installed=true;
 char line[200]{};std::snprintf(line,sizeof(line),"READY EXTRA-SET2 tyres=%d (GENERAL page, all human players, any mode) appearance=%d (Vehicle Select) hooks=%u",
                                options.tires,options.liveries,unsigned(writes.size()));log(line);return true;
 }catch(...){log("INITIALIZATION_FAILED");return false;}}

} // namespace extra_runtime

namespace {
using namespace extra_runtime;
// Phase 0 = frontend preview (menu car), phase 1 = race participant index.
bool selection(int participant,unsigned phase,int& player,int& id){
 if(phase==0){player=menu_player.load();id=menu_car.load();}
 else{if(participant<0||participant>=int(kRaceCars))return false;player=race_player[participant].load();id=race_car[participant].load();}
 return player>=0&&id>=0&&id<int(kCars);
}
bool family_matches(int id,const char* family_name){
 const char* known=extra_runtime::family(id);
 if(known[0])return !_stricmp(known,family_name);
 auto* v=vehicle(id);return v&&!_stricmp(v->family,family_name);
}
}

// The renderer asks this module; it never owns or rewrites customization state.
extern "C" unsigned WINAPI MRExtraOptionsAbi(){return 0x45583201u;}
// V2 identifies the selected appearance independently of renderer lighting.
// 0=no applicable selection, 1=PC bundle, 2=PS2 bundle, 3=PS2 with PC textures.
extern "C" unsigned WINAPI MRExtraVisualV2(const char* family_name,int participant,unsigned phase){
 if(!installed||!options.enabled||!options.liveries||!family_name)return 0;
 int player=0,id=-1;if(!selection(participant,phase,player,id)||!family_matches(id,family_name))return 0;
 const unsigned choice=paints[player][id];if(choice>=paint_count(id))return 0;
 return paint_kind(id,choice);
}
// V1 (legacy renderer builds): 1 = keep the complete original PC bundle.
extern "C" unsigned WINAPI MRExtraVisualV1(const char* family_name,int participant,unsigned phase){
 return MRExtraVisualV2(family_name,participant,phase)==1?1u:0u;
}
extern "C" unsigned WINAPI MRExtraRevisionV1(const char* family_name,int,unsigned){return family_name?generation.load():0;}
extern "C" BOOL WINAPI MRExtraTextureV1(const char* family_name,unsigned index,unsigned width,unsigned height,const void* original,void* output,unsigned bytes,int participant,unsigned phase){
 if(!original||!output||MRExtraVisualV2(family_name,participant,phase)!=3)return FALSE;
 int player=0,id=-1;selection(participant,phase,player,id);
 for(unsigned i=0;i<extra_package::binding_count;++i){const auto& b=extra_package::bindings[i];if(index==b.index&&width==b.width&&height==b.height&&bytes==pixels[i].original.size()&&bytes==pixels[i].derived.size()&&!std::memcmp(original,pixels[i].original.data(),bytes)){std::memcpy(output,pixels[i].derived.data(),bytes);char message[180]{};std::snprintf(message,sizeof(message),"TEXTURE_ACCEPTED family=%s CarID=%d phase=%u index=%u size=%ux%u",family_name,id,phase,index,width,height);log(message);return TRUE;}}
 char message[180]{};std::snprintf(message,sizeof(message),"TEXTURE_REJECTED family=%s CarID=%d phase=%u index=%u size=%ux%u bytes=%u",family_name,id,phase,index,width,height,bytes);log(message);
 return FALSE;
}
