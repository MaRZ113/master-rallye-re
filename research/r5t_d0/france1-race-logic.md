# France1 RaceTest XML race-logic inventory

> **Current-state update (R5T-D.1 closeout):** For France1 SplitTime0, the
> main Egg `en3d Matrix` Row3 is both the yellow-sign position and gameplay
> center. Baseline and StartArea-relocated debugger captures matched Row3 to
> runtime `P+0x4C/+0x50/+0x54`; a separate on-road edit triggered at its moved
> position. The earlier StartArea negative was caused by per-car one-shot
> activation during startup. SplitTime1/2 were not independently moved in
> runtime tests. See `research/r5t_d1/`.

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

For SplitTime0, Row3 is **CONFIRMED_BY_RUNTIME_EDIT** and
**CONFIRMED_BY_DEBUGGER** as both the yellow-sign position and gameplay center.
Its baseline center `(-2470.51, 84.36, -110.63)` matched the debugger's runtime
XYZ exactly. The StartArea-relocated center also matched the moved Row3. The
final nearby on-road edit from `(-2470.51, 84.36, -110.63)` to
`(-2415.42, 72.10, -124.94)` caused the split to be awarded at the new position
before its normal location. SplitTime1/2 were not independently moved.

`gaRaceSplitTimeAI/Radius` is the threshold for a 3D spherical proximity test,
`distance < Radius` for finite values: **CONFIRMED_BY_RUNTIME_EDIT** and
**CONFIRMED_BY_EXECUTABLE**. Split Time ID is stored at `this+0x14` and selects
the split event/state identity. `ExtraTime` semantics remain **UNKNOWN**.

### Historical D.0 static candidate comparison — superseded

Before runtime validation, the repeated four-Egg sibling groups appeared to be
strong static candidates because their centroids and corner distances tracked
the visual Egg/Radius values. They were a correlation only. Moving the four
`SplitTime0-0..3` visuals did not relocate SplitTime0, so those four transforms
are **NOT_SUPPORTED** as its direct center. SplitTime1/2 sibling transforms
were not independently tested.

The nearest RaceLine markers to the visual signs are indices 112, 224, and 336
at 6.181, 4.834, and 0.000 units. This is only a visual-position correlation;
the runtime indices from the actual SplitTime1/2 centers have not been
reproduced. The executable initializer maps the already-existing center to its
nearest RaceLine point for a split percentage; the direction is not reversed.

The D.0 prepared sibling-Egg translation and pending breakpoint capture are
historical and superseded. Final status: for SplitTime0, Egg Row3 is both the
sign position and gameplay center; the trigger is a 3D sphere with the
component Radius. SplitTime1/2 share the parsed structure but their Egg
transforms were not independently relocated at runtime. See
`research/r5t_d1/split-center-trace.md` for the final center and moved-position
tests.

## Retail RaceTest XML corpus

Scanned 41 XML files: 41 parsed; 0 failures.
StartArea: 41 files; FinishArea: 40 files; files with split AI: 38.
Split component-record count distribution: `{"0": 3, "3": 35, "4": 3}`.
Split Egg count distribution: `{"0": 4, "3": 35, "4": 2}`.
Radius range: [7.0, 30.0]; ExtraTime range: [42.5, 120.0]. These are corpus ranges only; no additional runtime semantics are inferred.

## Evidence boundary

- StartArea grid translation/orientation/scale and heading: **CONFIRMED_BY_RUNTIME_EDIT**.
- FinishArea contribution to completion region: **CONFIRMED_BY_RUNTIME_EDIT**; not proven exclusive.
- SplitTime0 Egg Row3 is both sign and trigger center: **CONFIRMED_BY_DEBUGGER** and **CONFIRMED_BY_RUNTIME_EDIT**.
- Trigger read path `[context+0x50]+0x4C..0x54`: **CONFIRMED_BY_EXECUTABLE**; runtime type of `P` remains **UNKNOWN**.
- SplitTime0 Radius is a 3D spherical threshold: **CONFIRMED_BY_EXECUTABLE** and **CONFIRMED_BY_RUNTIME_EDIT**.
- SplitTime0 sibling checkpoint objects are visual; their direct-center role is **NOT_SUPPORTED**.
- Per-car one-shot activation and the StartArea false-negative explanation: **CONFIRMED_BY_DEBUGGER**.
- R5T-D.1 status: **PASS** for France1 SplitTime0.
- `ExtraTime` semantics: **UNKNOWN**.
- Runtime version participant-to-slot order: not analyzed in this phase.
