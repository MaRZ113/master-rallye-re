# Owner test: invisible one-sided wall on Turkey2 (fix of 2026-10-19)

Package: `research-output\course-port-36\Turkey2` (rebuilt 2026-10-19; `package-report.json` lists the checks). Only the collision tree changed:
PS2 splitter planes now carry the no-contact code 0xFFFFFFFF. Geometry, render and XML are built by the same code as before. Cause and offline
evidence: `REPORT.md`, section "Invisible one-sided walls". Nothing here has been run in the game.

## Where
The spot that best fits the report: just after SplitTime0, where the road runs beside the fenced field. Two predicted wall lines (old build) run
along the road at x 588..614, z 340..402, between the road and the fence. The PS2 surface there is about y 63 to 65.

## Teleport points
For the development teleport (`../track-delta1/PROBE-TELEPORT.md`, `[ProbeTeleport]` section, format `x,y,z,heading`; heading in degrees,
atan2(dx, dz)):

```
; Turkey2, wall line 1 (old build): front side, drive west across the line -> was blocked
Point1=597.2,63.9,349.7,291
; same line from the back side, drive east across it -> passed before as well
Point2=587.8,64.5,353.3,111
; wall line 2 (old build), 11 units further on
Point3=608.2,64.7,363.7,291
Point4=598.8,65.2,367.3,111
```

## What to check
1. Points 1 and 3: drive slowly (first gear) in the given heading for about 10 units. Expected: no stop and no sideways push.
   In the old build the predicted wall line is about 5 units ahead of the start point (offline prediction, not observed).
2. Points 2 and 4: same; expected free, as before.
3. Drive the race normally and watch for any invisible stop on open ground, in both directions along the fence.
4. If a wall is still felt, please send the spot (screenshot with the HUD and, if possible, the teleport/physics log line with the position).

The same defect existed on every course: every course has PS2 splitter planes. All 36 packages were rebuilt with the fix; see
`../course-port/course-packages-36.json` for the checks.
