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
const char* __fastcall test_text(uint32_t* k,void*){return strings[*k].c_str();}
void __fastcall test_ctor(uint32_t* to,void*,const char* s){const auto n=std::strlen(s)+1;auto* p=std::malloc(n);std::memcpy(p,s,n);*to=reinterpret_cast<uint32_t>(p);}
void* __cdecl test_new(size_t n){return std::calloc(1,n);}
void __cdecl test_delete(uintptr_t p){std::free(reinterpret_cast<void*>(p));}
void __fastcall test_push(void* v,void*,uintptr_t,unsigned,uint32_t* p){lists[v].push_back(reinterpret_cast<char*>(*p));}
void __fastcall test_list(void*,void*,uint32_t* k,void* v){published[strings[*k]]=lists[v];lists.erase(v);std::free(v);}
int __fastcall test_command(void*,void*,unsigned){return command_value;}
void __fastcall test_init(void*,void*,void*){}
uintptr_t __fastcall test_tick(void*,void*,uint32_t x){return x;}
void __fastcall test_wheel(void*,void*){++wheel_calls;}
void* __cdecl test_object(){return reinterpret_cast<void*>(2);}
int __fastcall test_quick_car(void*,void*,int p){return numbers[p?"mock/quick/1":"mock/quick/0"];}
int __fastcall test_cup_car(void*,void*,int p){return numbers[p?"mock/cup/1":"mock/cup/0"];}
// Native vehicle registry: 0x34-byte rows, folder Name at +0x24.
unsigned char registry[0x24+64*0x34]{};
void* __cdecl test_registry(){return registry;}
struct Entry {uint32_t a,b;uintptr_t object;};
std::map<std::string,Entry> controllers;
void* __fastcall test_find(void*,void*,uint32_t* parent,uint32_t* child){
 if(strings[*child]!="ControllerCarBrokerAccess")return nullptr;
 auto it=controllers.find(strings[*parent]);return it==controllers.end()?nullptr:&it->second;
}
void check(bool ok,const char* s){if(!ok)throw std::runtime_error(s);}
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
 case 0x4d0570:return reinterpret_cast<uintptr_t>(&test_text);
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
 directory=argv[1];options.enabled=options.tires=options.liveries=true;installed=true;
 for(unsigned n=0;n<kRaceCars;++n){race_player[n]=-1;race_car[n]=-1;}
 for(auto [id,name]:{std::pair{2,"Tata"},{15,"Simmbugghini"},{18,"Megane"},{21,"SeatBuggy"}}){const uint32_t k=intern(name);std::memcpy(registry+0x24+id*0x34,&k,4);}

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
 wheel_update(off.get(),nullptr);check(off.records==stock,"independent tyre toggle");options.tires=true;

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
 check(published["Frontend/ExtraOptions/PaintList"].size()==3,"authored SeatBuggy presets");
 paints[0][21]=1;check(MRExtraVisualV2("SeatBuggy",0,1)==3,"race human: PS2 geometry with PC textures");
 check(MRExtraVisualV2("Megane",1,1)==0,"race AI unchanged");
 paints[0][21]=0;check(MRExtraVisualV2("SeatBuggy",0,1)==2,"race human PS2");paints[0][21]=1;
 options.liveries=false;check(MRExtraVisualV2("SeatBuggy",0,1)==0,"independent appearance toggle");options.liveries=true;
 pixels.resize(extra_package::binding_count);
 const auto& binding=extra_package::bindings[0];const unsigned size=binding.width*binding.height*4;
 std::vector<unsigned char> source(size,33),output(size,77);for(unsigned i=3;i<size;i+=4)source[i]=255;
 pixels[0].original=source;pixels[0].derived=source;pixels[0].derived[0]=64;
 numbers["Frontend/VehicleSelect/CarModel"]=21;select_tick(nullptr,nullptr,0);
 check(MRExtraTextureV1("SeatBuggy",binding.index,binding.width,binding.height,source.data(),output.data(),size,-1,0)!=FALSE,"qualified texture-only upload");
 for(unsigned i=3;i<size;i+=4)check(output[i]==source[i],"texture alpha remains exact");
 check(!MRExtraTextureV1("SeatBuggy",binding.index,binding.width,binding.height,source.data(),output.data(),size,1,1),"AI texture upload isolated");
 source[1]^=1;check(!MRExtraTextureV1("SeatBuggy",binding.index,binding.width,binding.height,source.data(),output.data(),size,-1,0),"mismatched atlas cannot be replaced");
 options.enabled=false;check(MRExtraVisualV1("SeatBuggy",0,1)==0,"customization off passthrough");
 std::cout<<"EXTRA_NATIVE_PASS GENERAL tyre row (Quick Race + championship, two players); human-only compound wheels; Vehicle Select PS2/PC immediate; renderer V1/V2/texture contract\n";return 0;
 }catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
