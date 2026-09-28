# Course DX import in Blender

R5T-A adds a read-only course path to the existing Master Rallye Blender add-on. It uses the shared DX arrays, sidecar parser, coordinate conversion, DXT decoder, preview material code, and mesh metadata representation. It does not create a second add-on or any course writer.

## Import

Use **File → Import → Master Rallye Course (.dx)** and select a course DX such as `DataGx/Course/Italy1/track01.dx`. The importer accepts the observed revision-135 course render grammar, validates all local index and vertex ranges, and imports one mesh into a `Master Rallye Course - <folder>` collection.

The collection has `Render Geometry`, `Course Helpers`, `Future Collision`, and `Future Route Data` children. The latter three remain empty and carry an explicit not-decoded status. Sidecar material names and DXT textures use the existing local resource resolution and preview path. The current sidecar parser reads all 42 available course TXT files unchanged. Retail Italy1 draw slots reference 77 unique DXT stems and France1 references 95; all resolve in their matching course folders.

Source positions use the established Master Rallye to Blender conversion `(X, Y, Z) → (X, -Z, Y)` at scale 1.0. One mesh preserves all UV sets, source colors, source normals and float32 bit metadata, plus face attributes for source draw ID, triangle index, and group ID. Object metadata retains DX identity/hash, revision, draw batch/container records, resource kind, render-validation results, sidecar candidates, and the opaque tail hash/boundary.

Course objects are marked `READ_ONLY`. The vehicle position, attribute, and topology exporters reject them. R5T-A implements no DX, BSP, route, checkpoint, surface, or SFL writer.

## Validated read model

Retail Italy1 parses as revision 135 with 54,612 vertices, two UV sets, 125,166 local indices, 837 draws and 41,722 triangles. The parsed ranges provide complete, disjoint coverage of indices and vertices. Retail France1 parses with 65,206 vertices, two UV sets, 193,731 local indices, 995 draws and 64,577 triangles, also with complete, disjoint coverage. Both have 100 and 127 TXT materials respectively. The per-draw texture slots are preserved; only the first existing preview texture is used by the established material preview.

All 36 retail DX files pass the same parser and range validation. The existing source coordinate conversion is reused; no course-specific evidence currently requires another coordinate convention.

## Verification limit

`tests/blender/r5t_a_course_smoke.py` imports Italy1 and France1 in headless Blender and checks mesh counts, metadata, collection placement, texture loading, and exporter rejection. No Blender executable is installed in the current environment, so that runtime smoke script could not be run here. The importer is therefore integrated and statically/parser-validated, but Blender execution and visual review remain pending.
