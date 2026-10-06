# R5T-F.2.1 — tag1400 wire layout

## Evidence and boundary

The supported Retail executable is `MRallye.exe`, SHA256 `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`. Ghidra Bridge decompilation of `0x005541D0` shows a 40-byte input header, `dimension_0 * dimension_1` per-cell uint32-counted lists, a byte-length-prefixed string table, and 56-byte records (`9×float32, uint32 string reference, 4×float32`). Fields retain neutral wire names.

The parser ends tag1400 exactly before a later tag1500 region in the controlled France1 pair. In that pair the previously called `1,824,828-byte tag1400 region` is actually the complete post-tag1339 suffix remainder `U + R`: tag1400 U is 1,809,324 bytes and tag1500 R is 15,504 bytes. R is byte-identical between donors.

## Fixed and repeated fields

| Relative offset | Wire type | Neutral field | France1 baseline | Status |
|---:|---|---|---:|---|
| 0 | uint32 | tag (1400) | 1400 | `CONFIRMED_BY_BINARY` |
| 4 | float32 | scalar | 20.0 | meaning `UNKNOWN` |
| 8 | uint32 | dimension_0 | 167 | `CONFIRMED_BY_BINARY` |
| 12 | uint32 | dimension_1 | 105 | `CONFIRMED_BY_BINARY` |
| 16 | 3×float32 | vector_a | [-3651.0869140625, -45.389556884765625, -554.8106689453125] | meaning `UNKNOWN` |
| 28 | 3×float32 | vector_b | [-316.90234375, 122.82241821289062, 1533.0980224609375] | meaning `UNKNOWN` |
| 40 | repeated | dimensioned cells: uint32 count then count×uint32 | 17535 cells | `CONFIRMED_BY_BINARY` |
| after cells | repeated | uint32 string count; each uint32 byte length + raw bytes | 7 entries | `CONFIRMED_BY_BINARY` |
| after strings | repeated | uint32 record count; 56-byte records | 24115 records | `CONFIRMED_BY_BINARY` |
| record +0..+35 | 9×float32 | float_prefix | first record retained | semantics `UNKNOWN` |
| record +36 | uint32 | string_ref_index | first record `0` | string-table reference `CONFIRMED_BY_BINARY` |
| record +40..+55 | 4×float32 | float_suffix | first record retained | semantics `UNKNOWN` |

No writer is implemented. Allocation/runtime names are not inferred from this file layout.
