# PS2-UI1 validation

| Check | Result / precise scope |
| --- | --- |
| Canonical inputs | All four size/SHA256 values rechecked; originals unchanged |
| PackFS baseline | 26 tests PASS with canonical corpus; directory SHA/counts/range constraints preserved |
| PSB/GXI/UI tests | 25 tests PASS, including optional canonical NUMS/TEMPLATE tests enabled |
| Combined discovery | 51 tests PASS, zero skips/failures |
| PSB canonical parsing | 10 banks, 120 images, 444 triangles; every decoded byte consumed |
| Exact references | 79 stems → 79 manifest files; no invented resource names |
| Texture verification | 418 textured triangles checked against actual GXI dimensions and cell/UV bounds |
| Null preservation | 26 Null records, 52 exact uninterpreted-field ranges; NaN/Inf bits retained |
| GXI | 87 targeted files satisfy exact magic/dimension/size gate; RGBA visual evidence from multiple HUD textures |
| Authored XML audit | 45 text XML resources: 40 PS2 frontend, five HUD including disabled copy; zero MAP128STRIPED references |
| Offline visuals | Primary four banks plus NEWHUD reconstructed and viewed; no screenshot-authored positions |
| Screenshot correlation | Six user JPEGs inspected, two full race HUDs; exact runtime build UNKNOWN |
| Metadata reproducibility | Seven generated JSON reports byte-identical on independent rebuild |
| CLI | info/dump/strings/sprites/glyphs/verify JSON checked on canonical primary inputs |
| Python compile | `python -m compileall -q ps2-research` PASS |
| Git whitespace | `git diff --check` / staged diff check PASS |
| Proprietary hygiene | Payloads, decoded XML, screenshots/derivatives, PNGs and raw ELF exports ignored; committed files source/docs/metadata only |

Tests cover minimal valid PSB, truncated headers/records, invalid version/magic,
impossible counts, absent image indices, invalid resource names/lengths,
rectangle/UV bounds, missing exact references, unsupported GXI, wrong payload
sizes, zero dimensions, unaligned strings and unknown trailing-byte preservation.
A Null NaN payload is checked bit-for-bit and serialized without nonstandard
JSON NaN. Geometry tests reject overlapping or rotated unsupported quad
interpretations. A two-color raster fixture verifies the V-to-row convention.

Canonical tests lock NUMS `(keys=10,images=4,triangles=32)` and TEMPLATE
`(11,11,34)`, their decoded hashes, aliases, exact atlas references and texture
bounds. They do not duplicate the parser's implementation as a gameplay oracle.

Reproduce from repository root:

```powershell
python ps2-research/tools/build_ui_report.py --inputs 'D:\Game\Master Rallye PS2' --screens 'D:\Game\Master Rallye PS2\PS2-userscreens'
$env:MASTER_RALLYE_PS2_INPUT='D:\Game\Master Rallye PS2'
$env:PS2_UI_CORPUS='D:\Game\Master Rallye\master-rallye-re-general\ps2-research\data\ui1\extracted\TNG\DATAPSM\HUD'
python -m unittest discover -s ps2-research/tests -v
python -m compileall -q ps2-research
git diff --check
```

For a diagnostic bank sheet:

```powershell
python ps2-research/tools/ui_visuals.py ps2-research/data/ui1/extracted/TNG/DATAPSM/HUD/NEWHUD.PSB --texture-dir ps2-research/data/ui1/extracted/TNG/DATAPSM/HUD --output-dir ps2-research/data/ui1/visuals/NEWHUD
```

Local ignored evidence resides in `data/ui1/`: targeted extractions plus their
provenance, Ghidra exports/query logs, `tests.log`, atlas/bonus/screenshot contact
sheets, and per-bank `visuals/*/contact.png` / individual images. Full raw
decompilation is not a source deliverable. Current offline environment has
Pillow 12.2.0 and Ghidra 12.1.4. The parser has no Pillow/Ghidra dependency.

RGBA byte samples: NEWHUD_000 pixel (39,8) is `[2,198,0,253]` on the green
radar grid; NEWHUD_003 pixel (38,29) is `[182,13,13,255]` on the red rev band.
Alpha isolates dial/grass/bush cutouts. All ten large NEWHUD glyphs reconstruct
upright using the same channel and scanline interpretation. Grade:
`CONFIRMED_BY_VISUAL_RECONSTRUCTION`; no GS upload/swizzle behavior is claimed.

This validates the asset reader and bounded content model. Live loading,
input/gameplay, dynamic course-map transforms, precise tint/blending/draw order,
and the entire GXI corpus remain untested. The historical screenshots do not
change those boundaries.
