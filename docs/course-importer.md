# Course and RaceTest import in Blender

The existing Master Rallye add-on imports compiled course resources
read-only. The DX importer reuses shared DX arrays, sidecar parsing, coordinate
conversion, DXT decoding, preview materials, and mesh metadata. R5T-SDK1 adds
the core semantic Course SDK above those raw parsers. G0 adds a bounded
RaceTest XML authoring path; compiled DX and other course resources remain
read-only.

## Import

Use **File → Import → Master Rallye Course (.dx)** and select a course DX such as `DataGx/Course/Italy1/track01.dx`. The importer accepts the observed revision-135 course render grammar, validates all local index and vertex ranges, and imports one mesh into a `Master Rallye Course - <folder>` collection.

The collection has `Render Geometry`, `Course Helpers`, and `Unknown - Opaque` children. The opaque collection carries neutral tag100 boundary/hash metadata with semantics marked `UNKNOWN`; it does not label the data as collision. The matching RaceTest XML importer adds semantic helpers under `Course Helpers/Race Logic`. Sidecar material names and DXT textures use the existing local resource resolution and preview path. Retail Italy1 draw slots reference 77 unique DXT stems and France1 references 95; all resolve in their matching course folders.

Source positions use the established Master Rallye to Blender conversion `(X, Y, Z) → (X, -Z, Y)` at scale 1.0. One mesh preserves all UV sets, source colors, source normals and float32 bit metadata, plus face attributes for source draw ID, triangle index, and group ID. Object metadata retains DX identity/hash, revision, draw batch/container records, resource kind, render-validation results, sidecar candidates, and the opaque tail hash/boundary.

Course render objects are marked `READ_ONLY`. The vehicle position, attribute,
and topology exporters reject them. There is no DX, GXM, tag100, tag1400,
route, surface, or SFL writer.

## RaceTest XML race logic

With a course mesh active, use **Load Course Race Logic** in the course
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
four ordered, individually transformable points; there is no filled area or
invented per-car start slot interpolation. Other MarkerLists remain grouped by
source list. Positions use the established
`(X, Y, Z) → (X, -Z, Y)` conversion. Directions are retained as source metadata;
the G1 route/limit/camera views additionally use them for locked, read-only
orientation previews and optional direction rays.

Each SplitTime has a simple editable center helper at `en3d Matrix` Row3 and a
three-ring wire sphere driven by the explicit `Radius`. The sphere remains the
3D trigger-volume preview; no large artificial sign is attached to the main
trigger center. The sibling Eggs `SplitTimeN-i` are shown at their own Row3
positions in `Visual Checkpoint Objects`. Each companion imports its own
`en3d Matrix` orientation as a locked, read-only helper basis and gets a
procedural labeled sign card plus cyan direction ray derived from that same
companion matrix. These are viewport aids only and do not assert runtime
forward semantics. The fallback panels use Blender geometry/text and no game
texture/model. Companion Row3 position authoring remains unchanged; companion
rotation is preserved from source and never exported. For France1 SplitTime0,
debugger and runtime evidence confirms the main Egg Row3 is both the main sign
position and gameplay center. Exact ExtraTime meaning remains `UNKNOWN`. All
sign/ray/radius preview objects are marked editor-only and excluded from the
XML edit traversal.

### G1 route, limit and camera diagnostics

RaceLine and the four literal limit lists are placed under
`Route Research/RaceLine` and `Route Research/Limits/<list>`. Each RaceLine and
limit view keeps individual source-order marker helpers and a source-order
polyline. The importer does not reorder points, synthesize a closing edge, or
interpret marker names as gameplay semantics. The `Cameras` list receives
individual position helpers and optional Marker Dir rays, but no path line is
invented. Direction-ray creation is disabled by default and can be enabled in
the XML import options. The points, curves, and rays are marked read-only and
editor-only; none are added to the stable G0 RaceTest writer allowlist.

Retail executable analysis confirms `gaRaceLineAI` consumes RaceLine positions
for per-car nearest sample/progress/rank tracking, and `gaLimitsAI` loads the
four exact limit lists to publish `LimitState`. It does not prove RaceLine AI
steering or limit-triggered reset behavior. The RaceTest `Cameras` list has not
been linked to the camera parameter records. All new G1 views remain
non-authorable pending isolated human runtime tests; details are in
[`research/g1/findings.md`](../research/g1/findings.md).

## G0 editing and export

Supported StartArea and FinishArea marker empties can be moved independently
or transformed together. Export reads each marker's final world-space point,
so group translation, rotation, and scale are represented by the four edited
positions. It never writes a Blender parent transform. Two current Retail
FinishArea lists have five markers; their helpers remain read-only, and an
attempted move is refused at export.

The SplitTime center Empty is at the gameplay trigger center and can be moved.
Its Radius and Split Time ID are editable in the Course Race Logic panel. The
wire sphere follows the explicit Radius custom property. Scale does not change
Radius and warns if the center helper scale is changed. The large companion
sign cards are placed at the sibling visual Egg positions; each companion's
own imported orientation drives only its read-only card/ray preview. ExtraTime
remains informational with meaning marked `UNKNOWN`.

Each exact source sibling `SplitTimeN-i` is a visual checkpoint companion and
has its own stable XML identity metadata. Its final world position can be
authored independently. The `SplitTimeN_Group` controller translates the main
Egg and all visual companions together; the wire Radius remains unchanged.
The main trigger center and each companion stay independently selectable.
Matrix rows 0–2 and Row3 W are preserved.

StartArea/FinishArea helpers represent points, so their final world positions
are exported without warnings for editor-only helper rotation/scale. The
checkpoint group is translation-only; export refuses group rotation or scale.

Use **Export Race Logic XML** in the Course Race Logic panel and choose a new
output path. The operator checks that the source XML hash still matches the
imported helpers. The core writer refuses the original path and existing
outputs, returns byte-identical source on no-op, and blocks any semantic XML
change outside its allowlist. A `<output>.mr-race-edit.json` manifest records
source/output hashes, changed paths and values, and warnings. The export does
not edit `Data.sma`, compiled resources, or the source XML.

Human runtime tests through Blender export confirmed StartArea, FinishArea, and
SplitTime0 center edits. A combined StartArea + FinishArea edit loaded normally.
These G0 results are recorded in
[`research/g0/runtime-results.md`](../research/g0/runtime-results.md). G0.1
visual-companion XML edits have not been separately human-runtime-tested. See
[`docs/course-race-logic-authoring.md`](course-race-logic-authoring.md) for the
writer allowlist and transform rules.

The core `discover_course_resources()` / `load_course_project()` APIs accept a
course folder or a resource path and can compose matching DX, RaceTest XML,
HNT, SFL, TXT, and GXM prefix data. Ambiguities are diagnostics, not silent
selection. Blender currently keeps its compatible two-step DX and RaceTest XML
operators; package discovery is available to scripts and other tools, while a
folder-browse operator remains future UI work.

Runtime evidence labels are attached to StartArea, FinishArea and split-center
helpers. The current France1 inventory contains 1,080 markers in eight lists,
76 Eggs, and three main split records with 12 visual companions. Headless validation is in
`tests/blender/r5t_b_xml_smoke.py`; the final SplitTime0 evidence is in
`research/r5t_d1/` and the France1 corpus inventory is in
`research/r5t_d0/france1-race-logic.md`.

Headless validation covers Retail France1 and Italy1 with Blender 5.2.2. The
semantic helper smoke checks the canonical coordinate transform, sphere rings,
radius, evidence scope, visual companions, StartArea/FinishArea hierarchy and
the packaged ZIP implementation. G0 tests both no-op and edited export through
workspace sources and the built ZIP. The packaged smoke imports the ZIP directly
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
