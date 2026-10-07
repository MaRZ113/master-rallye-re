# ELF PackFS map

Source SHA256:
`b15a80c516986bfd7f9fcfcfa2ec5fbf37643778c6363dde460006d7001a78f2`.
ELF32 little-endian MIPS executable, entry 0x00100008. One PT_LOAD:
file offset 0x1000, VA/PA 0x00100000, file size 0x38d490,
memory size 0x3d9978, RWX flags, alignment 0x1000.
For loaded source bytes, VA = file offset + 0xff000.

| Region | VA start | VA end (inclusive) |
| --- | --- | --- |
| .text | 0x00100000 | 0x0040da73 |
| .data | 0x0040da80 | 0x00442167 |
| .vudata | 0x00442170 | 0x004447ef |
| .rodata | 0x00444800 | 0x0048d0ef |
| .gcc_except_table | 0x0048d100 | 0x0048d48f |
| .sbss | 0x0048d500 | 0x0048d54b |
| .bss | 0x0048d580 | 0x004d9977 |

## Tooling boundary

Ghidra 12.1.4 (2026-09-21 build) at
`D:\Game\Master Rallye\_reverse-tools\ghidra-bridge-main\ghidra_12.1.4_PUBLIC`
was the only installation found across D:\Game, D:\Program Files and D:\projects.
Queries use `ghidra_ai_bridge.exporters.runner.export_single_function` from the
installed bridge environment. An ignored project is created inside this track.

Automatic R6 detection is wrong for these delay-slot instructions. Explicit
`MIPS:LE:64:64-32addr`/o32 preserves that control flow, but stock Ghidra lacks
R5900 SQ/LQ support. `--stack-surrogate` temporarily replaces SQ/LQ with SD/LD
in the in-memory PackFS analysis window 0x002b0000..0x002c1100, retaining low
64-bit register save/restore behavior. It clears stale function boundaries and
incorrect no-return assumptions for the query. This is an analysis surrogate,
not a full R5900 model. Original words and surrogate words are recorded in
ignored `data/packfs-local/exports/stack-surrogates.json`; every transaction is
rolled back. The canonical ELF is never written; queried projects are not saved.
Critical scalar loads, stores, branches, JAL/JALR and structures are checked
against source instruction words. No graphics/MMI behavior is inferred from
this surrogate. Raw exports and databases remain ignored.

## Owners and contracts

Names below describe recovered roles; they are not claimed original symbols.

| Owner | Address / last instruction | Evidence and flow |
| --- | --- | --- |
| PackFS construction | 0x002bb6a0 | Initializes pack object, psFile and raw-codec index |
| FilePackFS construction | 0x002bb7c0 | Registers PACK: filesystem; owns pack object |
| SetPackFile | 0x002bb840 | Calls OpenPackFile 0x002bb448 |
| OpenPackFile | 0x002bb448..0x002bb69c | Builds .PAK/.000 paths, opens buffered psFile, reads decoded 8-byte directory header and body, calls 0x002bfb80 |
| Directory attach | 0x002bfb80 | Stores header/body, calls 0x002bfe18 |
| Directory fixup | 0x002bfe18..0x002bfeac | Calls 0x002bfeb0, 0x002bfef8, 0x002bff88 |
| Header pointers | 0x002bfeb0..0x002bfef0 | Relocates body +4,+0xc,+0x14 |
| Codec pointers | 0x002bfef8..0x002bff80 | Four pointer fields in each 16-byte descriptor |
| Buckets/nodes | 0x002bff88..0x002c00b0 | Bucket heads, hash-next +0x10, sibling +0xc, directory child +0 |
| Path hash | 0x002bfd98 | Length-seeded hash, slash normalization, case mask 0xdf |
| Path lookup | 0x002bfbd8 | Masks hash by bucket_count-1, compares inline path +0x18, follows +0x10 |
| Codec lookup | 0x002bfce0 | Name lookup over descriptors; raw string is at 0x0047ff98, dir at 0x00480fa0 |
| File open | 0x002bba40 | Looks up node, returns node +8 size, creates handle |
| File size | 0x002bbc58 | Looks up node and returns +8 |
| File seek | 0x002bbd08 | Bounds logical handle cursor |
| File read | 0x002bbdb8 | Delegates range reads to pack data owner |
| Stored-range read | 0x002bb2f0 | Data seek = node +0 offset + relative cursor; stored-size +4 bounds |
| Whole stored-node load | 0x002bb398 | Allocates +4, reads +0 offset, checks codec against raw index |
| Generic psFile open | 0x002b85a8 | Installs compressor when file header selects one |
| Header read | 0x002bc068 | Reads 8 bytes into compressor state +0xc |
| Compression setup | 0x002bc0e0..0x002bc1b4 | Copies header, selects compressor, reads first block record |
| Block record | 0x002bc1e8..0x002bc238 | Reads 8 bytes into state +0x24/+0x28 |
| Block seek | 0x002bc240 | Uses nominal output block size and previous/current compressed lengths |
| Compressed block read | 0x002bc380..0x002bc4cc | Reads exactly current stored length, advances block record, invokes virtual decompressor |
| Compressor selection | 0x002bc6c0 | Header byte +4 == 1 selects LZO object 0x00496940; other values return no compressor |
| LZO init | 0x002bc4d8..0x002bc554 | Calls 0x002c06e0 with version 0x1070 and platform sizeof contract |
| LZO wrapper | 0x002bc5c0..0x002bc614 | Calls 0x002c0cd0(src, src_len, dst, out_len_ptr), tests return code, reports packet failure |
| LZO1X decoder | 0x002c0cd0..0x002c1008 | Literal/M1/M2/M3/M4 state machine; output length and source-end status |

The vtable at 0x004804a0 contains (adjustment, target) pairs. Its +0x1c
decompressor target is 0x002bc5c0, +0x24 buffer target 0x002bc618, and +0x2c
release target 0x002bc668. This links generic wrapper to decoder independently
of string proximity. Direct JAL at 0x002bc5e0 targets 0x002c0cd0.
Version strings `1.07` occur at 0x00480fd0 and 0x00480fd8; version constant,
decoder behavior and caller establish the LZO 1.07-era family (CONFIRMED_BY_BOTH).

Relevant diagnostic xrefs include OpenPackFile strings at 0x0047ffa0..0x004800b0,
file lookup/size/read at 0x004801f0/0x00480270/0x004802f0, and compressor buffer
failure at 0x00480470. Full machine exports are local, not committed.
