# France1 split-trigger localization — final status

## Canonical result

For France1 `SplitTime0`, the main Egg's `en3d Matrix` Row3 XYZ supplies both
the yellow sign position and the gameplay trigger center. The runtime
`gaRaceSplitTimeAI` sphere is centered on that position and uses its `Radius`.
This is **CONFIRMED_BY_DEBUGGER**, **CONFIRMED_BY_EXECUTABLE**, and
**CONFIRMED_BY_RUNTIME_EDIT**. The full evidence and addresses are in
[`R5T-D.1 findings`](../r5t_d1/findings.md) and
[`split center trace`](../r5t_d1/split-center-trace.md).

| Record | Proven role | Evidence / limit |
|---|---|---|
| Main `SplitTimeN` Egg Row3 | visual sign position; SplitTime0 gameplay sphere center | SplitTime0 confirmed by debugger and controlled runtime edit. SplitTime1/2 were not independently moved. |
| `gaRaceSplitTimeAI/Radius` | radius of 3D Euclidean proximity sphere | Executable path and Radius runtime edit confirm. |
| `Split Time ID` | split event identity/index | Executable field mapping; ID 0 isolated in debugger. |
| `ExtraTime` | field loaded at `this+0x1C` | Exact gameplay semantics **UNKNOWN**. |
| `SplitTimeN-0..3` sibling Eggs | movable visual checkpoint objects | Their direct role as SplitTime0 gameplay center is **NOT_SUPPORTED** by the runtime edit. SplitTime1/2 equivalents were not independently tested. |

## Evidence progression and superseded interpretation

The D.0 runtime probe moved only the main SplitTime0 Egg Row3 to StartArea.
The sign moved, and later driving near it appeared not to trigger the split.
That was initially interpreted as evidence that Row3 was visual-only. This
interpretation is **SUPERSEDED**. Debugger captures showed the runtime sphere
center matched the relocated Row3, while the one-shot acceptance path had
already accepted all four cars during startup because the sphere overlapped
StartArea. The later on-road edit moved Row3 from `(-2470.51, 84.36, -110.63)`
to `(-2415.42, 72.10, -124.94)` with Radius, ID, ExtraTime, RaceLine,
StartArea, FinishArea, and sibling visuals unchanged; SplitTime0 was awarded at
the new location before its ordinary location. This is causal runtime proof.

The earlier static hypothesis that the four sibling Egg transforms defined
the trigger is also superseded: moving those visible objects did not relocate
the gameplay event. The main Egg transform is the demonstrated center source
for SplitTime0. No independent runtime relocation result is claimed for
SplitTime1 or SplitTime2.

## RaceLine relation

The nearest RaceLine markers to the visual signs are indices 112, 224, and 336;
this proximity alone is not a trigger reference. The executable initializer
uses the already existing split center to find a nearby RaceLine point and
derive a percentage. The supported direction is **split center -> RaceLine
correlation**, not RaceLine point -> split center. `RaceLine[112]` as direct
SplitTime0 center is **NOT_SUPPORTED** by the controlled edit.

## Historical D.0 artifacts

The sibling-group translation design and its prepared XML are retained as
historical D.0 material only. They are not a pending probe and must not be
presented as the next runtime test. Do not infer trigger geometry from the
sibling group merely because its dimensions happened to track Radius.

## Other D.0 runtime findings retained

- `MarkerLists/StartArea` controls the physical grid frame: translation,
  orientation/heading, and spacing were runtime-confirmed; exact interpolation
  remains unknown.
- `MarkerLists/FinishArea` affects the race-completion region; exclusivity is
  not established.
- `tag100` physical meaning and `$bsp -> tag100` remain **UNKNOWN**.

R5T-D.1 status: **PASS**. No follow-up probe is pending in this closeout.
