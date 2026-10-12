// Shared production/test x86 bridges. PUSHFD/PUSHAD guards both observers.
extern "C" __declspec(naked) void physics_probe_clear_gate_bridge() {
    __asm {
        pushfd
        pushad
        mov eax, dword ptr [esp + 28]
        push 0
        push eax
        push 0004CCC70h
        call physics_probe_clear_writer_observe
        add esp, 12
        popad
        popfd
        pushfd
        pushad
        mov eax, esp
        push 0
        push 0004CCC70h
        push eax
        call physics_probe_transaction_observe
        add esp, 12
        popad
        popfd
        mov eax, dword ptr [eax + 8]
        mov byte ptr [eax + 33h], 0
        pushfd
        pushad
        mov eax, esp
        push 1
        push 0004CCC70h
        push eax
        call physics_probe_transaction_observe
        add esp, 12
        popad
        popfd
        ret
    }
}

extern "C" __declspec(naked) void physics_probe_clear_recovery_bridge() {
    __asm {
        pushfd
        pushad
        mov eax, dword ptr [esp + 28]
        push 0
        push eax
        push 0004CD1A1h
        call physics_probe_clear_writer_observe
        add esp, 12
        popad
        popfd
        pushfd
        pushad
        mov eax, esp
        push 0
        push 0004CD1A1h
        push eax
        call physics_probe_transaction_observe
        add esp, 12
        popad
        popfd
        mov ecx, dword ptr [eax + 8]
        mov byte ptr [ecx + 33h], 0
        pushfd
        pushad
        mov eax, esp
        push 1
        push 0004CD1A1h
        push eax
        call physics_probe_transaction_observe
        add esp, 12
        popad
        popfd
        ret
    }
}

extern "C" __declspec(naked) void physics_probe_clear_timer_bridge() {
    __asm {
        pushfd
        pushad
        mov eax, dword ptr [esp + 28]
        mov edx, dword ptr [esp + 24]
        push edx
        push eax
        push 0004CD1DEh
        call physics_probe_clear_writer_observe
        add esp, 12
        popad
        popfd
        pushfd
        pushad
        mov eax, esp
        push 0
        push 0004CD1DEh
        push eax
        call physics_probe_transaction_observe
        add esp, 12
        popad
        popfd
        mov eax, dword ptr [eax + 8]
        mov byte ptr [eax + 33h], cl
        pushfd
        pushad
        mov eax, esp
        push 1
        push 0004CD1DEh
        push eax
        call physics_probe_transaction_observe
        add esp, 12
        popad
        popfd
        ret
    }
}

extern "C" __declspec(naked) void physics_probe_publish_bridge() {
    __asm {
        pushfd
        pushad
        mov eax, esp
        push 0
        push 0004CCFF1h
        push eax
        call physics_probe_transaction_observe
        add esp, 12
        popad
        popfd
        mov byte ptr [ebp + 33h], 1
        mov ecx, dword ptr [esi + 1ch]
        pushfd
        pushad
        mov eax, esp
        push 1
        push 0004CCFF1h
        push eax
        call physics_probe_transaction_observe
        add esp, 12
        popad
        popfd
        ret
    }
}

extern "C" __declspec(naked) void physics_probe_matrix_complete_bridge() {
    __asm {
        pushfd
        pushad
        mov eax, esp
        push 0
        push 0004CD131h
        push eax
        call physics_probe_transaction_observe
        add esp, 12
        popad
        popfd
        mov ecx, dword ptr [esi + 3ch]
        mov edx, ebx
        add edx, ecx
        pushfd
        pushad
        mov eax, esp
        push 1
        push 0004CD131h
        push eax
        call physics_probe_transaction_observe
        add esp, 12
        popad
        popfd
        ret
    }
}

extern "C" __declspec(naked) void physics_probe_input_flag_bridge() {
    __asm {
        pushfd
        pushad
        mov eax, esp
        push 0
        push 000591345h
        push eax
        call physics_probe_transaction_observe
        add esp, 12
        popad
        popfd
        mov byte ptr [eax + 33h], dl
        mov eax, dword ptr [ecx + 2ch]
        pushfd
        pushad
        mov eax, esp
        push 1
        push 000591345h
        push eax
        call physics_probe_transaction_observe
        add esp, 12
        popad
        popfd
        ret
    }
}

extern "C" __declspec(naked) void physics_probe_restore_flag_bridge() {
    __asm {
        pushfd
        pushad
        mov eax, esp
        push 0
        push 0004CB62Ah
        push eax
        call physics_probe_transaction_observe
        add esp, 12
        popad
        popfd
        mov byte ptr [esi + 33h], al
        pushfd
        pushad
        mov eax, esp
        push 1
        push 0004CB62Ah
        push eax
        call physics_probe_transaction_observe
        add esp, 12
        popad
        popfd
        push dword ptr [esp + 4]
        call dword ptr [physics_probe_restore_target]
        ret 4
    }
}
