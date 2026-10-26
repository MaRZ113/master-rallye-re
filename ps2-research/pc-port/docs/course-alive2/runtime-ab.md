# COURSE-ALIVE2 game test

Kit: `dist/course-alive2/` (`overlay/package_course_alive2.py`). Nothing is deployed automatically.

## Install (test copy, e.g. `D:\Game\Master Rallye Pristine`)
1. Back up `d3d8.dll`, copy the kit `d3d8.dll` (PS2-enabled overlay; all previous features unchanged).
2. Copy `PS2Grass/PS2Birds.ps2bird` into the `GrassAssetDirectory` (default `PS2Grass`).
3. Copy the course packages `courses/France1`, `courses/SpainS2`, `courses/ItalyS4` (`DataGx`, `DataScene`) next to the exe.
4. Add `PS2Birds=1` and `Diagnostics=1` to `[PS2Port]` (`PS2Port.snippet.ini`).
5. Optional: `ProbeTeleport.snippet.ini` into `MRRRenderer.ini` (`FreeCamera.Enabled=1`, `[PhysicsObserver] Enabled=1`);
   Ctrl+Alt+1..n jumps to race-line points 150..600 units from a FlightList origin.

## What to look for
| Course | Expected (PS2 rules) |
|---|---|
| France1 | after ~11-20 s of racing, small brown birds (about 1.6 units wide) start from a FlightList origin in groups of up to 9, fly away from the camera and climb, flapping (3 frames, frame change every 5 ticks = 6 per second); they disappear when more than 800 units (XZ) from the camera |
| SpainS2 | same, distances 100..800; also the moving boats (SplineObjects) if enabled |
| ItalyS4 | same, 100..900 |
| Turkey3 / France2 / any other of the 26 | no birds (PS2 gate closed: no MillList in the course scene). Only with the DIAGNOSTIC `PS2BirdsIgnoreListGate=1` do birds appear there (not PS2). |

Check: sprite faces the camera and is not mirrored compared with the PS2; transparent edges; fog with distance; a bird
behind a hill or the water is hidden; pause freezes them; Restart starts with no birds; leaving the race removes them;
fps unchanged.

## Logs (`MRRRenderer\logs` session JSONL, `Diagnostics=1`)
- `ps2_birds_config`: `effective_mode 1`, 36 courses, status `birds_ready`;
- `ps2_birds_course`: `selected true`, `course_guard ps2_course_package`, `ps2_update_gate open` / `closed_no_local_milllist`;
- `ps2_birds_state` every 150 ticks (5 s): ticks, flying/pending/free counts, RNG state, every bird's key and position;
- `ps2_birds_draw` once with all HRESULTs 0; `ps2_birds_gate` once if a frame was refused;
- per-race ledger (ps2diag): effect `birds` with `drawn`, `no_bird_flying`, `ps2_list_gate_closed`.

## PS2 comparison wanted
A PCSX2 GS dump (`.gs.zst`) on France1 or SpainS2 **with birds on screen** (after 30+ s of racing, birds in view), and the
same spot on PC. It would settle the open visual items (orientation, size, blend) against the real GS output.
