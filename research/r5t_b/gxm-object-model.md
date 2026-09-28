# Course GXM object model (partial)

## Exact paired-table parser

R5T-A treated the old course GXM body as opaque. R5T-B found a bounded trailing
node table by calculating its expected serialized length from the paired TXT
node list, then parsing directly from that boundary. The production reader does
not search for strings. It checks node order, class code, flags, name, declared
child count for `moUnknown`, and `Index`/`Size` for `moMesh`; the table must end
at EOF.

| Pair | File size | Table start | Table size | Node count | Mesh / unknown |
|---|---:|---:|---:|---:|---:|
| France1 8.4.1 | 11,489,135 | `0xAE676B` | 59,396 | 2,322 | 2,283 / 39 |
| Italy1 8.4.1 | 8,728,347 | `0x84C140` | 28,123 | 1,117 | 1,082 / 35 |

Both pairs validate every encoded node name and mesh span against TXT. The
`moUnknown` third record field matches the TXT's direct child count. The
`moMesh` third field can be nonzero (for example 2 on `stuBox01`); it is
preserved as `record_control_u16` and remains unnamed. These are
`CONFIRMED_BY_SOURCE_COMPILED_PAIR` findings for these exact two samples, not a
claim that every GXM build shares the schema.

## Object tree and helpers

TXT braces supply exact parent IDs, while GXM confirms node order/class and
mesh spans. The exact high-value records are listed in
[`docs/course-source.md`](../../docs/course-source.md). France1 contains
`startpoint`, `_raceline`, `$boinds`, `$ps2cells`, and nested `$bsp` /
`$draw $landdb` / `$nodraw` nodes. Italy1 contains `raceline`, `_boinds`,
`_limits`, `$ps2cells`, `_bsplitX`, and nested `$bsp` content.

The table provides geometry spans but not the referenced source position/index
arrays, transforms, material references, or coordinate system. No helper is
placed in Blender from an invented origin, and no source geometry was edited.
The small developer GXM/TXT oracles named in the R5T-B plan were not present in
the current local `inputs/` corpus.
