# R-CAM1-A3g findings

## Scope and evidence

This change adds a Freecam-only cinematic vertical FOV and an independent manual roll controller. It reuses the existing exact-retail camera submission scope, QPC-derived `FlightInput.seconds`, `FrustumFrame`, and exact gameplay projection setter. It does not add a game patch site or change the scheduler bridge. Static code and synthetic/native tests are evidence for implementation behavior; visual game behavior still needs the human runtime pass.

## Default controls

Preset 0 uses WASD for planar movement, E/Q for vertical movement, LeftShift/LeftAlt for speed modifiers, F8 for Freecam, PageUp/PageDown and the mouse wheel for movement speed. E/Q replace the Space vertical binding because Space resumes the paused game. Custom preset users can still deliberately bind Space. FOV uses edge-triggered Z/X; roll uses held C/V, with B held to reset. These keys are configurable, and the window subclass continues forwarding native messages.

## Cinematic FOV

`CinematicFOVEnabled` only controls the Freecam lens. A configured initial `CinematicVerticalFOVDegrees=0` inherits the effective gameplay vertical FOV at activation, including ordinary GameplayFOV when enabled. A positive configured value becomes a smooth target. Z/X adjust the target by one bounded step on each key edge. The mouse wheel remains assigned to movement speed. The shared QPC delta is capped at 50 ms, and the first activation sample retains the visible lens even when smoothing is zero.

While Freecam is active, `GameFov::before_submit()` passes the controller's current vertical FOV to `FrustumFrame::begin()`. The projection override is allowed only at `GAMEPLAY_PROJECTION_RETURN_RVA`, on the render thread, while the current camera and projection match that synchronized scope. The same current VFOV is then used to form D3D projection `_11/_22`. If projection synthesis or the native setter rejects the override, the current scope is restored before stock projection fallback, preventing a widened CPU frustum from remaining paired with the stock lens. GameplayFOV remains the fallback outside Freecam and remains compatible with the cinematic override.

## Manual roll

The controller keeps `orientation_` as the unbanked camera orientation. Mouse yaw/pitch and the existing 0.30-second auto-horizon correction update this base orientation. A separately retained manual roll offset is composed around the final camera Back axis after horizon leveling. Therefore horizon correction cannot erase operator banking, and banking does not alter the native camera frame or camera position.

Roll Left adds positive rotation around camera Back; Roll Right subtracts it. `RollSpeedDegreesPerSecond` advances the target using the existing bounded wall-clock delta. Smoothing uses the exact exponential response to a linearly moving target, so equivalent elapsed intervals produce the same result at different sample rates. Releasing the key leaves the target angle in place. Holding RollReset sets the target to zero and smoothly returns to level. Reset takes priority over simultaneous left/right input. The offset is clamped symmetrically to `MaxRollDegrees`; the basis is re-orthogonalized only when a nonzero offset is applied.

AutoLevelHorizon disabled preserves inherited stock roll as the base while the manual offset remains independently adjustable. Input during the initial leveling interval acts on the manual layer and does not change the horizon controller's progress. Freecam deactivation drops its effective pose; the established scoped camera restoration remains the only camera-frame write boundary.

## Validation boundaries

Native tests cover key parsing and collisions, default and custom layouts, FOV inheritance/limits/edge steps/smoothing, projection math and CPU frustum agreement, roll signs/speed/smoothing/persistence/reset/bounds, interaction with auto-leveling and lens changes, yaw/pitch, near-vertical poses, focus loss, toggles, and rigid right-handed basis validity. They do not establish pause-time visual behavior, absence of visual snaps, or correct in-game projection order. See [runtime handoff](runtime-handoff.md).
