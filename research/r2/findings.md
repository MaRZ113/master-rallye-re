# Phase R2 findings

## Outcome

R2 adds a native Blender vehicle importer backed by the accepted R1 parser.
The implementation creates one editable mesh object per DX resource, preserves
draw/group/material provenance, decodes provisional preview textures through
the canonical DXT implementation, and packages the canonical library into an
installable add-on ZIP.

No DX/DXT writer, Course parser, executable analysis, or runtime-material
reverse engineering was added.

## Shared conversion model

Coordinate conversion now lives in `src/master_rallye/coords.py` and is used
by both glTF and Blender code. The established glTF path remains identity XYZ
at scale 1.0. Blender uses `(X, -Z, Y)`, a proper +90 degree X-axis rotation
from observed source +Y-up into Blender +Z-up. Its determinant is +1, so the
validated stored-global winding is unchanged. Normals use the same rotation.

The physical size of one source unit remains **UNKNOWN**. R2 applies no
cosmetic scale multiplier.

PNG raster presentation remains `flip-vertical`. Consumer UV policies are
independent: the accepted R1 glTF preview remains `V' = 1 - V`, while the
Blender 5.2.2 importer uses direct source V. In Blender A/B renders, direct V
made Astero `263/elf` and Pajero `203/BFGoodrich` artwork readable; `1 - V`
inverted it.

## Blender authoring model

The chosen representation is one object and mesh per DX. All reconstructed
faces remain triangles and retain physical-draw membership. Blender-accessible
attributes preserve source vertex ID/validity, source triangle ID, draw ID, and
top-level group ID. Exact color-like source bytes are kept in four integer
point attributes alongside a preview color attribute. All available UV sets
are imported.

Source normals are preserved as an inspectable point-domain vector plus exact
float32 component-bit attributes. Normal diagnostics and the Blender display
strategy are recorded in object JSON. Native Blender 5.2.2 custom-normal APIs
proved capable of access violations during repeated real imports, despite
finite unit-length source values. R2 therefore uses the documented
`blender-calculated-fallback` display strategy and never discards source
normal provenance. For valid normals this is supported behavior recorded in
metadata, not a warning. Invalid count, non-finite, and near-zero cases remain
real warnings.

Compact object JSON preserves ordered draw records, tags 2/7/8, group
hierarchy, texture slots, sidecar material candidates, neutral unknown fields,
trailing layout/hash, validation, and conversion policies. Opaque raw binary
tails are not copied into the `.blend`.

A geometry fingerprint and count/attribute checks report
`SOURCE_IDENTICAL`, `GEOMETRY_EDITED`, `TOPOLOGY_CHANGED`, or
`UNKNOWN`. The status is provenance assistance only and does not promise
byte-identical future serialization after arbitrary edits.

## Materials and textures

Materials use the first non-`Null` slot as provisional Base Color and reuse
visual definitions where safe. Draw-specific Master Rallye bindings remain in
object metadata even when Blender materials are shared. The DXT decoder writes
upright cached PNGs using the explicit R1 row policy; the same image is decoded
once per import cache. Decoded alpha is connected conservatively and marked
provisional.

Secondary slot blending, chrome/reflection behavior, render flags, and exact
alpha test/blend semantics remain **UNKNOWN**.

## Validation summary

Synthetic headless import passed in Blender 5.2.2 LTS. It exercises two
generated folder resources, tag-7/tag-8 records, two draws/materials, an
asymmetric texture, shared-corner topology, exact source-normal provenance,
invalid-normal fallback, edit-status transitions, Edit Mode, and save/reload.
The built ZIP was installed in an isolated Blender profile and imported the
same fixture using its private vendored parser.

Nineteen read-only game resources across Astero, Pajero, Forester, Bruno,
Ufo, megane, and ChevyBlazer were then imported with one implementation and no
per-file offsets. The representative subset remains:

| Resource | Vertices | Triangles | Draws | Tags | Materials |
|---|---:|---:|---:|---|---:|
| Astero/complete.dx | 2,657 | 2,423 | 24 | 2 | 20 |
| Astero/car.dx | 2,543 | 2,021 | 32 | 2/7/8 | 25 |
| Astero/wheel.dx | 220 | 252 | 5 | 2 | 4 |
| Bruno/car.dx | 2,455 | 2,014 | 21 | 2/7/8 | 19 |
| Bruno/wheel.dx | 220 | 252 | 5 | 2 | 4 |
| ChevyBlazer/car.dx | 2,713 | 2,156 | 36 | 2/7/8 | 28 |
| Ufo/complete.dx | 837 | 670 | 6 | 2 | 4 |
| megane/sus.dx | 48 | 48 | 1 | 2 | 1 |

Every sample validated its stored global indices, retained triangular topology,
reported `SOURCE_IDENTICAL`, and retained provenance plus JSON through a
temporary `.blend` save/reload. Astero folder discovery imported its three
actual DX resources. The known ChevyBlazer declared/root count warning remained
a non-fatal R1 diagnostic.

Temporary Astero complete side and three-quarter Blender renders contain all
2,657 vertices and 2,423 triangles with 20 preview materials. Geometry is
coherent and upright, with no exploded triangles, detached draw groups,
duplicate export geometry, or scale/axis discrepancy versus the accepted R1
representation. Directional door numbers and sponsor artwork were compared in Blender under
both modes. Upright PNG plus direct source V is correct; upright PNG plus
`1 - V` is vertically inverted. Geometry and scale remain unchanged.

All game-derived previews, PNGs, meshes, and `.blend` files remain under
ignored local output or the OS cache and are not repository artifacts.

## Decision gate

**Recommended next phase: R3A — DX/DXT writer and round-trip research.**

Blender import is stable on simple and grouped records, provenance survives
save/reload, and the authoring mesh preserves source draw/vertex/triangle
identity. Writer work must still begin conservatively: define edit classes,
reject unsafe topology changes, and prove serialization on synthetic data
before any game asset is written. R2 itself implements no writer.
