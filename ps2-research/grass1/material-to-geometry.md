# Material to actual source geometry

The source is a landscape **spatial/collision triangle structure** with the
model's shared visual vertex positions. `357628` consumes its references;
there is no need to guess material ownership from printable render names.
`CONFIRMED_BY_BOTH` applies to the following targeted layout. All offsets here
are decoded PSM file offsets or explicitly named runtime object offsets.

| PSM field | Layout / original consumer |
|---|---|
| Header | `u32 d00d, u32 2, u32 539`; vertex count at `0x1c` |
| Vertex span | Starts `0x20`; `52` bytes per disk record; XYZ at record `+0x24/+0x28/+0x2c` |
| Runtime vertices | `3900f0` produces `48`-byte records; position `+0x20/+0x24/+0x28`; container model `+0x18` |
| Tag-103 header | Tag, reference count, source triangle count, nx, nz, then nine floats; **56 bytes** |
| Header floats | Grid spacing triplet, minimum XYZ, maximum XYZ; first spacing is 32 in selected cases |
| Cells | `nx*nz`, Z-major; each `u32 count` followed by `count` four-byte references |
| Reference | Low `u16` triangle index, high `u16` material-table index |
| Materials | `u32 count`; each `u32 byte_length`, `u16 byte_length`, ASCII bytes; no padding or terminator required |
| Triangles | `u32 count`, then three `u32` shared vertex indices per source triangle; model container `+0x1c` |
| Runtime proxy | Model `+0x2c`; per-material detail ID vector proxy `+0x98` |

`38fac0` tag dispatch, `394900` stream order/allocation, `2d5100` cell/string
reads and `357628` three vertex loads independently support this decode.
The diagnostic scans only beyond the verified vertex span and accepts exactly
one tag-103 candidate with checked header/cell budgets, equal serialized
material lengths, matching triangle counts, index bounds and unique material
binding for every source triangle. Ambiguous or malformed input fails closed.
This is a targeted source decoder, not a complete PSM scene-tree SDK.

| Landscape | Vertices | Spatial offset | Triangle-count offset | Triangles | Grid | Cell refs |
|---|---:|---:|---:|---:|---|---:|
| FRANCE1 | 67,387 | `0x38ba07` | `0x3bffc3` | 23,064 | 91×59 | 48,119 |
| ITALY_S1 | 69,577 | `3835291` | `3970722` | 15,042 | 78×63 | 28,839 |
| TURKEY_S1 | 84,986 | `4709233` | `4888621` | 18,768 | 115×70 | 36,673 |
| SPAIN1 | 63,744 | `3485071` | `3617873` | 17,202 | 47×57 | 30,437 |

A source triangle may occur in several cells. Those references consistently
agree on its material; they do not create several authored surfaces.
`2d3540` deduplicates by triangle index while preserving first encounter order.
The bounded corpus check found **36/36** valid unique bindings for **671,413**
source triangles; [corpus-checks.json](corpus-checks.json) records each source
hash, offsets, budgets and category counts, without coordinates.

France1's positive control is material **4**, `$surfacetype(harddirt)
$detail(grass)`: 4,257 bound source triangles, 3,366 passing the slope/category
test. Selected triangle **9174** resolves its three real vertex indices.
The negative control is material **8**, same harddirt surface label but
`$detail(none)`: 1,114 bound triangles, **900** passing slope alone and **zero**
eligible. Triangle **16967** is a flat negative surface in the same model.
The difference is a proved category branch, not an inferred steepness effect.

France1 stones material **6** has 567 bound triangles, of which 555 pass slope;
none is selected by this two-pool generator. Turkey_S1 material **11** has
343 bound singular-shrub triangles, 153 passing slope, zero category matches.
These are active source-table records, not unused string occurrences.

**UNKNOWN LINK:** individual source triangles to exact visual scene-tree
strip, draw group and LOD partition. Shared model positions establish the
terrain surface source used by the decorator; they do not certify every source
triangle as a currently visible draw. This distinction is retained in reports.
