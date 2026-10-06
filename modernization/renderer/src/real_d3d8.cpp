#include "wrappers.hpp"
#include <new>
namespace {
using Factory=IDirect3D8*(WINAPI*)(UINT);
using VertexValidator=HRESULT(WINAPI*)(const DWORD*,const DWORD*,const D3DCAPS8*,BOOL,char**);
using PixelValidator=HRESULT(WINAPI*)(const DWORD*,const D3DCAPS8*,BOOL,char**);
INIT_ONCE once=INIT_ONCE_STATIC_INIT;
Factory factory=nullptr;VertexValidator vertex=nullptr;PixelValidator pixel=nullptr;
BOOL CALLBACK initialize(PINIT_ONCE,void*,void**){
 try {
 wchar_t path[32768];UINT n=GetSystemDirectoryW(path,32768);
 if(!n||n>=32760)return TRUE;
 std::wstring full(path,n);full+=L"\\d3d8.dll";
 HMODULE system=LoadLibraryW(full.c_str());
 if(system==gfx2::proxy_module){if(system)FreeLibrary(system);system=nullptr;}
 if(system){factory=reinterpret_cast<Factory>(GetProcAddress(system,"Direct3DCreate8"));vertex=reinterpret_cast<VertexValidator>(GetProcAddress(system,"ValidateVertexShader"));pixel=reinterpret_cast<PixelValidator>(GetProcAddress(system,"ValidatePixelShader"));}
 gfx2::note_real_runtime(system,full); // DLL remains pinned for live raw resources.
 }catch(...){OutputDebugStringA("R-GFX3 system runtime initialization failed\n");}
 return TRUE;
}
void ensure() noexcept {try{InitOnceExecuteOnce(&once,initialize,nullptr,nullptr);}catch(...){OutputDebugStringA("R-GFX3 system runtime initialization failed\n");}}
}
extern "C" IDirect3D8* WINAPI ProxyDirect3DCreate8(UINT sdk){
 ensure();if(!factory)return nullptr;
 IDirect3D8* raw=factory(sdk);
 try{gfx2::session().write("{\"type\":\"Direct3DCreate8\",\"sdk_version\":"+std::to_string(sdk)+",\"native_pointer\":"+std::to_string(reinterpret_cast<uintptr_t>(raw))+"}");}catch(...){}
 if(!raw)return nullptr;gfx2::Root8* wrapped=nullptr;
 try{wrapped=new(std::nothrow)gfx2::Root8(raw);}catch(...){}
 if(!wrapped)raw->Release();return wrapped;
}
extern "C" HRESULT WINAPI ProxyValidateVertexShader(const DWORD* code,const DWORD* declaration,const D3DCAPS8* caps,BOOL errors,char** output){ensure();return vertex?vertex(code,declaration,caps,errors,output):D3DERR_NOTAVAILABLE;}
extern "C" HRESULT WINAPI ProxyValidatePixelShader(const DWORD* code,const D3DCAPS8* caps,BOOL errors,char** output){ensure();return pixel?pixel(code,caps,errors,output):D3DERR_NOTAVAILABLE;}
