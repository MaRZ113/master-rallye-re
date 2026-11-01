#define MRSETUP_TEST 1
#include "setup_runtime.cpp"
#include <iostream>
uintptr_t __fastcall mock_tick(void*,void*,uint32_t word){return word^0x12345678u;}
int wmain(int argc,wchar_t** argv){
 if(argc!=2)return 2;
 mrsetup::root=std::filesystem::absolute(argv[1]);
 if(std::filesystem::exists(mrsetup::root))return 3;
 std::filesystem::create_directories(mrsetup::root);
 mrsetup::owner=CreateWindowW(L"STATIC",L"V-SET1 modal UI test host",WS_OVERLAPPEDWINDOW,0,0,600,400,nullptr,nullptr,nullptr,nullptr);
 if(!mrsetup::owner)return 4;
 mrsetup::ready=true;
 // A menu exists before Race/Type and Race/NumPlayers are published.
 mrsetup::test_mode=0;mrsetup::test_players=0;
 if(!mrsetup::visual_scope())return 23;
 if(mrsetup::race_scope())return 24;
 mrsetup::test_frontend_quick=false;if(mrsetup::frontend_scope())return 25;mrsetup::test_frontend_quick=true;
 mrsetup::test_split=true;if(mrsetup::frontend_scope())return 26;mrsetup::test_split=false;
 mrsetup::test_frontend_car=-1;if(mrsetup::frontend_scope())return 27;mrsetup::test_frontend_car=mrsetup::package::car_id;
 mrsetup::test_action=1;mrsetup::open();
 if(mrsetup::selected_livery!=1||mrsetup::selected_tyre!=1)return 5;
 mrsetup::test_mode=2;mrsetup::test_players=1;
 struct Prefix {uint32_t header;const char* data;uint32_t length,capacity;};
 char player[]="Vehicles/Car0",ai[]="Vehicles/Car1";Prefix p{0,player,13,31},other{0,ai,13,31};
 auto reject=[&](Prefix* prefix){auto calls=mrsetup::test_original_calls;mrsetup::test_writes.clear();mrsetup::front(nullptr,nullptr,prefix,nullptr);mrsetup::rear(nullptr,nullptr,prefix,nullptr);return mrsetup::test_writes.empty()&&mrsetup::test_original_calls==calls+2;};
 mrsetup::front(nullptr,nullptr,&p,nullptr);mrsetup::rear(nullptr,nullptr,&p,nullptr);
 if(mrsetup::test_writes.size()!=2||mrsetup::test_writes[0].first!="Vehicles/Car0/Suspension/Front/TyreType"||mrsetup::test_writes[1].first!="Vehicles/Car0/Suspension/Rear/TyreType")return 10;
 if(!reject(&other))return 11;
 mrsetup::test_player_type=0;if(!reject(&p))return 12;mrsetup::test_player_type=1;
 mrsetup::test_players=2;if(!reject(&p))return 13;mrsetup::test_players=1;
 mrsetup::test_mode=5;if(!reject(&p))return 14;mrsetup::test_mode=2;
 mrsetup::test_attract=true;if(!reject(&p))return 15;mrsetup::test_attract=false;
 mrsetup::test_replay=true;if(!reject(&p))return 16;mrsetup::test_replay=false;
 mrsetup::test_car=-1;if(!reject(&p))return 17;mrsetup::test_car=mrsetup::package::car_id;
 const auto& binding=mrsetup::package::bindings[0];auto bytes=binding.width*binding.height*4;
 mrsetup::textures[0].original.assign(bytes,17);mrsetup::textures[0].alternate.assign(bytes,41);
 std::vector<unsigned char> original(bytes,17),derived(bytes,0);
 if(!mrsetup::pixels(mrsetup::package::family,binding.index,binding.width,binding.height,original.data(),derived.data(),bytes)||derived[0]!=41)return 18;
 if(mrsetup::pixels("different-car",binding.index,binding.width,binding.height,original.data(),derived.data(),bytes))return 19;
 original[0]^=1;if(mrsetup::pixels(mrsetup::package::family,binding.index,binding.width,binding.height,original.data(),derived.data(),bytes))return 20;
 auto state=mrsetup::root/L"VehicleSetupState"/(std::wstring(mrsetup::package::identity_w)+L".ini");
 auto pin=[](const std::filesystem::path& p){std::ifstream f(p,std::ios::binary);return std::string(std::istreambuf_iterator<char>(f),{});};
 auto before=pin(state);if(before.empty())return 6;
 mrsetup::test_action=2;mrsetup::open();if(pin(state)!=before)return 7;
 mrsetup::test_action=3;mrsetup::open();if(mrsetup::selected_livery||mrsetup::selected_tyre)return 8;
 if(GetPrivateProfileIntW(L"VehicleSetup",L"Tyre",99,state.c_str())!=0)return 9;
 if(!reject(&p))return 21;
 std::array<unsigned char,20> self{};auto vt=mrsetup::adapter::menu_vtable;std::memcpy(self.data(),&vt,4);self[16]=1;
 mrsetup::tick=reinterpret_cast<mrsetup::Tick>(&mock_tick);
 if(mrsetup::menu_tick(self.data(),nullptr,0x7fc00001u)!=(0x7fc00001u^0x12345678u))return 22;
 DestroyWindow(mrsetup::owner);
 std::cout<<"PASS actual Win32 owned modal create/confirm/cancel/defaults/persistence; native adapter mock-backend Car0-only/AI/mode/replay/split/default gates and material-owner/pixel pins; no game process launched\n";
 return 0;
}
