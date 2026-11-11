#define WIN32_LEAN_AND_MEAN
#define NOMINMAX
#define _WIN32_WINNT 0x0601
#include <windows.h>
#include <dinput.h>

#include <array>
#include <string>

#include "rmod2_inprocess.hpp"
#include "vehicle_roster.hpp"
#if defined(RMOD_EXTRA_OPTIONS)
#include "extra_options_runtime.hpp"
#include "extra_ghost.hpp"
#endif
#if defined(RMOD_MENU_BUILDER)
#include "menu_builder_runtime.hpp"
#endif

namespace {

INIT_ONCE g_resolve_once = INIT_ONCE_STATIC_INIT;
HMODULE g_system_dinput8 = nullptr;
FARPROC g_exports[6]{};
bool g_resolve_ok = false;
INIT_ONCE g_boot_once = INIT_ONCE_STATIC_INIT;
volatile LONG g_boot_state = 0; // 0 NotStarted, 1 Initializing, 2 Ready, 3 Failed

constexpr const char* kExportNames[] = {
    "DirectInput8Create", "DllCanUnloadNow", "DllGetClassObject",
    "DllRegisterServer", "DllUnregisterServer", "GetdfDIJoystick"
};

BOOL CALLBACK resolve_system_dinput8(PINIT_ONCE, PVOID, PVOID*) {
    wchar_t system_dir[MAX_PATH]{};
    const UINT length = GetSystemDirectoryW(system_dir, MAX_PATH);
    if (!length || length >= MAX_PATH) return TRUE;
    std::wstring path(system_dir, length);
    if (!path.empty() && path.back() != L'\\') path.push_back(L'\\');
    path += L"dinput8.dll";

    // The full System32/SysWOW64 path prevents resolving this local proxy again.
    g_system_dinput8 = LoadLibraryExW(path.c_str(), nullptr, LOAD_LIBRARY_SEARCH_SYSTEM32);
    if (!g_system_dinput8) return TRUE;
    wchar_t loaded_path[MAX_PATH]{};
    const DWORD loaded_length = GetModuleFileNameW(g_system_dinput8, loaded_path, MAX_PATH);
    if (!loaded_length || loaded_length >= MAX_PATH ||
        CompareStringOrdinal(path.c_str(), -1, loaded_path, -1, TRUE) != CSTR_EQUAL ||
        g_system_dinput8 == GetModuleHandleW(L"dinput8.dll")) {
        FreeLibrary(g_system_dinput8);
        g_system_dinput8 = nullptr;
        return TRUE;
    }
    for (unsigned i = 0; i < 6; ++i) {
        g_exports[i] = GetProcAddress(g_system_dinput8, kExportNames[i]);
        if (!g_exports[i]) {
            FreeLibrary(g_system_dinput8);
            g_system_dinput8 = nullptr;
            for (auto& item : g_exports) item = nullptr;
            return TRUE;
        }
    }
    g_resolve_ok = true;
    return TRUE;
}

FARPROC system_export(unsigned index) {
    if (!InitOnceExecuteOnce(&g_resolve_once, resolve_system_dinput8, nullptr, nullptr) ||
        !g_resolve_ok || index >= std::size(g_exports)) return nullptr;
    return g_exports[index];
}

BOOL CALLBACK initialize_randomizer_once(PINIT_ONCE, PVOID, PVOID*) {
    InterlockedExchange(&g_boot_state, 1);
    char error[512]{};
    if (rmod2_boot::initialize(error, static_cast<unsigned>(sizeof(error)))) {
#if defined(RMOD_EXTRA_OPTIONS)
        extra_runtime::initialize();
#endif
        InterlockedExchange(&g_boot_state, 2);
    } else {
        InterlockedExchange(&g_boot_state, 3);
    }
#if defined(RMOD_EXTRA_OPTIONS)
    // Ghost/difficulty hooks are disjoint from the Randomizer plan and need no runtime core.
    extra_ghost::initialize();
#endif
#if defined(RMOD_MENU_BUILDER)
    // Frontend layouts are independent of the Randomizer boot result and of Extra Options;
    // they run after both so a shared provider (Extra Options appearance) is already initialized.
    menu_builder::initialize();
#endif
    return TRUE; // failure is final for this process; DirectInput still forwards.
}

} // namespace

extern "C" BOOL WINAPI DllMain(HINSTANCE instance, DWORD reason, LPVOID) {
    // Vehicle Manager roster (docs/vehicle-manager/DESIGN.md): before the first game instruction, kernel32 only.
    // Absent roster = no effect. Thread notifications stay inert.
    if (reason == DLL_PROCESS_ATTACH) vehicle_roster::attach(instance);
    return TRUE;
}

#if defined(RMOD_EXTRA_SDK_BINDING)
// x86 marker for a private SDK-aware build. It advertises the checked binding
// protocol, not a gameplay qualification or broad version compatibility.
extern "C" unsigned WINAPI MRExtraSdkBindingAbi() { return 0x45583101u; }
#endif

extern "C" HRESULT WINAPI ProxyDirectInput8Create(
    HINSTANCE instance, DWORD version, REFIID iid, LPVOID* output, LPUNKNOWN outer) {
    using Fn = HRESULT (WINAPI*)(HINSTANCE, DWORD, REFIID, LPVOID*, LPUNKNOWN);
    const auto function = reinterpret_cast<Fn>(system_export(0));
    if (function) InitOnceExecuteOnce(&g_boot_once, initialize_randomizer_once, nullptr, nullptr);
    return function ? function(instance, version, iid, output, outer) : E_FAIL;
}

extern "C" HRESULT WINAPI ProxyDllCanUnloadNow() {
    using Fn = HRESULT (WINAPI*)();
    const auto function = reinterpret_cast<Fn>(system_export(1));
    return function ? function() : E_FAIL;
}

extern "C" HRESULT WINAPI ProxyDllGetClassObject(REFCLSID clsid, REFIID iid, LPVOID* output) {
    using Fn = HRESULT (WINAPI*)(REFCLSID, REFIID, LPVOID*);
    const auto function = reinterpret_cast<Fn>(system_export(2));
    return function ? function(clsid, iid, output) : CLASS_E_CLASSNOTAVAILABLE;
}

extern "C" HRESULT WINAPI ProxyDllRegisterServer() {
    using Fn = HRESULT (WINAPI*)();
    const auto function = reinterpret_cast<Fn>(system_export(3));
    return function ? function() : E_FAIL;
}

extern "C" HRESULT WINAPI ProxyDllUnregisterServer() {
    using Fn = HRESULT (WINAPI*)();
    const auto function = reinterpret_cast<Fn>(system_export(4));
    return function ? function() : E_FAIL;
}

extern "C" LPCDIDATAFORMAT WINAPI ProxyGetdfDIJoystick() {
    using Fn = LPCDIDATAFORMAT (WINAPI*)();
    const auto function = reinterpret_cast<Fn>(system_export(5));
    return function ? function() : nullptr;
}
