# Serialized TNG directory

The outer decoded image begins with little-endian u32 signature 0x0100FACE
and u32 body_size=0x41d5c=269660. The first value is confirmed by bytes; the
loader reads the second to allocate/read the body. The tool requires both
signature and exact size, even though the queried loader does not validate the
signature. All offsets below are relative to the **body**, starting at file +8.

| Body offset | Type | Meaning / canonical value |
| --- | --- | --- |
| +0x00 | u16 | Node count, 3736; confirmed against all traversals |
| +0x02 | u16 | Codec descriptor count, 4; used by fixup/codec lookup |
| +0x04 | u32 pointer | Codec table, body +0x20 |
| +0x08 | u32 | Codec block size, 96 bytes |
| +0x0c | u32 pointer | Hash table, body +0x80 |
| +0x10 | u32 | Hash block size, 4100 bytes |
| +0x14 | u32 pointer | Node pool, body +0x1084 |
| +0x18 | u32 | Node pool size, 265432 bytes |
| +0x1c | u32 | Serialized old body base, 0x005c8498 |

32 + 96 + 4100 + 265432 = 269660. The root is the structurally reached directory
node named `\`; it is not an additional guessed header pointer.

## Relocation

0x002bfe18 computes delta = actual_loaded_body - old_base. It relocates nonzero
header pointers +4,+0xc,+0x14 (0x002bfeb0), all four pointers in each codec
descriptor (0x002bfef8), bucket heads and node links (0x002bff88).
Offline equivalent: resolve pointer to body offset as pointer - old_base; zero
remains null. There is no generic relocation-offset table in this directory.

Codec descriptors are 16 bytes with four pointers: codec name, encoder command,
decoder command, unknown_0x0c. Their strings are in the codec block. Values are
`dir`, `raw`, `user`, `gz`; the last has `gzip`/`gzip -d` command strings. Those
labels do not make the PS2 resource bytes gzip streams: all 3345 `gz` entries
were independently checked to have PackFS/LZO header (1,1,8192).

The hash block starts with u16 bucket_count=1024, u16 unknown_0x02=0, then
1024 u32 head pointers. The ELF lookup hashes a logical path, masks by count-1,
compares the inline path and follows node +0x10. `path_hash()` implements the
length-seeded 32-bit arithmetic, slash conversion and 0xdf case mask seen at
0x002bfd98. All canonical nodes land in the expected buckets.

## Node layout

| Node offset | Type | Meaning |
| --- | --- | --- |
| +0x00 | u32 | File byte offset in TNG.000; for `dir`, first child pointer |
| +0x04 | u32 | Stored range size; zero for directories |
| +0x08 | u32 | Size reported by PackFS file open/size; wrapper size for compressed resources |
| +0x0c | u32 pointer | Next sibling in directory tree |
| +0x10 | u32 pointer | Next node in hash bucket |
| +0x14 | u16 | Codec index |
| +0x16 | u16 | unknown_0x16, canonical zero; flag meaning UNKNOWN |
| +0x18 | NUL-terminated ASCII | Original logical path spelling |

Node records end at the next 4-byte boundary after the NUL. All 5433 canonical
name alignment bytes are 0x69. Those bytes are padding, not compression flags.
Raw ranges are byte-addressed and not uniformly sector-aligned. The sole data
file is .000 as opened by ELF; data_file_index=0 in the manifest is an offline
mapping, not an invented on-disc node field.

For directory codec, +0 is relocated; file offsets are left intact. Both
+0xc and +0x10 are relocated for every node. The offline parser independently
checks sequential record boundaries, bucket-chain reachability and cycles,
directory-child/sibling links against full path parentage, uniqueness and a
single root. All 3735 nonroot nodes appear exactly once in the tree.

The JSON manifest preserves source spelling and serialized addresses. Ordering
is node-pool byte order. `entry_index` is an offline ordinal; it is not claimed
to be an engine resource ID. `directory_size_0x08` preserves the original field;
`unpacked_size` for gz resources is a distinct nested-header value, with explicit
provenance. Unsupported codecs/relocations, malformed strings, unsafe paths and
unknown canonical input hashes fail closed.
