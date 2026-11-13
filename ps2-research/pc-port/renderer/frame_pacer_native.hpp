#pragma once
// PERF-PACING1 Win32 glue: config, DWM composition timing (resolved at run time, no link dependency), high-resolution
// wait and the frame_pacing log. Called once per Present from PS2PortExtension::color_present, after every present pass
// has been drawn and immediately before the native Present. See docs/perf-pacing1/PACING.md.
#include "frame_pacer.hpp"
#include "provenance.hpp"
#include <dwmapi.h>   // DWM_TIMING_INFO type only
#include <string>
namespace gfx2::ps2port::framepacing {

struct Pacer {
    pacing::Config config; pacing::Core core;
    bool configured = false, available = false, seeded = false; const char* reason = "not_configured";
    using Get = HRESULT(WINAPI*)(HWND, DWM_TIMING_INFO*); Get get = nullptr; HANDLE timer = nullptr;
    int64_t freq = 0, last_end = 0, log_at = 0, origin = 0;
    uint64_t frames = 0, waits = 0, late = 0, failures = 0, hist[5]{}; int64_t last_present = 0; double wait_ms = 0, work_ms_max = 0, refresh_hz = 0;
    static int64_t qpc() noexcept { LARGE_INTEGER v{}; QueryPerformanceCounter(&v); return v.QuadPart; }
    void configure() noexcept {
        configured = true; LARGE_INTEGER f{}; QueryPerformanceFrequency(&f); freq = f.QuadPart;
        const auto& ini = session().config_path;
        unsigned display = 2;
        if (!ini.empty()) {
            config.mode = GetPrivateProfileIntW(L"FramePacing", L"Mode", 1, ini.c_str());
            config.max_fps = GetPrivateProfileIntW(L"FramePacing", L"MaxFps", 100, ini.c_str());
            config.adaptive = GetPrivateProfileIntW(L"FramePacing", L"Adaptive", 1, ini.c_str()) != 0;
            config.min_fps = GetPrivateProfileIntW(L"FramePacing", L"MinFps", 55, ini.c_str());
            display = GetPrivateProfileIntW(L"Display", L"Mode", 0, ini.c_str());
        }
        if (config.mode != 1) { reason = "mode_off"; return; }
        // DWM-composed presentation only: Windowed (1) and Borderless (2). Stock/Exclusive keep the native present.
        if (display != 1 && display != 2) { reason = "not_dwm_composed_display_mode"; write("disabled"); return; }
        if (config.max_fps < 20) config.max_fps = 20;
        if (auto dwm = LoadLibraryW(L"dwmapi.dll")) get = reinterpret_cast<Get>(GetProcAddress(dwm, "DwmGetCompositionTimingInfo"));
        if (!get || freq <= 0) { reason = "dwm_timing_unavailable"; write("disabled"); return; }
        timer = CreateWaitableTimerExW(nullptr, nullptr, 0x00000002 /*CREATE_WAITABLE_TIMER_HIGH_RESOLUTION*/, TIMER_ALL_ACCESS);
        if (!timer) timer = CreateWaitableTimerW(nullptr, TRUE, nullptr);
        available = true; reason = "display_locked";
    }
    void wait_until(int64_t until) noexcept {
        const int64_t tenth = freq / 10000;   // 0.1 ms
        for (;;) {
            const int64_t left = until - qpc(); if (left <= 0) return;
            if (timer && left > tenth * 15) {   // sleep until ~1 ms before, then yield-spin
                LARGE_INTEGER due{}; due.QuadPart = -((left - tenth * 10) * 10000000 / freq);
                if (SetWaitableTimer(timer, &due, 0, nullptr, nullptr, FALSE)) { WaitForSingleObject(timer, 50); continue; }
            }
            YieldProcessor();
        }
    }
    void before_present() noexcept {
        if (!configured) configure(); if (!available) return;
        const int64_t start = qpc();
        DWM_TIMING_INFO t{}; t.cbSize = sizeof(t);
        if (FAILED(get(nullptr, &t)) || !t.qpcRefreshPeriod || !t.qpcVBlank) { if (++failures == 1) write("dwm_timing_query_failed"); last_end = 0; return; }
        const int64_t period = int64_t(t.qpcRefreshPeriod); refresh_hz = double(freq) / double(period);
        config.min_divisor = pacing::divisor_for(refresh_hz, config.max_fps);
        config.max_divisor = pacing::max_divisor_for(refresh_hz, config.min_fps, config.min_divisor);
        if (!seeded) { core.divisor = config.min_divisor; seeded = true; write("enabled"); }
        const double work = last_end ? double(start - last_end) / double(period) : 0;
        if (last_end) work_ms_max = std::max(work_ms_max, double(start - last_end) * 1000. / double(freq));
        // Measured on Windows 11 (2026-11-12): qpcVBlank is the vblank of the NEXT composition (6-11 ms ahead) and cRefresh
        // counts timing queries, not refreshes. Only the vblank phase and the period are usable, so refresh indices are counted
        // from our own origin, which is re-phased to the reported vblank on every frame (absorbs clock drift).
        const int64_t vblank = int64_t(t.qpcVBlank);
        if (!origin || vblank - origin < 0 || vblank - origin > period * (int64_t(1) << 40)) origin = vblank - period * 1024;
        else { const int64_t n = (vblank - origin + period / 2) / period; origin = vblank - n * period; }
        const auto plan = core.plan(start, origin, 0, period, period / 20);   // ~5 % of a refresh after the vblank
        if (plan.wait && plan.until > start && plan.until - start < period * 8) { wait_until(plan.until); ++waits; wait_ms += double(qpc() - start) * 1000. / double(freq); }
        if (plan.late) ++late;
        ++frames;
        if (last_end && core.adapt(config, work, plan.late)) write("divisor_changed");
        last_end = qpc();
        if (last_present) { const int64_t r = (last_end - last_present + period / 2) / period; ++hist[std::min<int64_t>(4, std::max<int64_t>(0, r))]; }   // present interval in refreshes
        last_present = last_end;
        if (!log_at) log_at = start; else if (start - log_at > freq * 10) { write("window"); log_at = start; }
    }
    void write(const char* what) noexcept {
        try {
            session().write("{\"type\":\"frame_pacing\",\"event\":\"" + std::string(what) + "\",\"reason\":\"" + reason + "\",\"refresh_hz\":" + std::to_string(refresh_hz) +
                ",\"max_fps\":" + std::to_string(config.max_fps) + ",\"adaptive\":" + (config.adaptive ? "true" : "false") + ",\"divisor\":" + std::to_string(core.divisor) +
                ",\"min_divisor\":" + std::to_string(config.min_divisor) + ",\"max_divisor\":" + std::to_string(config.max_divisor) + ",\"target_fps\":" + std::to_string(core.divisor ? refresh_hz / core.divisor : 0) +
                ",\"frames\":" + std::to_string(frames) + ",\"waits\":" + std::to_string(waits) + ",\"late\":" + std::to_string(late) +
                ",\"wait_ms_mean\":" + std::to_string(waits ? wait_ms / double(waits) : 0) + ",\"work_ms_max\":" + std::to_string(work_ms_max) +
                ",\"divisor_changes\":" + std::to_string(core.changes) +
                ",\"interval_refreshes\":[" + std::to_string(hist[0]) + "," + std::to_string(hist[1]) + "," + std::to_string(hist[2]) + "," + std::to_string(hist[3]) + "," + std::to_string(hist[4]) + "]}");
        } catch (...) {}
        frames = waits = late = 0; wait_ms = 0; work_ms_max = 0; for (auto& h : hist) h = 0;
    }
};
inline Pacer& pacer() noexcept { static Pacer p; return p; }
inline bool requested() noexcept { auto& p = pacer(); if (!p.configured) p.configure(); return p.available; }
inline void before_present() noexcept { pacer().before_present(); }
}
