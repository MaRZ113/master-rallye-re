#define WIN32_LEAN_AND_MEAN
#define NOMINMAX
#include <windows.h>
#include <cstdint>
#include <cstring>
#include <cstdlib>
#include <map>
#include <string>
#include <vector>
#include <iostream>
#include <stdexcept>
uintptr_t extra_test_resolve(uintptr_t);
#define EXTRA_OPTIONS_TEST 1
#include "../../src/native/rmod1/extra_options_runtime.cpp"

namespace {
std::map<std::string,uint32_t> names;
std::map<uint32_t,std::string> strings;
std::map<std::string,int> numbers;
std::map<std::string,float> reals;
std::map<std::string,std::string> texts;
std::map<void*,std::vector<std::string>> lists;
std::map<std::string,std::vector<std::string>> published;
int command_value=-1,wheel_calls=0;
uint32_t intern(const char* s){auto& id=names[s];if(!id){id=uint32_t(names.size());strings[id]=s;}return id;}
uint32_t __fastcall test_key(uint32_t* to,void*,const char* s){return *to=intern(s);}
void* __cdecl test_broker(){return reinterpret_cast<void*>(1);}
int __fastcall test_get(void*,void*,uint32_t* k){return numbers[strings[*k]];}
bool __fastcall test_bool(void*,void*,uint32_t* k){return numbers[strings[*k]]!=0;}
float __fastcall test_real(void*,void*,uint32_t* k){return reals[strings[*k]];}
void __fastcall test_int(void*,void*,uint32_t* k,int v){numbers[strings[*k]]=v;}
void __fastcall test_name(void*,void*,uint32_t* k,uint32_t* v){texts[strings[*k]]=strings[*v];}
void __fastcall test_ctor(uint32_t* to,void*,const char* s){const auto n=std::strlen(s)+1;auto* p=std::malloc(n);std::memcpy(p,s,n);*to=reinterpret_cast<uint32_t>(p);}
void* __cdecl test_new(size_t n){return std::calloc(1,n);}
void __cdecl test_delete(uintptr_t p){std::free(reinterpret_cast<void*>(p));}
void __fastcall test_push(void* v,void*,uintptr_t,unsigned,uint32_t* p){lists[v].push_back(reinterpret_cast<char*>(*p));}
void __fastcall test_list(void*,void*,uint32_t* k,void* v){published[strings[*k]]=lists[v];lists.erase(v);std::free(v);}
int __fastcall test_command(void*,void*,unsigned){return command_value;}
void __fastcall test_init(void*,void*,void*){}
uintptr_t __fastcall test_tick(void*,void*,uint32_t x){return x;}
void __fastcall test_wheel(void*,void*){++wheel_calls;}
int focused=2,scrolls=0;
void* __cdecl test_buttons(){return reinterpret_cast<void*>(3);}
int __fastcall test_focus(void*,void*){return focused;}
void __fastcall test_scroll(void*,void*,int){++scrolls;}
void* __cdecl test_object(){return reinterpret_cast<void*>(2);}
int __fastcall test_quick_car(void*,void*,int p){return numbers[p?"mock/quick/1":"mock/quick/0"];}
int __fastcall test_cup_car(void*,void*,int p){return numbers[p?"mock/cup/1":"mock/cup/0"];}
// Native vehicle registry: 0x34-byte rows, folder Name at +0x24.
unsigned char registry[0x24+513*0x34]{};
void* __cdecl test_registry(){return registry;}
struct Entry {uint32_t a,b;uintptr_t object;};
std::map<std::string,Entry> controllers;
void* __fastcall test_find(void*,void*,uint32_t* parent,uint32_t* child){
 if(strings[*child]!="ControllerCarBrokerAccess")return nullptr;
 auto it=controllers.find(strings[*parent]);return it==controllers.end()?nullptr:&it->second;
}
void check(bool ok,const char* s){if(!ok)throw std::runtime_error(s);}
// Menu-car display tick: records the registry folder of the shown CarID while the original runs.
std::string display_loaded;int display_calls=0;
void __fastcall test_display(void* self,void*,void*){++display_calls;int id=0;std::memcpy(&id,static_cast<char*>(self)+0xc,4);
 const int want=numbers[strings[*reinterpret_cast<uint32_t*>(static_cast<char*>(self)+0x10)]];
 if(id!=want){std::memcpy(static_cast<char*>(self)+0xc,&want,4);uintptr_t text=0;std::memcpy(&text,registry+0x24+want*0x34,4);display_loaded=reinterpret_cast<const char*>(text);}}
// Race participant wrapper setters (CarType +0x64, WheelType +0x6C).
std::map<int,std::string> car_type,wheel_type;
void __fastcall test_strdup(uint32_t* to,void*,const char* s){std::free(reinterpret_cast<void*>(*to));const auto n=std::strlen(s)+1;auto* p=std::malloc(n);std::memcpy(p,s,n);*to=reinterpret_cast<uint32_t>(p);}
void __fastcall test_car_type(void*,void*,int car,uint32_t* s){car_type[car]=reinterpret_cast<const char*>(*s);}
void __fastcall test_wheel_type(void*,void*,int car,uint32_t* s){wheel_type[car]=reinterpret_cast<const char*>(*s);}
}
uintptr_t extra_test_resolve(uintptr_t p){
 switch(p){
 case 0x4d0580:return reinterpret_cast<uintptr_t>(&test_key);
 case 0x4d8ec0:return reinterpret_cast<uintptr_t>(&test_broker);
 case 0x4d6760:return reinterpret_cast<uintptr_t>(&test_get);
 case 0x4d6520:return reinterpret_cast<uintptr_t>(&test_bool);
 case 0x4d6650:return reinterpret_cast<uintptr_t>(&test_real);
 case 0x4d8000:return reinterpret_cast<uintptr_t>(&test_int);
 case 0x4d85f0:return reinterpret_cast<uintptr_t>(&test_name);
 case 0x4d8880:return reinterpret_cast<uintptr_t>(&test_list);
 case 0x4d11d0:return reinterpret_cast<uintptr_t>(&test_ctor);
 case 0x407b30:return reinterpret_cast<uintptr_t>(&test_push);
 case 0x5c1cb4:return reinterpret_cast<uintptr_t>(&test_new);
 case 0x5b4c00:return reinterpret_cast<uintptr_t>(&test_delete);
 case 0x4d6fb0:return reinterpret_cast<uintptr_t>(&test_find);
 case 0x45a3c0:return reinterpret_cast<uintptr_t>(&test_registry);
 case 0x4ada50:case 0x4b0af0:return reinterpret_cast<uintptr_t>(&test_object);
 case 0x4ac660:return reinterpret_cast<uintptr_t>(&test_quick_car);
 case 0x4b0630:return reinterpret_cast<uintptr_t>(&test_cup_car);
 case 0x45d930:return reinterpret_cast<uintptr_t>(&test_command);
 case 0x482f30:case 0x480b60:return reinterpret_cast<uintptr_t>(&test_init);
 case 0x4830c0:case 0x481340:return reinterpret_cast<uintptr_t>(&test_tick);
 case 0x440fe0:return reinterpret_cast<uintptr_t>(&test_wheel);
 case 0x525a80:return reinterpret_cast<uintptr_t>(&test_buttons);
 case 0x525800:return reinterpret_cast<uintptr_t>(&test_focus);
 case 0x481f50:return reinterpret_cast<uintptr_t>(&test_scroll);
 case 0x44c4c0:return reinterpret_cast<uintptr_t>(&test_display);
 case 0x4d1990:return reinterpret_cast<uintptr_t>(&test_strdup);
 case 0x4aca40:return reinterpret_cast<uintptr_t>(&test_car_type);
 case 0x4acb40:return reinterpret_cast<uintptr_t>(&test_wheel_type);
 default:throw std::runtime_error("unmapped API");
 }
}

// Wheel object: +0x18 car, car+0x14 controller sub-object, +0x170/+0x174 surface record vector.
struct FakeWheel {
 std::vector<unsigned char> wheel=std::vector<unsigned char>(0x180),car=std::vector<unsigned char>(0x20);
 std::vector<float> records;
 FakeWheel(uintptr_t controller,const std::vector<float>& r):records(r){
  auto c=reinterpret_cast<uintptr_t>(car.data());std::memcpy(wheel.data()+0x18,&c,4);std::memcpy(car.data()+0x14,&controller,4);
  auto b=reinterpret_cast<uintptr_t>(records.data()),e=b+records.size()*4;std::memcpy(wheel.data()+0x170,&b,4);std::memcpy(wheel.data()+0x174,&e,4);
 }
 void* get(){return wheel.data();}
};

int main(int argc,char** argv){try{
 if(argc!=2)return 2;
 using namespace extra_runtime;
 directory=argv[1];
 uint32_t parsed=0;
 check(extra_registry::address(L"0x10000000",parsed)&&parsed==0x10000000,"descriptor hex address");
 check(!extra_registry::address(L"4294967296",parsed)&&!extra_registry::address(L"-1",parsed)&&!extra_registry::address(L"0x",parsed),"descriptor address rejects overflow/sign/empty");
 check(extra_registry::native_count(4+33*52+39*44,parsed)&&parsed==33,"SDK33 allocation count");
 check(!extra_registry::native_count(4+33*52+39*44+1,parsed),"non-record allocation rejected");
 for(unsigned count:{33u,128u,129u,255u,256u,257u,513u}){
  std::vector<uint32_t> ids(count),classes(count,0),locals(count);
  for(unsigned i=0;i<count;++i)ids[i]=locals[i]=i;
  uint32_t counts[]={count,0,0};uint32_t tables[]={uint32_t(reinterpret_cast<uintptr_t>(ids.data())),uint32_t(reinterpret_cast<uintptr_t>(ids.data())),uint32_t(reinterpret_cast<uintptr_t>(ids.data()))};
  mr_vehicle_registry::DescriptorV1 d{{'M','R','V','C'},1,44,count,52,3,0x45a3c0,
   uint32_t(reinterpret_cast<uintptr_t>(counts)),uint32_t(reinterpret_cast<uintptr_t>(tables)),
   uint32_t(reinterpret_cast<uintptr_t>(classes.data())),uint32_t(reinterpret_cast<uintptr_t>(locals.data()))};
  wchar_t location[32]{};std::swprintf(location,32,L"0x%08x",unsigned(reinterpret_cast<uintptr_t>(&d)));
  SetEnvironmentVariableW(L"MR_VEHICLE_REGISTRY_DESCRIPTOR",location);
  check(configure_registry()&&car_count==count,"capacity descriptor including numeric boundaries");
  d.record_stride=48;check(!configure_registry(),"unsupported stride rejected");d.record_stride=52;
  locals[0]=1;check(!configure_registry(),"inconsistent inverse mapping rejected");
 }
 SetEnvironmentVariableW(L"MR_VEHICLE_REGISTRY_DESCRIPTOR",L"invalid");check(!configure_registry(),"malformed present descriptor rejected");
 SetEnvironmentVariableW(L"MR_VEHICLE_REGISTRY_DESCRIPTOR",nullptr);
 allocate_state(513);
 directory=argv[1];options.enabled=options.tires=options.liveries=true;installed=true;
 for(unsigned n=0;n<kRaceCars;++n){race_player[n]=-1;race_car[n]=-1;}
 for(auto [id,name]:{std::pair{2,"Tata"},{15,"Simmbugghini"},{18,"Megane"},{21,"SeatBuggy"}}){
  const auto text=reinterpret_cast<uintptr_t>(name);std::memcpy(registry+0x24+id*0x34,&text,4);
  static const char display[]="DISPLAY NAME";const auto other=reinterpret_cast<uintptr_t>(display);std::memcpy(registry+0x0c+id*0x34,&other,4);}

 // GENERAL page: Quick Race and championship resolve the car like the native setup loader.
 numbers={{"Frontend/InQuickRaceMode",1},{"Frontend/CarSetup/PlayerID",0},{"mock/quick/0",21},{"mock/cup/0",7},{"mock/quick/1",15}};
 general_init(nullptr,nullptr,nullptr);
 check(published["Frontend/ExtraOptions/TireList"].size()==6,"six tyre labels");
 check(texts["Frontend/ExtraOptions/TireText"]=="STOCK","uppercase stock label");
 check(numbers["Frontend/ExtraOptions/TireLeftArrow"]==0&&numbers["Frontend/ExtraOptions/TireRightArrow"]==1,"integer arrow states");
 numbers["Frontend/ExtraOptions/Tire"]=3;general_tick(nullptr,nullptr,0);
 check(tires[0][21]==3&&texts["Frontend/ExtraOptions/TireText"]=="GRAVEL","choice commits immediately per player and CarID");
 numbers["Frontend/InQuickRaceMode"]=0;general_tick(nullptr,nullptr,0);
 check(tyre_row.car==7&&numbers["Frontend/ExtraOptions/Tire"]==0,"championship setup uses progress car");
 numbers["Frontend/ExtraOptions/Tire"]=5;general_tick(nullptr,nullptr,0);check(tires[0][7]==5&&tires[0][21]==3,"independent cars");
 numbers["Frontend/InQuickRaceMode"]=1;numbers["Frontend/CarSetup/PlayerID"]=1;general_tick(nullptr,nullptr,0);
 check(tyre_row.player==1&&tyre_row.car==15&&tires[1][15]==0,"second player has own choices");
 command_value=6;check(general_command(nullptr,nullptr,1)==1,"confirm on TYRE TYPE behaves like a native row");
 command_value=4;check(general_command(nullptr,nullptr,1)==4,"native rows unchanged");
 command_value=-3;check(general_command(nullptr,nullptr,1)==-3,"Back unchanged");

 // Race: human wheels of any mode get the compound; AI and foreign records stay exact.
 for(unsigned s=0;s<extra_options::kSurfaceCount;++s)for(unsigned f=0;f<extra_options::kTyreFields;++f){
  char path[64];std::snprintf(path,sizeof(path),"Vehicles/Tyres/%s0/%s",extra_options::kSurfaces[s],extra_options::kTyreFieldNames[f]);reals[path]=1.0f+0.25f*float(s)+0.01f*float(f);}
 std::vector<float> stock;for(unsigned r=0;r<5;++r)for(unsigned f=0;f<extra_options::kTyreFields;++f)stock.push_back(1.0f+0.25f*float(r)+0.01f*float(f));
 std::vector<unsigned char> human_controller(0x100),ai_controller(0x100);
 controllers["Controller/Car0"]={0,0,reinterpret_cast<uintptr_t>(human_controller.data())};
 controllers["Controller/Car1"]={0,0,reinterpret_cast<uintptr_t>(ai_controller.data())};
 numbers.insert({{"Race/NumCars",2},{"Race/Car0/PlayerType",1},{"Race/Car0/CarID",21},{"Race/Car1/PlayerType",2},{"Race/Car1/CarID",18},{"Race/AttractMode",0}});
 FakeWheel human(reinterpret_cast<uintptr_t>(human_controller.data())+0x18,stock),ai(reinterpret_cast<uintptr_t>(ai_controller.data())+0x18,stock);
 race.stamp=0;wheel_update(human.get(),nullptr);wheel_update(ai.get(),nullptr);
 check(wheel_calls==2,"original wheel update always runs first");
 check(human.records[2*12]==stock[2*12]*extra_options::grip_scale(extra_options::Tire::Gravel,2)&&human.records[0]==stock[0]*extra_options::grip_scale(extra_options::Tire::Gravel,0)&&human.records[0]<stock[0],"gravel compound scales human grip per surface");
 check(human.records[2*12+1]==stock[2*12+1],"non-grip fields exact");
 check(ai.records==stock,"AI wheel untouched");
 auto once=human.records;wheel_update(human.get(),nullptr);check(human.records==once,"idempotent every tick");
 check(race_player[0]==0&&race_car[0]==21&&race_car[1]==-1,"race identity published for renderer");
 FakeWheel attract(reinterpret_cast<uintptr_t>(human_controller.data())+0x18,stock);numbers["Race/AttractMode"]=1;race.stamp=0;
 wheel_update(attract.get(),nullptr);check(attract.records==stock,"attract untouched");numbers["Race/AttractMode"]=0;
 tires[0][21]=0;race.stamp=0;FakeWheel plain(reinterpret_cast<uintptr_t>(human_controller.data())+0x18,stock);
 wheel_update(plain.get(),nullptr);check(plain.records==stock,"Stock exact passthrough");tires[0][21]=3;
 options.tires=false;race.stamp=0;FakeWheel off(reinterpret_cast<uintptr_t>(human_controller.data())+0x18,stock);
 race_player[0]=-1;race_car[0]=-1;paints[0][21]=1;
 wheel_update(off.get(),nullptr);check(off.records==stock,"independent tyre toggle");
 check(MRExtraVisualV2("SeatBuggy",0,1)==1,"appearance race identity refreshes with Tires=0");
 check(MRExtraVisualV2("Megane",1,1)==0,"Tires=0 keeps AI appearance isolated");
 options.tires=true;paints[0][21]=0;

 // Vehicle Select rows: egg lookup is replaced (no native egg manager in the test).
 std::map<std::string,std::vector<unsigned char>> en2d;
 for(const char* e:{"ExtraModel","ExtraModelText","ExtraModelLeftArrow","ExtraModelRightArrow","ExtraPaint","ExtraPaintText","ExtraPaintLeftArrow","ExtraPaintRightArrow"}){
  en2d[e].assign(0x60,0);const float x=36.0f;std::memcpy(en2d[e].data()+0x54,&x,4);}
 row_egg=[&](const std::string& n)->uintptr_t{auto it=en2d.find(n);return it==en2d.end()?0:reinterpret_cast<uintptr_t>(it->second.data());};
 auto egg_x=[&](const char* n){float x=0;std::memcpy(&x,en2d[n].data()+0x54,4);return x;};

 // Vehicle Select: generic PS2/PC for every car, per-car presets where authored; immediate.
 numbers["Frontend/VehicleSelect/PlayerID"]=0;numbers["Frontend/VehicleSelect/CarModel"]=15;
 select_init(nullptr,nullptr,nullptr);
 check(published["Frontend/ExtraOptions/PaintList"]==std::vector<std::string>{"PS2","PC"},"generic appearance pair");
 check(MRExtraVisualV2("Simmbugghini",-1,0)==2,"default PS2 bundle");
 const unsigned before=generation;numbers["Frontend/ExtraOptions/Paint"]=1;select_tick(nullptr,nullptr,0);
 check(paints[0][15]==1&&generation==before+1,"immediate apply bumps renderer revision");
 check(MRExtraVisualV2("simmbugghini",-1,0)==1&&MRExtraVisualV1("Simmbugghini",-1,0)==1,"PC bundle in preview, case-insensitive");
 check(MRExtraVisualV2("Tata",-1,0)==0,"other family in preview untouched");
 numbers["Frontend/VehicleSelect/CarModel"]=21;select_tick(nullptr,nullptr,0);
 check(published["Frontend/ExtraOptions/PaintList"]==std::vector<std::string>{"PS2","PC"},"SeatBuggy reduced to PS2/PC");
 paints[0][21]=1;check(MRExtraVisualV2("SeatBuggy",0,1)==1,"race human PC bundle");
 check(MRExtraVisualV2("Megane",1,1)==0,"race AI unchanged");
 paints[0][21]=0;check(MRExtraVisualV2("SeatBuggy",0,1)==2,"race human PS2");
 check(MRExtraTextureV1("SeatBuggy",0,1,1,registry,registry,4,-1,0)==FALSE,"texture-transfer variant retired");
 check(migrate_paint(21,2)==2&&migrate_paint(21,1)==0&&migrate_paint(2,1)==1&&migrate_paint(15,5)==0&&migrate_paint(2,kUnset)==kUnset,"EXTRA-SET1 presets migrate to PS2/PC; stored DEMO kept (checked at use); unset stays unset");
 focused=3;select_scroll(nullptr,nullptr,1);check(scrolls==0,"Left/Right on MODEL keeps the carousel");
 focused=2;select_scroll(nullptr,nullptr,1);check(scrolls==1,"carousel still scrolls from its own row");
 options.liveries=false;check(MRExtraVisualV2("SeatBuggy",0,1)==0,"independent appearance toggle");options.liveries=true;
 for(int id:{127,128,254,255,256,512}){
  static const char name[]="CapacityBoundary";const auto ptr=reinterpret_cast<uintptr_t>(name);std::memcpy(registry+0x24+id*0x34,&ptr,4);
  numbers["Frontend/VehicleSelect/CarModel"]=id;select_tick(nullptr,nullptr,0);
  numbers["Frontend/ExtraOptions/Paint"]=1;select_tick(nullptr,nullptr,0);
  check(MRExtraVisualV2(name,-1,0)==1,"high physical ID PC appearance");
  tires[0][id]=3;numbers["Race/Car0/CarID"]=id;race.stamp=0;
  FakeWheel high(reinterpret_cast<uintptr_t>(human_controller.data())+0x18,stock);wheel_update(high.get(),nullptr);
  check(high.records[2*12]==stock[2*12]*extra_options::grip_scale(extra_options::Tire::Gravel,2),"high physical ID tyre wheel");
  tires[1][id]=2;save(1,id);wchar_t section[32]{};std::swprintf(section,32,L"Player2Car%u",unsigned(id));
  const auto path=(directory/"MRallyeExtraOptions.state.ini").wstring();
  check(GetPrivateProfileIntW(section,L"Tire",0,path.c_str())==2,"high physical ID INI persistence");
 }
 check(!valid_car(-1)&&!valid_car(513),"capacity bounds");

 // ---- vehicle-options.ini (revision 2) -------------------------------------------------------------------------
 {
  vehicle_options::Table bad;std::string error;
  check(!vehicle_options::parse("[Family:X]\nmodel=A,B\n",bad,error),"kits need one folder per choice");
  check(!vehicle_options::parse("[Family:X]\nmodel=A,B\nmodel_folders=X__p1,Y\n",bad,error),"virtual separator refused in folders");
  check(!vehicle_options::parse("[Family:X]\nmodel=A,B\nmodel_folders=Q,R\n[Family:Y]\nmodel=C,D\nmodel_folders=Q,S\n",bad,error),"kit folder of two families refused");
  check(!vehicle_options::parse("[Family:X]\nwhatever=1\n",bad,error),"unknown key refused");
  std::string kit;unsigned n=0;
  check(vehicle_options::split_virtual("Calmini__p3",kit,n)&&kit=="Calmini"&&n==3,"virtual name split");
  check(!vehicle_options::split_virtual("Calmini__p0",kit,n)&&!vehicle_options::split_virtual("Calmini__p03",kit,n)&&!vehicle_options::split_virtual("__p1",kit,n),"invalid virtual names");
 }
 const char* ini="; test\r\n[Family:CalminiFrontier]\r\nmodel_label = KIT\r\nmodel = BARE,STOCK,FULL ; three kits\r\n"
  "model_folders = CalminiFrontier_bare,CalminiFrontier,CalminiFrontier_full\r\nmodel_default = 1\r\npaint = GREY,RED,BLACK\r\n"
  "[Family:Evo2Plain]\r\nmodel =\r\n[Family:Evo2Painted]\r\nmodel =\r\npaint = SILVER,RED\r\n";
 {std::string error;check(vehicle_options::parse(ini,vopts,error),error.c_str());}
 {std::vector<std::string> c;
  check(vopts.candidates("DataGx/Vehicles/CalminiFrontier_full__p2/body.dxt",c)&&c.size()==2&&c[0]=="datagx/vehiclepaints/calminifrontier/2/body.dxt"&&c[1]=="datagx/vehicles/calminifrontier_full/body.dxt","paint file first, then the kit");
  check(!vopts.candidates("DataGx/Vehicles/CalminiFrontier_full__p3/body.dxt",c),"paint index past the family list refused");
  check(!vopts.candidates("DataGx/Vehicles/Pajero__p1/car.dx",c),"undeclared family never rewritten");
  check(vopts.family_of("CalminiFrontier_bare__p1")=="CalminiFrontier"&&vopts.family_of("CalminiFrontier_full")=="CalminiFrontier","family of kit/paint names");}
 static const char calmini[]="CalminiFrontier",plain_family[]="Evo2Plain",heritage[]="HeritageTrooper",painted[]="Evo2Painted";
 for(auto [id,name]:{std::pair<int,const char*>{30,calmini},{31,plain_family},{32,heritage},{33,painted}}){const auto ptr=reinterpret_cast<uintptr_t>(name);std::memcpy(registry+0x24+id*0x34,&ptr,4);}
 for(int id:{30,31,32,33}){paints[0][id]=kUnset;colours[0][id]=kUnset;paints[1][id]=kUnset;colours[1][id]=kUnset;}
 numbers["Frontend/VehicleSelect/PlayerID"]=0;numbers["Frontend/VehicleSelect/CarModel"]=30;
 select_init(nullptr,nullptr,nullptr);
 check(published["Frontend/ExtraOptions/PaintList"]==std::vector<std::string>{"BARE","STOCK","FULL"},"kit choices replace PS2/PC");
 check(texts["Frontend/ExtraOptions/ModelLabel"]=="KIT"&&texts["Frontend/ExtraOptions/PaintText"]=="STOCK","caption KIT, default kit STOCK");
 check(published["Frontend/ExtraOptions/ColourList"]==std::vector<std::string>{"GREY","RED","BLACK"}&&texts["Frontend/ExtraOptions/ColourText"]=="GREY","paint row");
 check(std::string(participant_folder(0,30))=="CalminiFrontier","default kit + paint 0 = family folder");
 numbers["Frontend/ExtraOptions/Paint"]=2;numbers["Frontend/ExtraOptions/Colour"]=1;select_tick(nullptr,nullptr,0);
 check(std::string(participant_folder(0,30))=="CalminiFrontier_full__p1","kit FULL + paint RED");
 check(std::string(participant_folder(1,30))=="CalminiFrontier","second player keeps defaults");
 check(std::string(participant_folder(-1,30))=="CalminiFrontier","AI: family default");
 // Menu car: the registry row carries the kit/paint folder only while the display tick runs.
 {std::vector<unsigned char> display(0x20,0);const int none=-1;std::memcpy(display.data()+0xc,&none,4);
  const uint32_t k=intern("Frontend/VehicleSelect/CarModel");std::memcpy(display.data()+0x10,&k,4);
  display_tick(display.data(),nullptr,nullptr);
  uintptr_t row_now=0;std::memcpy(&row_now,registry+0x24+30*0x34,4);
  check(display_loaded=="CalminiFrontier_full__p1"&&row_now==reinterpret_cast<uintptr_t>(calmini),"menu car built from the virtual folder, registry restored");
  display_loaded.clear();display_tick(display.data(),nullptr,nullptr);check(display_loaded.empty(),"no rebuild without a change");
  numbers["Frontend/ExtraOptions/Colour"]=2;select_tick(nullptr,nullptr,0);display_tick(display.data(),nullptr,nullptr);
  check(display_loaded=="CalminiFrontier_full__p2","paint change rebuilds the menu car at once");
  numbers["Frontend/VehicleSelect/CarModel"]=2;select_tick(nullptr,nullptr,0);display_loaded.clear();display_tick(display.data(),nullptr,nullptr);
  check(display_loaded=="Tata","other cars untouched");numbers["Frontend/VehicleSelect/CarModel"]=30;select_tick(nullptr,nullptr,0);}
 // Race: each participant gets its own folder; physics/registry untouched.
 numbers["Race/AttractMode"]=0;
 numbers["Race/Car0/PlayerType"]=1;numbers["Race/Car0/CarID"]=30;numbers["Race/Car1/PlayerType"]=1;numbers["Race/Car1/CarID"]=30;
 numbers["Race/Car2/PlayerType"]=2;numbers["Race/Car2/CarID"]=30;numbers["Race/Car3/PlayerType"]=2;numbers["Race/Car3/CarID"]=2;
 paints[1][30]=0;colours[1][30]=0;
 for(int c=0;c<4;++c)race_identity(c);
 check(car_type[0]=="CalminiFrontier_full__p2"&&wheel_type[0]==car_type[0],"player 1 own kit and paint");
 check(car_type[1]=="CalminiFrontier_bare","player 2 same car, own kit");
 check(!car_type.count(2)&&!car_type.count(3),"AI default and retail cars keep the native identity");
 numbers["Race/AttractMode"]=1;car_type.clear();race_identity(0);check(car_type.empty(),"attract untouched");numbers["Race/AttractMode"]=0;
 // Rows: Evo2Plain declares no model, no paints -> both rows hidden; focus walks over them.
 numbers["Frontend/VehicleSelect/CarModel"]=31;numbers["UI/Active"]=2;select_tick(nullptr,nullptr,0);
 check(egg_x("ExtraModel")==menu_dynamic::kParkedX&&egg_x("ExtraPaintRightArrow")==menu_dynamic::kParkedX,"rows without choices parked");
 numbers["UI/Active"]=3;select_tick(nullptr,nullptr,0);check(numbers["UI/Active"]==1,"Down from SelectCar skips MODEL and PAINT to Class");
 numbers["UI/Active"]=4;select_tick(nullptr,nullptr,0);check(numbers["UI/Active"]==2,"Up from Class skips PAINT and MODEL to SelectCar");
 check(published["Frontend/ExtraOptions/PaintList"]==std::vector<std::string>{"-"}&&numbers["Frontend/ExtraOptions/PaintRightArrow"]==0,"no fake choices");
 numbers["Frontend/VehicleSelect/CarModel"]=30;select_tick(nullptr,nullptr,0);
 check(egg_x("ExtraModel")==36.0f&&egg_x("ExtraPaintText")==36.0f,"rows come back for a car with choices");
 // Added car without a PS2 bundle or DEMO: nothing to switch, hidden; retail cars keep PS2/PC.
 numbers["Frontend/VehicleSelect/CarModel"]=32;select_tick(nullptr,nullptr,0);select_tick(nullptr,nullptr,0);
 check(published["Frontend/ExtraOptions/PaintList"]==std::vector<std::string>{"-"}&&egg_x("ExtraModel")==menu_dynamic::kParkedX,"added car: MODEL row hidden");
 numbers["Frontend/VehicleSelect/CarModel"]=2;select_tick(nullptr,nullptr,0);select_tick(nullptr,nullptr,0);
 check(published["Frontend/ExtraOptions/PaintList"]==std::vector<std::string>{"PS2","PC"}&&egg_x("ExtraModel")==36.0f&&egg_x("ExtraPaint")==menu_dynamic::kParkedX,"retail: MODEL shown, PAINT hidden");
 focused=4;select_scroll(nullptr,nullptr,1);check(scrolls==1,"Left/Right on PAINT keeps the carousel");focused=2;
 // Owner run 2026-11-13 (4Runner: paints, no model): the PAINT egg did not exist yet on screen entry.
 {auto saved=en2d["ExtraPaint"];en2d.erase("ExtraPaint");numbers["Frontend/VehicleSelect/CarModel"]=33;
  select_init(nullptr,nullptr,nullptr);{const float x=36.0f;std::memcpy(saved.data()+0x54,&x,4);}en2d["ExtraPaint"]=saved;   // scene rebuilt the egg at its authored x
  numbers["UI/Active"]=2;select_tick(nullptr,nullptr,0);
  check(egg_x("ExtraModel")==menu_dynamic::kParkedX&&egg_x("ExtraPaint")!=menu_dynamic::kParkedX,"paint-only car: MODEL hidden, PAINT shown");
  numbers["UI/Active"]=3;select_tick(nullptr,nullptr,0);check(numbers["UI/Active"]==4,"Down from SelectCar skips MODEL to PAINT (late PAINT egg)");
  numbers["UI/Active"]=3;select_tick(nullptr,nullptr,0);check(numbers["UI/Active"]==2,"Up from PAINT skips MODEL to SelectCar");
  numbers["UI/Active"]=2;numbers["Frontend/VehicleSelect/CarModel"]=2;select_tick(nullptr,nullptr,0);select_tick(nullptr,nullptr,0);}
 {char out[64]{};check(MRExtraFamilyV1("CalminiFrontier_bare__p2",out,64)&&std::string(out)=="CalminiFrontier","family export for kit/paint folders");
  check(!MRExtraFamilyV1("Pajero",out,64),"unknown names stay as they are");}
 check(model_row_available()&&!paint_row_available(),"Menu Builder rows: retail car has MODEL, no PAINT");
 numbers["Frontend/VehicleSelect/CarModel"]=30;select_tick(nullptr,nullptr,0);
 check(MRExtraVisualV2("CalminiFrontier_full__p2",-1,0)==1,"renderer query with a virtual folder answers for the family (PC)");
 {char label[32]{};check(paint_step(1,label,sizeof(label))&&std::string(label)=="GREY"&&colours[0][30]==0,"vehicle.paint steps and wraps");}
 options.enabled=false;check(MRExtraVisualV1("SeatBuggy",0,1)==0,"customization off passthrough");
 std::cout<<"EXTRA_NATIVE_PASS GENERAL tyre row (Quick Race + championship, two players); human-only compound wheels; Vehicle Select PS2/PC immediate for every car, carousel locked on MODEL/PAINT; kits/paints per player and participant; dynamic rows; renderer V1/V2 contract\n";return 0;
 }catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
