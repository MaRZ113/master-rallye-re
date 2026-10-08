# PS2-CDELTA1 ambient ownership survey

The largest newly identified authored ambient layer is a fleet controlled by
`gaEntitySpline`: **24 explicit model Eggs on 17 courses**, comprising 18 dinghies
on 11 courses, two barges on two courses and four airships on four courses.
Each Egg has a named, nonempty MarkerList plus speed/loop/trigger/banking settings.
This establishes authored movement inputs, not a successful runtime movement test.

Evidence comes from canonical decoded PackFS XML and named resource bytes.
`ambient-evidence.json` retains selected parameters, marker counts and source
hashes; it deliberately excludes full XML and route coordinates. The compared
PC layer is the 36 paired retail RaceTest XML files; all 41 retail RaceTest XML
were also inspected. The broader survey inventories 7,595 PC files and scans
99 PC XML files. `NOT_FOUND_IN_SCANNED_PC_CORPUS` always names the missing layer;
zero standalone XML Eggs does not exclude a prop baked into the course model.

## Q1: birds, owners, authored inputs and PC counterpart

All 36 PS2 RaceTest scenes contain one `gaAnimals_BirdManager`, generally on the
`IConManager`/`IContManager` list's `birds` Egg with `en3d Model Name=Null`.
The authored values name `Milling MarkerList=MillList` and
`Flight MarkerList=FlightList`; FlightList provides **542 Marker points across
36 courses**, while nonempty MillList provides **55 points across ten courses**.
Missing/nonempty milling routes and distance gates can affect execution;
manager count is not bird count. Every manager authors `Rnd Mil=10` and
`Rnd Fly=10`, whose interpretation and resulting population remain UNKNOWN.

For example, `\TNG\DATASCENE\RACETEST\ITALYS1.XML` authors FlightList=14
points and no nonempty MillList. Manager distance settings include Min Fly Dist,
Max Fly Dist, Min Mil Dist and Max Mil Dist. The selected metadata preserves
each course's values. `Bird Brown` is serialized **twice** per manager:
19 courses contain `(True, True)`, and 17 contain `(False, True)`. First/last
value selection by the runtime loader has not been determined, so a dictionary
that silently overwrites this property would lose evidence.

The resource side has `\TNG\DATAPSM\MISC\ANIMALS\BURDYBROWN.PSB` and
`BURDYWHITE.PSB`, each 720 decoded bytes. The existing strict PSB parser resolves
four mapped images, eight triangles, and texture names `burdybrown_000` or
`burdywhite_000`; matching GXI assets exist in the same directory. These are
valid sprite-bank structures, not authored 3D bird scene instances.
The manager-to-specific sprite selection and frame timing need bounded runtime
or executable proof. `HAWK.PSM` is an identical 44-byte stub to `NESSIE.PSM`,
with NaN header bounds, and does not establish a renderable hawk.

In the 36 paired PC scenes there are **84 authored bird-sound Eggs on 34
courses**, owned by `enAiSoundSource` with Sound values such as
`Environment\birds` and `Environment\birdsb`. They are sound sources, not
visual birds. No `gaAnimals_BirdManager` was found in the scanned PC scene
layer. Thus `AMBIENT_AI` has PS2 authored owner/route evidence, while the PC
sound counterpart is `PRESENT_ON_BOTH` as an ambient semantic family and
`DIFFERENTLY_USED`. Independent visual/runtime behavior remains UNKNOWN.

## Q2: airship and the larger shared spline fleet

All listed Eggs are `Use en2d=False`, `en3d Visible=True` and have
`AI No=0 / gaEntitySpline`. Their list is `IConManager`, except the ITALY3
barge uses `IContManager`. Resource paths are
`\TNG\DATAPSM\MISC\AIRSHIP\AIRSHIP.PSM` (6,760 decoded bytes),
`\TNG\DATAPSM\MISC\BARGE\BARGE.PSM` (6,939 bytes), and
`\TNG\DATAPSM\MISC\OBJECTS\DINGHYS\BLUEDINGHY.PSM` /
`REDDINGHY.PSM` (3,420 bytes each).

| PS2 course | Egg / model family | MarkerList / points | Authored speed | Loop / trigger |
|---|---|---|---:|---|
| TURKEYW | `barge` / barge | `bargelist` / 10 | 3 | False / False |
| ITALYS4 | `race zeppelin` / airship | `zeppelin` / 9 | 9 | True / False |
| ITALYS3FLIP | `boat` / dinghys | `boat1` / 7 | 3 | True / False |
| ITALY3 | `barge` / barge | `barge` / 11 | 3 | False / True |
| ITALYW2 | `boat` / dinghys | `boat` / 15 | 3.2 | True / False |
| FRANCEM | `zeppelin` / airship | `zeppelin` / 4 | 12 | True / False |
| SPAIN2 | `boat` / dinghys | `boat` / 6 | 3 | True / False |
| SPAINW | `boat1` / dinghys | `boat1` / 5 | 3 | True / False |
| SPAINW | `boat2` / dinghys | `boat2` / 5 | 3 | True / False |
| FRANCES2 | `boat1` / dinghys | `boat1list` / 6 | 3 | True / False |
| FRANCES2 | `boat2` / dinghys | `boat2list` / 7 | 2.5 | True / False |
| FRANCE1 | `boat1` / dinghys | `boatlist1` / 6 | 2.5 | True / False |
| FRANCE1 | `boat2` / dinghys | `boatlist2` / 4 | 2.7 | True / False |
| FRANCEWFLIP | `boat1` / dinghys | `boat1` / 6 | 3 | True / False |
| FRANCEWFLIP | `boat2` / dinghys | `boat2` / 4 | 3 | True / False |
| ITALYW1 | `zeppelin` / airship | `zeppelin` / 4 | 10 | True / False |
| SPAINS2 | `boat1` / dinghys | `boat1` / 7 | 8 | True / True |
| SPAINS2 | `boat5` / dinghys | `boat5` / 5 | 6 | True / True |
| SPAINWFLIP | `boat1` / dinghys | `boat1` / 5 | 3 | True / False |
| SPAINWFLIP | `boat2` / dinghys | `boat2` / 5 | 3 | True / False |
| ITALYS2 | `zeppelin` / airship | `zeppelin` / 6 | 12 | True / False |
| FRANCEW | `boat1` / dinghys | `boat1` / 6 | 3 | True / False |
| FRANCEW | `boat2` / dinghys | `boat2` / 4 | 3 | True / False |
| ITALYS3 | `boat` / dinghys | `boat1` / 7 | 3 | True / True |

`Use Const Speed`, `Use Closed Loop`, `Use Trigger System`,
`Max Speed/Const Speed`, `Trigger Dist On/Off`, `Use Rest On NonLoop`,
`Rest Time (sec)`, `Banking`, and `Number Of Samples=30` are real serialized
inputs. Speed values above are authored values; units and the exact curve
interpolator have not been proved. ITALY3 barge enables trigger gating at
400/1,000 authored distance, while TURKEYW barge has trigger gating disabled.
France1 boat1 has `Use Rest On NonLoop=True`, Rest Time=300 and Closed Loop=True;
do not infer how the runtime combines these settings.

The 36 paired PC XML scenes have no `gaEntitySpline` owners or standalone
airship/barge/dinghy model Eggs. However, PC France course models contain
embedded dinghy meshes/materials: see `course-dressing-survey.md`. Therefore
the supported delta is a separately controlled moving fleet versus PC bulk
course dressing, not proven PS2-exclusive boat visuals. No airship/barge names
were found in the scanned PC course TXT reports, but unnamed/baked geometry
and dormant executable support remain UNKNOWN. The fleet is `AMBIENT_AI` plus
`SCENE_PLACEMENT`, `CONFIRMED_BY_BYTES`; movement execution is UNKNOWN.

## Tumbleweed and haybales: authored physics versus actual response

There are **83 `gaAiRigidBody` Eggs on nine PS2 courses**: 58 haybales and
25 tumbleweeds. They contain Mass, MOI, Trigger Distance and Casts Shadow;
for example an ITALYS1 `Physics / haybale` Egg authors Mass=500,
MOI=`565 447 565`, Trigger Distance=5 and Casts Shadow=True.

| PS2 course | Haybale Eggs | Tumbleweed Eggs |
|---|---:|---:|
| ITALY2 | 11 | 0 |
| ITALYS1 | 14 | 0 |
| ITALYS4 | 10 | 0 |
| ITALYW1 | 10 | 0 |
| ITALYW2 | 13 | 0 |
| TURKEY1 | 0 | 7 |
| TURKEY3 | 0 | 6 |
| TURKEYM | 0 | 9 |
| TURKEYS2FLIP | 0 | 3 |

The two PS2 haybale resource aliases, `MISC\HAYBALE\HAYBALE.PSM` and
`MISC\OBJECTS\HAYBALES\HAYBALE.PSM`, are byte-identical 6,636-byte
payloads. They count as distinct scene placements, not distinct visual assets.
`MISC\OBJECTS\TUMBLEWEED\TUMBLWEED.PSM` is a nontrivial 9,819-byte payload
with `bigshrub $shader(treeblend)` and `Misc\Objects\Tumbleweed\shrubtrig2-tga`
printable references. The name does not prove its motion, wind coupling or
physical response. `gaAiRigidBody` on a named model with mass/MOI is authored
physics evidence (`PHYSICS_INTERACTIVE_PROP` candidate); successful activation,
collisions, knockability and solver response are **UNKNOWN**.

No matching standalone rigid-body owner was found in the scanned PC RaceTest
XML layer. PC has `Misc/Haybale/haybaletest.dx` and an associated TXT report
with `$chull(haybaletest)`, as well as baked Italian-course haybales and
`COLLIDE_haybale` nodes. Those establish asset/geometry/collision counterparts;
they do not establish PC dynamic-body activation or the same collision model.

## Other candidates and false-positive controls

**81 model-less `aiSpawnParticle` Eggs on 25 PS2 courses** have smoke-family
Egg names and authored transforms. The lack of serialized AI parameters means
the effect binding, rate and lifetime require executable/runtime evidence.
`PARTICLES\SMOKEY.GXI` exists, but no direct binding from these Eggs to that
texture is proved. The PC paired scene layer lacks this owner; PC particle
systems elsewhere and their resource names remain separate evidence. This
is a distributed `PARTICLE_SYSTEM` candidate, not 81 proved visible effects.

SPAINWFLIP contains a single ownerless `SplitTimes / SplitTime1-3` Egg with
model `misc\nessie\nessie`, Visible=True and translation
`1438.25 32.37 156.03`. Its resource is **only 44 decoded bytes**, byte-identical
to HAWK.PSM (SHA256 `339d5610a6a170f45fafc316d2ca7ae23bd9060ed8180f892efa8ea003d621ac`),
with NaN header floats and no material/texture strings. This is a referenced
stub/UNKNOWN candidate, not evidence of a visible monster or major feature.
It also explains why PS2 authored checkpoint model references total 431 rather
than an assumed 432: one checkpoint Egg has been assigned this stub instead.

The defensible large discovery is the route-controlled fleet and a wider
interactive/particle dressing layer. Deep PS2-AMBIENT1 can study the shared
gaEntitySpline contract, route sampling and trigger lifecycle once the full
survey ranks it against material/geometry deltas. No port is implemented here.
