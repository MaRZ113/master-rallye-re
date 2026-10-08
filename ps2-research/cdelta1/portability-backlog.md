# Portability backlog after CDELTA1

This is an evidence-ranked research backlog. Layer assignments are
portability hypotheses, not implemented features or demonstrated PC
activation paths. Exactly one next deep phase is selected in `next.md`.

## Ranking method

Impact, frequency, uniqueness and evidence use a 1–5 scale, where 5 is
strongest. Cost and PC complexity use 1–5, where 5 is hardest. Frequency is
based on authored course coverage when available; it is not screen-time or
runtime visibility. Evidence scores reward concrete scene/resource chains
and parsed geometry, without treating source records as runtime proof. These
ordinal judgments support the decision; they are not measured effort or a
promise of visual quality.

| Priority / candidate | Visual impact | Course frequency | Uniqueness | Evidence | Research cost | PC complexity | Reason and unresolved causal question |
|---|---:|---:|---:|---:|---:|---:|---|
| 1. PS2-AMBIENT1: spline-owned boats, barges, airships | 4 | 4 (17/36) | 5 | 4 | 2 | 4 | 24 entities and explicit path-list inputs expose a shared missing ownership layer. Which constructor/update path consumes each list and produces world transforms? |
| 2. PS2-CHECKPOINT1 / rigid props | 4 | 5 (checkpoint scenes 36/36; rigid props 9/36) | 5 | 3 | 4 | 5 | User-observed knockable barrels and 83 authored rigid-body candidates have gameplay significance. Which visual/checkpoint constructor creates dynamic bodies, and what differs from PC? |
| 3. PS2-GRASS1 | 5 | 5 (broad course material coverage) | 4 | 3 | 4 | 4 | Material `$detail(...)` and grass/bush resources give a concrete input surface. How are positions, density, culling and animation generated? |
| 4. PS2-WATER1 | 4 | 5 (PS2 material candidates 34/36; PC water-family metadata 33/36) | 3 | 4 | 3 | 4 | Most water-family content already exists on PC. Is the visible delta shader semantics, extra geometry, or both? Turkey3 is a bounded material/geometry candidate. |
| 5. PS2-AMBIENT1: visual birds | 3 | 5 (36 authored managers) | 4 | 3 | 3 | 4 | BirdManager and flight/milling inputs exist across the full course set. Which resources and runtime populations are selected, especially with an empty HAWK payload? |
| 6. PS2-REFL1 | 4 | UNKNOWN | 3 | 2 | 4 | 4 | Environment material evidence supports a renderer hypothesis. Which surface classes actually draw reflections, and what compositing/state differs from PC? |
| 7. PS2-PARTICLE1 candidate | 3 | 4 (81 `aiSpawnParticle` owners in 25/36) | 3 | 2 | 3 | 4 | Authored effect ownership is broader than a rare prop. Emission, particle selection and visible contribution need classification before ranking it as a major feature. |
| 8. PS2-DRESSING1 | 4 | UNKNOWN for total population | 3 | 2 | 5 | 3 | XML proves extra props, while landscape tree counts remain unavailable. Decode grouped geometry/LOD before deciding what course data actually needs porting. |
| 9. PC-PS2MAP1 | 3 | 5 (shared course RaceLine concept) | 2 | 4 | 2 | 3 | The PS2 procedural map and PC ordered RaceLine are already understood semantically. A future PC overlay can consume the PC sequence; it does not require binary layout identity. |
| 10. PS2-UI2.1, deferred | 2 | HUD-wide | 2 | 3 | 4 | 4 | Remaining COP2 sprite projection/video-offset ownership belongs to the prior UI track and should not displace course-content work. |

Spline-owned ambient objects outrank a fixed Grass → Water → Reflections
sequence because one bounded runtime question spans three distinct visible
families, 17 courses and multiple independently authored path lists. It is a
larger structural discovery than finding another isolated asset. The survey
does not claim its eventual pixel impact exceeds grass everywhere.

## Feature-to-layer hypotheses

| Feature | Classification | Proposed port layers | Dependencies and boundaries |
|---|---|---|---|
| Moving dinghies, barges and airships | `AMBIENT_AI`, `SCENE_PLACEMENT` | `COURSE_DATA_PORT`, `COURSE_SDK_EXTENSION`, `PC_RUNTIME_HOOK`, `REQUIRES_DEEPER_RE` | Need PS2 spline evaluator, timing/loop rules, world-transform consumer and model decode/conversion. PC embedded dinghy geometry is a possible source; no dormant PC spline owner is proved. |
| Visual bird flocks | `AMBIENT_AI`, possible `RUNTIME_GENERATED` | `PC_RUNTIME_HOOK`, `COURSE_DATA_PORT`, `REQUIRES_DEEPER_RE` | Need BirdManager resource selection/population/update. PC bird sound sources are shared ambience, not a ready visual system. |
| Rigid haybales and tumbleweed | `PHYSICS_INTERACTIVE_PROP` candidate | `PHYSICS_WORK`, `PC_RUNTIME_HOOK`, `COURSE_DATA_PORT`, `REQUIRES_DEEPER_RE` | Mass/MOI/trigger fields are authored. Physics behavior, collision ownership and player interaction remain untested. PC haybale test asset and embedded hay meshes do not demonstrate dynamic activation. |
| Checkpoint barrels/banner | `SCENE_PLACEMENT`, `RUNTIME_GENERATED`, physics candidate | `GAMEPLAY_PATCH`, `PHYSICS_WORK`, `COURSE_DATA_PORT`, `REQUIRES_DEEPER_RE` | Preserve split trigger/radius semantics while separating generated visual assets and bodies. User runtime observation is the barrel-interaction evidence; a visual asset swap alone is insufficient. |
| Grass/shrubs/stones detail | `MATERIAL_DETAIL`, possible `RUNTIME_GENERATED` | `D3D8_PROXY_RENDER_FEATURE`, `PC_RUNTIME_HOOK`, `COURSE_SDK_EXTENSION`, `REQUIRES_DEEPER_RE` | Recover deterministic placement/material consumption. PC `$grnd`/surface directives are potential semantic inputs, not a proven equivalent generator. |
| Water/puddle renderer | `RENDERER_SEMANTICS`, `COURSE_GEOMETRY` candidate | `D3D8_PROXY_RENDER_FEATURE`, `COURSE_DATA_PORT`, `REQUIRES_DEEPER_RE` | Existing PC water-family materials and decoded geometry reduce asset work. Turkey3's PS2 water/puddle records need PS2 draw/geometry proof before claiming extra placement. |
| Reflection/environment use | `RENDERER_SEMANTICS` | `D3D8_PROXY_RENDER_FEATURE`, `REQUIRES_DEEPER_RE` | Identify exact surfaces and rendering state before promising water or world reflection parity. |
| Extra static landscape dressing | `COURSE_GEOMETRY`, `SCENE_PLACEMENT` | `COURSE_DATA_PORT`, `COURSE_SDK_EXTENSION`, `REQUIRES_DEEPER_RE` | Require comparable instance/group/LOD decoding; texture and filename totals cannot decide population. |
| Authored particle effects | `PARTICLE_SYSTEM` | `PC_RUNTIME_HOOK`, `COURSE_DATA_PORT`, `REQUIRES_DEEPER_RE` | Owner occurrence is known; actual emitter/material/renderer linkage and visual effect remain bounded open questions. |
| PC minimap using existing RaceLine | `SHARED_SEMANTIC_DATA`, `HUD_UI` | `D3D8_PROXY_RENDER_FEATURE`, `PC_RUNTIME_HOOK` | Ordered PC Marker Pos XYZ can supply a future map. PS2 gaHudAiMap's runtime record layout differs; do not copy its byte layout into PC. |
| Reusable isolated model/texture | `ASSET_ONLY` | `EASY_ASSET_PORT` only after format proof | A decoded image/model may be technically reusable. Course placement, ownership, scale, collision and activation still need their corresponding layers. No proprietary asset is committed. |
| Nessie reference | `SCENE_PLACEMENT`, `UNKNOWN` payload role | `UNKNOWN` | 44-byte payload is identical to HAWK stub. There is no creature mesh or runtime behavior to port on current evidence. |

`COLLISION_ONLY` and `PHYSICS_INTERACTIVE_PROP` remain distinct: a mesh name or
collision record does not prove mass, dynamic integration, knockability or
reset behavior. A proposed renderer layer likewise does not imply gameplay
ownership is solved.

## Already understood versus still unresolved

PackFS resolves exact named PS2 resources; the survey adds authored XML
owners/placements and material-family comparisons. UI2 supplies the semantic
PS2 map producer and its ordered RaceLine input. PC Course SDK already reads
ordered RaceLine markers, explicit Eggs and compiled render geometry; its
current authoring scope stays unchanged.

Future work can use those facts without rerunning PackFS, static HUD reverse
or the procedural map algorithm. Spline evaluation, rigid-body activation,
detail placement, PS2 grouped course geometry and renderer water/reflection
semantics remain deeper reverse-engineering tasks. No port, asset mutation,
Course SDK change, runtime patch or deployment is part of CDELTA1.
