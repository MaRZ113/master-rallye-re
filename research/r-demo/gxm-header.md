# GXM header and geometry prefix

All paths below are corpus-qualified. `word_0xNN` names avoid assigning unproved roles.

For the `material_table` variant, 32 header bytes are followed by `word_0x0c` materials (zero in one frontend file). Each material has a u16-length ASCII name, a u8 slot count, and slots of three raw control bytes plus a u16-length ASCII reference. The remainder after the third float3 array stays opaque.

## demo-8.4.1

- GXM files: 76; variants: {'opaque_after_header': 29, 'material_table': 47}.
- `word_0x10 == 3 * word_0x18`: 76/76.
- Material-table files with unit-length float3 vector A array, finite float3 vector B and C arrays (B can be empty), indexed ten-word records, and 12 `FF` separator bytes: 47.

## demo-9.3.1

- GXM files: 33; variants: {'material_table': 33}.
- `word_0x10 == 3 * word_0x18`: 33/33.
- Material-table files with unit-length float3 vector A array, finite float3 vector B and C arrays (B can be empty), indexed ten-word records, and 12 `FF` separator bytes: 33.

## Header fields

| Offset | Observed interpretation | Evidence |
|---:|---|---|
| 0x00 | Packed variant/version word; low byte `02` in scanned corpus | CONFIRMED_BY_CORPUS |
| 0x04 | Zero in scanned corpus | CONFIRMED_BY_CORPUS |
| 0x08 | Nonzero in some nonvehicle variants; meaning unknown | CONFIRMED_BY_CORPUS |
| 0x0C | Number of material records in the recognized material-table variant | CONFIRMED_BY_CORPUS |
| 0x10 | Number of unit-length float3 vectors in recognized variant; equals 3 × word_0x18 in every file | CONFIRMED_BY_CORPUS |
| 0x14 | Number of finite float3 vectors in array B in recognized variant | CONFIRMED_BY_CORPUS |
| 0x18 | Number of ten-word records, each with three index triples; triangle interpretation is high confidence | HIGH_CONFIDENCE_INFERENCE |
| 0x1C | Number of finite float3 vectors in array C; second record index triple addresses this array | CONFIRMED_BY_CORPUS |

The parser refuses to locate geometry in variants whose material prefix is not proven. Array offsets and numeric bounds for every recognized file are in `gxm-header-corpus.json`.
