# R5T-D.0 findings — RaceTest XML race logic

> **Current-state note (R5T-D.1):** The static sibling-group candidate and
> prepared edit described below were superseded by a later controlled runtime
> edit. Moving the `SplitTime0-0..3` visuals did not move SplitTime0. The
> executable confirms that the trigger center is read from an unidentified
> runtime object at `[context+0x50]+0x4C..0x54`; the producer/source field is
> still **UNKNOWN**. See `research/r5t_d1/` for the current trace.

## Scope and source

This phase inspects RaceTest XML and the existing Blender add-on only. It does
not write course assets or infer trigger semantics from object names alone.

The primary source is Retail `DataScene/RaceTest/France1.xml`: 474,787 bytes,
SHA-256 `beaa2180912ffd54f313a149962e295f9894239014481d2c7ba2db84fb1e08e1`.
The file is external to the Git repository. Derived reports are
`france1-race-logic.json` and `france1-race-logic.md`.

## Runtime-confirmed behavior supplied by the project owner

- Four `MarkerLists/StartArea` positions control the physical grid's
  translation, orientation, spacing, and vehicle headings. One-marker-to-one-car
  mapping and interpolation math remain unknown.
- Expanding the four `FinishArea` markers caused race completion earlier.
  The list contributes to the completion region; whether it is the only
  completion subsystem is unknown.
- `gaRaceSplitTimeAI/Radius` changes the distance/extent at which that optional
  split event fires. Split events may be missed without preventing a finish.
- Moving only a SplitTime Egg's `en3d Matrix` Row3 moved its yellow visual sign;
  the gameplay trigger stayed at the old location. Row3 as trigger center is
  **REJECTED / NOT SUPPORTED**.
- `ExtraTime` has no assigned meaning.

## Static France1 XML inventory

The hierarchy-preserving parser found 1,080 Marker records in eight ordered
lists and 76 Eggs. The list inventory is:

| List | Count |
|---|---:|
| Cameras | 127 |
| RaceLine | 448 |
| StartArea | 4 |
| FinishArea | 4 |
| LeftInnerLimit | 147 |
| LeftOuterLimit | 85 |
| RightInnerLimit | 168 |
| RightOuterLimit | 97 |

StartArea centroid is `(-1664.4375, 53.8625, 172.7625)`; FinishArea centroid
is `(-1487.9075, 66.8425, 367.3675)`. Both source-order XZ polygons pass a
simple consistent-turn convexity check. The Blender add-on draws only the
source-order outline and four points, without a filled face.

## Split visual objects and candidate trigger structures

| ID | Visual Row3 | Radius | ExtraTime | Companion center to visual | Group corner distance |
|---:|---|---:|---:|---:|---:|
| 0 | `(-2470.51, 84.36, -110.63)` | 21 | 77.5 | 0.253 | 20.997–21.052 |
| 1 | `(-2797.56, -4.64, 563.60)` | 13 | 82.5 | 2.426 | 13.005–13.008 |
| 2 | `(-1644.96, 38.88, 1009.46)` | 12 | 70 | 1.033 | 12.011–12.056 |

Each split has sibling Eggs `SplitTimeN-0` through `SplitTimeN-3` in the
`SplitTimes` list. Their en3d Matrix Row3 positions form a compact repeated
four-point group. Its centroid and corner-distance pattern tracks the visual
Egg and Radius closely in all three cases. At the time of R5T-D.0, this made
the group a **HIGH_CONFIDENCE_INFERENCE candidate** for the runtime trigger's
spatial structure. A later controlled runtime edit moved the four visible
`SplitTime0-0..3` checkpoint objects without moving SplitTime0, so these four
transforms are **NOT_SUPPORTED** as SplitTime0's direct trigger center. The
analogous SplitTime1/2 groups were not independently moved in that test. The
result does not establish that the visual objects have no other role.

The nearest RaceLine markers to the three visual positions are indices 112,
224, and 336 at distances 6.181, 4.834, and 0.000. Their repeated 112-index
spacing is a separate **PLAUSIBLE** correlation. No edit or reference proves
that the RaceLine markers define the trigger.

See [`split-trigger-localization.md`](split-trigger-localization.md) for the
candidate comparison and the exact next probe.

## Retail corpus

The scan covered all 41 Retail `DataScene/RaceTest/*.xml` files. All 41 parse.
StartArea occurs in 41, FinishArea in 40, and `gaRaceSplitTimeAI` occurs in 38
files. The component-record distribution is 0 in 3 files, 3 in 35, and 4 in 3.
Split Egg distribution is 0 in 4 files, 3 in 35, and 4 in 2. `Multi.xml` has
four split AI records but no split visual Eggs, so component and Egg counts are
reported independently. The 117 observed Radius values range from 7 to 30;
113 ExtraTime values range from 42.5 to 120. Turkey3 and TurkeyS2Flip each
contain a fourth split Egg with a repeated ID; these are retained as corpus
outliers, not normalized away.

## Blender integration

The existing add-on now creates a hierarchy under
`Course Helpers/MR_RaceLogic`:

- Source marker lists retain separate collections and ordered marker IDs.
- StartArea and FinishArea get four point helpers plus a source-order outline.
- Split signs get procedural yellow helper icons at their serialized matrix
  transforms with source matrix, Split Time ID, Radius, and ExtraTime metadata.
- Sibling split Eggs are shown only as neutral points in an explicit UNKNOWN
  candidate collection. No gameplay trigger object or Radius sphere is drawn.

The France1 Blender 5.2.2 headless smoke imported 1,080 markers, both
four-point area lists, three split visual icons, and 12 sibling candidate
points. Italy1 passed the same hierarchy-aware smoke with 1,202 markers. A
direct import of the built add-on ZIP passed the France1 helper check without
installing to Blender's external user profile. These are automated
scene-structure checks, not manual viewport/runtime parity claims.

## Source comparison boundary

The paired Demo 8.4.1 France1/Italy1 GXM/TXT tables do not contain a literal
`$splittime0/1/2` node. France1 has literal finishline-related names; Italy1
has startline/finishline names and `_bsplitX`. The Demo 8.4.1
`RussiaTurkey1.gxm` contains `$splittime0/1/2` strings but has no paired TXT,
cooked DX, or same-identity RaceTest XML in the supplied corpus. No source to
RaceTest spatial link is claimed.

## Verification and boundaries

- Synthetic XML unit tests cover hierarchy, list ordering, marker grouping,
  matrix extraction, direct Egg/AI/component raw values, missing optionals,
  malformed rows, corpus record-vs-Egg counts, and multiple split eggs.
- Full synthetic suite: **144 tests passed**.
- Blender 5.2.2 source-code France1/Italy1 race-logic smoke: **PASS**.
- Blender 5.2.2 packaged-ZIP France1 smoke: **PASS**.
- Preferences-based add-on install smoke could not write to
  `AppData/Roaming/Blender Foundation/Blender/5.2/scripts/addons` under the
  current workspace permission boundary; archive import was tested directly
  instead.
- No course DX, XML, route, surface, BSP, or EXE writer was added. No EXE was
  patched. The R5T-C tag100 and `$bsp -> tag100` UNKNOWN findings are unchanged.
- The split-group runtime edit was prepared at the D.0 checkpoint but is
  superseded by the D.1 relocation result; do not run it as the next probe.
