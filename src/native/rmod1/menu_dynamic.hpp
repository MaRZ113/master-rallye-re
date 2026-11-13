#pragma once
// Dynamic row visibility for native frontend screens (Menu Builder "visible" rows, Extra Options Vehicle Select rows).
//
// A row is a set of eggs (button, value text, arrows) with one Button ID and its Up/Down neighbours. While the row's
// provider is unavailable the row is hidden:
//   * every egg is parked off-screen: its en2d translation x (en2d at egg+0x4C, x at +0x54; the same field Menu
//     Builder's static Hide sets at compile time, because native button AIs redraw their eggs whatever "en2d Visible"
//     says) is set to kParkedX and restored when the row comes back; re-asserted every frame while hidden;
//   * focus that lands on the row (UI/Active = its Button ID, set by a native Up/Down path or a mouse) continues in
//     the same direction to the next visible row, so Up/Down walk over hidden rows like a retail screen without them;
//   * the caller swallows the row's command (the focus never rests there, so this is a second line only).
// Opt-in per row: screens without rows are not touched.
#include <cstdint>
#include <cstring>
#include <functional>
#include <string>
#include <vector>

namespace menu_dynamic {

inline constexpr float kParkedX = -10000.0f;

struct Row {
    int button = 0, up = 0, down = 0;
    std::vector<std::string> eggs;
    bool hidden = false;
    std::vector<float> home;   // original x per egg (valid while hidden)
};

struct Host {
    std::function<uintptr_t(const std::string&)> en2d;   // live en2d object of an egg, 0 = absent
    std::function<int()> active;
    std::function<void(int)> set_active;
    std::function<void(const std::string&)> log;
};

struct State {
    int previous = -1;   // focus seen on the last frame (direction of travel)
    void reset() { previous = -1; }
};

inline bool read_x(uintptr_t en2d, float& x) {
    if (!en2d) return false;
    std::memcpy(&x, reinterpret_cast<const void*>(en2d + 0x54), 4);
    return true;
}
inline void write_x(uintptr_t en2d, float x) { if (en2d) std::memcpy(reinterpret_cast<void*>(en2d + 0x54), &x, 4); }

// available[i] = row i has choices for the current state. Call once per frame, before the screen's own tick.
inline void update(std::vector<Row>& rows, const std::vector<bool>& available, State& state, const Host& host) {
    for (size_t i = 0; i < rows.size(); ++i) {
        auto& r = rows[i];
        const bool hide = i < available.size() && !available[i];
        if (hide) {
            if (!r.hidden) r.home.assign(r.eggs.size(), kParkedX);
            for (size_t e = 0; e < r.eggs.size(); ++e) {
                const uintptr_t en = host.en2d(r.eggs[e]);
                float x = 0;
                if (!read_x(en, x)) continue;
                if (x != kParkedX) { r.home[e] = x; write_x(en, kParkedX); }
            }
            if (!r.hidden && host.log) host.log("ROW_HIDDEN button=" + std::to_string(r.button));
            r.hidden = true;
        } else if (r.hidden) {
            for (size_t e = 0; e < r.eggs.size(); ++e)
                if (r.home[e] != kParkedX) write_x(host.en2d(r.eggs[e]), r.home[e]);
            r.hidden = false;
            if (host.log) host.log("ROW_SHOWN button=" + std::to_string(r.button));
        }
    }
    // Focus: walk over hidden rows in the direction of travel.
    const int now = host.active();
    int at = now; bool decided = false, upward = false;
    for (size_t step = 0; step <= rows.size(); ++step) {
        const Row* r = nullptr;
        for (auto& x : rows) if (x.hidden && x.button == at) { r = &x; break; }
        if (!r) break;
        if (!decided) { upward = state.previous == r->down; decided = true; }
        at = upward ? r->up : r->down;
    }
    if (at != now) {
        host.set_active(at);
        if (host.log) host.log("FOCUS_SKIPPED " + std::to_string(now) + " -> " + std::to_string(at));
    }
    state.previous = at;
}

// A screen was (re)entered. Eggs that are still parked (an egg object that survived) go back to their place first;
// for rebuilt eggs this writes the authored x again. Then every row starts visible and is re-evaluated.
inline void entered(std::vector<Row>& rows, State& state, const Host& host) {
    for (auto& r : rows) {
        if (r.hidden)
            for (size_t e = 0; e < r.eggs.size() && e < r.home.size(); ++e) {
                float x = 0;
                const uintptr_t en = host.en2d(r.eggs[e]);
                if (r.home[e] != kParkedX && read_x(en, x) && x == kParkedX) write_x(en, r.home[e]);
            }
        r.hidden = false; r.home.clear();
    }
    state.reset();
}

inline bool hidden_button(const std::vector<Row>& rows, int button) {
    for (auto& r : rows) if (r.hidden && r.button == button) return true;
    return false;
}

} // namespace menu_dynamic
