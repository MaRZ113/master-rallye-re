# Narrow PC semantic comparison and future interfaces

The Course SDK worktree remains read-only at
`4244fa0c4d878523c9947f54816bf377cdfb2589`. This phase does not change its
Blender add-on, course writer, PC renderer, runtime or game data. CDELTA1's
paired-course/compiled-geometry evidence is reused, and four selected retail
PC sidecar hashes were freshly rechecked.

| Matched PC course | Ground material/texture examples | Additional detail directive |
|---|---|---|
| France1 | Material1/2 harddirt: GRASS_LEFT/RIGHT; material3 grass: GRASS; gravel blends GRASS_ROCK_LFT/RHT | Absent in checked sidecar bytes |
| Italy_S1 | Material35 harddirt I2A_ROAD;36/37 I2A_DIRTBLEND1L/R;38 grass I2A_GRASS | Absent |
| Turkey_s1 | Material0 harddirt GRAVEL_ROAD;1/2 GRASS_TO_MUD/MUD_TO_GRASS;3 grass BASEGRASS | Absent |
| Spain1 | Harddirt ROCKYPASSSW/SANDGRASS; grass ITALIAN GRASSSW and blends | Absent |

These are surface/texture-family correspondences, not a certified one-to-one
PS2 spatial-triangle↔PC draw assignment. Source ground geometry exists in the
PC course resources and the SDK can decode geometry/material metadata. Exact
cross-platform source triangulation, spatial partition equivalence and a
runtime draw-to-detail category interface remain unproved. No assertion that
PC lacks every possible vegetation mechanism is made.

The PS2 input is not just a grass texture: it includes **source triangle →
spatial material → detail category** plus geometric eligibility and regional
generation. Existing PC draw packets are not shown to retain that category.
A D3D8 wrapper cannot be assumed to recover it from texture names, surface
type or draw order. Future work needs an explicit interface carrying terrain
positions/indices, material identity/detail category and activation/observer
state. Course SDK annotation/extraction and runtime ownership may supply that
interface, but neither is implemented now.

| Planning classification | Current evidence / missing interface |
|---|---|
| ASSET_REUSE | GRASS1/BUSH1 image candidates and binding proved; original images stay external |
| MATERIAL_METADATA_EXTENSION | Needed to represent detail IDs independently of ground texture/surface type |
| COURSE_SDK_EXTENSION | Possible export of terrain source + material identity/category; mapping contract still required |
| RUNTIME_GEOMETRY_GENERATION | CPU grid/jitter/plane and incremental pools strongly justify this layer |
| D3D8_PROXY_RENDER_FEATURE | Possible later draw consumer after an explicit source/category interface; not automatically sufficient |
| ENGINE_RUNTIME_HOOK | Possible observer/lifetime/source access; actual PC hook is UNKNOWN |
| REQUIRES_DEEPER_RE | Exact embedded-program upload/residency and final flush, exceptional arithmetic and full activation replay |
| UNKNOWN | Exact PC architecture choice, visual parity, desired quality controls and cross-platform triangle equivalence |

A future implementation should preserve the original grid/hash behavior before
introducing configurability. An attractive barycentric field, crossed quads or
wind model would be a new feature unless independently supported. Only a small
PS2 source subset and detail VU residency contract need further recovery; a universal PSM
editor/GS emulator is not a prerequisite.

Treeblend is a separate shader lead. Mode11 is directly selected by this owner;
no treeblend property consumption was found in it. Explicit scene plants and
prebaked foliage remain separate from this material decorator. Shared spatial
and texture/state infrastructure could be useful for later terrain effects,
but does not establish the same generation algorithm for water or puddles.
