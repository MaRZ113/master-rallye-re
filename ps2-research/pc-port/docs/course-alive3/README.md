# COURSE-ALIVE3: PS2 physical props (hay bales and tumbleweeds) on PC

Opt-in `RigidProps=1` (PS2Port.ini). Default 0 = Stock: nothing is loaded, simulated or drawn.

All 83 `gaAiRigidBody` props of the 36 PS2 RaceTest courses are back as physical objects: 58 hay bales on Italy2,
ItalyS1, ItalyS4, ItalyW1, ItalyW2 and 25 tumbleweeds on Turkey1, Turkey3, TurkeyM, TurkeyS2Flip. They stand where the
PS2 puts them, sleep until a car hits them, then roll, tumble and settle on the course, the way the PS2 owner does it.
Inventory: [inventory.json](inventory.json) (coordinate-free).

## Why not the native PC physics

RIGID-PORT1..1.3 tried to admit the bodies into `gaPhysicsManager` and stopped at NO-GO: the PC `gaAiHayBale` path
hard-codes the hay model and mass 350, crashes in the stock contact code (`0x006363C0 -> 0x004FFDE0`), and the PC model
loader rejects PSM; private convex resource ownership and safe insertion are not solved. COURSE-ALIVE3 therefore takes
the COURSE-ALIVE1/2 route: the PS2 port proxy owns the props (physics, drawing) and reads what it needs from the game
(car poses, course collision). The game knows nothing of the props.

## Parts

| Part | File | Depends on |
|---|---|---|
| PS2 rigid prop physics (portable) | `renderer/ps2_rigid_props.hpp` | C++17 standard library only |
| Asset, per-race runtime, course guard, landscape and car hull loading, D3D resources | `renderer/rigid_props.hpp/.cpp` | `collision_debug.hpp` (tag1400 and tag101 parsers), `course_objects.hpp`, `sma_archive.hpp` |
| Native seam (proof, car poses, ticks, draw) | `renderer/rigid_props_native_integration.hpp` | FLEET-ALL-CARS1 participants, the COLLISION-DEBUG1 admission |
| Asset builder | `tools/prepare_rigid_props.py` | PS2 corpus, `course-port/build_objects.py`, `ps2-research/tools/rigid_runtime.py`, SDK collision reader |
| Contracts | `tests/rigid_props_tests.cpp` (ctest `rigid_props_contracts`) | |

Patch 0001 gained 13 lines next to the COLLISION-DEBUG1 seams (include, observe_transform, before_ui, repair in
`visual_wrappers.cpp`; include, config record, reset, shutdown in `wrappers.cpp`; source and test in `CMakeLists.txt`);
the baseline lock holds its new SHA-256. `ps2_diag.hpp` gained the effect `rigid_props`.

## What is the PS2 (RIGID1, static reverse of SLES_509.06)

| Item | PS2 evidence | Port |
|---|---|---|
| Authored props | 83 `gaAiRigidBody` Eggs, typed Mass / MOI / Trigger Distance / Casts Shadow (`19fe98`) | asset, bit-equal to `rigid_runtime.parse_authored` |
| Collision shape | PSM tag101 representation B (hay 16 points / 10 faces, an octagonal prism along X; tumbleweed 26 / 32) | the same points, face planes merged from its triangles |
| Centre of mass | tag101 base centre = model origin on both families | body origin = model origin |
| Tick | one manager invocation per game tick (30 per second, COURSE-WATER1 measurement), two half steps of float32(1/30)/2 (`1733a0 -> 173b68`) | `TickClock` 30 Hz, two half steps |
| State | x, q (wxyz), P, L; v = P/m, omega = R I^-1 R^T L (`266e20`) | same |
| Forces | gravity only, F = (0, -9.81 m, 0) (`27d060`); no wind or random input in the owner | same |
| Activation | near = camera-visible with radius 4 and squared 3D camera distance <= 10000 (`1a0258`, `200550`) | camera from the gameplay VIEW, four side planes of VIEW x PROJECTION |
| Wake | a paused settled prop is not woken by proximity, only by a contact with an active vehicle (`16e498`) | same; the car hull contact wakes it |
| Far | an active prop that goes far is paused, its momenta x float32(1/60) per invocation for 60 invocations, zero on the last; resumes when near | same |
| Rest | half step with \|v\| + \|omega\| < 0.3: backup pose restored, rest counter; counter x half step >= MaxClampTime (1) pauses | same |
| Initial placement | while touching the landscape, lift by an increment growing 0.01 per iteration, 1000 guard (`16f2f0`) | same |
| Drawn pose | rows = body basis, translation = position (`267f60`), Egg `en3d Interpolated` | interpolated between the last two ticks |

## What is not the PS2 (RIGID1 leaves it open)

- **Contact response.** The PS2 impulse magnitude, friction/restitution mixing and narrowphase are not reversed. Contacts
  are point-in-convex tests (hull points against landscape triangles, the car hull and other props, both ways; when no
  point lies inside the other hull, a face-normal separating-axis test gives one contact), solved by sequential impulses
  with Coulomb friction, restitution and a small penetration bias, 4 micro steps per PS2 half step. A point inside the
  car hull is pushed out through the face it entered by along the relative motion (a car moves up to 0.7 m per frame into
  a prop; the shallowest face is then often a side or the top, which pressed the bale into the ground), and car contacts
  resolve penetration by position projection, not by a velocity bias (that handed the car momentum for a position
  error). Port coefficients:
  hay restitution 0.15 / friction 0.7 / rolling resistance 2.5 per second, tumbleweed 0.35 / 0.45 / 1.0 (spin damping
  while touching the ground; without it a kicked round bale rolled 30..60 m on a gentle slope). Free flight is unchanged
  (the PS2 RK4 of a constant force is exact).
- **Mass: two-way coupling through the PC vehicle body (round 2).** On the PS2 the car and the prop are bodies of the
  same manager and exchange impulses (`25da08` applies J to both). The PC car is a body of the same class: collision
  holder `0x6F957C` -> backend (`0x692318`) -> convex instance vector -> instance+0x0C body of class `0x691A04`, whose
  layout equals the PS2 body (`0x4FF3E0`, `0x4FF4E0`: mass +0x20, position +0xA0, P +0x104, L +0x110, v +0x11C = P /
  mass). Each car takes the nearest such body within 3 m of its render origin. In the solver the car has that mass and
  its velocity takes the reaction; after the frame's ticks the summed reaction is added to the body (P += J, L += r x J,
  v = P / m), at most 12 m/s per frame. Offline: a 1300 kg car at 20 m/s into a 500 kg bale loses 5.55 m/s (perfectly
  inelastic 5.56), the summed impulse equals the car's loss. `RigidPropsCarImpulse=0` keeps the car kinematic (pushes
  as 1300 kg, feels nothing). The write happens on the render thread between game frames; the physics thread of the PC
  game is not proved to be the same thread.
- **Prop-prop wake.** A prop touched by an active prop is woken as well (the PS2 dispatcher is only proved for
  vehicle/prop pairs).
- **Landscape = course DX tag1400** (the surface triangles COLLISION-DEBUG1 draws), not the PS2 BSP narrowphase. Ground
  triangles (\|n.y\| > 0.5) are solid below whatever their stored winding; walls use the stored side (drivable side -n).
  BSP-only colliders (posts, banners) are not obstacles for the props.
- **Shadow owner.** The PS2 shadow technique is reversed (below), but which entities enter the PS2 shadow list is not:
  `330780` adds an entity when the descriptor at en3d+0x10 has a nonzero first word, and no writer of that descriptor
  was found; the rigid owner's `Casts Shadow` (+0x10) has no reader in the traced code. The port draws the PS2 shadow
  for the props whose authored `Casts Shadow` is True (all except Italy2's 11 bales). A PS2 check of whether bales cast
  a shadow decides this.
- **Wheels.** Only the car body hull (car.dx tag101 B) collides, not the wheel cylinders.

## Decisions

1. **Course guard.** As COURSE-ALIVE1: only when the course DX is a loose file that is not the retail PC one (a PS2
   course package). Measured on the 36 packages: every prop starts on the PS2 ground (hay bales 0.85..1.04 above it, hull
   half height 0.94; tumbleweeds 0.62..1.15, hull half height 0.48 - authored floating on the PS2 as well) and no package
   render has a hay triangle within 1.3 m of a hay bale Egg (no static duplicate). `RigidPropsStockCourses=1` lifts the
   guard for diagnostics.
2. **Material (round 2: PS2 shading).** The hay material is `Hay Bale $shader(dull)`, not `object`. Its setup `3aeb50`
   selects mode 3 (the car contract), the secondary texture `CommonTextures/dull` and the auxiliary `328000`, whose vertex
   callback `322400` overwrites every vertex colour with (0x72, 0x72, 0x72, 0xFE): after the x0.5 colour cache that is
   57/128 on the GS, i.e. the texture at 0.45 (the W5 model kept the PSM's white, twice too bright). Port: vertex colour
   0xFE727272 (MODULATE), opaque, fog, depth written, then the mode-3 secondary added (ONE/ONE, depth test, no depth
   write) with the REFL1 normal coordinates UV = (0.5 + 0.5 n.x, 0.5 - 0.5 n.y) of the view-space normal and
   `DULL.GXI` (32x32, mean RGB 49/34/21). Tumbleweed = `bigshrub $shader(treeblend)` (TREEBLEND1 mode2, no auxiliary:
   its PSM prelight 0x94/0xE0 is used as is): source alpha blend, no depth write, drawn far to near after the hay.
   Fog: the course fog is now also accepted when the game uses table (pixel) fog; the draw record logs the fog states
   (the first game test drew without fog: `"fog":false`).
5. **Drop shadow (round 2, PS2 `332628`).** The shared world-entity draw `330780` collects shadow casters and `332628`
   draws, per caster, the texture `Misc\Shadow\shadow` (`SHADOW.GXI`, 64x64, black with an alpha blob) projected onto
   the landscape: shadow box = model AABB X x1.75, Z x1.5, centred on the AABB centre, in the entity's yaw frame (right
   = (f.z, 0, -f.x), forward = (f.x, 0, f.z) from the forward axis); landscape triangles within half the larger box side
   whose normal n.y > 0.05, not `$surfacetype(water)`, with a vertex below the box centre; vertices lifted 0.1; UV =
   local (x, z) - centre over the box size + 0.5; vertex alpha = n.y x 128 x 0.85 / 128, divided by (0.75 d + 1) when
   d = (centre - vertex) . up - 0.5 >= 0. Port: the same on the tag1400 triangles, black x texture alpha x vertex alpha,
   alpha blend, no depth write, fog, CLAMP, drawn before the props, within 150 m of the camera.
3. **Pause, restart, exit.** No ticks while the pause menu is up (Eggs are Freezable); a new race generation re-creates
   the World at the authored poses; the landscape is kept while the course stays the same; a device reset recreates the
   textures, the physics state continues.
4. **Landscape load** on a worker thread at the first race frame of a course (course DX read + tag1400 parse + 8 m grid);
   the props appear when it is ready (`ps2_rigid_props_course` record has `terrain_ms`).

## Configuration

```ini
RigidProps=1
; optional:
RigidPropsAsset=PS2Grass/PS2RigidProps.ps2rgd
RigidPropsStockCourses=0
RigidPropsCarImpulse=1    ; 0 = the car pushes the props but does not feel their mass
RigidPropsDiagnostics=1   ; ps2_rigid_props_course/_gate/_draw, a state record every 150 ticks, ps2_rigid_props_car_impulse
```

## Asset

`PS2RigidProps.ps2rgd` (layout PS2RGD02: + per-vertex normals, environment texture, model AABB, shadow texture),
137,512 bytes, SHA-256 `98846199fad8be4bbf29a1f6c4c9e9833e71af52ee126bf867a03174db2d12ba`
(pinned in `rigid_props.hpp`). Regenerate:

```
python ps2-research/pc-port/tools/prepare_rigid_props.py --inventory ps2-research/pc-port/docs/course-alive3/inventory.json
```

## Status

Stress on the real PS2 ground of all 9 packages (`MRR_RIGID_TEST_ASSET` + `MRR_RIGID_TEST_COURSE_DX`): every prop kicked
as by a car at ~15 m/s, 20 s each: 83/83 stay above the PS2 ground, no NaN; all 58 bales asleep at the end (centre
0.79 m over the ground, octagon inradius 0.85); 22/25 tumbleweeds asleep, three still rolling down canyon slopes (they
stop by the PS2 far decay once out of view). Cost: about 8 microseconds per tick and active prop.

Offline contracts (ctest `rigid_props_contracts`): rotation of authored rows, hull planes, landscape contact and winding
rule, initial placement, settled sleep without wake by proximity, free fall, landing and sleep after MaxClampTime, far
decay, frustum, a car driving through two bales and a tumbleweed, asset layout and rejections, runtime batches, car
velocity from poses. In game: **PENDING_USER** (test steps in [runtime-ab.md](runtime-ab.md)).

## Game test 1 (owner, 2026-11-03) and round 2

Confirmed by the owner: hay bales and tumbleweeds are visible, are knocked over by the car and do not fly off on their
own. Session log `session-20261102-231525-396`: Turkey3 (6 props, landscape 27,866 records in 32 ms) - two tumbleweeds
hit, then paused far away (PS2 far rule); Italy2 (11 props, 20,705 records in 25 ms) - a bale hit and asleep again after
about 5 s; no prop below the ground; `"fog":false` on the draw. Requests: mass (the car must feel a bale), the props
are too bright (no shading), and the PS2 shadows. Round 2 adds the two-way coupling, the `dull` shading with its
environment layer, table-fog acceptance and the PS2 drop shadow (sections above). In game: **PENDING_USER**.

## Game test 2 (owner, 2026-11-03) and round 3

Owner: bales have weight and are knocked over, they look natural; the tumbleweed has a clear shadow and is knocked away
too easily. Log `session-20261103-000126-16248`: Italy2, one coupled car, 64 impulse records (velocity changes 0.1..3.3 m/s
per hit); Turkey3: a tumbleweed hit at tick ~5000 reached 24 m/s and rolled 100 m down the slope (height 52 -> 23)
before the far rule paused it. Fog states at the props' draw: fog disabled by the game there (`[0,0,0,1,1]`), so props
and course are equally unfogged.
Cause: the 5 kg / MOI 2 tumbleweed is PS2 data and a car hit legitimately throws it at about car speed, but the port had
no air drag, so it flew and rolled like a rubber ball. Round 3: quadratic air drag 0.5 rho Cd A / m per body (port value;
the PS2 owner has no wind/drag input in the traced code, its contact coefficients are not reversed either): tumbleweed
0.24 1/m (terminal fall about 6.4 m/s, from 25 m/s to under 5 m/s within a second), hay bale 0.0035 (negligible);
tumbleweed rolling resistance 1.0 -> 1.5. Offline stress: 25/25 tumbleweeds asleep after a kick, no long rolls.

## Owner check on the PS2 and round 4 (rollback)

The owner checked the PS2: neither hay bales nor tumbleweeds cast a shadow, and there is no air drag. Round 4 rolls back
round 3 completely (no drag, tumbleweed rolling resistance 1.0 again) and draws no prop shadow (the runtime builds the
shadow pass with range 0). This also settles the open shadow-owner question for these props: the authored
`Casts Shadow` does not put them into the `330780` shadow list. The reversed `332628` technique and
`rigid_shadow_triangles` stay documented and tested for a future car-shadow comparison; the asset keeps `SHADOW.GXI`.
