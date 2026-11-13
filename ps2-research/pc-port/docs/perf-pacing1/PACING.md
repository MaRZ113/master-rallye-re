# PERF-PACING1 — display-locked frame pacing

Status: **BUILT, awaiting the owner's run** (2026-11-12). Code: `renderer/frame_pacer.hpp`
(pure scheduler) and `renderer/frame_pacer_native.hpp` (Win32/DWM glue), called from `PS2PortExtension::color_present`
right before the native Present. `modernization/renderer` is not changed; pacing therefore needs the PS2Port overlay to be active. Tests:
`tests/atmosphere_tests.cpp` (PERF-PACING1 block).

## Symptom

The owner felt stutter in races, although the G0 probe pacing records showed short and even frame times after the probe
fix (`grime-*.jsonl`, about 2026-11-12 17:15–17:38: p50 8–10 ms, worst frame per 0.5 s window 10–19 ms, no window above 25 ms).

## Cause

* Game clock (MRallye.exe, `CONFIRMED_BY_EXE`): the main loop `0x5AFE30` reads QPC seconds (`0x64E370`), and
  `0x5FD8A0` ("SmoothTime") advances game time by the **mean of the last 8 frame intervals**. The ring size is 8, from
  `push 8` before the constructor `0x5FD750` at `0x5AF71C`. The simulation runs fixed 30 Hz ticks while game time ≥ tick/30.
  Rendering interpolates with alpha = (game time − previous tick) / (1/30). If game time is more than 1/6 s ahead of the ticks,
  the loop resets game time to the ticks.
* Renderer: Windowed/Borderless presents with `D3DPRESENT_INTERVAL_DEFAULT`, which does not wait for vblank in windowed D3D8, and with
  no frame limiter. DWM composes the latest frame at each refresh.
* DWM timing on this system (probe 2026-11-12): `qpcVBlank` is the vblank of the **next** composition (6–11 ms ahead)
  and `cRefresh` counts timing queries, not refreshes. The pacer therefore uses only the vblank phase and
  `qpcRefreshPeriod`, and counts refresh indices from its own origin, which is re-phased on every frame.
* Owner display: 180 Hz (AMD RX 6600, 1920×1080). At an uncapped 100–125 fps each frame stays on screen for 1 or 2
  refreshes in an irregular pattern, but the game time between frames is constant (SmoothTime). Constant motion per frame
  combined with uneven time on screen is judder. Frame-time statistics cannot show this.

## Fix

Before `Present`, the renderer reads DWM composition timing (`DwmGetCompositionTimingInfo`, resolved at run time)
and waits until the refresh that is `divisor` refreshes after the previous present. It then presents 5 % of a
refresh after that vblank, using a high-resolution waitable timer and a final yield spin of about 1 ms or less. Every frame is then composed for
exactly `divisor` refreshes, and the game loop interval, and with it the SmoothTime step, is constant.

* `divisor` = the smallest value with refresh/divisor ≤ `MaxFps` (default 100): 180 Hz → 90 fps, 144 Hz → 72 fps,
  60 Hz → 60 fps.
* Late frame: present at once and restart the cadence there. Adaptive mode raises the divisor when more than 10 % of the
  frames in a 90-frame window are late, and lowers it after 4 windows with no late frame and
  CPU work under 80 % of the smaller interval. It never goes above `MaxFps`.
* Only `[Display] Mode` 1 (Windowed) and 2 (Borderless) are paced. Stock, Exclusive and a failed DWM query keep the native present; this is logged once.

Config, `MRRRenderer.ini`:

```ini
[FramePacing]
Mode = 1        ; 0 = Off (uncapped), 1 = display-locked
MaxFps = 100
Adaptive = 1
```

Log: `frame_pacing` records in the session log. A `window` record every 10 s and a `divisor_changed` record on each change contain
refresh_hz, divisor, target_fps, frames, waits, late, wait_ms_mean, work_ms_max.

## Acceptance (owner run)

1. Same course and car as the stutter run, `Mode = 1`: motion is smooth. `frame_pacing` shows `target_fps` 90 and a low
   `late` count.
2. `Mode = 0` for A/B: the old judder returns.
3. Menus, loading, pause and replay keep working. Input latency is acceptable; pacing adds at most one refresh of waiting.

## Smoke run (build session, attract/menu, DLL 64a25755)

`frame_pacing` window records (10 s each): 819 frames, 819 waits, 0–1 late, `interval_refreshes` [0,0,819,0,0], so every
present is exactly 2 refreshes apart (90 fps at 180 Hz). A first build that trusted `cRefresh` paced only 133 of 1427 frames;
that is how the DWM quirk above was found.

## Follow-up (DLL 6e9944ea, 2026-11-12)

* Adaptive fix: a load stall (work > 4 slots) is neither a late frame nor a work sample. The step back down uses the 90th-percentile
  work (< 85 % of the smaller slot) instead of the window maximum. In the first build a race load raised the divisor to 3 for good.
  Attract smoke: 2 → 3 at the load, then back to 2 after about 5 s.
* PERF-ATMO3 (owner perf review): in the owner race logs, the heaviest 300-frame windows were 16–17 ms, of which `atmo_body` took
  3.4–4.8 ms and `atmo_body_shade` 2.2–3.4 ms. The relit-vertex cache only hit on byte-equal WORLD/VIEW, so every moving
  car missed. The relight depends only on the body rotation and, for the rim term, on the camera in body space. The cache now hits
  when the rotation differs by at most 0.008 per element (about 0.45°, Lambert error ≤ about 2/255) and the camera position in body space differs by at most 2 %, always
  compared with the pose the entry was shaded at. In attract (TV cameras) the hit rate rose from 5–10 % to 25–50 %, and `atmo_body_shade` fell from about 1.5 to
  0.4–1 ms. A chase camera in a race should hit more often. Log: `atmosphere_body_shade_cache` every 10 s.

## Long-race FPS drop (owner, 2026-11-12, DLL e452421c)

In the owner's runs (session 18:29 and others), frame time stepped 11.1 → 18.3 → 23.8 ms, which is exactly 2/3/4 refreshes (90 → 60 → 45 fps).
This was not a leak: earlier uncapped long races had a flat frame time (12.9 → 12.7 ms). The adaptive divisor raised the divisor on
clustered spikes (>10 % late in one 90-frame window) and never stepped back, because the measured work includes the native
Present. Fix: `MinFps` (default 55; on 180 Hz the divisor is at most 3, so never 45), and a raise needs two consecutive windows with more than 20 % late frames.
Attract smoke: the divisor goes 2 → 3 at the load and back to 2, `max_divisor` 3.
