# Phase R0.5 findings

## Scope and method

R0.5 reused the R0 inventory, relationship graph, sidecar parser, DX probe, and
DXT decoder. The original extracted archive was read only. No executable was
opened, and no Ghidra work was performed.

The primary sample was `DataGx/Vehicles/Astero/wheel.dx`. Validation used
Astero `complete.dx`, Bruno `wheel.dx`, and the structurally different Astero
`car.dx`. Generated OBJ/MTL/PNG files live only below ignored
`.research-output/r0_5/` and are not repository artifacts.

## Tooling corrections

- The inventory scanner now traverses only `DataGame`, `DataGx`, and
  `DataScene`; arbitrary root siblings are excluded.
- Regenerated corpus: **7,595 files, 806,260,689 bytes, 148 TXT files**. The
  removed false entry was the 279,160-byte external
  `master_rallye_data_sma_tree.txt` helper.
- DX parsing validates every header/vertex/UV/index/trailer extent before
  unpacking and reports `DxParseError` with the affected section.
- Tools accept an explicit root and no longer search path strings for a
  literal `Data.sma_unpacked` component.
- Python caches and temporary proof output are ignored.

## Astero wheel byte map

The local `uint16` index buffer ends at `0x24F0`. The trailer is:

| File range | Structure | Evidence status |
|---|---|---|
| `0x24F0..0x24F7` | `uint32 1`, `uint32 5` table envelope | values **CONFIRMED**; first word meaning **UNKNOWN**; count meaning **HIGH** |
| `0x24F8..0x26B2` | five variable tag-2 records | boundaries **CONFIRMED** for sample |
| `0x26B3..0x26BA` | `uint32 1`, `uint32 756` | values **CONFIRMED**; first word meaning **UNKNOWN** |
| `0x26BB..0x328A` | 756 global `uint32` indices | **HIGH** |
| `0x328B..0x32C2` | 56-byte footer | bounds fields **HIGH**; other fields unresolved |

The detailed raw core bytes, length-string offsets, and interpretations are in
`draw-record-proof.json`; the compact schema is in `docs/formats/dx.md`.

## Addressing proof

For every triangle in each draw:

```text
stored_global = (local[1] + vertex_base,
                 local[0] + vertex_base,
                 local[2] + vertex_base)
```

The first two corners are swapped, so the second table is not a byte-width-only
copy. The equation exactly reproduces 14,844 stored indices across all four
validated resources. In every file, draw index ranges completely partition the
local buffer and computed vertices remain inside the declared local range and
the file-wide vertex array.

For Astero wheel specifically, five draws cover all 756 indices, all 220
vertices, and all 252 triangles. Draw triangle counts are `72, 36, 54, 18, 72`.
The first three sum to the sidecar wheel span 162; the last two sum to hub span
90. There are no fabricated triangles.

## Material correlation

The binary records embed three ordered strings each. Full-tuple matching gives
one sidecar material candidate for every Astero wheel draw:

| Binary draw | Texture tuple | TXT material |
|---:|---|---|
| 0 | `asterowheel64-tga`, `rubber-tga`, `Null` | 0 `AsteroWheel64` |
| 1 | `tread-tga`, `rubber-tga`, `Null` | 2 `AsteroTread` |
| 2 | `wheel643-tga`, `rubber-tga`, `Null` | 1 `AsteroWheel643` |
| 3 | `asterowheel64-tga`, `chrome-tga`, `Null` | 4 `AsteroWheel64b` |
| 4 | `asterowheelrim-tga`, `chrome-tga`, `Null` | 3 `AsteroRim` |

The non-monotonic `0,2,1,4,3` mapping disproves implicit sidecar order. No
direct material-index field has been observed. All slots remain in diagnostic
JSON; OBJ/MTL uses only the first non-`Null` slot as an explicitly limited
proof diffuse texture.

## Record variants and the car discrepancy

Astero car's declared 27 top-level records expand to 32 physical draws. Four
type-7 named groups contain five child records. Their labels and triangle spans
match the sidecar screens and brake-light nodes. This sample could not
distinguish control words 3 and 4 because their values happened to agree. R1
corpus evidence supersedes the original word-3 inference: the fifth control
word (index 4) is the supported direct-child count. Type-8 remains one observed
child form.

The former 2,089-vs-2,021 triangle discrepancy is explained without altering
either count. The sidecar contains `$chull(Astero)` at triangle 1937 with size
68. It is absent from `car.dx`; binary `screenfront` begins at triangle 1937,
whereas the sidecar begins it at 2005. Subtracting exactly 68 aligns all later
screen and brake-light spans. The evidence supports omission from this render
resource, not a claim about how the engine uses the hull elsewhere.

## Visual proof

The experimental exporter wrote 220 positions, 220 UVs/normals, 252 faces, five
material groups, an MTL, and four required primary PNG textures. A small
software render viewed the wheel predominantly along its axle.

Observed result: a single coherent circular wheel/tire with a centered hub;
no exploded triangles, cross-range spikes, detached hub, or missing triangle
bands. Material regions are spatially sensible. Direct-V and flipped-V renders
both remain plausible for these largely rotational wheel textures, so vertical
origin remains **UNRESOLVED**. The proof uses direct V by default and exposes
`--flip-v` for comparison.

## Validation matrix

| File | Vertices | Triangles | Top-level records | Physical draws | Address equation | Full index/vertex partition |
|---|---:|---:|---:|---:|---|---|
| Astero `wheel.dx` | 220 | 252 | 5 | 5 | exact | yes |
| Astero `complete.dx` | 2,657 | 2,423 | 24 | 24 | exact | yes |
| Bruno `wheel.dx` | 220 | 252 | 5 | 5 | exact | yes |
| Astero `car.dx` | 2,543 | 2,021 | 27 | 32 | exact | yes |

## Synthetic verification

Eight tests cover BGRA PNG channels, one and multiple local-index groups,
material/record correlation, truncated header/vertex/UV/index sections,
unreasonable counts, and exclusion of files outside the three archive roots.
They contain no reconstructed game bytes.

## Checkpoint

### CONFIRMED

- Corrected 7,595-file archive scope and 148 TXT count.
- Five reproducibly bounded Astero wheel records and complete 252-triangle
  accounting.
- Stored global indices are an exact winding-swapped expansion of local
  indices plus per-draw base in the four validation files.
- No executable analysis occurred.

### HIGH-CONFIDENCE

- Simple draw core meanings for base, inclusive local max, index start/count,
  and texture-slot list.
- Texture-tuple-to-sidecar-material mapping for the five wheel draws.
- Type-7 group boundaries in Astero car; R1 corpus evidence later refined the child-count field.
- `$chull(Astero)` is the exact 68-triangle source span omitted from car render
  geometry.

### STILL UNRESOLVED

- Header constants; draw flags/control words; type-7/type-8 control semantics;
  multi-texture runtime blending; UV vertical origin; car data after its global
  index table; course variants.

### NEXT BEST EXPERIMENT

R1 should turn the proven vehicle parser into a clean reusable library and add
an interchange exporter that preserves every draw and texture slot as metadata.
It should test more vehicle variants and formalize optional trailing sections
before any Blender integration. Executable-assisted work is not required for
the solved draw mapping; it should be reserved for the remaining runtime
material semantics only if asset-only evidence stalls.
