# France1 RaceTest XML race-logic inventory

> **Current-state update (R5T-D.1):** Static positions below are not recovered
> gameplay trigger centers. Retail executable analysis shows
> `gaRaceSplitTimeAI` reads its center from an unidentified runtime object via
> `[context+0x50]` and XYZ offsets `+0x4C/+0x50/+0x54`. Moving the four
> `SplitTime0-0..3` checkpoint visuals did not move SplitTime0, so those four
> transforms are **NOT_SUPPORTED** as SplitTime0's direct center. The analogous
> SplitTime1/2 groups were not independently tested. See `research/r5t_d1/`.

Source: `France1.xml` (474,787 bytes, SHA-256 `beaa2180912ffd54f313a149962e295f9894239014481d2c7ba2db84fb1e08e1`).

Parsed 1080 Marker records in 8 source-ordered MarkerLists and 76 Eggs. The XML tree and all marker positions/directions are preserved in the companion JSON.

## Area lists

| List | Markers | Centroid (source XYZ) | Local X bounds | Local Z bounds | Ordered XZ outline |
|---|---:|---|---|---|---|
| StartArea | 4 | (-1664.438, 53.862, 172.762) | -1678.490 … -1649.710 | 160.720 … 184.870 | convex source order: true |
| FinishArea | 4 | (-1487.908, 66.843, 367.368) | -1517.410 … -1468.480 | 331.650 … 402.400 | convex source order: true |

### Source-order area positions

**StartArea**
- Marker 0 (No 0): Pos `-1649.71 52.42 174.33`, Dir `1.00 0.00 0.00`
- Marker 1 (No 1): Pos `-1658.30 53.26 160.72`, Dir `1.00 0.00 0.00`
- Marker 2 (No 2): Pos `-1678.49 55.13 171.13`, Dir `1.00 0.00 0.00`
- Marker 3 (No 3): Pos `-1671.25 54.64 184.87`, Dir `1.00 0.00 0.00`

**FinishArea**
- Marker 0 (No 0): Pos `-1473.27 68.30 331.65`, Dir `1.00 0.00 0.00`
- Marker 1 (No 1): Pos `-1517.41 67.38 344.60`, Dir `1.00 0.00 0.00`
- Marker 2 (No 2): Pos `-1492.47 67.52 402.40`, Dir `1.00 0.00 0.00`
- Marker 3 (No 3): Pos `-1468.48 64.17 390.82`, Dir `1.00 0.00 0.00`

Runtime edits confirm StartArea moves/rotates/scales the physical start grid and its heading. FinishArea expansion made race completion occur earlier. These are runtime observations from the project owner; neither list is asserted to be the only related subsystem.

## Split visual objects and spatial candidates

| Split ID | Visual Egg Row3 | Radius | ExtraTime | nearest RaceLine marker (distance) | 4-point group centroid to visual | group corner distance range |
|---:|---|---:|---:|---|---:|---|
| 0 | (-2470.510, 84.360, -110.630) | 21.00000 | 77.50000 | 112 (6.181) | 0.252 | 20.997 … 21.052 |
| 1 | (-2797.560, -4.640, 563.600) | 13.00000 | 82.50000 | 224 (4.834) | 2.426 | 13.005 … 13.008 |
| 2 | (-1644.960, 38.880, 1009.460) | 12.00000 | 70.00000 | 336 (0.000) | 1.032 | 12.011 … 12.056 |

The visual Egg's `en3d Matrix` Row3 is **CONFIRMED_BY_RUNTIME_EDIT** as the yellow sign position. Moving it alone moved the sign but left the gameplay trigger at the old location; Row3 as trigger center is therefore **REJECTED / NOT SUPPORTED**. Radius changes the event's trigger extent (**CONFIRMED_BY_RUNTIME_EDIT**), but the trigger center remains **UNKNOWN**.

### Historical D.0 static candidate comparison — superseded

Before the D.1 runtime test, the repeated four-Egg sibling groups `SplitTimes/SplitTimeN-0 … SplitTimeN-3` appeared to be strong static candidates: their centroids were within 0.253, 2.426, and 1.033 units of their visual Eggs, and their corner distances tracked Radius values 21, 13, and 12. Moving `SplitTime0-0..3` without moving SplitTime0 makes those four transforms **NOT_SUPPORTED** as SplitTime0's direct trigger center. The analogous SplitTime1/2 transforms were not independently tested; all may still have other visual or spatial roles.

The nearest RaceLine markers to the visual signs are indices 112, 224, and 336 at 6.181, 4.834, and 0.000 units. This is still only a visual-position correlation. Executable analysis separately shows that the actual, currently unknown center is mapped to its nearest RaceLine point to initialize split percentage; the concrete runtime indices have not been reproduced.

The D.0 prepared translation of the sibling Egg transforms is superseded and is not the next test. The current next step is a read-only breakpoint capture at `MRallye.exe+0x8CC50` to record the runtime center and caller; see `research/r5t_d1/split-center-trace.md`.

## Retail RaceTest XML corpus

Scanned 41 XML files: 41 parsed; 0 failures.
StartArea: 41 files; FinishArea: 40 files; files with split AI: 38.
Split component-record count distribution: `{"0": 3, "3": 35, "4": 3}`.
Split Egg count distribution: `{"0": 4, "3": 35, "4": 2}`.
Radius range: [7.0, 30.0]; ExtraTime range: [42.5, 120.0]. These are corpus ranges only; no additional runtime semantics are inferred.

## Evidence boundary

- StartArea grid translation/orientation/scale and heading: **CONFIRMED_BY_RUNTIME_EDIT**.
- FinishArea contribution to completion region: **CONFIRMED_BY_RUNTIME_EDIT**; not proven exclusive.
- Split Radius affects trigger extent: **CONFIRMED_BY_RUNTIME_EDIT**.
- Split visual transform vs gameplay trigger: separate; visual position confirmed, trigger position **UNKNOWN**.
- Trigger center memory read at `[context+0x50]+0x4C..0x54`: **CONFIRMED_BY_EXECUTABLE**; owner and source producer **UNKNOWN**.
- Moving visible `SplitTime0-0..3` checkpoint objects does not move the event: **CONFIRMED_BY_RUNTIME_EDIT**.
- `ExtraTime` semantics: **UNKNOWN**.
- Runtime version participant-to-slot order: not analyzed in this phase.
