# Course and RaceTest import in Blender

R5T-A adds a read-only course path to the existing Master Rallye Blender add-on. It uses the shared DX arrays, sidecar parser, coordinate conversion, DXT decoder, preview material code, and mesh metadata representation. R5T-D.0 extends the RaceTest XML path in that same add-on with a hierarchy-preserving parser and typed race-logic helpers. Neither path writes course resources.

## Import

Use **File → Import → Master Rallye Course (.dx)** and select a course DX such as `DataGx/Course/Italy1/track01.dx`. The importer accepts the observed revision-135 course render grammar, validates all local index and vertex ranges, and imports one mesh into a `Master Rallye Course - <folder>` collection.

The collection has `Render Geometry`, `Course Helpers`, `Future Collision`, and `Future Route Data` children. The latter three remain empty and carry explicit not-decoded status. An imported XML marker overlay is a separate sibling collection. Sidecar material names and DXT textures use the existing local resource resolution and preview path. The current sidecar parser reads all 42 available course TXT files unchanged. Retail Italy1 draw slots reference 77 unique DXT stems and France1 references 95; all resolve in their matching course folders.

Source positions use the established Master Rallye to Blender conversion `(X, Y, Z) → (X, -Z, Y)` at scale 1.0. One mesh preserves all UV sets, source colors, source normals and float32 bit metadata, plus face attributes for source draw ID, triangle index, and group ID. Object metadata retains DX identity/hash, revision, draw batch/container records, resource kind, render-validation results, sidecar candidates, and the opaque tail hash/boundary.

Course objects are marked `READ_ONLY`. The vehicle position, attribute, and topology exporters reject them. R5T-A implements no DX, BSP, route, checkpoint, surface, or SFL writer.

## RaceTest XML markers (R5T-B; hierarchy update in R5T-D.0)

With a course mesh active, use **Import RaceTest XML Race Logic** in the course
panel and select its `DataScene/RaceTest/<course>.xml`. The parser retains the
complete XML element tree and exposes ordered `MarkerLists`, `EggLists`, Egg
matrices, AI objects, and direct Egg/AI/component values. Source attributes and
unknown named values remain available on the typed objects and on split-helper
metadata. Each marker keeps its parent list,
source index, `No`, `Marker Type`, exact Pos/Dir strings, parsed vectors, XML
path, and the original named values/attributes.

The helper collections live under `Course Helpers/MR_RaceLogic`. StartArea and
FinishArea have four ordered point helpers and a source-order outline; no filled
face or car-slot interpolation is invented. Other markers remain grouped by
their source list. Positions use the established `(X, Y, Z) → (X, -Z, Y)`
conversion. Directions stay as source metadata.

Split visual Eggs get a small original procedural yellow arrow icon at the
serialized `en3d Matrix` transform. The visual object stores the raw matrix,
Split Time ID, Radius, and ExtraTime. The four sibling `SplitTimeN-0…3` Egg
positions appear in a separate neutral `UNKNOWN` candidate collection. No
Radius sphere and no gameplay-trigger object is drawn: the trigger position is
still unknown and the sign transform is proven independent from it. These
helpers do not contain copied game models or textures.

Runtime evidence labels are attached to StartArea and FinishArea helpers. The
current France1 inventory contains 1,080 markers in eight lists, 76 Eggs, and
three split visual Eggs. Headless validation is in
`tests/blender/r5t_b_xml_smoke.py`; the R5T-D.0 corpus/spatial report is
`research/r5t_d0/france1-race-logic.md`.

Blender 5.2.2 headless validation passes for both Retail France1 and Italy1.
The built add-on ZIP was also imported directly from the archive in Blender
and passed the France1 hierarchy/helper check without installing into the
user profile. The standard preferences-based installer smoke requires writing
to Blender's user add-on directory, which is outside this workspace's allowed
write roots.

## GXM source point candidate (R5T-B.1)

With a course DX object selected, use **Import GXM Startpoint Point Candidate**
in the same course panel and select a same-stem GXM/TXT pair. The read-only
overlay places only the first eight candidate float3 positions as Empty
objects under `Course Helpers`; it invents no edges or faces. It preserves the
source GXM hash, node ordinal/parent/span, pool offset/count, each point index,
source byte offset, and exact source coordinates. The source-to-Blender
identity conversion is a `HIGH_CONFIDENCE_INFERENCE` from the measured global
source-to-DX and existing DX-to-Blender transforms.

On France1 these points form an axis-aligned 10-unit box and spatially
correlate with RaceTest Marker 0. The node-to-point association, box
connectivity, and gameplay meaning remain unproven. Blender headless smoke
validation checks eight point-only objects and metadata; this is not a manual
viewport or runtime validation.

The headless checks are `tests/blender/r5t_b1_gxm_helper_smoke.py` and the
course path in `tests/blender/addon_install_smoke.py`, which verifies the same
operator from the packaged add-on ZIP.

## Validated read model

Retail Italy1 parses as revision 135 with 54,612 vertices, two UV sets, 125,166 local indices, 837 draws and 41,722 triangles. The parsed ranges provide complete, disjoint coverage of indices and vertices. Retail France1 parses with 65,206 vertices, two UV sets, 193,731 local indices, 995 draws and 64,577 triangles, also with complete, disjoint coverage. Both have 100 and 127 TXT materials respectively. The per-draw texture slots are preserved; only the first existing preview texture is used by the established material preview.

All 36 retail DX files pass the same parser and range validation. The existing source coordinate conversion is reused; no course-specific evidence currently requires another coordinate convention.

## Verification

`tests/blender/r5t_a_course_smoke.py` passed headless in Blender 5.2.2 for
retail Italy1 and France1. It checks mesh counts, source identity attributes,
per-course collection placement, loaded DXT images, read-only metadata, and
rejection by vehicle exporters. Italy1 imports 54,612 vertices, 41,722
triangles and 75 textured material slots; France1 imports 65,206 vertices,
64,577 triangles and 97 textured material slots. No manual viewport review or
game-render parity claim is included. Exact results are in
[`research/r5t_a/blender-validation.md`](../research/r5t_a/blender-validation.md).
