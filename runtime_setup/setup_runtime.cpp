#include "setup_runtime.hpp"
#include "setup_package.hpp"
#include "setup_adapter.hpp"
#include <mmsystem.h>
#include <bcrypt.h>
#include <array>
#include <cstdio>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <vector>
#include <cstdint>
#include <atomic>

namespace mrsetup {
namespace {
using Tick=uintptr_t(__thiscall*)(void*,uint32_t);
using Writer=void(__thiscall*)(void*,void*,void*);
Tick tick=nullptr;
HWND owner=nullptr;
std::atomic_uint selected_livery{package::default_livery},selected_tyre{package::default_tyre},generation{1};
std::atomic_bool ready{false};
bool attempted=false,opened=false,key_down=false;
std::string failure="Not initialized";
std::filesystem::path root;
std::filesystem::path config_path(){wchar_t executable[32768]{};if(!GetModuleFileNameW(nullptr,executable,32768))return {};return std::filesystem::path(executable).parent_path()/L"VSET1.ini";}
bool package_present(){static const bool present=[](){auto p=config_path();return !p.empty()&&GetFileAttributesW(p.c_str())!=INVALID_FILE_ATTRIBUTES;}();return present;}
bool safe_ini(const std::filesystem::path& p){auto a=GetFileAttributesW(p.c_str());std::error_code ec;auto size=std::filesystem::file_size(p,ec);return a!=INVALID_FILE_ATTRIBUTES&&!(a&(FILE_ATTRIBUTE_REPARSE_POINT|FILE_ATTRIBUTE_DIRECTORY))&&!ec&&size>0&&size<=4096;}

void log(const char* message) noexcept {
 try {std::ofstream f(root/"vset1-runtime.log",std::ios::app);f<<message<<'\n';}catch(...){}
}
bool copy(void* to,const void* from,size_t bytes) noexcept {
 SIZE_T done=0;return ReadProcessMemory(GetCurrentProcess(),from,to,bytes,&done)&&done==bytes;
}
template<class T> T function(uintptr_t va){return reinterpret_cast<T>(va);}
uint32_t name(const char* text){uint32_t n=0;function<void(__thiscall*)(uint32_t*,const char*)>(adapter::key)(&n,text);return n;}
void* broker(){return function<void*(__cdecl*)()>(adapter::broker)();}
void set_name(const char* key,const char* value){auto k=name(key),v=name(value);function<void(__thiscall*)(void*,uint32_t*,uint32_t*)>(adapter::name_set)(broker(),&k,&v);}
#ifdef MRSETUP_TEST
int test_car=package::car_id,test_mode=2,test_players=1,test_player_type=1,test_original_calls=0;
bool test_attract=false,test_replay=false;
bool test_frontend_quick=true,test_split=false;
int test_frontend_car=package::car_id,test_setup_player=0;
std::vector<std::pair<std::string,std::string>> test_writes;
int car(){return test_car;} int mode(){return test_mode;}
int test_action=0;
#else
int car(){auto* p=function<void*(__cdecl*)()>(adapter::players)();return function<int(__thiscall*)(void*,int)>(adapter::car_get)(p,0);}
int mode(){auto* p=function<void*(__cdecl*)()>(adapter::race)();return function<int(__thiscall*)(void*)>(adapter::race_type)(p);}
#endif
#ifdef MRSETUP_TEST
int integer(const char* path){
 if(!std::strcmp(path,"Race/NumPlayers"))return test_players;
 if(!std::strcmp(path,"Race/Car0/PlayerType"))return test_player_type;
 if(!std::strcmp(path,"Race/Car0/CarID"))return test_car;
 if(!std::strcmp(path,"Frontend/QuickRace/Car0"))return test_frontend_car;
 if(!std::strcmp(path,"Frontend/CarSetup/PlayerID"))return test_setup_player;
 return 0;
}
bool boolean(const char* path){
 if(!std::strcmp(path,"Race/AttractMode"))return test_attract;
 if(!std::strcmp(path,"Race/PlaybackReplay"))return test_replay;
 if(!std::strcmp(path,"Frontend/InQuickRaceMode"))return test_frontend_quick;
 if(!std::strcmp(path,"Frontend/SplitScreen"))return test_split;
 return false;
}
void original_writer(uintptr_t,void*,void*,void*){++test_original_calls;}
void write_tyre(const char* key){test_writes.emplace_back(key,package::alternative_tyre);}
#else
int integer(const char* path){auto key=name(path);return function<int(__thiscall*)(void*,uint32_t*)>(adapter::int_get)(broker(),&key);}
bool boolean(const char* path){auto key=name(path);return function<bool(__thiscall*)(void*,uint32_t*)>(adapter::bool_get)(broker(),&key);}
void original_writer(uintptr_t address,void* self,void* prefix,void* data){function<Writer>(address)(self,prefix,data);}
void write_tyre(const char* key){set_name(key,package::alternative_tyre);}
#endif
bool player_prefix(void* value){char* p=nullptr;char s[32]{};return value&&copy(&p,static_cast<char*>(value)+4,4)&&p&&copy(s,p,sizeof(s))&&!std::strcmp(s,"Vehicles/Car0");}
bool frontend_scope(){return ready&&boolean("Frontend/InQuickRaceMode")&&!boolean("Frontend/SplitScreen")&&integer("Frontend/QuickRace/Car0")==package::car_id&&!boolean("Race/AttractMode")&&!boolean("Race/PlaybackReplay");}
bool race_scope(){return ready&&mode()==2&&integer("Race/Car0/CarID")==package::car_id&&integer("Race/NumPlayers")==1&&!boolean("Race/AttractMode")&&!boolean("Race/PlaybackReplay");}
bool visual_scope(){return frontend_scope()||race_scope();}
bool applies(void* prefix){return ready&&selected_tyre==1&&player_prefix(prefix)&&race_scope()&&integer("Race/Car0/PlayerType")==1;}
void log_scope(){char text[512]{};std::snprintf(text,sizeof(text),"SCOPE frontendQuick=%u split=%u selectedCar=%d setupPlayer=%d raceType=%d racePlayers=%d raceCar0=%d attract=%u replay=%u",boolean("Frontend/InQuickRaceMode"),boolean("Frontend/SplitScreen"),integer("Frontend/QuickRace/Car0"),integer("Frontend/CarSetup/PlayerID"),mode(),integer("Race/NumPlayers"),integer("Race/Car0/CarID"),boolean("Race/AttractMode"),boolean("Race/PlaybackReplay"));log(text);}
void __fastcall front(void* self,void*,void* prefix,void* data){
 original_writer(adapter::front_target,self,prefix,data);
 if(applies(prefix)){write_tyre("Vehicles/Car0/Suspension/Front/TyreType");log("APPLIED front Car0 alternative; source family unchanged");}
}
void __fastcall rear(void* self,void*,void* prefix,void* data){
 original_writer(adapter::rear_target,self,prefix,data);
 if(applies(prefix)){write_tyre("Vehicles/Car0/Suspension/Rear/TyreType");log("APPLIED rear Car0 alternative; source family unchanged");}
}
bool patch(void* at,const void* data,size_t bytes){DWORD old=0,ignored=0;if(!VirtualProtect(at,bytes,PAGE_EXECUTE_READWRITE,&old))return false;std::memcpy(at,data,bytes);bool restored=VirtualProtect(at,bytes,old,&ignored)!=FALSE;return FlushInstructionCache(GetCurrentProcess(),at,bytes)&&restored;}
std::string hash(const void* data,unsigned size){
 unsigned char value[32]{};
 BCRYPT_ALG_HANDLE a=nullptr;BCRYPT_HASH_HANDLE h=nullptr;DWORD object_size=0,done=0;
 if(BCryptOpenAlgorithmProvider(&a,BCRYPT_SHA256_ALGORITHM,nullptr,0)<0)return {};
 if(BCryptGetProperty(a,BCRYPT_OBJECT_LENGTH,reinterpret_cast<PUCHAR>(&object_size),4,&done,0)<0){BCryptCloseAlgorithmProvider(a,0);return {};}
 std::vector<unsigned char> object(object_size);bool ok=BCryptCreateHash(a,&h,object.data(),object_size,nullptr,0,0)>=0;
 if(ok)ok=BCryptHashData(h,(PUCHAR)data,size,0)>=0&&BCryptFinishHash(h,value,32,0)>=0;
 if(h)BCryptDestroyHash(h);BCryptCloseAlgorithmProvider(a,0);if(!ok)return {};
 static const char hex[]="0123456789abcdef";std::string s;for(auto v:value){s+=hex[v>>4];s+=hex[v&15];}return s;
}
std::vector<unsigned char> read(const char* relative,const char* expected,unsigned limit){
 auto p=root/std::filesystem::path(relative);auto inside=p.lexically_normal().lexically_relative(root);if(inside.empty()||*inside.begin()==L"..")return {};
 for(auto q=p;!q.empty()&&q!=root;q=q.parent_path())if(GetFileAttributesW(q.c_str())&FILE_ATTRIBUTE_REPARSE_POINT)return {};
 std::ifstream f(p,std::ios::binary|std::ios::ate);auto n=f.tellg();if(!f||n<=0||n>limit)return {};std::vector<unsigned char> b(static_cast<size_t>(n));f.seekg(0);f.read(reinterpret_cast<char*>(b.data()),n);if(!f||hash(b.data(),unsigned(b.size()))!=expected)return {};return b;
}
struct Texture {std::vector<unsigned char> original,alternate;};
std::array<Texture,package::binding_count> textures;

bool persist(unsigned livery,unsigned tyre){
 // This independent sidecar is never a championship/PlayerState file.
 auto folder=root/L"VehicleSetupState";std::error_code ec;std::filesystem::create_directory(folder,ec);
 auto attributes=GetFileAttributesW(folder.c_str());if(attributes==INVALID_FILE_ATTRIBUTES||(attributes&FILE_ATTRIBUTE_REPARSE_POINT))return false;
 auto path=folder/(std::wstring(package::identity_w)+L".ini"),temp=folder/(std::wstring(package::identity_w)+L".pending");
 if((GetFileAttributesW(path.c_str())!=INVALID_FILE_ATTRIBUTES&&(GetFileAttributesW(path.c_str())&FILE_ATTRIBUTE_REPARSE_POINT))||GetFileAttributesW(temp.c_str())!=INVALID_FILE_ATTRIBUTES)return false;
 HANDLE f=CreateFileW(temp.c_str(),GENERIC_WRITE,0,nullptr,CREATE_NEW,FILE_ATTRIBUTE_NORMAL,nullptr);if(f==INVALID_HANDLE_VALUE)return false;
 char text[512]{};int n=std::snprintf(text,sizeof(text),"[VehicleSetup]\r\nSchema=1\r\nPackage=%s\r\nContract=%s\r\nCarID=%u\r\nLivery=%u\r\nTyre=%u\r\n",package::identity,package::contract,package::car_id,livery,tyre);DWORD written=0;
 bool ok=n>0&&n<int(sizeof(text))&&WriteFile(f,text,n,&written,nullptr)&&written==unsigned(n)&&FlushFileBuffers(f);CloseHandle(f);
 if(ok)ok=MoveFileExW(temp.c_str(),path.c_str(),MOVEFILE_REPLACE_EXISTING|MOVEFILE_WRITE_THROUGH)!=FALSE;
 if(!ok)DeleteFileW(temp.c_str());return ok;
}
HWND combo(HWND parent,int id,int y,const char* label,const char* a,const char* b,unsigned value){
 CreateWindowA("STATIC",label,WS_CHILD|WS_VISIBLE,16,y,115,22,parent,nullptr,nullptr,nullptr);
 auto w=CreateWindowA("COMBOBOX","",WS_CHILD|WS_VISIBLE|WS_TABSTOP|CBS_DROPDOWNLIST,135,y,290,120,parent,(HMENU)(INT_PTR)id,nullptr,nullptr);
 SendMessageA(w,CB_ADDSTRING,0,(LPARAM)a);SendMessageA(w,CB_ADDSTRING,0,(LPARAM)b);SendMessage(w,CB_SETCURSEL,value,0);return w;
}
INT_PTR CALLBACK dialog(HWND w,UINT msg,WPARAM wp,LPARAM){
 if(msg==WM_INITDIALOG){
  SetWindowTextA(w,"Rally Workshop - Vehicle Setup (Quick Race pilot)");
  combo(w,101,25,"Paint / Livery",package::livery_default,package::livery_alternative,selected_livery);
  combo(w,102,70,"Tires",package::tyre_default_label,package::tyre_alternative_label,selected_tyre);
  CreateWindowA("STATIC","Applies to player 1 in the next Quick Race. AI stays Stock.",WS_CHILD|WS_VISIBLE,16,115,440,28,w,nullptr,nullptr,nullptr);
  CreateWindowA("BUTTON","Apply",WS_CHILD|WS_VISIBLE|WS_TABSTOP|BS_DEFPUSHBUTTON,135,155,90,27,w,(HMENU)IDOK,nullptr,nullptr);
  CreateWindowA("BUTTON","Defaults",WS_CHILD|WS_VISIBLE|WS_TABSTOP,235,155,90,27,w,(HMENU)103,nullptr,nullptr);
  CreateWindowA("BUTTON","Cancel",WS_CHILD|WS_VISIBLE|WS_TABSTOP,335,155,90,27,w,(HMENU)IDCANCEL,nullptr,nullptr);
  SetTimer(w,1,80,nullptr);SetFocus(GetDlgItem(w,101));return FALSE;
 }
 if(msg==WM_TIMER){
#ifdef MRSETUP_TEST
  if(test_action){int action=test_action;test_action=0;
   SendDlgItemMessage(w,101,CB_SETCURSEL,1,0);SendDlgItemMessage(w,102,CB_SETCURSEL,1,0);
   if(action==3)SendMessage(w,WM_COMMAND,103,0);
   SendMessage(w,WM_COMMAND,action==2?IDCANCEL:IDOK,0);return TRUE;
  }
#endif
  static DWORD previous=0;static DWORD pov=JOY_POVCENTERED;JOYINFOEX j{};j.dwSize=sizeof(j);j.dwFlags=JOY_RETURNALL;
  if(joyGetPosEx(JOYSTICKID1,&j)==JOYERR_NOERROR){auto pressed=j.dwButtons&~previous;previous=j.dwButtons;
   if(pressed&1)SendMessage(w,WM_COMMAND,IDOK,0);if(pressed&2)SendMessage(w,WM_COMMAND,IDCANCEL,0);if(pressed&8)SendMessage(w,WM_COMMAND,103,0);
   if(j.dwPOV!=pov&&j.dwPOV!=JOY_POVCENTERED){auto f=GetFocus();if(j.dwPOV==0||j.dwPOV==18000)SetFocus(GetDlgItem(w,GetDlgCtrlID(f)==101?102:101));else{int s=int(SendMessage(f,CB_GETCURSEL,0,0));if(s>=0)SendMessage(f,CB_SETCURSEL,1-s,0);}}pov=j.dwPOV;
  }return TRUE;
 }
 if(msg==WM_COMMAND){
  if(LOWORD(wp)==103){SendDlgItemMessage(w,101,CB_SETCURSEL,package::default_livery,0);SendDlgItemMessage(w,102,CB_SETCURSEL,package::default_tyre,0);return TRUE;}
  if(LOWORD(wp)==IDCANCEL){EndDialog(w,0);return TRUE;}
  if(LOWORD(wp)==IDOK){auto l=SendDlgItemMessage(w,101,CB_GETCURSEL,0,0),t=SendDlgItemMessage(w,102,CB_GETCURSEL,0,0);
   if(l<0||l>1||t<0||t>1||!persist(unsigned(l),unsigned(t))){MessageBoxA(w,"Selection was not saved; previous setup retained.","Vehicle Setup",MB_ICONERROR);return TRUE;}
   selected_livery=unsigned(l);selected_tyre=unsigned(t);++generation;log("CONFIRMED setup; next vehicle creation only");EndDialog(w,1);return TRUE;
  }
 }
 return FALSE;
}
void open(){
 if(opened||!owner||!ready)return;
 log_scope();
 if(!frontend_scope()||integer("Frontend/CarSetup/PlayerID")!=0){MessageBoxA(owner,"Select the configured vehicle for player 1 in single-player Quick Race. See vset1-runtime.log for the exact context.","Vehicle Setup",MB_OK);return;}
 opened=true;
 struct Template {DLGTEMPLATE header;WORD menu,cls,title;};
 Template t{};t.header.style=WS_POPUP|WS_CAPTION|WS_SYSMENU|DS_MODALFRAME;t.header.cx=305;t.header.cy=140;
 DialogBoxIndirectParamW(GetModuleHandleW(nullptr),&t.header,owner,dialog,0);opened=false;
}
uintptr_t __fastcall menu_tick(void* self,void*,uint32_t opaque_tick_word){
 auto result=tick(self,opaque_tick_word);bool down=(GetAsyncKeyState(VK_F6)&0x8000)!=0;
 unsigned char leaving=1;uintptr_t vtable=0;bool active=copy(&vtable,self,4)&&vtable==adapter::menu_vtable&&copy(&leaving,static_cast<char*>(self)+0x10,1)&&!leaving;
 if(active&&down&&!key_down&&GetForegroundWindow()==owner)open();key_down=down;
 return result;
}
bool install(){
 if(reinterpret_cast<uintptr_t>(GetModuleHandleW(nullptr))!=adapter::image_base){failure="Unsupported image base";return false;}
 for(const auto& item:adapter::apis){std::array<unsigned char,8> found{};if(!copy(found.data(),(void*)item.va,8)||found!=item.bytes){failure="Unsupported or conflicting native parameter API";return false;}}
 // Verify complete call instructions and the native menu vtable owner.
 constexpr uintptr_t sites[]={adapter::front_call,adapter::rear_call};constexpr uintptr_t targets[]={adapter::front_target,adapter::rear_target};
 for(unsigned i=0;i<2;++i){unsigned char b[5]{};if(!copy(b,(void*)sites[i],5)||b[0]!=0xe8||sites[i]+5+*reinterpret_cast<int32_t*>(b+1)!=targets[i]){failure="Conflicting participant writer hook";return false;}}
 uintptr_t init=0;if(!copy(&init,(void*)adapter::menu_init_slot,4)||init!=adapter::menu_init_target){failure="Unsupported setup initialization owner";return false;}
 uintptr_t observed=0;if(!copy(&observed,(void*)adapter::menu_tick_slot,4)||observed!=adapter::menu_tick_target){failure="Unsupported/conflicting setup screen";return false;}
 for(unsigned i=0;i<package::binding_count;++i){const auto& b=package::bindings[i];textures[i].original=read(b.base_path,b.base_sha,b.width*b.height*4);textures[i].alternate=read(b.alternate_path,b.alternate_sha,b.width*b.height*4);if(textures[i].original.size()!=b.width*b.height*4||textures[i].alternate.size()!=b.width*b.height*4){failure="Missing/changed livery asset";return false;}}
 auto state=root/L"VehicleSetupState"/(std::wstring(package::identity_w)+L".ini");
 if(std::filesystem::exists(state)&&(!safe_ini(state)||(GetFileAttributesW(state.parent_path().c_str())&FILE_ATTRIBUTE_REPARSE_POINT))){failure="Unsafe/oversized setup state";return false;}
 if(std::filesystem::exists(state)){if(GetPrivateProfileIntW(L"VehicleSetup",L"Schema",0,state.c_str())!=1||GetPrivateProfileIntW(L"VehicleSetup",L"CarID",-1,state.c_str())!=package::car_id){failure="State schema/CarID mismatch";return false;}wchar_t identity[128]{};GetPrivateProfileStringW(L"VehicleSetup",L"Package",L"",identity,128,state.c_str());if(std::wcscmp(identity,package::identity_w)){failure="State identity mismatch";return false;}wchar_t contract[128]{};GetPrivateProfileStringW(L"VehicleSetup",L"Contract",L"",contract,128,state.c_str());if(std::wcscmp(contract,package::contract_w)){failure="Preset contract changed; explicit state review/reset required";return false;}selected_livery=GetPrivateProfileIntW(L"VehicleSetup",L"Livery",99,state.c_str());selected_tyre=GetPrivateProfileIntW(L"VehicleSetup",L"Tyre",99,state.c_str());if(selected_livery>1||selected_tyre>1){failure="Removed/invalid preset; restore sidecar explicitly";return false;}}
 // Validate all sites before mutation; roll back the exact writes on failure.
 unsigned char original[2][5]{};for(unsigned i=0;i<2;++i)copy(original[i],(void*)sites[i],5);
 void* hooks[]={reinterpret_cast<void*>(&front),reinterpret_cast<void*>(&rear)};
 for(unsigned i=0;i<2;++i){unsigned char b[5]={0xe8};auto displacement=int32_t(reinterpret_cast<uintptr_t>(hooks[i])-sites[i]-5);std::memcpy(b+1,&displacement,4);if(!patch((void*)sites[i],b,5)){for(unsigned j=0;j<=i;++j)patch((void*)sites[j],original[j],5);failure="Writer hook transaction failed";return false;}}
 tick=function<Tick>(observed);auto replacement=&menu_tick;
 if(!patch((void*)adapter::menu_tick_slot,&replacement,4)){patch((void*)adapter::menu_tick_slot,&observed,4);for(unsigned j=0;j<2;++j)patch((void*)sites[j],original[j],5);failure="Menu hook failed; rollback attempted";return false;}
 log("READY V-SET1.1 frontend/race scope separation; F6 Gearbox; windowed pilot");return true;
}
}
void frame(IDirect3DDevice8& device)noexcept{try{if(attempted)return;attempted=true;if(!package_present())return;auto config=config_path();root=config.parent_path();if(!safe_ini(config)){log("DISABLED unsafe or oversized VSET1.ini");return;}if(GetPrivateProfileIntW(L"VehicleSetup",L"Enabled",0,config.c_str())!=1){log("DISABLED no hooks installed; native Stock fleet fallback");return;}D3DDEVICE_CREATION_PARAMETERS cp{};if(FAILED(device.GetCreationParameters(&cp)))return;owner=cp.hFocusWindow;if(!(GetWindowLongW(owner,GWL_STYLE)&WS_CAPTION)){failure="Windowed pilot requires a captioned game window";log(failure.c_str());return;}ready=install();if(!ready){log(failure.c_str());MessageBoxA(owner,failure.c_str(),"V-SET1 disabled - native Stock retained",MB_OK|MB_ICONERROR);}}catch(...){ready=false;}}
bool pilot_family_allowed(const char* family)noexcept{try{return !package_present()||(ready&&family&&!std::strcmp(family,package::family)&&visual_scope());}catch(...){return false;}}
unsigned revision(const char* family)noexcept{return ready&&family&&!std::strcmp(family,package::family)&&visual_scope()?generation.load():0u;}
bool pixels(const char* family,unsigned index,unsigned width,unsigned height,const void* original,void* output,unsigned bytes)noexcept{try{
 if(!ready||!selected_livery||!family||std::strcmp(family,package::family)||!visual_scope())return false;
 for(unsigned i=0;i<package::binding_count;++i){const auto& b=package::bindings[i];if(index!=b.index||width!=b.width||height!=b.height||bytes!=textures[i].original.size())continue;
  if(std::memcmp(original,textures[i].original.data(),bytes))return false;
  std::memcpy(output,textures[i].alternate.data(),bytes);return true;
 }return false;
}catch(...){return false;}}
}
