#define WIN32_LEAN_AND_MEAN
#define NOMINMAX
#include <windows.h>
#include <dinput.h>

#include <array>
#include <fstream>
#include <iostream>
#include <iterator>
#include <string>
#include <thread>

int wmain(int argc, wchar_t** argv) {
    if (argc != 2) return 2;
    HMODULE proxy = LoadLibraryW(argv[1]);
    if (!proxy) return 3;
    wchar_t system_dir[MAX_PATH]{};
    const UINT n = GetSystemDirectoryW(system_dir, MAX_PATH);
    if (!n || n >= MAX_PATH) return 4;
    std::wstring system_path(system_dir, n);
    if (!system_path.empty() && system_path.back() != L'\\') system_path.push_back(L'\\');
    system_path += L"dinput8.dll";
    HMODULE system = LoadLibraryExW(system_path.c_str(), nullptr, LOAD_LIBRARY_SEARCH_SYSTEM32);
    if (!system) return 5;
    using CreateFn = HRESULT (WINAPI*)(HINSTANCE, DWORD, REFIID, LPVOID*, LPUNKNOWN);
    auto p = reinterpret_cast<CreateFn>(GetProcAddress(proxy, "DirectInput8Create"));
    auto s = reinterpret_cast<CreateFn>(GetProcAddress(system, "DirectInput8Create"));
    if (!p || !s) return 6;
    GUID invalid{}; invalid.Data1 = 0xFFFFFFFFu;
    std::array<HRESULT, 8> results{};
    std::array<LPVOID, 8> outputs{};
    std::array<std::thread, 8> callers;
    for (std::size_t i = 0; i < callers.size(); ++i)
        callers[i] = std::thread([&, i] { results[i] = p(GetModuleHandleW(nullptr), DIRECTINPUT_VERSION, invalid, &outputs[i], nullptr); });
    for (auto& caller : callers) caller.join();
    LPVOID expected_output = nullptr;
    const HRESULT expected = s(GetModuleHandleW(nullptr), DIRECTINPUT_VERSION, invalid, &expected_output, nullptr);
    if (expected_output != nullptr) return 11;
    for (std::size_t i = 0; i < results.size(); ++i)
        if (results[i] != expected || outputs[i] != nullptr) return 7;

    wchar_t exe[MAX_PATH]{};
    const DWORD path_length = GetModuleFileNameW(nullptr, exe, MAX_PATH);
    if (!path_length || path_length >= MAX_PATH) return 8;
    std::wstring log_path(exe, path_length);
    const auto slash = log_path.find_last_of(L"\\/");
    if (slash == std::wstring::npos) return 9;
    log_path.resize(slash + 1); log_path += L"MRallyeRandomizer-boot.log";
    std::ifstream input(log_path);
    const std::string log((std::istreambuf_iterator<char>(input)), std::istreambuf_iterator<char>());
    auto count = [&](const std::string& marker) {
        std::size_t found = 0, at = 0;
        while ((at = log.find(marker, at)) != std::string::npos) { ++found; at += marker.size(); }
        return found;
    };
    if (count("BOOT_B_PROXY_LOADED") != 1 || count("BOOT_B_FAILED") != 1 || count("NATIVE_INSTALL_COMPLETE") != 0) return 10;
    std::cout << "BOOT_B_INIT_ONCE_PASS concurrent_calls=8 invalid_host_fail_closed=1 directinput_forwarding=8/8\n";
    FreeLibrary(system); FreeLibrary(proxy);
    return 0;
}
