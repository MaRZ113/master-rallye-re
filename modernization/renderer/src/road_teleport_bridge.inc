// Shared production/test x86 call bridge. It forwards the original thiscall
// register and three native stack arguments without inventing a new ABI.
extern "C" __declspec(naked) void road_teleport_adjust_bridge() {
    __asm {
        pushfd
        pushad
        mov eax, esp
        push eax
        call road_teleport_adjust_bridge_observe
        add esp, 4
        popad
        popfd
        // Duplicate the exact three native stack arguments. The original
        // stdcall callee consumes these copies with ret 0x0C, leaving the
        // bridge's incoming stack frame intact for a post-call observation.
        push dword ptr [esp + 12]
        push dword ptr [esp + 12]
        push dword ptr [esp + 12]
        call dword ptr [road_teleport_adjust_original]
        pushfd
        pushad
        mov eax, esp
        push eax
        call road_teleport_adjust_bridge_after
        add esp, 4
        popad
        popfd
        ret 0Ch
    }
}
