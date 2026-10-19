# Full PS2 course conversion: status (2026-10-19)

Goal: all 36 courses with the full PS2 content in PC quality, later integrated into the PS2 PC-port proxy. The plan has seven work packages (W1 to
W7). Everything below was done offline; nothing has been run in the game yet. Local commits only.

| Package | State | Where |
|---|---|---|
| W1 collision | done for 36 courses: whole PS2 BSP as PC tag100, PS2 surface grid (tag1400), checks against the PS2 BSP | `../track-coll2/REPORT.md` |
| W2 render | writer done (36/36 round trip); PS2 render builder runs on all 36 courses | `../track-render1/REPORT.md`, `NOTES.md` |
| W3 materials | draw-field rules derived from 1.2 million shared triangles; alpha copied from PS2; textures by the TRACK-GROUND1 policy | `../track-render1/NOTES.md`, `material-map-36.json` |
| W4 logic | XML writer done for 36 courses (limits, splits, replay cameras, 3 sounds); OFF COURSE behaviour of both games decompiled and modelled offline; timing differs by code only | `LOGIC-PORT.md`, `build_logic.py`, `limit_sim.py`, `limit-sim-36.json` |
| W5 ambient (birds, splines, emitters) | spline objects: 24/24 move on 17 courses (COURSE-ALIVE1, opt-in `SplineObjects=1`, drawn by the PS2 port proxy, bit-equal to the AMBIENT1 reference; user game test 2026-10-20: loads, draws, PS2 speed); birds and emitters not started | `AMBIENT-PROPS.md`, `../pc-port/docs/course-alive1/README.md` |
| W6 physics props | hay bale model ready; bodies need native code (PS2 class missing on PC, PC `gaAiHayBale` crashes in the contact code) | `AMBIENT-PROPS.md`, `track-delta1/HAY-PROBE.md` |
| W7 packages | `build_course.py --all` built all 36 packages; rebuilt 2026-10-19 after the Turkey2 invisible-wall fix (PS2 splitter planes keep the no-contact code, `track-coll2/REPORT.md`); 33 pass every offline check, SpainS1 and its flip miss one collision column of 18,035 and ItalyS4 one horizontal ray of 9,731 (float32 step, W1 report) | `course-packages-36.json`, `research-output\course-port-36` |

## What a package contains now
`DataGx/Course/<dir>/<name>.dx` with:
- the PS2 landscape render (exact PS2 triangle set, PC attributes where the PS2 triangle equals the PC one);
- the PS2 collision tree, including the PS2 exterior shell and void areas;
- the PS2 surface grid;
- the PC sector table.

Plus the PS2-only textures as `.dxt` files, and `DataScene/RaceTest/<Course>.xml` with the PS2 race logic (W4, `LOGIC-PORT.md`).

## First game test (owner)
Turkey3 v1 (`research-output\course-port-turkey3-v1`, README there), optionally against the EXPERIMENTAL noise variant
`course-port-turkey3-v1-noise-local`. What decides the next steps:
- does the course load and stay stable;
- are faces missing (corner-order rule);
- does the car rest on the PS2 ground;
- do puddles and wires look right.

## Known limits (details in the reports)
- tag1339 max y and radius rule, the sector polygon rule and three tag1500 constants are not decoded. They stay as in retail, which is consistent
  because the batch partition is kept.
- Plane codes are valid but their physical meaning is unknown. Surface types come from tag1400, whose engine use is not reversed.
- Noise layer: PS2-only ground takes the PS2 noise UV (vertex pair +28 plus 0.5, equal to PC modulo 1 on 36 courses), so no triangle loses
  the layer any more (`../track-render1/GAME-TEST-1.md`, fifth test).
- PS2 triangles outside every PC sector are drawn from the root (always drawn, as PC does). Mostly a few hundred per course, but ~3,500 on
  Spain2, SpainM, SpainS1 (+flip) and ~1,900 on SpainW (+flip), up to 298 units outside. The cost on frame time is unknown.
- Draw counts 465 to 1,532 and up to 79,879 vertices per course, inside the retail ranges (367 to 1,558 draws, 87,479 vertices).
- The PS2 OFF COURSE border is in the XML; the PS2 reset timing (about 2 ticks against about 12 on PC) needs two code bytes, not applied.
- Moving objects, birds and rigid props need native code (`AMBIENT-PROPS.md`).
- Turkey3 rock foot gap (open since the v4 test): found in the seventh test, from the owner's dumps and a software render. One ground triangle
  in a fold under the rock was flipped by the normal rule; PC's corner order is now used wherever PC has the triangle. The ItalyW2 torn
  fence was fixed in the same round: the PC material now has to match the PS2 alpha class. Not yet confirmed in the game
  (`../track-render1/GAME-TEST-1.md`).
- Owner game tests so far (`../track-render1/GAME-TEST-1.md`, seven rounds): courses load and race to the finish, the PS2 OFF COURSE border works,
  the Turkey2 grass seam and invisible wall are fixed. Only Turkey3, Turkey2, FranceM and ItalyW2 were driven; the other courses are checked
  offline only. The band in front of the Turkey3 mound (seventh test) is not in the course data (same as retail there); it comes from a proxy
  layer and needs an A/B on the proxy side.
