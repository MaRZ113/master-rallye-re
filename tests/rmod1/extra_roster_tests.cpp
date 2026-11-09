#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include "../../src/native/rmod1/sdk_roster_abi.hpp"
#include "../../src/native/rmod1/vehicle_registry_abi.hpp"
#include <cwchar>
#include <iostream>
#include <vector>

int main(int argc,char** argv){
 if(argc!=2)return 2;
 const auto module=LoadLibraryA(argv[1]);if(!module)return 3;
 const auto reg=reinterpret_cast<DWORD(WINAPI*)(const rmod1::SdkRosterV1*)>(GetProcAddress(module,"MRRegisterSdkRosterV1"));
 const auto limit=reinterpret_cast<int(WINAPI*)()>(GetProcAddress(module,"MROpponentLimitV1"));
 if(!reg||!limit)return 4;
 rmod1::SdkVehicleV1 rows[]={{30,1,7},{31,1,7},{32,2,15}};
 rmod1::SdkRosterV1 profile{sizeof(profile),1,3,0x6dc,rows};
 if(!reg(&profile))return 5;
 rows[1].physical_id=30;if(reg(&profile))return 6;rows[1].physical_id=31;
 rows[1].class_id=3;if(reg(&profile))return 7;rows[1].class_id=1;
 rows[1].mode_mask=32;if(reg(&profile))return 8;rows[1].mode_mask=7;
 rows[1].physical_id=25;if(reg(&profile))return 9;rows[1].physical_id=31;
 std::vector<rmod1::SdkVehicleV1> many;
 for(int id=26;id<513;++id)many.push_back({id,id%3,15});
 profile.count=static_cast<unsigned>(many.size());profile.vehicles=many.data();profile.challenge_human_offset=0x12000;
 if(!reg(&profile))return 10;
 mr_vehicle_registry::DescriptorV1 registry{{'M','R','V','C'},1,44,513,52,3,0x45a3c0,0x10000000,0x10000010,0x10000020,0x10001000};
 wchar_t address[32]{};std::swprintf(address,32,L"0x%08x",unsigned(reinterpret_cast<uintptr_t>(&registry)));
 SetEnvironmentVariableW(L"MR_VEHICLE_REGISTRY_DESCRIPTOR",address);
 if(!reg(&profile))return 14;
 many.back().physical_id=513;if(reg(&profile))return 15;many.back().physical_id=512;
 registry.record_count=512;if(reg(&profile))return 16;
 SetEnvironmentVariableW(L"MR_VEHICLE_REGISTRY_DESCRIPTOR",nullptr);
 profile.count=3;profile.vehicles=rows;
 profile.challenge_human_offset=0;if(reg(&profile))return 11;profile.challenge_human_offset=0x6dc;
 if(!reg(&profile)||reg(nullptr))return 12;
 // Loading a provider must not increase the native or configured participant limit.
 if(limit()!=3)return 13;
 std::cout<<"SDK_ROSTER_PASS valid provider, duplicates/classes/masks/bounds rejected, participant default preserved\n";
 FreeLibrary(module);return 0;
}
