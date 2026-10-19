# W4 survey: race logic, PS2 vs PC RaceTest XML (36 courses)

Read-only comparison (`logic_delta.py`, `logic-delta-36.json`). Nothing is written to any XML yet.

## Marker lists
| List | PS2 | PC | Notes |
|---|---|---|---|
| StartArea, FinishArea | yes | yes | equal point for point on all 36 courses |
| RaceLine | yes | yes | PS2 has 1 or 2 points more; every PC point lies on a PS2 point (max distance 0.0) on all 36 |
| Left/RightInnerLimit, Left/RightOuterLimit | no | yes | the four lists the PC `gaLimitsAI` uses (inner polygon, outer polygon, 8 samples outside -> LimitState 2) |
| Left/RightOuterLimit2 | yes | no | the only PS2 limit pair |
| Cameras | yes | yes | equal on most courses; differs on some (Spain2 297 units, TurkeyS1 125, TurkeyM 93, SpainW 89) |
| BoomCameras, StaticCameras | yes | no | PS2 replay / TV cameras |
| FlightList | yes | no | bird flight paths (ambient, W5) |
| MillList, boat*, barge*, zeppelin | some | no | spline paths of moving objects (W5) |

Consequence for item 5 of the plan (two separate tasks):
1. **Data:** PS2 has one limit pair, PC needs inner and outer pairs. Writing PS2 Limit2 into the PC outer lists (the earlier Turkey3 probe) moves
   the PC OFF COURSE border to the PS2 line. It is checked by comparing the lists and XML bytes.
2. **Behaviour:** what PS2 does with Limit2 (how fast and how it resets, and whether at all inside its solid shell) is not known from the data. It
   needs the PS2 limit code (ELF) or a PCSX2 observation, and then a runtime comparison on PC. With the PS2 shell now in the collision, the car is
   physically stopped near the PS2 border anyway.

## Eggs (Turkey3 as the example; all courses in the JSON)
- PC only:
  - engine and HUD objects: `gaVehicleResetManager`, `gaHudLoader`, 19 `gaRacePaceNoteAI` (pace notes) on gps_arrow models;
  - a 4th split `Copy of SplitTime1`;
  - 16 checkpoint Eggs on the PC model `misc\checkpoints\checkpoint` (PS2: 12 on `misc\objects\checkpoints\checkpoint`).
- PS2 only:
  - 6 `gaAiRigidBody` tumbleweeds (W6);
  - `gaAnimals_BirdManager` (W5);
  - 4 sound sources without a model;
  - 42 model-less Eggs against 11 on PC (cameras, spline objects, emitters; to be classified).
- Splits: SplitTime0..2 are at the same positions on both. PS2 has 3 splits on every course, PC has a 4th on some (Turkey3, TurkeyS2Flip).

Working rule for W4: the PC XML stays the base, because the engine needs its PC-only objects (reset manager, HUD loader, pace notes). The PS2
differences are applied one by one, each as a recorded change:
- the extra PC split removed;
- PS2 checkpoint layout (12, PS2 positions);
- PS2-only Eggs only where their class works on PC (rigid bodies need W6 first);
- Limit2 as an option.
