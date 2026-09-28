# R5T-A Blender validation

## Integrated path

`blender/master_rallye_io` adds **File → Import → Master Rallye Course (.dx)**. It calls the shared canonical parser and existing mesh/material/DXT path. Each import creates one render mesh under a course collection; helper, future collision, and future route collections are empty and labeled undecoded. Course metadata is read-only and the vehicle exporters reject course objects.

The mesh uses the existing `(X, Y, Z) → (X, -Z, Y)` conversion, all parsed UV sets, raw color channels, source normals/provenance, exact draw IDs, source triangle positions, group IDs, and material/texture metadata.

## Parser-side target results — CONFIRMED_BY_BINARY

| Course | Vertices | UV sets | Local indices | Draws | Triangles | Sidecar materials | Draw texture refs |
|---|---:|---:|---:|---:|---:|---:|---:|
| Retail Italy1 | 54,612 | 2 | 125,166 | 837 | 41,722 | 100 | 77/77 unique DXT stems resolved |
| Retail France1 | 65,206 | 2 | 193,731 | 995 | 64,577 | 127 | 95/95 unique DXT stems resolved |

Both pass complete, disjoint index and vertex validation. All 36 retail DX files pass the same course parser.

## Blender execution status — CONFIRMED_BY_RUNTIME (Blender only)

Headless smoke import passed in Blender 5.2.2 LTS for both retail targets. The check validated mesh counts, source identity attributes, per-course collection hierarchy, DXT images loaded into Blender materials, read-only metadata, and disabled vehicle exporters.

| Course | Blender vertices | Polygons | Draws | UV sets | Material slots | Slots with loaded DXT |
|---|---:|---:|---:|---:|---:|---:|
| Italy1 | 54,612 | 41,722 | 837 | 2 | 75 | 75 |
| France1 | 65,206 | 64,577 | 995 | 2 | 97 | 97 |

Blender suffixes duplicate global collection names (for example, `Render Geometry.001`); the smoke check verifies the render collection beneath each course root instead of assuming the global name is unsuffixed. Both imports report the expected undecoded trailing course/BSP payload. This confirms Blender data creation and texture loading, not visual D3D8 parity; no manual viewport appearance review was performed. The JSON run output is retained under ignored `.research-output/r5t_a/blender-smoke.json` and is not committed.
