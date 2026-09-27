# Minimal observed rev131 → rev135 delta model

This is an output-difference model for the same-source Trooper pairs only. It
does not state how either cooker implements the transformation internally.

| Structure | Rev131 observation | Rev135 observation | Minimal observed transform | Status |
|---|---|---|---|---|
| Header revision | 131 at offset `0x04` | 135 at offset `0x04` | `RESERIALIZE` revision field | `CONFIRMED_BY_BYTES` |
| Header geometry counts | Same in each pair | Same | `COPY` | `CONFIRMED_BY_BYTES` |
| Position/normal/color/UV arrays | Exact source-order bytes | Exact same bytes | `COPY` | `CONFIRMED_BY_BYTES` |
| Local uint16 indices | Values differ; draw triangles permuted | Same oriented triangle multisets in changed order | `REORDER` triangles using the recorded per-draw map | `CONFIRMED_BY_BYTES` for these assets |
| First 20 draw bytes | Same mapped record core | Same mapped record core | `COPY` | `CONFIRMED_BY_BYTES` |
| Draw pre-string prefix | 11 opaque bytes | 24 parsed bytes | `UNKNOWN` (13-byte net growth; field mapping/source unknown) | `UNKNOWN` |
| Texture-reference suffix | Exact names and order | Exact same suffix | `COPY` | `CONFIRMED_BY_BYTES` |
| Trailing uint32 index block | Byte sequence unchanged | Same bytes after relocation | `COPY` bytes in this observed output model; semantic role `UNKNOWN` | `CONFIRMED_BY_BYTES` for bytes |
| tag101/tag102 | Present on role-specific resources | Exact same raw payloads after relocation | `COPY` bytes in this observed output model | `CONFIRMED_BY_BYTES` for bytes |
| marker-1339 / remaining trailer | Exact bytes | Exact same bytes after relocation | `COPY` bytes in this observed output model | `CONFIRMED_BY_BYTES` for bytes |
| Alignment | Existing section boundaries | Draw tail shifted by record growth | `RESERIALIZE` offsets as a consequence of record size | `CONFIRMED_BY_BYTES` |

`COPY` here describes a viable byte-level transform for the paired outputs; it
does not prove that the cooker internally copied rather than recomputed those
same values. The observed +13 bytes per draw are explained by the difference between the
11-byte legacy pre-string region and the 24-byte rev135 prefix. The exact
overlapping changed bytes and each new prefix are stored per record in
`dx-binary-diff.json`. The edit model's changed-byte accounting is complete for
all three files; see `dx-binary-diff.md` for the distinction between aligned
edit counts and same-offset Hamming counts.

## Not yet an upgrader recipe

The output correspondence is strong enough to state which geometry and
reference data remain stable in these pairs. It is not enough to generate the
rev135 prefix or validate the meaning of the trailing index block. We do not
know whether prefix values are constants, source-derived fields, or values
recomputed from internal cooker structures. No generic translation procedure
is justified yet.
