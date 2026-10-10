#include "game_fov.hpp"
namespace gfx2::camera_bridge {
Callback callback=nullptr;uintptr_t scheduler_original=0;
// EBP points to the PUSHAD image, not to native locals. Callbacks get the
// immutable original input image; post callbacks never substitute native outputs.
// The 512-byte FXSAVE area and callback stack are 16-byte aligned.
#define NOTIFY(K,OFFSET) \
 __asm {mov ebp,esp} \
 __asm {and esp,0xfffffff0} \
 __asm {sub esp,528} \
 __asm {fxsave [esp]} \
 __asm {fninit} \
 __asm {mov dword ptr [esp+512],01f80h} \
 __asm {ldmxcsr [esp+512]} \
 __asm {cld} \
 __asm {lea eax,[ebp+OFFSET]} \
 __asm {sub esp,8} \
 __asm {push eax} \
 __asm {push K} \
 __asm {call dword ptr [callback]} \
 __asm {lea esp,[esp+8]} \
 __asm {fxrstor [esp]} \
 __asm {mov esp,ebp}
#define LOAD_INPUT(N) \
 __asm {push dword ptr [esp+N+32]} \
 __asm {popfd} \
 __asm {mov edi,[esp+N]} \
 __asm {mov esi,[esp+N+4]} \
 __asm {mov ebp,[esp+N+8]} \
 __asm {mov ebx,[esp+N+16]} \
 __asm {mov edx,[esp+N+20]} \
 __asm {mov ecx,[esp+N+24]} \
 __asm {mov eax,[esp+N+28]}
__declspec(naked) void scheduler(){
 __asm {pushfd} __asm {pushad} NOTIFY(0,0)
 __asm {push dword ptr [esp+40]} LOAD_INPUT(4)
 __asm {call dword ptr [scheduler_original]}
 __asm {pushfd} __asm {pushad} NOTIFY(1,36)
 __asm {popad} __asm {popfd} __asm {lea esp,[esp+36]} __asm {ret 4}
}

#undef LOAD_INPUT
#undef NOTIFY
}
