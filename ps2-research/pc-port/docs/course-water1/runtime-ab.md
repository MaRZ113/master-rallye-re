# COURSE-WATER1 game test (owner)

Kit: `dist/course-water1/` (`overlay/package_course_water1.py`). Test install: `D:\Game\Master Rallye Pristine`.

## Install

1. Copy `d3d8.dll` next to `MRallye.exe`; copy `PS2Grass/PS2Water.ps2wtr` and `PS2Grass/PS2SplineObjects.ps2spl` into the
   grass asset directory (`GrassAssetDirectory`, default the game directory: then put them in `PS2Grass/` and keep the
   existing `GrassAssetDirectory=PS2Grass` line).
2. Copy `courses/<Course>/DataGx` and `DataScene` of Turkey3, Turkey2 and France1 over the game directory (loose files).
3. `PS2Port.ini`: add the lines of `PS2Port.A-stock-water.ini` (A) or `PS2Port.B-ps2-water.ini` (B). Both enable the
   moving boats (SplineObjects=1) and Diagnostics=1, and turn the CourseObjects preview off.
4. Optional: `ProbeTeleport.snippet.ini` into `MRRRenderer.ini` (Ctrl+Alt+1..9 jump beside the largest puddle / water /
   waterfall surface of each kit course).

## A/B (same course, same camera, A then B)

| Course | Look at | Expected with B (PS2Water=1) |
|---|---|---|
| Turkey3 | the river ford and the puddles beside the road | puddles transparent towards their edges (the ground shows through), bright moving shimmer layer, no solid blue sheet; no second puddle copy |
| Turkey2 | the river, the extra PS2 puddles | river opaque with the semi-transparent WATERSURFACE2 layer (fixed pattern), puddles as in Turkey3 |
| France1 | river with the two dinghies, the two waterfalls | boats on the water, hull below the water line hidden; waterfalls scroll downwards in two layers at different speeds |

Also check on all three: water is fogged in the distance like the ground; the shimmer moves smoothly and stops in the
pause menu; no flicker, no z-fighting at puddle borders; grass, ground detail, car reflections, birds, HUD unchanged.

## Lifecycle

- race -> menu -> race (3 times) on one course; restart from the pause menu; change course.
- Alt+Tab out and back during a race (device reset): water still drawn, no black or white surfaces.
- Replay after the race.

## Performance

Same spot, A vs B, with `DrawTiming=1` (perf build) or the frame counter: expected cost per frame is a few hundred
microseconds at most (Turkey2 ~3,000 puddle vertices updated per frame, one extra draw per replaced draw).

## What to send

- `MRRRenderer/logs/` of a B run: `ps2_water_config` (effective_mode 1, status water_ready), one `ps2_water_course` record
  per course (triangles, parts, source 1 = package), any `ps2_water` reason records, `ps2_course_objects_gate`.
- Paired screenshots A/B of the spots above; PS2 screenshots of the same spots if you have them (PCSX2).
- A GS dump of France1 at a waterfall would confirm the waterfall passes (not in the existing dumps).
