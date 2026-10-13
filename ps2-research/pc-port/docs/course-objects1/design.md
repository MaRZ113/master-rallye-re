# Safe additional course surfaces: Turkey3

The first object-layer pilot adds the canonical PS2 Turkey3 puddle source meshes
to the PC framebuffer through the existing independent D3D8 overlay build.
It writes no PC course, XML, texture or executable file. Stock is the default.
The frozen modernization/renderer source and previous foliage/reflection builds
remain unchanged.

This is **SOURCE_GEOMETRY_STATIC_MATERIAL_PREVIEW**, a content-delivery pilot.
It uses original XYZ, authored UV/color and original course WATER-TGA. PS2 mode9
rewrites color/UV at runtime and adds a second texture pass; those computations
are deliberately outside this initial material. This layer makes no PS2 parity
claim and does not replace the native PC landscape.

## Data and instance contract

prepare_course_objects.py reuses PackFS, WATER1 visual PSM decoding and GXI
validation. It freshly verifies the four canonical input hashes and selected
PSM/GXI payloads. ADC-suppressed and diagnostic degenerate triples are excluded
with the established rules. The private deterministic artifact has 17 source
mesh rows, 2,235 expanded source vertices, 745 faces and one original 64x64 image.
Its SHA-256 is 2e3d6f8c90b3ed602d121f96fe7246a6fe3b70ab7c3c5d547c4bb8bf03a02b95.
Only that exact artifact, version1 and known source identities are admitted.

The mesh table preserves source node/material offsets and vertex ranges; the
compact source-contract.json preserves paths, materials, strips and exclusions.
The source frame is GAME_SOURCE, independently aligned to PC by GEOM1. Placement
is identity because these are landscape-world vertices. No model-local object,
XML instance or runtime pose is inferred from that fact.

The binary schema, typed coordinate/material fields, source mesh identities and
native transaction form the first reusable layer. Current support is deliberately
limited to this source family. Additional model-local meshes, transforms and
materials need explicit validated adapters and a new admitted schema/version.
Unknown versions, models, transforms and materials fail closed. This is not a
universal PSM importer.

## Render boundary

Neither Present nor an arbitrary EndScene is an insertion point. The staged
integration stores effective gameplay view/projection at their verified native
return sites, then requires a successful main-target world draw. It draws once
per frame at the exact existing UI DrawPrimitive consumer boundary, before
UiWorldScope and the original native UI call, even if Free Camera hides HUD.

Admission requires the exact PC executable, current render thread/native scene,
one camera, live RaceTest/Turkey3 certificate, current device/reset/race/owner,
same-frame gameplay matrices and world draw, intact typed UI consumer, and the
same main backbuffer/depth/viewport. Native forward-depth and fixed-function
dependencies must be supported. State-block recording is rejected. There is no
fallback to an unverified frame-end or offscreen target.

Depth clears invalidate world/depth proof. Scene transitions clear camera proof.
Every exact camera submission attempt invalidates earlier depth proof before
querying the new matrix, including failure. A subsequent successful world draw
is required. Course/race changes and true Reset invalidate the same proof.

The supplied old turkey3.jsonl frame94470 supports this insertion order: one
BeginScene span, gameplay projection/view at sequences3/4, indexed world draws
through481, another world primitive509, then first typed UI draw525. That capture
does not embed a course certificate and has unknown target identities; production
course/target admission is checked live. It does not prove every future frame's
ordering or visibility.

## Draw-local material and state transaction

| Field | Temporary source-preview policy |
|---|---|
| Geometry | One private DrawPrimitiveUP, triangle list, 745 source faces |
| World/view/projection | Identity world; captured effective gameplay view/projection |
| FVF / pixel shader | XYZ + DIFFUSE + TEX1 (0x142) / fixed function |
| Texture0 | Original Turkey3 WATER-TGA; retained rows, RGBA to BGRA |
| Stage0 | Texture x authored diffuse; original first UV pair, WRAP, linear, no mip |
| Stage1 | Disabled; no secondary water/reflection pass |
| Alpha | Test off; SRCALPHA/INVSRCALPHA blend; source alpha is255 |
| Depth | Test on, LESSEQUAL, write on; no height lift or Z bias |
| Cull | NONE, explicit source-inspection policy; PS2 winding/culling parity unknown |
| Lighting/fog/stencil/user clip | Temporarily disabled for this preview |
| Color writes | RGBA enabled |

Because authored color and the primary texture are opaque, this is an opaque
textured source preview despite enabling the conventional primary blend factors.
It is not the PS2 ground-gap transparency contract. Fill/clipping/wrap/bias,
stage0 result target and vertex blending are verified native dependencies rather
than silently inherited unknown state.

All 34 touched slots are captured before mutation. Attempted writes are recorded
before the call, so a failing setter that partially changes state is rolled back.
Every exact native value is restored, including stream0 because UP drawing clears
it. Getter COM references are balanced or retained until a failed restore can be
repaired. Render/depth targets, viewport, application buffers, indices and shader
constants are never modified.

The original UI draw is submitted once with its native HRESULT after a successful
restoration. The additional draw has its own diagnostic record; it is not fed into
the application's pending draw/vehicle classifier. Native-only setters update the
effective tracker and leave logical game state unchanged. Failed restoration is
repaired before subsequent affected application writes/getters/draws. If repair
remains impossible, unsafe submission is refused and the real failure reported.

Private image/frame references release before true Reset and final native device
Release. Failed Reset suspends the layer; successful actual Reset recreates it.
Window-mode reset echoes bypass this lifecycle. Disabling the layer releases
camera proof surface references immediately while retaining pending transaction
ownership for repair. The added static model does not enable CPU upload mirrors.

## Geometry and visibility limits

WATER1 established 0/745 identical PC faces and0/537 matching positions, with
22,679 other PS2 positions independently aligned to PC. Of the745 surface
centroids,405 are above and340 below nearby covering PC terrain. Retaining source
heights can therefore produce hidden or raised parts where the terrain editions
differ. Depth is kept enabled; geometry is not moved to force visibility.

Seventeen source mesh records and11 shared-edge components are not asserted
counts of live puddles. Authored conditional/LOD activation is unresolved.
No collision, physics, object movement or native course replacement is added.
The next useful expansion is one independently placed static model with a
verified transform and duplicate-PC-geometry check, after this delivery layer's
controlled runtime test.
