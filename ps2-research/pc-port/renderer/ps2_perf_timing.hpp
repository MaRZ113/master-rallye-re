#pragma once
// PERF2 (docs/perf2): opt-in PS2PerfTiming=1 per-category QPC timing of the overlay's per-draw work. Off by default;
// when off every timer is one predictable branch. Records `ps2_perf_timing` to the session log every
// PS2PerfWindow frames (default 300) with calls/frame, us/frame and the slowest single call per category.
#include <windows.h>
#include <array>
#include <cstdint>
#include <cstdio>
#include <string>

namespace gfx2::ps2port::perf {

enum Category : unsigned {
    Certificate, RaceCertificate, HudContext, Participants, FleetCar, FleetWheel, LampEntry, RaceEntry, WheelEntry,
    FrontendEntry, ReflectionSnapshot, ReflectionClassify, GeometryHash, CategoryCount
};
inline constexpr const char* kCategoryNames[CategoryCount] = {
    "certificate", "race_certificate", "hud_context", "participant_table", "fleet_car", "fleet_wheel", "lamp_entry",
    "race_entry", "wheel_entry", "frontend_entry", "reflection_snapshot", "reflection_classify", "geometry_hash"};

struct Stat { uint64_t calls = 0, ticks = 0, max = 0; };
struct State {
    bool enabled = false; unsigned window = 300;
    uint64_t device = UINT64_MAX, first_frame = UINT64_MAX, last_frame = UINT64_MAX;
    std::array<Stat, CategoryCount> stats{};
    double tick_us = 0;
};
inline State& state() noexcept { static State s; return s; }
inline bool enabled() noexcept { return state().enabled; }
inline void configure(bool on, unsigned window) noexcept {
    auto& s = state(); s = {}; s.enabled = on; s.window = window < 30 ? 30 : window > 6000 ? 6000 : window;
    LARGE_INTEGER f{}; QueryPerformanceFrequency(&f); s.tick_us = f.QuadPart ? 1e6 / double(f.QuadPart) : 0;
}
inline uint64_t now() noexcept { LARGE_INTEGER t{}; QueryPerformanceCounter(&t); return uint64_t(t.QuadPart); }

// Writer is called with the finished record; frames are counted from the draw entries that call frame().
template <class Writer> void frame(uint64_t device, uint64_t frame_number, Writer&& write) noexcept {
    auto& s = state(); if (!s.enabled) return;
    if (s.device != device || s.first_frame == UINT64_MAX || frame_number < s.first_frame) {
        s.device = device; s.first_frame = s.last_frame = frame_number; s.stats = {}; return; }
    s.last_frame = frame_number;
    const uint64_t frames = frame_number - s.first_frame; if (frames < s.window) return;
    try {
        std::string r = "{\"type\":\"ps2_perf_timing\",\"frames\":" + std::to_string(frames) + ",\"first_frame\":" + std::to_string(s.first_frame) + ",\"categories\":{";
        bool first = true;
        for (unsigned i = 0; i < CategoryCount; ++i) { const auto& x = s.stats[i]; if (!x.calls) continue;
            char buf[192]; std::snprintf(buf, sizeof(buf), "%s\"%s\":{\"calls_per_frame\":%.1f,\"us_per_frame\":%.1f,\"max_us\":%.1f}",
                first ? "" : ",", kCategoryNames[i], double(x.calls) / double(frames), double(x.ticks) * s.tick_us / double(frames), double(x.max) * s.tick_us);
            r += buf; first = false; }
        r += "}}"; write(r);
    } catch (...) {}
    s.first_frame = frame_number; s.stats = {};
}

class Timer {
    unsigned c_; uint64_t t0_;
public:
    explicit Timer(unsigned c) noexcept : c_(c), t0_(enabled() ? now() : 0) {}
    ~Timer() { if (!t0_) return; const uint64_t d = now() - t0_; auto& x = state().stats[c_]; ++x.calls; x.ticks += d; if (d > x.max) x.max = d; }
    Timer(const Timer&) = delete; Timer& operator=(const Timer&) = delete;
};

}  // namespace gfx2::ps2port::perf
