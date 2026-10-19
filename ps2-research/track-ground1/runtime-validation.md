# TRACK-GROUND1: runtime A/B validation instructions

Status of everything below: NOT_PERFORMED. Nothing in this phase is RUNTIME_CONFIRMED; the checks are for the project owner, in the test install `D:\Game\Master Rallye Pristine`. The authoritative corpora (`Data.sma_unpacked`, the PS2 `TNG.PAK/TNG.000`) were only read: retail `turkey3.dx` keeps its 2001-11-15 timestamp and SHA-256 `724a69da708a124f...`, retail `Turkey3.xml` SHA-256 `9f00ef08e428f14f...` (the source hash recorded by the earlier XML probes), all outputs are written under `D:\Game\Master Rallye\research-output`.

## Candidates (built with `python ps2_course_objects.py --pc-root <retail unpacked> --out <dir> --terrain [--ground-detail noise2]`)
| Name | Folder in `research-output` | Content |
|---|---|---|
| A | none | Stock: remove every loose file listed below from the test install |
| B | `t4-terrain-g1` | default: native PC triangles kept where equivalent (2,104), 1,916 PS2 triangles added as 18 PC-textured models with mean noise tint, 1,402 PC triangles neutralised, house, caravans, collision slabs and brushes. 44 files, 18.7 MB |
| C | `t4-terrain-g1-noise2` | EXPERIMENTAL (HYPOTHESIS): as B, but the 18 added ground models carry a second UV set (PS2 +28/+32 pair), slot 2 `noise-tga` and `noise-tga.dxt`, no tint. Same `turkey3.dx` and XML as B (SHA-256 prefixes `6652692e39cb5315`, `0bb3d1c87b9a4219`). 62 files |

## Install and revert
1. Make sure `[Diagnostics] CrashLog=1` is set in `MRRRenderer.ini` (crash report `MRRRenderer\logs\crash-<pid>.txt`; send nothing, the file stays in the install and I read it).
2. Delete from the install: `DataGx\Misc\PS2Port`, `DataScene\RaceTest\Turkey3.xml`, `DataGx\Course\Turkey3\turkey3.dx` (leftovers of earlier candidates).
3. Copy the candidate folder content over the install keeping paths: `DataGx\Misc\PS2Port`, `DataScene\RaceTest\Turkey3.xml`, `DataGx\Course\Turkey3\turkey3.dx`.
4. Revert (Stock = A): delete those three again. If anything crashes or looks wrong, delete only `DataGx\Course` first (restores the PC ground and PC collision; the added models then lie on top of the PC ground).
5. Switching B to C: replace only `DataGx\Misc\PS2Port\terrain` (the collision file is identical).

## Teleport points (`[ProbeTeleport] Enabled=1`, Ctrl+Alt+1..9)
```
Point1=1985.4,34.9,-113.0,0         ; house, PS2 lighting, wall texture, fence-free ground around it
Point2=1955.9,35.3,-160.6,0         ; red caravan 4 at its original PS2 position (no snapping), ground texture and trench
Point3=2379.1,32.9,-854.0,0         ; caravan 1
Point4=2148.5,21.47,25.73,0         ; collision region rank 1, corner A (PS2 contact 19.965, patched 20.254)
Point5=2172.5,19.87,13.73,0         ; collision region rank 1, centre (PS2 18.367, patched 19.438)
Point6=2196.5,25.0,1.73,0           ; collision region rank 1, corner B (PS2 23.505, patched 23.787)
Point7=2316.5,17.99,475.73,0        ; collision region rank 2 (PS2 16.494, patched 20.254)
Point8=2628.5,67.33,499.73,0        ; collision region rank 3 mound (PS2 65.833, patched 71.205)
Point9=2682.5,28.02,-778.27,0       ; middle of the largest ground-delta cluster, texture comparison
```
Heading 0 is arbitrary; steer by hand. Stop the car before teleporting (velocity is not reset).

## Checks for B against A (Stock), with screenshots at the same point and camera
1. Textures: the added ground around Point1, Point2 and Point9 shows no blurrier patch than the PC ground beside it (the terrain models use the PC 128x128 files); no mirrored or upside-down ground texture; seams between added and native ground have no gaps (see sky or black) and no flicker (z-fighting).
2. Brightness: added ground and native ground have about the same brightness (tint 0.954); note any visible step at the seam.
3. Noise detail: native ground has the fine grain, added ground does not (expected, KNOWN gap); record whether the difference is noticeable.
4. Missing geometry: drive along the large cluster (2490..2870, -980..-585) and around the rock arch near (2610, 70, -844): no holes, no missing cliff faces from either side.
5. House and caravans: unchanged against the earlier verified build (house, caravans solid, correct textures, red caravans standing on the ground at their PS2 positions).
6. Collision at Point4 to Point8: drive over the region slowly and note, for each point, whether the car rides on an invisible bump (patched surface is higher than the PS2 one by 0.3 to 1.1 units at rank 1, 3.8 to 5.2 at rank 2, up to 6 or more at rank 3), whether it sinks, or whether it feels like the visible surface. Rank 3 and rank 2 lie next to the PS2 exterior shell, so expect no PS2 behaviour comparison there.
7. Stability: load, race, menu, race three times, no crash; a crash report in `MRRRenderer\logs` if one occurs; load time against Stock.
8. Stock: with A the game must behave exactly as before.

## Checks for C (only after B passes)
Does the course load; do the ground models look the same as in B or does the noise grain appear on them (a hypothesis result, either way is information); any black or white ground (the noise stage applied without a valid UV), crash or hang? Report which of these happened, nothing else is needed.

## What would count as PASS (decided by the owner, not by me)
B: items 1 to 5 and 7, 8 without regressions against the previous build. The collision items 6 are observations for TRACK-COLL1, not a pass or fail of this phase. C: informational only.
