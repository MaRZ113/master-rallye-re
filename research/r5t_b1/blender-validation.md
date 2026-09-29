# R5T-B.1 Blender validation

Blender 5.2.2 LTS was run headless from the user-provided installation at
`D:\Game\Master Rallye\_reverse-tools\blender-5.2.2-windows-x64`.
Derived run JSON files are under ignored `.research-output/r5t_b1/`.

## Retail course render import

The existing course importer passed for both retail DX resources. All source
vertices, triangles, draws, both UV sets, source metadata, and DXT textures
were retained. The only importer warning was the documented undecoded course
tail; route and surface remain false, and tag100 remains an opaque detected
section.

| Course | DX revision | Vertices | Triangles | Draws | UV sets | Material slots with loaded DXT |
|---|---:|---:|---:|---:|---:|---:|
| Italy1 | 135 | 54,612 | 41,722 | 837 | 2 | 75/75 |
| France1 | 135 | 65,206 | 64,577 | 995 | 2 | 97/97 |

## RaceTest XML marker overlays

The existing marker overlay passed on the matching Demo 9.10 France1 DX/XML
pair with 583 markers and on retail France1 with 1,080 markers. Both records
had zero parse issues. Positions use the same shared DX-to-Blender transform;
these tests do not assign gameplay semantics to the records.

## GXM startpoint point overlay

The new existing-add-on operator passed on the Demo 8.4.1 France1 GXM/TXT pair.
It created exactly eight Empty objects under `Course Helpers`, preserved the
node index/parent/span, float3 pool offset, point indexes and byte offsets,
and created no edges or faces. It reports the global source-to-Blender
identity as an inference and retains UNKNOWN point connectivity.

The 58-entry add-on ZIP was then installed in Blender using an isolated
`BLENDER_USER_CONFIG`, `BLENDER_USER_SCRIPTS`, and
`BLENDER_USER_EXTENSIONS` profile under ignored `.research-output`. The
packaged Demo 9.10 France1 DX/XML import passed with 583 markers, and the
packaged GXM source operator passed with eight point-only empties. A separate
packaged synthetic vehicle import passed, including collision overlay and
byte-identical positions-only zero-edit export.

These are data-creation and metadata smoke tests, not manual viewport review
or game-runtime proof. No course exporter is enabled.
