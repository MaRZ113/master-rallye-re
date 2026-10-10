# R-CAM1-A3f.2 runtime handoff

This candidate changes only Freecam elapsed-time acquisition. The user-confirmed A3f.1 controls and camera behavior remain the baseline; this handoff checks whether sub-millisecond timing removes the remaining small translation micro-stutter.

Use the newly built `modernization/renderer/.build-msvc/Release/d3d8.dll` with the same exact retail executable, configuration and scene used for the successful A3f.1 check. Keep movement speed/smoothing, FOV, display mode, AF/MSAA, control preset and camera route unchanged. Prefer the same paused France1 position or other repeatable scene.

1. Start a race, enable Freecam and hold a straight translation key for about 10 seconds at ordinary speed. Repeat at the same route using the prior A3f.1 DLL if it is still available. Compare the small visual cadence changes, not overall speed or acceleration feel.
2. Repeat with one diagonal direction, then stop input and verify the existing smooth coast remains unchanged.
3. Pause the game while continuing Freecam translation for several seconds; it should still move. Release the key and confirm no large jump on resume.
4. Alt+Tab away and back, then continue translating. There should be no elapsed-time jump, cursor flicker, stale input, or changed camera scope behavior.
5. Capture F10 after a few seconds of active movement. Confirm `flight_clock_source` is `qpc`, frequency is positive and stable, `flight_dt_last_ms` is no longer restricted to integer milliseconds, and `flight_clock_invalid_samples` remains zero. A `get_tick_count64` source is acceptable only if the platform's QPC initialization/query failed; the fallback must report 1000 Hz and must not show a domain-transition spike.
6. Recheck toggle off/on, mouse look, speed keys/wheel, horizon, HUD/vehicle rendering, and quit as a short lifecycle smoke test.

PASS: translation cadence is visibly smoother than the A3f.1 baseline, ordinary speed and acceleration feel are preserved, pause flight remains possible, focus return produces no jump, and F10 reports a stable valid clock. FAIL: stutter remains materially unchanged, movement speed/response changes, a focus/pause jump appears, or camera/renderer lifecycle regresses. Synthetic tests and successful DLL validation alone do not establish this runtime pass.
