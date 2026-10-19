# COURSE-ALIVE1: moving PS2 spline objects on PC

Opt-in `SplineObjects=1` (PS2Port.ini). Default 0 = Stock, nothing is loaded or drawn.

All 24 `gaEntitySpline` objects of the 36 PS2 RaceTest courses move again: 18 dinghies, 2 barges, 4 airships on 17
courses. They use the PS2 route, clock, orientation, banking, trigger, rest and loop rules, and the PS2 model converted
to the PC format by course-port W5. Inventory: [inventory.json](inventory.json) (coordinate-free). Verification:
[verification.json](verification.json).

## Parts

| Part | File | Depends on |
|---|---|---|
| PS2 controller (portable) | `renderer/ps2_spline_motion.hpp` | C++17 standard library only |
| Asset, per-race runtime, course guard, D3D resources | `renderer/spline_objects.hpp/.cpp` | `course_objects.hpp` (shared `ObjectVertex`, world proof, state transaction) |
| Native seam (draw, Car0, pause) | `renderer/spline_objects_native_integration.hpp` | the PS2 port extension seams (same as grass and course objects) |
| Asset builder | `tools/prepare_spline_objects.py` | PS2 corpus, `course-port/build_objects.py`, `tools/spline_runtime.py` |
| Verification | `tools/verify_spline_objects.py`, `tests/spline_objects_tests.cpp`, `tests/test_spline_objects.py` | built test binary, PS2 corpus, `research-output/course-port-36` |

`ps2_spline_motion.hpp` has no D3D, Windows or proxy type in it. The future PS2 PC-port proxy can take it as it is and
feed it its own time, observer and draw path. No existing subsystem is duplicated: the draw goes through the course
object world proof and `CourseObjectTransaction`; Car0 is read the way the HUD map reads the vehicle.

## Controller contract (AMBIENT1, not changed)

Everything below is the existing static reverse in `ps2-research/ambient1/`; the C++ follows
`tools/spline_runtime.py` operation by operation in float32.

- Knots: `Use Const Speed=True` gives chord/speed per span and a closing time chord/speed, also on open routes (so an
  open constant route holds its last marker for that time). `False` gives equal spans `(L/speed)/N`.
- Position: uniform Catmull-Rom on the markers, controls clamped (open) or modulo N (closed), original weight order and
  the odd weight cache.
- Orientation: forward = normalised displacement since the last tick; up = (0,1,0) or, with `Banking`, the bank angle
  averaged over `Number Of Samples`; right = (F.z, F.y, -F.x). The matrix is written as the PS2 writes it (not
  re-orthonormalised).
- Tick: Car0 XZ distance with strict squared hysteresis (`Trigger Dist On/Off`), freeze while inactive, then
  +1/30 after the pose is published; closed routes wrap to 0, open routes clamp, `Use Rest On NonLoop` counts
  `Rest Time*30` invocations before the restart. No Car0 payload = no tick at all.

## Decisions

1. **Cadence: 50 invocations per second.** The owner has no elapsed-time input; it adds 1/30 per invocation. New
   static evidence (this phase, Ghidra EER on SLES_509.06): the EE main loop `3ed9e0` calls entity dispatch
   `2a13e0 -> 2a2300 -> 21f088` exactly once per loop iteration, with no fixed-step accumulator (`3e80a8/3e8150` are a
   frame timer only), and the PS2 PAL game renders one frame per 50 Hz field (all GS dumps, `docs/diag-reflection2`).
   So `SplineClock` converts host time to 50 Hz invocations (0.25 s stall clamp). Consequence: a nominal route second
   lasts 0.6 s; the inventory gives each cycle in real seconds. Not runtime-captured on PS2 (see limits).
2. **Pause, restart, exit.** The dispatcher skips frozen entities when the world is frozen, and every spline Egg is
   `Freezable=True`, so the clock stops while the PC pause menu is up. A new race generation re-creates the controllers
   at t=0 (the PS2 owner is created when the Egg hatches); leaving the race stops drawing; a device reset only drops
   the textures, the motion state continues.
3. **Draw instead of an engine hook.** The PC executable has no `gaEntitySpline`, and writing an Egg matrix would need
   unproved PC entity offsets and a per-tick hook (`AMBIENT-PROPS.md`). The proxy therefore draws the object itself at
   the typed pre-UI boundary with the verified gameplay view/projection, the native depth buffer and the course fog.
   The game knows nothing of these objects: no collision (separate task) and no game culling.
4. **Material = PS2 object shader.** `$shader(object)`: texture x vertex colour (MODULATE, the PSM colour as the course
   render stores it), opaque (blend and alpha test off: the dinghy texture alpha is ignored, as on PS2), fog on,
   no back-face culling (the W5 models already carry both sides), depth tested and written.
5. **No static duplicates.** The PS2 course packages contain no spline Egg and no Egg with a W5 model; the
   `--static-splines` stand-in of `build_objects.py` must not be installed with this feature. The France and TurkeyW
   landscapes contain harbour scenery with the dinghy/plating textures (piers with moored boats, 300+ triangles); these
   are static on PS2 as well and are not copies of the moving objects (checked per route marker).
6. **Course guard.** The routes are authored on the PS2 terrain. The pilot draws only when the course DX next to the
   exe is a loose file that is not the retail PC one (a PS2 package); otherwise `stock_pc_course_*`.
   `SplineObjectsStockCourses=1` lifts this for diagnostics.
7. **First init.** The bank flag before the first pose is assumed 0 (AMBIENT1 open question); banking starts with the
   first tick, as in the reference.

## Configuration

```ini
SplineObjects=1
; optional:
SplineObjectsAsset=PS2Grass/PS2SplineObjects.ps2spl
SplineObjectsStockCourses=0
Diagnostics=1   ; ps2_spline_objects_config/_course/_gate/_draw and a pose record every 250 invocations
```

## Build and kit

- Overlay build at master `6dd86c0` (+ this change): ctest baseline 24/24, PS2 40/40 (new `ps2_spline_objects_contracts`),
  unittest 142 OK; PS2-enabled DLL `6a4f65aa...` (`dist/current`).
- The overlay refused every build at HEAD because `a6fe7fe` (probe teleport) and `c357e8b` (crash log) had changed
  `modernization/renderer` after the lock. Both are opt-in developer tools; the lock now adopts `c357e8b`
  (`probe_baseline_adoption` in `overlay/baseline-lock.json`). Patch 0001 has the same added/removed lines as before
  plus the spline seams; only its context moved. Patch 0002 (generator) emits the spline proof resets in the
  generated forwarders.
- In-game kit: `dist/course-alive1/` (`overlay/package_course_alive1.py`), test steps in [runtime-ab.md](runtime-ab.md).

## Verified automatically (verification.json)

- inventory: exactly the 24 Eggs of 17 courses, properties and routes bit-equal to the PS2 XML; all 24 AMBIENT1
  applicability rows matched by route hash and duration;
- resources: models and textures equal the W5 conversion, retail loader winding, two-sided copies;
- C++ vs AMBIENT1 reference: every object, 20,000 invocations (400 s) with absent/far/near Car0: 480,000 invocations,
  0 mismatches in position, forward, up, time, bank mean, ring and rest (bit-equal float32); pose summaries at 0/10/60/120/300 s;
- bounds, loops and re-initialisation per object;
- no static duplicates in the 17 PS2 course packages, package DX accepted by the guard, retail DX refused;
- C++ contracts (ctest `ps2_spline_objects_contracts`): basis, knots, clock, trigger equality, freeze/resume, rest,
  open hold, banking, asset layout rejections, runtime restart, world vertices.

## Game test (owner, 2026-10-20, kit DLL 6a4f65aa)

User-confirmed: the objects load, are drawn correctly and move; the speed matches the PS2 (so the 50 Hz cadence of
decision 1 holds in practice). Status: **CONFIRMED_BY_USER_GAME_TEST** for the kit courses.

## Still open after the game test

- courses outside the kit (14 more spline courses) were not driven; same code and data path;
- pause/restart/exit in the real menus, replays;
- performance (expected negligible: at most 2 objects, 3 draws, ~500 triangles per frame).

## Limits

- The PS2 cadence is a static conclusion (main loop + 50 Hz frames). If a PCSX2 capture shows otherwise, only
  `kTicksPerSecond` changes.
- Split-screen: drawn only in single-camera races (the split proof is not wired for this feature).
- Water: the object is drawn after the course, so translucent water does not cover a submerged hull (PS2 draw order
  between the Egg and the water is not reversed).
- No collision with the moving objects (separate task); the routes of all 24 objects have constant height.
- Birds, physics props and emitters are later phases.
