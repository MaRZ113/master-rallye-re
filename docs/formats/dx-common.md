# Shared DX prefix

The vehicle and course readers now share one bounded parser for the DX header, vertex arrays, UV arrays, and local-index array. `parse_dx_common_prefix` stops exactly at the resource/build-specific draw grammar; it does not scan for likely record tags.

| Offset/order | Wire data | Current statement |
|---|---|---|
| `0x00` | `uint32` magic `0x0000D00D` | Confirmed across the inspected DX corpus |
| `0x04` | `uint32` revision/build word | France1/Italy1 values: 127, 131, 135, 135 for Demo 8.4.1, 9.3.1, 9.10.0, retail |
| `0x08` | `uint32` observed as 1337 | Value is corpus-confirmed; meaning is unknown |
| `0x0C` | `uint32` vertex count | Followed by that many float32 XYZ positions |
| next | `vertex_count × 3` float32 normals | Same count as positions in the parsed corpus |
| next | `vertex_count × 4` raw color-like bytes | Retained as bytes; interpretation reuses existing importer behavior |
| next | `uint32` UV set count, then per-set `vertex_count × 2` float32 | Parsed as separate full-size sets |
| next | `uint32` local index count, then `uint16` indices | Draw ranges reference this array |
| next | Resource-specific records | Parsing stops here and delegates to the vehicle or course interpretation |

The exact common-prefix boundary and all arrays are exposed in `DxCommonPrefix`. Course and vehicle readers use the same `VertexData`, UV, index validation, and existing tag-2/7/8 draw-record code where their surrounding grammar is structurally shared. Prefix parsing alone does not establish the meaning of any later field.

Evidence: 36/36 retail course prefixes and all previously supported vehicle DX prefixes parse using this reader. Course revision-135 index validation and vehicle global-table validation remain separate policies.
