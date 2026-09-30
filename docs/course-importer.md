# Course and RaceTest import in Blender

The existing Master Rallye add-on imports course resources read-only. The DX
importer reuses shared DX arrays, sidecar parsing, coordinate conversion, DXT
decoding, preview materials, and mesh metadata. R5T-SDK1 adds the core semantic
Course SDK above those raw parsers and makes RaceTest helpers consume that
model. It does not write course resources.

## Import

Use **File → Import → Master Rallye Course (.dx)** and select a course DX such as `DataGx/Course/Italy1/track01.dx`. The importer accepts the observed revision-135 course render grammar, validates all local index and vertex ranges, and imports one mesh into a `Master Rallye Course - <folder>` collection.

The collection has `Render Geometry`, `Course Helpers`, and `Unknown - Opaque` children. The opaque collection carries neutral tag100 boundary/hash metadata with semantics marked `UNKNOWN`; it does not label the data as collision. The matching RaceTest XML importer adds semantic helpers under `Course Helpers/Race Logic`. Sidecar material names and DXT textures use the existing local resource resolution and preview path. Retail Italy1 draw slots reference 77 unique DXT stems and France1 references 95; all resolve in their matching course folders.

Source positions use the established Master Rallye to Blender conversion `(X, Y, Z) → (X, -Z, Y)` at scale 1.0. One mesh preserves all UV sets, source colors, source normals and float32 bit metadata, plus face attributes for source draw ID, triangle index, and group ID. Object metadata retains DX identity/hash, revision, draw batch/container records, resource kind, render-validation results, sidecar candidates, and the opaque tail hash/boundary.

Course objects are marked `READ_ONLY`. The vehicle position, attribute, and topology exporters reject them. R5T-A implements no DX, BSP, route, checkpoint, surface, or SFL writer.

## RaceTest XML race logic

With a course mesh active, use **Import RaceTest XML Race Logic** in the course
panel and select its `DataScene/RaceTest/<course>.xml`. The parser retains the
complete XML element tree and exposes ordered `MarkerLists`, `EggLists`, Egg
matrices, AI objects, and direct Egg/AI/component values. Source attributes and
unknown named values remain available on the typed objects and on split-helper
metadata. Each marker keeps its parent list,
source index, `No`, `Marker Type`, exact Pos/Dir strings, parsed vectors, XML
path, and the original named values/attributes.

The forensic XML layer retains the full ordered tree. The semantic
`CourseRaceLogic` model supplies typed StartArea, FinishArea and SplitTime
records; Blender does not reparse split IDs, Radius, ExtraTime or Egg Row3.
Helpers live under `Course Helpers/Race Logic`. StartArea and FinishArea retain
ordered points and a source-order outline. No filled FinishArea volume or
per-car start slot interpolation is invented. Other MarkerLists remain
grouped by source list. Positions use the established
`(X, Y, Z) → (X, -Z, Y)` conversion. Directions stay as source metadata.

Split visual Eggs get a small original procedural yellow arrow icon at the
serialized `en3d Matrix` transform. For France1 SplitTime0, debugger and
runtime evidence confirms this Row3 is both the sign position and gameplay
center. The add-on now draws the read-only trigger as a three-ring wire sphere
at the semantic center, with the parsed Radius and `Split Time ID`. SplitTime0
has direct runtime/debugger evidence; other records retain executable/shared
structure evidence without claiming separate runtime movement tests. Exact
ExtraTime meaning remains `UNKNOWN`. Exact-name `SplitTimeN-<index>` siblings
appear in a separate `Visual Checkpoint Objects` collection and are never
marked as trigger-center sources. No helper includes copied game models or
textures.

The core `discover_course_resources()` / `load_course_project()` APIs accept a
course folder or a resource path and can compose matching DX, RaceTest XML,
HNT, SFL, TXT, and GXM prefix data. Ambiguities are diagnostics, not silent
selection. Blender currently keeps its compatible two-step DX and RaceTest XML
operators; package discovery is available to scripts and other tools, while a
folder-browse operator remains future UI work.

Runtime evidence labels are attached to StartArea and FinishArea helpers. The
current France1 inventory contains 1,080 markers in eight lists, 76 Eggs, and
three split visual Eggs. Headless validation is in
`tests/blender/r5t_b_xml_smoke.py`; the final SplitTime0 evidence is in
`research/r5t_d1/` and the France1 corpus inventory is in
`research/r5t_d0/france1-race-logic.md`.

Headless validation covers Retail France1 and Italy1 with Blender 5.2.2. The
semantic helper smoke checks the canonical coordinate transform, sphere rings,
radius, evidence scope, visual companions, StartArea/FinishArea hierarchy and
the packaged ZIP implementation. The packaged smoke imports the ZIP directly
without installing into the user profile.

## GXM source topology diagnostic (R5T-E.1)

With a course DX object selected, use **Import GXM Startpoint Mesh** in the
same course panel and select a same-stem version-7 GXM/TXT pair. This
read-only diagnostic resolves the literal `startpoint` `moMesh` triangle
span through the canonical source position index fields and creates one mesh
under `Course Helpers`. It preserves the GXM hash, node ordinal/parent/span,
triangle indices, unique source position indices, and source-to-Blender
transform note. The transform remains supported by the measured global
source-to-DX and existing DX-to-Blender transforms.

France1 imports as 8 positions, 12 triangles, and 18 edges. The connectivity
is now decoded; gameplay meaning of the `startpoint` name remains unknown.
Headless Blender validation checks the imported counts and source metadata.
It does not claim manual viewport parity or runtime behavior.

R5T-E.1 headless validation in Blender 5.2.2 passed for this source mesh, the
existing Retail Italy1/France1 importer path, and the packaged ZIP install
with France1 DX, RaceTest XML, and the version-7 source GXM.

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
