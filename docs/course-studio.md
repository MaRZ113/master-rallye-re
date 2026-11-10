# Master Rallye Course Studio

Course Studio creates, edits and builds Master Rallye courses in Blender. It
replaces the COURSE-VIS1 inspector panels with one product: a single sidebar
tab, one project model, one build. The same core runs from the command line.

* Core library (no `bpy`): `src/master_rallye/studio/`
* Blender add-on: `blender/master_rallye_io/studio/` (add-on `master_rallye_io` 5.0)
* Command line: `tools/mr_course_studio.py`
* Getting started: [course-studio-getting-started.md](course-studio-getting-started.md)
* Qualification: [course-studio-qualification.md](course-studio-qualification.md)

## 1. Project model

`master_rallye.studio.model.CourseProject` (schema `mr-course-studio-project/2`)
holds everything a course is: meshes with a role, materials, textures, start and
finish areas, checkpoints, the AI route, limits, pace notes, sound sources,
environment, build settings, provenance and an operation history. On disk it is
a folder: `project.json`, `geometry.bin` (all mesh arrays) and `blob-*.bin`
(binary data such as a recovered native object tree). Paths are relative to the
project folder or the resource root; no install path is stored as a requirement.

Positions are game space (the RaceTest/DX frame, Y up). Blender shows game
`(x, y, z)` as `(x, -z, y)`. Headings are degrees, 0 = game +Z.

| Role | In the game |
|---|---|
| `terrain` | drawn, collision tree, surface database (`$bsp/$draw $landdb`) |
| `terrain_hidden` | collision tree + surface database, not drawn (Retail `$landdb fill`) |
| `visual` | drawn only (`$objects`) |
| `collision` | collision tree only (`$bsp/$nodraw`): walls, proxies, blockers |
| `water` | drawn + surface database, never solid (Surface.xml `Solid=False`) |
| `physical` (Blender) | movable rigid body of the optional Renderer RigidProps module |

Inside Blender the objects in the `MR Course` collections are the source of
truth; saving the `.blend` also writes the project folder next to it
(`<name>_mrcourse/`). Reopening restores objects, materials, settings, links to
game textures and the binary blobs.

## 2. Native course DX writer (`dx_build.py`)

The writer emits the complete course DX for any topology. Its contract was
recovered from `invspaingx.dx`, which Retail `MRallye.exe` cooked from a GXM we
wrote, and from a census of Retail course records against their TXT names:

| Part | Contract |
|---|---|
| Header | `0xD00D, 135, 1337, vertex count`; positions, normals, BGRA colours, 2 UV sets, u16 local indices |
| Draw table | envelope `(1, n)` of tag-2 records, one per material, split at 65 536 local vertices |
| Record core | `vertex base, local max, index start, index count, address, effect, mip, flags, slot mask` |
| address | 1 wrap, 2 `$clamp(u)`, 4 `$clamp(v)`, 0 `$clamp(uv)` |
| effect | 0, 1 water/puddle, 2 scrolling (`$shader(waterall)`, `$scroll`) |
| flags | blend (slot-0 UsesAlpha), alpha test (`$alphatest()`), 1, 1 |
| slot mask | bit0 base, bit1 vertex lighting, bit2 environment (metal), bit3 noise, bit4 water |
| Order | opaque, water, blended, alpha-tested |
| Winding | render `(b, a, c)` of the authoring triangle |
| Noise UV | `(x, z) / 37 + 0.5` with integer shifts of 5 |
| tag100 | solid-leaf collision BSP (section 3) |
| tag1339 | render AABB centre, farthest-vertex radius, AABB |
| tag1400 | land records `(c, b, a)` + plane `n,d`, material-name strings, 20-unit z-major cell grid by triangle AABB |

`tag1500`, present only in Retail files, is a sector visibility graph (2-D
convex sectors with per-edge neighbour links and visible-sector lists) used by
the Retail hierarchical render batches. The Retail cooker's own flat layout has
none, and a course cooked that way was played by the owner (invspaingx), so
Studio writes the flat layout.

Golden test: the same GXM through the game's cooker and through Studio yields
the same 74 draw records (texture slots and every field), the same land grid
(167 x 103, all cells), the same 14 surface strings and land records within
the cooker's float rounding (< 5 mm). The only intended difference: Studio
drops zero-area triangles; the cooker keeps them as NaN-plane land records.

Every build re-reads its DX with the independent Retail-format parsers.

## 3. Collision

* **Build**: terrain faces (code = land record index) + collision objects +
  optional map-edge closure (`close_land`, Retail `$skirt`) -> solid-leaf BSP
  with polygon clipping (`course_bsp.build_solid_bsp`).
* **Solid union** (`bsp_union.py`): a solid-leaf BSP from a polygon soup is only
  correct when every face separates solid from empty. Buried parts of objects are
  clipped against the terrain tree; terrain and other objects inside a closed
  object are clipped against its tree. A building sunk into the ground is solid
  inside (the E2.2 hole cause).
* **Edited Retail courses** (`native_graft.py`): import keeps the native tree's
  object cells (solid convex cells above the ground). The build grafts the new
  terrain, Studio objects and closure into every empty cell of that object tree:
  the result is exactly `native object OR new ground`. If the user edits the
  recovered native collision mesh, Studio falls back to the solid union of its
  closed cells and says so.
* **Probes** (`validate_tree`): the game's own query (`s = n.p + d`, `s <= 0`
  back) on a grid: holes under the surface (error next to the AI route, warning
  elsewhere), solid space just above the surface, walls on the AI route (solid at
  1.2/2.2 m: error), steps (solid only at 0.5 m: warning), buried collision faces.
* **Differences**: points where two builds disagree; **game collision preview**:
  the exact solid/empty boundary around the 3D cursor; **probe at cursor**.

## 4. Gameplay

* **Start/Finish**: the four native `Marker Pos` corners; the grid is placed by
  the game (0x48EB40).
* **Checkpoints**: Master Rallye's checkpoint *is* `gaRaceSplitTimeAI` (Split
  Time ID, trigger Radius, ExtraTime added to the countdown shown by
  `gaHudAiCheckPoint`) plus four `misc\checkpoints\checkpoint` boards;
  `gaRacePostFirstSplitTimeAI` gets `numberOfSplitTimePoints` and
  `TimeToFirstCheckpoint`. "Add Checkpoint" creates exactly that.
* **AI**: native AI data is the RaceLine list and `DataScene/ICont/<key>.sfl`.
  The SFL is synthesised with the pure-pursuit model fitted to Retail fields.
  "Preview AI Path" traces a car steering by the field. One native route exists;
  extra route curves are variants with one active route.
* **Limits** (gaLimitsAI resets): road corridor (Retail medians 20..45/30..75 m),
  open terrain (150/300 m, free off-road driving) or four editable curves.
* **Pace notes**: `gps_arrow` eggs with a graphic ID; automatic placement uses the
  Retail statistics of IDs by turn direction; every note is editable.
* **Environment**: a Retail scene supplies sky, physics, cameras, HUD, managers;
  place-bound sound sources are replaced by the course's own.

## 5. Materials and surfaces

Shaders: ground, object, sign, metal, tree, water, puddle, waterall. Surface
types are the ten rows of `DataGame/Surface.xml` (friction, restitution, track
texture, solid), shown in the editor; the physics reads the first
`$surfacetype(...)` of a land record's string. Textures are FEED containers
(`0xFEED, 1, crc32(payload), w, h` + bottom-up BGRA32); any image is accepted
and conformed to a power of two. Unchanged imported materials keep their exact
Retail names.

## 6. Build (`build.py`)

Validate -> DX (+ re-read) -> collision probes -> textures -> RaceTest -> SFL ->
HNT -> stage -> re-read staged tree -> COURSE-CAP2 rows -> publish with
`os.replace` (previous build kept as `.previous`). Output:
`resource-root/` (DX, TXT, textures, RaceTest XML/HNT, ICont SFL),
`courses.json` + `compose.json` (accepted CAP2 input with this course added;
fresh private profile), `course-build.json` (hashes, reports, all findings),
`optional/` (Renderer RigidProps asset when physical objects exist).
"Make private game package" runs `tools/build_course_registry.py`
(private output under `.research-output/course-cap2/`, Python with `capstone`).

## 7. Physical objects (optional Renderer module)

Hay bales, tumbleweeds, checkpoint barrels and new models made from any Blender
mesh (model + convex hull + texture; mass, inertia, wake distance, shadow) are
written into a PS2RGD02 asset: the 36 PS2 courses plus the Studio course. The
course itself never references the asset: its game files are byte-identical
with and without physical objects (Blender qualification B). The accepted
Renderer loads only its pinned asset digest; branch
`feature/course-studio-rigid` adds `RigidPropsAssetSha256` (INI-declared digest,
same layout validation). Limits: 16 models, 16 textures, 32 props per course.

## 8. Large and merged courses

Terrain tools: carve road along the route, join terrains with weld, snap open
edges to a neighbour, find gaps, split into sections. One DX and one collision
tree are written for the whole course (only the first landscape egg collides,
E1.6). Validator budgets: ~250 textures (Retail crash above ~256), DX size,
land records. Draw records split automatically at 65 536 vertices.

## 9. Command line

```
python tools/mr_course_studio.py new <dir> --name MyCourse --template valley
python tools/mr_course_studio.py import-retail <dir> --race France1
python tools/mr_course_studio.py import-obj <dir> --obj terrain.obj --role terrain
python tools/mr_course_studio.py validate <dir> --collision
python tools/mr_course_studio.py build <dir> --catalog <CAP2 build-input.json> [--cap2]
```
