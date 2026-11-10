# Course Studio qualification (2026-11-10)

Status: **OFFLINE AND BLENDER QUALIFIED, GAMEPLAY NOT YET TESTED BY THE OWNER.**
No game process was started for this report; runtime items below are owner gates.

## Technical tests

| Suite | Result |
|---|---|
| `tests/synthetic/test_course_studio_core.py` (18 tests) | PASS |
| Retail cooker equivalence (game-cooked `invspaingx.dx` vs Studio from the same GXM) | PASS: 74/74 draw records and fields, 167x103 grid with all cells, 14 surface strings, land records within cooker rounding (< 5 mm), tag1339 equal; Studio drops 3 zero-area records the cooker keeps as NaN planes |
| Existing course suites (`test_course*.py`, 102 tests) | PASS except one CAP2 test needing `capstone` in the system Python (environment) |
| Renderer `rigid_props_tests` with the declared-digest change (MSVC, private 515-prop asset) | PASS |
| PS2RGD02 writer round trip of the accepted asset | byte-identical |

## Blender 5.2.2 headless qualification (`tests/blender/course_studio_e2e.py`)

| Scenario | Result | Evidence |
|---|---|---|
| B new course from scratch | PASS | valley template, terrain subdivided (topology change), road carved, checkpoint added (ordered by route), building + grounded proxy, collision probes 0 holes / 0 route walls, AI trace ends 20 m from the route end, build 2.4 MB DX, CAP2 Race ID 41 |
| B physical objects | PASS | 2 PS2 families + one new model from a Blender mesh + its instance -> optional asset (37 courses, 4 new props, new model); course game files byte-identical with and without physical objects |
| D save / close / reopen | PASS | same geometry (14 510 triangles), materials, texture links, checkpoints, route, build settings; reopened project folder builds an identical DX; stable registration |
| C external geometry | PASS | OBJ written by the test, imported with Blender's OBJ importer, route snapped, start/finish/checkpoints, probes clean, build |
| A Retail France1 | PASS | opened in 32 s (terrain 24 514, objects 17 903, water 3 205, native collision 20 002 closed cells); topology, hill, material surface, checkpoint, route edited, blocker added; built as new course (22.9 MB DX, Race ID 42 in the chained candidate); probes: 0 holes and 0 walls next to the route |
| Installed ZIP | PASS | Blender add-on installer, vendored core, new course and build |

France1 collision probes (6 m grid, 98 052 samples, 4 300 route samples):

| Tree | holes (route) | solid above surface | route walls | route steps |
|---|---|---|---|---|
| Retail tree | 206 (n/a) | 1 719 | 0 | - |
| Studio rebuild, native cells grafted | 211 (0) | 1 601 | 0 | 2 |
| Studio rebuild after deleting 2 000 native cells and moving one | 219 (0) | 1 499 | 0 | 2 |

The off-route holes are Retail cooker artefacts on hills (E2.4) present in both.

## Private game candidate

`.research-output/course-cap2/studio-candidate-02` (newest Renderer build of
446619c in the renderer hosts) and `studio-candidate-01` (accepted Renderer
host of COURSE-CAP2): 43 races; Race 41 `Studio E2E Valley` (new course with
physical objects), Race 42 `France - Studio edit` (edited France1), both in
Quick Race group 0. Launchers: `Launch-sdk.cmd` (no Renderer, no Extra
Options), `Launch-input.cmd`, `Launch-renderer.cmd`, `Launch-both.cmd`. Extra
Options rebuilt for this composite (`extra-set1/course-studio-01`). Fresh
private profile.

## Owner gates (not run)

1. Both courses appear in Quick Race, load the right geometry, the car does not
   fall through, collisions match the Blender collision.
2. Checkpoints trigger and add time; finish and Results work; records saved.
3. AI follows the route.
4. Original courses (incl. Race 39/40) unchanged; Renderer and Extra Options
   together without regressions.
5. Physical objects: without the Renderer the course runs without them (by
   construction identical files). With a Renderer built from `master` 48795d8
   (RigidProps declared digest) and the `optional/RigidProps.ini` lines they
   appear; the packaged Renderer hosts do not contain that build.

## Proven limits (evidence)

* One native AI route per course (one RaceLine list + one SFL field).
* Physical objects exist only through the Renderer RigidProps module; at most
  32 per course, 16 models and 16 textures in the asset (`rigid_props.hpp`).
* Only the first landscape egg collides (E1.6): Studio always writes one merged
  DX. Texture count about 256 per scene (E1).
* New championships for added races are outside COURSE-CAP2 (Quick Race only).
* Surface physics parameters are global (`DataGame/Surface.xml`); materials
  choose among its ten types.
