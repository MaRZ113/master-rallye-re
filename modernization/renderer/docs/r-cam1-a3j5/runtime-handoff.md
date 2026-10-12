# R-CAM1-A3j.5 — One-session runtime handoff

This candidate is experimental and default-off. Back up the currently accepted `d3d8.dll` before installing it. Use the pristine retail game whose EXE SHA-256 is `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`.

Set the following values in the existing renderer INI, restart the game completely, and start an offline France1 race with exactly one human car:

```ini
[FreeCamera]
Enabled=1
VehicleTeleportEnabled=1
VehicleTeleportRoadOnly=1
VehicleTeleportArmTimeoutSeconds=60
VehicleTeleportMaxRoadDistance=20.0

[FreeCameraKeys]
ArmRoadTeleport=T

[PhysicsObserver]
Enabled=1
RoadTargetPreviewEnabled=1
```

Drive briefly and perform one ordinary stock recovery if needed to populate the live RaceLine snapshot. Pause, enable Freecam, and move to a nearby, visually clear road section no more than 20 horizontal units from the camera. F10/status output should show a current native route snapshot and a valid road candidate before arming.

Press `T` once while paused. Expect `road_teleport_armed` with the selected ordinal, target, route fingerprint, current actor/controller/backing, and request sequence. Resume manually, then invoke ordinary stock recovery once. Do not use a cliff, foliage, an obstacle, or an off-road target.

## PASS evidence

One JSONL session should show this same request sequence and scene identity progressing through:

1. `road_teleport_destination_overridden`, where the original marker and selected marker are recorded and the native adjustment returns the selected marker;
2. `road_teleport_destination_committed`, where the stock-copied matrix X/Z matches the selected route point;
3. `road_teleport_native_consumed`, with exactly one active human consumer and chassis X/Z matching the committed translation;
4. `road_teleport_completed`, with a recognized native clear writer and a later zero-flag controller sample.

The car must visibly move to the selected road section, then steer, brake, and continue driving normally. Also invoke ordinary stock recovery once with no armed request and confirm the normal destination remains unchanged. Exit normally.

## FAIL / stop conditions

Stop and restore the accepted DLL if the game crashes, the vehicle behaves incorrectly, the car lands away from the selected road, normal driving does not resume, or the stock no-request recovery changes. A native helper return that differs from the selected ordinal must report a cancelled request and restore the original progress ordinal; it is not a teleport pass.

Do not interpret `road_target_validated`, `road_teleport_armed`, or a matrix commit as completion. If the route snapshot is absent, first complete an ordinary stock recovery so the exact stock getter is observed, then pause and arm again. If setup reports any context mismatch, wrong build, missing observer/preview setting, or failed quiescence, do not repeat the test on a modified executable.

Return one session JSONL and report whether the car reached the selected road, normal driving resumed, stock recovery without an armed target stayed normal, and the exact final road-teleport state/reason. The current observer does not prove full obstacle, foliage, chassis-footprint, or contact clearance.
