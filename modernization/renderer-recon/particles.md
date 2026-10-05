# Billboards, trails and weather prerequisites

**CONFIRMED_BY_EXE:** `DrawBillboards_005641C0` emits textured triangles using
current-camera basis and dynamic FVF0x142, stride24. DrawPrimitive VA `0x00564ECA`
(RVA `0x00164ECA`). Batch owner `0x00563CB0` groups particle work by model/texture;
FinalizeCamera `0x0056E250` invokes it after geometry, stock shadows and trails.
DirectX/Particles/Enable controls this final emission.

`DrawTrails_00571EC0` generates triangle records, updates packed vertex alpha and
emits DrawPrimitive at `0x005722E8` (RVA `0x001722E8`). `0x00571BF0` supplies
particle-family state and resource bindings; `0x00571B30` reaches the trail drawer.
Five setup modes `0x00584EA0`: opaque, SRCALPHA/INVSRCALPHA, ONE/ONE,
ONE/INVSRCCOLOR, ZERO/INVSRCCOLOR. Blended modes disable depth writes; effective
state and inherited Z compare must be logged rather than guessed.

**CONFIRMED_BY_EXISTING_RESEARCH / source observation:** protected retail
`DataGame/GameParticles.xml` has 12 ParticleRecord entries and Face Camera
fields (false in the inspected records). Executable names around VA
`0x004C16CA`..`0x004C17BA` include dirt_drive, dirt_drive_persist, tarmac_skid,
mud_drive, water_drive_front/rear, grass_drive, stones_drive and sparks. These
identify particle resource/trigger leads, not a complete physical Surface enum.

**STATIC_INFERENCE:** existing world geometry and camera-basis submission are a
plausible renderer seam for rain/spray. World-space streaks need emitter placement,
velocity/lifetime, long-axis orientation and density controls; screen-relative rain
needs a different projection/ownership policy. Wheel spray has existing water/dirt
leads, but contact/wetness-to-emitter logic is not mapped. Road/dirt/mud/snow GPU
material identity cannot be obtained from these names alone.

The generic renderer is present; a reusable weather spawning interface is UNKNOWN.
No rain was created. Future validation should compare dust, skid, water and sparks,
log their texture/FVF/blend/depth signature and determine simulation time during pause.

## Physical surface inputs for future spray/wetness

The existing protected retail `DataGame/Surface.xml` records are retained as
derived metadata in [surface prerequisites](data/surface-prerequisites.json),
with the source SHA256. The 16 indexed records name tarmac, harddirt, grass,
gravel, mud, rubber, rock, hay, metal and water; indices10..15 are NotDefined.
They include quality, friction, restitution, solid and `misc/tracks/...` texture
properties. No named snow type occurs in this inspected file.

**CONFIRMED_BY_EXE:** `RegisterSurfaceProperties_004DB5B0` (RVA0x000DB5B0)
registers Surface_Type/Quality/Restitution/Friction/TrackTexture/Solid properties
by index. This establishes a data seam, not a renderer category or a verified
tyre-contact-to-particle trigger. `TrackTexture` here must not be relabeled the
road's diffuse texture. Binding physical surface IDs to compiled draw materials
and to wheel-spray triggers remains unresolved.
