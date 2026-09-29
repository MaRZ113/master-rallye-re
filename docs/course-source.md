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

## Remaining source grammar limits

The float3 pool is not yet associated per node. No raceline ordering, limits
or boinds geometry, BSP mesh mapping, foliage material grammar, or source
transform records are decoded. Small developer pairs are sparse: only
Boinds currently has GXM, TXT, and cooked DX together. France1 remains a large
validation pair, not a substitute for missing isolated oracles.

The current parser can inventory and compare source hierarchy metadata with
`mrtool diff-course`. It is not a GXM writer and does not modify game assets.
