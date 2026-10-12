# R-CAM1-A3h.3 Runtime Handoff

## Setup

Use the candidate Win32 `d3d8.dll` from `.build-msvc/Release/` with the exact pristine retail executable. Keep the existing game EXE and accepted configuration unchanged. In `MRRRenderer.ini`, enable:

```ini
[FreeCamera]
Enabled=1
CleanViewPilot=1
CleanViewEnabled=0

[FreeCameraKeys]
ToggleCleanView=H
```

Launch a normal Quick Race, enter gameplay, activate Freecam with the existing Freecam key, and pause using the native game pause control. Only then press H once. H toggles the single Clean View request; press it again to restore the full native UI. This pilot does not consume the key.

## Observe

1. With Freecam off or pause closed, confirm H does not hide UI.
2. With Freecam active and native pause open, press H. The current verified native UI consumer stream should disappear while the 3D world remains visible. Press H again and confirm it returns.
3. Resume the race, Alt+Tab, and return. A request must disarm when pause/focus/context is lost; UI must render normally.
4. Quit normally. Confirm no crash or stuck UI state.
5. Use F10 during a short paused-Freecam sample. Preserve the bounded log and report `clean_view_requested`, `pause_menu_known`, `pause_menu_enabled`, `clean_view_suppressed_draws`, `clean_view_forwarded_unverified_draws`, `clean_view_last_admission_reason`, `clean_view_last_scope_reason`, and UI ownership capture provenance.

## Pass / fail

PASS: only the active exact UI consumer draw stream is suppressed while the exact-build, race, pause, Freecam, focus, device-scene, hook, identity, FVF, topology, and callsite gates all hold; the second H press restores UI immediately; leaving pause/focus or Freecam restores/disarms; the world and native game state continue; normal exit succeeds.

FAIL: any UI disappears with Freecam off, outside native pause, or outside the verified consumer; an unverified draw is skipped; UI remains hidden after disarm; the 3D scene stops; or the game hangs/crashes.

Please return the F10 JSONL and the result of the five checks. Until that visual check is done, the feature remains a pilot and the clean-view result is not considered runtime-confirmed.
