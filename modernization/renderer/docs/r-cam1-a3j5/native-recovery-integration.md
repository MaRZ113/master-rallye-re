# R-CAM1-A3j.5 — Native Recovery Integration

## Result

The default-off prototype redirects only the route ordinal passed to the stock recovery adjustment helper. The game still owns recovery selection entry, transform construction, apply-flag publication, matrix copy, physics consumption, chassis/wheel reset, and native clearing. This is a build-and-synthetic-test candidate for one human runtime session; the new destination has **not** yet been confirmed in game.

The implementation targets only pristine retail `MRallye.exe` SHA-256 `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4` (3,121,214 bytes, PE32/I386, ImageBase `0x00400000`). The proxy also checks the exact call context before installing this opt-in hook. A different executable, an unknown image base, a changed context, or a failed suspension/quiescence check leaves the hook uninstalled.

## Native destination seam

`ResetManager_Recovery_004CCC90` calls `ResetRecovery_AdjustForNearbyCars_004CD200` at VA `0x004CCD34` / RVA `0x000CCD34`. The call bytes are `E8 C7 04 00 00`; a 31-byte surrounding context begins at VA `0x004CCD2B` / RVA `0x000CCD2B`. The bridge forwards ECX (the reset manager) and all three stack arguments unchanged unless one armed request passes every gate. Arguments are participant index, marker ordinal, and live route object. The target uses `ret 0x0C`; the bridge mirrors that cleanup.

The returned EAX ordinal is consumed immediately by the stock caller to index the `0x48`-byte RaceLine records and read position at `+0x38`, then build the stock recovery matrix. Only the second stack argument is replaced. The native helper remains responsible for its neighboring-participant adjustment. The request is admitted only for the certified one-human, one-car France1 case, where that adjustment should leave the supplied ordinal unchanged.

If the helper returns a different ordinal, the request is cancelled and the bridge restores EAX to the original progress-derived ordinal before the caller builds the matrix. This is the fail-closed stock fallback. Such a path is never recorded as a redirected matrix commit. Race Progress/LastMarker, Broker fields, controller backing, and physics state are not written by the proxy.

The optional RaceLine getter observer records both the native getter result and the reset-manager identity preserved in ESI. That is the same manager subsequently passed to the recovery-adjustment helper, allowing the route snapshot and intercepted selection to be correlated to one owner. The getter bridge retains its `ret 4` cleanup and restores the native getter's registers and flags after observation.

The selected target comes from the current native RaceLine snapshot (France1: 448 records, stride `0x48`, XYZ at `+0x38`). The preview's nearest-marker choice is bounded to 20 horizontal world units by default. The stock recovery code derives height and orientation from its route logic; the implementation does not inject a matrix or reuse the single observed 1.004-unit vertical difference. Static research says the stock collision-service query returns false on this path, so road membership does not prove obstacle, foliage, chassis-footprint, or contact clearance. `physical_clearance_verified` therefore remains false.

## Request and transaction gates

Arming requires all of the following at the same current scene epoch: exact retail build, current France1 race certificate, live route snapshot, active Freecam, verified pause, one human car, matching human actor/controller/backing and controller generation, no current apply flag or pending controller call, idle reset timer, finite selected marker, non-ambiguous road candidate, and configured horizontal distance in `1..20`. Only one request can be armed; the default timeout is 60 seconds (allowed configuration range `1..300`). Device release, controller replacement, race/owner generation change, teardown, expiry, or hook ownership loss cancels it.

The native selection callback rechecks the route pointer and copied route fingerprint, manager, participant zero, current human identity, generation, native thread, and idle recovery state before changing the stack argument. A stack write failure cancels the request and leaves the original argument intact. The stock matrix-copy observer must then see the same manager, participant, human backing, thread, race generation, and a translation matching the selected marker in X/Z within 0.25 units. It only observes the native matrix.

The existing transaction observer continues to correlate the copy with the one active human controller consumer, the resulting chassis position, an observed stock clear writer, and a subsequent zero-flag controller sample. Only then does status advance to `road_teleport_completed`. A candidate, an armed request, an overridden ordinal, or a committed matrix alone is not a completed teleport.

## Runtime settings

All controls remain off in `MRRRenderer.ini.example`. For the one-session test, enable:

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

`T` is sampled by the existing focused Freecam input path; it is not consumed from the game's arbitrary keyboard stream. The user must still resume manually and invoke the game's ordinary recovery control. The proxy does not synthesize input, unpause, or initiate recovery from a D3D callback.

## Evidence boundary

The 31-byte call context, target, x86 stack cleanup, and surrounding native use are checked against the exact retail image by the retail regression test when that image is available. Existing A3j transaction captures establish the ordinary stock publication/copy/consumer/clear sequence, but do not establish safety at every RaceLine point. Runtime success requires the human handoff in `runtime-handoff.md`; no static or synthetic result is represented as a physical-clearance or gameplay pass.
