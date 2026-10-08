# PS2-CDELTA1 findings

**COMPLETE as a bounded content/visual-delta survey.** This is static resource,
scene and parsed PC geometry evidence, with historical screenshot correlation
and separately attributed user gameplay observations. No independent runtime
run, port or Course SDK change occurred.

The strongest new discovery is a shared authored movement layer: **24
gaEntitySpline Eggs across 17 courses**, including 18 dinghies, two barges and
four airships. Its model resources are nontrivial, the path lists are nonempty,
and XML supplies speed/loop/trigger/rest/banking settings. Runtime interpolation
and execution remain unresolved. The selected next reverse is PS2-AMBIENT1,
narrowly defined around that shared contract.

## Coverage and identity

81 PS2 DataScene XML resources, all 36 RaceTest scenes and their 36 actual
landscape PSMs were read through canonical PackFS. PC coverage is 7,595
inventory files, 99 DataScene XML, 41 RaceTest XML including tests/templates,
36 course TXT sidecars and four decoded DX samples. Comparison counts use
the 36 confidently paired canonical PC scenes, not the extra five.

All 36 pairs are STRONG. The internal landscape name normally agrees; Italy1's
PS2 italy1 / PC track01 alias is proved by its 213 identical ordered positions.
35 route comparisons have identical compared XYZ; ItalyS1 has two differing
points among 292 compared. PS2 has one or two extra route records. Therefore
the files and full route hashes are not declared identical or EXACT. Pairing
does not fit, sort or reverse coordinates. See course-pairs.json/.md.

## Questions answered

| Question | Answer / evidence boundary |
|---|---|
| Q1 birds | 36 gaAnimals_BirdManager owners, 542 FlightList points on 36 courses and 55 nonempty MillList points on ten. BURDY sprite banks structurally valid; manager-to-species producer remains UNKNOWN. PC counterpart includes sound Eggs, not the same visual owner. Duplicate Bird Brown values retained. |
| Q2 airship | Four real model Eggs with gaEntitySpline and paths. Same owner controls 18 dinghies and two barges. Assets are actively referenced, movement inputs authored, execution UNKNOWN. |
| Q3 checkpoints | PS2 selects objects/checkpoints drum/metal payload; PC selects legacy checkpoint asset. 431 versus 440 authored visual companions; 108 versus 110 split trigger owners. Visual Eggs lack gaAiRigidBody. Knockability is USER_RUNTIME_OBSERVATION, body/collision/banner ownership UNKNOWN. |
| Q4 grass | Every PS2 landscape contains grass/shrubs/none detail directives; stones on seven France models, singular shrub on Turkey_S1. None in 36 PC material reports. Terrain textures/surface metadata exist on PC; procedural detail interpretation is inference until consumer reverse. |
| Q5 extra dressing | 58 haybales and 25 tumbleweeds with rigid owners, 24 spline objects, and 81 smoke-named emitters. Comparable XML prop counts proved; total grouped/LOD tree and plant populations UNKNOWN. PC already embeds hay and dinghy meshes. |
| Q6 water | PS2 compiled course material references, PC sidecars and decoded France1/ItalyS1 water draws go beyond filenames. Turkey3 has a PS2 puddle/water material candidate with zero named PC water bindings in 939 validated draws; PS2 surface binding remains UNKNOWN. |
| Q7 larger discoveries | Fleet ownership, rigid haybales, distributed smoke, Turkey3 discrepancy and treeblend survived novelty screening. Nessie/Hawk are identical 44-byte stub candidates, not a proved monster/hawk. |
| Q8 PC dormant/shared | Standalone haybaletest render/hull resource exists without a scene reference; Italian hay and French dinghy geometry already present; water geometry and bird ambience already shared. PC dynamic activation is unproved. |

## Shared RaceLine and future map

Ordered Marker Pos XYZ is a semantic bridge between both course authoring
systems. Existing UI2 proves PS2 gaHudAiMap reads RaceLine and produces
procedural untextured strokes. PC gaRaceLineAI and Course SDK already retain
ordered marker positions. Full file hashes, endpoint counts and runtime record
layouts differ; do not copy PS2's 80-byte in-memory record into PC. **PC-PS2MAP1**
is backlog only. No minimap or HUD implementation was started.

## What remains unknown

PSM material-to-draw/instance grouping, total tree counts, exact treeblend/wire
semantics, spline update/timing, visual BirdManager binding, physics activation,
checkpoint body registration, smoke emission and reflection behavior need
deeper work. These do not invalidate scoped XML/material survey metrics.

No PS2_ONLY_CONFIRMED feature is asserted. Missing owners/directives/families
are NOT_FOUND_IN_SCANNED_PC_CORPUS with explicit layer bounds. Collision mesh
names and Hitable flags are not dynamic physics proof. Resource references and
Visible flags are not successful draws. Screenshot camera/build/course identity
is insufficient to upgrade a static claim.

See delta-matrix.md/.json, the five novel candidates, individual surveys,
portability-backlog.md, validation.md and next.md. CDELTA1 stops after commit.
