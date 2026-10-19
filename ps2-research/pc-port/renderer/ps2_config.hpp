#pragma once
// PS2Port.ini v2 (docs/config-v2.md). Modules keep asking for their historical key names; this layer
// answers from the v2 key when it is present in the INI and falls back to the historical key only when
// the v2 key is absent, so old INIs and fixtures keep working while the documented INI stays short.
#include <windows.h>
#include <cwchar>

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
        {L"RacePS2FleetCapture", L"Diagnostics"},
        {L"RacePS2FleetDamageCapture", L"Diagnostics"},
        {L"RacePS2DamageCapture", L"Diagnostics"},
    };
    if (!legacy) return nullptr;
    for (const auto& r : rules) if (!std::wcscmp(r.legacy, legacy)) return r.key;
    return nullptr;
}

inline bool present(const wchar_t* key, const wchar_t* ini) noexcept {
    wchar_t probe[4]{};
    GetPrivateProfileStringW(L"PS2Port", key, L"\x1f", probe, 4, ini);
    return std::wcscmp(probe, L"\x1f") != 0;
}

inline const wchar_t* resolve(const wchar_t* legacy, const wchar_t* ini) noexcept {
    const wchar_t* key = v2_key(legacy);
    return key && present(key, ini) ? key : legacy;
}

inline DWORD read_string(const wchar_t* legacy, const wchar_t* fallback, wchar_t* out, DWORD size, const wchar_t* ini) noexcept {
    return GetPrivateProfileStringW(L"PS2Port", resolve(legacy, ini), fallback, out, size, ini);
}

inline UINT read_int(const wchar_t* legacy, INT fallback, const wchar_t* ini) noexcept {
    return GetPrivateProfileIntW(L"PS2Port", resolve(legacy, ini), fallback, ini);
}

}  // namespace gfx2::ps2port::config
