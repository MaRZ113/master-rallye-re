# PS2 PackFS foundation

Status: **COMPLETE** for the supplied canonical PS2 filesystem foundation.
Evidence is static ELF analysis and offline byte validation. PS2 runtime,
full asset-format interpretation, and PC rendering integration were not tested.

The original TNG.PAK independently decodes to 269668 bytes with SHA256
`391929a42dac29eaa6a4306d9e178ad7da925a5426de0befd5550524cc6a56c4`.
The standard-library Python decoder and an independent installed FFmpeg LZO
decoder agree byte-for-byte. Neither consumes an old unpacked artifact.

Recovered structures give 137 directories and 3599 files, including exact HUD,
grass, water and environment resources. Hash-chain, contiguous node-pool and
directory-tree traversals all agree on 3736 nodes. All file ranges are valid,
nonoverlapping, and cover the 1225915283-byte TNG.000 completely.

## Historical supersession

| HISTORICAL | CURRENT | EVIDENCE |
| --- | --- | --- |
| LZO is not used | LZO1X token machine at 0x002c0cd0 is invoked by the compressor wrapper; init uses 0x1070 | CONFIRMED_BY_BOTH |
| TNG.PAK is directly parsable compressed bytes | Decode 33 framed streams first; the golden directory is the authority | CONFIRMED_BY_BOTH |
| BXML-like header is always 24 bytes | The validated resources use an 8-byte file header and variable per-block 8-byte records | CONFIRMED_BY_BOTH |
| 0x69 implies raw entry | All 5433 node-name alignment bytes in this directory are 0x69 padding; codec comes from node +0x14 | CONFIRMED_BY_BYTES |
| Strings carved from compressed PAK provide authoritative offset/size metadata | Offset/size belongs to a structurally reached node, not to a string occurrence | CONFIRMED_BY_BOTH |
| Historical unpacked file boundaries are correct | Fresh manifest ranges and independently decoded payloads supersede them; old artifacts were not used | CONFIRMED_BY_BYTES |

The precise input/caller/header bytes of individual historical failed
`lzo1x_decompress_safe` invocations were not available. Feeding the full framed
PAK fails in the independent decoder, while its correctly sliced first stream
succeeds. This proves the framing error mechanism without claiming to have
reproduced every historical invocation or its exact error code.

## Remaining unknowns

- Compression header byte +0x05 is consistently 1; its purpose is UNKNOWN.
- Node +0x16 and hash-table +0x02 are zero but have no proven flag semantics.
- Codec `user` and alternate codec/header values are unsupported and rejected.
- Names identify graphics candidates, not rendering roles or visual effects.
- A matching GXI size equation does not prove RGBA channel order, swizzling,
  palette/mipmap policy, or a complete texture format.

See `elf-packfs-map.md`, `compression-framing.md`, `directory-format.md`,
`tng-directory.md`, `graphics-targets.md`, and `validation.md` for evidence scope.
