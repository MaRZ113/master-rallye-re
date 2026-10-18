#include "crash_log.hpp"
#include <windows.h>
#include <cstdio>
#include <cstring>

namespace gfx2 {
namespace {
wchar_t g_path[MAX_PATH * 2];
volatile LONG g_events = 0;
uintptr_t g_exe_begin = 0, g_exe_end = 0;
PVOID g_handler = nullptr;

bool severe(DWORD code) {
    return code == EXCEPTION_ACCESS_VIOLATION || code == EXCEPTION_ILLEGAL_INSTRUCTION || code == EXCEPTION_INT_DIVIDE_BY_ZERO ||
           code == EXCEPTION_PRIV_INSTRUCTION || code == EXCEPTION_IN_PAGE_ERROR || code == 0xC0000374 || code == 0xC0000409;
}

bool readable(const void* p, void* out, size_t n) {
    __try { std::memcpy(out, p, n); return true; } __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
}

void put(HANDLE f, const char* text) {
    DWORD written = 0;
    WriteFile(f, text, static_cast<DWORD>(std::strlen(text)), &written, nullptr);
}

void describe(char* out, size_t cap, uintptr_t address) {
    HMODULE module = nullptr;
    if (GetModuleHandleExW(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS | GET_MODULE_HANDLE_EX_FLAG_UNCHANGED_REFCOUNT,
                           reinterpret_cast<LPCWSTR>(address), &module) && module) {
        wchar_t name[MAX_PATH]{};
        GetModuleFileNameW(module, name, MAX_PATH);
        const wchar_t* base = wcsrchr(name, L'\\');
        std::snprintf(out, cap, "%ls+0x%08zX", base ? base + 1 : name, address - reinterpret_cast<uintptr_t>(module));
    } else {
        std::snprintf(out, cap, "?");
    }
}

LONG CALLBACK handler(EXCEPTION_POINTERS* info) {
    if (!info || !info->ExceptionRecord || !info->ContextRecord) return EXCEPTION_CONTINUE_SEARCH;
    const auto& rec = *info->ExceptionRecord;
    const uintptr_t eip = reinterpret_cast<uintptr_t>(rec.ExceptionAddress);
    if (!severe(rec.ExceptionCode) || eip < g_exe_begin || eip >= g_exe_end) return EXCEPTION_CONTINUE_SEARCH;
    if (InterlockedIncrement(&g_events) > 40) return EXCEPTION_CONTINUE_SEARCH;
    HANDLE f = CreateFileW(g_path, FILE_APPEND_DATA, FILE_SHARE_READ | FILE_SHARE_WRITE, nullptr, OPEN_ALWAYS, FILE_ATTRIBUTE_NORMAL, nullptr);
    if (f == INVALID_HANDLE_VALUE) return EXCEPTION_CONTINUE_SEARCH;
    char line[512], where[160];
    const CONTEXT& c = *info->ContextRecord;
    describe(where, sizeof(where), eip);
    std::snprintf(line, sizeof(line), "=== exception %ld code=0x%08lX at 0x%08zX (%s) thread=%lu\r\n", static_cast<long>(g_events),
                  rec.ExceptionCode, eip, where, GetCurrentThreadId());
    put(f, line);
    if (rec.ExceptionCode == EXCEPTION_ACCESS_VIOLATION && rec.NumberParameters >= 2) {
        std::snprintf(line, sizeof(line), "access: %s address 0x%08zX\r\n", rec.ExceptionInformation[0] == 0 ? "read" : rec.ExceptionInformation[0] == 1 ? "write" : "execute",
                      static_cast<size_t>(rec.ExceptionInformation[1]));
        put(f, line);
    }
#if defined(_M_IX86)
    std::snprintf(line, sizeof(line), "eax=%08lX ebx=%08lX ecx=%08lX edx=%08lX esi=%08lX edi=%08lX ebp=%08lX esp=%08lX eflags=%08lX\r\n",
                  c.Eax, c.Ebx, c.Ecx, c.Edx, c.Esi, c.Edi, c.Ebp, c.Esp, c.EFlags);
    put(f, line);
    put(f, "stack (esp upward; module+rva where the value points into a module):\r\n");
    for (int i = 0; i < 48; ++i) {
        DWORD value = 0;
        if (!readable(reinterpret_cast<const void*>(static_cast<uintptr_t>(c.Esp) + i * 4), &value, 4)) break;
        char tag[160];
        describe(tag, sizeof(tag), value);
        std::snprintf(line, sizeof(line), "  [esp+%02X] %08lX  %s\r\n", i * 4, value, tag[0] == '?' ? "" : tag);
        put(f, line);
    }
    put(f, "ebp chain (return addresses):\r\n");
    uintptr_t ebp = c.Ebp;
    for (int i = 0; i < 16 && ebp; ++i) {
        DWORD frame[2]{};
        if (!readable(reinterpret_cast<const void*>(ebp), frame, 8)) break;
        char tag[160];
        describe(tag, sizeof(tag), frame[1]);
        std::snprintf(line, sizeof(line), "  ebp=%08zX ret=%08lX %s\r\n", ebp, frame[1], tag);
        put(f, line);
        if (frame[0] <= ebp) break;
        ebp = frame[0];
    }
#endif
    put(f, "\r\n");
    CloseHandle(f);
    return EXCEPTION_CONTINUE_SEARCH;
}
}

void install_crash_log(const std::wstring& config_path) noexcept {
    if (g_handler) return;
    if (GetPrivateProfileIntW(L"Diagnostics", L"CrashLog", 0, config_path.c_str()) != 1) return;
    HMODULE exe = GetModuleHandleW(nullptr);
    auto* dos = reinterpret_cast<const IMAGE_DOS_HEADER*>(exe);
    auto* nt = reinterpret_cast<const IMAGE_NT_HEADERS*>(reinterpret_cast<const char*>(exe) + dos->e_lfanew);
    g_exe_begin = reinterpret_cast<uintptr_t>(exe);
    g_exe_end = g_exe_begin + nt->OptionalHeader.SizeOfImage;
    const std::wstring dir = config_path.substr(0, config_path.find_last_of(L"\\/"));
    swprintf(g_path, sizeof(g_path) / sizeof(g_path[0]), L"%ls\\MRRRenderer\\logs\\crash-%lu.txt", dir.c_str(), GetCurrentProcessId());
    g_handler = AddVectoredExceptionHandler(1, handler);
}
}
