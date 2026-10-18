# TRACK-DELTA1 — Turkey3 delta census (plan stage T1, first course)

Registry: [turkey3-registry.json](turkey3-registry.json) (14 elements, valid against
[../track-port0/registry-schema.json](../track-port0/registry-schema.json)).
Generator: [turkey3_delta.py](turkey3_delta.py). It reads the local TURKEY3 geometry report
(`data/geom1/TURKEY3-cli.json`, regenerable with `tools/geometry_delta.py`, hash reproduced in GEOM1)
and the PS2/PC scene XML through `tools/course_delta.py:parse_scene`. Nothing original is written.

Regenerate:

    python -X utf8 ps2-research/track-delta1/turkey3_delta.py --pc-scene <PC>/DataScene/RaceTest/Turkey3.xml --pc-dx <PC>/DataGx/Course/Turkey3/turkey3.dx --sdk <course-worktree> --output ps2-research/track-delta1/turkey3-registry.json
    python -I ps2-research/track-port0/validate_registry.py ps2-research/track-delta1/turkey3-registry.json

## Geometry (PS2 source triangles: 40,832; T1b refinement)

Exact PC match: 36,001. The other 4,831 are classified by [turkey3_t1b.py](turkey3_t1b.py) into
[turkey3-t1b.json](turkey3-t1b.json). Fits are congruent rigid fits at tolerance .001 (diagnostics, not authored poses).
A candidate PC target is a draw that uses the same texture basename or exactly matched another face with that texture.

| Element | Non-exact tris | Class | Evidence from T1b |
|---|---:|---|---|
| Puddles (`puddle`) | 745 | MISSING_ON_PC | 0 PC matches; channel A already built (COURSE-OBJECTS1). Vertical relation to PC surface is mixed, so it is a water layer, not a decal |
| Shrubs (TURshrub2, treeblend) | 1,360 | PLACEMENT_DIFFERS | 1,222 other faces of these groups match PC exactly, with PC textures `shrub-tga` / `shrub1-tga` instead of PS2 `shrubtrig2-tga`. The 1,360 extra faces are all congruent to PC shrub geometry (1,312 by components, 48 whole groups): extra instances of a mesh PC already has. Repetitive shapes make this fit weak evidence of *where* |
| Hut (rustic Hut) | 491 | UNCLASSIFIED | 309 faces congruent to PC hut draws (e.g. draw 627); 182 not fitted |
| House 1 | 33 | MISSING_ON_PC | texture `brickhouse-tga` has no PC draw and no exact peer |
| Caravans (CARAVAN, RED CARAVAN, ALPHA) | 488 | MISSING_ON_PC | textures `caravan-tga`, `newtex-tga` have no PC draw |
| Boats (boat1 to boat4) | 256 | PLACEMENT_DIFFERS | all five groups congruent to PC draws 823 to 826 |
| Tyres | 124 | DIFFERENT_MATERIAL | exact geometry; non-exact part differs in texture binding (26 faces also fit) |
| Fence hut | 84 | UNCLASSIFIED | PC has 8 draws with this texture family, no congruent fit |
| Ground | 1,242 | UNCLASSIFIED | see below |
| Other | 8 | UNCLASSIFIED | |
| PC-only (reverse direction) | 971 in 99 groups | SAME / NONE | kept untouched; delta-port never removes PC content |

Ground extras (1,242 triangles, about 120,000 area units) are not simple decals. Centroid against the PC surface directly below:
439 far below (more than 0.5), 300 far above (mean normal Y only 0.49, i.e. steep slopes), 256 slightly below,
118 overlay above (0 to 0.5), 73 with no PC surface under them (mean 153 units from the RaceLine), 56 coincident.
They are mostly 50 to 65 units from the RaceLine. Reading them as extra terrain pieces such as banks or hidden layers is
a hypothesis; a visual review of the geometry_delta SVG overlay is needed before classifying them.

## Scene logic (PS2 vs PC Turkey3 XML)

| Item | PS2 | PC | Note |
|---|---|---|---|
| `gaRaceSplitTimeAI` Eggs | 3 (IDs 0 to 2) | 4 | PC has an extra Egg named `Copy of SplitTime1` (Split Time ID 1, radius 10, ExtraTime 85) at (2454.25, 18.23, -490.17), with four checkpoint models `Copy of SplitTime1-0..3` |
| Shared splits 0, 1, 2 | | | identical IDs, radius, ExtraTime and trigger positions; checkpoint barrel positions differ by about 1 unit |
| Checkpoint models | 12 | 16 | the extra four are the `Copy of` barrels; model path differs (`misc\objects\checkpoints\checkpoint` vs `misc\checkpoints\checkpoint`) |
| `gaAiRigidBody` | 6 | 0 | tumbleweed; blocked by RIGID-PORT1.3 |
| `gaAnimals_BirdManager` | 1 | 0 | `FlightList`, 12 points |
| `aiSpawnParticle` | 11 | 0 | binding UNKNOWN |
| `gaAttractModeAI` | 1 | 2 | |
| RaceLine points | 422 | 420 | within 1 unit by `cdelta1/course-pairs.md` |
| Limit lists | `LeftOuterLimit2` 230, `RightOuterLimit2` 209 | Left and Right, Inner and Outer, 110 to 159 | different structure; mapping UNKNOWN |
| Cameras | 70, plus Boom 4 and Static | 69 | |
| StartArea / FinishArea | 4 / 4 identical | 4 / 4 | SAME |

The user confirmed PC Turkey3 has three splits in play. The fourth `gaRaceSplitTimeAI` Egg is a copy of split 1 under the name
`Copy of SplitTime1`. The XML alone cannot say whether the duplicate ID 1 fires or is ignored. `Copy of` Eggs occur in 18 retail
PC scenes, none in PS2 Turkey3 (grep over the scene text); their purpose is a separate question for T5.

## Consequences for the plan
- Firm MISSING_ON_PC geometry: puddles (built), House 1, three caravan variants, together 566 triangles. All use textures absent from PC.
- Shrubs and boats are existing PC meshes at other placements; they need a placement decision (PS2 adds instances), not new meshes.
  Their PS2 texture (`shrubtrig2`) differs from the PC texture on the exactly matching faces.
- Hut is partly explained (309 of 491). Fence and ground need visual review.
- Splits: PS2 and PC agree on the three real splits. The PC `Copy of SplitTime1` is PC-only; do not import it as PS2 logic.
- Limit-list structure differs, so G1-style authoring cannot be applied before mapping their semantics.

## Next
T1c: run the same pipeline on France1 and ItalyS1, then the remaining courses. Add a visual review step for ground extras
(`tools/geometry_delta_visualize.py`). Investigate what `Copy of` Eggs do on PC (T5).
