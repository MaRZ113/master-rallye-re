# COURSE-ALIVE1 game test

Kit: `dist/course-alive1/` (`package_course_alive1.py`). Nothing is deployed automatically.

## Install (test copy of the game, e.g. `D:\Game\Master Rallye Pristine`)
1. Back up `d3d8.dll`, then copy the kit `d3d8.dll` (PS2-enabled overlay, includes the probe teleport and crash log).
2. Copy `PS2Grass/PS2SplineObjects.ps2spl` to the `GrassAssetDirectory` (default `PS2Grass`).
3. Copy `courses/FranceM`, `courses/SpainS2`, `courses/ItalyW2` contents (`DataGx`, `DataScene`) next to the exe
   (the same PS2 course packages as `research-output/course-port-36`). Do NOT install the `course-objects-1` static
   stand-in XML: it would add a second, standing copy.
4. Add `SplineObjects=1` and `Diagnostics=1` to `[PS2Port]` (`PS2Port.snippet.ini`).
5. Optional: `ProbeTeleport.snippet.ini` into `MRRRenderer.ini` (needs `FreeCamera.Enabled=1`,
   `[PhysicsObserver] Enabled=1`); Ctrl+Alt+1..n jumps to the race-line point nearest each route.

## What to check
| Course | Object | Expected |
|---|---|---|
| FranceM | airship (zeppelin) | white/grey airship, closed loop at height 158, ~155 s per lap, no banking; visible over the course from the start |
| SpainS2 | boat1 (red), boat5 (blue) | both wait at their first marker until the car is within 300 units (XZ), then move; banking in turns (1.0 / 0.6); they stop again when the car is more than 600 away |
| ItalyW2 | boat (red) | moves from the race start, closed 15-marker loop, ~249 s per lap, banking 0.3 |

For each: the object floats on the water (boats) at the PS2 height; no second standing copy; both sides drawn; fogged
with distance like the course; it stops while the pause menu is open; Restart puts it back at the start; leaving the
race removes it; the fps is unchanged.

## Logs (`MRRRenderer\logs`, session JSONL)
- `ps2_spline_objects_config`: `effective_mode 1`, 17 courses, 24 objects, status `spline_objects_ready`;
- `ps2_spline_objects_course`: `selected true`, `course_guard ps2_course_package` (a stock course gives
  `stock_pc_course_*` and nothing is drawn);
- `ps2_spline_objects_draw` once: draws, triangles, `fog`, `observer car0_vehicle_output`, all HRESULTs 0;
- `ps2_spline_objects_pose` every 150 invocations (5 s at 30 Hz): per object time, active, position, forward, up. These can be
  compared with `tools/spline_runtime.py` for the same invocation count;
- `ps2_spline_objects_gate` once if a frame was refused (reason).

Please send: the session log, a screenshot per course with the object, and whether the speed looks like the PS2.
