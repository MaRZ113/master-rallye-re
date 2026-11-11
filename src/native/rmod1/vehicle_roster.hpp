#pragma once
// VehicleRoster (Vehicle Manager phase 2, docs/vehicle-manager/DESIGN.md).
//
// Runs in dinput8 DllMain(PROCESS_ATTACH). DINPUT8 is a static import of the retail MRallye.exe, so this happens
// before the first game instruction and before the lazily created vehicle registry singleton (0x6F5ED4): the same
// moment the external suspended launcher used. It installs the active roster written by the Vehicle Manager:
//
//   <game>\MRMods\Vehicles\active\roster.mrvr   MRVR v1: native payload at its fixed private address, the RVP1 table
//                                                (exact preimages) and the MRVC descriptor it must publish
//   <game>\MRMods\Vehicles\active\resources\     loose game files that differ from or add to the retail data
//
// Every check happens before the first write; any failure leaves the image untouched and the game runs stock.
// Only kernel32 memory/file calls are used (loader-lock safe). The MRVC address is published in this process'
// MR_VEHICLE_REGISTRY_DESCRIPTOR variable, exactly where the launcher used to put it for the child, so every
// consumer (Extra Options, Randomizer, runtime core) keeps working unchanged.
//
// Resources: the EXE's CreateFileA and GetFileAttributesA import slots are redirected for game-relative paths that
// exist in the overlay. Menu Builder reads the CreateFileA slot when it hooks the VFS call site (0x64D573), so it
// chains through this provider without a second patch of the same site.
#ifndef WIN32_LEAN_AND_MEAN
#define WIN32_LEAN_AND_MEAN
#endif
#ifndef NOMINMAX
#define NOMINMAX
#endif
#include <windows.h>
#include <algorithm>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <cctype>
#include <string>
#include <vector>

namespace vehicle_roster {

inline constexpr uint32_t kImageBase = 0x00400000;
inline constexpr uint32_t kRegistrySingleton = 0x006F5ED4;
inline constexpr uint32_t kIatCreateFileA = 0x0068F1E0;
inline constexpr uint32_t kIatGetFileAttributesA = 0x0068F100;
inline constexpr uint32_t kHeaderSize = 256;
inline constexpr uint32_t kRvpHeaderSize = 120;
inline constexpr uint32_t kRvpOpHeaderSize = 12;

struct State {
    char game_dir[MAX_PATH]{};       // with trailing backslash
    char overlay_dir[MAX_PATH]{};    // ...\MRMods\Vehicles\active\resources\ (with trailing backslash)
    std::vector<std::string> overlay; // sorted, lower case, forward slashes, game-relative
    FARPROC create_file = nullptr, get_attributes = nullptr;
    bool installed = false;
    // Save guard: class of every physical ID the running roster offers (-1 = not offered), first ID per class.
    std::vector<int> id_class; int class_first[4]{0, 7, 14, -1}; bool save_guard = false; const char* class_source = "retail";
};
inline State& state() { static State s; return s; }

inline void log(const char* text) {
    char path[MAX_PATH]{};
    if (std::snprintf(path, sizeof(path), "%sMRallyeVehicleRoster.log", state().game_dir) <= 0) return;
    HANDLE f = CreateFileA(path, FILE_APPEND_DATA, FILE_SHARE_READ | FILE_SHARE_WRITE, nullptr, OPEN_ALWAYS, FILE_ATTRIBUTE_NORMAL, nullptr);
    if (f == INVALID_HANDLE_VALUE) return;
    DWORD written = 0;
    WriteFile(f, text, DWORD(std::strlen(text)), &written, nullptr);
    WriteFile(f, "\r\n", 2, &written, nullptr);
    CloseHandle(f);
}

inline uint32_t u32(const std::vector<uint8_t>& b, size_t at) { uint32_t v = 0; std::memcpy(&v, b.data() + at, 4); return v; }
inline uint16_t u16(const std::vector<uint8_t>& b, size_t at) { uint16_t v = 0; std::memcpy(&v, b.data() + at, 2); return v; }

inline bool read_file(const char* path, std::vector<uint8_t>& out, uint64_t limit) {
    out.clear();
    HANDLE f = CreateFileA(path, GENERIC_READ, FILE_SHARE_READ, nullptr, OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, nullptr);
    if (f == INVALID_HANDLE_VALUE) return false;
    LARGE_INTEGER size{};
    bool ok = GetFileSizeEx(f, &size) && size.QuadPart > 0 && uint64_t(size.QuadPart) <= limit;
    if (ok) {
        out.resize(size_t(size.QuadPart));
        DWORD got = 0;
        ok = ReadFile(f, out.data(), DWORD(out.size()), &got, nullptr) && got == out.size();
    }
    CloseHandle(f);
    if (!ok) out.clear();
    return ok;
}

inline uint64_t fnv64(const uint8_t* p, size_t n) { uint64_t h = 0xcbf29ce484222325ull; for (size_t i = 0; i < n; ++i) { h ^= p[i]; h *= 0x100000001b3ull; } return h; }

struct Op { uint32_t rva; uint16_t length; uint8_t flags, page; const uint8_t* before; const uint8_t* after; };

inline bool readable_image(uint32_t va, size_t n, bool code) {
    MEMORY_BASIC_INFORMATION m{};
    if (VirtualQuery(reinterpret_cast<void*>(uintptr_t(va)), &m, sizeof(m)) != sizeof(m) || m.State != MEM_COMMIT || m.Type != MEM_IMAGE ||
        m.AllocationBase != reinterpret_cast<void*>(uintptr_t(kImageBase)) || (m.Protect & PAGE_GUARD)) return false;
    if (uintptr_t(va) + n > uintptr_t(m.BaseAddress) + m.RegionSize) return false;
    const DWORD p = m.Protect & 0xff;
    const bool exec = p == PAGE_EXECUTE || p == PAGE_EXECUTE_READ || p == PAGE_EXECUTE_READWRITE || p == PAGE_EXECUTE_WRITECOPY;
    return code ? exec : (p != PAGE_NOACCESS);
}

// ---- resource overlay -------------------------------------------------------------------------------------------
inline void collect(const std::string& dir, const std::string& rel, std::vector<std::string>& out, unsigned depth) {
    if (depth > 16 || out.size() > 100000) return;
    WIN32_FIND_DATAA d{};
    HANDLE h = FindFirstFileA((dir + rel + "*").c_str(), &d);
    if (h == INVALID_HANDLE_VALUE) return;
    do {
        if (!std::strcmp(d.cFileName, ".") || !std::strcmp(d.cFileName, "..")) continue;
        std::string name = rel + d.cFileName;
        if (d.dwFileAttributes & FILE_ATTRIBUTE_DIRECTORY) collect(dir, name + "\\", out, depth + 1);
        else {
            for (auto& c : name) { if (c == '\\') c = '/'; else c = char(std::tolower(static_cast<unsigned char>(c))); }
            out.push_back(name);
        }
    } while (FindNextFileA(h, &d));
    FindClose(h);
}

// Game-relative key of a path, or empty: relative paths, or absolute ones inside the game folder.
inline std::string overlay_key(const char* path) {
    if (!path || !*path) return {};
    std::string p(path);
    for (auto& c : p) { if (c == '\\') c = '/'; else c = char(std::tolower(static_cast<unsigned char>(c))); }
    std::string game(state().game_dir);
    for (auto& c : game) { if (c == '\\') c = '/'; else c = char(std::tolower(static_cast<unsigned char>(c))); }
    if (p.size() > 2 && p[1] == ':') {
        if (p.compare(0, game.size(), game)) return {};
        p.erase(0, game.size());
    }
    while (p.compare(0, 2, "./") == 0) p.erase(0, 2);
    if (p.empty() || p[0] == '/' || p.find("..") != std::string::npos) return {};
    return p;
}
inline bool redirect(const char* path, char* out, size_t size) {
    const auto& s = state();
    if (s.overlay.empty()) return false;
    const auto key = overlay_key(path);
    if (key.empty() || !std::binary_search(s.overlay.begin(), s.overlay.end(), key)) return false;
    std::string rel = key;
    for (auto& c : rel) if (c == '/') c = '\\';
    return std::snprintf(out, size, "%s%s", s.overlay_dir, rel.c_str()) > 0;
}

// ---- save guard (ROSTER_FALLBACK_ID0) -----------------------------------------------------------------------------
// The owner's decision: a saved car the installed roster does not offer must never crash the game. PlayerState.xml
// is served through a sanitized private copy whenever it holds such an ID; the save itself is not rewritten (the
// game's next normal save stores the replacement). Class-scoped keys (PlayerT<c>Car<n>) get the first car of their
// class, because a car of another class breaks that class list; every other key gets ID0.
inline bool memory_readable(uint32_t va, size_t n) {
    MEMORY_BASIC_INFORMATION m{};
    return va && VirtualQuery(reinterpret_cast<void*>(uintptr_t(va)), &m, sizeof(m)) == sizeof(m) && m.State == MEM_COMMIT &&
           !(m.Protect & (PAGE_GUARD | PAGE_NOACCESS)) && uintptr_t(va) + n <= uintptr_t(m.BaseAddress) + m.RegionSize;
}
inline void load_classes() {
    auto& s = state();
    s.id_class.assign(25, -1);
    for (int id = 0; id < 25; ++id) s.id_class[size_t(id)] = id < 7 ? 0 : id < 14 ? 1 : 2;   // retail: T1 0..6, T2 7..13, T3 14..24
    s.class_first[0] = 0; s.class_first[1] = 7; s.class_first[2] = 14; s.class_first[3] = -1; s.class_source = "retail";
    char value[32]{};
    const DWORD n = GetEnvironmentVariableA("MR_VEHICLE_REGISTRY_DESCRIPTOR", value, sizeof(value));
    if (!n || n >= sizeof(value)) return;
    const uint32_t va = uint32_t(std::strtoul(value, nullptr, 16));
    uint32_t d[11]{};
    if (!memory_readable(va, sizeof(d))) return;
    std::memcpy(d, reinterpret_cast<void*>(uintptr_t(va)), sizeof(d));
    if (std::memcmp(d, "MRVC", 4) || d[1] != 1 || !d[3] || d[3] > 4096 || !d[5] || d[5] > 4) return;
    uint32_t counts[4]{}, tables[4]{};
    if (!memory_readable(d[7], d[5] * 4) || !memory_readable(d[8], d[5] * 4)) return;
    std::memcpy(counts, reinterpret_cast<void*>(uintptr_t(d[7])), d[5] * 4);
    std::memcpy(tables, reinterpret_cast<void*>(uintptr_t(d[8])), d[5] * 4);
    std::vector<int> classes(d[3], -1); int first[4]{-1, -1, -1, -1};
    for (uint32_t c = 0; c < d[5]; ++c) {
        if (counts[c] > d[3] || !memory_readable(tables[c], counts[c] * 4)) return;
        for (uint32_t i = 0; i < counts[c]; ++i) {
            uint32_t id = 0; std::memcpy(&id, reinterpret_cast<void*>(uintptr_t(tables[c] + i * 4)), 4);
            if (id >= d[3]) return;
            classes[id] = int(c); if (first[c] < 0) first[c] = int(id);
        }
    }
    s.id_class = std::move(classes);
    for (int c = 0; c < 4; ++c) s.class_first[c] = first[c];
    s.class_source = "registry";
}
// Integer value of `Name="key"` lines; returns the class scope (0..3) of PlayerT<c>Car keys, 4 for unscoped car keys,
// -1 for anything that is not a car ID.
inline int car_key_scope(const std::string& name) {
    auto ends = [&](const char* tail) { const size_t n = std::strlen(tail); return name.size() > n && !name.compare(name.size() - n, n, tail); };
    for (const char* prefix : {"RallyeCup/PlayerT", "MasterRallye/PlayerT"}) {
        const size_t n = std::strlen(prefix);
        if (!name.compare(0, n, prefix) && name.size() > n + 4 && name[n] >= '1' && name[n] <= '4' && !name.compare(n + 1, 3, "Car") &&
            name.find_first_not_of("0123456789", n + 4) == std::string::npos) return name[n] - '1';
    }
    auto starts = [&](const char* head) { return !name.compare(0, std::strlen(head), head); };
    auto digits_after = [&](const char* head) { const size_t n = std::strlen(head); if (!starts(head) || name.size() == n) return false;
        for (size_t i = n; i < name.size(); ++i) if (name[i] < '0' || name[i] > '9') return false; return true; };
    if (digits_after("Frontend/QuickRace/Car") || digits_after("Frontend/Network/Car")) return 4;
    if (starts("MasterRallye/Car") && ends("/CarID")) return 4;
    return -1;
}
inline bool sanitize_save(const char* original, char* out, size_t out_size) {
    auto& s = state();
    std::vector<uint8_t> raw;
    if (!read_file(original, raw, 16ull * 1024 * 1024)) return false;
    std::string text(raw.begin(), raw.end()), fixed;
    fixed.reserve(text.size());
    unsigned changes = 0; size_t at = 0;
    while (at < text.size()) {
        size_t end = text.find('\n', at); if (end == std::string::npos) end = text.size(); else ++end;
        std::string line = text.substr(at, end - at); at = end;
        const size_t name_at = line.find("Name=\"");
        const size_t type_at = line.find("Type=\"Int\" Value=\"");
        if (name_at != std::string::npos && type_at != std::string::npos) {
            const size_t name_end = line.find('"', name_at + 6);
            const std::string name = line.substr(name_at + 6, name_end - name_at - 6);
            const int scope = car_key_scope(name);
            if (scope >= 0) {
                const size_t v = type_at + 18, v_end = line.find('"', v);
                const long id = std::strtol(line.substr(v, v_end - v).c_str(), nullptr, 10);
                const bool offered = id >= 0 && size_t(id) < s.id_class.size() && s.id_class[size_t(id)] >= 0;
                const bool in_class = scope == 4 || (offered && s.id_class[size_t(id)] == scope);
                if (!offered || !in_class) {
                    const int replacement = scope < 4 && s.class_first[scope] >= 0 ? s.class_first[scope] : 0;
                    line.replace(v, v_end - v, std::to_string(replacement));
                    char note[200]{};
                    std::snprintf(note, sizeof(note), "ROSTER_FALLBACK_ID0 key=%s id=%ld -> %d (%s)", name.c_str(), id, replacement,
                                  offered ? "other class" : "not in the installed roster");
                    log(note); ++changes;
                }
            }
        }
        fixed += line;
    }
    if (!changes) return false;
    char dir[MAX_PATH]{}, file[MAX_PATH]{};
    std::snprintf(dir, sizeof(dir), "%sMRMods", s.game_dir); CreateDirectoryA(dir, nullptr);
    std::snprintf(dir, sizeof(dir), "%sMRMods\\Vehicles", s.game_dir); CreateDirectoryA(dir, nullptr);
    std::snprintf(file, sizeof(file), "%sMRMods\\Vehicles\\PlayerState.read.xml", s.game_dir);
    HANDLE h = CreateFileA(file, GENERIC_WRITE, 0, nullptr, CREATE_ALWAYS, FILE_ATTRIBUTE_NORMAL, nullptr);
    if (h == INVALID_HANDLE_VALUE) return false;
    DWORD written = 0;
    const bool ok = WriteFile(h, fixed.data(), DWORD(fixed.size()), &written, nullptr) && written == fixed.size();
    CloseHandle(h);
    if (!ok) return false;
    char note[160]{};
    std::snprintf(note, sizeof(note), "SAVE_GUARD served a corrected copy of PlayerState.xml (%u car IDs, classes from %s); the save file is unchanged", changes, s.class_source);
    log(note);
    return std::snprintf(out, out_size, "%s", file) > 0;
}

using CreateFileAFn = HANDLE(WINAPI*)(LPCSTR, DWORD, DWORD, LPSECURITY_ATTRIBUTES, DWORD, DWORD, HANDLE);
using GetFileAttributesAFn = DWORD(WINAPI*)(LPCSTR);
inline HANDLE WINAPI create_file(LPCSTR path, DWORD access, DWORD share, LPSECURITY_ATTRIBUTES sa, DWORD disposition, DWORD flags, HANDLE templ) {
    const auto real = reinterpret_cast<CreateFileAFn>(state().create_file);
    if (!(access & (GENERIC_WRITE | FILE_WRITE_DATA | FILE_APPEND_DATA | DELETE)) && disposition == OPEN_EXISTING) {
        char target[MAX_PATH * 2]{};
        try {
            if (state().save_guard && overlay_key(path) == "datagame/playerstate.xml") {
                if (sanitize_save(path, target, sizeof(target))) return real(target, access, share, sa, disposition, flags, templ);
            } else if (redirect(path, target, sizeof(target))) return real(target, access, share, sa, disposition, flags, templ);
        } catch (...) {}
    }
    return real(path, access, share, sa, disposition, flags, templ);
}
inline DWORD WINAPI get_attributes(LPCSTR path) {
    const auto real = reinterpret_cast<GetFileAttributesAFn>(state().get_attributes);
    char target[MAX_PATH * 2]{};
    try { if (redirect(path, target, sizeof(target))) return real(target); } catch (...) {}
    return real(path);
}
inline bool hook_slot(uint32_t slot, void* hook, FARPROC& original) {
    FARPROC current = nullptr;
    if (!readable_image(slot, 4, false)) return false;
    std::memcpy(&current, reinterpret_cast<void*>(uintptr_t(slot)), 4);
    if (!current) return false;
    DWORD old = 0, ignored = 0;
    if (!VirtualProtect(reinterpret_cast<void*>(uintptr_t(slot)), 4, PAGE_READWRITE, &old)) return false;
    original = current;
    std::memcpy(reinterpret_cast<void*>(uintptr_t(slot)), &hook, 4);
    VirtualProtect(reinterpret_cast<void*>(uintptr_t(slot)), 4, old, &ignored);
    return true;
}

// ---- install ----------------------------------------------------------------------------------------------------
inline bool install_native(const std::vector<uint8_t>& b, char* why, size_t why_size) {
    auto fail = [&](const char* text) { std::snprintf(why, why_size, "%s", text); return false; };
    if (b.size() < kHeaderSize || std::memcmp(b.data(), "MRVR", 4) || u32(b, 4) != 1 || u32(b, 8) != kHeaderSize) return fail("ROSTER_FORMAT_UNSUPPORTED");
    const uint32_t ext_address = u32(b, 16), ext_alloc = u32(b, 20), ext_size = u32(b, 24), rw_count = u32(b, 28);
    const uint32_t descriptor_va = u32(b, 96), rvp_offset = u32(b, 144), rvp_size = u32(b, 148), ext_offset = u32(b, 152), ext_size2 = u32(b, 156);
    uint64_t digest = 0; std::memcpy(&digest, b.data() + 160, 8);
    if (fnv64(b.data() + kHeaderSize, b.size() - kHeaderSize) != digest) return fail("ROSTER_DIGEST_MISMATCH");
    if (rw_count > 8 || ext_size != ext_size2 || !ext_size || ext_size > ext_alloc || ext_alloc > 64u * 1024 * 1024 ||
        uint64_t(rvp_offset) + rvp_size > b.size() || uint64_t(ext_offset) + ext_size > b.size() || rvp_size < kRvpHeaderSize)
        return fail("ROSTER_LAYOUT_INVALID");
    // RVP1 table (the launcher's format): identity, then operations with exact preimages.
    const std::vector<uint8_t> rvp(b.begin() + rvp_offset, b.begin() + rvp_offset + rvp_size);
    if (std::memcmp(rvp.data(), "MRVP", 4) || u16(rvp, 4) != 1 || u16(rvp, 6) != 0x014c || u32(rvp, 8) != kImageBase) return fail("RVP_HEADER_UNSUPPORTED");
    const uint32_t count = u32(rvp, 20);
    if (count > 4096) return fail("RVP_COUNT_INVALID");
    std::vector<Op> ops;
    size_t at = kRvpHeaderSize;
    for (uint32_t i = 0; i < count; ++i) {
        if (at + kRvpOpHeaderSize > rvp.size()) return fail("RVP_TRUNCATED");
        Op op{u32(rvp, at + 4), u16(rvp, at + 8), rvp[at + 10], rvp[at + 11], nullptr, nullptr};
        at += kRvpOpHeaderSize;
        if (!op.length || op.length > 8192 || at + size_t(op.length) * 2 > rvp.size()) return fail("RVP_TRUNCATED");
        op.before = rvp.data() + at; op.after = rvp.data() + at + op.length; at += size_t(op.length) * 2;
        if (op.flags == 1) continue;                       // file-only (PE header reconstruction)
        if ((op.flags != 0 && op.flags != 2) || (op.page != 1 && op.page != 2)) return fail("RVP_OPERATION_UNSUPPORTED");
        ops.push_back(op);
    }
    // 1. Every precondition, no writes.
    uint32_t singleton = 1;
    if (!readable_image(kRegistrySingleton, 4, false)) return fail("REGISTRY_SINGLETON_UNREADABLE");
    std::memcpy(&singleton, reinterpret_cast<void*>(uintptr_t(kRegistrySingleton)), 4);
    if (singleton) return fail("REGISTRY_ALREADY_CONSTRUCTED");
    for (const auto& op : ops) {
        const uint32_t va = kImageBase + op.rva;
        if (!readable_image(va, op.length, op.page == 1)) return fail("PATCH_TARGET_NOT_IN_RETAIL_IMAGE");
        if (std::memcmp(reinterpret_cast<void*>(uintptr_t(va)), op.before, op.length)) {
            std::snprintf(why, why_size, "PREIMAGE_MISMATCH rva=0x%x (not the retail EXE, or another module patched it)", op.rva);
            return false;
        }
    }
    MEMORY_BASIC_INFORMATION vacant{};
    if (VirtualQuery(reinterpret_cast<void*>(uintptr_t(ext_address)), &vacant, sizeof(vacant)) != sizeof(vacant) || vacant.State != MEM_FREE ||
        uintptr_t(vacant.BaseAddress) + vacant.RegionSize < uintptr_t(ext_address) + ext_alloc) {
        std::snprintf(why, why_size, "PRIVATE_ARENA_OCCUPIED address=0x%08x size=0x%x (a DLL was mapped there; stock game)", ext_address, ext_alloc);
        return false;
    }
    // 2. Private payload.
    auto* arena = static_cast<uint8_t*>(VirtualAlloc(reinterpret_cast<void*>(uintptr_t(ext_address)), ext_alloc, MEM_RESERVE | MEM_COMMIT, PAGE_READWRITE));
    if (arena != reinterpret_cast<uint8_t*>(uintptr_t(ext_address))) { if (arena) VirtualFree(arena, 0, MEM_RELEASE); return fail("PRIVATE_ARENA_ALLOCATION_FAILED"); }
    std::memcpy(arena, b.data() + ext_offset, ext_size);
    if (std::memcmp(reinterpret_cast<void*>(uintptr_t(descriptor_va)), b.data() + 100, 44)) { VirtualFree(arena, 0, MEM_RELEASE); return fail("DESCRIPTOR_MISMATCH"); }
    DWORD old = 0;
    if (!VirtualProtect(arena, ext_alloc, PAGE_EXECUTE_READ, &old)) { VirtualFree(arena, 0, MEM_RELEASE); return fail("ARENA_PROTECT_FAILED"); }
    for (uint32_t i = 0; i < rw_count; ++i) {
        const uint32_t off = u32(b, 32 + i * 8), size = u32(b, 36 + i * 8);
        if (!size) continue;
        if (uint64_t(off) + size > ext_alloc || !VirtualProtect(arena + off, size, PAGE_READWRITE, &old)) { VirtualFree(arena, 0, MEM_RELEASE); return fail("ARENA_DATA_PAGE_FAILED"); }
    }
    FlushInstructionCache(GetCurrentProcess(), arena, ext_size);
    // 3. Image operations; a failure after the first write cannot be undone safely -> terminate (launcher policy).
    for (const auto& op : ops) {
        void* target = reinterpret_cast<void*>(uintptr_t(kImageBase + op.rva));
        DWORD previous = 0, ignored = 0;
        if (!VirtualProtect(target, op.length, op.page == 1 ? PAGE_EXECUTE_READWRITE : PAGE_READWRITE, &previous)) {
            log("FATAL VirtualProtect failed during installation; terminating to avoid a half-patched game");
            TerminateProcess(GetCurrentProcess(), 0xE003);
        }
        std::memcpy(target, op.after, op.length);
        VirtualProtect(target, op.length, previous, &ignored);
    }
    FlushInstructionCache(GetCurrentProcess(), nullptr, 0);
    for (const auto& op : ops)
        if (std::memcmp(reinterpret_cast<void*>(uintptr_t(kImageBase + op.rva)), op.after, op.length)) {
            log("FATAL post-install verification failed; terminating");
            TerminateProcess(GetCurrentProcess(), 0xE004);
        }
    wchar_t value[32]{};
    std::swprintf(value, 32, L"0x%x", descriptor_va);
    SetEnvironmentVariableW(L"MR_VEHICLE_REGISTRY_DESCRIPTOR", value);
    std::snprintf(why, why_size, "INSTALLED operations=%u payload=%u at 0x%08x descriptor=0x%08x records=%u", unsigned(ops.size()), ext_size, ext_address,
                  descriptor_va, u32(b, 112));
    return true;
}

inline void attach(HINSTANCE self) {
    auto& s = state();
    try {
        char module[MAX_PATH]{};
        const DWORD n = GetModuleFileNameA(self, module, MAX_PATH);
        if (!n || n >= MAX_PATH) return;
        char* slash = std::strrchr(module, '\\');
        if (!slash) return;
        slash[1] = 0;
        std::snprintf(s.game_dir, sizeof(s.game_dir), "%s", module);
        // The executable must be the one this DLL serves (a static importer at the retail base).
        if (reinterpret_cast<uintptr_t>(GetModuleHandleW(nullptr)) != kImageBase) return;
        char roster[MAX_PATH]{};
        std::snprintf(roster, sizeof(roster), "%sMRMods\\Vehicles\\active\\roster.mrvr", s.game_dir);
        if (GetFileAttributesA(roster) != INVALID_FILE_ATTRIBUTES) {
            std::vector<uint8_t> bytes;
            char why[256]{};
            if (!read_file(roster, bytes, 64ull * 1024 * 1024)) log("ROSTER_SKIPPED roster.mrvr unreadable");
            else if (!install_native(bytes, why, sizeof(why))) { char line[320]{}; std::snprintf(line, sizeof(line), "ROSTER_NOT_INSTALLED %s; stock game", why); log(line); }
            else {
                log(why);
                s.installed = true;
                std::snprintf(s.overlay_dir, sizeof(s.overlay_dir), "%sMRMods\\Vehicles\\active\\resources\\", s.game_dir);
                collect(s.overlay_dir, "", s.overlay, 0);
                std::sort(s.overlay.begin(), s.overlay.end());
                s.overlay.erase(std::unique(s.overlay.begin(), s.overlay.end()), s.overlay.end());
            }
        }
        // The save guard always runs: with this roster, with a launcher-installed registry (descriptor already
        // published), or for the retail roster when no vehicle package is installed at all.
        load_classes();
        s.save_guard = true;
        const bool files = hook_slot(kIatCreateFileA, reinterpret_cast<void*>(&create_file), s.create_file) &&
            (s.overlay.empty() || hook_slot(kIatGetFileAttributesA, reinterpret_cast<void*>(&get_attributes), s.get_attributes));
        if (s.installed || !files) {
            char line[200]{};
            std::snprintf(line, sizeof(line), "RESOURCE_OVERLAY files=%u import_hooks=%s save_guard_classes=%s", unsigned(s.overlay.size()),
                          files ? "installed" : "FAILED", s.class_source);
            log(line);
        }
    } catch (...) { log("ROSTER_EXCEPTION stock game"); }
}

} // namespace vehicle_roster
