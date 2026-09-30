# Course source resources

Status: **read-only; version-7 mesh topology decoded** (R5T-E.1 PASS).
Vehicle source-format conclusions are not carried over unless a course
source/compiled pair confirms them.

## Current source coverage

Demo 8.4.1 is the only supplied build with paired course `.gxm` and `.txt`
inputs for France1 and Italy1. The TXT inventory preserves the literal node
names, line text, brace-backed parentage, and `moMesh` `Index`/`Size` spans.
Paired version-7 GXM resolves those spans into source position references; it
does not assign behavior to names such as `_raceline`, `_limits`, `$boinds`,
`$bsp`, or `$ps2cells`.

The bounded GXM prefix reader remains available for unknown versions. The
version-7 model decoder uses the paired TXT to determine the exact node-table
start from file end, then checks every node class, name, unknown-node child
count, and mesh span. No name search is used by that parser. Version-7 topology
and node-table cross-checks pass France1, Italy1, Boinds, and Demo 9.10 AI
Track. R5T-B.1 compared the trailing float3 bank with same-build cooked DX
positions; R5T-E.1 now decodes each mesh's source position indices. Source
node transforms and gameplay meanings remain unknown.

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

At the R5T-B.1 checkpoint, France1's `startpoint` record was known as
`moMesh`, `Index 0`, `Size 12`, and the first eight float3 pool entries formed
the 10-unit point set. The span-to-position mapping and connectivity were
then `UNKNOWN`; R5T-E.1 below subsequently resolves them. The center's
proximity to RaceTest Marker 0 remains a correlation, not runtime semantics.

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
role remains possible. At this R5T-C checkpoint the candidate point-to-node
binding was still a `HIGH_CONFIDENCE_INFERENCE`; R5T-E.1 below later confirmed
the mesh-to-position mapping. Runtime meaning of that source name remains
unknown.

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

Version-7 `moMesh` triangle spans now resolve through explicit position indices
into the source float3 bank. No raceline ordering, limits or boinds gameplay
role, BSP mesh mapping, foliage material grammar, or source transform records
are decoded. Small developer pairs are sparse: Boinds has GXM, TXT, and cooked
DX together; late Demo 9.10 AI Track adds a paired version-7 parser sample.

The source readers inventory and compare hierarchy metadata with
`mrtool diff-course`; they remain read-only. There is no GXM writer and no game
asset is modified.

## R5T-E.1 version-7 source topology (PASS; read-only)

The earlier blind-scan result correctly stopped at **MORE WORK NEEDED**: its
Italy1/Boinds candidate windows were not interpretable as one position-index
stream. That status records the earlier evidence state and is superseded by
the loader-guided version-7 decoder; the historical report remains available.

The exact Demo 9.3.1 executable (SHA-256
`931CFC4E0C520C26581B0C1173D1BEB586FACD17176B885666F455090F646680`) was
checked with `ghidra-bridge`. `0x005BEA30` extracts class from header bits
0–7, version from bits 8–15, and child count from bits 16–31. For class 2 it
accepts model versions 2–7 and invokes `0x005BDF40`; the latter reads seven
32-bit model counts. For version 7 it calls `0x005BE940` on the triangle bank.
That reader consumes `12 + 4 + 12 + 12 + 12` bytes per item and advances by
`0x34` (52) bytes. This is **CONFIRMED_BY_EXECUTABLE** for the loader path.

The read-only parser now decodes only `moModel` version 7. Its verified bank
order is color-like float4, raw variable-length material block, normal float3,
texcoord-like float3, 52-byte triangle records, source-position float3, and
the TXT-validated node table. The 13 little-endian u32 fields are grouped as
color `[0:3]`, material `[3]`, texcoord `[4:7]`, position `[7:10]`, and normal
`[10:13]`. References validate against their independent pools; observed
`0xFFFFFFFF` sentinels are allowed only in color, material, and texcoord
domains. Word 1 remains unnamed/zero in the tested files. Word 2 and word 5
remain conservatively named color-like and texcoord-like pools.

Cross-file validation passes France1, Italy1, developer Boinds, and Demo
9.10.0 AI Track: all references are in range (with observed sentinels), every
mesh span is in bounds, and each file's spans cover the triangle bank without
gaps or overlaps. France1 startpoint resolves to the closed 12-triangle,
8-position 10-unit box described by
[`startpoint-proof.json`](../research/r5t_e/startpoint-proof.json). Italy1's
triangle bank begins exactly at `0x58EDCC`; Boinds begins at `0x107E96` (the
old `0x107E94` candidate was two bytes early); France1's `0x6E956C` diagnostic
window lies within its texcoord-like bank and is not a topology input.

`CourseProject.source_geometry` and `source_meshes` now expose the decoded
read-only source topology. Source names such as `COLLIDE_finishline` are kept
literal and retain `UNKNOWN` gameplay role. The narrow GXM startpoint
diagnostic now uses this decoder; the standard Retail course importer remains
unchanged. No writer was added. Detailed counts, hashes, bank offsets, index
statistics, and the derived startpoint proof are in
[`course-gxm-v7.json`](../research/r5t_e/course-gxm-v7.json) and
[`startpoint-proof.json`](../research/r5t_e/startpoint-proof.json).

## R5T-D.0 / D.1 RaceTest split-source and runtime closeout

The retail RaceTest hierarchy now provides a stronger course-side baseline for
race logic. The complete France1 XML has 1,080 ordered Marker records in eight
MarkerLists and 76 Eggs. France1 and Italy1's 8.4.1 GXM/TXT pairs were searched
through the canonical node table: France1 exposes literal `FINISHLINE` and
`COLLIDE_finishline*` names; Italy1 exposes `STARTLINE`, `FINISHLINE`,
`COLLIDE_finishline*`, and `_bsplitX`. Their gameplay roles remain `UNKNOWN`.
Direct semantic equivalence to RaceTest areas or split triggers is not proven;
their spatial correlation with the retail areas is measured in the R5T-F.0
report. No `$splittime0/1/2` node was found in either paired France1 or Italy1
source.

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

## R5T-F.0 France1 named-mesh spatial correlation

The decoded Demo 8.4.1 France1 version-7 GXM contains four literal
`COLLIDE_finishline*` `moMesh` nodes. Each resolves to 24 triangles and 14
unique position records beneath the literal hierarchy
`Model/$autovsphere_300/$bsp/$nodraw`. Every undirected edge in each mesh is
referenced by two triangles. These structural facts do not establish a
gameplay, visual, or physical role.

In RaceTest runtime/XML coordinates, the centroids of `COLLIDE_finishline01`
and `COLLIDE_finishline` form a pair 18.1523 units apart; their midpoint is
6.5835 X/Z units from StartArea edge 0 and the pair direction is 2.2580 degrees
from that edge. `COLLIDE_finishline02` and `COLLIDE_finishline03` form a pair
18.1510 units apart; their midpoint is 0.0489 X/Z units from FinishArea edge 3
and the pair direction is 0.8716 degrees from it. All four edge comparisons
are retained in the machine report. The 3-degree / 10-unit reporting threshold
is descriptive; it is not a semantic classifier.

The spatial relationships are **STRONG_SPATIAL_CORRELATION**. The literal
source names remain identity only. Direct equivalence to the RaceTest areas,
physical collision meaning, and any `moMesh -> tag100` relationship remain
**UNKNOWN / NOT PROVEN**. See
[`research/r5t_f0/findings.md`](../research/r5t_f0/findings.md) and the
[machine-readable correlation report](../research/r5t_f0/france1-named-geometry-correlation.json).

Position ownership is exclusive for all 14 positions in each mesh. One
hash-pinned research copy moves only `COLLIDE_finishline03` by source X +20.0;
its source topology, non-target positions, node table, and attribute banks are
unchanged. The mutation is prepared but has not yet been cooked or runtime
tested. It is not a general GXM writer. The one-probe boundary and exact
human-observation checklist are in
[`research/r5t_f0/runtime-probe-handoff.md`](../research/r5t_f0/runtime-probe-handoff.md).
