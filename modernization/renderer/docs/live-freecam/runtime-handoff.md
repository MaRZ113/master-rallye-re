# Live Freecam runtime handoff

Use `D:\Game\Master Rallye\master-rallye-re-general\modernization\renderer\.build-msvc\Release\d3d8.dll`
(SHA-256
`bd1df3765e09cc9a034c89ef523772adec282c795043df47da954240a4732674`,
2,311,680 bytes) with the exact pristine retail `MRallye.exe` (SHA-256
`bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`). Back
up the currently installed DLL, then copy this candidate beside the game EXE.
The active local INI at `D:\Game\Master Rallye Pristine\MRRRenderer.ini` now
has `[FreeCamera] Enabled=1` and `AllowUnpaused=1`; no other user settings
were replaced. Do not modify the EXE.

1. Start an offline France1 race and leave simulation running. Press F8,
   translate/look around, then stop input. Confirm the Freecam stays in world
   space while the car and AI continue moving. Press F8 again and confirm the
   current stock chase camera returns.
2. Activate F8 while running, note the view, pause, move the camera, then
   resume. Freecam should remain active at its moved pose through both
   transitions. Confirm the race itself advances after resume.
3. While running Freecam, press H and verify Global HUD Hide; use a bookmark.
   Press T while unpaused and verify it is rejected. Pause, then check that the
   existing Road Teleport arm path still requires its normal gates. Clean View
   remains available only through its prior paused-Freecam policy.
4. If practical, repeat in Windowed mode, maximize/restore once, and verify
   Freecam remains safely deactivated across a graphics Reset and can be
   reactivated after the live race proof is revalidated. Check focus loss,
   cursor restoration, and normal exit.

With tracing enabled, attach one session JSONL and one F10 capture. Look for
`freecam_transition` values `freecam_activated_running`,
`freecam_running_to_paused`, and `freecam_paused_to_running`; verify
`freecam_admission_accepted=true`, `live_simulation_camera_active=true` while
running, unchanged race generation/owner lifetime, and successful camera scope
restoration. `road_teleport` must still reject an unpaused T request. Confirm
physical vehicle/AI motion directly; a zero pause field alone is not proof that
physics advanced.

## Freecam recovery candidate

Use the freshly built candidate at `D:\Game\Master Rallye\master-rallye-re-general\modernization\renderer\.build-msvc\Release\d3d8.dll` (SHA-256 `bd1df3765e09cc9a034c89ef523772adec282c795043df47da954240a4732674`), together with the exact pristine retail EXE. The active `D:\Game\Master Rallye Pristine\MRRRenderer.ini` has `Enabled=1`, `AllowUnpaused=1`, and uses `CinematicVerticalFOVDegrees=30`, `MinVerticalFOVDegrees=30`, and `MaxVerticalFOVDegrees=110`. FOV values are degrees; the supported interval is 30–110, a nonzero initial target outside the configured bounds is clamped, and zero inherits gameplay FOV. Z/X adjust by the configured step while Freecam is active. The prior INI is backed up beside it.

Check the `free_camera_config` record first: expect `parsed_enabled=true`, `runtime_enabled=true`, `allow_unpaused=true`, and `cinematic_fov_reason=configured`. In France1, press F8 while the game window is focused; expect `freecam_transition.event=freecam_activated_running` and then `free_camera_state.active=true`. Move/look, switch stock camera if desired, and press F8 to restore it.

For paused HUD suppression, pause the race, activate Freecam with F8, then press H. Expect the existing Clean View draw gate to suppress its verified pause UI and F10 to report `clean_view_suppressed_draws>0` with `policy_reason=paused_freecam_clean_view`. Pressing H in an interactive pause menu without Freecam keeps that menu visible by design. If Clean View still does not suppress after Freecam is active, capture F10 and inspect `clean_view.reason`, `context_snapshot_valid`, `native_ui_scope`, and `consumer_hook_owned`; do not weaken the UI identity gate from a visual guess.
