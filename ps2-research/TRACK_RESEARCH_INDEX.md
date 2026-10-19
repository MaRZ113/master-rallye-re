# Track (course) research index

Entry point for PS2 -> PC course-content porting. Index only: every claim lives in the linked
documents and keeps their evidence labels. Paths are relative to `ps2-research/`.

Course data: 36 PS2 courses are paired with 36 PC `DataScene/RaceTest/*.xml` (all STRONG; ordered
RaceLine XYZ match within 1 unit). Pairing is semantic, not file-identical. Canonical PS2 ELF is
`SLES_509.06`; extraction goes through `packfs/` (`tools/` has the `tngtool` extractor).

## 1. Start here

| Doc | What it gives |
|---|---|
| [cdelta1/final-report.md](cdelta1/final-report.md) | PS2-vs-PC course delta survey: the master map |
| [cdelta1/delta-matrix.md](cdelta1/delta-matrix.md), [novel-candidates.md](cdelta1/novel-candidates.md) | 16 ranked deltas, 5 real discoveries |
| [cdelta1/course-pairs.md](cdelta1/course-pairs.md) | The 36 PS2<->PC course pairs |
| [cdelta1/portability-backlog.md](cdelta1/portability-backlog.md) | Ranked port candidates |
| [revalidation1/](revalidation1/final-report.md), [revalidation2/](revalidation2/README.md) | Audit of earlier claims, corrections, open items; read before trusting older docs |

## 2. Topics

| Topic | PS2 finding | Research dir | Status |
|---|---|---|---|
| Spline fleet: 18 dinghies, 2 barges, 4 airships on 17 courses | `gaEntitySpline` Catmull-Rom owner, clock, loop/trigger, matrix publisher | [ambient1/](ambient1/final-report.md) (`spline-algorithm.md`, `xml-parameter-contract.md`, `portability-notes.md`) | Reversed offline; no live PS2 capture; not ported |
| Birds (36 managers, 542 flight + 55 milling origins) | `BirdManager` spawn/flight/RNG/sprite draw | [ambient2/](ambient2/final-report.md) (`HANDOFF.md`, `flight-motion.md`, `bird-*.json`) | Reversed; live counts UNKNOWN; not ported |
| Grass / shrubs (`$detail(...)`) | Material-bound placement, density, RNG, textures | [grass1/](grass1/final-report.md) | Placement reproducible; VU1 residency/flush open |
| Water / puddles | Material parser, draw, Turkey3 extra puddle (745 faces, 0 PC matches) | [water1/](water1/final-report.md), `turkey3-delta.md` | Turkey3 puddle ported as additive layer (below) |
| Tree / treeblend foliage | `tree` vs `treeblend` alpha/depth contract | [treeblend1/](treeblend1/final-report.md) | Static contract done; capture needed |
| Dressing (huts, boats, shrubs, pines, haybales) | Hierarchy, LOD, instance ownership | [dressing1/](dressing1/final-report.md) | No feature implementation-ready |
| Geometry delta PS2 vs PC | Exact triangle matching per course | [geom1/](geom1/final-report.md) (`geometry-delta-map.md`) | Turkey3 36001/40832, France1 41620/41817, ItalyS1 39682/40479 |
| Checkpoints, smoke emitters, haybales, tumbleweeds | Changed checkpoint asset, 81 emitters, rigid props | [cdelta1/checkpoint-survey.md](cdelta1/checkpoint-survey.md), [course-dressing-survey.md](cdelta1/course-dressing-survey.md), [water-puddle-survey.md](cdelta1/water-puddle-survey.md), [detail-vegetation-survey.md](cdelta1/detail-vegetation-survey.md) | Survey only; physics owner UNKNOWN |
| Course lighting / ground noise | Prelight identical; PS2 subtractive noise pass | [course-light1/findings.md](course-light1/findings.md) | Ported as opt-in `GroundDetail=1` |
| Reflection and environment | Vehicle-focused, shared render contract | [refl1/](refl1/final-report.md) | Context only |
| In-race map | Procedural `gaHudAiMap` from route/split data | [ui2/minimap.md](ui2/minimap.md), `minimap-format.json` | Covered by HUD port (hud-port docs) |

## 2b. Track port work (this effort)

| Doc | Content |
|---|---|
| [track-port0/policy.md](track-port0/policy.md) | Per-aspect channels, coverage rules, G-COLL and PCSX2 gates, trigger criteria |
| [track-delta1/README.md](track-delta1/README.md) | Turkey3 delta census, registry v2, collision and scene censuses |
| [track-delta1/T2-BSP-FORMAT.md](track-delta1/T2-BSP-FORMAT.md) | PS2 `.BSP` format reversed from the ELF |
| [track-delta1/T2-SOLID-SHELL.md](track-delta1/T2-SOLID-SHELL.md) | PS2 solid exterior across 36 courses and runtime probe plan |
| [track-delta1/T2-BEHAVIOR.md](track-delta1/T2-BEHAVIOR.md) | Static comparison of the PS2 wall and PC OFF COURSE, verdict: not ported for now |
| [track-delta1/PROBE-TELEPORT.md](track-delta1/PROBE-TELEPORT.md) | Development teleport used for the runtime probes |
| [track-ground1/final-report.md](track-ground1/final-report.md) | TRACK-GROUND1: texture and ground material parity, collision diagnostics, ranked regions for TRACK-COLL1 |
| [track-delta1/SCENE-CENSUS.md](track-delta1/SCENE-CENSUS.md) | Splits, limit lists, controllers across 36 courses |

## 3. Already in the PC port (`pc-port/`)

| Item | Docs | Status |
|---|---|---|
| Grass/shrub layer, all 36 courses | [docs/full-coverage/courses/coverage.md](pc-port/docs/full-coverage/courses/coverage.md) (+ `*-placement.json`, `coverage-registry.json`), [docs/grass-port1..3/](pc-port/docs/grass-port3/resource-and-placement-contract.md), `split-grass1/`, `menu-grass-fix1/` | Implemented (see config-v2.md for GrassMode/ShrubsMode defaults) |
| Ground detail pass | [docs/ground-detail1/README.md](pc-port/docs/ground-detail1/README.md), `ground-perf1/` | Implemented, opt-in |
| Turkey3 puddle additive layer | [docs/course-objects1/final-report.md](pc-port/docs/course-objects1/final-report.md) | IMPLEMENTED_PENDING_USER_RUNTIME |
| Config / architecture | [docs/architecture.md](pc-port/docs/architecture.md), [docs/config-v2.md](pc-port/docs/config-v2.md), `docs/visual-parity-expansion/` | Reference |

Code: `pc-port/renderer/course_objects*.{hpp,cpp}`, `grass_pilot.*`, `ground_detail*.hpp`;
tools `pc-port/tools/prepare_course_objects.py`, `prepare_grass_pilot.py`.

## 4. Tools and tests

`tools/`: `course_delta.py`, `geometry_delta.py`, `detail_runtime.py`, `dressing_runtime.py`,
`foliage_runtime.py`, `water_runtime.py`, `spline_runtime.py`, `bird_runtime.py` (+ `package_*_handoff.py`).
`tests/`: matching `test_*_runtime.py`, `test_course_delta.py`, `test_geometry_delta.py`.

## 5. Not yet ported (candidates)

Spline fleet and birds are the top two. Both are reversed offline but absent from PC XML. Next
research items named by the reports: runtime capture of spline owner (`ambient1/next.md`), VU1
residency for grass (`grass1/next.md`). Unreversed: rigid-body physics for haybales/tumbleweeds,
smoke-emitter binding, checkpoint knockability.

## 6. Outside this directory

- `../../master-rallye-re-course` (branch `research/r5t-course-archaeology`, `4244fa0`): Course SDK and
  Blender tooling, used as the read-only PC reference by all phases above.
- Branches `research/general-re`, `research/r-*`: historical evidence, not edited here.
- `ps2-research/data/` and `pc-port/.build-*` are local generated caches, not research sources.
