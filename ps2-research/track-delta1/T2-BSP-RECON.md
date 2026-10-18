# T2 reconnaissance: PS2 `.BSP` versus PC tag100 (not a full reverse)

Purpose: decide how the collision gate G-COLL can be approached. Static byte-level reading only; no live capture, no Ghidra pass yet.
Evidence labels: BYTES = read from the file now, STRING = ELF string, INFERENCE = not proved.

## Facts
| Fact | Evidence |
|---|---|
| 36 `\TNG\DATAPSM\COURSE\<C>\<C>.BSP` files; Turkey3 is 3,429,888 bytes (SHA-256 `70918e3e...a732`) | BYTES (PackFS via `tngtool`) |
| The first six u32 are `26579, 16166, 7096, 49840, 49840, 41245`. Relations: 26579 + 16166 + 7096 = 49841 = 49840 + 1 | BYTES |
| From offset 0x18 the stream follows the PC tag100 node grammar: 8-byte leading fields, a boolean, a 20-byte record of four floats plus u32, child and sibling booleans with selectors | BYTES (parser walk reaches 16 nodes, 11 plane records) |
| PC tag100 for the same course: header words `56366, 61179, 117544, 117544, 0`, 235,089 nodes, all plane codes `0xFFFFFFFF`, axis-aligned planes at the top of the tree | BYTES (`course_tag100.py`) |
| PS2 differs from PC in this prefix: no tag word 100, the first word 26579 sits where the tag is; each non-root node has one extra byte after its selector; later planes are general (not axis-aligned) and their last word is a non-`-1` code (for example `0x17BE`) | BYTES; the exact grammar is not yet reproduced (parse fails at 0x1D0) |
| ELF strings tied to this data: `.bsp` (VA 0x4879b8), `$bsp`, `BSP/PlaneThickness`, `BSP/SubTreeScale`, `BSP/StoreDrawPolys`, `BSP/StoreNoDrawPolys`, `BSP/StoreAllPolys`, `BSP/Vert`, `BSP/DrawVert`, `BSP/NoDrawVert`, `BSPNonLeafNode::PushEdge`, `physMemPool<BSPEdge>`, `physMemPool<BSPPoly>` | STRING (`SLES_509.06`, file offset = VA - 0xff000) |
| Convex versus BSP narrowphase is dispatched via `2e3270 -> 2470f8` | `rigid1/terrain-contact.md` |

## Inferences, not proved
- The PS2 `.BSP` is the serialized form of the same BSP class family that PC compiles into tag100 (`$bsp -> tag100`).
- The non-`-1` plane codes and the larger size (most of 3.4 MB is not partition planes) suggest the PS2 file carries collision polygons,
  edges and surface data in addition to the partition tree, matching the `BSP/StoreDrawPolys` strings. Not verified.
- PS2 and PC trees are different compilations of one source: node counts are 49,841 against 235,089.

## Consequence for G-COLL
Comparing the two datasets needs a loader-faithful PS2 reader first. That means locating the `.bsp` reader from the string at 0x4879b8
and the `BSP/*` option strings, then reproducing its grammar (the work is bounded: the PC grammar is already known, the delta is a
handful of fields). After that, G-COLL follows the revised policy: geometric queries on both datasets, then a runtime check.

## Reproduce
    python -X utf8 ps2-research/track-delta1/bsp_probe.py ps2-research/data/track-bsp/TURKEY3.BSP

(the extracted file goes to the ignored `ps2-research/data/track-bsp/`; extraction code is in this note's session log: `tngtool.load_pak` and `read_payload`).
