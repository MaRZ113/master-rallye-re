#define WIN32_LEAN_AND_MEAN
#define NOMINMAX
#include <windows.h>
#include <dinput.h>

#include <array>
#include <iostream>
#include <iterator>
#include <string>

int wmain(int argc, wchar_t** argv) {
    if (argc != 2) return 2;
    HMODULE proxy = LoadLibraryW(argv[1]);
    if (!proxy) { std::wcerr << L"proxy load failed: " << GetLastError() << L"\n"; return 3; }

    wchar_t system_dir[MAX_PATH]{};
    const UINT length = GetSystemDirectoryW(system_dir, MAX_PATH);
    if (!length || length >= MAX_PATH) return 4;
    std::wstring system_path(system_dir, length);
    if (!system_path.empty() && system_path.back() != L'\\') system_path.push_back(L'\\');
    system_path += L"dinput8.dll";
    HMODULE system = LoadLibraryExW(system_path.c_str(), nullptr, LOAD_LIBRARY_SEARCH_SYSTEM32);
    if (!system) return 5;

    constexpr const char* names[] = {
        "DirectInput8Create", "DllCanUnloadNow", "DllGetClassObject",
        "DllRegisterServer", "DllUnregisterServer", "GetdfDIJoystick"
    };
    for (unsigned ordinal = 1; ordinal <= std::size(names); ++ordinal) {
        FARPROC by_name = GetProcAddress(proxy, names[ordinal - 1]);
        FARPROC by_ordinal = GetProcAddress(proxy, MAKEINTRESOURCEA(ordinal));
        FARPROC target_name = GetProcAddress(system, names[ordinal - 1]);
        FARPROC target_ordinal = GetProcAddress(system, MAKEINTRESOURCEA(ordinal));
        if (!by_name || by_name != by_ordinal || !target_name || target_name != target_ordinal)
            return 6;
    }

    using CreateFn = HRESULT (WINAPI*)(HINSTANCE, DWORD, REFIID, LPVOID*, LPUNKNOWN);
    const auto proxy_create = reinterpret_cast<CreateFn>(GetProcAddress(proxy, "DirectInput8Create"));
    const auto system_create = reinterpret_cast<CreateFn>(GetProcAddress(system, "DirectInput8Create"));
    GUID invalid_iid{};
    invalid_iid.Data1 = 0xFFFFFFFFu;
    LPVOID proxy_out = nullptr, system_out = nullptr;
    const HRESULT proxy_hr = proxy_create(GetModuleHandleW(nullptr), DIRECTINPUT_VERSION,
                                           invalid_iid, &proxy_out, nullptr);
    const HRESULT system_hr = system_create(GetModuleHandleW(nullptr), DIRECTINPUT_VERSION,
                                             invalid_iid, &system_out, nullptr);
    if (proxy_hr != system_hr || proxy_out != system_out) return 7;

    using CanUnloadFn = HRESULT (WINAPI*)();
    const auto proxy_can_unload = reinterpret_cast<CanUnloadFn>(GetProcAddress(proxy, "DllCanUnloadNow"));
    const auto system_can_unload = reinterpret_cast<CanUnloadFn>(GetProcAddress(system, "DllCanUnloadNow"));
    if (!proxy_can_unload || proxy_can_unload() != system_can_unload()) return 9;

    using GetClassFn = HRESULT (WINAPI*)(REFCLSID, REFIID, LPVOID*);
    const auto proxy_get_class = reinterpret_cast<GetClassFn>(GetProcAddress(proxy, "DllGetClassObject"));
    const auto system_get_class = reinterpret_cast<GetClassFn>(GetProcAddress(system, "DllGetClassObject"));
    if (!proxy_get_class || !system_get_class) return 10;
    GUID unknown_clsid{};
    unknown_clsid.Data1 = 0xFFFFFFFFu;
    constexpr GUID iid_unknown = {0x00000000u, 0x0000u, 0x0000u,
        {0xC0u, 0x00u, 0x00u, 0x00u, 0x00u, 0x00u, 0x00u, 0x46u}};
    LPVOID proxy_class = nullptr, system_class = nullptr;
    const HRESULT proxy_class_hr = proxy_get_class(unknown_clsid, iid_unknown, &proxy_class);
    const HRESULT system_class_hr = system_get_class(unknown_clsid, iid_unknown, &system_class);
    if (proxy_class_hr != system_class_hr || proxy_class != system_class) return 11;

    using FormatFn = LPCDIDATAFORMAT (WINAPI*)();
    const auto proxy_format = reinterpret_cast<FormatFn>(GetProcAddress(proxy, "GetdfDIJoystick"));
    const auto system_format = reinterpret_cast<FormatFn>(GetProcAddress(system, "GetdfDIJoystick"));
    if (!proxy_format || proxy_format() != system_format()) return 8;

    std::cout << "DINPUT8_FORWARD_PASS named=6 ordinal=6 directinput8create=system-match joystick-format=system-match\n";
    FreeLibrary(system);
    FreeLibrary(proxy);
    return 0;
}
