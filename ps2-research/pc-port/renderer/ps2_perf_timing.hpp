#pragma once
// PERF2 (docs/perf2): opt-in PS2PerfTiming=1 per-category QPC timing of the overlay's per-draw work. Off by default;
// when off every timer is one predictable branch. Records `ps2_perf_timing` to the session log every
// PS2PerfWindow frames (default 300) with calls/frame, us/frame and the slowest single call per category.
// FPS1 (docs/perf-fps1): the record also carries the frame time of the window (first indexed draw to first indexed
// draw: avg/p50/p95/p99/max ms) and per-effect categories. PS2PerfBypassKey (default F7, only with PS2PerfTiming=1)
// cycles a DIAGNOSTIC bypass of draw-time effects for in-scene A/B; each change starts a new window.
#include <windows.h>
#include <algorithm>
#include <array>
#include <cstdint>
#include <cstdio>
#include <string>

namespace gfx2::ps2port::perf {

enum Category : unsigned {
    Certificate, RaceCertificate, HudContext, Participants, FleetCar, FleetWheel, LampEntry, RaceEntry, WheelEntry,
    FrontendEntry, ReflectionSnapshot, ReflectionClassify, GeometryHash,
    Atmosphere, Water, Ground, XTrail, XTrailGlass, VehiclePartition, ReflectionNote, HudCapture,
    UiGrass, UiSpline, UiBirds, UiRigid, UiCollision, UiCourse, UiReflection, PresentPass, BaselineCertificate,
    AtmoWorld, AtmoUpload, AtmoBody, AtmoHeadlight, AtmoSunWorld, AtmoSunUi,
    AtmoBodyGate, AtmoBodyOwner, AtmoBodyGeometry, AtmoBodyShade, Grime,
    CategoryCount
};
inline constexpr const char* kCategoryNames[CategoryCount] = {
    "certificate", "race_certificate", "hud_context", "participant_table", "fleet_car", "fleet_wheel", "lamp_entry",
    "race_entry", "wheel_entry", "frontend_entry", "reflection_snapshot", "reflection_classify", "geometry_hash",
    "atmosphere", "water", "ground_detail", "xtrail", "xtrail_glass", "vehicle_partition", "reflection_note", "hud_capture",
    "ui_grass", "ui_spline", "ui_birds", "ui_rigid_props", "ui_collision", "ui_course_objects", "ui_reflection",
    "present_pass", "baseline_certificate",
    "atmo_world", "atmo_upload", "atmo_body", "atmo_headlight", "atmo_sun_world", "atmo_sun_ui",
    "atmo_body_gate", "atmo_body_owner", "atmo_body_geometry", "atmo_body_shade", "grime"};

// DIAGNOSTIC bypass steps (PS2PerfBypassKey). Only draw-time effects whose skip falls back to the native draw or to
// no extra draw; vehicle models, reflections and the HUD are never bypassed (their continuity spans frames).
enum Bypass : unsigned { BypassGrass = 1, BypassGround = 2, BypassWater = 4, BypassLive = 8, BypassPresent = 16 };
inline constexpr unsigned kBypassSteps[] = {0, BypassGrass, BypassGround, BypassWater, BypassLive, BypassPresent,
                                            BypassGrass | BypassGround | BypassWater | BypassLive | BypassPresent};
inline constexpr const char* kBypassNames[] = {"none", "grass", "ground_detail", "water", "live_objects", "motion_blur", "all"};
inline constexpr unsigned kBypassStepCount = sizeof(kBypassSteps) / sizeof(kBypassSteps[0]);
// PERF-ATMO1 (docs/perf-atmo1): DIAGNOSTIC atmosphere A/B (PS2PerfAtmosphereKey, default F6; F8 is the free camera),
// only with PS2PerfTiming=1. AtmoRing is not a bypass:
// it switches the private vertex upload from the shared MANAGED buffer (Lock 0) to a DYNAMIC ring (NOOVERWRITE).
enum AtmoBypass : unsigned { AtmoHeadlights = 1, AtmoGlints = 2, AtmoSun = 4, AtmoWorldNative = 8, AtmoRing = 16, AtmoBodies = 32 };
inline constexpr unsigned kAtmoSteps[] = {0, AtmoHeadlights, AtmoGlints, AtmoSun, AtmoRing, AtmoWorldNative, AtmoBodies,
                                          AtmoHeadlights | AtmoGlints | AtmoSun | AtmoWorldNative | AtmoBodies};
inline constexpr const char* kAtmoNames[] = {"none", "headlights", "lamp_glints", "sun_fx", "ring_upload", "world_native", "bodies", "all"};
inline constexpr unsigned kAtmoStepCount = sizeof(kAtmoSteps) / sizeof(kAtmoSteps[0]);
inline constexpr unsigned kMaxFrameSamples = 6000;

struct Stat { uint64_t calls = 0, ticks = 0, max = 0; };
struct State {
    bool enabled = false; unsigned window = 300;
    uint64_t device = UINT64_MAX, first_frame = UINT64_MAX, last_frame = UINT64_MAX;
    std::array<Stat, CategoryCount> stats{};
    double tick_us = 0;
    uint64_t frame_start = 0; unsigned samples = 0; std::array<float, kMaxFrameSamples> frame_ms{};
    unsigned bypass_key = VK_F7, bypass_step = 0; bool key_down = false;
    unsigned atmo_key = VK_F6, atmo_step = 0; bool atmo_down = false;
};
inline State& state() noexcept { static State s; return s; }
inline bool enabled() noexcept { return state().enabled; }
inline bool bypassed(unsigned effect) noexcept { const auto& s = state(); return s.enabled && (kBypassSteps[s.bypass_step] & effect); }
inline bool atmo(unsigned effect) noexcept { const auto& s = state(); return s.enabled && (kAtmoSteps[s.atmo_step] & effect); }
inline void configure(bool on, unsigned window, unsigned bypass_key = VK_F7, unsigned atmo_key = VK_F6) noexcept {
    auto& s = state(); s = {}; s.enabled = on; s.window = window < 30 ? 30 : window > kMaxFrameSamples ? kMaxFrameSamples : window;
    s.bypass_key = bypass_key; s.atmo_key = atmo_key;
    LARGE_INTEGER f{}; QueryPerformanceFrequency(&f); s.tick_us = f.QuadPart ? 1e6 / double(f.QuadPart) : 0;
}
inline uint64_t now() noexcept { LARGE_INTEGER t{}; QueryPerformanceCounter(&t); return uint64_t(t.QuadPart); }

inline void reset_window(State& s, uint64_t device, uint64_t frame_number, uint64_t t) noexcept {
    s.device = device; s.first_frame = s.last_frame = frame_number; s.stats = {}; s.samples = 0; s.frame_start = t;
}
inline std::string frame_time_json(State& s) {
    if (!s.samples) return "null";
    float* b = s.frame_ms.data(); float* e = b + s.samples; double sum = 0; for (float* p = b; p != e; ++p) sum += *p;
    auto pct = [&](double q) { float* k = b + unsigned(q * double(s.samples - 1) + .5); std::nth_element(b, k, e); return double(*k); };
    const double avg = sum / double(s.samples), p50 = pct(.50), p95 = pct(.95), p99 = pct(.99), mx = double(*std::max_element(b, e));
    char buf[256]; std::snprintf(buf, sizeof(buf), "{\"samples\":%u,\"fps\":%.1f,\"avg_ms\":%.2f,\"p50_ms\":%.2f,\"p95_ms\":%.2f,\"p99_ms\":%.2f,\"max_ms\":%.2f}",
        s.samples, avg > 0 ? 1000.0 / avg : 0.0, avg, p50, p95, p99, mx);
    return buf;
}

// Writer is called with the finished record; frames are counted from the draw entries that call frame().
template <class Writer> void frame(uint64_t device, uint64_t frame_number, Writer&& write) noexcept {
    auto& s = state(); if (!s.enabled) return;
    if (frame_number == s.last_frame && s.device == device) return;
    const uint64_t t = now();
    if (s.device != device || s.first_frame == UINT64_MAX || frame_number < s.first_frame) { reset_window(s, device, frame_number, t); return; }
    // One sample per new frame: the time since the first indexed draw of the previous frame.
    if (s.samples < kMaxFrameSamples) s.frame_ms[s.samples++] = float(double(t - s.frame_start) * s.tick_us / 1000.0);
    s.frame_start = t; s.last_frame = frame_number;
    const bool down = (GetAsyncKeyState(int(s.bypass_key)) & 0x8000) != 0;
    if (down && !s.key_down && GetForegroundWindow()) {
        s.bypass_step = (s.bypass_step + 1) % kBypassStepCount;
        try { write(std::string("{\"type\":\"ps2_perf_bypass\",\"frame\":") + std::to_string(frame_number) + ",\"bypass\":\"" + kBypassNames[s.bypass_step] + "\"}"); } catch (...) {}
        s.key_down = down; reset_window(s, device, frame_number, t); return;
    }
    s.key_down = down;
    const bool atmo_down = (GetAsyncKeyState(int(s.atmo_key)) & 0x8000) != 0;
    if (atmo_down && !s.atmo_down && GetForegroundWindow()) {
        s.atmo_step = (s.atmo_step + 1) % kAtmoStepCount;
        try { write(std::string("{\"type\":\"ps2_perf_atmo_bypass\",\"frame\":") + std::to_string(frame_number) + ",\"atmo\":\"" + kAtmoNames[s.atmo_step] + "\"}"); } catch (...) {}
        s.atmo_down = atmo_down; reset_window(s, device, frame_number, t); return;
    }
    s.atmo_down = atmo_down;
    const uint64_t frames = frame_number - s.first_frame; if (frames < s.window) return;
    try {
        std::string r = "{\"type\":\"ps2_perf_timing\",\"frames\":" + std::to_string(frames) + ",\"first_frame\":" + std::to_string(s.first_frame) +
            ",\"bypass\":\"" + kBypassNames[s.bypass_step] + "\",\"atmo\":\"" + kAtmoNames[s.atmo_step] + "\",\"frame_time\":" + frame_time_json(s) + ",\"categories\":{";
        bool first = true;
        for (unsigned i = 0; i < CategoryCount; ++i) { const auto& x = s.stats[i]; if (!x.calls) continue;
            char buf[192]; std::snprintf(buf, sizeof(buf), "%s\"%s\":{\"calls_per_frame\":%.1f,\"us_per_frame\":%.1f,\"max_us\":%.1f}",
                first ? "" : ",", kCategoryNames[i], double(x.calls) / double(frames), double(x.ticks) * s.tick_us / double(frames), double(x.max) * s.tick_us);
            r += buf; first = false; }
        r += "}}"; write(r);
    } catch (...) {}
    reset_window(s, device, frame_number, t);
}

// Adds one measured span (QPC ticks) to a category; for staged timings inside one call.
inline void add(unsigned c, uint64_t ticks) noexcept { if (!enabled()) return; auto& x = state().stats[c]; ++x.calls; x.ticks += ticks; if (ticks > x.max) x.max = ticks; }

class Timer {
    unsigned c_; uint64_t t0_;
public:
    explicit Timer(unsigned c) noexcept : c_(c), t0_(enabled() ? now() : 0) {}
    ~Timer() { if (!t0_) return; const uint64_t d = now() - t0_; auto& x = state().stats[c_]; ++x.calls; x.ticks += d; if (d > x.max) x.max = d; }
    Timer(const Timer&) = delete; Timer& operator=(const Timer&) = delete;
};

}  // namespace gfx2::ps2port::perf
