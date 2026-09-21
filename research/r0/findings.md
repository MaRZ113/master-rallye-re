# Phase R0 findings

## Method

1. Built one archive-wide index containing relative path, extension, size, first
   64 bytes, signature class, stem neighbors, resource family, SHA-256, and
   extension/directory/pattern/signature/size aggregates.
2. Parsed all 122 XML files before interpreting binary formats.
3. Parsed every vehicle TXT sidecar into materials, texture slots, mesh names,
   hierarchy order, and mesh spans.
4. Used Astero as the main lab sample, Bruno as the normal control, and Ufo as
   the unusual control.
5. Tested binary hypotheses by computed boundaries and differential samples;
   no executable was opened or decompiled.

## Inventory highlights

- 7,596 files / 806,539,849 bytes.
- 6,960 DXT, 160 DX, 149 TXT, 122 XML, 113 DXB, 54 HNT, 36 SFL, 2 XML#.
- 190 same-stem cross-extension groups: 136 DX+TXT, 52 HNT+XML, and 2
  HNT+XML+XML#.
- 607 SHA-256 duplicate groups. Repeated course textures dominate the largest
  groups (up to 48 identical copies), demonstrating extensive asset reuse.
- 5,175 filenames use the exporter-style `*-tga.dxt` pattern.
- One zero-byte TXT file exists; it is retained in the inventory rather than
  silently ignored.

## Human-readable pipeline map

`vehicles.xml` supplies vehicle physics/config broker values. Astero has 147
entries there and 26 modification entries. `RaceTest/smash.xml` directly selects
`Car Name = Astero`. The same identifier matches `DataGx/Vehicles/Astero`.

Astero TXT sidecars describe 28 materials in car/complete and five in wheel,
then a nested named mesh hierarchy. Across those sidecars, 33 unique TGA names
resolve losslessly to 33 `*-tga.dxt` files. No referenced Astero texture is
missing.

The TXT `Index/Size` spans correlate with decoded binary triangles for
`complete.dx` and `wheel.dx`, but `car.dx` has fewer binary triangles than its
full TXT span. This is an explicit warning that TXT spans may include exporter
nodes or geometry not present in a specific compiled variant.

## Binary findings

### DX

All 160 DX files share the 12-byte prefix
`0D D0 00 00 87 00 00 00 39 05 00 00`. The next word drives exact boundaries
for position, normal, color, UV, and index sections in all five prototype
samples. Normals average length 1.0 and indices fit their declared buffers.

The region after indices contains variable draw/material records and
length-prefixed texture stems. Mesh/object names observed in TXT were not found
in the Astero DX binaries. Raw indices appear local to draw groups; faces are
therefore intentionally not exported yet.

### DXT

All 6,960 DXT files are a custom 20-byte header plus exactly `W*H*4` bytes.
There is no DDS header, block-compressed DXT payload, or stored mip tail.
Targeted alpha measurements agree with TXT alpha flags. Brake-light channel
statistics strongly support BGRA ordering.

### HNT, SFL, DXB

HNT is a text dependency manifest. SFL is structurally a 20-byte header plus an
8-bit `W*H` plane, but its meaning is unknown. DXB has a stable prefix and
font/sprite-like evidence, but its records remain unmapped.

## Prototype result

`dx_mesh_probe.py` successfully parses the confirmed leading DX sections and
writes diagnostic JSON. `dxt_decode.py` validates and decodes the observed
uncompressed texture wrapper into PNG with an explicit channel-order option.
Two synthetic-only unit tests pass. No original or decoded game asset is stored
in Git.

## Checkpoint

### CONFIRMED

- The inventory, counts, hashes, magic prefixes, same-stem relationships, and
  26 vehicle profiles are reproducible.
- All 122 XML files parse; Astero's config/scene identifier and all 33 sidecar
  texture references map to existing assets.
- `.dxt` uses magic `0xFEED`, a 20-byte header, explicit dimensions, one
  uncompressed 4-byte-per-pixel plane, and no stored mip tail.
- `.hnt` is a textual resource dependency manifest.
- `.sfl` file length is `20 + width*height` for all 36 samples.
- No executable analysis occurred.

### HIGH-CONFIDENCE

- `.dx` is compiled 3D model data with positions, normals, vertex colors, UVs,
  a local/grouped 16-bit triangle index buffer, and trailing draw/material
  records.
- DXT pixels are BGRA, with the fourth byte acting as alpha.
- TXT sidecars preserve hierarchy/object/material/export metadata omitted or
  reorganized in compiled DX.
- `Astero` is representative of the common vehicle layout; `Bruno` validates
  it and `Ufo` exercises the missing-wheel variant.

### UNRESOLVED

- Exact DX draw-record schema, vertex-base application, material flags, and
  mapping from each TXT mesh node to compiled draw ranges.
- DX header constants `135` and `1337`.
- DXT word at `0x08`, vertical origin, and color-space convention.
- DXB record layout and SFL raster semantics.
- Runtime lookup/alias behavior for configuration-only vehicle identifiers.

### NEXT BEST EXPERIMENT

Map one full Astero `wheel.dx` draw-record table. It has only five materials and
252 triangles, yet contains all needed ingredients: local index ranges, vertex
ranges, three texture slots, and exact TXT material order. Validate each
candidate base/range equation across all five records, then emit a temporary
(non-repository) OBJ/PNG preview for visual checking. Only if those equations
hold for Astero car/complete and Bruno should R1 begin. Executable inspection is
still unnecessary for this next experiment.
