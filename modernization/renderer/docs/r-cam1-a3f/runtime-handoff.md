# R-CAM1-A3f runtime handoff

Use the confirmed pristine retail build, an offline one-player France1 race,
and Borderless mode. Keep the normal Classic+ settings unchanged.

1. Start with the stock camera and press F8. Confirm there is no activation
   snap.
2. Leave the mouse still for roughly 0.3 seconds. Confirm the tilted horizon
   levels smoothly, without moving the camera or changing its view direction.
3. Fly and look around. Confirm yaw/pitch do not add roll and movement still
   responds with the same bindings and speed modifiers.
4. Pause the race. Confirm mouse look and movement continue while the game
   simulation remains paused and the native pause menu still works.
5. Press F8 again and confirm the current stock camera resumes.
6. Optionally repeat with `AutoLevelHorizon=0`; the original native roll should
   remain visible.

If orientation fails, capture one F10 while Freecam is active. The snapshot
should show the mode, signed current roll, zero target roll in auto-level mode,
progress, orientation validity, and unchanged camera scope/restore counters.
Do not make another long lifecycle capture if this short flight is healthy.

Pass requires no activation snap, a stable level horizon after the configured
transition, predictable look controls, working pause-time flight, and clean
stock-camera restoration. Automated tests are not runtime confirmation.
