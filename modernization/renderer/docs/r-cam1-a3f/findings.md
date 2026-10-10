# R-CAM1-A3f — Freecam horizon stabilization

## Scope and baseline

A3f refines Freecam orientation only. It retains the A3e live France1 race
certificate, current displayed-pose handoff, scheduler bridge, camera scope,
native camera restoration, input subclass, pause-time wall clock, and
CPU-frustum coordination. It does not alter terrain streaming, game pause,
camera ownership, FOV, or the native camera ABI.

The persistent tilted horizon came from copying the currently visible native
pose on activation and then rotating yaw/pitch without ever removing the
inherited roll. The exact-pose copy was correct for preventing an activation
snap; it now remains intact for the complete activation sample.

## Orientation policy

When `FreeCamera.AutoLevelHorizon=1` (default), the controller finds a level
Right vector from `cross(WorldUp, Back)` and measures the shortest signed angle
from the current Right to that target around Back. It rotates only Right and Up
around Back; camera position and look direction therefore remain unchanged.
The correction uses cumulative smoothstep progress over
`FreeCamera.HorizonLevelSeconds` (default 0.30 s), with input delta clamped to
50 ms. Progress is accumulated from the existing `GetTickCount64` wall clock,
so pause-time flight is preserved and large stalls cannot create a large
single-frame jump. User yaw/pitch are applied first, then the remaining roll is
corrected against the resulting view direction.

The resulting basis is orthogonalized and checked as a finite, right-handed
rigid pose before the existing camera scope uses it. At less than 5% of the
world-up cross-product magnitude, the controller projects its last valid
horizontal Right into the plane perpendicular to Back; the current Right is a
final fallback. If neither is valid, it retains the prior pose and marks the
orientation invalid for diagnostics. No LookAt reconstruction or position
change is used.

With `AutoLevelHorizon=0`, native roll is retained and mouse orientation works
as before. A zero leveling duration means immediate correction on the first
post-activation sample; the activation sample itself always preserves the
visible pose. Accepted duration is finite and bounded to 0–5 seconds.

## Diagnostics and limits

The existing bounded `free_camera_state` transition record and F10 snapshot
include `horizon_mode`, `horizon_leveling_active`, `current_roll_degrees`,
`target_roll_degrees`, `horizon_level_progress`, and `orientation_valid`.
Transition records are emitted when leveling begins or completes, not every
frame. The camera scope still owns and restores the same 176 bytes only after
the full scheduler completion.

Automated tests verify orientation math and legacy scope contracts. They do
not establish mouse feel, pause behavior, visual horizon smoothness, or live
terrain streaming. Those remain part of the short in-game handoff.
