# Global HUD Hide — first runtime handoff

Candidate DLL: `modernization/renderer/.build-msvc/Release/d3d8.dll`. Keep the accepted DLL and INI backed up; install the candidate through the user's normal local test procedure. The pristine EXE is not modified. Use the existing exact-retail installation and do not change other renderer settings during the first pass.

The default is `[HUD] ToggleEnabled=1`, `ToggleKey=H`, `HiddenAtStartup=0`, `PreserveMenus=1`. If `[HUD]` is absent, the existing `[FreeCameraKeys] ToggleCleanView=H` remains an alias. F10 stays reserved. Enable `[Trace] Enabled=1` only if captures are needed, then restart the game after editing the INI.

1. Start offline France1 and drive with the stock camera. Press H once. The HUD should disappear while the world, physics, and native input continue. Switch stock cameras; the HUD should stay hidden.
2. Press H again. All suppressed race HUD packets should return. Compare the position, timer, lap, tachometer/speed, progress, GPS, and status indicators.
3. Hide the HUD, enter and leave Freecam, and confirm the preference remains hidden until H is pressed again. Pause without Freecam and confirm the interactive pause menu remains visible. In paused Freecam, verify the existing Clean View result still works from the same H preference.
4. While hidden, return to the main menu, navigate settings and car/track selection, and start another supported race. The menu must remain usable and the preference must still hide the new race HUD.
5. Check results/loading text and progress. Minimize/restore or Alt+Tab once. H must not phantom-toggle on focus regain; the device must recover without a crash.
6. Start or enter a supported single-player replay and press H while replay playback is active. The race HUD should disappear while the replay controls remain usable. Pause the replay; the interactive pause controls must remain visible. F10 should report `current_ui_context=replay_running`, `replay_mode=true`, and positive `suppressed_hud_draws` when the capture frame contains an eligible HUD draw.
7. In F10, inspect `hud_hide.requested_hidden`, `effective_hidden`, `policy_ready`, `current_ui_context`, `suppressed_hud_draws`, and `rejected_ambiguous_draws`. A key edge by itself is not a suppression pass.

PASS requires the whole relevant race HUD to disappear and restore in both ordinary gameplay and active replay, replay controls and the native pause menu to remain usable, frontend/results/loading screens to remain visible, and no ambiguous or stale context to suppress draws. FAIL if any expected HUD part remains, replay controls/menu/result/loading UI disappears, a draw is suppressed with an uncertified context, or focus/reset causes a phantom toggle or crash. If only selected HUD elements remain, capture F10 with them visible and identify the missed native path before broadening classification.

Return the session JSONL and two F10 captures if anything differs: `H-hidden` during active stock-camera driving and `menu-hidden-preference` after returning to the frontend. No runtime PASS is claimed by the static test report.
