#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include "../../src/native/rmod1/sdk_roster_abi.hpp"
#include <iostream>

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
 profile.count=65;if(reg(&profile))return 10;profile.count=3;
 profile.challenge_human_offset=0;if(reg(&profile))return 11;profile.challenge_human_offset=0x6dc;
 if(!reg(&profile)||reg(nullptr))return 12;
 // Loading a provider must not increase the native or configured participant limit.
 if(limit()!=3)return 13;
 std::cout<<"SDK_ROSTER_PASS valid provider, duplicates/classes/masks/bounds rejected, participant default preserved\n";
 FreeLibrary(module);return 0;
}
