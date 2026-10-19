# W5 and W6: moving objects, birds and physical props

## What PS2 has and PC lacks
Counted over the 36 PS2 RaceTest XML (`build_objects.py` report, `LOGIC-PORT.md`):

| PS2 class | Eggs | Courses | What it is | In `MRallye.exe` |
|---|---|---|---|---|
| `gaEntitySpline` | 24 | 17 | dinghies (blue, red), barges, airships on Catmull-Rom routes | no |
| `gaAnimals_BirdManager` | 36 | 36 | bird flocks from `FlightList` / `MillList` (sprite birds) | no |
| `gaAiRigidBody` | 83 | 9 | hay bales (Italy, mass 500) and tumbleweeds (Turkey, mass 5) | no (PC has `gaAiHayBale`, which crashes in the contact code, `track-delta1/HAY-PROBE.md`) |

Sound sources, clouds and camera managers exist on PC and are handled by the XML writer (W4). The static hay stacks and moored boats
that are part of the PS2 landscape scene are already in the course render (W2): for example 14 hay meshes (4,820 triangles) on Italy2. The
Eggs above come on top of them.

Because the classes are missing, no XML edit can bring the behaviour. Writing their AI names into a PC XML is not tried: at best the engine
ignores them, at worst it fails on load.

## Done offline now
`build_objects.py` -> `research-output\course-objects-1`:
- PC models of the PS2 objects in `DataGx\Misc\PS2Port\<name>\`:

  | Model | Triangles (PS2) | Template | Textures |
  |---|---|---|---|
  | bluedinghy, reddinghy | 24 | `haybaletest.dx` | PC `dinghy-tga` |
  | airship | 60 | `haybaletest.dx` | white 8x8: the PS2 material is `$shader(notexture)`, read as vertex colour only from the shader name |
  | barge | 81 (2 textures) | `checkpoint.dx` (2 draws) | PC `basegravel-tga`, `plating2-tga` |
  | haybale | 60 | `haybaletest.dx` | PC `hay-tga` (the PS2 second layer `hay_env` has no PC file and is dropped) |

  The geometry follows the course render rules: the PS2 strip rule, PC corner order, PS2 normals, colours and raw UV. Every triangle is also
  stored reversed, because PS2 draws objects without back-face culling. Texture names in the template slots keep their length, so a few
  files have short aliases (`din-tga.dxt`).
  Not converted:
  - the `misc\objects\haybales\haybale` alias, byte-identical to the hay bale;
  - the tumbleweed: `$shader(treeblend)` needs an alpha material and there is no loose-model alpha template yet.
- Optional static stand-in for the 24 spline objects, made with `--static-splines`: a plain Egg (no AI) per object, at the PS2 start pose of
  its route. The pose follows the PS2 owner code (`ambient1/transform-pipeline.md`):
  - position = first route marker;
  - forward = the secant to the second marker;
  - up = (0, 1, 0);
  - right = (G.z, G.y, -G.x).

  The XML goes to `course-objects-1\<Course>\DataScene\RaceTest\<Course>.xml`; it extends the W4 XML of the package. The objects stand still,
  so this only shows that the models load and sit in the right place. It does not reproduce the PS2 behaviour.
- `objects-report.json` contains every spline object's parameters and its route points, ready for a native controller.

## What needs native code (not started)
Proposed as one small component of its own (no dependency on the modernization proxy), loaded with the course and driven per game tick:
1. **Spline objects (W5a).** Find the stand-in Egg by name, then write its en3d matrix every tick:
   - inputs: the route, `Max Speed/Const Speed`, `Use Closed Loop`, `Rest Time`, `Banking` and the trigger distances;
   - the evaluator: the PS2 Catmull-Rom, clock and banking rules, already written down and checked offline in `ambient1/` (`spline-algorithm.md`, `transform-pipeline.md`);
   - this needs the PC Egg/entity matrix offsets and a per-tick hook in `MRallye.exe` (not reversed yet).
2. **Birds (W5b).**
   - available: the flight equation, the RNG order and the animation keys from `ambient2/`;
   - missing: the PS2 sprite banks still need conversion into PC images, and a PC sprite/quad draw path has to be found or added.
3. **Physical props (W6).**
   - the PC physics manager must accept new bodies;
   - the existing `gaAiHayBale` path crashes in the stock contact code (`0x006363C0` -> `0x004FFDE0`, NULL pooled contact record), so the
     contact pool contract is the first thing to reverse;
   - available: the PS2 side (mass, inertia, convex shapes, wake and sleep rules) in `rigid1/`;
   - the hay bale model above is ready; the tumbleweed model needs the alpha template.

Each of these needs the game running to verify, so they are listed here rather than built blind.

## Game test (optional, independent of the rock issue)
Install `course-port-36\FranceM` (or any course from the table in the report), then copy `course-objects-1\DataGx\Misc\PS2Port` and
`course-objects-1\FranceM\DataScene\RaceTest\FranceM.xml` over it. Things to check:
- the course loads;
- the airship stands near its route start (-926, 158, 1262);
- the model looks right: white body with the PS2 vertex colours, both sides drawn.
