# R-CAM1-A3e runtime handoff

## Candidate and config

Build the exact-revised Win32 Release `d3d8.dll` from this repository. Keep the
existing first-flight configuration in
`modernization/renderer/docs/r-cam1-a3d/first-flight.ini`: FreeCamera enabled,
Numpad preset, F8 toggle, F10 trace enabled. The DLL remains exact-pristine
retail gated; do not alter the EXE.

## Test

1. Launch a normal offline one-player Quick Race on France1.
2. Wait until active gameplay is visible and stable.
3. Press F8 once. Move a short distance with the configured controls.
4. Press F8 again to restore the stock camera.

## Read the result

The renderer emits compact `free_camera_state` and `race_epoch_snapshot`
records on meaningful certificate/input transitions; F10 remains available
for the full per-frame snapshot. Check:

- `root_job_success`: scene `RaceTest/France1`, source
  `DataScene/RaceTest/France1.xml`, flags `1/1`, `commit_success=true`,
  `terminal=true`, `failed=false`.
- `hud_job_success`: scene `Hud/Hud0`, parent points to the root, flags `1/0`,
  `commit_success=true`, `terminal=true`, `failed=false`.
- `manager_scene_after_commit` may be the HUD scene for both jobs; it is recorded
  as SceneManager state, not used as the root job's identity.
- `owner.participant_states` may contain 0 or 2. The corresponding
  `participant_states_reason` should be `native_phase_0_or_2`.
- `live_certificate_valid=true` and reason
  `live_france1_offline_race_certificate` means the race passed the gate.
- `input_observation.toggle_pressed_while_focused=true` means the configured
  key was sampled down while focused; `controller_toggle_edge=true` means the
  flight controller received a rising edge.
- `free_camera.active=true`, followed by `scopes` increasing and `restores`
  increasing after F8 off, is the expected short-flight trace. The user's
  observation of camera movement is still required to call the flight PASS.

If certificate is false, report `live_certificate_reason`, root/HUD evidence,
participant states/reason, and owner status. If the certificate is true but no
movement occurs, use the input edge, `free_camera.reason`, scopes and restores
to name the next specific blocker. Do not broaden race identity or camera
write scope from a static/synthetic pass.

## Verdict boundary

Automated tests and the DLL PE/export checks establish only source contracts,
build correctness and proxy packaging. Human movement in active France1 is
required for `READY_FOR_HUMAN_FLIGHT` to become a successful flight result.
