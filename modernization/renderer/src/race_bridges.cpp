#include "race_epoch.hpp"
namespace gfx2::race_bridge {
Callback callback=nullptr;
uintptr_t request_original=0,queue_original=0,commit_original=0,attach_original=0,
 live_original=0,retire_original=0,destroy_original=0,open_error_original=0,read_error_original=0,execute_original=0;
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
#define TAIL(NAME,K,ORIGINAL) \
 __declspec(naked) void NAME(){ \
 __asm {pushfd} __asm {pushad} NOTIFY(K,0) \
 __asm {popad} __asm {popfd} __asm {jmp dword ptr [ORIGINAL]} }
TAIL(request,0,request_original)
TAIL(queue,1,queue_original)
TAIL(retire,8,retire_original)
TAIL(destroy,9,destroy_original)
TAIL(open_error,10,open_error_original)
TAIL(read_error,11,read_error_original)

__declspec(naked) void commit(){
 __asm {pushfd} __asm {pushad} NOTIFY(2,0)
 __asm {push dword ptr [esp+40]} LOAD_INPUT(4)
 __asm {call dword ptr [commit_original]}
 __asm {pushfd} __asm {pushad} NOTIFY(3,36)
 __asm {popad} __asm {popfd} __asm {lea esp,[esp+36]} __asm {ret 4}
}
__declspec(naked) void attach(){
 __asm {pushfd} __asm {pushad} NOTIFY(4,0)
 __asm {push dword ptr [esp+44]} __asm {push dword ptr [esp+44]} LOAD_INPUT(8)
 __asm {call dword ptr [attach_original]}
 __asm {pushfd} __asm {pushad} NOTIFY(5,36)
 __asm {popad} __asm {popfd} __asm {lea esp,[esp+36]} __asm {ret 8}
}
__declspec(naked) void live(){
 __asm {pushfd} __asm {pushad} NOTIFY(7,0)
 __asm {push dword ptr [esp+40]} LOAD_INPUT(4)
 __asm {call dword ptr [live_original]}
 __asm {pushfd} __asm {pushad} NOTIFY(6,36)
 __asm {popad} __asm {popfd} __asm {lea esp,[esp+36]} __asm {ret 4}
}
__declspec(naked) void execute(){
 __asm {pushfd} __asm {pushad} NOTIFY(12,0) LOAD_INPUT(0)
 __asm {call dword ptr [execute_original]}
 __asm {pushfd} __asm {pushad} NOTIFY(13,36)
 __asm {popad} __asm {popfd} __asm {lea esp,[esp+36]} __asm {ret}
}
#undef TAIL
#undef LOAD_INPUT
#undef NOTIFY
}
