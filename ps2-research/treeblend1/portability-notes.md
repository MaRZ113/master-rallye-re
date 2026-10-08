# Future foliage portability

This phase closes a bounded material/rendering contract. It does not authorize a PC port or certify every selected source group as IMPLEMENTATION_READY.

| Case | Geometry | Material contract | Texture | Instance mapping | LOD/live subset | Rendering/runtime readiness |
|---|---|---|---|---|---|---|
| A Turkey TURshrub2 | Source group decoded; unmatched paired PC candidate | Ready at static mode2 level | Original GXI identified; conversion/descriptor capture pending | UNKNOWN | UNKNOWN | CPU/embedded contract ready; live validation pending |
| B Italy pinus2 | Source group decoded; selected placement not matched | Ready at static mode6 level | PC pixels reusable with explicit row convention | UNKNOWN | UNKNOWN | Same static contract; live validation pending |
| C France pinetree | Shared source surface under declared tolerances; PC redundancy known | Static mode6 and PC generic alpha candidate | PC pixels reusable | No independent plant owner proved | UNKNOWN | Static contract ready; live sampled alpha/state pending |
| D Hut control | Source subset decoded; DRESSING subpart reuse retained | Ordinary object mode15 | Different image/alpha conventions | Prior bounded ownership only | UNKNOWN | Negative control, no foliage port requirement |
| E France bush01 | 24 shared unsigned surfaces, strict match | PS2 mode2 versus PC tree/_alphatest candidate | PS2 image differs; controlled conversion would be needed | Mesh-subset correspondence ready, plant ownership UNKNOWN | UNKNOWN | Material delta sufficiently specified; live state/alpha pending |

“Ready” above means research knowledge at its declared representation, not a playable content package. None of the cases is labeled universally IMPLEMENTATION_READY.

## Planning classifications

* E: **ASSET_REUSE + MATERIAL_METADATA_EXTENSION + ALPHA_BLEND_FEATURE + DEPTH_STATE_FEATURE + TEXTURE_CONVERSION**. The existing PC geometric surfaces can be reused at the studied subset; native redundant triangles/winding must be handled consciously. Shader/category ownership and runtime sampled-alpha semantics must be supplied before implementation.
* C: **ASSET_REUSE + ALPHA_TEST_FEATURE**. No transfer of the already identical image pixels is inherently needed. Exact coverage/GS-to-D3D state behavior still needs verification.
* B: **ASSET_REUSE + REQUIRES_DEEPER_RE**. Shared image does not prove shared instances/placement. Do not add the PS2 group on top of an unclassified PC pinus2 group.
* A: **COURSE_VISUAL_GEOMETRY_PORT + TEXTURE_CONVERSION + MATERIAL_METADATA_EXTENSION**, as candidate future work, plus **LOD_RESEARCH_REQUIRED / REQUIRES_DEEPER_RE** for ownership and active subsets. The full examined source group remains a geometry delta, not a proved population of sixteen extra shrubs.
* D: **NO_PORT_NEEDED** for demonstrating the ordinary alpha/depth control; broader hut content remains governed by DRESSING1.

**BILLBOARD_RENDER_FEATURE** is not justified by these shader paths. No recovered treeblend LOD crossfade or wind effect needs reproduction in this bounded contract.

A future Course SDK extension could expose original material identity/category and source group provenance to the PC runtime/renderer. A D3D8 proxy requires a reliable mapping to those identities; inference from texture or polygon shape alone is insufficient. PC_RUNTIME_HOOK or D3D8_PROXY_RENDER_FEATURE are architectural options, not implemented decisions.

Remaining implementation-facing facts are selected texture-cache option semantics/alpha conversion, complete inherited GS state, live queue/visibility/culling and shader identity at the corresponding PC draw. Geometry ownership/LOD remain separate from renderer behavior. No SDK, PC renderer, game data or playable course output was changed.
