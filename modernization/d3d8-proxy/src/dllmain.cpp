#include "provenance.hpp"
BOOL WINAPI DllMain(HMODULE module,DWORD reason,LPVOID){
 if(reason==DLL_PROCESS_ATTACH)gfx2::proxy_module=module;
 return TRUE;
}
