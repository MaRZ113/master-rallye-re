# Vehicle packets entering shared geometry

**CONFIRMED_BY_EXISTING_RESEARCH:** R-MAT1 establishes vehicle material flags,
ordered slots, environment stage, alpha-test/blend and transparent sorting for the
hash-locked retail image. R5V vehicle resource research separates body/complete/wheel
resources; that resource distinction does not establish different D3D caller PCs.

**CONFIRMED_BY_EXE:** entity+0x50 is the renderable packet, compiled instance at
packet+0x74. `0x0056BBC0` initializes/interpolates its world transform using
`0x00583B90`, attaches packet to instance+0xB0 and runs hierarchy `0x0054C9D0`.
Shared queue emission `0x00576970` binds layout/VB/IB/textures/material and final
instance depth overrides. This is the renderer-side vehicle seam; body and wheels
can both pass through it. A unique body/wheel caller function is not established.

Damage lead: renderer constructor `0x0056B680` owns configuration `0x00589110` at
+0x8C. Submission checks damage through `0x005893A0`, allocation `0x005841D0`, and
mutation `0x005892E0` before drawing. RemoveEnvMap/EnvMapFadeStrength options exist.
Exact damaged color/geometry/material mutation policy still needs tracing; there
is no invented per-material fade field.

Glass/window identity requires resource/material provenance. Alpha families join
the sorted alpha queue; env alpha setup still writes Z, then instance state can
override it. An env material is not necessarily glass: body/chrome may use it too.
Driver/interior separate draw ownership is not established.

Future seams: compiled instance/resource handle for car and wheel classification;
normal-bearing layout plus base/env stage for per-pixel/specular/reflection;
captured world matrix and post-damage VB content for shadow casting. Shared buffer
suballocation prevents assuming a VB is exclusively one car. Wet body/normal maps
require texture/material identity and a new shader policy, not changes in R-GFX1.

## Entity/resource and transform producers now traced

**CONFIRMED_BY_EXE:** `BuildVehicleEntities_004B6A00` appends `/car` to the selected
vehicle resource root and binds the body packet through `0x004F5B70` (call
`0x004B7027`). It appends `/wheel`, creates four entity objects (`0x004F5670`),
names them from the parent entity plus `/Wheel` and decimal index0..3, and binds
each wheel model at call `0x004B71E1`. TyretrackQuality, ShadowQuality and
ParticleQuality gate associated effects. Resource-name constructors `0x00443D40`
and `0x00443ED0` independently form Vehicles/<selection>/car and /wheel.

The body and wheel entities receive `AISimulateeTransform` controllers constructed
by `0x004F5290`. Initialization `0x004F5350` binds Broker key
`Physics/<entity-name>/Transform`; update `0x004F5440` copies all16 matrix DWORDs
into entity+0x50 packet+0x1C..+0x58. Renderer interpolation `0x00583B90` then feeds
the final WORLD seam. This establishes concrete per-wheel transform ownership
without inventing a unique D3D caller for wheels.

Ghost/replay is separate: `0x004BFE00` forms Vehicles/%sAlpha/car and /wheel,
creates four wheel entities, and attaches `gaWheelSplinePlaybackAI` (`0x004BFFA0`,
wheel index+0x10). Update `0x004C00D0` constructs wheel matrices from recorded
pose/suspension/steering/rotation data. Exact replay interpolation scalars are not
reinterpreted as ordinary physics matrices. Both paths reach the shared renderer.
The ghost alpha resources must be distinguished from ordinary vehicle glass.
