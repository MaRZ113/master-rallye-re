# Blender vehicle importer (Phase R2)

The R2 add-on imports proven Master Rallye **vehicle** DX resources directly
into an editable Blender mesh. It does not write DX/DXT files and it does not
support Course DX resources.

## Compatibility

- Tested: **Blender 5.2.2 LTS** (`d13f752e3b9c`).
- Expected API baseline: Blender **4.3 or newer**.
- Older versions were not tested and are not claimed as supported.

## Build and install

Build the ignored distribution artifact from the repository root:

```powershell
py -3 tools/build_blender_addon.py
```

This creates `dist/master_rallye_io-r2.zip`. The build copies the canonical
`src/master_rallye` package into the add-on's private `vendor` namespace;
there is no second editable parser copy in the repository.

In Blender, open **Edit > Preferences > Add-ons**, choose **Install from
Disk**, select the ZIP, and enable **Import-Export: Master Rallye Vehicle IO**.
Generated ZIP files are local artifacts and are ignored by Git.

## Import workflows

**File > Import > Master Rallye DX (.dx)** imports one vehicle resource. The
operator can load an adjacent TXT sidecar and resolve sibling DXT textures.
Strict validation is enabled by default.

**File > Import > Master Rallye Vehicle Folder** discovers every `*.dx` file
directly inside the selected vehicle folder. It creates a parent collection
named `Master Rallye - <folder>` and one child collection per actual resource
stem. Resource names are preserved; the operator does not assume only
`car`, `complete`, or `wheel`.

Both modes leave original game files read-only. Preview PNGs are decoded into
the operating-system temporary cache and reused during the import.

## Authoring representation

Each DX resource becomes one ordinary editable Blender mesh object. It retains
all source vertices and reconstructed source triangles. Physical draw records
remain face membership rather than separate objects.

| Domain | Attribute | Purpose |
|---|---|---|
| Point | `mr_source_vertex` | Original zero-based DX vertex identity |
| Point | `mr_source_vertex_valid` | Provenance marker for future checks |
| Point | `mr_source_normal` | Original DX-space values where finite |
| Point | `mr_source_normal_valid` | Validity marker for the vector attribute |
| Point | `mr_source_normal_bits_x/y/z` | Exact source float32 component bits |
| Face | `mr_draw_id` | Physical draw membership |
| Face | `mr_source_triangle` | Original reconstructed triangle identity |
| Face | `mr_group_id` | Top-level structural draw group |
| Point | `mr_color_byte_0..3` | Exact original color-like bytes |

All UV sets are imported as `MR UV 0`, `MR UV 1`, and so on. A
`MR Vertex Color` preview attribute is also created. Original normals are
preserved independently from Blender display shading. The
float-vector attribute is convenient for inspection, while the three integer
bit attributes retain exact source float32 provenance, including non-finite
values.

The object carries small scalar properties for common inspection plus a
structured `mr_metadata_json` property. The JSON preserves draw order,
record paths/tags/offsets, group membership, texture slots, material
candidates, neutral unknown fields, validation results, trailing-layout
classification/hash, and coordinate/texture policies. It deliberately does
not embed the source binary or opaque trailing bytes.

Tag-7/tag-8 groups are structural metadata only. They are not converted into a
fake Blender transform hierarchy.

## Coordinates and UVs

R1 glTF keeps source XYZ at native scale. Blender uses +Z as up, so the shared
conversion module maps:

```text
source/glTF (X, Y, Z) -> Blender (X, -Z, Y)
```

This is a +90 degree X-axis rotation with determinant +1. Handedness and the
validated stored-global triangle order are retained. Positions and normals use
the same rotation. Scale is exactly 1.0; the physical meaning of a Master
Rallye world unit remains **UNKNOWN**.

Texture raster and UV transforms stay independent:

- DXT parsing preserves stored BGRA rows;
- preview PNG encoding applies the explicit `flip-vertical` row policy;
- the accepted glTF preview independently applies `V' = 1 - V`;
- Blender imports the source V value directly.

A Blender 5.2.2 A/B comparison used upright PNGs and directional Astero/Pajero
door numbers and sponsor text. Direct V was upright; `1 - V` was inverted.
The glTF policy is unchanged. Keeping these named policies independent prevents
a raster flip from being accidentally cancelled by the wrong consumer UV
transform.

## Normal safety and provenance

Every import records normal count, non-finite and near-zero counts, and minimum
and maximum magnitude. A normalized display candidate is validated in Python
and expanded per corner for diagnostics, without modifying the stored source
values.

Blender 5.2.2 native-crashed in real multi-resource sessions through both
`normals_split_custom_set_from_vertices` and
`normals_split_custom_set`, even though the tested vehicle normals were finite
and unit length. The add-on therefore makes no native custom-normal call. It
uses Blender-calculated display normals while preserving source normals
losslessly for future writer research. This expected strategy remains visible
as `mr_display_normal_strategy` and in `normal_provenance`, but it is not a
user-facing warning when normal count and values are valid. Count mismatch,
non-finite, or near-zero source normals still produce a genuine warning.
Preview shading is secondary to process stability and provenance.

## Preview materials

A Blender material is created from the first non-`Null` binary texture slot
and connected to Principled BSDF Base Color. A neutral material is used when no
usable preview texture exists. Materials with the same supported visual
definition may be reused, while each draw's full Master Rallye binding remains
separate in object metadata. A folder-wide material cache retains aggregate
diagnostics, but each resource result reports only warnings created while that
resource was imported; earlier missing-texture warnings are not repeated.

Decoded alpha is connected conservatively and marked provisional. Exact
runtime blend/test behavior, chrome/reflection/environment semantics, secondary
slot blending, and unusual flags remain **UNKNOWN**. The Blender shader is a
preview, not a claim about the original DirectX renderer.

## Inspection and authoring status

Select an imported object and open the **Master Rallye** tab in the 3D View
sidebar. The panel shows source identity, counts, texture bindings, and a
current authoring status. It can print the complete JSON metadata or reload
cached preview images.

The status diagnostic distinguishes:

- `SOURCE_IDENTICAL`: counts, required provenance attributes, topology, and
  target-space geometry fingerprint still match the import;
- `GEOMETRY_EDITED`: topology still maps but coordinates changed;
- `TOPOLOGY_CHANGED`: counts or required provenance attributes changed;
- `UNKNOWN`: insufficient metadata.

This is an early safety signal, not a byte-perfect round-trip guarantee.
Arbitrary topology edits may invalidate one-to-one source identity. No writer
exists in R2.

## Save and reload

Headless tests save and reopen both synthetic and real imported vehicles.
Meshes, materials, UVs, custom attributes, object JSON, draw/group metadata,
and absolute preview-image cache paths survive. The `.blend` is not
self-contained unless the user explicitly packs resources; cached PNGs must
remain available for external image references to resolve.

Never commit a `.blend` containing imported game geometry or decoded game
textures.

## Known limitations

- Vehicle DX only; Course DX is outside R2.
- No DX/DXT writer or in-game replacement path.
- No exact runtime multi-texture or alpha semantics.
- Opaque trailing sections are classified and hashed, not embedded in the
  `.blend`.
- Source identity metadata assists future writer research but cannot preserve
  identity through every arbitrary Blender topology operation.
