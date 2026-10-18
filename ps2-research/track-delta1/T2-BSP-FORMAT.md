# T2: PS2 course `.BSP` format (reversed from the loader)

Status: grammar reproduced and verified on all 36 files (every file parses to its exact byte size, 0 trailing bytes, all count
invariants hold). Meaning of several fields is still open and marked below. No live PS2 capture was done (PCSX2 is still required
for Turkey3 by the policy).

## Where it comes from
| Item | Evidence |
|---|---|
| `FUN_00394498` (ELF `SLES_509.06`, VA 0x394498..0x3946db) receives an object whose path is at +0xc. When the path contains `course` (string 0x4879a8) it strips the extension (`.` at 0x4879b0), appends `.bsp` (0x4879b8), opens a 0x38-byte file stream and calls the reader; the result is stored at `(param_1+4)+0x30` | Ghidra EER decompilation (read-only), `elf_string_refs.py` finds the string references |
| Reader `FUN_003b6cd8`: reads six u32; creates pools; reads the tree with `FUN_003b6ef8`; reads a plane table with `FUN_003b6e10` | same |
| `FUN_003b7278` plane record = 3 f32 + f32 + u32 (20 bytes); `FUN_003b7310` node payload = 2 u32; `FUN_003b7460` one boolean byte | same |
| Callers of the opener: `0x390378` inside `0x3900f0` (course object setup) | same |

## Layout (little endian)
```
header      6 x u32: w0 w1 w2 w3 w4 w5
tree        recursive nodes (below), depth first
plane table w5 x 20-byte records: f32 nx, ny, nz, d ; u32 code
```
Node:
```
u32 field_0, u32 field_1
u8  has_plane   -> 20-byte record (nx ny nz d code)
u8  has_payload -> u32 word0, u32 word1
u8  has_child   -> u8 sel_a, u8 sel_b ; the child subtree follows immediately
u8  has_sibling -> u8 sel_a, u8 sel_b ; the sibling subtree follows (after the child's subtree)
```
Booleans are single bytes (the loader treats nonzero as true). `sel_a`, `sel_b` choose one of three typed pools
(`003b8988`, `003b8868`/`003b88f8`, `003b87d8`) for the allocation; PC tag100 has one selector per link, PS2 has two.

## Verified relations (all 36 files; census in `ps2-bsp-census.json`)
- consumed bytes equal file size; nodes = 2 x (nodes with a plane) + 1.
- w3 = w4 = number of nodes with a plane; w0 = number of nodes with a payload; w5 = plane table size.
- Payload nodes are leaves only. A payload is `(word0, word1)`: `word0` low 24 bits are a start index and `word1` a count (1 to 19).
  The runs of all payload leaves partition the plane table exactly and in order (Turkey3: counts sum to 41,245 = table size).
  Each such leaf therefore owns a contiguous run of plane records: a convex cell bounded by those planes (INFERENCE for the geometric reading).
- `field_0` is 0, 1 or 0xFFFFFFFF; the counts of nodes with `1` and `0xFFFFFFFF` equal w2 and w1 respectively (Turkey3: 7,096 and 16,166).
- Plane `code`: in the tree it is 0xFFFFFFFF for some planes (3,146 on Turkey3) and otherwise a large id; the table has 16,412 distinct ids on Turkey3.
  The ids look like polygon or surface identifiers (INFERENCE).

## Compared with PC tag100 (`src/master_rallye/course_tag100.py`)
Same family: depth-first nodes, 2 u32 leading fields, optional 20-byte plane record, child/sibling flags.
PS2 additions: header is six words without a tag; a payload block (8 bytes) in place of the PC "list"; two selector bytes per link;
a trailing plane table. PC Turkey3 has 235,089 nodes, all planes coded -1; PS2 Turkey3 has 99,681 nodes with polygon ids.
So the PS2 file carries per-leaf convex cells and polygon ids that the PC tree does not.

## Orientation and leaf kinds (added by the query work, see T2-QUERIES.md)
- Plane convention in both trees: `n.p + d >= 0` is the front half-space, and the front half-space is the **second** link (`sibling` in the
  parser's naming), the back half-space is the first link (`child`). Checked on PC tag100 (98% empty above ground, 99% solid below) and on
  the PS2 tree (ground-plane matches only with this orientation).
- A plane node has exactly two links. `field_0` of a leaf follows from its link: every `-1` leaf is a back link (solid side), every `+1`
  leaf is a front link (empty side), on PS2 (16,166 and 7,096 on Turkey3) and PC alike. Payload leaves occur on both links
  (17,312 front, 9,267 back on Turkey3).
- Payload leaves are therefore the PS2-specific addition. Their meaning (solid or empty, and how the stored planes define polygons) is
  not settled: treating them as solid when reached through a back link gives 90 to 99% solid below ground but also 21% solid 30 units
  above ground, so the rule is incomplete.

## Open
- How the engine decides solidity inside a payload leaf, and how `code` maps to the visual polygons, material and `$surfacetype`.
- The PS2 query code that walks this tree. `0x2470f8` (convex versus BSP) calls `0x247ef0`, `0x248658`, `0x248780`, `0x248820`, `0x248fd8`;
  `0x247ef0` was read and handles hull plane sets, not the tree walk, so the walker is elsewhere. Next target: the callers of the leaf
  accessors and the `BSPNonLeafNode` virtual methods.
- The PC runtime meaning of tag100 beyond the solid/empty model is also not fully established (see `docs/course-cooker.md`).

## Reproduce
    python -X utf8 ps2-research/track-delta1/bsp_census.py "D:/Game/Master Rallye PS2" ps2-research/track-delta1/ps2-bsp-census.json
    python -X utf8 ps2-research/track-delta1/test_ps2_bsp.py

Ghidra: `DecompFns.java` (run with `analyzeHeadless ... -readOnly -noanalysis -postScript DecompFns.java <out> <addr>...` on the
`EERevalidation2` project). Raw decompiler output stays local (`data/track-bsp/`), it is not committed.
