# DX draw to runtime material

**CONFIRMED_BY_EXECUTABLE:** `FUN_005520E0` serializes a tag-2 material with 3 ordered texture names. `FUN_005528B0` reads the matching layout, allocates 0x48 bytes, calls `FUN_0057F7E0`, restores fields, and resolves texture names. `FUN_0057F8B0` copies the same layout. `FUN_0054D4C0 -> FUN_00577620 -> FUN_00577FB0 -> FUN_00580360` connects the material-bearing object to shader selection. This is a paired serialization and call/data-flow trace, not a numeric-value guess.

| DX core offset / parser field | Runtime destination | Transform |
|---|---|---|
| +0x04 vertex_base | +0x18 | dword |
| +0x08 local_vertex_max | +0x30 | dword |
| +0x0C index_start | +0x14 | dword |
| +0x10 index_count | +0x1C | dword |
| +0x14 unknown_0x14 | +0x24 | dword; meaning unknown |
| +0x18 unknown_0x18 | +0x44 | type code constructs optional variant object |
| +0x1C unknown_0x1c_float | +0x28 | float |
| +0x20 flags_0x20[0] | +0x22 | byte; alpha enable |
| +0x21 flags_0x20[1] | +0x23 | byte; alpha test selector |
| +0x22 flags_0x20[2] | +0x20 | byte; pass flag, not alpha-test selector |
| +0x23 flags_0x20[3] | +0x21 | byte; pass flag |
| +0x24 unknown_0x24 | +0x34 | direct dword feature-mask copy |
| following 3 names | +0x38/+0x3C/+0x40 | ordered looked-up texture handles |

`FUN_00580360` uses runtime +0x34 bits 0/1 for base, bit 0x4 for env conditional on Reflections, bit 0x8 for noise conditional on DetailPasses, and bit 0x10 for water. It uses +0x22 and +0x23 to choose no suffix / _alpha / _alphatest. Byte 2 maps to +0x20, not +0x23: the post-R4D hypothesis that byte 2 chooses alpha test is rejected. `FUN_005781B0` reads runtime +0x20/+0x21 in pass setup. The binary parser retains the raw unknown_0x24 name for compatibility while the semantic model exposes its established feature-mask role.

Ghidra missed the virtual shader methods at 0x5867A0/0x586150. They were disassembled in a temporary transaction that was rolled back. Large raw decompiles remain outside Git.
