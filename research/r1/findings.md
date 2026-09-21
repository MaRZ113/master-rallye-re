# Phase R1 findings

## Scope and method

R1 promoted the evidence-backed R0.5 vehicle logic into the reusable
`src/master_rallye` package and a small `tools/mrtool.py` CLI. Original archive
resources were opened read-only. Scanner scope was exactly `DataGx/Vehicles`;
Course, DXB, SFL, HNT, and executable analysis were excluded.

The scanner stores archive-relative metadata only. Derived glTF/BIN/PNG/OBJ and
preview renders were generated beneath ignored `.research-output/r1/` and are
not repository artifacts.

## Vehicle corpus result

| Metric | Result |
|---|---:|
| Vehicle DX resources | 78 |
| Parsed | 78 |
| Validated | 78 |
| Exact stored-global matches | 78 |
| Fully accounted | 49 |
| Partially accounted | 29 |
| Failed | 0 |
| Vertices examined | 142,447 |
| Triangles examined | 119,977 |
| Stored/reconstructed indices compared | 359,931 |
| Physical draws | 1,478 |
| Unknown draw tags | 0 |

`VALIDATED` requires internally safe draws and exact reconstructed/stored global
indices. `FULLY_ACCOUNTED` additionally requires no opaque trailing section.
Thus the 29 partial resources are not geometry failures: their known draw data
matches exactly while later bytes remain intentionally uninterpreted.

All corpus files happen to have complete/disjoint local-index coverage and
complete/disjoint declared vertex ranges. R1 keeps both as diagnostics rather
than grammar requirements. Synthetic inputs with unused or shared vertex ranges
remain valid when their actual references are in bounds.

## Record grammar refinement

Tags 2, 7, and 8 occur in 78, 25, and 25 files respectively. No new tag was
found. Physical records must be scanned sequentially to the global index
envelope and then grouped. Corpus cases where type-7 control words differ prove
that control word 4 (the fifth word) is the direct-child count; R0.5 could not
distinguish words 3 and 4 because their sample values agreed.

Eleven car files declare a root-related count one below the reconstructed root
count: ChevyBlazer, IceCream, Kamaz, KiaSportage, Navara, Pajero, Patrol,
RMonster, SeatBuggy, Tata, and Xtrail. Each still has complete draw coverage and
an exact global-table match. The field is preserved as
`declared_top_level_record_count`, but its universal semantics are only
**MEDIUM**.

The exact index equation remains:

```text
stored_global_triangle = (local[1] + vertex_base,
                          local[0] + vertex_base,
                          local[2] + vertex_base)
```

It reproduces all 359,931 corpus indices. Reconstructed face normals align with
averaged stored vertex normals for 119,454 triangles, oppose for 98, and are
near zero for 425. This independent corpus signal supports exporting the stored
global winding at **HIGH** confidence. The corrected R0.5 four-sample subtotal is 14,844 indices.

## Trailing-layout classification

| Resource type | Recognized 56-byte bounds | Opaque |
|---|---:|---:|
| `car` | 0 | 26 |
| `complete` | 24 | 2 |
| `wheel` | 25 | 0 |
| `sus` | 0 | 1 |

All 49 recognized footers contain midpoint/minimum/maximum values matching the
parsed positions. Their other four scalar fields retain neutral unknown names.
Opaque sizes range from 44 to 6,600 bytes and are preserved byte-for-byte in the
model plus SHA-256 in the report. Larger tails strongly cluster in `car`, but
are not required for extraction and were not guessed.

## Sidecar and material correlation

TXT remains optional supporting metadata. Matching is by normalized ordered
texture tuple; missing sidecar slots are padded with `Null` to the binary tuple
width. The results are:

- 72 resources have sidecars; six do not;
- 132 draws have multiple equally supported material names;
- 63 draws are unmatched, 58 of them from missing-sidecar resources;
- the five remaining unmatched draws occur one each in IceCream car/complete,
  KiaSportage car/complete, and Pajero complete;
- no referenced non-`Null` DXT resource is missing.

The exporter never invents a material index. It stores every candidate and
ordered binary slot while using only the first non-`Null` texture for a
provisional preview material.

## glTF proof and visual validation

Astero `complete.dx` exported with 2,657 positions/normals/UVs/colors, 2,423
triangles, 24 draw primitives, 24 material objects, and 20 cached primary PNGs.
Accessor bounds, buffer ranges, primitive index totals (7,269), and metadata
counts validate. A software preview showed a coherent complete car: no exploded
triangles, cross-draw spikes, detached assemblies, reversed placement, missing
groups, or duplicate exporter geometry.

The original orientation experiment conflated stored DXT raster rows with UV
coordinates. Pre-push correction established two independent transforms.
`parse_dxt_bytes()` preserves the raw BGRA plane, while PNG presentation now
explicitly reverses stored row order. Four asymmetric Astero textures were
checked: `mastersticker263-tga`, `asteropanels128-tga`,
`asteroleftdoor1-tga`, and `asterorightdoor1-tga`. Stored-order PNGs are
vertically inverted; row-flipped PNGs make text, number, and door details
visually upright.

Astero complete was then regenerated with these corrected PNGs in direct-V and
`V' = 1 - V` modes. Only `1 - V` put `MASTER` above readable `263`, retained
upper-door handles/details, and kept directional body art coherent. Thus the
glTF UV policy remains V-flip at **HIGH** confidence, but now from a valid
raster-corrected comparison. Both modes remain available, and metadata records
both the PNG row policy and selected UV mode.

The same exporter, with no per-file offsets, successfully handled:

| Sample | Vertices | Triangles | Primitives | Primary PNGs |
|---|---:|---:|---:|---:|
| Astero complete | 2,657 | 2,423 | 24 | 20 |
| Astero car | 2,543 | 2,021 | 32 | 25 |
| Astero wheel | 220 | 252 | 5 | 4 |
| Bruno car | 2,455 | 2,014 | 21 | 19 |
| Bruno wheel | 220 | 252 | 5 | 4 |
| ChevyBlazer car | 2,713 | 2,156 | 36 | 28 |
| Ufo complete | 837 | 670 | 6 | 4 |
| megane sus | 48 | 48 | 1 | 1 |

These include simple/grouped records, both trailing families, a declared/root
count mismatch, two additional vehicle families, an unusual `sus` resource,
and the 44-byte Ufo complete tail.

## Implementation and verification

- `dx.py`: bounds-checked parser, hierarchy, addressing, stored-table checks,
  neutral trailing preservation, and non-fatal coverage diagnostics.
- `dxt.py`: raw BGRA preservation plus explicit `preserve-stored` / `flip-vertical` PNG row policies.
- `sidecar.py` and `materials.py`: independent metadata parsing and ambiguity.
- `assets.py`: case-insensitive local texture resolution.
- `export/gltf.py`: glTF 2.0 with one primitive per draw, complete MR metadata,
  cached textures, and neutral fallback materials.
- `export/obj.py`: diagnostic fallback.
- `coverage.py`: full vehicle scanner and structured reports.
- 22 synthetic behavioral tests pass; asymmetric fixtures independently cover BGRA channels, stored rows, PNG presentation rows, and UV transforms; no game bytes are fixtures.

## Remaining unknowns

Opaque trailing sections, draw control/flag meanings, exact semantics of the
root-related declared count, runtime multi-texture blending, and some sidecar
name ambiguities remain unresolved. They do not block stable vehicle geometry
and provisional textured extraction. No executable-assisted experiment is
needed for the R1 objectives.

## Decision gate

**Recommended next phase: R2A — Blender integration.** Vehicle geometry
coverage is 78/78 with exact index validation, all observed record variants are
supported, and glTF exports coherently across diverse families. Blender work
should consume the stable library/data model, preserve draw/group and texture
metadata, expose the evidenced V-flip, and keep runtime multi-texture semantics
explicitly provisional. R2C may follow later if accurate in-engine material
blending becomes the main requirement.
