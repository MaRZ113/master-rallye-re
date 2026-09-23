# R4E.1 human runtime results

Source: project owner report supplied with the R4F request. The ignored candidate files were generated from protected original Astero `car.dx`; the candidate hashes are recorded in `runtime-results.json`. No screenshot or game asset is committed.

| Probe | Result | Human observation |
|---|---|---|
| N1, draw 11 chrome/chromebar, all 192 normals +90° about source +Y | **PASS — CONFIRMED_BY_RUNTIME** | Reflection/shading visibly changed on the selected chrome/chromebar; geometry remained in place and unchanged in shape. This is consistent with the recovered D3D8 camera-space-normal environment mapping path. |
| M1, body draw 7, feature mask `0x07 → 0x03` | **PASS — CONFIRMED_BY_RUNTIME** | Targeted environment/reflection contribution disappeared. Primary body/livery texture stayed visible; chrome, rims and chromebar remained reflective. |

N1 confirms the DX normal writer is consumed by the original runtime. M1 confirms the serialized `0x04` feature bit controls the runtime material feature mask, `base_env` shader family and slot-1 environment stage for this material. Both probes retained the structurally audited non-target data. No constant-normal fallback is needed.

**SAME-TOPOLOGY VEHICLE SDK V1 BASELINE: FROZEN.** Runtime-confirmed: position, normal, UV and vertex-color writing; same-size DXT content replacement; alpha and environment material-state writing; tag-101 convex collision translation; vehicle texture dependency resolution and staging/bundling; and Python full-tree `Data.sma` packing with controlled overrides. Dependency resolution and staging are structurally implemented components of the runtime-confirmed end-to-end packaging workflow. Unknown material fields stay raw. Topology-changing DX writing has not yet been runtime-confirmed and is the scope of R4F.
