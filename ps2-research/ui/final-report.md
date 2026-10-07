# PS2-UI1 closeout report

**PS2-UI1 STATUS: COMPLETE** for the requested first content reverse. This is
a verified offline asset/format result with historical screenshot correlation;
it is not a new PS2 runtime or PC HUD implementation.

| Repository field | Value |
| --- | --- |
| Worktree | `D:\Game\Master Rallye\master-rallye-re-general` |
| Branch | `master` |
| Starting HEAD | `940d4edf39392118b796d832160528fbe75702ec` |
| PackFS foundation / UI analysis base | `1d47e84bd3587e9dd56c393830a690ad3ef40368` |
| Foundation commit | `research: reconstruct PS2 TNG filesystem` |
| UI commit | `research: reverse PS2 HUD resources`; resulting hash is reported in chat and Git log |
| Branch/worktree changes | None; existing master worktree reused |
| Historical research | research/general-re, research/r-* and their directories untouched |
| Push | None |

PackFS baseline: **26 tests PASS**, no parser/codec behavior changes and no
regressions. Golden directory remains 269668 bytes, SHA256
`391929a42dac29eaa6a4306d9e178ad7da925a5426de0befd5550524cc6a56c4`, with 3736
nodes, 137 directories and 3599 files. All four canonical inputs retain their
exact hashes, including complete TNG.000. Original assets/ELF were only read.

PSB format: little-endian signature **F001**, version **125**, mapping-count
and key/index pairs, image count, per-image triangle count, then packed records.
Each record contains 6 float UV components, 6 signed local XY components,
4 signed allocated-cell bounds, u32 name length and exact ASCII bytes without
NUL/alignment. Texture names resolve within the PSB's logical directory plus
`.GXI`. In-memory records are 0x48 bytes, different from disk. Adjacent triangle
pairs are accepted as quads only with rectangular geometry/UV and a shared
diagonal. Unknowns are preserved: Null UV/cell bits, unexpected trailing bytes;
verification rejects unrecognized tails/signatures/versions. No color/alpha,
draw-order, named pivot, screen-anchor or font advance field was established.

HUD-NUMS: **2656 decoded bytes**, **3 textures**, **10 character keys / 4 unique
drawn glyphs**, **32 triangles**. Keys `'0'..'9'` map to image indices
`[0,0,1,2,3,3,3,3,3,3]`. Offline images are digits **1,2,3,4**, with local
height 48 and geometry widths **34,46,45,48**. Baseline, advance and bearing
remain UNKNOWN. Key/geometry confidence is CONFIRMED_BY_BOTH; drawn glyph
identity is CONFIRMED_BY_VISUAL_RECONSTRUCTION. NEWHUD separately contains
the full 0–9 large-digit set plus small digits; its map is retained explicitly.

HUD-TEMPLATE: **3004 decoded bytes**, exact references **hud-template_000..007**,
**11 images / 34 triangles / 17 quads**. Identified content includes the dial,
radar background, needle, race-progress car/split/finish markers, GPS direction
pointer and progress-outline pieces. Authored HUD0 model indices directly
support dial/needle/car/split/finish/bar relationships. Precise role of image
4's green vertical marker, dynamic stretching, tint/order, runtime anchors and
final viewport conversion remain UNKNOWN. PSB-local coordinates and authored
XML matrices are stored separately; 640×480 bottom-origin entity placement is
a static/screenshot inference, not a proven runtime transform rule.

MASTER_TEMPLATE: **4714 decoded bytes**, **10 images / 54 triangles / 10 textures**;
dial, radar, pointers, markers and a complete oval strip reconstruct correctly.
PACENOTES: **4192 decoded bytes**, **24 images / 48 triangles / 24 textures**;
identity image keys, reversed texture-stem order, all diagrams reconstructed.
Gameplay pace-note enum/trigger meanings remain UNKNOWN.

MAP / MINIMAP:

- MAP128STRIPED found: **YES**.
- Exact path: `\TNG\DATAPSM\COMMONTEXTURES\MAP128STRIPED1-TGA.GXI`.
- Dimensions/alpha: **128×128 / 255 everywhere**; striped world-map picture.
- Referenced by: **none in ten parsed PSBs or 45 audited XML resources**;
  global/constructed references are unresolved.
- Dynamic course-map path known: **NO**. gaHudAiMap is the bounded owner lead.
  Screenshot course-route overlay is different from this fixed texture.

GXI: **87** targeted files match magic **0x00013039**, u16 width/height and exact
`8 + width*height*4` size. Byte order **RGBA** is corroborated by distinct red/
green HUD pixels, alpha silhouettes and whole glyphs. Raw row 0 corresponds to
PSB V=1; UV crop uses `(1-vmax)..(1-vmin)`. Grade is visual reconstruction,
not a GS upload/swizzle proof. Unsupported magic, zero dimensions and wrong
payload sizes fail closed; the rest of the 3177-file GXI corpus is not certified.

Offline visual validation: **performed / PASS**. NUMS, TEMPLATE,
MASTER_TEMPLATE, PACENOTES and NEWHUD contact sheets/individual images were
generated from bytes and viewed. All 0–9 NEWHUD large digits are whole and
upright. Six historical user JPEGs were inspected; two racing HUDs corroborate
dial, rank, damage and progress families. No sprites were manually positioned
to imitate a screenshot. Active scene, exact executable build/frame and live
HUD behavior remain unverified.

Bonus targets: all **seven present**; prefix is `\TNG\DATAPSM\`:

| Target / exact tail | Dimensions | Alpha min–max (distinct) |
| --- | --- | --- |
| GRASS1 / PARTICLES\GRASS1.GXI | 32×32 | 0–255 (223) |
| BUSH1 / PARTICLES\BUSH1.GXI | 32×32 | 0–255 (213) |
| WATERSURFACE2 / COMMONTEXTURES\WATERSURFACE2.GXI | 64×64 | 4–131 (128) |
| ENVSOURCE64X64 / COMMONTEXTURES\ENVSOURCE64X64.GXI | 64×64 | 0–255 (2) |
| RENDERTARGET64X64 / COMMONTEXTURES\RENDERTARGET64X64.GXI | 64×64 | 0–255 (2) |
| STATICRENDERTARGET64X64 / COMMONTEXTURES\STATICRENDERTARGET64X64.GXI | 64×64 | 110–110 (1) |
| WINDSCREEN-REFLECT / COMMONTEXTURES\WINDSCREEN-REFLECT.GXI | 32×32 | 255–255 (1) |

ELF UI: PSB bank loader **0x00386D28**, mapping reader **0x00387188**, image
reader **0x00387258**, triangle reader **0x00387478**. Structural confidence:
CONFIRMED_BY_BOTH. HUD-owner families include gaHudAiSpeedDial/Needle,
gaHudAiMap, rank/newhud, pace notes and gaHudLoader candidates. Scalar
configuration and image-size helpers were inspected through ghidra-bridge;
dynamic map geometry/whole renderer was not decompiled. See `elf-ui-map.md`
for exact addresses, rejected clues and analysis limitations.

Tests: **PackFS 26 PASS; PSB/GXI/UI 25 PASS; combined 51 PASS with no skips**.
Compileall and Git diff/whitespace checks PASS. Seven generated JSON reports
are byte-identical after rebuild. Six CLI modes return deterministic JSON with
input hashes. Canonical primary hashes/counts/texture references are locked.

Created source: `tools/psbtool.py`, `tools/ui_visuals.py`,
`tools/build_ui_report.py`, `tools/elf_ui_query.py`, `tests/test_psbtool.py`.
Modified source index: `ps2-research/README.md`. Created documentation:
`ui/findings.md`, `ui/psb-format.md`, `ui/elf-ui-map.md`,
`ui/hud-resource-map.md`, `ui/ps2-hud-layout.md`, `ui/validation.md`,
`ui/next.md`, this report. Created metadata: `ui/psb-manifest.json`,
`ui/hud-elements.json`, `ui/texture-metadata.json`,
`ui/resource-inventory.json`, `ui/input-provenance.json`,
`ui/extraction-provenance.json`, `ui/screenshot-correlation.json`.

Working-tree closeout: only the listed PS2 source/docs/metadata are included
in the UI commit. Proprietary extracted assets, decoded XML, screenshots and
derivatives, PNGs, Ghidra projects/raw exports remain ignored locally. No
unrelated tracked work is included. Unrelated ZIP archives appeared/changed at
repository root during parallel work; none was touched or staged. The PS2
tracked changes are clean after their commit; untracked archives remain outside
the commit, and their final observed inventory is reported separately in chat.

Recommended next phase: **PS2-UI2 dynamic HUD ownership / minimap**. It has the
strongest evidence-backed gap: useful fixed assets are reconstructed, while
runtime bank selection, course-map geometry and entity/viewport transforms are
still unresolved. No next phase, PC HUD, freecam, grass, water or reflections
implementation was started.
