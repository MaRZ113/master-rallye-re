# T1-full (logic part): scene census over all 36 paired courses

Script `scene_census.py`, data `scene-census-36.json`. PS2 XML from PackFS against paired PC retail XML, parsed with the Course SDK reader.
Geometry and material comparison for the other 33 courses is not done here: `geometry_delta.py` is gated to three courses by hash.

## Findings

- **Splits.** All 36 PS2 courses have exactly three `gaRaceSplitTimeAI` Eggs. PC has three on 34 courses and four on two:
  Turkey3 (`Copy of SplitTime1`) and TurkeyS2Flip (`Copy of SplitTime0`). In both, the extra Egg is a PC-only copy with five Eggs named `Copy of` (the split and its four barrels).
- **Shared splits** (compared numerically, position tolerance 0.01): identical on 32 of 36 courses. Real differences:
  ItalyM1 ExtraTime split 0: 77.5 PS2 / 75.0 PC, split 1: 60.0 / 82.5; ItalyS1 split 2 radius 18 / 19; SpainM split 2 position shifted 0.14; SpainWFlip split 0 position shifted 0.22.
  Text differences such as `75.00000` versus `75.0000` are format only and were not counted.
- **Limit lists.** Every PS2 course uses `LeftOuterLimit2` and `RightOuterLimit2` where PC uses `LeftOuterLimit`, `RightOuterLimit`, `LeftInnerLimit`, `RightInnerLimit`. The mapping is unknown.
- **Controllers, PS2 only.** Birds: 36 managers (one per course). Spline objects: 24 on 17 courses. Particle emitters: 81. Rigid bodies on 9 courses (Italy2 11, ItalyS1 14, ItalyS4 10,
  ItalyW1 10, ItalyW2 13, Turkey1 7, Turkey3 6, TurkeyM 9, TurkeyS2Flip 3). PC has none of these anywhere (`gaEntitySpline`, `gaAiRigidBody`, `gaAnimals_BirdManager`, `aiSpawnParticle` all 0).
- **Checkpoint model.** PS2 uses `misc\objects\checkpoints\checkpoint`, PC `misc\checkpoints\checkpoint` (per-course counts in the JSON).

## Per course

| Course | Splits PS2 / PC | Shared splits identical | PC `Copy of` Eggs | Rigid | Birds | Emitters | Splines |
|---|---|---|---:|---:|---:|---:|---:|
| FRANCE1 | 3 / 3 | 3 / 3 | 1 | 0 | 1 | 0 | 2 |
| FRANCE2 | 3 / 3 | 3 / 3 | 0 | 0 | 1 | 6 | 0 |
| FRANCEM | 3 / 3 | 3 / 3 | 2 | 0 | 1 | 4 | 1 |
| FRANCES1 | 3 / 3 | 3 / 3 | 1 | 0 | 1 | 2 | 0 |
| FRANCES2 | 3 / 3 | 3 / 3 | 0 | 0 | 1 | 3 | 2 |
| FRANCEW | 3 / 3 | 3 / 3 | 1 | 0 | 1 | 1 | 2 |
| FRANCEWFLIP | 3 / 3 | 3 / 3 | 0 | 0 | 1 | 2 | 2 |
| ITALY1 | 3 / 3 | 3 / 3 | 0 | 0 | 1 | 6 | 0 |
| ITALY2 | 3 / 3 | 3 / 3 | 0 | 11 | 1 | 2 | 0 |
| ITALY3 | 3 / 3 | 3 / 3 | 2 | 0 | 1 | 2 | 1 |
| ITALYM1 | 3 / 3 | 1 / 3 | 0 | 0 | 1 | 6 | 0 |
| ITALYM1FLIP | 3 / 3 | 3 / 3 | 0 | 0 | 1 | 5 | 0 |
| ITALYM2 | 3 / 3 | 3 / 3 | 1 | 0 | 1 | 2 | 0 |
| ITALYS1 | 3 / 3 | 2 / 3 | 0 | 14 | 1 | 4 | 0 |
| ITALYS2 | 3 / 3 | 3 / 3 | 0 | 0 | 1 | 1 | 1 |
| ITALYS3 | 3 / 3 | 3 / 3 | 1 | 0 | 1 | 3 | 1 |
| ITALYS3FLIP | 3 / 3 | 3 / 3 | 1 | 0 | 1 | 1 | 1 |
| ITALYS4 | 3 / 3 | 3 / 3 | 1 | 10 | 1 | 3 | 1 |
| ITALYW1 | 3 / 3 | 3 / 3 | 0 | 10 | 1 | 0 | 1 |
| ITALYW2 | 3 / 3 | 3 / 3 | 1 | 13 | 1 | 1 | 1 |
| SPAIN1 | 3 / 3 | 3 / 3 | 1 | 0 | 1 | 0 | 0 |
| SPAIN2 | 3 / 3 | 3 / 3 | 0 | 0 | 1 | 0 | 1 |
| SPAINM | 3 / 3 | 2 / 3 | 1 | 0 | 1 | 0 | 0 |
| SPAINS1 | 3 / 3 | 3 / 3 | 0 | 0 | 1 | 0 | 0 |
| SPAINS1FLIP | 3 / 3 | 3 / 3 | 0 | 0 | 1 | 0 | 0 |
| SPAINS2 | 3 / 3 | 3 / 3 | 1 | 0 | 1 | 0 | 2 |
| SPAINW | 3 / 3 | 3 / 3 | 0 | 0 | 1 | 0 | 2 |
| SPAINWFLIP | 3 / 3 | 2 / 3 | 0 | 0 | 1 | 0 | 2 |
| TURKEY1 | 3 / 3 | 3 / 3 | 2 | 7 | 1 | 2 | 0 |
| TURKEY2 | 3 / 3 | 3 / 3 | 0 | 0 | 1 | 1 | 0 |
| TURKEY3 | 3 / 4 | 3 / 3 | 5 | 6 | 1 | 11 | 0 |
| TURKEYM | 3 / 3 | 3 / 3 | 2 | 9 | 1 | 1 | 0 |
| TURKEYS1 | 3 / 3 | 3 / 3 | 0 | 0 | 1 | 1 | 0 |
| TURKEYS2 | 3 / 3 | 3 / 3 | 0 | 0 | 1 | 6 | 0 |
| TURKEYS2FLIP | 3 / 4 | 3 / 3 | 5 | 3 | 1 | 5 | 0 |
| TURKEYW | 3 / 3 | 3 / 3 | 0 | 0 | 1 | 0 | 1 |
