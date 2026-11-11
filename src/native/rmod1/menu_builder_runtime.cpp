#define WIN32_LEAN_AND_MEAN
#define NOMINMAX
#include <windows.h>
#include "menu_builder_runtime.hpp"
#include <array>
#include <cmath>
#include <cstdarg>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <map>
#include <mutex>
#include <sstream>
#include <string>
#include <vector>

namespace menu_builder {
namespace {
namespace fs = std::filesystem;

// ---- retail ABI (MRallye.exe bf8aef32…) ---------------------------------------------------------
constexpr uintptr_t kKey = 0x4d0580, kBroker = 0x4d8ec0, kGetInt = 0x4d6760, kGetBool = 0x4d6520, kPutInt = 0x4d8000,
                    kPutBool = 0x4d7aa0, kPutName = 0x4d85f0, kStringCtor = 0x4d11d0, kScreenName = 0x449cf0,
                    kRequestScreen = 0x45d910, kGetCommand = 0x45d930, kEggManager = 0x4f6310, kFindEgg = 0x4f5eb0,
                    kHostInit = 0x462ab0;
constexpr uintptr_t kEggManagerGlobal = 0x6f96fc;
constexpr uintptr_t kCreateFileSite = 0x64d573;   // FF 15 [0x68F1E0] CALL CreateFileA in the VFS open 0x64D530
constexpr uintptr_t kScreenNameSite = 0x45d865;   // CALL 0x449CF0 in the screen change 0x45D6C0
constexpr uintptr_t kHostInitSlot = 0x690540;     // gaFEScreenGraphicsMainAI vtable 0x69052C [5] = init
constexpr int kRetailScreens = 0x36, kHostScreen = 0x33, kFirstCustom = 64;

struct Api { uintptr_t va; std::array<unsigned char, 8> bytes; };
constexpr Api kApis[] = {
    {0x4d0580, {0x8b,0x44,0x24,0x04,0x56,0x8b,0xf1,0x50}}, {0x4d8ec0, {0xa1,0x10,0x94,0x6f,0x00,0x83,0xec,0x20}},
    {0x4d6760, {0x8b,0x44,0x24,0x04,0x83,0xec,0x20,0x55}}, {0x4d6520, {0x8b,0x44,0x24,0x04,0x83,0xec,0x20,0x55}},
    {0x4d8000, {0x83,0xec,0x24,0x8b,0x44,0x24,0x28,0x55}}, {0x4d7aa0, {0x83,0xec,0x24,0x8b,0x44,0x24,0x28,0x55}},
    {0x4d85f0, {0x83,0xec,0x24,0x8b,0x44,0x24,0x28,0x55}}, {0x4d11d0, {0x53,0x8b,0xd9,0x56,0x6a,0x00,0xc7,0x03}},
    {0x449cf0, {0x51,0x8b,0x44,0x24,0x0c,0x56,0x85,0xc0}}, {0x45d910, {0x56,0x8b,0xf1,0x6a,0x00,0xe8,0xe6,0x0d}},
    {0x45d930, {0x83,0xec,0x5c,0x53,0x55,0x56,0x57,0x8b}}, {0x4f6310, {0x51,0xa1,0xfc,0x96,0x6f,0x00,0x53,0x33}},
    {0x4f5eb0, {0x8b,0x44,0x24,0x04,0x8b,0x49,0x1c,0x50}}, {0x462ab0, {0x6a,0xff,0x68,0x8b,0x6f,0x68,0x00,0x64}},
};

template <class T> T fn(uintptr_t va) { return reinterpret_cast<T>(va); }

struct Helper { int screen; int pending; bool ready; };  // 0x45D610: per-screen command helper (screen AI +0xC)

// ---- layout tables --------------------------------------------------------------------------------
struct Rect { float x0 = 0, y0 = 0, x1 = 0, y1 = 0; bool empty() const { return x1 <= x0 || y1 <= y0; } };
struct Action {
    std::string type = "native";
    std::map<std::string, std::string> args;
    int num(const char* k, int fallback = 0) const { auto it = args.find(k); return it == args.end() ? fallback : std::atoi(it->second.c_str()); }
    std::string str(const char* k) const { auto it = args.find(k); return it == args.end() ? std::string() : it->second; }
};
struct Button { int id = 0; std::string egg; bool enabled = true; Rect local; Action action; std::map<std::string, Rect> hit; };
struct Screen {
    std::string scene; int id = -1; bool custom = false; std::string source; unsigned long long fnv = 0;
    std::map<std::string, std::string> variants; int focus = 0; bool has_back = false; Action back;
    std::vector<Button> buttons;
    int base_state = 0; // 0 unknown, 1 ok, -1 base changed (redirect disabled)
    const Button* find(int bid) const { for (auto& b : buttons) if (b.id == bid) return &b; return nullptr; }
};
struct Layout { std::string name; bool mouse = true; std::vector<std::string> aspects; std::vector<Screen> screens; };

Layout g_layout;
fs::path g_root, g_dir;
bool g_installed = false, g_live_dump = true;
std::mutex g_log_mutex;
// Frontend state (game thread only).
int g_current = -1;                 // last screen index passed to GetScreenName by the screen change
std::string g_variant = "4:3";      // variant served for the current scene
int g_mode = 0;                     // renderer interface mode 0 Stock / 1 Centered4x3 / 2 PreserveMargins
double g_ratio = 4.0 / 3.0;
Helper* g_last_helper = nullptr;
std::vector<int> g_stack;           // navigate.screen return stack
int g_forward_screen = -1, g_forward_command = 0;  // native.forward: command delivered on the target's first tick
POINT g_last_mouse{-1, -1};
bool g_lbutton = false, g_rbutton = false;
HWND g_window = nullptr;
std::map<std::string, MRMenuActionV1> g_extensions;
// Diagnostics: scripted frontend test (MenuBuilder.ini [Diagnostics] AutoTest=<file>), run on the game thread.
struct Step { std::string op; std::vector<std::string> args; };
std::vector<Step> g_steps;
size_t g_step = 0;
ULONGLONG g_step_due = 0;
int g_test_fail = 0, g_test_pass = 0;
unsigned char* g_trampoline = nullptr;

void log(const std::string& line) noexcept {
    try {
        std::lock_guard<std::mutex> lock(g_log_mutex);
        std::ofstream f(g_root / "MenuBuilder" / "MenuBuilder.log", std::ios::app);
        SYSTEMTIME t; GetLocalTime(&t);
        char stamp[32]; std::snprintf(stamp, sizeof(stamp), "%02u:%02u:%02u.%03u ", t.wHour, t.wMinute, t.wSecond, t.wMilliseconds);
        f << stamp << line << '\n';
    } catch (...) {}
}
std::string fmt(const char* format, ...) {
    char buf[1024]; va_list a; va_start(a, format); std::vsnprintf(buf, sizeof(buf), format, a); va_end(a); return buf;
}

bool read_mem(uintptr_t p, void* out, size_t n) noexcept {
    SIZE_T done = 0;
    return p && ReadProcessMemory(GetCurrentProcess(), reinterpret_cast<const void*>(p), out, n, &done) && done == n;
}

// ---- Broker -----------------------------------------------------------------------------------------
uint32_t key(const char* s) { uint32_t r = 0; fn<void(__thiscall*)(uint32_t*, const char*)>(kKey)(&r, s); return r; }
void* broker() { return fn<void*(__cdecl*)()>(kBroker)(); }
int get_int(const char* s) { auto k = key(s); return fn<int(__thiscall*)(void*, uint32_t*)>(kGetInt)(broker(), &k); }
bool get_bool(const char* s) { auto k = key(s); return fn<bool(__thiscall*)(void*, uint32_t*)>(kGetBool)(broker(), &k); }
void put_int(const char* s, int v) { auto k = key(s); fn<void(__thiscall*)(void*, uint32_t*, int)>(kPutInt)(broker(), &k, v); }
void put_bool(const char* s, bool v) { auto k = key(s); fn<void(__thiscall*)(void*, uint32_t*, int)>(kPutBool)(broker(), &k, v ? 1 : 0); }
void put_name(const char* s, const char* value) { auto k = key(s), v = key(value); fn<void(__thiscall*)(void*, uint32_t*, uint32_t*)>(kPutName)(broker(), &k, &v); }

// Live egg position (en2d object at egg+0x4C, translation row at +0x54/+0x58; same fields the
// StandardButton tick copies into Frontend/ButtonPulser/Position).
bool egg_position(const std::string& name, float& x, float& y) {
    fn<void(__cdecl*)()>(kEggManager)();
    uintptr_t manager = 0;
    if (!read_mem(kEggManagerGlobal, &manager, 4) || !manager) return false;
    uint32_t k = key(name.c_str());
    auto egg = reinterpret_cast<uintptr_t>(fn<void*(__thiscall*)(void*, uint32_t*)>(kFindEgg)(reinterpret_cast<void*>(manager), &k));
    uintptr_t en2d = 0;
    float xy[2]{};
    if (!egg || !read_mem(egg + 0x4c, &en2d, 4) || !en2d || !read_mem(en2d + 0x54, xy, sizeof(xy))) return false;
    x = xy[0]; y = xy[1];
    return true;
}

// ---- configuration ---------------------------------------------------------------------------------
std::vector<std::string> split(const std::string& line, char sep) {
    std::vector<std::string> out; std::string cur;
    for (char c : line) { if (c == sep) { out.push_back(cur); cur.clear(); } else if (c != '\r') cur += c; }
    out.push_back(cur);
    return out;
}
Rect parse_rect(const std::string& s) {
    Rect r; std::istringstream in(s); in >> r.x0 >> r.y0 >> r.x1 >> r.y1; return r;
}
Action parse_action(const std::vector<std::string>& t, size_t from) {
    Action a;
    if (from < t.size()) a.type = t[from];
    for (size_t i = from + 1; i < t.size(); ++i) {
        auto eq = t[i].find('=');
        if (eq != std::string::npos) a.args[t[i].substr(0, eq)] = t[i].substr(eq + 1);
    }
    return a;
}
Screen* screen_by_scene(const std::string& scene) {
    for (auto& s : g_layout.screens) if (_stricmp(s.scene.c_str(), scene.c_str()) == 0) return &s;
    return nullptr;
}
Screen* screen_by_id(int id) {
    for (auto& s : g_layout.screens) if (s.id == id) return &s;
    return nullptr;
}

bool load_layout(const fs::path& dir) {
    std::ifstream f(dir / "runtime.txt", std::ios::binary);
    if (!f) { log("LAYOUT_MISSING runtime.txt"); return false; }
    std::string line; int lineno = 0; bool header = false, end = false;
    while (std::getline(f, line)) {
        ++lineno;
        auto t = split(line, '\t');
        if (t.empty() || t[0].empty()) continue;
        const auto& k = t[0];
        if (k == "MRMENU") { header = t.size() > 1 && t[1] == "1"; if (!header) { log("LAYOUT_FORMAT unsupported"); return false; } }
        else if (!header) { log("LAYOUT_FORMAT missing header"); return false; }
        else if (k == "layout" && t.size() > 1) g_layout.name = t[1];
        else if (k == "mouse" && t.size() > 1) g_layout.mouse = t[1] == "1";
        else if (k == "aspects") g_layout.aspects.assign(t.begin() + 1, t.end());
        else if (k == "screen" && t.size() >= 6) {
            Screen s; s.scene = t[1]; s.id = std::atoi(t[2].c_str()); s.custom = t[3] == "custom"; s.source = t[4];
            s.fnv = std::strtoull(t[5].c_str(), nullptr, 16);
            if (s.custom ? s.id < kFirstCustom || s.id > 255 : s.id < 0 || s.id >= kRetailScreens) { log(fmt("LAYOUT_SCREEN_ID invalid line %d", lineno)); return false; }
            g_layout.screens.push_back(s);
        } else if (t.size() >= 2 && screen_by_scene(t[1])) {
            auto* s = screen_by_scene(t[1]);
            if (k == "variant" && t.size() >= 4) s->variants[t[2]] = t[3];
            else if (k == "focus" && t.size() >= 3) s->focus = std::atoi(t[2].c_str());
            else if (k == "back" && t.size() >= 3) { s->has_back = true; s->back = parse_action(t, 2); }
            else if (k == "button" && t.size() >= 7) {
                Button b; b.id = std::atoi(t[2].c_str()); b.egg = t[3]; b.enabled = t[4] == "1"; b.local = parse_rect(t[5]);
                b.action = parse_action(t, 6);
                s->buttons.push_back(b);
            } else if (k == "hit" && t.size() >= 5) {
                for (auto& b : s->buttons) if (b.id == std::atoi(t[2].c_str())) b.hit[t[3]] = parse_rect(t[4]);
            }
        } else if (k == "end") end = true;
    }
    if (!end) { log("LAYOUT_FORMAT truncated (no end)"); return false; }
    return true;
}

// ---- renderer interface mode and window ------------------------------------------------------------
int renderer_mode() {
    HMODULE d3d8 = GetModuleHandleW(L"d3d8.dll");
    if (!d3d8) return 0;
    wchar_t path[MAX_PATH]{};
    GetModuleFileNameW(d3d8, path, MAX_PATH);
    if (_wcsicmp(fs::path(path).parent_path().c_str(), g_root.c_str()) != 0) return 0;  // system d3d8: Stock
    const auto ini = (g_root / "MRRRenderer.ini").wstring();
    const int version = GetPrivateProfileIntW(L"General", L"ConfigVersion", 1, ini.c_str());
    if (version >= 2) {
        const int preset = GetPrivateProfileIntW(L"Quality", L"Preset", 2, ini.c_str());
        if (preset == 0) return 0;
        if (preset == 1) return 2;
        const int wide = GetPrivateProfileIntW(L"Quality", L"Widescreen", 0, ini.c_str());
        return wide >= 0 && wide <= 2 ? wide : 0;
    }
    wchar_t mode[64]{};
    GetPrivateProfileStringW(L"Widescreen", L"InterfaceMode", L"Stock", mode, 64, ini.c_str());
    if (!_wcsicmp(mode, L"1") || !_wcsicmp(mode, L"Centered4x3")) return 1;
    if (!_wcsicmp(mode, L"2") || !_wcsicmp(mode, L"PreserveMargins")) return 2;
    return 0;
}

BOOL CALLBACK find_window(HWND w, LPARAM out) {
    DWORD pid = 0; GetWindowThreadProcessId(w, &pid);
    if (pid == GetCurrentProcessId() && IsWindowVisible(w) && !GetWindow(w, GW_OWNER)) {
        RECT r{}; GetClientRect(w, &r);
        auto* best = reinterpret_cast<HWND*>(out);
        RECT b{}; if (*best) GetClientRect(*best, &b);
        if (!*best || (r.right * r.bottom) > (b.right * b.bottom)) *best = w;
    }
    return TRUE;
}
// The process owns several wsUIWindow windows (the original game window, the renderer's presentation
// window, a debug window); the frontend is shown in the largest visible one. Re-checked every 500 ms
// because the presentation window can be created after the first frontend scene is loaded.
HWND game_window() {
    static ULONGLONG checked = 0;
    const ULONGLONG now = GetTickCount64();
    if (g_window && IsWindow(g_window) && now - checked < 500) return g_window;
    checked = now;
    HWND best = nullptr;
    EnumWindows(find_window, reinterpret_cast<LPARAM>(&best));
    if (best) g_window = best;
    return g_window;
}

double half_extra() { return g_mode == 0 ? 0.0 : std::max(0.0, (480.0 * g_ratio - 640.0) / 2.0); }

void refresh_view() {
    g_mode = renderer_mode();
    RECT r{};
    if (HWND w = game_window(); w && GetClientRect(w, &r) && r.right > 0 && r.bottom > 0) g_ratio = double(r.right) / r.bottom;
}

std::string choose_variant(const Screen& s) {
    if (g_mode == 0 || s.variants.empty()) return s.variants.count("4:3") ? "4:3" : (s.variants.empty() ? "4:3" : s.variants.begin()->first);
    std::string best; double diff = 1e9;
    for (auto& [aspect, path] : s.variants) {
        auto p = aspect.find(':');
        double ratio = p == std::string::npos ? 4.0 / 3.0 : std::atof(aspect.substr(0, p).c_str()) / std::atof(aspect.substr(p + 1).c_str());
        if (std::abs(ratio - g_ratio) < diff) { diff = std::abs(ratio - g_ratio); best = aspect; }
    }
    return best;
}

// PreserveMargins reference rules (renderer research margin-rules.json): authored point → direction.
constexpr struct { short x, y; signed char dir; } kMarginRules[] = {
    {15,150,-1},{15,390,-1},{20,135,-1},{20,150,-1},{20,175,-1},{20,350,-1},{20,360,-1},{20,365,-1},{20,375,-1},{20,380,-1},
    {20,410,-1},{20,415,-1},{23,370,-1},{440,390,1},{450,160,1},{450,400,1},{475,390,1},{485,160,1},{485,400,1},{490,210,1},
    {490,440,1},{490,450,1},{510,390,1},{520,160,1},{520,400,1},{540,408,1},{540,423,1},{545,40,1},{545,280,1},{545,390,1},
    {550,179,1},{550,194,1},{550,419,1},{550,434,1},{555,160,1},{555,400,1},{565,75,1},{565,315,1},{570,22,1},{570,262,1},
    {580,390,1},{590,160,1},{590,400,1},{601,52,1},{601,292,1},{610,408,1},{610,423,1},{620,179,1},{620,194,1},{620,419,1},{620,434,1},
};
// Same classification as the renderer (ui_margins.cpp margin_direction): exact points, then the left band
// x in [25,106], y in [19,100) or [259,340) for every packet.
int margin_dir(float x, float y) {
    if (g_mode != 2) return 0;
    for (auto& r : kMarginRules) if (r.x == x && r.y == y) return r.dir;
    if (x >= 25 && x <= 106 && ((y >= 19 && y < 100) || (y >= 259 && y < 340))) return -1;
    return 0;
}

// ---- scene redirection (VFS CreateFileA) ---------------------------------------------------------------
unsigned long long fnv64_file(const char* path) {
    std::ifstream f(path, std::ios::binary);
    if (!f) return 0;
    unsigned long long h = 0xcbf29ce484222325ull;
    char buf[65536];
    while (f) { f.read(buf, sizeof(buf)); for (std::streamsize i = 0; i < f.gcount(); ++i) { h ^= static_cast<unsigned char>(buf[i]); h *= 0x100000001b3ull; } }
    return h;
}

bool base_ok(Screen& s, const char* request_path) {
    if (s.custom) return true;
    if (s.base_state != 0) return s.base_state > 0;
    const DWORD attr = GetFileAttributesA(request_path);
    const bool loose = attr != INVALID_FILE_ATTRIBUTES && !(attr & FILE_ATTRIBUTE_DIRECTORY);
    if (s.source == "archive") s.base_state = loose ? -1 : 1;
    else if (s.source == "loose") s.base_state = loose && fnv64_file(request_path) == s.fnv ? 1 : -1;
    else s.base_state = -1;
    if (s.base_state < 0)
        log(fmt("BASE_CHANGED scene=%s compiled_from=%s now=%s: layout page disabled, native page kept", s.scene.c_str(), s.source.c_str(), loose ? "loose" : "archive"));
    return s.base_state > 0;
}

// Extension availability decides whether a button is served enabled.
bool extension_available(const std::string& name);

std::string serve_xml(const Screen& s, const std::string& variant) {
    auto it = s.variants.find(variant);
    if (it == s.variants.end()) return {};
    fs::path file = g_dir / fs::path(it->second);
    std::vector<std::string> disable;
    for (auto& b : s.buttons)
        if (b.action.type == "extension" && !extension_available(b.action.str("ext"))) disable.push_back(b.egg);
    if (disable.empty()) return file.string();
    // Unavailable providers: serve a cached copy with the button's Enabled flag cleared, so the native
    // StandardButton draws it greyed and GetCommand refuses it (UI/Enabled) instead of a dead button.
    std::ifstream in(file, std::ios::binary);
    std::string xml((std::istreambuf_iterator<char>(in)), {});
    for (auto& egg : disable) {
        auto start = xml.find("<Egg Name=\"" + egg + "\">");
        if (start == std::string::npos) continue;
        auto stop = xml.find("</Egg>", start);
        // First "Enabled" value of the egg (the StandardButton flag); tolerant to the tag's spacing.
        auto en = xml.find("Name=\"Enabled\"", start);
        if (en == std::string::npos || en > stop) continue;
        auto close = xml.find('>', en), val = xml.find("Value=\"True\"", en);
        if (val != std::string::npos && val < close) xml.replace(val, 12, "Value=\"False\"");
    }
    fs::path cache = g_root / "MenuBuilder" / "cache" / (s.scene + "." + variant.substr(0, variant.find(':')) + "x" + variant.substr(variant.find(':') + 1) + ".xml");
    std::error_code ec; fs::create_directories(cache.parent_path(), ec);
    std::ofstream out(cache, std::ios::binary | std::ios::trunc);
    out << xml;
    return out ? cache.string() : file.string();
}

using CreateFileAFn = HANDLE(WINAPI*)(LPCSTR, DWORD, DWORD, LPSECURITY_ATTRIBUTES, DWORD, DWORD, HANDLE);
CreateFileAFn g_create_file = nullptr;

HANDLE WINAPI create_file_hook(LPCSTR path, DWORD access, DWORD share, LPSECURITY_ATTRIBUTES sa, DWORD disposition, DWORD flags, HANDLE templ) {
    try {
        if (path && !(access & GENERIC_WRITE) && disposition == OPEN_EXISTING) {
            std::string p(path);
            for (auto& c : p) if (c == '\\') c = '/';
            const auto slash = p.rfind('/');
            const auto dir = slash == std::string::npos ? std::string() : p.substr(0, slash);
            const auto file = p.substr(slash + 1);
            const auto dot = file.rfind('.');
            const bool frontend = dir.size() >= 15 && _stricmp(dir.c_str() + dir.size() - 15, "FrontendScreens") == 0;
            if (frontend && dot != std::string::npos) {
                const auto scene = file.substr(0, dot), ext = file.substr(dot + 1);
                if (auto* s = screen_by_scene(scene)) {
                    if (!_stricmp(ext.c_str(), "xml") && base_ok(*s, path)) {
                        refresh_view();
                        g_variant = choose_variant(*s);
                        const auto target = serve_xml(*s, g_variant);
                        if (!target.empty()) {
                            HANDLE h = g_create_file(target.c_str(), access, share, sa, disposition, flags, templ);
                            log(fmt("REDIRECT scene=%s id=%d variant=%s mode=%d ratio=%.3f file=%s %s", scene.c_str(), s->id, g_variant.c_str(),
                                    g_mode, g_ratio, target.c_str(), h == INVALID_HANDLE_VALUE ? "OPEN_FAILED" : "ok"));
                            if (h != INVALID_HANDLE_VALUE) return h;
                        }
                    } else if (!_stricmp(ext.c_str(), "hnt") && s->custom) {
                        const auto target = (g_dir / (s->scene + ".hnt")).string();
                        HANDLE h = g_create_file(target.c_str(), access, share, sa, disposition, flags, templ);
                        if (h != INVALID_HANDLE_VALUE) return h;
                    }
                }
            }
        }
    } catch (...) {}
    return g_create_file(path, access, share, sa, disposition, flags, templ);
}

// ---- custom screen names (screen change 0x45D6C0) ------------------------------------------------------
void* __fastcall screen_name_hook(void* self, void*, void* out, int id) {
    g_current = id;
    if (id >= kFirstCustom) {
        if (auto* s = screen_by_id(id)) {
            fn<void(__thiscall*)(void*, const char*)>(kStringCtor)(out, s->scene.c_str());
            log(fmt("SCREEN_CHANGE custom id=%d scene=%s", id, s->scene.c_str()));
            return out;
        }
    }
    return fn<void*(__thiscall*)(void*, void*, int)>(kScreenName)(self, out, id);
}

// Host screen AI init (thiscall, one stack argument, RET 4): default focus of custom screens.
void __fastcall host_init(void* self, void*, void* argument) {
    fn<void(__thiscall*)(void*, void*)>(kHostInit)(self, argument);
    try {
        if (g_current >= kFirstCustom)
            if (auto* s = screen_by_id(g_current)) {
                int focus = s->focus;
                if (!focus || !s->find(focus)) for (auto& b : s->buttons) if (b.enabled) { focus = b.id; break; }
                if (focus) put_int("UI/Active", focus);
                log(fmt("CUSTOM_SCREEN_READY scene=%s id=%d focus=%d", s->scene.c_str(), s->id, focus));
            }
    } catch (...) {}
}

// ---- actions -------------------------------------------------------------------------------------------
bool extension_available(const std::string& name) {
    if (g_extensions.count(name)) return true;
    if (name == "game.quit") return true;
#if defined(RMOD_EXTRA_OPTIONS)
    if (name == "extra_options.model_source") return extra_runtime::appearance_available();
#endif
    return false;
}

bool run_extension(const std::string& name, const std::string& args, int screen, int button) {
    if (auto it = g_extensions.find(name); it != g_extensions.end()) return it->second(args.c_str(), screen, button) != 0;
    if (name == "game.quit") { put_bool("Game/Quit", true); return true; }
#if defined(RMOD_EXTRA_OPTIONS)
    if (name == "extra_options.model_source") {
        char label[64]{};
        const bool ok = extra_runtime::appearance_step(args == "-1" ? -1 : 1, label, sizeof(label));
        if (ok) log(fmt("EXTENSION extra_options.model_source -> %s", label));
        return ok;
    }
#endif
    return false;
}

int screen_index(const Helper* h) {
    if (h && h->screen == kHostScreen && g_current >= kFirstCustom) return g_current;
    return h ? h->screen : -1;
}

// Executes a runtime-owned action. Returns the command to hand to the native screen AI (-1 = consumed).
int execute(Helper* h, int sid, int bid, const Action& a) {
    const auto& t = a.type;
    if (t == "native") return a.num("command", bid);
    if (t == "none") return -1;
    if (t == "navigate.screen") {
        const int target = a.num("screen", -1);
        if (target < 0 || (target >= kRetailScreens && !screen_by_id(target))) { log(fmt("ACTION_INVALID navigate target=%d", target)); return -1; }
        g_stack.push_back(sid);
        fn<void(__thiscall*)(void*, int)>(kRequestScreen)(h, target);
        log(fmt("ACTION navigate.screen from=%d button=%d to=%d", sid, bid, target));
        return -1;
    }
    if (t == "native.forward") {
        const int target = a.num("screen", -1), command = a.num("command", 0);
        if (target < 0 || target >= kRetailScreens || command <= 0) { log(fmt("ACTION_INVALID forward screen=%d command=%d", target, command)); return -1; }
        g_forward_screen = target; g_forward_command = command;
        if (target == sid && !screen_by_id(sid)) return command;
        fn<void(__thiscall*)(void*, int)>(kRequestScreen)(h, target);
        log(fmt("ACTION native.forward from=%d button=%d to=%d command=%d", sid, bid, target, command));
        return -1;
    }
    if (t == "navigate.back") {
        int target = 1;
        if (!g_stack.empty()) { target = g_stack.back(); g_stack.pop_back(); }
        fn<void(__thiscall*)(void*, int)>(kRequestScreen)(h, target);
        log(fmt("ACTION navigate.back from=%d to=%d", sid, target));
        return -1;
    }
    if (t == "broker.set_int") { put_int(a.str("key").c_str(), a.num("value")); log(fmt("ACTION set_int %s=%d", a.str("key").c_str(), a.num("value"))); return -1; }
    if (t == "broker.toggle_bool") { const auto k = a.str("key"); const bool v = !get_bool(k.c_str()); put_bool(k.c_str(), v); log(fmt("ACTION toggle %s=%d", k.c_str(), v)); return -1; }
    if (t == "broker.cycle_int") {
        const auto k = a.str("key");
        const int lo = a.num("min", 0), hi = a.num("max", 1), step = a.num("step", 1);
        int v = get_int(k.c_str()) + step;
        if (v > hi) v = lo; if (v < lo) v = hi;
        put_int(k.c_str(), v);
        log(fmt("ACTION cycle %s=%d", k.c_str(), v));
        return -1;
    }
    if (t == "extension") {
        const auto name = a.str("ext");
        if (!run_extension(name, a.str("args"), sid, bid)) log(fmt("ACTION_UNAVAILABLE extension=%s screen=%d button=%d", name.c_str(), sid, bid));
        return -1;
    }
    log(fmt("ACTION_UNKNOWN %s", t.c_str()));
    return -1;
}

// ---- mouse & diagnostics -----------------------------------------------------------------------------------
Rect live_rect(const Button& b, bool& live) {
    float x = 0, y = 0;
    live = egg_position(b.egg, x, y);
    if (live) {
        const float shift = static_cast<float>(margin_dir(x, y) * half_extra());
        return {x + shift + b.local.x0, y + b.local.y0, x + shift + b.local.x1, y + b.local.y1};
    }
    auto it = b.hit.find(g_variant);
    return it != b.hit.end() ? it->second : Rect{};
}

const Button* hit_test(const Screen& s, double ux, double uy) {
    const Button* best = nullptr;
    for (auto& b : s.buttons) {
        bool live = false;
        const Rect r = live_rect(b, live);
        if (!live || r.empty()) continue;  // eggs that do not exist in the live scene are not clickable
        if (ux >= r.x0 && ux < r.x1 && uy >= r.y0 && uy < r.y1) best = &b;  // later (drawn on top) wins
    }
    return best;
}

void mouse(const Screen& s) {
    HWND w = game_window();
    if (!w || GetForegroundWindow() != w) { g_lbutton = g_rbutton = false; return; }
    POINT p{}; RECT r{};
    if (!GetCursorPos(&p) || !ScreenToClient(w, &p) || !GetClientRect(w, &r) || r.right <= 0 || r.bottom <= 0) return;
    const bool inside = p.x >= 0 && p.y >= 0 && p.x < r.right && p.y < r.bottom;
    g_ratio = double(r.right) / r.bottom;
    const double vw = g_mode == 0 ? 640.0 : 480.0 * g_ratio;
    const double ux = p.x * vw / r.right - half_extra(), uy = 480.0 - p.y * 480.0 / r.bottom;
    const bool moved = p.x != g_last_mouse.x || p.y != g_last_mouse.y;
    g_last_mouse = p;
    const bool l = (GetAsyncKeyState(VK_LBUTTON) & 0x8000) != 0, rb = (GetAsyncKeyState(VK_RBUTTON) & 0x8000) != 0;
    const bool lclick = g_lbutton && !l, rclick = g_rbutton && !rb;
    g_lbutton = l; g_rbutton = rb;
    if (!inside) return;
    const Button* b = hit_test(s, ux, uy);
    if (b && (moved || lclick) && get_int("UI/Active") != b->id) put_int("UI/Active", b->id);
    if (b && lclick) { put_int("UI/Control", 4); log(fmt("MOUSE_CLICK scene=%s button=%d egg=%s ui=(%.1f,%.1f)", s.scene.c_str(), b->id, b->egg.c_str(), ux, uy)); }
    if (rclick) put_int("UI/Control", 5);
}

void live_dump(const Screen& s, int sid) {
    if (!g_live_dump) return;
    try {
        std::error_code ec; fs::create_directories(g_root / "MenuBuilder" / "live", ec);
        std::ofstream f(g_root / "MenuBuilder" / "live" / (s.scene + ".txt"), std::ios::trunc);
        RECT r{}; if (HWND w = game_window()) GetClientRect(w, &r);
        f << "screen\t" << s.scene << "\t" << sid << "\nvariant\t" << g_variant << "\nmode\t" << g_mode << "\nwindow\t" << r.right << "\t" << r.bottom
          << "\nfocus\t" << get_int("UI/Active") << "\n";
        for (auto& b : s.buttons) {
            bool live = false;
            const Rect rr = live_rect(b, live);
            float x = 0, y = 0; egg_position(b.egg, x, y);
            f << "button\t" << b.id << "\t" << b.egg << "\t" << (live ? "live" : "missing") << "\tpos=" << x << "," << y
              << "\thit=" << rr.x0 << "," << rr.y0 << "," << rr.x1 << "," << rr.y1 << "\taction=" << b.action.type << "\n";
        }
    } catch (...) {}
}

// Screenshot request for the external runner (tools/menu-builder/test/run_runtime_check.ps1), which captures
// the presentation window with PrintWindow(PW_RENDERFULLCONTENT) from another process, so the game thread
// never waits for DWM and the capture works while the window is covered.
bool request_shot(const std::string& name) {
    std::error_code ec; fs::create_directories(g_root / "MenuBuilder" / "shots", ec);
    std::ofstream f(g_root / "MenuBuilder" / "shots" / (name + ".req"), std::ios::trunc);
    f << name << std::endl;
    return bool(f);
}

int control_code(const std::string& k) {
    if (!_stricmp(k.c_str(), "up")) return 7;
    if (!_stricmp(k.c_str(), "down")) return 1;
    if (!_stricmp(k.c_str(), "left")) return 2;
    if (!_stricmp(k.c_str(), "right")) return 3;
    if (!_stricmp(k.c_str(), "accept") || !_stricmp(k.c_str(), "enter")) return 4;
    if (!_stricmp(k.c_str(), "back") || !_stricmp(k.c_str(), "escape")) return 5;
    return 0;
}

void check(bool ok, const std::string& what) {
    (ok ? g_test_pass : g_test_fail)++;
    log(fmt("TEST %s %s", ok ? "PASS" : "FAIL", what.c_str()));
}

// One step per frame at most; "wait" delays the next step. Input goes through the native channels:
// UI/Control for keys (7 up, 1 down, 2 left, 3 right, 4 accept, 5 back) and the runtime hit test for clicks.
void autotest(Screen* s, int sid) {
    if (g_step >= g_steps.size()) return;
    const ULONGLONG now = GetTickCount64();
    if (now < g_step_due) return;
    const Step st = g_steps[g_step++];
    g_step_due = now + 250;
    const auto arg = [&](size_t i) { return i < st.args.size() ? st.args[i] : std::string(); };
    const char* scene = s ? s->scene.c_str() : "(native)";
    if (st.op == "wait") g_step_due = now + std::strtoull(arg(0).c_str(), nullptr, 10);
    else if (st.op == "key") { put_int("UI/Control", control_code(arg(0))); log(fmt("TEST key %s on %s(%d)", arg(0).c_str(), scene, sid)); }
    else if (st.op == "click" || st.op == "hover") {
        const double ux = std::atof(arg(0).c_str()), uy = std::atof(arg(1).c_str());
        const Button* b = s ? hit_test(*s, ux, uy) : nullptr;
        if (b) { put_int("UI/Active", b->id); if (st.op == "click") put_int("UI/Control", 4); }
        log(fmt("TEST %s ui=(%.1f,%.1f) scene=%s -> %s", st.op.c_str(), ux, uy, scene, b ? b->egg.c_str() : "nothing"));
    }
    else if (st.op == "expect-screen") check(s ? !_stricmp(s->scene.c_str(), arg(0).c_str()) : std::atoi(arg(0).c_str()) == sid && sid >= 0,
                                             fmt("screen %s (now %s/%d)", arg(0).c_str(), scene, sid));
    else if (st.op == "expect-focus") check(get_int("UI/Active") == std::atoi(arg(0).c_str()), fmt("focus %s (now %d) on %s", arg(0).c_str(), get_int("UI/Active"), scene));
    else if (st.op == "expect-hit") {
        const Button* b = s ? hit_test(*s, std::atof(arg(0).c_str()), std::atof(arg(1).c_str())) : nullptr;
        check(arg(2) == "none" ? b == nullptr : (b && b->egg == arg(2)), fmt("hit (%s,%s) = %s (now %s)", arg(0).c_str(), arg(1).c_str(), arg(2).c_str(), b ? b->egg.c_str() : "nothing"));
    }
    else if (st.op == "shot") { const bool ok = request_shot(arg(0)); g_step_due = now + 900; log(fmt("TEST shot %s %s", arg(0).c_str(), ok ? "requested" : "FAILED")); }
    else if (st.op == "dump") { if (s) live_dump(*s, sid); }
    else if (st.op == "log") log("TEST note " + arg(0));
    else if (st.op == "end") { log(fmt("TEST_DONE pass=%d fail=%d", g_test_pass, g_test_fail)); g_step = g_steps.size(); }
    else log("TEST unknown step " + st.op);
}

using GetCommandFn = int(__thiscall*)(Helper*, int);

int __fastcall get_command(Helper* h, void*, int sound) {
    const auto original = reinterpret_cast<GetCommandFn>(g_trampoline);
    Screen* s = nullptr;
    int sid = -1;
    try {
        sid = screen_index(h);
        s = screen_by_id(sid);
        if (s && s->base_state < 0) s = nullptr;  // native page kept: never act on it
        if (s && h != g_last_helper) {
            g_last_helper = h;
            if (!s->custom && s->focus && !s->find(get_int("UI/Active"))) put_int("UI/Active", s->focus);
            log(fmt("SCREEN_ACTIVE scene=%s id=%d variant=%s focus=%d", s->scene.c_str(), sid, g_variant.c_str(), get_int("UI/Active")));
            live_dump(*s, sid);
        }
        if (s && g_layout.mouse) mouse(*s);
        if (!g_steps.empty()) autotest(s, sid);
    } catch (...) { s = nullptr; }
    // native.forward: the target screen's own AI receives the command as if its button was pressed.
    if (h && g_forward_screen >= 0 && h->screen == g_forward_screen && g_current == g_forward_screen) {
        const int command = g_forward_command;
        g_forward_screen = -1; g_forward_command = 0;
        log(fmt("FORWARD_DELIVERED screen=%d command=%d", h->screen, command));
        return command;
    }
    int result = original(h, sound);
    if (!s) return result;
    try {
        if (result > 0) {
            if (const Button* b = s->find(result)) {
                if (b->action.type == "native" && !b->action.args.count("command")) return result;  // retail command, native AI owns it
                return execute(h, sid, result, b->action);
            }
            return s->custom ? -1 : result;
        }
        if (result == -3) {
            if (s->has_back) return execute(h, sid, -3, s->back);
            if (s->custom) return execute(h, sid, -3, Action{"navigate.back", {}});
        }
        if (s->custom && result != -1) return -1;  // the host AI never sees commands of a custom screen
    } catch (...) { log("ACTION_EXCEPTION"); return -1; }
    return result;
}

// ---- installation -------------------------------------------------------------------------------------------
bool patch(uintptr_t va, const void* bytes, size_t size) {
    DWORD old = 0, ignored = 0;
    if (!VirtualProtect(reinterpret_cast<void*>(va), size, PAGE_EXECUTE_READWRITE, &old)) return false;
    std::memcpy(reinterpret_cast<void*>(va), bytes, size);
    FlushInstructionCache(GetCurrentProcess(), reinterpret_cast<void*>(va), size);
    return VirtualProtect(reinterpret_cast<void*>(va), size, old, &ignored) != FALSE;
}
std::array<unsigned char, 5> rel(unsigned char op, uintptr_t at, const void* target) {
    std::array<unsigned char, 5> b{op};
    const auto off = static_cast<int32_t>(reinterpret_cast<uintptr_t>(target) - at - 5);
    std::memcpy(b.data() + 1, &off, 4);
    return b;
}

} // namespace

bool initialize() noexcept {
    try {
        wchar_t exe[MAX_PATH]{};
        if (!GetModuleFileNameW(nullptr, exe, MAX_PATH)) return false;
        g_root = fs::path(exe).parent_path();
        const auto ini = (g_root / "MenuBuilder" / "MenuBuilder.ini").wstring();
        if (!fs::exists(ini)) return true;  // feature not installed: nothing to log, Classic frontend
        const int enabled = GetPrivateProfileIntW(L"General", L"Enabled", 0, ini.c_str());
        g_live_dump = GetPrivateProfileIntW(L"Diagnostics", L"LiveDump", 1, ini.c_str()) != 0;
        wchar_t name[128]{};
        GetPrivateProfileStringW(L"General", L"Layout", L"", name, 128, ini.c_str());
        if (!enabled || !name[0]) { log("CLASSIC menu builder disabled; native frontend unchanged"); return true; }
        g_dir = g_root / "MenuBuilder" / "Layouts" / name;
        wchar_t test[260]{};
        GetPrivateProfileStringW(L"Diagnostics", L"AutoTest", L"", test, 260, ini.c_str());
        if (test[0]) {
            std::ifstream t(g_root / "MenuBuilder" / test);
            std::string line;
            while (std::getline(t, line)) {
                if (!line.empty() && line.back() == 13) line.pop_back();
                if (line.empty() || line[0] == '#') continue;
                std::istringstream in(line); Step st; in >> st.op; std::string a; while (in >> a) st.args.push_back(a);
                g_steps.push_back(st);
            }
            log(fmt("AUTOTEST loaded %u steps", unsigned(g_steps.size())));
        }
        if (!load_layout(g_dir)) { log("LAYOUT_REJECTED native frontend unchanged"); return false; }
        for (const auto& api : kApis) {
            std::array<unsigned char, 8> seen{};
            if (!read_mem(api.va, seen.data(), seen.size()) || seen != api.bytes) {
                log(fmt("API_LAYOUT_UNSUPPORTED va=0x%x: not the retail image or another hook owns it; no hooks installed", unsigned(api.va)));
                return false;
            }
        }
        std::array<unsigned char, 6> site{};
        uintptr_t slot = 0;
        std::array<unsigned char, 5> name_site{};
        if (!read_mem(kCreateFileSite, site.data(), 6) || site[0] != 0xff || site[1] != 0x15 ||
            !read_mem(kScreenNameSite, name_site.data(), 5) || name_site != rel(0xe8, kScreenNameSite, reinterpret_cast<void*>(kScreenName)) ||
            !read_mem(kHostInitSlot, &slot, 4) || slot != kHostInit) {
            log("HOOK_CONFLICT a call site or vtable slot differs from retail; no hooks installed");
            return false;
        }
        uintptr_t iat = 0, create_file = 0;
        std::memcpy(&iat, site.data() + 2, 4);
        if (!read_mem(iat, &create_file, 4) || !create_file) { log("HOOK_CONFLICT CreateFileA import unreadable"); return false; }
        g_create_file = reinterpret_cast<CreateFileAFn>(create_file);

        // Trampoline for GetCommand: replay SUB ESP,5C / PUSH EBX,EBP,ESI,EDI (7 bytes) then JMP 0x45D937.
        g_trampoline = static_cast<unsigned char*>(VirtualAlloc(nullptr, 32, MEM_COMMIT | MEM_RESERVE, PAGE_EXECUTE_READWRITE));
        if (!g_trampoline) return false;
        std::memcpy(g_trampoline, reinterpret_cast<void*>(kGetCommand), 7);
        auto back = rel(0xe9, reinterpret_cast<uintptr_t>(g_trampoline) + 7, reinterpret_cast<void*>(kGetCommand + 7));
        std::memcpy(g_trampoline + 7, back.data(), 5);
        FlushInstructionCache(GetCurrentProcess(), g_trampoline, 32);

        struct Write { uintptr_t va; std::vector<unsigned char> before, after; };
        std::vector<Write> writes;
        auto add = [&](uintptr_t va, std::vector<unsigned char> after) {
            Write w{va, std::vector<unsigned char>(after.size()), after};
            read_mem(va, w.before.data(), w.before.size());
            writes.push_back(w);
        };
        { auto c = rel(0xe8, kCreateFileSite, reinterpret_cast<void*>(&create_file_hook)); add(kCreateFileSite, {c[0], c[1], c[2], c[3], c[4], 0x90}); }
        { auto c = rel(0xe8, kScreenNameSite, reinterpret_cast<void*>(&screen_name_hook)); add(kScreenNameSite, {c.begin(), c.end()}); }
        { auto v = reinterpret_cast<uintptr_t>(&host_init); add(kHostInitSlot, {reinterpret_cast<unsigned char*>(&v), reinterpret_cast<unsigned char*>(&v) + 4}); }
        { auto j = rel(0xe9, kGetCommand, reinterpret_cast<void*>(&get_command)); add(kGetCommand, {j[0], j[1], j[2], j[3], j[4], 0x90, 0x90}); }
        for (size_t i = 0; i < writes.size(); ++i)
            if (!patch(writes[i].va, writes[i].after.data(), writes[i].after.size())) {
                for (size_t k = 0; k <= i; ++k) patch(writes[k].va, writes[k].before.data(), writes[k].before.size());
                log("HOOK_INSTALL_FAILED rolled back");
                return false;
            }
        g_installed = true;
        size_t buttons = 0, custom = 0;
        for (auto& s : g_layout.screens) { buttons += s.buttons.size(); custom += s.custom; }
        log(fmt("READY MENU-BUILDER layout=%s screens=%u custom=%u buttons=%u mouse=%d hooks=%u", g_layout.name.c_str(),
                unsigned(g_layout.screens.size()), unsigned(custom), unsigned(buttons), g_layout.mouse ? 1 : 0, unsigned(writes.size())));
        return true;
    } catch (...) {
        log("INITIALIZATION_FAILED");
        return false;
    }
}

} // namespace menu_builder

extern "C" unsigned WINAPI MRMenuAbiV1() { return 0x4d4d0001u; }

extern "C" BOOL WINAPI MRMenuRegisterActionV1(const char* name, MRMenuActionV1 action) {
    if (!name || !*name || !action) return FALSE;
    try { menu_builder::g_extensions[name] = action; menu_builder::log(menu_builder::fmt("EXTENSION_REGISTERED %s", name)); return TRUE; } catch (...) { return FALSE; }
}

extern "C" int WINAPI MRMenuQueryV1(char* buffer, int size) {
    if (!buffer || size <= 0) return 0;
    const auto text = menu_builder::fmt("installed=%d layout=%s screen=%d variant=%s mode=%d", menu_builder::g_installed ? 1 : 0,
                                        menu_builder::g_layout.name.c_str(), menu_builder::g_current, menu_builder::g_variant.c_str(), menu_builder::g_mode);
    std::snprintf(buffer, size_t(size), "%s", text.c_str());
    return int(text.size());
}
