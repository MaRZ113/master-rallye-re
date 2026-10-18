# Probe teleport (development tool, not validated in game)

Moves the human car to fixed Turkey3 points so the three wall probes in `T2-SOLID-SHELL.md` can be driven without searching for the spot.
Code: `physics_probe_dev_teleport_*` in `modernization/renderer/src/physics_probe.cpp`, hotkey poll in `src/game_fov.cpp`.
Candidate DLL: `modernization/renderer/.build-msvc/Release/d3d8.dll` (build and 24 CTest pass; no game run).

## How it works
It reuses the stock Reset publication: it writes a 4x4 matrix at `P+0x34` and the level flag at `P+0x33`, which the controller turns into
`SetPhysicsBodyPose_0043A020` (position, previous position, wheel reset). The pair is re-written for up to 30 frames until the chassis (`body+0xA0`)
is within 1.5 units of the target in X and Z, then it stops. Outcome lines `probe_teleport` (requested, completed, failed with reason) go to the session JSONL.

## Install
In `MRRRenderer.ini` set `FreeCamera.Enabled=1`, `[PhysicsObserver] Enabled=1`, then add:

```
[ProbeTeleport]
Enabled=1
; probe 1 (route idx 6, right of travel): road, control at 1/3, near the wall
Point1=3161.5,37.7,168.3,0
Point2=3182.7,36.7,176.4,0
Point3=3217.6,35.1,189.7,0
; probe 2 (route idx 84, left)
Point4=2592.5,35.3,309.6,0
Point5=2585.9,41.6,280.3,0
Point6=2574.5,52.6,229.5,0
; probe 3 (route idx 219, right)
Point7=2387.6,36.8,-686.3,0
Point8=2368.2,45.5,-681.4,0
Point9=2337.3,59.3,-673.5,0
```
Format `x,y,z,yawDegrees`; y is PC ground plus 1.5 (wall points interpolate road and wall ground). Hotkey: Ctrl+Alt+1..9 during a race. Needs a live race, and the car idle (no reset in progress).

## Known gaps
- Yaw: rotation about +Y only; sign and forward axis unverified, so use yaw 0 and steer. Headings toward the wall are about 69, -167, -76 degrees (atan2(dx, dz)).
- Velocity is not reset by the stock path (policy unknown); stop the car before teleporting.
- The reset manager may clear the flag before the controller reads it; hence the re-assert loop. If `failed: chassis_did_not_reach_target` appears, that is the cause to investigate.
- Not course-gated: the points mean something only on Turkey3.
