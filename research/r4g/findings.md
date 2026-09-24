# R4G findings and runtime closeout

R4F runtime closeout was recorded first in commit dd6b28c. The original game loads the F1 Astero +3-vertex/+1-triangle car.dx, displays the triangle, and retains collision, external/internal damage, breakable glass, wheels and general function.

R4G parsed marker-1339 on all 78 protected DX files. Min/max and center match the render-plus-detailed-tag101-B hypothesis within float tolerance on 78/78. Radius matches within 1e-5 on 77/78; WildCat/car.dx differs by 0.00019169. Direct recomputation is byte-exact on 26/78 full footers. The writer preserves original bytes when no bounds update is required and conservatively rounds outward on edited resources. The exact old exporter rounding/pre-export state remains unresolved; see bounds-1339.md.

Tag101 per-axis scaling passed 27/27 finite hulls. All 28 tag101 sections retained zero-edit identity; the non-finite Forklift outlier was not scaled. The writer recomputes AABB, centroids, base radius and face areas, keeps topology/adjacency/loops, and audits allowed byte fields. C1 later passed human wall-contact testing with normal damage and physics; see runtime-results.md.

B1 car, C1 collision, P1 complete, and W1 wheel Astero candidates are isolated under ignored .research-output/r4g/runtime-tests/. Each has an asset, validation.json and TEST_INSTRUCTIONS.txt. Candidate generation reported zero unexplained diffs. All four candidates later passed original-game runtime testing; see runtime-results.md/json.

The high-level VehicleProject validator and builder check donor provenance, resources, texture dependencies and DXT payloads, fixed draw/material identities, bounds, collision and edits. The builder stages only modified assets and optionally writes a fresh full-tree SMA. Blender now identifies resource roles, exports project JSON, validates/builds, previews limited collision translation/scale and shows bounds on demand.

Regression: 89 Python synthetic tests pass; 78/78 DX and 6960/6960 DXT zero-edit checks pass; 78/78 R4F zero-edit topology rebuilds stay byte-identical; Blender 5.2.2 real Astero/project workflow smoke and 22-resource import/save/reload validation pass. The Blender B1 edit-mode export is byte-identical to the direct B1 candidate (SHA-256 7de8988d598de649d993ae132e80353da60b8393a154da73b5fb4b7e08db56ce). Later human runtime validation: B1, C1, P1 and W1 PASS. MASTER RALLYE VEHICLE SDK v1 is a RUNTIME-CONFIRMED BASELINE within the documented donor-identity limits.
