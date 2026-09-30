# Course source resources

Status: **partial, read-only** (R5T-B). Vehicle source-format conclusions are
not carried over unless a course source/compiled pair confirms them.

## Current source coverage

Demo 8.4.1 is the only supplied build with paired course `.gxm` and `.txt`
inputs for France1 and Italy1. The TXT inventory preserves the literal node
names, line text, brace-backed parentage, and `moMesh` `Index`/`Size` spans.
It does not decode per-node coordinate/index membership or assign behavior to
names such as `_raceline`, `_limits`, `$boinds`, `$bsp`, or `$ps2cells`.

The GXM prefix reader bounds the 32-byte header and an observed count-based
16-byte bank. A second, exact node-table reader requires the paired TXT: the
TXT node inventory determines the table's start from the file end, and the
reader then checks every node class, name, unknown-node child count, and mesh
span. No name search is used by that parser. This cross-check is confirmed for
the France1 and Italy1 8.4.1 pairs only. R5T-B.1 bounds a trailing float3 bank
and compares it to same-build cooked DX positions, but per-node point/index
membership and node transforms remain unknown.

| Source | GXM object-table offset | Table bytes | Nodes | `moMesh` | `moUnknown` |
|---|---:|---:|---:|---:|---:|
| France1 8.4.1 | `0xAE676B` | 59,396 | 2,322 | 2,283 | 39 |
| Italy1 8.4.1 | `0x84C140` | 28,123 | 1,117 | 1,082 | 35 |

## Observed helper records

The source spans below are exact TXT/GXM fields. They are not decoded runtime
coordinates or gameplay semantics.

| Course | Literal node | `Index` | `Size` | Evidence |
|---|---|---:|---:|---|
| France1 | `startpoint` | 0 | 12 | `CONFIRMED_BY_SOURCE_COMPILED_PAIR` name/span; first-eight-point association remains inferred |
| France1 | `_raceline` | 59,293 | 954 | `CONFIRMED_BY_SOURCE_COMPILED_PAIR` name/span; route meaning not independently proven |
| France1 | `$boinds` | 60,247 | 251 | exact source identifier/span; meaning unknown |
| France1 | `$ps2cells` | 60,498 | 91 | exact source identifier/span; meaning unknown |
| Italy1 | `_boinds` | 45,667 | 348 | exact source identifier/span; meaning unknown |
| Italy1 | `_limits` | 46,015 | 564 | exact source identifier/span; meaning unknown |
| Italy1 | `raceline` | 46,579 | 690 | exact source identifier/span; route meaning not independently proven |
| Italy1 | `$ps2cells` | 47,269 | 108 | exact source identifier/span; meaning unknown |

Course source material/directive text also contains `$grnd`, `$grndu`, `$grndv`,
`$landdb`, `$draw`, and `$nodraw`. These remain source labels until a controlled
cook isolates their compiled effects.

## R5T-B.1 float3 bank and startpoint candidate

Header word 7 matches the finite float3 count in measured Demo 8.4.1 France1,
Italy1, and developer Boinds pairs. The corresponding bank ends at the exact
TXT-validated object-table boundary. Across all 48 signed axis permutations,
`(x, z, -y)` is the strongest source-to-DX position match in all three pairs.
Composing that relation with the established DX-to-Blender `(x, -z, y)` gives
identity as a `HIGH_CONFIDENCE_INFERENCE` for this source corpus. This is a
global spatial relation, not a decoded node transform.

France1's `startpoint` record is `moMesh`, `Index 0`, `Size 12`. The first
eight float3 pool entries are the eight corners of a 10-unit axis-aligned
box. Their center maps within 1.559 units of Demo 9.10 France1 RaceTest Marker
0. That correlation supports, but does not prove, the startpoint association;
the span-to-point/index mapping and connectivity remain `UNKNOWN`.

R5T-B.1 changed exactly point 0's source X from `-987.0555419921875` to
`-986.0555419921875` (+1.0) in an ignored source copy; the original GXM is
unchanged. Three baseline and three modified cold-cache cooks had identical
source inputs within each cohort and differed across cohorts only in that
GXM. Their 10,118,248-byte tag100 regions were internally identical within
each cohort and had different hashes across cohorts, while render prefixes
varied naturally. This confirms that this source float edit deterministically
changes tag100 (`CONFIRMED_BY_SOURCE_COMPILED_PAIR`). The owner observed no
obvious starting-grid or other gameplay difference in the loaded modified
course (`CONFIRMED_BY_RUNTIME` for that observation). Because only one corner
moved, spawning or trigger semantics remain unknown. See
[`research/r5t_b1/startpoint.md`](../research/r5t_b1/startpoint.md) and
[`research/r5t_b1/multi-cook-method.md`](../research/r5t_b1/multi-cook-method.md).

## R5T-C whole-volume startpoint candidate

The first-eight France1 candidate points were copied to an isolated source
folder and translated together by +3.0 source X units. All eight target
float32 fields receive the same delta; the 10-unit box dimensions are preserved
with zero measured pairwise-distance change. `France1.gxm` is the only changed
source file. Two baseline and two modified Demo 9.10 cold-cache cooks confirm
that this edit changes the 10,118,248-byte tag100 suffix reproducibly (263
bytes, 142 ranges), while render prefixes vary naturally. The owner observed
no change to player or AI starting positions/order, countdown, or race start in
that same-runtime comparison. Since the boxes overlap, a containment/helper
role remains possible. The candidate point-to-node binding remains a
`HIGH_CONFIDENCE_INFERENCE`; runtime meaning remains unknown.

The owner also reports cross-runtime France1 controls: player order is front in
8.4.1, second in 9.3.1, and the ordinary Retail order in Retail. Both old-source
cook outputs placed into Retail show the ordinary Retail order. This revises
the earlier interpretation that the old participant order was preserved by
course source. Runtime/version-dependent participant-slot assignment is a
strong inference. Later R5T-D.0 Retail edits confirm that the four RaceTest
`StartArea` positions drive the physical grid frame, including translation,
orientation, spacing, and heading; per-car interpolation and participant
assignment remain unresolved. This supersedes the earlier proposal to probe
whether StartArea moves the grid. Exact source spans, hashes, runtime notes,
and the split-trigger probe are in
[`research/r5t_c/whole-x3-closeout.md`](../research/r5t_c/whole-x3-closeout.md).

The read-only tag100 differential reports 452 changed bytes across 253 ranges
for the earlier one-corner tracer. Eleven float4 windows have unit-length
first-three-component candidates, but none fits the eight startpoint-box
corners under either tested plane convention. These are not decoded tag100
records or proven physical planes. `$bsp` remains unmapped; the small complete
developer pair has `$boinds`/`$landdb`, not `$bsp`, and the other small `$bsp`
sources lack matching TXT/DX in the supplied corpus. See
[`research/r5t_c/findings.md`](../research/r5t_c/findings.md).

## Remaining source grammar limits

The float3 pool is not yet associated per node. No raceline ordering, limits
or boinds geometry, BSP mesh mapping, foliage material grammar, or source
transform records are decoded. Small developer pairs are sparse: only
Boinds currently has GXM, TXT, and cooked DX together. France1 remains a large
validation pair, not a substitute for missing isolated oracles.

The current parser can inventory and compare source hierarchy metadata with
`mrtool diff-course`. It is not a GXM writer and does not modify game assets.

## R5T-E GXM topology-bank investigation (partial)

The current Demo 8.4.1 corpus contains course GXM only for France1 and Italy1;
Demo 9.3.1, Demo 9.10.0, and Retail course folders contain none. Developer
Boinds provides the third paired GXM/TXT/DX sample. Header word 3 exactly
matches `Materials(Size N)` in all three pairs. All `moMesh` spans cover
`[0, header[6])` without gaps, and `header[4] == 3 * header[6]` in all three.
This raises the triangle/corner model to **HIGH_CONFIDENCE_INFERENCE**, but the
raw corner bank has not been identified as a common, validated structure.

Exploratory offsets in Italy1 and Boinds yield candidate 32-bit and 16-bit
sequences whose entry counts equal header word 4 and whose early values align
with mesh spans. Both contain values at or above the respective trailing
float3-pool count; their referential meaning is unproven. No validated
intermediate vertex-to-position mapping was found. A
France1 16-bit diagnostic window was rejected as a proven boundary; it does
not establish the startpoint's expected box connectivity. These windows are
research observations only and are not used by `course_gxm.py`.

France1 `startpoint` remains a TXT/GXM-confirmed `Index 0`, `Size 12` record;
the first eight pool points form the previously documented 10-unit box. The
36 corner entries, position binding, closed topology, and per-triangle
material relation remain **UNKNOWN**. No source parser or Blender changes were
made. See [`research/r5t_e/findings.md`](../research/r5t_e/findings.md),
[`research/r5t_e/gxm-topology.md`](../research/r5t_e/gxm-topology.md), and the
[machine-readable evidence](../research/r5t_e/topology-candidates.json).

## R5T-D.0 / D.1 RaceTest split-source and runtime closeout

The retail RaceTest hierarchy now provides a stronger course-side baseline for
race logic. The complete France1 XML has 1,080 ordered Marker records in eight
MarkerLists and 76 Eggs. France1 and Italy1's 8.4.1 GXM/TXT pairs were searched
through the canonical node table: France1 exposes literal `FINISHLINE` and
`COLLIDE_finishline*` names; Italy1 exposes `STARTLINE`, `FINISHLINE`,
`COLLIDE_finishline*`, and `_bsplitX`. These names do not spatially bind to the
retail XML areas or split triggers. No `$splittime0/1/2` node was found in
either paired France1 or Italy1 source.

The 8,325,199-byte Demo 8.4.1 `RussiaTurkey1.gxm` contains source strings for
`$splittime0` at `0x7F07AE`, `$splittime1` at `0x7F07C7`, and `$splittime2` at
`0x7F07E0`. The supplied corpus has no matching TXT, cooked DX, or
same-identity RaceTest XML for that file. It therefore remains a source-name
observation, not a source-to-XML/runtime correlation.

Retail France1's RaceTest XML contains one `gaRaceSplitTimeAI` Egg for each ID
0–2. Each has four sibling Eggs named `SplitTimeN-0` through `SplitTimeN-3`.
Their Row3 positions form repeated point groups, but moving the four
`SplitTime0-0..3` checkpoint objects did not move SplitTime0's gameplay center.
Those sibling transforms are **NOT_SUPPORTED** as the direct center for
SplitTime0; SplitTime1/2 equivalents were not independently tested.

For France1 SplitTime0, the main Egg `en3d Matrix` Row3 is now confirmed as
both the yellow-sign position and the gameplay trigger center. Baseline and
StartArea-relocated debugger captures showed runtime `P+0x4C/+0x50/+0x54`
matching the Egg Row3. A final source-isolated on-road edit moved only that
Row3 from `(-2470.51, 84.36, -110.63)` to `(-2415.42, 72.10, -124.94)`; the
split was awarded at the moved location before its ordinary location. Evidence
is **CONFIRMED_BY_RUNTIME_EDIT**, **CONFIRMED_BY_DEBUGGER**, and
**CONFIRMED_BY_EXECUTABLE**. SplitTime1/2 were not independently moved in
runtime tests.

The earlier StartArea test appeared negative because its relocated sphere
overlapped the starting grid. Debugger observation at the one-shot acceptance
path showed all four cars accepted during startup, one byte per car, so later
driving could not activate those split events again. This corrects, rather than
erases, the earlier observation.

The executable's `0x0048CFE0` initializer maps the existing split center to its
nearest RaceLine point and stores a split percentage. The dependency is
**split center → nearest RaceLine sample**, not RaceLine → center. Static
visual-sign neighbors 112/224/336 have not been reproduced from the runtime
centers; moving RaceLine[112] is **NOT_SUPPORTED** as the direct SplitTime0
center. Radius is a 3D spherical threshold (`distance < Radius`); ExtraTime's
semantics remain **UNKNOWN**. See `research/r5t_d1/` for debugger details and
the canonical evidence ledger.
