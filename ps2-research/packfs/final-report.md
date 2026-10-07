# PS2 PACKFS STATUS: COMPLETE

Filesystem foundation for the exact supplied PS2 inputs is complete. Static
ELF/offline validation only; no manual PS2 runtime or PC graphics feature claim.

REPOSITORY:

- Worktree: `D:\Game\Master Rallye\master-rallye-re-general`
- Branch: `master`
- Starting HEAD: `68e5f10f51cf2d5524ac15b41787beeba1f28d44`
- Final HEAD: `940d4edf39392118b796d832160528fbe75702ec`, an independently
  created renderer commit during this run; no PS2 files are in that commit.
- No new branch/worktree; no push.
- No PS2 commit created; shared index left untouched because parallel renderer
  work appeared during execution. PS2 additions remain under `ps2-research/`.

HISTORICAL POLICY:

- research/general-re ref touched: NO (still starting HEAD).
- Historical research/r-* edited by this track: NO.
- Concurrent renderer work had its own changes, including research/r-gfx5;
  those were independently committed and are excluded from this result.

INPUTS (all available, freshly hash-verified):

| File | Exact bytes | SHA256 |
| --- | ---: | --- |
| SLES_509.06 | 3739852 | b15a80c516986bfd7f9fcfcfa2ec5fbf37643778c6363dde460006d7001a78f2 |
| SYSTEM.CNF | 56 | db08eef06278820a562f9cdacd6a2d5d2bb31870e7cf3a51e83daee3a90c5df2 |
| TNG.PAK | 135556 | d98c7cf1049a8a3bc2f90a528a2b6f52cd43c16c2e0564830d5ecb9c592ab28d |
| TNG.000 | 1225915283 | 004ac1676376275bf40c1fd5c1c4a9dcfaae870bf1a7916434eb73b0b1faff86 |

ELF PACKFS:

- Pack owner/OpenPackFile: 0x002bb448.
- Generic compression setup/header/block owners: 0x002bc0e0, 0x002bc068,
  0x002bc1e8, 0x002bc380.
- LZO wrapper: 0x002bc5c0; inner decoder: 0x002c0cd0.
- LZO version family: 1.07-era, init constant 0x1070.
- Evidence: CONFIRMED_BY_BOTH, checked through ghidra-bridge exporter on
  Ghidra 12.1.4. See `elf-packfs-map.md` for exact boundaries, xrefs, call
  contract, ELF layout and temporary R5900 stack-analysis surrogate limitations.

COMPRESSION FRAMING:

- Header: u32 decoded size; u8 compressor_id=1; u8 unknown_0x05=1;
  u16 nominal output block size=8192.
- Records: u32 previous payload length; u32 current payload length; then exactly
  current-length bytes of one inner LZO1X stream. Lengths exclude record bytes.
- No inter-record alignment; no raw-block escape proven in the LZO path.
- Raw resource storage is a separate directory codec.
- Terminal: previous=last length, current=0, exact input/output exhaustion.

TNG.PAK GOLDEN:

- Input: 135556 bytes.
- Output: 269668 bytes.
- Output SHA256:
  `391929a42dac29eaa6a4306d9e178ad7da925a5426de0befd5550524cc6a56c4`.
- Golden match: YES; pure Python and independent FFmpeg LZO are byte-identical.
- 33 blocks: first 32 output 8192 bytes; last output 7524 bytes.

DIRECTORY:

- Root: `\`, structurally reached directory node.
- Fixup owner: 0x002bfe18, with helpers 0x002bfeb0/0x002bfef8/0x002bff88.
- Relocation: pointer - serialized body base 0x005c8498; zero remains null.
- Header: 32 bytes, 96-byte codec block, 4100-byte hash block, 265432-byte node
  pool. Node count 3736, codec count 4, buckets 1024.
- Files/directories share 24-byte node prefix plus NUL-terminated name aligned
  to 4 bytes. Directory +0 is first child; file +0 is TNG.000 byte offset;
  +4 stored size; +8 reported wrapper size; +0xc sibling; +0x10 hash-next;
  +0x14 codec; +0x16 UNKNOWN; +0x18 inline path.
- No string-carving parser. Hash-chain, sequential node and tree validations agree.

MANIFEST / TNG.000:

- Complete deterministic `tng-manifest.json`: 137 directories, 3599 files.
- Compressed: 3345 PackFS/LZO header-confirmed resources; raw: 254; unknown
  resource compression in this source set: 0.
- All ranges valid: YES. Invalid ranges: 0. Overlaps: 0. Gaps: 0.
- Total stored bytes: 1225915283.
- Total header-declared decoded bytes: 1419944771 (inventory, not all-resource
  decompression proof).
- All 3345 compressed headers are (1,1,8192). Full decoding is limited to the
  eight validation resources below.

EXTRACTION SANITY (exact paths use prefix `\TNG\DATAPSM\`):

| Path below prefix | TNG.000 offset | Stored | Decoded | Compression |
| --- | ---: | ---: | ---: | --- |
| HUD\HUD-TEMPLATE.PSB | 1209525455 | 1095 | 3004 | PackFS/LZO |
| HUD\HUD-NUMS.PSB | 1209465583 | 1005 | 2656 | PackFS/LZO |
| HUD\NEWHUD_000.GXI | 1209708170 | 9856 | 16392 | PackFS/LZO |
| COMMONTEXTURES\ENVSOURCE64X64.GXI | 1036874990 | 10660 | 16392 | PackFS/LZO |
| COMMONTEXTURES\REAR128-TGA.GXI | 1038214044 | 12244 | 65544 | PackFS/LZO |
| COURSE\FRANCE1\WATER-TGA.GXI | 1043658891 | 11195 | 16392 | PackFS/LZO |
| COURSE\FRANCE2\GRASS-TGA.GXI | 1047518025 | 16392 | 16392 | raw |
| COURSE\ITALY3\I2A_GRASSPATH-TGA.GXI | 1080561258 | 16104 | 16392 | PackFS/LZO |

Stored-range and decoded-payload SHA256 for every entry are in
`extraction-provenance.json`. Payload files are local/ignored only. All six GXI
have magic 0x00013039 and exact 8+width*height*4 size; channel order remains UNKNOWN.

GRAPHICS TARGETS:

- HUD: 135 name-matched candidates, including PSB layouts and NEWHUD GXI.
- Grass/detail: 175 candidates; particles/GRASS1 and BUSH1 exist.
- Water: 46 candidates; CommonTextures/WATERSURFACE2 exists.
- Reflection/environment: 19 candidates, including ENVSOURCE and REAR128.
- ELF detail/surface strings and named resource existence are confirmed;
  spawning, material meaning, HUD element mapping and render paths remain UNKNOWN.
- Full candidate metadata: `graphics-targets.json`; scope: `graphics-targets.md`.

HISTORICAL FINDINGS:

- Confirmed: LZO 1.07-era decoder lead, golden decode, real named resource families.
- Disproven: no LZO, fixed 24-byte strip, 0x69-as-raw flag, string-carved metadata
  as authority, historical boundaries as ground truth.
- Unresolved: exact arguments/errors of individual old failed LZO-safe calls;
  purpose of header +0x05/node +0x16; full asset/render semantics.
- Framing failure mechanism independently reproduced: framed PAK fails in inner
  LZO decoder; correctly sliced first stream succeeds.

TOOLING:

- CLI: `ps2-research/tools/tngtool.py`.
- Commands: info, decompress-pak, list, find, verify, extract.
- Runtime dependency: Python 3.10+ standard library only.
- Repeatable report/extraction: `tools/build_report.py --inputs <source directory>`.
- Read-only ELF queries: `tools/elf_query.py`, installed ghidra-bridge/PyGhidra.
- Usage and exact commands: `../README.md`.

TESTS:

- PS2 unit/integration: 26/26 PASS, no skipped canonical tests.
- Relevant existing library: 22/22 PASS.
- Six CLI commands and overwrite guard: PASS.
- Pure Python vs independent oracle byte equality: PASS.
- Repeat-generation JSON byte identity: PASS.
- Compileall and diff/new-file whitespace checks: PASS.
- Proprietary ignore checks and final input hashes: PASS.
- Renderer rebuild: not needed, no renderer code changed by this track.

FILES CREATED (all below `ps2-research/`; no existing tracked file modified):

- `.gitignore`, `README.md`.
- Tools: `tools/tngtool.py`, `tools/elf_query.py`, `tools/build_report.py`.
- Tests: `tests/test_tngtool.py`.
- Documentation: `packfs/findings.md`, `elf-packfs-map.md`,
  `compression-framing.md`, `directory-format.md`, `tng-directory.md`,
  `graphics-targets.md`, `validation.md`, `next.md`, `final-report.md`.
- Structural JSON: `packfs/input-provenance.json`, `tng-manifest.json`,
  `graphics-targets.json`, `golden-validation.json`, `extraction-provenance.json`.
- Ignored local data: Ghidra projects/exports/logs, full decoded directory,
  eight validation payloads/provenance and CLI smoke output under `data/`.

PS2 COMMIT: NOT CREATED. WORKING TREE: `?? ps2-research/` only; concurrent renderer
work was independently committed. Shared index untouched by this track.
No proprietary game payload staged or committed.

RECOMMENDED NEXT PS2 STEP: bounded HUD PSB resource/layout reverse, starting from
the two small exact extracted PSB files and their ELF consumers. See `next.md`.
Filesystem phase stops here.
