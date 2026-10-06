#include "provenance.hpp"
#include "state_tracker.hpp"
#include <bcrypt.h>
#include <sstream>
#include <iomanip>
#include <vector>
#include <cstdio>
#include <cwchar>
namespace gfx2 {
HMODULE proxy_module=nullptr;
std::wstring module_path(HMODULE m) {
 std::vector<wchar_t> b(32768);DWORD n=GetModuleFileNameW(m,b.data(),static_cast<DWORD>(b.size()));
 if(!n || n>=b.size())return {};return {b.data(),n};
}
std::string utf8(const std::wstring& s){
 if(s.empty())return {};int n=WideCharToMultiByte(CP_UTF8,0,s.data(),static_cast<int>(s.size()),nullptr,0,nullptr,nullptr);
 std::string out(n,'\0');WideCharToMultiByte(CP_UTF8,0,s.data(),static_cast<int>(s.size()),out.data(),n,nullptr,nullptr);return out;
}
std::string quote(const std::string& s){
 std::string o="\"";for(unsigned char c:s){
  if(c=='"'||c=='\\'){o+='\\';o+=c;}else if(c<32){char b[7];sprintf_s(b,"\\u%04x",c);o+=b;}else o+=c;
 }return o+'"';
}
std::string sha256_file(const std::wstring& path,uint64_t* size) noexcept {
 HANDLE f=INVALID_HANDLE_VALUE;BCRYPT_ALG_HANDLE a=nullptr;BCRYPT_HASH_HANDLE h=nullptr;
 std::string output;
 try {
  f=CreateFileW(path.c_str(),GENERIC_READ,FILE_SHARE_READ|FILE_SHARE_WRITE|FILE_SHARE_DELETE,nullptr,OPEN_EXISTING,FILE_ATTRIBUTE_NORMAL,nullptr);
  if(f==INVALID_HANDLE_VALUE)throw 1;
  LARGE_INTEGER n;if(!GetFileSizeEx(f,&n))throw 1;if(size)*size=n.QuadPart;
  if(BCryptOpenAlgorithmProvider(&a,BCRYPT_SHA256_ALGORITHM,nullptr,0)<0)throw 1;
  if(BCryptCreateHash(a,&h,nullptr,0,nullptr,0,0)<0)throw 1;
  unsigned char buf[65536],digest[32];DWORD read=0;
  for(;;){if(!ReadFile(f,buf,sizeof(buf),&read,nullptr))throw 1;if(!read)break;if(BCryptHashData(h,buf,read,0)<0)throw 1;}
  if(BCryptFinishHash(h,digest,32,0)<0)throw 1;
  char b[3];for(unsigned char c:digest){sprintf_s(b,"%02x",c);output+=b;}
 }catch(...){output.clear();}
 if(h)BCryptDestroyHash(h);if(a)BCryptCloseAlgorithmProvider(a,0);if(f!=INVALID_HANDLE_VALUE)CloseHandle(f);return output;
}
Caller caller_info(uintptr_t pc){
 Caller c;c.address=pc;HMODULE m=nullptr;
 if(pc && GetModuleHandleExW(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS|GET_MODULE_HANDLE_EX_FLAG_UNCHANGED_REFCOUNT,reinterpret_cast<LPCWSTR>(pc),&m)){
  auto path=module_path(m);if(!path.empty()){c.known=true;c.base=reinterpret_cast<uintptr_t>(m);c.module=utf8(path);}
 }return c;
}
std::string pp_json(const D3DPRESENT_PARAMETERS& p){
 std::ostringstream o;o<<"{\"width\":"<<p.BackBufferWidth<<",\"height\":"<<p.BackBufferHeight
 <<",\"format\":"<<p.BackBufferFormat<<",\"count\":"<<p.BackBufferCount<<",\"multisample\":"<<p.MultiSampleType
 <<",\"swap_effect\":"<<p.SwapEffect<<",\"device_window\":"<<reinterpret_cast<uintptr_t>(p.hDeviceWindow)
 <<",\"windowed\":"<<p.Windowed<<",\"auto_depth\":"<<p.EnableAutoDepthStencil<<",\"depth_format\":"<<p.AutoDepthStencilFormat
 <<",\"flags\":"<<p.Flags<<",\"refresh\":"<<p.FullScreen_RefreshRateInHz<<",\"interval\":"<<p.FullScreen_PresentationInterval<<"}";return o.str();
}
Session::Session(){
 if(!InitializeCriticalSectionEx(&lock_,2000,0))throw std::bad_alloc();
 auto own=module_path(proxy_module),exe=module_path(nullptr);uint64_t exe_size=0;
 proxy_path=utf8(own);exe_path=utf8(exe);proxy_sha=sha256_file(own);exe_sha=sha256_file(exe,&exe_size);target=exe_sha==TARGET_SHA;
 auto base=own.substr(0,own.find_last_of(L"\\/"));
 auto ini=base+L"\\MRRRenderer.ini";config_path=ini;visual_config=read_visual_config(ini);
 auto boolean=[&](const wchar_t* key){wchar_t b[16];GetPrivateProfileStringW(L"Trace",key,L"true",b,16,ini.c_str());return _wcsicmp(b,L"false")!=0&&wcscmp(b,L"0")!=0;};
 enabled=boolean(L"Enabled");summaries=boolean(L"FrameSummaries");
 CreateDirectoryW((base+L"\\MRRRenderer").c_str(),nullptr);directory=base+L"\\MRRRenderer\\logs";CreateDirectoryW(directory.c_str(),nullptr);
 SYSTEMTIME t;GetSystemTime(&t);wchar_t name[128];swprintf_s(name,L"\\session-%04u%02u%02u-%02u%02u%02u-%lu.jsonl",t.wYear,t.wMonth,t.wDay,t.wHour,t.wMinute,t.wSecond,GetCurrentProcessId());
 file_=CreateFileW((directory+name).c_str(),GENERIC_WRITE,FILE_SHARE_READ,nullptr,CREATE_NEW,FILE_ATTRIBUTE_NORMAL,nullptr);
 std::ostringstream o;o<<"{\"type\":\"session\",\"schema_version\":1,\"proxy_version\":\"R-GFX3-1\",\"architecture\":\"I386/PE32\",\"exe_path\":"<<quote(exe_path)<<",\"exe_size\":"<<exe_size<<",\"exe_sha256\":"<<quote(exe_sha)<<",\"proxy_path\":"<<quote(proxy_path)<<",\"proxy_sha256\":"<<quote(proxy_sha)<<",\"build\":"<<quote(target?"PRISTINE_RETAIL":"UNKNOWN_BUILD")<<",\"trace_enabled\":"<<(enabled?"true":"false")<<"}";write(o.str());
 auto effective=visual_config;if(!target){effective.anisotropy=effective.fov=effective.shadow_off=false;effective.reason="unsupported_build";}
 write("{\"type\":\"renderer_config\",\"version\":\"R-GFX3-1\",\"config_path\":"+quote(utf8(config_path))+",\"build\":"+quote(target?"PRISTINE_RETAIL":"UNKNOWN_BUILD")+",\"requested\":"+config_json(visual_config)+",\"effective_before_caps\":"+config_json(effective)+"}");
}
Session& session(){static Session* s=new Session();return *s;}
uint64_t Session::device_serial() noexcept {EnterCriticalSection(&lock_);auto n=++serial_;LeaveCriticalSection(&lock_);return n;}
void Session::write(const std::string& s) noexcept {
 try {std::string line=s+'\n';EnterCriticalSection(&lock_);
  if(file_!=INVALID_HANDLE_VALUE && bytes_+line.size()<=16*1024*1024){
   DWORD done=0;if(!WriteFile(file_,line.data(),static_cast<DWORD>(line.size()),&done,nullptr)||done!=line.size()){
    LARGE_INTEGER at;at.QuadPart=bytes_;SetFilePointerEx(file_,at,nullptr,FILE_BEGIN);SetEndOfFile(file_);CloseHandle(file_);file_=INVALID_HANDLE_VALUE;OutputDebugStringA("R-GFX3 logging failed; forwarding remains active\n");
   }else bytes_+=done;
  }LeaveCriticalSection(&lock_);
 }catch(...){OutputDebugStringA("R-GFX3 log allocation failure\n");}
}
void note_real_runtime(HMODULE m,const std::wstring& requested) noexcept {
 try{auto& s=session();s.real_path=utf8(module_path(m));s.write("{\"type\":\"real_runtime\",\"requested_path\":"+quote(utf8(requested))+",\"actual_path\":"+quote(s.real_path)+",\"loaded\":"+(m?"true":"false")+"}");}catch(...){}
}
void note_create_device(UINT a,D3DDEVTYPE t,HWND w,DWORD f,const D3DPRESENT_PARAMETERS* p,const D3DPRESENT_PARAMETERS* post,HRESULT hr,uintptr_t raw,uintptr_t wrapped) noexcept {
 try{std::ostringstream o;o<<"{\"type\":\"create_device\",\"adapter\":"<<a<<",\"device_type\":"<<t<<",\"focus_window\":"<<reinterpret_cast<uintptr_t>(w)<<",\"behavior_flags\":"<<f<<",\"parameters_before\":"<<(p?pp_json(*p):"null")<<",\"parameters_after\":"<<(post?pp_json(*post):"null")<<",\"hresult\":"<<static_cast<uint32_t>(hr)<<",\"real_pointer\":"<<raw<<",\"wrapper_pointer\":"<<wrapped<<"}";session().write(o.str());}catch(...){}
}
}
