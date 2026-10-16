# Target identity and compatibility

## Original PC retail executable used with REA

| Property | Value |
|---|---|
| Path | `D:\Game\Master Rallye Pristine\MRallye.exe` |
| Size | 3,121,214 bytes |
| SHA-256 | `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4` |
| Format | PE32, I386 |
| PE timestamp | `0x3C02695D` |
| REA result | Ghidra 12.1.4 analysis; 13,099 procedures and 7,467 defined strings reported |

The hash is the previously validated retail PC target and was the target
selected for the REA queries in this audit. It is not the PS2 executable.

## Canonical PS2 source set

| File | Size | SHA-256 |
|---|---:|---|
| `SLES_509.06` | 3,739,852 | `b15a80c516986bfd7f9fcfcfa2ec5fbf37643778c6363dde460006d7001a78f2` |
| `SYSTEM.CNF` | 56 | `db08eef06278820a562f9cdacd6a2d5d2bb31870e7cf3a51e83daee3a90c5df2` |
| `TNG.PAK` | 135,556 | `d98c7cf1049a8a3bc2f90a528a2b6f52cd43c16c2e0564830d5ecb9c592ab28d` |
| `TNG.000` | 1,225,915,283 | `004ac1676376275bf40c1fd5c1c4a9dcfaae870bf1a7916434eb73b0b1faff86` |

All four hashes were checked against the canonical values during this audit.
`SLES_509.06` is the 32-bit MIPS R5900 executable REA could not import. Its
prior static PS2 analysis was produced by the project's Ghidra/PyGhidra path
and original-byte tools, not by the current REA provider.

A direct standard-library ELF header/PT_LOAD check on the same file found:
ELF32, little-endian, `ET_EXEC`, machine `EM_MIPS` (8), entry `0x00100008`,
raw `e_flags=0x20924001`, one `PT_LOAD` at file offset `0x1000` / VA
`0x00100000` (`filesz=0x38d490`, `memsz=0x3d9978`). The checked file-backed
mapping is therefore `file_offset = VA - 0x000ff000` within that segment.
The raw `e_flags` value is recorded without interpreting it as proof of a
specific supported REA processor profile. A focused byte verifier compared
the frozen TREEBLEND1 instruction words and data anchors to this mapping;
details are in `ps2-elf-byte-recheck.json`. It confirms provenance, not
instruction semantics.

## PC Course SDK reference

`D:\Game\Master Rallye\master-rallye-re-course`, HEAD
`4244fa0c4d878523c9947f54816bf377cdfb2589`, branch
`research/r5t-course-archaeology`, clean before and after inspection. The
Course SDK was read-only and was not changed.
