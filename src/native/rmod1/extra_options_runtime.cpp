#define WIN32_LEAN_AND_MEAN
#define NOMINMAX
#include <windows.h>
#include "extra_options_runtime.hpp"
#include "extra_options.hpp"
#include "extra_options_package.hpp"
#include "extra_registry.hpp"
#include "vehicle_options.hpp"
#include "menu_dynamic.hpp"
#include <deque>
#include <functional>
#include <cctype>
#include <memory>
#include <mutex>
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
constexpr int kModelButton=3,kPaintButton=4;
// Race participant identity (0x44A320 loop): 0x44A510 (quick race wrapper) / 0x44A710 (championship wrapper) copy the
// registry folder of the participant's CarID into Race/Car<N>/CarType and WheelType, which the body/wheel boot
// 0x4B6A00 loads as vehicles/<name>/car|wheel. Both are thiscall (car index, extra) RET 8.
constexpr uintptr_t kIdentityQuickCall=0x44a389,kIdentityQuick=0x44a510,kIdentityCupCall=0x44a394,kIdentityCup=0x44a710;
constexpr unsigned kUnset=0xffffffffu;   // no stored choice: the family default applies
constexpr unsigned kPlayers=2,kRaceCars=8;
unsigned car_count=0;
uintptr_t registry_getter=0x45a3c0;
constexpr int kTyreButton=6; // GENERAL rows are 1..5; the native tick ignores IDs above 5.
std::array<std::unique_ptr<std::atomic_uint[]>,kPlayers> paints{},tires{},colours{};
std::atomic_int menu_car{-1},menu_player{0};
std::array<std::atomic_int,kRaceCars> race_player{},race_car{};
std::atomic_uint generation{1};
extra_options::Config options{};
bool installed=false;
fs::path directory;
std::unique_ptr<std::array<char,65>[]> families;
std::mutex family_mutex;
bool valid_car(int id){return id>=0 && unsigned(id)<car_count;}
// --- DEMO model variants (Roster V4, docs/vehicle-manager/ROSTER_V4_PLAN.md stage 3) ------------
// The installed roster may list, per family, an alternative resource folder (the historical Demo model) in
// MRMods/Vehicles/active/variants.ini. Choosing DEMO on the MODEL row points that CarID's registry folder
// (row +0x24, the string every model/physics loader reads) at the variant folder; the roster ships the folder's
// resources and a physics block cloned from the family. The registry row is global, so the latest choice of
// the player in Vehicle Select applies to every car with that CarID (opponents included).
struct Variant {std::string base,folder,manufacturer,model,widget;int carsheet=-1,small=-1,widget_frame=-1;};
// Per CarID: original race small-icon frame (registry row +0x1C) and the live Vehicle Select widget whose
// carousel widget state (egg pointer, frame last queued).
struct VariantArt {uint32_t small=0;uintptr_t egg=0;int shown=-1;};
std::unique_ptr<VariantArt[]> variant_art;
std::unique_ptr<signed char[]> no_switch;   // per CarID: -1 unknown, 0 switchable, 1 nothing to switch (added cars)

std::vector<Variant> variants;
std::unique_ptr<int[]> variant_of;            // per CarID: index into variants, -1 none, -2 not resolved yet
std::unique_ptr<uintptr_t[]> original_folder; // registry folder pointer as constructed
uintptr_t registry_row(int id);
int variant_index(int id);
bool declared_model(int id);
const char* family(int id);
void allocate_state(unsigned count){
 std::array<std::unique_ptr<std::atomic_uint[]>,kPlayers> next_paints,next_tires,next_colours;
 for(unsigned p=0;p<kPlayers;++p){next_paints[p]=std::make_unique<std::atomic_uint[]>(count);next_tires[p]=std::make_unique<std::atomic_uint[]>(count);
  next_colours[p]=std::make_unique<std::atomic_uint[]>(count);
  for(unsigned i=0;i<count;++i){next_paints[p][i]=kUnset;next_tires[p][i]=0;next_colours[p][i]=kUnset;}}
 auto next_families=std::make_unique<std::array<char,65>[]>(count);
 auto next_variants=std::make_unique<int[]>(count);auto next_original=std::make_unique<uintptr_t[]>(count);
 variant_art=std::make_unique<VariantArt[]>(count);
 no_switch=std::make_unique<signed char[]>(count);for(unsigned i=0;i<count;++i)no_switch[i]=-1;
 for(unsigned i=0;i<count;++i){next_variants[i]=variants.empty()?-1:-2;next_original[i]=0;}
 paints=std::move(next_paints);tires=std::move(next_tires);colours=std::move(next_colours);families=std::move(next_families);car_count=count;
 variant_of=std::move(next_variants);original_folder=std::move(next_original);
}
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


// MODEL row. Retail families: PS2/PC for every car (owner decision), DEMO as a third choice where the roster has a
// variant. A family declared in vehicle-options.ini replaces them with its own choices (equipment kits, one resource
// folder each) or with none (add-on cars: the row is hidden/"-"). PAINT row: the family's paints, if any.
vehicle_options::Table vopts;
const vehicle_options::Family* declared(int id);
constexpr const char* kLabels[]={"PS2","PC","DEMO"};
constexpr unsigned kKinds[]={2,1,1}; // MRExtraVisualV2: 1 = PC bundle, 2 = PS2 bundle; DEMO renders as PC
// Cars with nothing to switch (no PS2 bundle, no DEMO variant: the added Heritage/SDK cars) get one "-" choice and
// the row is hidden. Families with a PS2 bundle = the renderer's race fleet table (frontend_fleet_registry.hpp,
// kRaceFleetProfiles: PC family -> PS2 model); keep in sync when the renderer gains a PS2 model.
constexpr const char* kPs2Families[]={"Astero","Bruno","ChevyBlazer","Forester","ForesterSTI","Frontera","IceCream","Jump","Kamaz",
 "Kangoo","KiaSportage","LandCruiser","Mattserati","Navara","NewRav","Pajero","Patrol","RMonster","SeatBuggy","Simmbugghini",
 "Tata","Terrano","Ufo","WildCat","Xtrail","forklift","megane"};
bool nothing_to_switch(int id){
 if(!no_switch||!valid_car(id))return false;
 if(no_switch[id]>=0)return no_switch[id]==1;
 const char* f=family(id);if(!f[0])return false;               // registry not readable yet: ask again later
 bool ps2=false;for(const char* r:kPs2Families)if(!_stricmp(r,f))ps2=true;
 const bool single=!ps2&&variant_index(id)<0;
 no_switch[id]=single?1:0;
 if(single){char line[160]{};std::snprintf(line,sizeof(line),"MODEL_ROW_NONE CarID=%d family=%s (no PS2 bundle, no DEMO)",id,f);log(line);}
 return single;
}
unsigned paint_count(int id){
 if(auto* f=declared(id);f&&f->model_declared)return f->model.size()<2?1u:unsigned(f->model.size());
 if(nothing_to_switch(id))return 1u;
 return variant_index(id)>=0?3u:2u;
}
const char* paint_label(int id,unsigned i){
 if(auto* f=declared(id);f&&f->model_declared)return f->model.size()<2?"-":f->model[i<f->model.size()?i:0].c_str();
 if(nothing_to_switch(id))return "-";
 return kLabels[i<3?i:0];
}
unsigned paint_kind(int id,unsigned i){if(auto* f=declared(id);(f&&f->model_declared)||nothing_to_switch(id))return 1u;return kKinds[i<3?i:0];}
const char* model_caption(int id){if(auto* f=declared(id))return f->model_label.c_str();return "MODEL";}
unsigned colour_count(int id){auto* f=declared(id);return f&&f->paints.size()>1?unsigned(f->paints.size()):1u;}
const char* colour_label(int id,unsigned i){auto* f=declared(id);return f&&f->paints.size()>1?f->paints[i<f->paints.size()?i:0].c_str():"-";}
// Stored choices: kUnset = never chosen -> family default.
unsigned model_value(int player,int id){
 const unsigned n=paint_count(id),raw=paints[player][id].load();
 if(raw==kUnset){auto* f=declared(id);return f&&f->model_declared&&f->model_default<n?f->model_default:0u;}
 return raw%n;
}
unsigned colour_value(int player,int id){
 const unsigned n=colour_count(id),raw=colours[player][id].load();
 if(raw==kUnset){auto* f=declared(id);return f&&f->paint_default<n?f->paint_default:0u;}
 return raw%n;
}
// EXTRA-SET1 state stored preset indexes; keep only whether the preset was the PC bundle. 2 = DEMO (checked
// against the roster when used: a car without a variant falls back to PS2). kUnset stays unset.
unsigned migrate_paint(int id,unsigned stored){if(stored==kUnset)return kUnset;auto* v=vehicle(id);if(stored==2)return 2u;if(v)return stored<v->paint_count&&v->paint_kinds[stored]==1?1u:0u;return stored<2?stored:0u;}
int clamp_player(int p){return p==1?1:0;}

// Folder name of a physical CarID: native registry 0x45a3c0, 0x34-byte rows, C string at +0x24
// (the setup loader 0x44d720 copies it with 0x4d1990). Live check: IDs 0..32 incl. SDK cars.
// Rows past the roster belong to other tables, so path-like or empty strings are rejected.
const char* family(int id){
 if(!valid_car(id))return "";
 std::lock_guard<std::mutex> lock(family_mutex);
 auto& slot=families[id];
 if(!slot[0]){
  const auto table=reinterpret_cast<uintptr_t>(fn<void*(__cdecl*)()>(registry_getter)());uintptr_t text=0;char copy[65]{};
  if(table&&read(table+0x24+uintptr_t(id)*0x34,&text,4)&&text&&read(text,copy,sizeof(copy)-1)&&copy[0]&&!std::strpbrk(copy,"/\\"))
   std::memcpy(slot.data(),copy,sizeof(copy));
 }
 return slot.data();
}

// vehicle-options.ini entry of the CarID's family (null: retail behaviour, or the registry is not readable yet).
const vehicle_options::Family* declared(int id){
 if(vopts.families.empty()||!valid_car(id))return nullptr;
 const char* f=family(id);return f[0]?vopts.find(f):nullptr;
}
// Folder string the game should load for this player's choices: the kit (or DEMO/family folder) plus "__p<n>" for a
// paint. Interned: the registry row may point at it while the menu-car tick runs.
bool declared_model(int id){auto* f=declared(id);return f&&f->model_declared;}
std::deque<std::string> interned;
const char* intern_name(const std::string& s){for(auto& i:interned)if(i==s)return i.c_str();interned.push_back(s);return interned.back().c_str();}
int variant_index(int id);
const char* participant_folder(int player,int id){
 const char* base=family(id);if(!base[0])return base;
 std::string kit=base;
 const unsigned m=player>=0?model_value(player,id):[&]{auto* f=declared(id);return f&&f->model_declared?f->model_default:0u;}();
 if(auto* f=declared(id);f&&f->model_declared){if(f->model.size()>=2&&m<f->folders.size())kit=f->folders[m];}
 else if(m==2&&variant_index(id)>=0)kit=variants[size_t(variant_index(id))].folder;
 const unsigned c=player>=0?colour_value(player,id):[&]{auto* f=declared(id);return f&&f->paints.size()>1?f->paint_default:0u;}();
 return intern_name(vehicle_options::virtual_name(kit,colour_count(id)>1?c:0));
}

// --- DEMO variants: registry folder pointer --------------------------------------------------------
uintptr_t registry_row(int id){
 const auto table=reinterpret_cast<uintptr_t>(fn<void*(__cdecl*)()>(registry_getter)());
 return table?table+0x24+uintptr_t(id)*0x34:0;
}
int variant_index(int id){
 if(!valid_car(id)||!variant_of)return -1;
 if(variant_of[id]!=-2)return variant_of[id];
 int found=-1;uintptr_t text=0;char copy[65]{};
 const uintptr_t row=registry_row(id);
 if(!row||!read(row,&text,4)||!text||!read(text,copy,sizeof(copy)-1))return -1; // registry not readable yet: retry later
 for(size_t i=0;i<variants.size();++i)if(!_stricmp(copy,variants[i].base.c_str())){found=int(i);break;}
 original_folder[id]=text;variant_of[id]=found;
 if(variant_art)read(row-4,&variant_art[id].small,4);   // small-icon frame, the field before the folder
 if(found>=0){char line[200]{};std::snprintf(line,sizeof(line),"VARIANT_BOUND CarID=%d family=%s DEMO=%s",id,copy,variants[size_t(found)].folder.c_str());log(line);}
 return found;
}
bool demo_selected(int player,int id){const int v=variant_index(id);return v>=0&&!declared_model(id)&&model_value(clamp_player(player),id)==2;}
// Revision 2: the registry folder is no longer swapped globally (the menu car gets its folder only inside its own tick,
// race participants through Race/Car<N>/CarType). What stays per CarID is the race small icon of a DEMO variant
// (registry row +0x1C, the field before the folder); true when it changed.
bool apply_variant(int player,int id){
 const int v=variant_index(id);if(v<0)return false;
 const auto& var=variants[size_t(v)];
 const uintptr_t row=registry_row(id);
 if(var.small<0||!variant_art||!row)return false;
 const uint32_t small=demo_selected(player,id)?uint32_t(var.small):variant_art[id].small;
 uint32_t now=0;if(!read(row-4,&now,4)||now==small)return false;
 DWORD previous=0,ignored=0;
 if(!VirtualProtect(reinterpret_cast<void*>(row-4),4,PAGE_READWRITE,&previous))return false;
 std::memcpy(reinterpret_cast<void*>(row-4),&small,4);VirtualProtect(reinterpret_cast<void*>(row-4),4,previous,&ignored);
 char line[200]{};std::snprintf(line,sizeof(line),"VARIANT_ICON player=%d CarID=%d small=%u",player+1,id,small);log(line);
 return true;
}
void apply_all_variants(int player){if(!variants.empty())for(unsigned id=0;id<car_count;++id)apply_variant(player,int(id));}
// Menu car display AI (gaFE car egg, vtable slot 0x69021c -> 0x44c4c0, thiscall RET 4): each tick it reads the car
// ID from the Broker key at +0x10, compares it with the cached one at +0x0C and, on a change, builds
// "Vehicles/<registry row +0x24>/complete" synchronously (0x44C550..0x44C58A). For the Vehicle Select car the row
// points at the player's kit/paint folder for the duration of that call only; a different folder than last time
// invalidates the cache so the model is rebuilt at once.
constexpr uintptr_t kDisplayTickSlot=0x69021c,kDisplayTick=0x44c4c0;
std::atomic_uint display_refresh{0};
struct DisplaySeen {void* self=nullptr;const char* folder=nullptr;};
std::array<DisplaySeen,8> display_seen{};unsigned display_next=0;
void __fastcall display_tick(void* self,void*,void* argument){
 uintptr_t row=0,original=0;bool swapped=false;
 try{
  const int id=fn<int(__thiscall*)(void*,void*)>(0x4d6760)(broker(),static_cast<char*>(self)+0x10);
  const char* want=nullptr;
  if(installed&&options.enabled&&options.liveries&&valid_car(id)&&id==menu_car.load()){
   want=participant_folder(clamp_player(menu_player.load()),id);
   if(!want[0]||!_stricmp(want,family(id)))want=nullptr;
  }
  DisplaySeen* slot=nullptr;for(auto& s:display_seen)if(s.self==self)slot=&s;
  if(!slot){slot=&display_seen[display_next++%display_seen.size()];*slot={self,nullptr};}
  if(slot->folder!=want){slot->folder=want;const int stale=-2;std::memcpy(static_cast<char*>(self)+0xc,&stale,4);}
  if(want&&(row=registry_row(id))!=0&&read(row,&original,4)&&original){
   const auto ptr=reinterpret_cast<uintptr_t>(want);DWORD previous=0,ignored=0;
   if(VirtualProtect(reinterpret_cast<void*>(row),4,PAGE_READWRITE,&previous)){std::memcpy(reinterpret_cast<void*>(row),&ptr,4);VirtualProtect(reinterpret_cast<void*>(row),4,previous,&ignored);swapped=true;}
  }
 }catch(...){}
 fn<void(__thiscall*)(void*,void*)>(kDisplayTick)(self,argument);
 if(swapped){DWORD previous=0,ignored=0;
  if(VirtualProtect(reinterpret_cast<void*>(row),4,PAGE_READWRITE,&previous)){std::memcpy(reinterpret_cast<void*>(row),&original,4);VirtualProtect(reinterpret_cast<void*>(row),4,previous,&ignored);}}
}
// Race: Race/Car<N>/CarType and WheelType of every participant become its own kit/paint folder (humans: their
// choice, AI: the family default). Physics (0x44ED50) and setup screens keep reading the registry family folder.
void race_identity(int car){
 if(!installed||!options.enabled||!options.liveries||car<0||car>=int(kRaceCars)||boolean("Race/AttractMode"))return;
 char path[64]{};
 std::snprintf(path,sizeof(path),"Race/Car%d/CarID",car);const int id=integer(path);
 if(!valid_car(id))return;
 std::snprintf(path,sizeof(path),"Race/Car%d/PlayerType",car);
 int player=-1;
 if(integer(path)==1){int humans=0;for(int k=0;k<car;++k){std::snprintf(path,sizeof(path),"Race/Car%d/PlayerType",k);if(integer(path)==1)++humans;}player=clamp_player(humans);}
 const char* name=participant_folder(player,id);
 if(!name[0]||!_stricmp(name,family(id)))return;
 uint32_t text=0;fn<void(__thiscall*)(uint32_t*,const char*)>(0x4d1990)(&text,name);
 void* wrapper=fn<void*(__cdecl*)()>(0x4ada50)();
 if(wrapper){fn<void(__thiscall*)(void*,int,uint32_t*)>(0x4aca40)(wrapper,car,&text);fn<void(__thiscall*)(void*,int,uint32_t*)>(0x4acb40)(wrapper,car,&text);}
 fn<void(__cdecl*)(uintptr_t)>(0x5b4c00)(text);
 char line[200]{};std::snprintf(line,sizeof(line),"RACE_IDENTITY Car%d player=%d CarID=%d family=%s folder=%s",car,player+1,id,family(id),name);log(line);
}
void __fastcall identity_quick(void* self,void*,int car,int extra){fn<void(__thiscall*)(void*,int,int)>(kIdentityQuick)(self,car,extra);try{race_identity(car);}catch(...){log("RACE_IDENTITY_FAILED");}}
void __fastcall identity_cup(void* self,void*,int car,int extra){fn<void(__thiscall*)(void*,int,int)>(kIdentityCup)(self,car,extra);try{race_identity(car);}catch(...){log("RACE_IDENTITY_FAILED");}}
void load_vehicle_options(){
 const auto path=directory/"MRMods"/"Vehicles"/"active"/"vehicle-options.ini";
 std::ifstream f(path,std::ios::binary);if(!f)return;
 std::string text((std::istreambuf_iterator<char>(f)),{}),error;
 vehicle_options::Table table;
 char line[300]{};
 if(vehicle_options::parse(text,table,error)){vopts=std::move(table);std::snprintf(line,sizeof(line),"VEHICLE_OPTIONS_LOADED families=%u",unsigned(vopts.families.size()));}
 else std::snprintf(line,sizeof(line),"VEHICLE_OPTIONS_REJECTED %s; retail MODEL rows only",error.c_str());
 log(line);
}
void load_variants(){
 const auto path=(directory/"MRMods"/"Vehicles"/"active"/"variants.ini").wstring();
 if(GetFileAttributesW(path.c_str())==INVALID_FILE_ATTRIBUTES)return;
 for(unsigned i=0;i<64;++i){
  wchar_t section[24]{};std::swprintf(section,24,L"Variant%u",i);
  auto get=[&](const wchar_t* key){wchar_t w[128]{};GetPrivateProfileStringW(section,key,L"",w,128,path.c_str());std::string out;for(const wchar_t* c=w;*c;++c)out.push_back(*c<128?char(*c):'?');return out;};
  Variant v{get(L"Base"),get(L"Folder"),get(L"Manufacturer"),get(L"Model")};
  {const auto c=get(L"CarSheetFrame"),m=get(L"SmallFrame"),f=get(L"WidgetFrame");v.widget=get(L"Widget");
   if(!c.empty())v.carsheet=std::atoi(c.c_str());if(!m.empty())v.small=std::atoi(m.c_str());if(!f.empty())v.widget_frame=std::atoi(f.c_str());}
  if(v.base.empty())break;
  if(v.folder.empty()||v.folder.find_first_of("/\\.")!=std::string::npos||v.folder.size()>48)continue;
  variants.push_back(v);
 }
 char line[96]{};std::snprintf(line,sizeof(line),"VARIANTS_LOADED count=%u",unsigned(variants.size()));log(line);
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
 // "Model" (revision 2) is the raw MODEL index; the EXTRA-SET1/2 "Paint" key is only read for migration.
 const unsigned model=paints[player][id].load(),colour=colours[player][id].load();
 if(model!=kUnset){std::swprintf(number,16,L"%u",model);WritePrivateProfileStringW(section,L"Model",number,path.c_str());}
 if(colour!=kUnset){std::swprintf(number,16,L"%u",colour);WritePrivateProfileStringW(section,L"Colour",number,path.c_str());}
 std::swprintf(number,16,L"%u",tires[player][id].load());WritePrivateProfileStringW(section,L"Tire",number,path.c_str());
}

// --- GENERAL page: TYRE TYPE ---------------------------------------------------------------
struct Row {int player=-1,car=-1;unsigned value=0;};
Row tyre_row;
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
 if(!valid_car(car)){tyre_row={};return;}
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
void apply_all_variants(int player);
void __fastcall general_init(void* self,void*,void* argument){fn<Init>(kGeneralInit)(self,argument);try{tyre_sync(true);apply_all_variants(clamp_player(integer("Frontend/CarSetup/PlayerID")));}catch(...){log("TIRE_MENU_INIT_FAILED");}}
uintptr_t __fastcall general_tick(void* self,void*,uint32_t argument){
 const auto result=fn<Tick>(kGeneralTick)(self,argument);
 try{tyre_sync(false);}catch(...){log("TIRE_MENU_UPDATE_FAILED");}
 return result;
}
// Confirm on TYRE TYPE behaves like confirm on the four native rows.
int __fastcall general_command(void* manager,void*,unsigned sound){const int c=fn<Command>(kCommand)(manager,sound);return c==kTyreButton?1:c;}

// --- Vehicle Select: MODEL (PS2/PC/DEMO or kits) and PAINT rows, applied immediately ----------------------
// Broker surface of the rows (scene: tools/extra_set2_frontend.py): MODEL = PaintList/Paint/PaintText/arrows plus the
// caption ModelLabel; PAINT = ColourList/Colour/ColourText/arrows. A row without choices shows "-", arrows off.
struct LookRow {int player=-1,car=-1;unsigned value=0,colour=0;};
LookRow look_row;
void publish_look(){
 const unsigned v=look_row.value,n=paint_count(look_row.car),c=look_row.colour,m=colour_count(look_row.car);
 put_text("Frontend/ExtraOptions/ModelLabel",model_caption(look_row.car));
 put_text("Frontend/ExtraOptions/PaintText",paint_label(look_row.car,v));
 put_int("Frontend/ExtraOptions/Paint",int(v));
 put_int("Frontend/ExtraOptions/PaintLeftArrow",v>0);
 put_int("Frontend/ExtraOptions/PaintRightArrow",v+1<n);
 put_text("Frontend/ExtraOptions/ColourText",colour_label(look_row.car,c));
 put_int("Frontend/ExtraOptions/Colour",int(c));
 put_int("Frontend/ExtraOptions/ColourLeftArrow",c>0);
 put_int("Frontend/ExtraOptions/ColourRightArrow",c+1<m);
}
void look_changed(int player,int car,const char* what,const char* label){
 ++generation;save(player,car);publish_look();
 char line[200]{};std::snprintf(line,sizeof(line),"APPEARANCE_SELECTED player=%d CarID=%d family=%s %s=%s folder=%s",player+1,car,family(car),what,label,participant_folder(player,car));log(line);
}
void look_sync(bool force){
 const int player=clamp_player(integer("Frontend/VehicleSelect/PlayerID")),car=integer("Frontend/VehicleSelect/CarModel");
 if(!valid_car(car)){look_row={};menu_car=-1;return;}
 menu_player=player;menu_car=car;family(car);
 if(force||player!=look_row.player||car!=look_row.car){
  look_row={player,car,model_value(player,car),colour_value(player,car)};
  std::vector<const char*> labels;for(unsigned i=0;i<paint_count(car);++i)labels.push_back(paint_label(car,i));
  list("Frontend/ExtraOptions/PaintList",labels);
  labels.clear();for(unsigned i=0;i<colour_count(car);++i)labels.push_back(colour_label(car,i));
  list("Frontend/ExtraOptions/ColourList",labels);publish_look();return;
 }
 // Both rows are read before either is published (publishing writes both Broker values back).
 const int v=integer("Frontend/ExtraOptions/Paint"),c=integer("Frontend/ExtraOptions/Colour");
 if(v>=0&&unsigned(v)<paint_count(car)&&unsigned(v)!=look_row.value){
  look_row.value=unsigned(v);paints[player][car]=look_row.value;look_changed(player,car,"model",paint_label(car,v));
 }
 if(c>=0&&unsigned(c)<colour_count(car)&&unsigned(c)!=look_row.colour){
  look_row.colour=unsigned(c);colours[player][car]=look_row.colour;look_changed(player,car,"paint",colour_label(car,c));
 }
}
// Vehicle Select names follow the model: the native publisher 0x4819b0 writes ManufacturerName/ModelName
// (localization groups 0x33/0x34 by CarID) only when the car changes; DEMO overrides them afterwards, and leaving
// DEMO re-runs the publisher. Folder swaps happen here too, so every path that changes MODEL is covered.
// Vehicle Select carousel: the widget egg (Vehicle Manager writes its name and scene frame into variants.ini) shows
// image-bank frames through its en2d object (egg+0x4C). The frame is changed the way gaFrontendDisablerAI does it
// (0x450E70): 0x4E23E0 trims the en2d command list, 0x4E1FF0 queues the new frame. Queued only on a change.
void sync_carousel_art(int player){
 if(!variant_art)return;
 uintptr_t manager=0;
 for(unsigned id=0;id<car_count;++id){
  const int v=variant_index(int(id));if(v<0)continue;
  const auto& var=variants[size_t(v)];
  if(var.carsheet<0||var.widget_frame<0||var.widget.empty())continue;
  if(!manager){fn<void(__cdecl*)()>(0x4f6310)();if(!read(0x6f96fc,&manager,4)||!manager)return;}
  uint32_t k=key(var.widget.c_str());
  const auto egg=reinterpret_cast<uintptr_t>(fn<void*(__thiscall*)(void*,uint32_t*)>(0x4f5eb0)(reinterpret_cast<void*>(manager),&k));
  uintptr_t en2d=0;
  if(!egg||!read(egg+0x4c,&en2d,4)||!en2d)continue;
  auto& art=variant_art[id];
  if(art.egg!=egg){art.egg=egg;art.shown=var.widget_frame;}       // a fresh screen starts with the scene frame
  const int want=demo_selected(player,int(id))?var.carsheet:var.widget_frame;
  if(art.shown==want)continue;
  fn<void(__thiscall*)(void*)>(0x4e23e0)(reinterpret_cast<void*>(en2d));
  fn<void(__thiscall*)(void*,int)>(0x4e1ff0)(reinterpret_cast<void*>(en2d),want);
  art.shown=want;
  char line[160]{};std::snprintf(line,sizeof(line),"VARIANT_CARSHEET CarID=%u widget=%s frame=%d",id,var.widget.c_str(),want);log(line);
 }
}
struct NameState {int car=-1;bool demo=false;} names;
void variant_sync(void* screen){
 if(variants.empty())return;
 const int player=clamp_player(integer("Frontend/VehicleSelect/PlayerID")),car=integer("Frontend/VehicleSelect/CarModel");
 if(!valid_car(car)){names={};return;}
 apply_variant(player,car);
 sync_carousel_art(player);
 const bool demo=demo_selected(player,car);
 if(car==names.car&&demo==names.demo)return;
 if(demo){const auto& v=variants[size_t(variant_index(car))];
  if(!v.manufacturer.empty())put_text("Frontend/VehicleSelect/ManufacturerName",v.manufacturer.c_str());
  if(!v.model.empty())put_text("Frontend/VehicleSelect/ModelName",v.model.c_str());}
 else if(car==names.car&&names.demo&&screen)fn<void(__thiscall*)(void*)>(0x4819b0)(screen);
 names={car,demo};
}
// Vehicle Select rows without choices are hidden (menu_dynamic.hpp): MODEL (button 3) when the family has fewer than
// two models, PAINT (button 4) when it has fewer than two paints. Order top -> bottom: Class 1, SelectCar 2, MODEL 3,
// PAINT 4, then back to Class (scene: tools/extra_set2_frontend.py). A scene without the PAINT row keeps MODEL -> Class.
uintptr_t egg_en2d(const std::string& name){
 uintptr_t manager=0;fn<void(__cdecl*)()>(0x4f6310)();if(!read(0x6f96fc,&manager,4)||!manager)return 0;
 uint32_t k=key(name.c_str());
 const auto egg=reinterpret_cast<uintptr_t>(fn<void*(__thiscall*)(void*,uint32_t*)>(0x4f5eb0)(reinterpret_cast<void*>(manager),&k));
 uintptr_t en2d=0;return egg&&read(egg+0x4c,&en2d,4)?en2d:0;
}
std::function<uintptr_t(const std::string&)> row_egg=egg_en2d;   // tests replace the egg lookup
std::vector<menu_dynamic::Row> select_rows;menu_dynamic::State select_rows_state;
menu_dynamic::Host select_rows_host(){
 return {row_egg,[]{return integer("UI/Active");},[](int b){put_int("UI/Active",b);},[](const std::string& s){log(s.c_str());}};
}
void select_rows_entered(){
 menu_dynamic::entered(select_rows,select_rows_state,select_rows_host());
 const bool paint_row=row_egg("ExtraPaint")!=0;
 select_rows.clear();
 select_rows.push_back({kModelButton,2,paint_row?kPaintButton:1,{"ExtraModel","ExtraModelText","ExtraModelLeftArrow","ExtraModelRightArrow"}});
 if(paint_row)select_rows.push_back({kPaintButton,kModelButton,1,{"ExtraPaint","ExtraPaintText","ExtraPaintLeftArrow","ExtraPaintRightArrow"}});
 select_rows_state.reset();
}
void select_rows_update(){
 if(select_rows.empty())return;
 const int car=integer("Frontend/VehicleSelect/CarModel");
 std::vector<bool> available{valid_car(car)&&paint_count(car)>=2};
 if(select_rows.size()>1)available.push_back(valid_car(car)&&colour_count(car)>=2);
 menu_dynamic::update(select_rows,available,select_rows_state,select_rows_host());
}
void __fastcall select_init(void* self,void*,void* argument){fn<Init>(kSelectInit)(self,argument);try{select_rows_entered();names={};look_sync(true);apply_all_variants(clamp_player(integer("Frontend/VehicleSelect/PlayerID")));variant_sync(self);}catch(...){log("APPEARANCE_MENU_INIT_FAILED");}}
// Left/Right on MODEL or PAINT changes only that row, never the carousel.
void __fastcall select_scroll(void* self,void*,int direction){
 try{void* buttons=fn<void*(__cdecl*)()>(0x525a80)();if(buttons){const int f=fn<int(__thiscall*)(void*)>(0x525800)(buttons);if(f==kModelButton||f==kPaintButton)return;}}catch(...){}
 fn<void(__thiscall*)(void*,int)>(kSelectScroll)(self,direction);
}
uintptr_t __fastcall select_tick(void* self,void*,uint32_t argument){
 try{select_rows_update();}catch(...){log("ROWS_UPDATE_FAILED");}
 const auto result=fn<Tick>(kSelectTick)(self,argument);
 try{look_sync(false);variant_sync(self);}catch(...){log("APPEARANCE_MENU_UPDATE_FAILED");}
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
  race_player[n]=h.player;race_car[n]=id;if(valid_car(id)){family(id);h.compound=tires[h.player][id].load();}
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
 try{
  // MODEL needs participant identity even when tyre customization is disabled.
  // Keep the original update and the existing bounded race cache; do not apply
  // a compound merely to refresh appearance ownership.
  if(options.enabled&&options.liveries&&!options.tires&&(!race.stamp||GetTickCount64()-race.stamp>500))refresh_race();
  apply_wheel(wheel);
 }catch(...){}
}

bool patch(uintptr_t va,const void* p,size_t size){DWORD previous=0,ignored=0;if(!VirtualProtect(reinterpret_cast<void*>(va),size,PAGE_EXECUTE_READWRITE,&previous))return false;std::memcpy(reinterpret_cast<void*>(va),p,size);const bool ok=FlushInstructionCache(GetCurrentProcess(),reinterpret_cast<void*>(va),size)!=FALSE;return VirtualProtect(reinterpret_cast<void*>(va),size,previous,&ignored)&&ok;}
bool call_is(uintptr_t site,uintptr_t target){std::array<unsigned char,5> b{};if(!read(site,b.data(),b.size())||b[0]!=0xe8)return false;int32_t offset=0;std::memcpy(&offset,b.data()+1,4);return site+5+offset==target;}
bool slot_is(uintptr_t slot,uintptr_t target){uintptr_t v=0;return read(slot,&v,4)&&v==target;}
std::vector<unsigned char> load(const char* name,size_t bytes){std::ifstream f(directory/name,std::ios::binary|std::ios::ate);if(!f||f.tellg()!=std::streamoff(bytes))return {};std::vector<unsigned char> p(bytes);f.seekg(0);f.read(reinterpret_cast<char*>(p.data()),std::streamsize(bytes));if(!f)return {};return p;}

bool configure_registry(){
 wchar_t env[32]{};const DWORD length=GetEnvironmentVariableW(L"MR_VEHICLE_REGISTRY_DESCRIPTOR",env,32);
 unsigned count=0;
 if(length){
  uint32_t location=0;mr_vehicle_registry::DescriptorV1 d{};
  if(length>=32||!extra_registry::address(env,location)||!read(location,&d,sizeof(d))||!extra_registry::descriptor(d))return false;
  std::array<uint32_t,3> counts{},tables{};
  if(!read(d.class_counts_va,counts.data(),sizeof(counts))||!read(d.class_tables_va,tables.data(),sizeof(tables)))return false;
  // Retired IDs (Vehicle Manager tombstones) stay in the registry but are offered by no class.
  if(uint64_t(counts[0])+counts[1]+counts[2]>d.record_count)return false;
  // Verify every mapping in bounded chunks, without allocating from untrusted counts.
  std::array<uint32_t,256> ids{};
  for(unsigned c=0;c<3;++c){
   if(!extra_registry::span(tables[c],counts[c],4))return false;
   for(unsigned first=0;first<counts[c];){
    const unsigned n=(counts[c]-first)<ids.size()?counts[c]-first:unsigned(ids.size());
    if(!read(uintptr_t(tables[c])+uintptr_t(first)*4,ids.data(),size_t(n)*4))return false;
    for(unsigned j=0;j<n;++j){
     if(ids[j]>=d.record_count)return false;
     uint32_t rc=0,rl=0;
     if(!read(uintptr_t(d.reverse_classes_va)+uintptr_t(ids[j])*4,&rc,4)||!read(uintptr_t(d.reverse_locals_va)+uintptr_t(ids[j])*4,&rl,4)||rc!=c||rl!=first+j)return false;
    }
    first+=n;
   }
  }
  count=d.record_count;registry_getter=d.registry_getter_va;
 }else{
  if(GetLastError()!=ERROR_ENVVAR_NOT_FOUND)return false;
  // Retail and accepted SDK33 keep this PUSH imm32 allocation operand.
  // Read the installed size rather than walking beyond a native registry.
  unsigned char instruction[5]{};uint32_t allocation=0;
  if(!read(0x45a3df,instruction,sizeof(instruction))||instruction[0]!=0x68)return false;
  std::memcpy(&allocation,instruction+1,4);
  if(!extra_registry::native_count(allocation,count))return false;
 }
 allocate_state(count);
 char line[128]{};std::snprintf(line,sizeof(line),"REGISTRY_READY count=%u source=%s",count,length?"MRVC_V1":"native-allocation");log(line);
 return true;
}

}

bool initialize() noexcept {try{
 wchar_t exe[32768]{};if(!GetModuleFileNameW(nullptr,exe,32768))return false;directory=fs::path(exe).parent_path();
 std::ifstream f(directory/"MRallyeExtraOptions.ini",std::ios::binary);std::string ini((std::istreambuf_iterator<char>(f)),{});
 const auto parsed=extra_options::parse_config(ini);if(parsed.accepted)options=parsed.config;else log("CONFIG absent/invalid; customization disabled; existing Randomizer settings unchanged");
 if(!options.enabled||(!options.tires&&!options.liveries)){log("CUSTOMIZATION_DISABLED no menu or wheel hooks installed");return true;}
 if(options.liveries){load_variants();load_vehicle_options();}
 if(!configure_registry()){log("REGISTRY_UNSUPPORTED: customization hooks disabled; no guessed CarID bounds");return false;}
 const auto state=(directory/"MRallyeExtraOptions.state.ini").wstring();
 for(unsigned p=0;p<kPlayers;++p)for(unsigned i=0;i<car_count;++i){wchar_t s[32]{};std::swprintf(s,32,p?L"Player2Car%u":L"Car%u",i);
  const auto model=GetPrivateProfileIntW(s,L"Model",-1,state.c_str()),paint=GetPrivateProfileIntW(s,L"Paint",-1,state.c_str());
  const auto colour=GetPrivateProfileIntW(s,L"Colour",-1,state.c_str()),tire=GetPrivateProfileIntW(s,L"Tire",0,state.c_str());
  paints[p][i]=model!=kUnset?unsigned(model):migrate_paint(int(i),paint);colours[p][i]=colour;tires[p][i]=tire<extra_options::kTireCount?tire:0;}
 pixels.resize(extra_package::binding_count);for(unsigned i=0;i<extra_package::binding_count;++i){const auto& b=extra_package::bindings[i];const size_t size=size_t(b.width)*b.height*4;pixels[i].original=load(b.original,size);pixels[i].derived=load(b.derived,size);}
 for(const auto& api:extra_package::apis){std::array<unsigned char,8> observed{};if(!read(api.va,observed.data(),observed.size())||observed!=api.bytes){log("API_LAYOUT_UNSUPPORTED: no Extra Options hooks installed");return false;}}
 struct Write{uintptr_t address;std::array<unsigned char,5> before,after;unsigned size;};std::vector<Write> writes;
 const auto slot=[&](uintptr_t at,uintptr_t original,void* target){if(!slot_is(at,original))throw 2;Write w{at,{},{},4};read(at,w.before.data(),4);const auto v=reinterpret_cast<uintptr_t>(target);std::memcpy(w.after.data(),&v,4);writes.push_back(w);};
 const auto call=[&](uintptr_t at,uintptr_t original,void* target){if(!call_is(at,original))throw 2;Write w{at,{},{},5};read(at,w.before.data(),5);w.after[0]=0xe8;const auto o=int32_t(reinterpret_cast<uintptr_t>(target)-at-5);std::memcpy(w.after.data()+1,&o,4);writes.push_back(w);};
 try{
  if(options.tires){
   slot(kGeneralInitSlot,kGeneralInit,reinterpret_cast<void*>(&general_init));slot(kGeneralTickSlot,kGeneralTick,reinterpret_cast<void*>(&general_tick));
   call(kGeneralCommandCall,kCommand,reinterpret_cast<void*>(&general_command));
  }
  if(options.tires||options.liveries)call(kWheelCall,kWheel,reinterpret_cast<void*>(&wheel_update));
  if(options.liveries){slot(kSelectInitSlot,kSelectInit,reinterpret_cast<void*>(&select_init));slot(kSelectTickSlot,kSelectTick,reinterpret_cast<void*>(&select_tick));
   call(kSelectScrollCall,kSelectScroll,reinterpret_cast<void*>(&select_scroll));
   slot(kDisplayTickSlot,kDisplayTick,reinterpret_cast<void*>(&display_tick));
   call(kIdentityQuickCall,kIdentityQuick,reinterpret_cast<void*>(&identity_quick));
   call(kIdentityCupCall,kIdentityCup,reinterpret_cast<void*>(&identity_cup));}
 }catch(int){log("HOOK_CONFLICT: Extra Options not installed; selected call/vtable mismatch");return false;}
 for(size_t i=0;i<writes.size();++i)if(!patch(writes[i].address,writes[i].after.data(),writes[i].size)){for(size_t j=0;j<=i;++j)patch(writes[j].address,writes[j].before.data(),writes[j].size);log("HOOK_INSTALL_FAILED rolled back");return false;}
 for(unsigned n=0;n<kRaceCars;++n){race_player[n]=-1;race_car[n]=-1;}
 installed=true;
 char line[200]{};std::snprintf(line,sizeof(line),"READY EXTRA-SET2 tyres=%d (GENERAL page, all human players, any mode) appearance=%d (Vehicle Select) hooks=%u",
                                options.tires,options.liveries,unsigned(writes.size()));log(line);return true;
 }catch(...){log("INITIALIZATION_FAILED");return false;}}

// Menu Builder provider "extra_options.model_source": the same PS2/PC choice as the MODEL row of
// Vehicle Select, for the car currently selected there (Frontend/VehicleSelect/{PlayerID,CarModel}).
bool appearance_available() noexcept {return installed&&options.enabled&&options.liveries;}
bool appearance_step(int direction,char* label,size_t size) noexcept {try{
 if(!appearance_available())return false;
 const int player=clamp_player(integer("Frontend/VehicleSelect/PlayerID")),car=integer("Frontend/VehicleSelect/CarModel");
 if(!valid_car(car))return false; // V-CAP2: per-car state is sized from the live registry
 family(car);
 const unsigned n=paint_count(car),old=model_value(player,car);
 if(n<2)return false;
 const unsigned v=direction<0?(old+n-1)%n:(old+1)%n;
 paints[player][car]=v;++generation;save(player,car);
 menu_player=player;menu_car=car;look_row={player,car,v,colour_value(player,car)};publish_look();
 if(label&&size)std::snprintf(label,size,"%s",paint_label(car,v));
 char line[180]{};std::snprintf(line,sizeof(line),"APPEARANCE_SELECTED player=%d CarID=%d family=%s choice=%s source=menu-builder",player+1,car,family(car),paint_label(car,v));log(line);
 return true;
 }catch(...){return false;}}

bool appearance_label(char* label,size_t size) noexcept {try{
 if(!appearance_available()||!label||!size)return false;
 const int player=clamp_player(integer("Frontend/VehicleSelect/PlayerID")),car=integer("Frontend/VehicleSelect/CarModel");
 if(!valid_car(car))return false;
 std::snprintf(label,size,"%s",paint_label(car,model_value(player,car)));return true;
 }catch(...){return false;}}

// Menu Builder "vehicle.model_label" (row caption; unavailable = the row has no choices) and "vehicle.paint".
bool model_row_available() noexcept {try{
 if(!appearance_available())return false;
 const int car=integer("Frontend/VehicleSelect/CarModel");return valid_car(car)&&paint_count(car)>=2;
 }catch(...){return false;}}
bool model_caption_label(char* label,size_t size) noexcept {try{
 if(!model_row_available()||!label||!size)return false;
 std::snprintf(label,size,"%s",model_caption(integer("Frontend/VehicleSelect/CarModel")));return true;
 }catch(...){return false;}}
bool paint_row_available() noexcept {try{
 if(!appearance_available())return false;
 const int car=integer("Frontend/VehicleSelect/CarModel");return valid_car(car)&&colour_count(car)>=2;
 }catch(...){return false;}}
bool paint_label_of(char* label,size_t size) noexcept {try{
 if(!paint_row_available()||!label||!size)return false;
 const int player=clamp_player(integer("Frontend/VehicleSelect/PlayerID")),car=integer("Frontend/VehicleSelect/CarModel");
 std::snprintf(label,size,"%s",colour_label(car,colour_value(player,car)));return true;
 }catch(...){return false;}}
bool paint_step(int direction,char* label,size_t size) noexcept {try{
 if(!paint_row_available())return false;
 const int player=clamp_player(integer("Frontend/VehicleSelect/PlayerID")),car=integer("Frontend/VehicleSelect/CarModel");
 const unsigned n=colour_count(car),old=colour_value(player,car),v=direction<0?(old+n-1)%n:(old+1)%n;
 colours[player][car]=v;menu_player=player;menu_car=car;look_row={player,car,model_value(player,car),v};
 look_changed(player,car,"paint",colour_label(car,v));
 if(label&&size)std::snprintf(label,size,"%s",colour_label(car,v));
 return true;
 }catch(...){return false;}}

// Menu Builder "vehicle.tyres": the TYRE TYPE compound of the Vehicle Select car (the GENERAL page reads the same
// per-car state when it opens: tyre_sync(true) in general_init).
bool tyre_available() noexcept {return installed&&options.enabled&&options.tires;}
bool tyre_label(char* label,size_t size) noexcept {try{
 if(!tyre_available()||!label||!size)return false;
 const int player=clamp_player(integer("Frontend/VehicleSelect/PlayerID")),car=integer("Frontend/VehicleSelect/CarModel");
 if(!valid_car(car))return false;
 const unsigned v=tires[player][car].load();
 std::snprintf(label,size,"%s",extra_options::kTireLabels[v<extra_options::kTireCount?v:0]);return true;
 }catch(...){return false;}}
bool tyre_step(int direction,char* label,size_t size) noexcept {try{
 if(!tyre_available())return false;
 const int player=clamp_player(integer("Frontend/VehicleSelect/PlayerID")),car=integer("Frontend/VehicleSelect/CarModel");
 if(!valid_car(car))return false;
 const unsigned n=extra_options::kTireCount,old=tires[player][car].load()%n;
 const unsigned v=direction<0?(old+n-1)%n:(old+1)%n;
 tires[player][car]=v;save(player,car);
 if(label&&size)std::snprintf(label,size,"%s",extra_options::kTireLabels[v]);
 char line[180]{};std::snprintf(line,sizeof(line),"TIRE_SELECTED player=%d CarID=%d compound=%s source=menu-builder",player+1,car,extra_options::kTireLabels[v]);log(line);
 return true;
 }catch(...){return false;}}

} // namespace extra_runtime

namespace {
using namespace extra_runtime;
// Phase 0 = frontend preview (menu car), phase 1 = race participant index.
bool selection(int participant,unsigned phase,int& player,int& id){
 if(phase==0){player=menu_player.load();id=menu_car.load();}
 else{if(participant<0||participant>=int(kRaceCars))return false;player=race_player[participant].load();id=race_car[participant].load();}
 return player>=0&&player<int(kPlayers)&&valid_car(id);
}
bool family_matches(int id,const char* family_name){
 const char* known=extra_runtime::family(id);
 if(known[0]&&!_stricmp(known,family_name))return true;
 // The renderer names a car by its model folder: a kit, DEMO or paint folder of this family is the same car.
 if(known[0]){
  const auto owner=extra_runtime::vopts.family_of(family_name);
  if(!owner.empty())return vehicle_options::same(owner,known);
  for(const auto& v:extra_runtime::variants)if(!_stricmp(v.folder.c_str(),family_name))return !_stricmp(v.base.c_str(),known);
  std::string kit;unsigned paint=0;
  if(vehicle_options::split_virtual(family_name,kit,paint))return !_stricmp(kit.c_str(),known);
  return false;
 }
 auto* v=vehicle(id);return v&&!_stricmp(v->family,family_name);
}
}

// The renderer asks this module; it never owns or rewrites customization state.
extern "C" unsigned WINAPI MRExtraVehicleRegistryAbi(){return 0x4d525601u;}
extern "C" unsigned WINAPI MRExtraOptionsAbi(){return 0x45583201u;}
// V2 identifies the selected appearance independently of renderer lighting.
// 0=no applicable selection, 1=PC bundle, 2=PS2 bundle, 3=PS2 with PC textures.
extern "C" unsigned WINAPI MRExtraVisualV2(const char* family_name,int participant,unsigned phase){
 if(!installed||!options.enabled||!options.liveries||!family_name)return 0;
 int player=0,id=-1;if(!selection(participant,phase,player,id)||!family_matches(id,family_name))return 0;
 return paint_kind(id,model_value(player,id));
}
// Family folder of any car folder name (kit, DEMO variant, "<kit>__p<n>"): the renderer keys its per-family profiles
// (lamps, brake, damage, HUD icons) by family. Returns the length written, 0 = unknown name (use it as is).
extern "C" unsigned WINAPI MRExtraFamilyV1(const char* name,char* out,unsigned size){
 if(!name||!out||!size)return 0;
 std::string f;
 try{
  f=extra_runtime::vopts.family_of(name);
  if(f.empty())for(const auto& v:extra_runtime::variants)if(!_stricmp(v.folder.c_str(),name)){f=v.base;break;}
  std::string kit;unsigned paint=0;
  if(f.empty()&&vehicle_options::split_virtual(name,kit,paint)){
   f=extra_runtime::vopts.family_of(kit);
   if(f.empty())for(const auto& v:extra_runtime::variants)if(!_stricmp(v.folder.c_str(),kit.c_str())){f=v.base;break;}
   if(f.empty())f=kit;
  }
 }catch(...){return 0;}
 if(f.empty()||f.size()+1>size)return 0;
 std::memcpy(out,f.c_str(),f.size()+1);return unsigned(f.size());
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
