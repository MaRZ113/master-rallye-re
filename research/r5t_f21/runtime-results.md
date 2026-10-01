# R5T-F.2.1 runtime closeout

Status: **PASS — TREE_CARRIER_CONFIRMED.** Runtime outcomes below are human-reported observations from Demo 9.10.0 France1 tests. The conclusion is limited to the controlled `COLLIDE_finishline03` translation.

## Hybrid observations

| Build | Tree donor | tag1400 donor | OLD collision | NEW collision | FinishArea / RACE COMPLETE | Visual finish anomaly | Texture anomaly | Stability |
|---|---|---|---|---|---|---|---|---|
| T | modified | baseline | absent | present | normal at original unchanged region | none observed | none observed | normal in tested scenario |
| U | baseline | modified | present | absent | normal at original unchanged region | none observed | none observed | normal in tested scenario |

Hybrid T used the modified tag100 tree with baseline tag1339, tag1400, and fixed later region(s). Hybrid U used the baseline tree with modified tag1400 while keeping tag1339 and later region(s) fixed. In both, visible finish support stayed at its original render position and race completion remained in the original region.

## Exact controlled state

- Runtime: Demo 9.10.0; supported executable SHA256 `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`.
- Source: `COLLIDE_finishline03`, GXM Index 47083; 24 triangles, 14 unique positions, 12 coplanar plane groups.
- Edit: translate all unique source positions by +20.0 on GXM X.
- Runtime location: OLD `[-1471.7653, 68.4258, 352.5542]`; NEW `[-1451.7653, 68.4258, 352.5542]`; expected delta `[20.0, 0.0, 0.0]`.
- Tree SHA256: baseline `61137e87426d4b31ebafe1724d79d4e074b4eb813b1a9d746bb9bf14fae10ec9`; modified `eec48f80aa462c30c103b4d0d4fcd7f561d272b9ba1e15064f2d32dc2d520d70`.
- tag1400 SHA256: baseline `c0fbfeea9cc247f6f5024ce41a2f8b29befeabe899dd650dbf944d9d3e9b6e63`; modified `a01be211ab6a14a04930d4fdcda431b45cb5b780bcdb59fc9808fdae3af334ba`.
- Hybrid DX SHA256: T `51db114245db76de54a27c21cd8cb5ec1041850b4b91c35b1c381e36dcb919da`; U `de656fdab5fed3c6186e11ef13d00e1da127852ce3572f1b0d861a56985b3561`.

## Bounded conclusion and evidence

| Claim | Evidence status | Scope |
|---|---|---|
| `COLLIDE_finishline03` source mesh has a runtime physical role; source X +20 moves its physical state by about runtime X +20 | `CONFIRMED_BY_RUNTIME_EDIT` | Tested source edit only |
| The tested physical location follows the tag100 tree donor | `CONFIRMED_BY_SOURCE_RUNTIME_EDIT`, `CONFIRMED_BY_COOKER_DIFFERENTIAL`, `CONFIRMED_BY_FULL_SUFFIX_REGION_SWAP`, `CONFIRMED_BY_TREE_ONLY_REGION_SWAP`, `CONFIRMED_BY_RUNTIME_TEST` | Controlled France1 baseline/modified pair |
| Modified tag1400 is sufficient for this translation | `NOT_SUPPORTED` | Hybrid U retained OLD and lacked NEW collision |
| Modified tag1400 is required for this translation | `NOT_SUPPORTED` | Hybrid T had NEW and lacked OLD collision |
| Source-derived planes bind to records inside the tag100 tree | `HIGH_CONFIDENCE_GEOMETRIC_BINDING` | 12/12 unique coplanar source plane groups matched in both cohorts |
| Render support, tested physical collider, and FinishArea completion are separable in this experiment | `CONFIRMED_BY_RUNTIME_EDIT` | Tested support/collider and unchanged FinishArea |
| All tag100 is collision data; tag100 is a BSP; tag1400 has no physical role | `UNKNOWN` | Not established |

F.1's reciprocal whole-suffix swap established that the tested state followed the tag100-through-EOF donor. F.2 added loader-guided tree parsing and a high-confidence geometric plane match but did not isolate tree-only runtime causality. F.2.1's T/U mismatched hybrids now resolve that boundary: the tested state follows T. This does not prove that every tag100 record is physical, identify the hierarchy as a BSP, or determine tag1400's broader purpose.

## Tree accounting and corpus invariants

General observed wire-size equation: `24 + 12N + 20P + 4Q + 20L + (N−1)`, where N is node count, P optional-record count, Q present optional-list block count, and L optional-list item count. For the current Retail files Q=L=0, so size is `23 + 13N + 20P`.

| France1 tree | Nodes N | Plane-bearing / optional records P | Bytes |
|---|---:|---:|---:|
| Baseline | 360,581 | 180,290 | 8,293,376 |
| Modified | 360,433 | 180,216 | 8,289,972 |
| Delta | −148 | −74 | −3,404 |

The delta is `13*(−148) + 20*(−74) = −3,404`; the selector byte per non-root node is already included in the 13-byte term. There is no unexplained 148-byte residual. All 36/36 Retail courses satisfy the observed count relationships: word0+word1=word2+1; word2=word3; terminal-like count=P+1; total nodes=2P+1. These are structural invariants; logical binary-partition semantics remain UNKNOWN.

For `COLLIDE_finishline03`, 24 source triangles form 12 unique coplanar plane groups; 12/12 groups matched in each baseline and modified cohort. The optional `code` has a high-confidence numeric correspondence to at least one triangle ordinal per group via `code = source_triangle_ordinal − 12`; its semantic meaning remains UNKNOWN. The possible relationship to startpoint Index 0 / Size 12 remains a hypothesis.

## tag1400 and post-test snapshots

The current tag1400 decoder establishes wire structure only. The controlled pair has equal tag1400 sizes (1,809,324 bytes), 64 changed byte positions across 47 ranges, and a separate byte-identical 15,504-byte tag1500 region. The hybrids show modified tag1400 is neither sufficient nor required for the tested translation; broader tag1400 runtime semantics remain UNKNOWN. No uniform-grid, surface-physics, or tyre-contact interpretation is promoted here.

At staging, 2862 non-target files were recorded byte-identical. A later read-only comparison of the runtime folders found 2 differing non-target paths; their origin and effect are UNKNOWN and are not attributed to the runtime or course data. The exact paths, sizes, and hashes are retained in `runtime-results.json`. The course DX, executable, and RaceTest XML identities still pass the staged manifest checks.

## Future work boundary

Course Logic Authoring v0 is a reasonable future phase limited to preserving-unknown-field edits for StartArea, FinishArea, and SplitTime center/Radius/ID. It is only a recommendation; no authoring code or new phase was started here. `ExtraTime` semantics, full tag100 meaning, BSP status, tag1400 runtime role, source `$bsp` relation, other collision classes, and writer grammar remain unresolved.

No writer, source mutation, EXE patch, Blender change, or new runtime experiment was part of this closeout.
