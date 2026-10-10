# R-CAM1-A3f.1 — Freecam flight feel and input

## Scope and preserved boundary

A3f.1 refines translation, flight speed and the existing game-window input subclass. It does not change the race certificate, camera owner, scheduler bridge, FOV/frustum path, horizon leveling, or the 176-byte camera scope. The A3f horizon behavior remains as previously accepted. Mouse-look smoothing is deferred to retain direct aim response.

## Translation

The eight movement controls now form a normalized desired direction in the current camera basis, with ascent/descent still aligned to world Y. Fast and Slow remain multiplicative factors on the runtime base speed. The controller stores velocity in world coordinates, so changing camera heading while coasting does not rotate existing momentum.

For the default `MovementSmoothSeconds=0.12`, velocity approaches the target exponentially. Position uses the exact integral for a constant target over each bounded sample, avoiding frame-subdivision drift. Input elapsed time remains wall-clock based and capped at 50 ms, so pause-time flight remains available and long stalls cannot teleport the camera. A zero smoothing time restores immediate velocity changes. Velocity is zeroed on activation/deactivation, focus or certificate loss, race/owner identity changes, failed camera scopes, invalid orientation and shutdown. Near-zero residual velocity is snapped to rest. The selected default response is deliberately short; human feel remains to be checked.

## Speed controls

`MoveSpeed` is the configured starting speed. PageUp and PageDown change it by the configured `WheelSpeedFactor` (default 1.25), one adjustment per press edge. The same controls are available with every movement preset and can be rebound through `[FreeCameraKeys]`. Mouse wheel input uses the existing verified HWND subclass, accumulates at most twelve notches, consumes each batch once in the controller, handles partial deltas and is discarded on focus loss/deactivation. `WM_MOUSEWHEEL` is always forwarded to the original procedure; no input is swallowed.

Speed is clamped to `MinMoveSpeed` and `MaxMoveSpeed`, defaults 0.25 and 300. It persists across Freecam toggles and focus changes for the current certified race, then resets to configured `MoveSpeed` when race generation or owner lifetime changes. It is not saved. Invalid bounds, non-finite values, invalid factors and conflicting key assignments disable the Freecam configuration.

## Cursor policy

The prior path hid the cursor from `QualityPipeline::cursor_tick()` during Present while the game HWND continued native `WM_SETCURSOR` processing between Presents. That handler could restore the game cursor. During active focused Freecam, the existing HWND subclass now returns handled only for client-area `WM_SETCURSOR`; non-client and all other messages continue through `CallWindowProcW`. The Present-owned quality cursor path remains the only component saving/restoring the cursor handle. Focus-loss messages immediately disable the subclass capture flag and clear pending wheel input; the quality path restores normal cursor policy on its next tick. No `ShowCursor` calls or global/thread hooks were added.

The controller F10/state JSON now exposes configured/current speed, limits, smoothing time, velocity magnitude, adjustment source/count, wheel availability/status, cursor capture/policy and the deferred look-smoothing value. These are transition/F10 diagnostics, not per-frame logs.

## Evidence boundary

The movement/controller and Win32 message contracts are covered by synthetic tests. They cannot prove perceived flight feel or eliminate visual cursor flicker under the game's actual window procedure; those remain human runtime checks. The user-provided A3f runtime confirmation remains the baseline and is not evidence for this A3f.1 candidate.
