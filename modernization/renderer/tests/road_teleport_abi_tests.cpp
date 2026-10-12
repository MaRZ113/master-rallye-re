#include "road_teleport_bridge.hpp"
#include <cstdint>
#include <cstdio>

extern "C" uintptr_t road_teleport_adjust_original = 0;
extern "C" uint32_t road_teleport_test_seen[16] = {};
#include "../src/road_teleport_bridge.inc"

extern "C" __declspec(naked) void road_teleport_adjust_bridge_observe(
    const gfx2::RoadAdjustSaved*) noexcept {
    __asm {
        mov eax, dword ptr [esp + 4]
        mov dword ptr [road_teleport_test_seen], eax
        mov edx, dword ptr [eax + 24]
        mov dword ptr [road_teleport_test_seen + 4], edx
        mov edx, dword ptr [eax + 40]
        mov dword ptr [road_teleport_test_seen + 8], edx
        mov edx, dword ptr [eax + 44]
        mov dword ptr [road_teleport_test_seen + 12], edx
        mov edx, dword ptr [eax + 48]
        mov dword ptr [road_teleport_test_seen + 16], edx
        mov edx, dword ptr [eax + 12]
        add edx, 12
        mov dword ptr [edx], 77
        // Exercise the bridge's PUSHAD/PUSHFD preservation.
        mov eax, 0deadbeefh
        mov ecx, 0c001c0deh
        mov edx, 0badf00dh
        mov ebx, 012345678h
        mov esi, 087654321h
        mov edi, 055aa55aah
        mov ebp, 033cc33cch
        stc
        ret
    }
}

extern "C" __declspec(naked) void road_teleport_test_native_adjust() {
    __asm {
        mov dword ptr [road_teleport_test_seen + 32], ecx
        mov eax, dword ptr [esp + 4]
        mov dword ptr [road_teleport_test_seen + 36], eax
        mov eax, dword ptr [esp + 8]
        mov dword ptr [road_teleport_test_seen + 40], eax
        mov edx, dword ptr [esp + 12]
        mov dword ptr [road_teleport_test_seen + 44], edx
        mov eax, dword ptr [esp + 8]
        add eax, 1000
        stc
        ret 0ch
    }
}

extern "C" void road_teleport_adjust_bridge_after(
    gfx2::RoadAdjustSaved* saved) noexcept {
    road_teleport_test_seen[6] = saved->eax;
    road_teleport_test_seen[7] = saved->flags;
    // Production post-call observation leaves the native return value intact.
}

extern "C" __declspec(naked) uint32_t road_teleport_test_invoke(
    uint32_t, uint32_t, uint32_t, uint32_t) {
    __asm {
        mov eax, dword ptr [esp + 4]
        mov edx, dword ptr [esp + 8]
        mov ecx, dword ptr [esp + 12]
        mov ebx, dword ptr [esp + 16]
        push ebx
        push ecx
        push edx
        mov ecx, eax
        call road_teleport_adjust_bridge
        pushfd
        pop edx
        mov dword ptr [road_teleport_test_seen + 48], edx
        ret 10h
    }
}

int main() {
    road_teleport_adjust_original = reinterpret_cast<uintptr_t>(
        &road_teleport_test_native_adjust);
    const uint32_t result = road_teleport_test_invoke(
        0x12345678, 0, 12, 0x23456780);
    if (road_teleport_test_seen[2] != 0 ||
        road_teleport_test_seen[3] != 12 ||
        road_teleport_test_seen[4] != 0x23456780 ||
        road_teleport_test_seen[8] != 0x12345678 ||
        road_teleport_test_seen[9] != 0 ||
        road_teleport_test_seen[10] != 77 ||
        road_teleport_test_seen[11] != 0x23456780 ||
        result != 1077 || road_teleport_test_seen[6] != 1077 ||
        (road_teleport_test_seen[7] & 1u) == 0 ||
        (road_teleport_test_seen[12] & 1u) == 0) {
        std::fprintf(stderr,
            "road teleport bridge mismatch: entry=(%u,%u,%08X) native=(%08X,%u,%u,%08X) result=%u after=%u flags=%08X/%08X\n",
            road_teleport_test_seen[2], road_teleport_test_seen[3],
            road_teleport_test_seen[4],
            road_teleport_test_seen[8], road_teleport_test_seen[9],
            road_teleport_test_seen[10], road_teleport_test_seen[11], result,
            road_teleport_test_seen[6], road_teleport_test_seen[7],
            road_teleport_test_seen[12]);
        return 1;
    }
    std::puts("road teleport production bridge ABI PASS");
    return 0;
}
