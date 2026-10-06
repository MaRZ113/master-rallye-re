# R-GFX4-5 continuation #4: stable semantic authorization

The native ReflectionScope implementation is unchanged: requested NORMAL TCI → draw-local REFLECTIONVECTOR retaining low16 bits → one original draw → exact native restore. No reflection intensity, texture, matrix, vertex color, lighting or shader change.

Authorization now accepts either unchanged strong live body proof or a full-key `PROVEN_VEHICLE_BODY_ENV` entry learned by that oracle. Every draw still passes exact-build/race/mapped geometry/rigid WORLD/material validation. Targets remain opaque Z-writing FVF0x152 with stock stage1 env and CAMERASPACENORMAL. Wheels0x112,brake0x102,alpha/glass,unproven static env and unknown resource/material/LOD keys remain Stock. Similar material alone cannot seed the registry. An identical proven vehicle asset intentionally works on another instance without that instance's current four-wheel proof.

Synthetic wrapper regression sustains two-wheel frames beyond object grace and captures positive learned reflection while live constellation_id=0. Full wheels returning produces no reflection gap. Previously learned brake-off body signatures now return immediately, strengthening the former one-frame Stock expectation; both brake layers still produce zero writes. Stock mode performs no native reflection writes even with registered proof. Failed temporary/restore/native draw contracts and logical/native TCI restoration remain unchanged.

F10 adds `vehicle_semantic_source`, `semantic_signature_id/state`, `object_constellation_id` at draw time and `semantic_owner_return_rva`. Bounded `vehicle_semantic_signature` rows record first learning frame/epoch, origin constellation/four wheel IDs/reason mask/grace and full canonical words/resource generations. This provenance is separate from current object classification, which may legitimately be CANDIDATE/UNKNOWN for a modified learned draw. Frame-end proof never retroactively replaces the draw-time source.

Frame counters expose learned signatures,live body draws,learned/live modified reflection draws,promotions,invalidations and unproven eligible-material observations. Rejections include cold/unproven candidates, not a proven static-world taxonomy. No semantic-toggle-rate claim is made from sampled summaries. The analyzer validates discovery provenance, exact canonical key/hash/generations, learning lifetime and current material plus adjacent native setters/restores; it preserves legacy/live four-wheel audit requirements.

Successful Reset and scene/non-race-only/failed Present clear the registry; surviving MANAGED resources require relearning. This conservative policy preserves established Reset/menu contracts. Within a continuing race, transient object proof loss does not clear shared asset proof. See [classification](vehicle-classification.md) and [human handoff](runtime-handoff.md).


---

## Historical continuation #3 and earlier evidence

# R-GFX4-4 reflection ownership update

R-GFX4-3 supplied human captures prove actual native execution: E-normal-view39 modifications/2735 triangles/78 writes; E-backview17/1623/34, with successful per-draw restoration. Brake-off cam2 has22/1304/44; brake-on falls to0 because the old whole-body semantic predicate rejects a0x102 mutation. The native reflection implementation and appearance are unchanged in continuation #3.

Object proof now accepts dynamic or repeated structural four-wheel admission and bounded retained identity. [Vehicle classification](vehicle-classification.md) specifies the anchors, grace, conflicts and invalidation. Current draw gating remains opaque BODY0x152 + NORMAL/DIFFUSE + stock stage1 env/NORMAL TCI. Unseen signatures need one complete-frame draw proof;0x102 brake base/glow, wheels and alpha always stay Stock. No texture matrix, texture, intensity, UV, combine, lighting or shader changes. New candidate's brake/start visuals remain pending human runtime.

The earlier prototype description below is historical where it requires a dynamic-only chassis; native TCI behavior and exclusions remain applicable.

# ViewDependent2D prototype boundary

R-GFX4-1 deliberately blocked this feature. R-GFX4-2 recognizes ViewDependent2D as an opt-in draw-local experiment; Stock remains default. Unknown EXE hash forces Stock and disables semantic classification. ConfigVersion/missing/invalid behavior and AF/FOV/shadow policy retain closed R-GFX3 contracts.

Only the mapped DrawIndexedPrimitive owner can qualify: strong VEHICLE_BODY constellation, race projection, known resource signature, rigid WORLD, exact FVF 0x152 (XYZ/NORMAL/DIFFUSE/TEX1), alpha blend=0, depth write=1 and active stage1 stock env family. Wheels 0x112, no-normal 0x142, alpha/likely glass, frontend preview, static world, terrain/road/vegetation/particles/UI and unknown objects remain stock. DrawPrimitive has no positive vehicle owner in this map and is deliberately excluded; its forwarding/shadow behavior is tested unchanged.

Pinned D3D8 TCI high bits are CAMERASPACENORMAL=0x10000 and CAMERASPACEREFLECTIONVECTOR=0x30000. Desired temporary DWORD = (previous_effective & 0xffff) | 0x30000. Only issue the native setter if needed; no per-draw GPU getters. Keep native stage1 texture, matrix, COUNT2, color18/current1/texture2, alpha4/current1/texture2, filtering and every other state unchanged. In particular no reflection strength, image replacement, matrix compensation, cubemap or shader.

ReflectionScope owns the temporary native setter and restores the exact preceding effective TCI in its noexcept destructor. It survives draw failure, disabled/failing capture and logger disablement during draw. Original indexed draw executes exactly once and returns its original HRESULT even if restoration fails. Logical game shadow remains NORMAL; effective shadow tracks successful native writes. F10 records both draw-time TCI and restore outcome rather than snapshotting only the restored value.

Failed temporary setter: no override, original stock draw runs once. Failed restore: preserve the original draw HRESULT, mark native_restore_success=false, disable reflection for the device and retain a pending exact restore. Getters continue returning known logical state. Before any subsequent DP/DIP/UP draw or unreviewed state-block operation, retry pending restoration; if that fails, return that failure without executing a draw in leaked state. A successful game setter of the pending value or Reset clears the pending repair. Reflection remains disabled after such failure. This exceptional path is not misreported as transparent or successful; human captures must have zero restore failures.

F10 preserves legacy schema_version=1 and adds object/material/constellation/reason fields, requested_stage1_tci, effective_stage1_tci_for_draw, reflection_mode/candidate/applied/restore fields, and effective_state.stage1. Feature bit8 denotes reflection. Temporary setter/restore are explicit native_override events; per-frame counters report candidates, modified draws/triangles and native write attempts. analyze_vehicle_draws.py audits qualification, low bits and successful adjacent setter/restore events; automated trace PASS is separate from visual quality.

The stock 2D env texture may be authored for normal lookup. Reflection-vector coordinates with the unchanged XY scale/bias may stretch, invert or look worse. Do not tune aesthetics until normal/backview captures and human comparison establish what happens. Native synthetic tests establish state isolation, not rendering quality or hardware coordinate correctness.
