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
std::map<std::string,std::string> texts;
std::map<void*,std::vector<std::string>> lists;
std::map<std::string,std::vector<std::string>> published;
int command_value=-1,stock_calls=0;
uint32_t __fastcall test_key(uint32_t* to,void*,const char* s){auto& id=names[s];if(!id){id=uint32_t(names.size());strings[id]=s;}*to=id;return id;}
void* __cdecl test_broker(){return reinterpret_cast<void*>(1);}
int __fastcall test_get(void*,void*,uint32_t* k){return numbers[strings[*k]];}
bool __fastcall test_bool(void*,void*,uint32_t* k){return numbers[strings[*k]]!=0;}
void __fastcall test_int(void*,void*,uint32_t* k,int v){numbers[strings[*k]]=v;}
void __fastcall test_put_bool(void*,void*,uint32_t* k,bool v){numbers[strings[*k]]=v?1:0;}
void __fastcall test_name(void*,void*,uint32_t* k,uint32_t* v){texts[strings[*k]]=strings[*v];}
void __fastcall test_string(void*,void*,uint32_t* k,uint32_t* v){
 // This overload accepts String objects for BOTH path and value. Treating the
 // path as an interned Name reproduces the native 0x4d5267 invalid dereference.
 if(strings.count(*k)||strings.count(*v))throw std::runtime_error("String overload received Name ID");
 texts[reinterpret_cast<char*>(*k)]=reinterpret_cast<char*>(*v);
}
void __fastcall test_ctor(uint32_t* to,void*,const char* s){const auto n=std::strlen(s)+1;auto* p=std::malloc(n);std::memcpy(p,s,n);*to=reinterpret_cast<uint32_t>(p);}
void* __cdecl test_new(size_t n){return std::calloc(1,n);}
void __cdecl test_delete(uintptr_t p){std::free(reinterpret_cast<void*>(p));}
void __fastcall test_push(void* v,void*,uintptr_t,unsigned,uint32_t* p){lists[v].push_back(reinterpret_cast<char*>(*p));}
void __fastcall test_list(void*,void*,uint32_t* k,void* v){published[strings[*k]]=lists[v];lists.erase(v);std::free(v);}
void __fastcall test_writer(void*,void*,void*,void*){++stock_calls;}
int __fastcall test_command(void*,void*,unsigned){return command_value;}
void __fastcall test_init(void*,void*,void*){}
uintptr_t __fastcall test_tick(void*,void*,uint32_t x){return x;}
void check(bool ok,const char* s){if(!ok)throw std::runtime_error(s);}
}
uintptr_t extra_test_resolve(uintptr_t p){
 switch(p){
 case 0x4d0580:return reinterpret_cast<uintptr_t>(&test_key);
 case 0x4d8ec0:return reinterpret_cast<uintptr_t>(&test_broker);
 case 0x4d6760:return reinterpret_cast<uintptr_t>(&test_get);
 case 0x4d6520:return reinterpret_cast<uintptr_t>(&test_bool);
 case 0x4d8000:return reinterpret_cast<uintptr_t>(&test_int);
 case 0x4d7aa0:return reinterpret_cast<uintptr_t>(&test_put_bool);
 case 0x4d85f0:return reinterpret_cast<uintptr_t>(&test_name);
 case 0x4d8720:return reinterpret_cast<uintptr_t>(&test_string);
 case 0x4d8880:return reinterpret_cast<uintptr_t>(&test_list);
 case 0x4d11d0:return reinterpret_cast<uintptr_t>(&test_ctor);
 case 0x407b30:return reinterpret_cast<uintptr_t>(&test_push);
 case 0x5c1cb4:return reinterpret_cast<uintptr_t>(&test_new);
 case 0x5b4c00:return reinterpret_cast<uintptr_t>(&test_delete);
 case 0x496d20:case 0x498090:return reinterpret_cast<uintptr_t>(&test_writer);
 case 0x45d930:return reinterpret_cast<uintptr_t>(&test_command);
 case 0x4839d0:return reinterpret_cast<uintptr_t>(&test_init);
 case 0x483d20:return reinterpret_cast<uintptr_t>(&test_tick);
 default:throw std::runtime_error("unmapped API");
 }
}
int main(int argc,char** argv){try{
 if(argc!=2)return 2;
 using namespace extra_runtime;
 directory=argv[1];options={true,true,true};installed=true;
 numbers={{"Frontend/InQuickRaceMode",1},{"Frontend/QuickRace/Car0",21},
          {"Race/Type",2},{"Race/NumPlayers",1},{"Race/Car0/PlayerType",1},{"Race/Car0/CarID",21}};
 setup_init(nullptr,nullptr,nullptr);
 check(published["Frontend/ExtraOptions/TireList"].size()==6,"all six native tire labels");
 check(published["Frontend/ExtraOptions/PaintList"].size()==3,"independent visual presets");
 check(texts["Frontend/ExtraOptions/TireText"]=="STOCK","stock font requires uppercase UI labels");
 check(numbers["Frontend/ExtraOptions/TireRightArrow"]==1,"native arrows use integer state, not Bool datum");
 put_int("Frontend/ExtraOptions/Paint",2);put_int("Frontend/ExtraOptions/Tire",5);
 command_value=7;check(setup_command(nullptr,nullptr,1)==-3,"Apply uses original Back command after commit");
 check(paints[21]==2&&tires[21]==5,"native Apply commits both choices");
 check(MRExtraVisualV1("seatbuggy",-1,0)==1,"case-normalized frontend full bundle selection");
 check(MRExtraVisualV2("seatbuggy",-1,0)==1,"V2 identifies PC bundle");
 check(MRExtraVisualV1("seatbuggy",0,1)==1,"race visual identity does not depend on tire writer");
 char car0[64]="Vehicles/Car0",car1[64]="Vehicles/Car1";
 struct Prefix {uint32_t zero;char* text;} prefix{0,car0};
 texts.clear();front(nullptr,nullptr,&prefix,nullptr);rear(nullptr,nullptr,&prefix,nullptr);
 check(stock_calls==2&&texts["Vehicles/Car0/Suspension/Front/TyreType"]=="mud"&&texts["Vehicles/Car0/Suspension/Rear/TyreType"]=="mud","original writers plus coherent front and rear native family");
 check(MRExtraVisualV1("SeatBuggy",0,1)==1,"player race selection");
 check(MRExtraVisualV1("SeatBuggy",1,1)==0,"same-family AI remains unchanged");
 check(MRExtraVisualV1("Tata",0,1)==0,"unrelated family remains unchanged");
 paints[21]=1;
 check(MRExtraVisualV2("SeatBuggy",-1,0)==3,"V2 identifies PS2 geometry with PC textures");
 paints[21]=0;check(MRExtraVisualV2("SeatBuggy",-1,0)==2,"V2 identifies PS2 bundle");paints[21]=1;
 check(MRExtraVisualV2("SeatBuggy",1,1)==0,"V2 leaves same-family AI unchanged");
 check(MRExtraVisualV2("Tata",0,1)==0,"V2 rejects unrelated vehicle family");
 options.liveries=false;check(MRExtraVisualV2("SeatBuggy",-1,0)==0,"V2 honours disabled livery feature");options.liveries=true;
 pixels.resize(extra_package::binding_count);
 const auto& binding=extra_package::bindings[0];const unsigned size=binding.width*binding.height*4;
 std::vector<unsigned char> source(size,33),output(size,77);for(unsigned i=3;i<size;i+=4)source[i]=255;
 pixels[0].original=source;pixels[0].derived=source;pixels[0].derived[0]=64;
 check(MRExtraTextureV1("SeatBuggy",binding.index,binding.width,binding.height,source.data(),output.data(),size,-1,0)!=FALSE,"qualified texture-only upload");
 for(unsigned i=3;i<size;i+=4)check(output[i]==source[i],"texture alpha remains exact");
 check(!MRExtraTextureV1("SeatBuggy",binding.index,binding.width,binding.height,source.data(),output.data(),size,1,1),"AI texture upload isolated");
 source[1]^=1;check(!MRExtraTextureV1("SeatBuggy",binding.index,binding.width,binding.height,source.data(),output.data(),size,-1,0),"mismatched atlas cannot be replaced");
 paints[21]=2;
 for(unsigned i=0;i<6;++i){tires[21]=i;texts.clear();front(nullptr,nullptr,&prefix,nullptr);rear(nullptr,nullptr,&prefix,nullptr);
  if(!i)check(texts.empty(),"Stock exact passthrough");
  else check(texts.size()==2&&texts.begin()->second==extra_options::kTireNames[i],"every complete original family routed");}
 prefix.text=car1;texts.clear();front(nullptr,nullptr,&prefix,nullptr);check(texts.empty(),"AI prefix untouched");prefix.text=car0;
 numbers["Race/PlaybackReplay"]=1;front(nullptr,nullptr,&prefix,nullptr);check(texts.empty(),"replay untouched");numbers["Race/PlaybackReplay"]=0;
 command_value=9;setup_command(nullptr,nullptr,1);check(draft_paint==0&&draft_tire==0&&paints[21]==2,"Defaults remains a draft");
 command_value=8;check(setup_command(nullptr,nullptr,1)==-3,"Cancel uses original Back command");check(draft_paint==2&&draft_tire==5,"Cancel restores committed settings");
 options.liveries=false;check(MRExtraVisualV1("SeatBuggy",0,1)==0,"independent livery toggle");options.liveries=true;options.tires=false;texts.clear();front(nullptr,nullptr,&prefix,nullptr);check(texts.empty(),"independent tire toggle");
 options.enabled=false;check(MRExtraVisualV1("SeatBuggy",0,1)==0,"customization off passthrough");
 std::cout<<"EXTRA_NATIVE_PASS native-event Apply/Cancel/Defaults; six tire routes; Stock/AI/replay isolation; full visual-bundle query; independent toggles\n";return 0;
 }catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
