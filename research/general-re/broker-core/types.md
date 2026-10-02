# Types and payload ownership

Retail tags, `CONFIRMED_BY_EXE` from XML dispatch, setters, destruction and Dump.
Machine-readable summary: [types.json](types.json).

| Tag | Type | `entry+04` payload |
|---|---|---|
| 0 | Bool | owned 1-byte value |
| 1 | Float | owned 4-byte float |
| 2 | Int | owned 4-byte integer |
| 3 | Matrix | owned 0x40-byte matrix |
| 4 | String | owned 4-byte interned-string-ID wrapper |
| 5 | Vector4 | owned 0x10-byte vector |
| 6 | Vector3 | owned 0x0C-byte vector |
| 7 | Vector2 | owned 8-byte vector |
| 8 | MarkerListName | owned 4-byte interned-name wrapper, not marker geometry |
| 9 | StringList | owned 0x10-byte vector wrapper and owned string elements |
| A | XmlData | direct polymorphic object, not a pointer wrapper |
| B | XmlFilename | owned 4-byte interned logical-filename wrapper |
| C | empty/unbound | no live typed payload |

“StringListName” in the task is not adopted as an unproven pointer-to-list-name
representation: the observed type is StringList with a vector payload.

`004DD980/004DDC20`, removal `004D8D40`, Dump `00601D00` and serializer
`005FE460/005FE580` independently establish 0x0C as empty. There is no matching
typed XML parser branch for it. Rows skipped by Dump explain its manager size
exceeding emitted count; no hidden type should be invented from that difference.

Matrix/vector numerical conventions and every XmlData subclass are outside this
closeout. Dump values are formatted diagnostics, not lossless float serialization
or raw-memory representations. Typed XML is the persistence representation.
