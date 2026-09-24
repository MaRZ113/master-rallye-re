# Blender vehicle importer and experimental topology exporter (R4F)

The add-on imports proven Master Rallye **vehicle** DX resources directly into
an editable Blender mesh. The R3/R4E safe exporters patch same-topology DX
attributes against the original template; R4E also stages same-size DXT
replacements. R4F adds a separate experimental topology rebuild action for
existing draws. Course DX resources remain unsupported.

## Compatibility

- Tested: **Blender 5.2.2 LTS** (`d13f752e3b9c`).
- Expected API baseline: Blender **4.3 or newer**.
- Older versions were not tested and are not claimed as supported.

## Build and install

Build the ignored distribution artifact from the repository root:

```powershell
py -3 tools/build_blender_addon.py
```

This creates `dist/master_rallye_io.zip`. The build copies the canonical
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

The optional **Show collision hulls** setting creates read-only tag-101 helper
objects when available. See `docs/blender-collision.md`.

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
| Point | `mr_generated_vertex`, `mr_parent_source_vertex` | Tooling-only generated/parent provenance for R4F |
| Face | `mr_source_face_valid`, `mr_draw_assignment_valid` | Distinguish original faces and explicit existing-draw assignment |

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
- `POSITIONS_ONLY_CHANGED`: complete source provenance remains valid and
  coordinates changed;
- `UNSUPPORTED_TOPOLOGY_CHANGED`: topology, triangle mapping, or draw/group
  membership changed;
- `INVALID_PROVENANCE`: source identity attributes or metadata are missing,
  duplicated, invalid, or out of range.

Only `SOURCE_IDENTICAL` and `POSITIONS_ONLY_CHANGED` are exportable.

## Experimental positions-only export

Use **File > Export > Master Rallye DX — Positions Only (Experimental)** or
the button in the Master Rallye object panel. The exporter requires complete
1:1 source vertex/triangle identity, unchanged topology and draw membership,
identity object transforms, the import-time source SHA-256, and positions
inside the original AABB. It refuses the original source path.

Unchanged position records retain their exact original bytes. Changed vertices
replace only their 12-byte XYZ records. Before a file is written, the writer
audits the binary diff, reparses the candidate, compares every known
non-position structure and diagnostic, and hashes preserved sections. See
`docs/dx-writer.md`.

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
- No topology-changing serializer, normal/UV/material writer, bounds updater,
  DXT Blender export, or automatic game replacement.
- At this R2 stage, positions-only output still awaited human runtime testing. The later R3 test passed; see format-status.md.
- No exact runtime multi-texture or alpha semantics.
- Opaque trailing sections are classified and hashed, not embedded in the
  `.blend`.
- Collision tag-101 overlays are read-only forensic helpers; collision export
  and editing are not supported.
- Source identity metadata assists future writer research but cannot preserve
  identity through every arbitrary Blender topology operation.

## R2.5 sidecar discovery

The importer uses the shared evidence-scored resolver rather than requiring
`<dx-stem>.txt`. Selected path, score, ambiguity state, and every alternate
candidate with its evidence metrics are stored in `mr_metadata_json`.
Nonstandard files such as `ForesterWheel.txt`, `PajeroWheel.txt`, and
`MattWheel.txt` can therefore be selected without a hardcoded alias table.

Sidecar material metadata now includes nullable `has_alpha`, `uses_alpha`, and
`is_noise` for every texture entry. These fields are preserved for future
research only; the preview shader remains conservative after R4D corpus analysis because exact stage and alpha-state mapping is unresolved. See docs/blender-materials.md. Folder
warnings are printed as `resource -> warning` lines before the aggregate
summary. All R2.2 raster, direct-V Blender UV, normal-provenance, and safe
display-normal policies remain unchanged.

## R4E authoring

The new **Export DX - Safe Attributes** operation validates import provenance,
source hash, triangle/draw mapping, source-indexed UV loops, source-space
`mr_source_normal` and `MR Vertex Color` before patching the DX template. A UV,
normal, or color divergence between corners of one source vertex is rejected
with `REQUIRES_R4F_TOPOLOGY_WRITER`. The existing positions-only export remains
for R3-compatible workflows. Fixed alpha/env edits are staged by draw ID in the
material inspector. The selected texture can be exported to PNG, validated,
staged from an edited PNG, and queried for reverse users. All writes go to
separate project/staging paths. See vehicle-authoring.md and texture-authoring.md.

## R4F authoring extension

The panel lists existing draw IDs/materials, shows draw IDs on selected faces, and assigns selected faces to an existing draw. A distinct **Export DX - Topology Changing (Experimental)** command previews source/compiled counts and splits. It requires explicit triangulation and complete source-space normal, color and UV data; it refuses missing or ambiguous draw membership. Generated provenance remains tooling metadata only. The output render core is rebuilt and collision bytes remain untouched. See docs/topology-authoring.md. The F1 Astero car.dx topology output was confirmed by human runtime testing; R4G B1/P1/W1 subsequently confirmed expanded bounds and complete/wheel topology in their tested contexts.

## R4G vehicle workflow controls

Imported objects display RACE BODY, PRESENTATION or WHEEL TEMPLATE roles. The sidebar can save a VehicleProject, validate it, and build an isolated mod staging tree. A car.dx with a finite tag101 hull exposes source-space collision translation and per-axis scale controls, validation/reset, preview center/radius/AABB and source hash. Marker-1339 box/sphere visualization is opt-in. These controls do not write the source DX; collision scale and expanded bounds await original-game tests. See docs/vehicle-project.md and docs/collision-authoring.md.
