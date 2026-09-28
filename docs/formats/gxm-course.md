# Course GXM structure (partial)

Status: **partial, paired-source parser**. Confirmed on Demo 8.4.1 France1 and
Italy1 GXM/TXT pairs only.

## Parsed regions

The first 32 bytes are eight little-endian `uint32` header words. Header word
`0x08` bounds an observed 16-byte-stride bank beginning at `0x20`; its payload
values are retained as opaque data. The parser does not name this bank as
positions, normals, colors, or transforms.

The trailing node table is parsed with its paired TXT inventory. The TXT names
and classes supply the expected serialized table length, giving a direct
end-relative boundary. The table starts with a length-prefixed `moModel` root.
Subsequent records observed in both samples are:

| TXT class | Binary record | Interpretation |
|---|---|---|
| `moMesh` | `u8 class=1`, `u8 flags=1`, `u16 control`, `u32 Index`, `u32 Size`, `u16 name_length`, name | class/name/span are checked against TXT; `control` is preserved without semantics |
| `moUnknown` | `u8 class=3`, `u8 flags=1`, `u16 child_count`, `u16 name_length`, name | name and declared direct-child count are checked against TXT |

Names are Latin-1 byte strings. The parser validates the complete table reaches
EOF, each name and mesh span matches its TXT record, and every encoded unknown
node child count matches the TXT hierarchy. This is `CONFIRMED_BY_BINARY` and
`CONFIRMED_BY_SOURCE_COMPILED_PAIR` for the two current samples. The reader
requires the paired TXT; it does not scan the GXM for a candidate name.

## Unknown regions

The vertex/index data before the trailing node table, object transforms,
material bindings, and relationships between source mesh spans and source
coordinates remain **UNKNOWN**. The node-table parser is read-only and is not a
GXM writer.
