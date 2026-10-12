# Live Freecam

Status: `LIVE_FREECAM_READY_FOR_RUNTIME`. The user has accepted the previous
paused-camera baseline; this build adds opt-in flight while the offline race is
running. A live gameplay run of this change is still required.

## Admission and safety

`FreeCamera.AllowUnpaused` is parsed as a strict boolean and defaults to `0`.
Missing or invalid configuration therefore cannot silently enable live flight.
With it disabled, the legacy gate still requires a valid race certificate, a
verified camera owner, known native pause state, and confirmed pause. With it
enabled, the same race/camera certificate is required; known paused and known
running states are accepted. Unknown pause state, lost foreground focus, an
invalid camera owner, or a missing race certificate fail closed with distinct
diagnostic reasons.

The policy change only affects `FlightController` admission. It does not change
the existing native camera hook, scheduler bridge, x86 ABI, or camera write
surface. The established submission path captures the verified current camera
before applying the effective pose. `FrustumFrame` temporarily owns the same
176 CameraFrame bytes as the accepted A3d implementation: side planes,
previous pose, and current pose. The D3D projection/FOV path remains tied to
that scope. The scheduler boundary restores the snapshot only after checking
the camera pointer, owner lifetime, and race generation; identity changes
abandon the pointer rather than restoring through stale storage. See
[`r-cam1-a3d/implementation.md`](../r-cam1-a3d/implementation.md) and
[`r-cam1-a3d/final-report.md`](../r-cam1-a3d/final-report.md) for the previously
verified retail hook and field contract.

While active, the controller keeps its own camera pose. The native camera may
continue to update independently; a new stock pose is used when Freecam is
turned off, while the live Freecam pose is not copied from the moving vehicle.
Pause/resume does not cancel the controller when live mode is enabled, so its
pose, speed, cinematic FOV, and roll remain owned by the controller. Existing
focus loss, camera replacement, race-generation change, graphics Reset,
restoration failure, and renderer teardown cancellation rules remain active.

Road Teleport does not inherit the live-camera permission. Its existing arm
path still receives the native pause observation, and the physics observer
requires a fresh matching paused sample plus the existing road, owner, and race
gates. T while running cannot authorize relocation. Clean View keeps its
independent paused-Freecam admission; Global HUD Hide stays independent of
Freecam and pause, with its existing protected scene contexts.

## Configuration

The public example remains safely paused-only by default. The current local
development/test configuration was updated in place at
`D:\Game\Master Rallye Pristine\MRRRenderer.ini`: its existing
`[FreeCamera] Enabled=1` is preserved and `AllowUnpaused=1` is added. Other
settings were left intact. The production Win32 INI reader forwards this key
into `raw_fields`, and the Windows test writes a temporary INI through that
same reader before invoking `parse_free_camera_config()`.

## Diagnostics

The bounded Freecam snapshot now reports `allow_unpaused_configured`, admission
mode/acceptance/reason, native pause known/enabled, live-simulation camera
state, race certificate, camera owner, focus, scope-active/restored state, race
generation, and owner lifetime. `freecam_transition` records activation while
running or paused, running↔paused transitions, deactivation, and lifecycle
cancellation. These records establish the camera policy and scope; they do not
by themselves prove that physics advanced. That must be checked during the
human run.

## Optional lens configuration failure isolation

The 12 October runtime exposed that invalid optional lens settings were coupled to global Freecam validity. A malformed bound could disable camera input and paused Clean View. Optional lens errors now leave Freecam enabled and fail the lens back to native view. Valid nonzero initial FOV values are clamped to the configured range. The session emits `free_camera_config` with raw values and a precise `cinematic_fov_reason`; `free_camera_state` repeats the reason for F10 analysis. The active INI currently uses 30-degree initial/minimum and 110-degree maximum values; all settings are degrees, supported bounds are 30–110, and zero inherits the native lens.
