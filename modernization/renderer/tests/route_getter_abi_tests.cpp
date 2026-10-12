#include "physics_probe_model.hpp"

#include <cstdint>
#include <cstring>

#define CHECK(condition) do { if (!(condition)) return __LINE__; } while (0)

struct CapturedCall {
    uint32_t eax;
    uint32_t ecx;
    uint32_t edx;
    uint32_t ebx;
    uint32_t esi;
    uint32_t edi;
    uint32_t ebp;
    uint32_t esp;
    uint32_t eflags;
};

struct CapturedPair {
    CapturedCall direct;
    CapturedCall bridged;
};

static_assert(sizeof(CapturedCall) == 9 * sizeof(uint32_t));
static_assert(offsetof(CapturedPair, bridged) == sizeof(CapturedCall));

extern "C" {
volatile uint32_t abi_native_return = 0;
volatile uint32_t abi_native_calls = 0;
volatile uint32_t abi_native_arguments[2] = {};
volatile uint32_t abi_native_this_values[2] = {};
volatile uint32_t abi_observer_calls = 0;
volatile uint32_t abi_observer_route = 0;
volatile uint32_t abi_observer_manager = 0;
volatile uint32_t abi_observer_rejected = 0;
}

extern "C" __declspec(naked) void abi_test_native_getter() {
    __asm {
        // Native contract: ECX is the object, [ESP+4] is one stack argument.
        mov eax, dword ptr [esp + 4]
        mov edx, dword ptr [abi_native_calls]
        cmp edx, 2
        jae native_recorded
        mov dword ptr [abi_native_arguments + edx * 4], eax
        mov dword ptr [abi_native_this_values + edx * 4], ecx
        inc dword ptr [abi_native_calls]
    native_recorded:
        mov ecx, 055667788h
        mov edx, 099AABBCCh
        mov eax, dword ptr [abi_native_return]
        // Give the harness observable callee flags; RET 4 leaves them intact.
        cmp dword ptr [esp + 4], 0
        ret 4
    }
}

extern "C" void __cdecl abi_test_observer(uint32_t route_object,
                                           uint32_t recovery_manager) {
    ++abi_observer_calls;
    abi_observer_route = route_object;
    abi_observer_manager = recovery_manager;
    abi_observer_rejected = gfx2::physics_probe::pointer_shape(route_object) ? 0u : 1u;
    // Deliberately damage volatile state; the bridge must restore the getter's.
    __asm {
        mov eax, 0BADF00Dh
        mov ecx, 0C001D00Dh
        mov edx, 0DEADC0DEh
        stc
    }
}

extern "C" __declspec(naked) void abi_test_route_getter_bridge() {
    __asm {
        // ABI-equivalent test target: the same stack/register sequence as the
        // production bridge, substituting only a local native getter symbol.
        push dword ptr [esp + 4]
        call abi_test_native_getter
        pushfd
        pushad
        mov eax, dword ptr [esp + 28]
        mov edx, dword ptr [esp + 4]
        push edx
        push eax
        call abi_test_observer
        add esp, 8
        popad
        popfd
        ret 4
    }
}

extern "C" __declspec(naked) void abi_run_pair(uint32_t,
                                                CapturedPair*) {
    __asm {
        push ebp
        push ebx
        push esi
        push edi
        mov edi, dword ptr [esp + 24]

        // Baseline: the caller's original argument is already pushed.
        push dword ptr [esp + 20]
        mov ecx, 011223344h
        mov ebx, 022334455h
        mov esi, 033445566h
        mov ebp, 044556677h
        call abi_test_native_getter
        mov dword ptr [edi + 0], eax
        mov dword ptr [edi + 4], ecx
        mov dword ptr [edi + 8], edx
        mov dword ptr [edi + 12], ebx
        mov dword ptr [edi + 16], esi
        mov dword ptr [edi + 20], edi
        mov dword ptr [edi + 24], ebp
        mov eax, esp
        mov dword ptr [edi + 28], eax
        pushfd
        pop eax
        mov dword ptr [edi + 32], eax

        // Patched-call model: same caller stack and register inputs.
        push dword ptr [esp + 20]
        mov ecx, 011223344h
        mov ebx, 022334455h
        mov esi, 033445566h
        mov ebp, 044556677h
        call abi_test_route_getter_bridge
        mov dword ptr [edi + 36], eax
        mov dword ptr [edi + 40], ecx
        mov dword ptr [edi + 44], edx
        mov dword ptr [edi + 48], ebx
        mov dword ptr [edi + 52], esi
        mov dword ptr [edi + 56], edi
        mov dword ptr [edi + 60], ebp
        mov eax, esp
        mov dword ptr [edi + 64], eax
        pushfd
        pop eax
        mov dword ptr [edi + 68], eax

        pop edi
        pop esi
        pop ebx
        pop ebp
        ret
    }
}

static int run_case(uint32_t argument, uint32_t native_return) {
    abi_native_return = native_return;
    abi_native_calls = 0;
    abi_native_arguments[0] = abi_native_arguments[1] = 0;
    abi_native_this_values[0] = abi_native_this_values[1] = 0;
    abi_observer_calls = 0;
    abi_observer_route = 0xFFFFFFFFu;
    abi_observer_manager = 0xFFFFFFFFu;
    abi_observer_rejected = 0;

    CapturedPair pair{};
    abi_run_pair(argument, &pair);
    CHECK(std::memcmp(&pair.direct, &pair.bridged, sizeof(CapturedCall)) == 0);
    CHECK(pair.direct.eax == native_return);
    CHECK(pair.direct.esp == pair.bridged.esp);
    CHECK(pair.direct.eflags == pair.bridged.eflags);
    CHECK(abi_native_calls == 2);
    CHECK(abi_native_arguments[0] == argument && abi_native_arguments[1] == argument);
    CHECK(abi_native_this_values[0] == 0x11223344u &&
          abi_native_this_values[1] == 0x11223344u);
    CHECK(abi_observer_calls == 1);
    CHECK(abi_observer_route == native_return);
    CHECK(abi_observer_manager == 0x33445566u);
    CHECK(abi_observer_rejected ==
          (gfx2::physics_probe::pointer_shape(native_return) ? 0u : 1u));
    return 0;
}

int main() {
    int result = run_case(0x13572468u, 0xA1B2C3D4u);
    if (result) return result;

    // NULL is forwarded to the observer and rejected by the same pointer-shape
    // predicate used before the production snapshot reader dereferences a route.
    result = run_case(0u, 0u);
    if (result) return result;

    // Repeated distinct arguments expose stack drift that a one-shot test misses.
    for (uint32_t i = 1; i <= 128; ++i) {
        result = run_case(0x10000u + i * 4u, 0x70000000u + i * 4u);
        if (result) return result;
    }
    return 0;
}
