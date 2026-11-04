#pragma once
// MRRRenderer.ini v2 (FPS1, ps2-research/pc-port/config/MRRRenderer.ini). [General] ConfigVersion=2 keeps the v1 section and
// key names where they map one to one ([Display], [HUD], [FreeCamera], [FreeCameraKeys], [ProbeTeleport], [PhysicsObserver],
// [Compatibility], [Diagnostics] CrashLog) and folds the rest into [Quality] and [Diagnostics] Trace. The baseline visual and
// trace readers get a v1 view of the file (MRRRenderer\config-v1.ini, rewritten at every start); the readers that use the
// session config path (ProbeTeleport, PhysicsObserver, CrashLog) read the unchanged sections of the original file.
#include "ps2_config.hpp"
#include <windows.h>
#include <cstdlib>
#include <cwchar>
#include <string>
#include <vector>

namespace gfx2::ps2port {

namespace renderer_v2 {
inline std::wstring get(const wchar_t* section, const wchar_t* key, const wchar_t* fallback, const std::wstring& ini) {
    wchar_t b[256]{}; GetPrivateProfileStringW(section, key, fallback, b, 256, ini.c_str()); return b;
}
inline int get_int(const wchar_t* section, const wchar_t* key, int fallback, const std::wstring& ini) {
    const auto v = get(section, key, L"", ini); wchar_t* end = nullptr; const long n = std::wcstol(v.c_str(), &end, 10);
    return end == v.c_str() ? fallback : int(n);
}
// One v1 key. Every write goes to the fresh view file.
inline bool put(const wchar_t* section, const wchar_t* key, const std::wstring& value, const std::wstring& view) {
    return WritePrivateProfileStringW(section, key, value.c_str(), view.c_str()) != FALSE;
}
// Copies every key of a section unchanged (absent section: nothing).
inline bool copy_section(const wchar_t* section, const std::wstring& ini, const std::wstring& view) {
    std::vector<wchar_t> body(32768, L'\0');
    const DWORD n = GetPrivateProfileSectionW(section, body.data(), DWORD(body.size()), ini.c_str());
    if (!n) return true;
    std::wstring lines;
    for (size_t i = 0; i < n && body[i];) {
        const std::wstring line = body.data() + i; i += line.size() + 1;
        const auto t = config::v3::trim(line);
        if (t.empty() || t[0] == L';' || t[0] == L'#' || t.find(L'=') == std::wstring::npos) continue;
        const auto eq = t.find(L'=');
        lines += config::v3::trim(t.substr(0, eq)) + L"=" + config::v3::trim(t.substr(eq + 1)); lines.push_back(L'\0');
    }
    lines.push_back(L'\0');
    return WritePrivateProfileSectionW(section, lines.c_str(), view.c_str()) != FALSE;
}
}  // namespace renderer_v2

// Pure part, testable: the v1 view of a v2 file written to `view`. Returns false if any write fails.
inline bool write_renderer_v1_view(const std::wstring& ini, const std::wstring& view) {
    using namespace renderer_v2;
    DeleteFileW(view.c_str());
    bool ok = put(L"Renderer", L"ConfigVersion", L"1", view);
    for (const wchar_t* s : {L"Display", L"HUD", L"FreeCamera", L"FreeCameraKeys", L"Compatibility", L"VehicleReflections"})
        ok = copy_section(s, ini, view) && ok;
    // Always explicit: without HUD.HiddenAtStartup the v1 parser treats FreeCamera.CleanViewEnabled=1 as "hide the HUD at
    // start" (legacy); the v1 MenuFreezeFix default is off, in v2 it is on unless the file says 0.
    ok = put(L"HUD", L"HiddenAtStartup", get_int(L"HUD", L"HiddenAtStartup", 0, ini) == 1 ? L"1" : L"0", view) && ok;
    ok = put(L"Compatibility", L"MenuFreezeFix", get_int(L"Compatibility", L"MenuFreezeFix", 1, ini) == 1 ? L"1" : L"0", view) && ok;
    // [Quality]: 0 = all Stock, 1 = Classic+ (MSAA 4x, AF 16x, widescreen HUD, 60 degree FOV), 2 = the values given.
    const int preset = get_int(L"Quality", L"Preset", 2, ini);
    int aa = get_int(L"Quality", L"AntiAliasing", 0, ini), af = get_int(L"Quality", L"Anisotropy", 0, ini);
    int wide = get_int(L"Quality", L"Widescreen", 0, ini), fov = get_int(L"Quality", L"GameplayFOV", 0, ini);
    int shadows = get_int(L"Quality", L"Shadows", 0, ini);
    std::wstring vfov = get(L"Quality", L"VerticalFOVDegrees", L"60", ini);
    if (preset == 0) { aa = af = wide = fov = shadows = 0; }
    if (preset == 1) { aa = 4; af = 16; wide = 2; fov = 1; vfov = L"60"; shadows = 0; }
    ok = put(L"AntiAliasing", L"Mode", aa > 1 ? L"1" : L"0", view) && ok;
    ok = put(L"AntiAliasing", L"Samples", std::to_wstring(aa > 1 ? aa : 4), view) && ok;
    ok = put(L"Filtering", L"AnisotropicFiltering", af > 1 ? L"1" : L"0", view) && ok;
    ok = put(L"Filtering", L"MaxAnisotropy", std::to_wstring(af > 1 ? af : 16), view) && ok;
    ok = put(L"Widescreen", L"InterfaceMode", std::to_wstring(wide < 0 || wide > 2 ? 0 : wide), view) && ok;
    ok = put(L"Camera", L"GameplayFOV", fov == 1 ? L"1" : L"0", view) && ok;
    ok = put(L"Camera", L"VerticalFOVDegrees", vfov, view) && ok;
    ok = put(L"Shadows", L"Mode", shadows == 1 ? L"1" : L"0", view) && ok;
    // [Diagnostics] Trace: the v1 trace reader defaults to ON when [Trace] is absent, so both keys are always written.
    const std::wstring trace = get_int(L"Diagnostics", L"Trace", 0, ini) == 1 ? L"1" : L"0";
    ok = put(L"Trace", L"Enabled", trace, view) && ok;
    ok = put(L"Trace", L"FrameSummaries", trace, view) && ok;
    return ok;
}

// The file the baseline visual/trace readers should read: the v1 view for a v2 file, else the file itself.
inline std::wstring renderer_ini_v1_view(const std::wstring& ini, const std::wstring& base) {
    try {
        if (GetPrivateProfileIntW(L"General", L"ConfigVersion", 0, ini.c_str()) < 2) return ini;
        CreateDirectoryW((base + L"\\MRRRenderer").c_str(), nullptr);
        const std::wstring view = base + L"\\MRRRenderer\\config-v1.ini";
        return write_renderer_v1_view(ini, view) ? view : ini;
    } catch (...) { return ini; }
}

}  // namespace gfx2::ps2port
