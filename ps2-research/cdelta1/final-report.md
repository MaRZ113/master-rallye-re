# PS2-CDELTA1 closeout

| Field | Result |
|---|---|
| Repository / branch | D:\Game\Master Rallye\master-rallye-re-general / master |
| Starting HEAD | a8d9930438e70db979d2f3baf722c1f44e634cf4 |
| End HEAD / commit | Commit containing this report: research: survey PS2 and PC course content deltas; exact resulting hash in Git metadata and chat |
| Preflight | Clean general worktree; existing branch reused; required baseline/SDK references reviewed |
| PS2 corpus | All four canonical inputs hash/size matched; 3599-file manifest; originals unchanged |
| PC corpus / SDK | Curated retail Data.sma_unpacked; 7595 paths, 99 XML, 41 RaceTest, 36 course TXT, 4 decoded course DX; SDK reference 4244fa0, unchanged |
| PS2 coverage | 81 DataScene XML, 36 RaceTest, 36 actual landscape PSMs; named ambient/checkpoint resources |
| Course pairs | 36 STRONG; Italy, France, Turkey and Spain all covered; internal identity plus ordered spatial evidence |
| Delta catalog | 16 records including known leads/shared semantics/overlapping subfamilies and one rejected stub control |
| Novel candidates | Five substantive discoveries; no padded top-ten list |
| Birds / airship | 36 bird managers; 542 flight/55 milling markers; four airship placements with paths |
| Checkpoints | Changed PS2 drum/metal resource; 431 visual references versus 440 PC, separate split triggers; knockability user-observed, physics owner UNKNOWN |
| Detail / water | Detail directives all 36 PS2; water-family metadata PS2 34 / PC 33; PC water geometry proved; Turkey3 surface candidate remains unbound |
| Extra dressing | 58 haybales + 25 tumbleweeds with rigid ownership; 24 spline models; 81 smoke-named emitters; total trees UNKNOWN |
| RaceLine | Ordered XYZ semantic bridge, not identical files/layouts; PC-PS2MAP1 backlog only |
| Highest-value new finding | Shared spline-controlled fleet: 18 dinghies, 2 barges, 4 airships on 17 courses |
| Best next phase | Exactly one: PS2-AMBIENT1, bounded gaEntitySpline input/update/world-transform contract |
| Tests | Baseline 80 PASS; final 98 unittest PASS, zero skips; 18 pytest PASS, 22 subtests PASS |
| Compile / diff / determinism | PASS / PASS / eleven generated outputs byte-identical on rerun |
| Originals / Course SDK | PS2 and read PC source hashes unchanged; SDK clean before/after; no authoring/Blender changes |
| Push / scope | No push, port, asset mutation, renderer/gameplay implementation or next phase started |
| Status | COMPLETE bounded survey; runtime/PSM-instance/physics questions explicitly UNKNOWN |

## Ranked findings

| Priority | Finding | Supported conclusion | Practical limit |
|---|---|---|---|
| 1 | Spline ambient fleet | One owner spans 24 models on 17 courses, with explicit nonempty routes and loop/trigger/speed settings | Execution and spline evaluator not reversed; some PC dinghies already baked into scenery |
| 2 | Rigid hay/tumble layer | 83 authored dynamic-body candidates on nine courses, with mass/MOI/trigger fields | Contact, wind, activation and knockability untested; PC hay collision/visual content already exists |
| 3 | Detail vegetation | Course material detail interface widespread on PS2, absent from scanned PC material names | No generator/density/culling/wind proof; no grass blade/tree population comparison |
| 4 | Checkpoint visuals | Different selected model/material resource, separate shared trigger semantics | User knockability report not independently confirmed; no rigid owner on checkpoint Eggs |
| 5 | Smoke ownership | 81 model-less smoke-named particle Eggs on 25 courses | Resource binding/emission/visible result UNKNOWN |
| 6 | Water/puddle | Existing PC decoded water draws; Turkey3 has a meaningful named-material discrepancy | PS2 extra surface versus relabeling/unbound material UNKNOWN |
| 7 | Treeblend | 14 PS2 course families; France1 bush material differs from same PC texture family | Rendering effect and plant population UNKNOWN |

See delta-matrix.md/.json for all 16 records, course-pairs.md/.json for all
36 comparisons, and novel-candidates.md for five non-overlapping discoveries.
Counts use documented compatible metrics; overlapping fleet rows are not summed.

## Evidence separation

**PROVED / CONFIRMED_BY_BYTES:** canonical resource paths and ranges, selected
decoded hashes, authored XML references/owners/parameters, ordered spatial
agreement, material strings, PC sidecar records and decoded PC draw geometry.
PS2 bird banks validate structurally as PSB resources. No new executable reverse
was required; prior PackFS/UI2 executable evidence retains its original scope.

**LIKELY / STATIC_INFERENCE:** spline-controlled visible movement, material-driven
detail generation, dynamic hay/tumble behavior, foliage-renderer differences
and additional Turkey3 water geometry. Authoring inputs support these candidates;
their runtime producers/consumers are not newly proved.

**USER-OBSERVED / USER_RUNTIME_OBSERVATION:** PS2 yellow checkpoint barrels can
be knocked down while PC markers do not collide, according to the user. Static
Hitable=True on both platforms does not prove or refute the gameplay observation.

**SCREENSHOT_CORRELATION:** six historical JPEGs, also found byte-identical in
PS2.zip, corroborate turf/detail and a broad water surface. No exact capture
build/course/frame/camera binding; no new major ambient object independently
identified. No geometry was traced from screenshots.

**UNKNOWN:** actual runtime movement/physics/emission, PSM draw-to-material and
group/LOD instance decoding, total tree population, checkpoint automatic body
registration/banner construction, reflection contract and dormant PC activation.
No PS2_ONLY_CONFIRMED or new independent runtime result is asserted.

## False-positive and scope controls

Nessie looked like an unusually large discovery in SPAINWFLIP XML, but its PSM
is identical to HAWK's 44-byte stub candidate. It is not a proved creature.
PC course TXT has embedded dinghy/hay meshes, and a dormant haybaletest hull
asset; absence of standalone XML references is not absence of that visual family.
Repeated PSM material strings, filenames, draw partitions and collision names
are never converted to visible-object counts or dynamic-physics proof.

The survey is COMPLETE because the breadth, identities and available comparison
layers support a defensible next reverse. It does not require every rendering
or physics internal to be solved. The exact next causal question and competing
priorities are in next.md and portability-backlog.md.

All research outputs are under ps2-research; proprietary payloads, screenshots,
dependencies and raw scratch remain ignored. Existing master was reused, no
historical branch or Course SDK content was modified. Commit includes only
this phase's source/test/docs/metadata and the PS2 README index. No push.
CDELTA1 stops here.
