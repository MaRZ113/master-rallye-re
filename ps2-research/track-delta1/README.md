# TRACK-DELTA1 — Turkey3 delta census (plan stage T1, first course)

Registry: [turkey3-registry.json](turkey3-registry.json) (14 elements, valid against
[../track-port0/registry-schema.json](../track-port0/registry-schema.json)).
Generator: [turkey3_delta.py](turkey3_delta.py). It reads the local TURKEY3 geometry report
(`data/geom1/TURKEY3-cli.json`, regenerable with `tools/geometry_delta.py`, hash reproduced in GEOM1)
and the PS2/PC scene XML through `tools/course_delta.py:parse_scene`. Nothing original is written.

Regenerate:

    python -X utf8 ps2-research/track-delta1/turkey3_delta.py --pc-scene <PC>/DataScene/RaceTest/Turkey3.xml --pc-dx <PC>/DataGx/Course/Turkey3/turkey3.dx --sdk <course-worktree> --output ps2-research/track-delta1/turkey3-registry.json
    python -I ps2-research/track-port0/validate_registry.py ps2-research/track-delta1/turkey3-registry.json

## Geometry (PS2 source triangles: 40,832)

| Class | Triangles | Reading |
|---|---:|---|
| Exact PC match | 36,001 | SAME |
| Puddle (`$shader(puddle)`) | 745 (520 extra + 225 modified-texture) | MISSING_ON_PC, CONFIRMED; channel A already built (COURSE-OBJECTS1) |
| Foliage treeblend (TURshrub2) | 1,360 | UNCLASSIFIED; plant population UNKNOWN |
| Foliage tree (fence hut) | 84 | UNCLASSIFIED |
| Buildings (hut, house) | 524 | UNCLASSIFIED; DRESSING1 found PC subpart fits for the hut, so likely REUSE_EXISTING_PC_MESH at other placement |
| Vehicle props (caravan, boat, tyres) | 868 | UNCLASSIFIED; boat1 group fits PC draw 825 (DRESSING1) |
| Ground (`$shader(ground)`) | 1,242 (1,164 extra) | UNCLASSIFIED; may be alternative triangulation or real extra ground |
| Other | 8 | UNCLASSIFIED |
| PC-only (reverse direction) | 971 in 99 groups | Kept untouched; delta-port never removes PC content |

The six UNCLASSIFIED rows total 4,086 triangles; with the puddles they equal the 4,831 non-exact PS2 triangles.
They are bounded candidates, not proved absent on PC: exact world-coordinate mismatch does not prove the object is missing,
since a counterpart may sit at another placement (DRESSING1) or differ in triangulation.

## Scene logic (PS2 vs PC Turkey3 XML)

| Item | PS2 | PC | Note |
|---|---:|---:|---|
| Entities | 83 | 71 | |
| `gaRaceSplitTimeAI` Eggs | 3 | 4 | The first three positions are identical. PC has an extra split at (2454.25, 18.23, -490.17) |
| Checkpoint model refs | 12 (`misc\objects\checkpoints\checkpoint`) | 16 (`misc\checkpoints\checkpoint`) | 4 per split, so the 4th PC split is a whole extra checkpoint |
| `gaAiRigidBody` | 6 | 0 | Tumbleweed; blocked by RIGID-PORT1.3 |
| `gaAnimals_BirdManager` | 1 | 0 | MarkerList `FlightList` (12 points) |
| `aiSpawnParticle` | 11 | 0 | Binding UNKNOWN |
| `gaAttractModeAI` | 1 | 2 | |
| RaceLine points | 422 | 420 | Ordered XYZ hash differs, within-1-unit match known from `cdelta1/course-pairs.md` |
| Limit lists | `LeftOuterLimit2` 230, `RightOuterLimit2` 209 | Left/Right Inner and Outer, 110 to 159 | Different structure; semantic mapping UNKNOWN |
| Cameras | 70 plus Boom (4) and Static cameras | 69 | |
| StartArea / FinishArea | 4 / 4, identical | 4 / 4 | SAME |

## Consequences for the plan
- Only the puddle layer is a firm, already-built MISSING_ON_PC geometry item. Everything else geometric needs per-group
  rigid fitting against PC draws (reuse `tools/dressing_runtime.py`) before a channel is chosen.
- The split/checkpoint difference is a real data delta on this course; PC is the superset here, so importing PS2 logic
  would remove a split. This needs a decision before T5 (it may be a PC fix rather than a PS2 feature).
- Limit-list structure differs, so G1-style authoring cannot be applied without first mapping the semantics.

## Next
T1b: rigid-fit classification of the 1,360 + 524 + 868 + 84 candidate triangles (hut, boat, caravan, tyres, shrubs, fence)
against PC draws, and ground extra-triangle analysis. Then repeat on France1 and ItalyS1, and finally the remaining courses.
