# R5V-F.2c validation status

| Gate | Status | Evidence |
|---|---|---|
| Research branch and repo-local outputs | PASS | research/r5v-f-2b-native-mercedes-cook-proof; artifacts stay under this repository's ignored research-output tree |
| Runtime car cook | PASS | cook-b/car-cook.log lines 1591-1614: miss, car.gxm read, retail build, save and reload |
| Runtime wheel cook | PASS | same log lines 1620-1643 |
| Runtime complete cook | PASS | cook-a/complete-cook.log lines 1499-1522 |
| One-session three-role recook | NOT YET | complete was a cache hit in the later car/wheel session |
| Rev135 parser and geometry | PASS | all three strict modern parser results VALID |
| Legacy rev127 render comparison | PASS WITH TINY DRIFT | identical counts, topology, indices, normals, UVs and AABB; color/position rounding noted |
| Authentic car tag101 structure | PASS | finite, in-range, closed, Euler 2, convex, serializer roundtrip |
| Legacy tag101 auxiliary comparison | OPEN | 36 secondary descriptor bytes differ; meaning unresolved by current collision tooling |
| Material/texture closure | PASS | 25/25 unique non-null DXT dependencies resolve, parse, hash-match and load |
| Cook A snapshot | FROZEN FOR DETERMINISM | three DX files copied and hash-verified in cook-a/cache_snapshot |
| Junction source bugfix | PASS | helpers compare Get-Item.Target; creating-to-created recovery is explicit and regression-tested |
| Cook B | WAITING_FOR_HUMAN | exact clean-cache instructions prepared |
| Cook A/B hashes | WAITING | no fresh full Cook B set |
| Junction removal | NOT RUN | must follow determinism comparison and use safe helper |
| Cache-only package | NOT READY | gated on Cook B and collision classification |
| Portability runtime | WAITING | short test instructions prepared; package not yet built |
| Final Mercedes ID26 acceptance | BLOCKED | no cache-only proof; collision auxiliary semantics open |

This phase does not add ID27, modify class mappings, or begin tracks. No push is part of the phase.
