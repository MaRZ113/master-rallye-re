# Course source resources

Status: **partial, read-only** (R5T-B). Vehicle source-format conclusions are
not carried over unless a course source/compiled pair confirms them.

## Current source coverage

Demo 8.4.1 is the only supplied build with paired course `.gxm` and `.txt`
inputs for France1 and Italy1. The TXT inventory preserves the literal node
names, line text, brace-backed parentage, and `moMesh` `Index`/`Size` spans.
It does not decode source coordinates or assign behavior to names such as
`_raceline`, `_limits`, `$boinds`, `$bsp`, or `$ps2cells`.

The GXM prefix reader bounds the 32-byte header and an observed count-based
16-byte bank. A second, exact node-table reader requires the paired TXT: the
TXT node inventory determines the table's start from the file end, and the
reader then checks every node class, name, unknown-node child count, and mesh
span. No name search is used by that parser. This cross-check is confirmed for
the France1 and Italy1 8.4.1 pairs only. Transforms and the GXM geometry arrays
remain unknown.

| Source | GXM object-table offset | Table bytes | Nodes | `moMesh` | `moUnknown` |
|---|---:|---:|---:|---:|---:|
| France1 8.4.1 | `0xAE676B` | 59,396 | 2,322 | 2,283 | 39 |
| Italy1 8.4.1 | `0x84C140` | 28,123 | 1,117 | 1,082 | 35 |

## Observed helper records

The source spans below are exact TXT/GXM fields. They are not decoded runtime
coordinates or gameplay semantics.

| Course | Literal node | `Index` | `Size` | Evidence |
|---|---|---:|---:|---|
| France1 | `startpoint` | 0 | 12 | `CONFIRMED_BY_SOURCE_COMPILED_PAIR` name/span; position unknown |
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

## Controlled source edits

No source GXM was edited in R5T-B. The parsed table provides exact node and
mesh-span boundaries, but source vertex/index arrays and transforms have not
been mapped. Therefore no safe `startpoint`, raceline, bounds, BSP, or foliage
candidate was created. Continue from isolated developer GXM/TXT pairs once
they are available; France1 is not a substitute for those smaller oracles.

The current parser can inventory and compare source hierarchy metadata with
`mrtool diff-course`. It is not a GXM writer and does not modify game assets.
