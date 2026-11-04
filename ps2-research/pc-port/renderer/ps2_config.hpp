#pragma once
// PS2Port.ini v2 (docs/config-v2.md). Modules keep asking for their historical key names; this layer
// answers from the v2 key when it is present in the INI and falls back to the historical key only when
// the v2 key is absent, so old INIs and fixtures keep working while the documented INI stays short.
// PS2Port.ini v3 (FPS1, ps2-research/pc-port/config): [General] ConfigVersion=3 switches to sectioned files. Keys lose the
// "PS2" prefix, every on/off key is 0/1 (Reflection=1 means the historical 4, FrontendModel=1 the historical 2 with
// PS2FrontendAllCars=1), debug and research switches live in the optional RendererDiag.ini beside it, and the asset paths
// are fixed defaults. Without ConfigVersion=3 the v2/legacy behaviour below is unchanged.
#include <windows.h>
#include <cwchar>
#include <cwctype>
#include <cstdlib>
#include <map>
#include <mutex>
#include <string>
#include <utility>

namespace gfx2::ps2port::config {

struct Rule { const wchar_t* legacy; const wchar_t* key; };

inline const wchar_t* v2_key(const wchar_t* legacy) noexcept {
    static constexpr Rule rules[] = {
        {L"ReflectionMode", L"Reflection"},
        {L"FoliageMode", L"Foliage"},
        {L"FrontendModelMode", L"FrontendModel"},
        {L"BrakeGlowMode", L"BrakeGlow"},
        {L"GrassMode", L"Grass"},
        {L"ShrubsMode", L"Shrubs"},
        {L"CourseObjectsMode", L"CourseObjects"},
        // One switch for every race-car feature; the X-Trail and pilot switches follow it.
        {L"RacePS2FleetMode", L"RaceFleet"},
        {L"RacePS2ModelMode", L"RaceFleet"},
        {L"RacePS2WheelMode", L"RaceFleet"},
        {L"RacePS2ModelParts", L"RaceFleet"},
        {L"RacePS2CrewMode", L"RaceFleet"},
        {L"XtrailFidelityMode", L"RaceFleet"},
        {L"RaceModelMode", L"RaceFleet"},
        {L"RacePS2ModelAssetDirectory", L"RaceModelAssetDirectory"},
        // One diagnostics switch for logs and F10 sidecars (FrontendGeometryDiagnostics, which forces
        // buffer mirroring, stays a legacy-only research probe).
        {L"ReflectionDiagnostics", L"Diagnostics"},
        {L"VehicleModelDiagnostics", L"Diagnostics"},
        {L"XtrailFidelityDiagnostics", L"Diagnostics"},
        {L"XtrailGlassDiagnostics", L"Diagnostics"},
        {L"BrakeGlowDiagnostics", L"Diagnostics"},
        {L"FrontendModelDiagnostics", L"Diagnostics"},
        {L"RacePS2ModelDiagnostics", L"Diagnostics"},
        {L"RacePS2WheelDiagnostics", L"Diagnostics"},
        {L"CourseObjectsDiagnostics", L"Diagnostics"},
        {L"GrassDiagnostics", L"Diagnostics"},
        {L"ShrubsDiagnostics", L"Diagnostics"},
        {L"SplineObjectsDiagnostics", L"Diagnostics"},
        {L"PS2BirdsDiagnostics", L"Diagnostics"},
        {L"RacePS2FleetCapture", L"Diagnostics"},
        {L"RacePS2FleetDamageCapture", L"Diagnostics"},
        {L"RacePS2DamageCapture", L"Diagnostics"},
    };
    if (!legacy) return nullptr;
    for (const auto& r : rules) if (!std::wcscmp(r.legacy, legacy)) return r.key;
    return nullptr;
}

inline bool is_v3(const wchar_t* ini) noexcept;
namespace v3 { inline bool value(const wchar_t* legacy, const wchar_t* ini, std::wstring& out); }
inline bool present(const wchar_t* key, const wchar_t* ini) noexcept {
    if (is_v3(ini)) { try { std::wstring v; return v3::value(key, ini, v); } catch (...) { return false; } }
    wchar_t probe[4]{};
    GetPrivateProfileStringW(L"PS2Port", key, L"\x1f", probe, 4, ini);
    return std::wcscmp(probe, L"\x1f") != 0;
}

inline const wchar_t* resolve(const wchar_t* legacy, const wchar_t* ini) noexcept {
    const wchar_t* key = v2_key(legacy);
    return key && present(key, ini) ? key : legacy;
}

namespace v3 {
// How the historical value is derived from the v3 value.
enum class Kind { Same, ReflectionOn4, FrontendOn2, FrontendAllCars };
struct Name { std::wstring key; Kind kind = Kind::Same; };
// Historical (v2-resolved) name -> v3 name: the "PS2" prefix is dropped; three keys change their values.
inline Name name(const wchar_t* historical) {
    const std::wstring h = historical ? historical : L"";
    if (h == L"Reflection") return {L"Reflection", Kind::ReflectionOn4};
    if (h == L"FrontendModel") return {L"FrontendModel", Kind::FrontendOn2};
    if (h == L"PS2FrontendAllCars") return {L"FrontendModel", Kind::FrontendAllCars};
    if (h.size() > 3 && h.compare(0, 3, L"PS2") == 0) return {h.substr(3), Kind::Same};
    return {h, Kind::Same};
}
// Shipped values of the keys the v3 files leave out (the historical code defaults differ for some of them).
inline const wchar_t* default_value(const std::wstring& historical) noexcept {
    static constexpr std::pair<const wchar_t*, const wchar_t*> table[] = {
        {L"RaceModelAssetDirectory", L"PS2Vehicles"}, {L"FrontendModelAssetDirectory", L"PS2Vehicles"},
        {L"GrassAssetDirectory", L"PS2Grass"}, {L"GroundDetailAsset", L"PS2Grass\\PS2GroundNoise.gxi"},
        {L"BrakeGlowAsset", L"PS2Grass\\PS2BrakeGlow.gxi"}, {L"KiaBrakeOnAsset", L"PS2Vehicles\\PS2KiaBrakeOn.gxi"},
        {L"ReflectionSourceGXI", L"PS2Grass\\PS2EnvSource64x64.gxi"}, {L"PS2HudAssetDir", L"PS2Hud"},
        {L"CollisionDebugArchive", L"Data.sma"}, {L"ReflectionWorldFirst", L"1"}, {L"BaselineAllRaceModes", L"1"},
        {L"RetailDerivativeBuilds", L"1"},
    };
    for (const auto& [k, v] : table) if (historical == k) return v;
    return nullptr;
}
inline std::wstring trim(const std::wstring& s) {
    size_t a = 0, b = s.size();
    while (a < b && std::iswspace(s[a])) ++a;
    while (b > a && std::iswspace(s[b - 1])) --b;
    return s.substr(a, b - a);
}
// Every key of every section of one file; the first occurrence wins.
inline void load_file(const std::wstring& path, std::map<std::wstring, std::wstring>& out) {
    std::wstring sections(8192, L'\0');
    const DWORD n = GetPrivateProfileSectionNamesW(sections.data(), DWORD(sections.size()), path.c_str());
    for (size_t i = 0; i < n && sections[i];) {
        const std::wstring section = sections.c_str() + i; i += section.size() + 1;
        std::wstring body(32768, L'\0');
        const DWORD m = GetPrivateProfileSectionW(section.c_str(), body.data(), DWORD(body.size()), path.c_str());
        for (size_t j = 0; j < m && body[j];) {
            const std::wstring line = body.c_str() + j; j += line.size() + 1;
            const auto t = trim(line); const auto eq = t.find(L'=');
            if (t.empty() || t[0] == L';' || t[0] == L'#' || eq == std::wstring::npos) continue;
            out.emplace(trim(t.substr(0, eq)), trim(t.substr(eq + 1)));
        }
    }
}
struct Files { bool v3 = false; std::map<std::wstring, std::wstring> values; };
inline std::wstring file_stamp(const std::wstring& path) {
    WIN32_FILE_ATTRIBUTE_DATA a{};
    if (!GetFileAttributesExW(path.c_str(), GetFileExInfoStandard, &a)) return L"-";
    return std::to_wstring(a.ftLastWriteTime.dwHighDateTime) + L"." + std::to_wstring(a.ftLastWriteTime.dwLowDateTime) + L"." +
           std::to_wstring(a.nFileSizeLow);
}
// PS2Port.ini first, then RendererDiag.ini; parsed once per INI path and file version (write time and size).
inline const Files& files(const wchar_t* ini) {
    static std::mutex lock; static std::map<std::wstring, Files> cache;
    std::lock_guard<std::mutex> guard(lock);
    const std::wstring path = ini ? ini : L"";
    const auto slash = path.find_last_of(L"\\/");
    const std::wstring diagnostics = (slash == std::wstring::npos ? std::wstring() : path.substr(0, slash + 1)) + L"RendererDiag.ini";
    const std::wstring key = path + L"|" + file_stamp(path) + L"|" + file_stamp(diagnostics);
    auto found = cache.find(key);
    if (found != cache.end()) return found->second;
    Files f;
    f.v3 = GetPrivateProfileIntW(L"General", L"ConfigVersion", 0, path.c_str()) >= 3;
    if (f.v3) { load_file(path, f.values); load_file(diagnostics, f.values); }
    return cache.emplace(key, std::move(f)).first->second;
}
// The historical value of a historical key; false when neither file nor the shipped defaults have it.
inline bool value(const wchar_t* legacy, const wchar_t* ini, std::wstring& out) {
    const Files& f = files(ini);
    const wchar_t* historical = v2_key(legacy) ? v2_key(legacy) : legacy;
    const Name n = name(historical);
    auto it = f.values.find(n.key);
    if (it == f.values.end()) it = f.values.find(historical);  // a historical name written into a v3 file
    if (it == f.values.end()) { if (const auto* d = default_value(historical)) { out = d; return true; } return false; }
    const bool on = it->second == L"1";
    switch (n.kind) {
    case Kind::ReflectionOn4: out = on ? L"4" : it->second; break;
    case Kind::FrontendOn2: out = on ? L"2" : it->second; break;
    case Kind::FrontendAllCars: out = on ? L"1" : L"0"; break;
    default: out = it->second; break;
    }
    return true;
}
}  // namespace v3

inline bool is_v3(const wchar_t* ini) noexcept { try { return v3::files(ini).v3; } catch (...) { return false; } }

inline DWORD read_string(const wchar_t* legacy, const wchar_t* fallback, wchar_t* out, DWORD size, const wchar_t* ini) noexcept {
    if (is_v3(ini)) {
        try {
            std::wstring v; if (!v3::value(legacy, ini, v)) v = fallback ? fallback : L"";
            if (!out || !size) return 0;
            const size_t n = v.size() < size - 1 ? v.size() : size - 1;
            std::wmemcpy(out, v.data(), n); out[n] = 0; return DWORD(n);
        } catch (...) { if (out && size) out[0] = 0; return 0; }
    }
    return GetPrivateProfileStringW(L"PS2Port", resolve(legacy, ini), fallback, out, size, ini);
}

inline UINT read_int(const wchar_t* legacy, INT fallback, const wchar_t* ini) noexcept {
    if (is_v3(ini)) {
        try {
            std::wstring v; if (!v3::value(legacy, ini, v)) return UINT(fallback);
            wchar_t* end = nullptr; const long parsed = std::wcstol(v.c_str(), &end, 10);
            return end == v.c_str() ? UINT(fallback) : UINT(parsed);
        } catch (...) { return UINT(fallback); }
    }
    return GetPrivateProfileIntW(L"PS2Port", resolve(legacy, ini), fallback, ini);
}

}  // namespace gfx2::ps2port::config
