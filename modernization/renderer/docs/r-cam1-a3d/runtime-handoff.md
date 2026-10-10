# First flight — human validation pending

Use the candidate DLL identified in [validation](validation.md), with pristine
retail SHA256 `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`.
Do not replace the EXE. Keep an external backup of the current DLL/INI. The agent
has not deployed this candidate or launched the game.

[first-flight.ini](first-flight.ini) is an actual complete opt-in preset:
Windowed 1280x720, stock rendering features, physical Numpad, F8, tracing ON.
Alternatively merge its FreeCamera sections into your accepted Windowed/Borderless
INI and keep other accepted settings. Put the configuration at the existing
`MRRRenderer.ini` beside `d3d8.dll` (game root); `MRRRenderer/logs` is the log directory,
not the INI directory. Freecam defaults OFF in the public example.

1. Open Main Menu: F8 must not activate; confirm ordinary input and accepted UI.
2. Quick Race → France1, one human and initially one total car. Start driving,
   then release F8 and press once after a few rendered race frames.
3. Expected: flight starts at the visible pose without a flip/snap. Mouse looks;
   Numpad8/2/4/6 moves, Numpad9/3 moves vertically, LeftShift is fast, LeftAlt
   is precision. Toggle NumLock and verify the physical keypad still works.
   Native driving input is forwarded; WASD/Custom alternatives exist.
4. Look around near the car and dust: scene, CPU visibility and particles must
   remain coherent. Press F8 off; native current chase camera must resume.
5. Repeat with GameplayFOV Off and On; do not require FOV for flight.
6. Alt+Tab/minimize/restore: no held movement or mouse jump; flight deactivates.
   Reset requires a new observed race lifecycle, so Restart before reactivating
   if `reset_requires_new_lifecycle` is reported. Repeat same-course Restart,
   then return to menu: old certificate must not survive. Test multiple cars
   only after the one-car path passes (Type2, no more than eight).
7. Set Trace.Enabled=0 and restart game: Freecam must still activate with the
   same supported race; F10/session logging are independently optional.
8. With Freecam.Enabled=0, smoke-test supported display lifecycle, accepted UI,
   Broker opening/native Dump/F10, ordinary Restart and idle-menu Attract.
   Do not reopen Exclusive as part of this test.

Expected bounded trace records when tracing is enabled:

- `free_camera_state.state.certificate_valid=true`, reason
  `live_france1_offline_race_certificate`, then active=true after F8.
- `free_camera_scope.event=first_effective_scope`, owned_bytes=176.
- `free_camera_scope.event=first_verified_restore_after_scheduler`.
- F10 `race_epoch_snapshot`: phase A3d, status LIVE_RACE_CERTIFIED,
  storage_readable/native_live_unique/temporal_match true; source names and
  root/HUD parent lifetime now present. `free_camera` carries scopes/restores/failures.
  Present capture can occur inside an active scope, so its restore count may trail
  scopes by one. Observer `camera_writes_authorized=false` describes the read-only
  observation module; the nested Freecam certificate/scope reports control separately.

If F8 does not activate or any restoration/visibility fault appears, take **one F10
capture in the settled France1 race**, plus the matching session identity record.
It must show job source/flags/parent/terminal success, the three owner layers,
typed context, camera pointer, certificate reason and Freecam scope counters.
Do not start a broad new capture campaign. If F8 invokes a native command, rebind
ToggleKey before further flight and report the conflict.

PASS requires visible independent movement, coherent local geometry/particles,
current-stock return, focus/Restart exclusions, Trace=0 operation and no baseline
regression. A build/test pass alone does not close this phase.
