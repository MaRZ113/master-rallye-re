#include "extra_options_bridge.hpp"
#pragma warning(push)
#pragma warning(disable:4201) // legacy vendored D3D8 anonymous union
#include "fleet_frame_policy.hpp"
#pragma warning(pop)
#include <thread>
#include <vector>
#include <cstring>
#include <iostream>
int failures=0;
#define CHECK(x) do{if(!(x)){std::cerr<<"FAIL "<<__LINE__<<": "#x"\n";++failures;}}while(0)
unsigned WINAPI visual(const char*,int,unsigned){return 1;}
unsigned WINAPI revision(const char*,int,unsigned){return 7;}
BOOL WINAPI texture(const char*,unsigned,unsigned,unsigned,const void*,void*,unsigned,int,unsigned){return FALSE;}
int main(int argc,char** argv){
 mrextra::API absent,legacy{visual,revision,nullptr,texture};
 CHECK(!absent.native("Tata",0,1));CHECK(!absent.generation("Tata",0,1));
 CHECK(legacy.complete()&&legacy.native("Tata",0,1));CHECK(!legacy.variant("Tata",0,1));
 CHECK(!legacy.native(nullptr,0,1));CHECK(!mrextra::from_module(GetModuleHandleW(L"kernel32.dll")).complete());
 CHECK(mrextra::upload_key(absent,"Tata",0,1)==mrextra::upload_key(absent,"Tata",1,0));
 CHECK(mrextra::upload_key(legacy,"Tata",0,1)==mrextra::UploadKey{});
 mrextra::Cache late;unsigned probes=0;bool loaded=false;
 auto probe=[&]()noexcept{++probes;return loaded?legacy:mrextra::API{};};
 CHECK(!late.get(0,probe).complete());loaded=true;
 CHECK(!late.get(249,probe).complete()&&probes==1);CHECK(late.get(250,probe).complete()&&probes==2);
 CHECK(late.get(251,probe).complete()&&probes==2);
 mrextra::Cache partial;auto incomplete=legacy;incomplete.texture=nullptr;
 CHECK(!partial.get(0,[&]()noexcept{return incomplete;}).complete());
 mrextra::Cache concurrent;std::atomic_uint calls{0};std::vector<std::thread> workers;
 for(unsigned i=0;i<8;++i)workers.emplace_back([&](){concurrent.get(1,[&]()noexcept{++calls;return legacy;});});
 for(auto& worker:workers)worker.join();CHECK(calls==1);
 CHECK(concurrent.get(2,[&]()noexcept{++calls;return absent;}).complete()&&calls==1);
 CHECK(!mrextra::api().complete()); // no proxy loaded, no implicit LoadLibrary
 if(argc!=2){std::cerr<<"fixture path required\n";return 2;}
 const auto module=LoadLibraryA(argv[1]);CHECK(module);if(!module)return 2;
 using Set=void(WINAPI*)(unsigned,unsigned,unsigned);
 const auto set=reinterpret_cast<Set>(GetProcAddress(module,"ExtraFixtureSet"));CHECK(set);if(!set)return 2;
 set(123,2,1);CHECK(!mrextra::from_module(module).complete());
 set(mrextra::kAbi,2,1);const auto api=mrextra::from_module(module);CHECK(api.complete());
 CHECK(api.variant("Tata",-1,0)==2);CHECK(!api.native("Tata",0,1));
 CHECK(api.variant("Tata",1,1)==0);CHECK(api.variant("DefTomcat",0,1)==0);
 set(mrextra::kAbi,1,2);CHECK(api.native("Tata",0,1));CHECK(!api.native("Tata",1,1));
 CHECK(mrextra::upload_key(api,"Tata",0,1)==mrextra::UploadKey{});
 // Discover a provider loaded after the renderer's first failed lookup.
 Sleep(260);CHECK(mrextra::api().complete());
 gfx2::RaceCertificate race{};race.valid=true;race.single_human_car_race=true;race.participant_count=1;
 gfx2::ps2port::FleetActive active{};active.active=true;strcpy_s(active.folder.data(),active.folder.size(),"Tata");active.index=0;
 CHECK(!gfx2::ps2port::fleet_single_car_race(true,race,active));
 active.index=1;CHECK(gfx2::ps2port::fleet_single_car_race(true,race,active));
 active.index=0;set(mrextra::kAbi,2,3);CHECK(gfx2::ps2port::fleet_single_car_race(true,race,active));
 set(mrextra::kAbi,3,4);const auto key=mrextra::upload_key(api,"Tata",0,1);
 CHECK(key.variant==3&&key.generation==4&&key.phase==1&&key.participant==0);
 CHECK(key!=mrextra::upload_key(api,"Tata",-1,0));
 CHECK(key!=mrextra::upload_key(api,"Tata",1,1));
 unsigned char source[]={0x11,0x22,0x33,0x80},out[4]{};
 CHECK(api.replace("Tata",0,1,1,source,out,4,0,1));CHECK(out[0]==0x44&&out[3]==0x80&&source[0]==0x11);
 CHECK(!api.replace("Tata",0,1,1,source,out,4,1,1));CHECK(!api.replace("Tata",1,1,1,source,out,4,0,1));
 CHECK(!api.replace("Tata",0,2,1,source,out,4,0,1));
 set(mrextra::kAbi,3,5);CHECK(key!=mrextra::upload_key(api,"Tata",0,1));
 // Cache owns a module reference: releasing the caller does not dangle APIs.
 FreeLibrary(module);CHECK(mrextra::api().complete()&&mrextra::variant("Tata",0,1)==3);
 std::cout<<"Extra Options optional ABI/late-load/standalone/participant/texture/cache checks: "<<(failures?"FAIL":"PASS")<<"\n";
 return failures?1:0;
}
