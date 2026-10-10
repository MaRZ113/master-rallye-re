# R-CAM1-A3g runtime handoff

The candidate is ready for human runtime validation. Keep the same pristine retail executable, display mode, AF/MSAA, interface mode, course, and renderer configuration used for the successful A3f.2 retest. Use `modernization/renderer/MRRRenderer.ini.example` as the setting reference and enable FreeCamera explicitly in the test INI. Do not compare different builds or change multiple camera settings at once.

## Cinematic FOV

1. Start a France1 race, pause the game, and activate Freecam with F8. Confirm the camera starts at the current view without a lens snap.
2. Press Z once, release, and observe one smooth narrower-lens transition. Press X once and observe a smooth wider-lens transition. Holding either key must not produce an unbounded per-frame jump.
3. Repeat while driving slowly, while parked, and while flying. The view should zoom without moving the camera or changing movement speed, mouse sensitivity, or horizon.
4. Set `CinematicVerticalFOVDegrees=0` and repeat with GameplayFOV both off and on. The initial lens should inherit the effective current view. Then test a positive configured starting FOV.
5. Test minimum and maximum limits. FOV changes must retain expected edge visibility and native traversal without popping/culling that disagrees with the image.
6. Turn Freecam off. The stock/gameplay projection must return immediately. Reactivate and confirm there is no stale lens state.

## Manual roll

1. With `AutoLevelHorizon=1`, activate Freecam on a view with inherited roll. Confirm the existing 0.30-second leveling remains smooth.
2. During initial leveling, hold C briefly, release it, and confirm the manual bank remains after the native roll finishes leveling. Positive `manual_roll_degrees` is Roll Left; V should produce the opposite sign.
3. Move the mouse through yaw and pitch with a nonzero manual offset. The offset should remain steady and the camera basis should remain stable, including near vertical look directions.
4. Hold B. The manual offset should ease back to zero without overshoot. Repeat with `AutoLevelHorizon=0`; inherited stock roll should remain while the manual layer still resets independently.
5. Confirm the configured maximum angle, focus loss/return, Freecam off/on, pause-time roll, and simultaneous FOV + roll. Camera position and gameplay should not change because of roll.

## F10 evidence and verdict

Capture one F10 record during an active lens transition and one with a retained manual roll. The Freecam snapshot should show `fov_source`, `effective_vertical_fov`, `target_vertical_fov`, `effective_horizontal_fov`, `fov_transition_active`, `projection_vfov`, `projection_frustum_synchronized=true`, `fov_validation_reason=projection_matches_cpu_frustum`, `manual_roll_degrees`, `manual_roll_target_degrees`, and `manual_roll_transition_active`. During reset, the roll target should be zero while the current offset eases toward zero.

PASS requires smooth FOV and manual roll in a paused race, correct synchronized FOV/culling, no camera translation caused by roll, stable auto-level behavior, limit enforcement, stock projection restoration on Freecam off, and no lifecycle regression. FAIL includes lens/frustum mismatch, projection or camera snap, roll drift under yaw/pitch, auto-level fighting manual roll, state persisting after Freecam off, focus-return jumps, or any renderer/race regression. Synthetic tests and DLL verification do not constitute the runtime pass.
