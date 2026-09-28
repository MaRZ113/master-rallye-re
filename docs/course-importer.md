# Course DX import in Blender

R5T-A adds a read-only course path to the existing Master Rallye Blender add-on. It uses the shared DX arrays, sidecar parser, coordinate conversion, DXT decoder, preview material code, and mesh metadata representation. R5T-B adds a separate RaceTest XML marker overlay to that same add-on. Neither path writes course resources.

## Import

Use **File → Import → Master Rallye Course (.dx)** and select a course DX such as `DataGx/Course/Italy1/track01.dx`. The importer accepts the observed revision-135 course render grammar, validates all local index and vertex ranges, and imports one mesh into a `Master Rallye Course - <folder>` collection.

The collection has `Render Geometry`, `Course Helpers`, `Future Collision`, and `Future Route Data` children. The latter three remain empty and carry explicit not-decoded status. An imported XML marker overlay is a separate sibling collection. Sidecar material names and DXT textures use the existing local resource resolution and preview path. The current sidecar parser reads all 42 available course TXT files unchanged. Retail Italy1 draw slots reference 77 unique DXT stems and France1 references 95; all resolve in their matching course folders.

Source positions use the established Master Rallye to Blender conversion `(X, Y, Z) → (X, -Z, Y)` at scale 1.0. One mesh preserves all UV sets, source colors, source normals and float32 bit metadata, plus face attributes for source draw ID, triangle index, and group ID. Object metadata retains DX identity/hash, revision, draw batch/container records, resource kind, render-validation results, sidecar candidates, and the opaque tail hash/boundary.

Course objects are marked `READ_ONLY`. The vehicle position, attribute, and topology exporters reject them. R5T-A implements no DX, BSP, route, checkpoint, surface, or SFL writer.

## RaceTest XML marker overlay (R5T-B)

With a course mesh active, use **Import RaceTest XML Markers** in the course
panel and select its `DataScene/RaceTest/<course>.xml`. The operator extracts
literal `Marker Pos` and `Marker Dir` Vector3 values, places one neutral sphere
Empty for each marker with a valid position, and retains the raw XML record,
marker number/type, source path, and source coordinates as custom metadata. It
applies the same `(X, Y, Z) → (X, -Z, Y)` coordinate conversion as course DX.
Direction is preserved as metadata and does not orient the display object.

The overlay uses an `XML Markers - <course>` child collection and does not
change the render mesh. France1's 583/583 and Italy1's 277/277 Demo 9.10 XML
marker positions lie inside their matching course DX bounds. This supports
visual coordinate correlation; it does not identify marker gameplay behavior.
Headless validation is in `tests/blender/r5t_b_xml_smoke.py`.

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
