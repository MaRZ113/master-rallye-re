# W4: race logic of the PS2 courses on PC

Two separate tasks, as agreed: the XML data (W4a) and the OFF COURSE behaviour (W4b). The survey that came before this is `LOGIC-DELTA.md`.

## W4a: XML writer (`build_logic.py`)
The retail PC RaceTest XML stays the base: the engine needs its PC-only objects (reset manager, HUD loader, pace notes, boot cars). The
writer changes byte spans only; every byte outside them is checked to be the retail byte. Output: `research-output\course-logic-36` (36 XML
and `logic-36.json`), and since this step every W7 package carries `DataScene\RaceTest\<Course>.xml` (`build_course.py`, `--xml-only` to
refresh the XML alone). All 36 pass their checks.

| Change | Courses | Rule |
|---|---|---|
| Limits | 36 | `Left/RightOuterLimit` and `Left/RightInnerLimit` = PS2 `Left/RightOuterLimit2`, in PS2 order, Y = 0, polyline densified to 10 units |
| Split values | ItalyM1 (ExtraTime 75 -> 77.5 and 82.5 -> 60, TimeToFirstCheckpoint 75 -> 62.5), ItalyS1 (Radius 19 -> 18), 3 courses with position offsets of 0.01 to 0.22 | Radius, ExtraTime, Row3 from the PS2 Egg of the same name |
| PC-only split copies removed | Turkey3 (`Copy of SplitTime1`), TurkeyS2Flip (`Copy of SplitTime0`) | PC split Eggs without a PS2 Egg of that name |
| Replay cameras | 32 courses where the PS2 `Cameras` list differs (all but FranceS1, ItalyW1, ItalyW2, TurkeyS2Flip) | PS2 positions and directions, PC Marker Type |
| Sound sources | FranceM (`tunnel1`, `harbour`, `ocean`) | PS2 `enAiSoundSource` with no PC sound source within 100 units, sound file present on PC |

Not changed, with the reason:
- Sound parameters of sources present on both: on six courses (France2, SpainS2, ItalyS4, Italy3, ItalyM1Flip, Turkey3) every PS2 source has
  the same placeholder values (`Environment/birds`, 40/80, volume 1), the PC values are the tuned ones.
- Clouds, camera managers, track/shadow boot: identical on both.
- PS2-only lists `BoomCameras`, `StaticCameras`, `FlightList`, `MillList`: the names are not in `MRallye.exe`, so nothing on PC reads them
  (`BoomCameras` and `StaticCameras` are not in the PS2 ELF either). `FlightList`, `MillList` and the boat/barge/zeppelin paths belong to W5.
- PS2-only classes `gaAiRigidBody`, `gaAnimals_BirdManager`, `gaEntitySpline`: not in the PC executable, they need native code (W5, W6).

Why the limits are written this way (all from the decompiled code, see W4b):
- PS2 uses only `Left/RightOuterLimit2`. The string `LeftInnerLimit` exists in the ELF but the update never reads those lists.
- PS2 picks the nearest marker in X/Z. PC picks it in 3D. With one constant Y per list the 3D minimum is the X/Z minimum.
- PC treats a car inside the inner lists as inside without looking at the outer ones. With inner = outer the PC border is the PS2 border.
- PS2 tests the car against one segment, chosen by the corner bisector at the nearest marker. PC needs the car outside two consecutive
  segments. On the PS2 marker spacing this differs on 1.5 to 9% of the area around the road. With the same polyline densified to 10 units
  the two agree on 99.5% or more (table below).
- Densifying makes the lists longer than any retail list: up to 1,187 markers, retail maximum 470 (a RaceLine). The PC lists are vectors
  (count = (end - begin) / 0x48), no fixed array was seen. If the game has trouble with it, `--limit-step 20` halves the count at about 99.2%.

### Offline check of the border (`limit_sim.py`, `limit-sim-36.json`)
Both classifiers are transcribed from the code. On a grid (8 units) up to 320 units around the RaceLine it compares PC "state 2" with PS2
"outside". Car height = nearest RaceLine marker.

SIM_TABLE

`ps2_route_inside` is the share of PS2 RaceLine markers that PS2 itself classifies as inside: a few courses have a RaceLine marker outside
their own Limit2 (start or finish areas), PC with the new lists gives the same.

## W4b: OFF COURSE behaviour, PS2 against PC
Decompiled with Ghidra (PS2 project `EERevalidation2`, PC retail `MRallye.exe`).

| | PS2 (SLES_509.06) | PC (MRallye.exe) |
|---|---|---|
| Limits update | `FUN_001a6098` | `0x004CD9B0` |
| Lists read | `LeftOuterLimit2`, `RightOuterLimit2` | `Left/RightInnerLimit`, `Left/RightOuterLimit` |
| Nearest marker | X/Z, window +-12 around the cached index, full list every 15 ticks (`FUN_001a6758`) | 3D, window +-24, full list every 15 ticks (`0x004CE140`) |
| Segment choice | bisector at the nearest marker | step back when the next marker is closer to the current one than to the car (3D) |
| Side test | one segment | two consecutive segments, both outside |
| LimitState | 1 inside, 2 outside, immediately | 0 inside inner, 1 inside outer, 2 from the 8th consecutive sample outside (`cmp [counter], 7` at `0x004CDE6C`) |
| Reset manager | `gaVehicleResetManager` update `FUN_001a4c48` | `0x004CCAF0`, same structure |
| Player reset trigger | LimitState 2 -> reset timer 2 (`FUN_001a5950`) | LimitState 2 -> reset timer 5 (`0x004CD4A0`, `mov edi, 5` at `0x004CD4BA`) |
| Other timers (player) | reset request 105, physics flag 2, stuck 60 | reset request 105, physics flag 1, stuck 60 |

So the PS2 player is reset about 2 ticks after crossing its border; PC resets about 12 ticks after crossing (8 samples + 5). The tick rate
of either game is not measured here. The XML cannot change this. Reproducing the PS2 timing on PC needs two code bytes changed (not done,
not part of any package):
- `0x004CDE6F` (file offset `0xCDE6F`): `07` -> `00` (state 2 at the first sample outside);
- `0x004CD4BB` (file offset `0xCD4BB`): `05` -> `02` (reset timer 2).
This would belong to the PS2 PC-port proxy or a small separate patch, after the data part is confirmed in the game.

The earlier impression that PS2 resets "softer" comes from the border, not the timing: the PS2 border lies farther out (median 88 against
61 on Turkey3, `track-delta1/T2-BEHAVIOR.md`) and the PS2 solid shell stops the car near it. The timing on PS2 is quicker.

## What is not verified
Nothing here has run in the game. Open points for the game test:
- does the PC game accept limit lists of about 1,200 markers;
- does OFF COURSE come at the PS2 border (teleport points from `track-delta1/limits_port_spots.py` lie between the PC and PS2 borders);
- does a race on Turkey3 still count three splits after `Copy of SplitTime1` is removed;
- replay cameras from the PS2 list.
