#pragma once
// Display-locked frame pacing (PERF-PACING1). Pure scheduler; Win32 glue in frame_pacer_native.hpp.
//
// Why: the game advances its world with a fixed 30 Hz simulation plus interpolation, driven by a clock that adds the
// mean of the last 8 frame intervals (MRallye.exe 0x5FD8A0, "SmoothTime"; ring size 8 at 0x5AF71C). The renderer itself
// has no VSync or limiter in Windowed/Borderless mode (D3D8 windowed present is composed by DWM). With an uncapped
// ~100-125 fps on a 180 Hz display each frame stays on screen for 1 or 2 refreshes in an irregular pattern while the
// game time between frames is constant: the motion judders although every frame time is short.
//
// What: before Present, wait until the refresh that is `divisor` refreshes after the previous present (DWM composition
// timing: last vblank QPC, refresh counter, refresh period), then present just after that vblank. Every frame is then
// composed for exactly `divisor` refreshes and the game's loop interval (and so its SmoothTime step) is constant.
// The divisor is the smallest one whose rate is <= MaxFps; Adaptive raises it when frames repeatedly miss their slot
// and lowers it again after sustained headroom. A late frame is presented at once and the schedule re-aligns.
#include <cstdint>
#include <algorithm>
#include <cmath>
#include <array>
namespace gfx2::pacing {

struct Config {
    unsigned mode = 1;        // 0 = off (uncapped, retail behavior), 1 = display-locked
    unsigned max_fps = 100;   // highest pacing rate; refresh / divisor stays at or below it
    bool adaptive = true;     // move the divisor with sustained misses / headroom
    unsigned min_divisor = 1; // derived from max_fps and refresh
    unsigned min_fps = 55;    // adaptive never drops below this rate (180 Hz: 60 fps, never 45)
    unsigned max_divisor = 4; // derived from min_fps and refresh
};

inline unsigned max_divisor_for(double refresh_hz, unsigned min_fps, unsigned floor_k) noexcept {
    unsigned k = std::max(1u, floor_k);
    if (!(refresh_hz > 0) || !min_fps) return k;
    while (k < 8 && refresh_hz / (k + 1) >= double(min_fps) - 0.5) ++k;
    return k;
}
inline unsigned divisor_for(double refresh_hz, unsigned max_fps) noexcept {
    if (!(refresh_hz > 0) || !max_fps) return 1;
    unsigned k = 1;
    while (k < 8 && refresh_hz / k > double(max_fps) + 0.5) ++k;
    return k;
}

// Pure scheduler. Times are QPC ticks.
struct Plan { bool wait = false; int64_t until = 0; uint64_t refresh = 0; bool late = false; };
struct Core {
    unsigned divisor = 1;
    uint64_t last_refresh = 0; bool have_last = false;
    // adaptive state (per window of `window` frames)
    unsigned window_frames = 0, window_late = 0, calm_windows = 0, busy_windows = 0;
    double window_work_max = 0;   // CPU work (previous present return -> this present call), in refresh periods
    unsigned changes = 0;

    // vblank: QPC of refresh number `counter`; period: QPC ticks per refresh. offset: ticks after the vblank to present.
    Plan plan(int64_t now, int64_t vblank, uint64_t counter, int64_t period, int64_t offset) noexcept {
        Plan p{};
        if (period <= 0) return p;
        const int64_t since = now - vblank;
        const uint64_t current = counter + uint64_t(since >= 0 ? since / period : 0);   // last vblank at or before now
        if (!have_last || current + 64 < last_refresh || current > last_refresh + 64) {      // first frame or a long stall
            have_last = true; last_refresh = current; p.refresh = current; return p;
        }
        const uint64_t target = last_refresh + divisor;
        if (current >= target) {   // too late for the slot: present now and restart the cadence here
            p.late = current > target || (now - (vblank + int64_t(current - counter) * period)) > offset + period / 2;
            last_refresh = current; p.refresh = current; return p;
        }
        p.wait = true; p.refresh = target; p.until = vblank + int64_t(target - counter) * period + offset;
        last_refresh = target;
        return p;
    }
    // Called once per frame with the frame's CPU work in refresh periods. Returns true when the divisor changed.
    // A stall (work > 4 slots: loading, alt-tab) is neither a late frame nor a work sample. Raising needs >10 % late frames
    // in a window; lowering needs 4 calm windows whose 90th-percentile work fits 85 % of the smaller slot.
    std::array<float, 128> work_samples{}; unsigned work_count = 0;
    bool adapt(const Config& c, double work_periods, bool late, unsigned window = 90) noexcept {
        const bool stall = work_periods > 4.0 * double(divisor);
        ++window_frames;
        if (!stall) { if (late) ++window_late; if (work_count < work_samples.size()) work_samples[work_count++] = float(work_periods); window_work_max = std::max(window_work_max, work_periods); }
        if (window_frames < window) return false;
        double p90 = 0;
        if (work_count) { std::sort(work_samples.begin(), work_samples.begin() + work_count); p90 = work_samples[std::min<unsigned>(work_count - 1, unsigned(work_count * 9 / 10))]; }
        bool changed = false;
        const unsigned floor_k = std::max(1u, c.min_divisor);
        if (divisor < floor_k) { divisor = floor_k; changed = true; }
        else if (divisor > std::max(floor_k, c.max_divisor)) { divisor = std::max(floor_k, c.max_divisor); changed = true; }
        else if (c.adaptive && window_late * 5 > window_frames) {   // >20 % late in two consecutive windows, never below MinFps
            if (++busy_windows >= 2 && divisor < c.max_divisor) { ++divisor; busy_windows = 0; calm_windows = 0; changed = true; }
        }
        else if (c.adaptive && divisor > floor_k && window_late * 50 <= window_frames && work_count && p90 < 0.85 * double(divisor - 1)) {
            busy_windows = 0; if (++calm_windows >= 4) { --divisor; calm_windows = 0; changed = true; }   // ~4 windows of clear headroom
        } else { calm_windows = 0; if (window_late * 5 <= window_frames) busy_windows = 0; }
        window_frames = window_late = 0; window_work_max = 0; work_count = 0;
        if (changed) ++changes;
        return changed;
    }
};
}
