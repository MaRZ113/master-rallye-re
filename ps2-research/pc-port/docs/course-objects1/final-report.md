# PS2-COURSE-OBJECTS1 — Turkey3 additive visual layer

| Item | Result |
|---|---|
| Repository / branch | master-rallye-re-general / master |
| Starting / ending HEAD | 3f837f4ddcb27ee1034a4b0753634c92009360ec; unchanged |
| Frozen renderer tree | 7f9f5a7d9464b7b86ff09a9bf6c34b7ce341682d; source unchanged |
| First target | Canonical PS2 Turkey3 landscape puddle mesh family |
| Source geometry | 17 mesh records /51 strips /745 faces /537 distinct XYZ |
| Private runtime asset | PS2OBJ01 version1;70,384 bytes; exact SHA admission |
| Coordinates / placement | Original float32 game-world XYZ; identity; no height changes |
| Material | SOURCE_GEOMETRY_STATIC_MATERIAL_PREVIEW; original primary texture/UV/color |
| Drawing | One bounded additional native UP draw at verified pre-UI boundary |
| State safety | 34 captured slots; exact restore; partial-failure retry; no state blocks |
| Course/camera gate | Live Turkey3 certificate; same frame/device/reset/owner/camera/RT/depth/viewport |
| Stock default | CourseObjectsMode=0; foliage/pixel/reflection modes also0 |
| CPU mirroring | Not activated by this static object layer |
| Baseline / PS2 CTest | 24/24 PASS /28/28 PASS |
| Focused Python | 41/41 PASS;0 FAIL;0 SKIP |
| Native private-asset integration | PASS with canonical local artifact; Reset/lifetime/counts checked |
| Generator / exports / compileall / diff check | PASS |
| Earlier foliage/reflection artifacts | Preserved; no runtime acceptance promotion |
| New layer in-game visibility | NOT_PERFORMED; controlled user A/B required |
| Original game assets / Course SDK / renderer | Unchanged |
| Commit / push / deployment | None; previous worktree changes preserved |
| Overall status | IMPLEMENTED_PENDING_USER_RUNTIME |

The safe additional-content path is implemented independently of playable PC
course data. It loads a verified local source artifact, admits only Turkey3,
captures the effective gameplay camera and draws original PS2 source surfaces
before the original native UI submission. Stock does not load this asset or
allocate its image. No D3D8 proxy chain or new executable hook site is introduced.

The original PC source course lacks these exact surface records according to
WATER1/GEOM1's independently checked compiled-geometry comparison. The layer
uses the recovered visual PSM source and does not confuse collision triangles,
mesh owners, components and live object counts.

See [design.md](design.md) for identity, rendering and lifecycle,
[source-contract.json](source-contract.json) for original hashes/offsets and
[runtime-ab.md](runtime-ab.md) for the simple manual check.
Artifact and DLL hashes are in [build-report.json](build-report.json).

## Important material and visibility boundary

The first material displays original authored source attributes and the original
Turkey3 WATER-TGA. It does not yet perform mode9's ground-gap RGBA preparation,
animated primary UV, secondary WATERSURFACE2 pass or unproved secondary basis.
Original source alpha is255; this preview is effectively opaque. CULL_NONE and
disabled fog/lighting are explicit inspection policies, not PS2 culling/lighting
claims. No PS2 visual parity is asserted.

The PC terrain differs:405 source triangle centroids lie above and340 below
nearby covering PC surfaces in the frozen comparison. Some added parts may be
hidden or raised relative to PC ground. They are neither lifted nor depth-test
disabled to manufacture visibility. Conditional PS2 source/LOD membership is
not resolved by drawing the whole supported source family.

## Runtime boundary support

Existing supplied frame94470 has one native scene span and all indexed world
draws before first typed UI sequence525. It supports the insertion contract in
that captured frame. The filename is not a runtime course certificate, and the
old target fields are unknown. New native course/camera/target checks are mandatory.
No blanket claim about every future render ordering follows from this sample.

## Foundation for later objects

The asset table retains stable source mesh/material IDs and ranges. Coordinate
frame, source ownership and material policy are explicit. Current support is one
verified course-world surface family. Further models need validated model-local
geometry, explicit placement transforms, material/resource adapters and a
duplication check against baked PC content; unknown versions/families fail closed.
Physics, spline controllers and ambient spawning have not been implemented.

Both independent Win32 Release DLLs and the current staged patches are included
in the compact handoff. Original image/geometry data remains only in ignored
.assets and is excluded from the archive. A source-and-test reviewer can rebuild
using the external pinned renderer checkout and run corpus-independent tests.

The next step is the user Turkey3 A/B, followed by one bounded static model and
verified placement adapter. See [next.md](next.md).
