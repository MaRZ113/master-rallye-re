# Conditional X-Trail CAR branch admission

This is a source-backed registry candidate, not an implemented override. Original PC CAR SHA e334085754f81d20d237a70e653b533344771e6409468e2e09252e380b3d063f and PS2 CAR SHA af57572e92ce47d810666779fb60c8c178f1979feb203416131a3acc81449326 were independently re-read. The original decoder/converter reconstructed all eleven conditional meshes. No original geometry or texture bytes are copied into these reports.

| PC source record | PS2 original branch | Original faces | Identity decision |
|---|---|---:|---|
|23|root.20.0.0 carshiny brake-off|6|Same positions as on, but exact UV and near-identical normals select off uniquely|
|24|root.20.1.0 carbrakelights brake-on|6|Exact UV and near-identical normals select on uniquely|
|25|root.20.1.1 carbrakelights glow|22|Unique examined source geometry and UV; use current native selected draw, never infer brake controller state|
|26|root.21.0.0 carflat plus root.21.0.1 carglass|1+5|Intact left screen is two materials inside one PC draw; partition required|
|27|root.21.1.0 carglass|6|Cracked left screen distinct UV|
|28|root.22.0.0 carglass|6|Cracked right screen distinct UV|
|29|root.22.1.0 carflat plus root.22.1.1 carglass|1+5|Intact right screen requires partition|
|30/31|root.24.0.0 / root.24.1.0 carglass|14 each|Geometry, UV and normals identical across PC branches; PS2 branches have matching UV and differ primary texture. Geometry-plus-UV is insufficient.|

`registry-candidates.json` retains exact source geometry, UV, normal, full corner-attribute SHA-256, original slots, bindings and residuals. Raw-f32 PC/PS2 attribute digests need not equal because tiny normal conversion residuals exist. Their purpose is exact current PC resource admission; use the established geometric correspondence to choose PS2 private data. Material/texture names alone do not grant identity. Full current owner, source buffers, generation/revision, range and current transforms remain mandatory.

## Latest same-session F10 observations

Frame 1657 and 4453 contain the native off-layout at index start13401; frame1786 contains on-layout13419 and glow13437. In the examined source layout these are original index5940/5958/5976 plus the same relocation7461. Frames also contain unrelated six-face draws; count matching is explicitly not authority. Source-layout candidates for conditional windows persist at13503/13557/13575. The registry logs exact frame hashes, native states, matrices and bound textures for later join. No historical draw ordinal or numerical buffer ID is promoted to persistent identity.

This is measured native branch submission evidence. It is not a proof that every matching count belongs to X-Trail, and F10 does not carry the CPU mirror bytes needed to grant a new hash certificate. The native selected packet should choose the branch; no new repeated brake/damage memory reads are needed.

## Smallest safe integration

Brake off/on are separable by position+UV+normal current source signature, then replacement at each selected original draw boundary preserves native switching. Keep native brake-on/glow render states initially: original source `carbrakelights` requires its own recovered mode1/14 runtime contract, not blanket carshiny or generic frontend glass. Geometry/material replacement is distinct from PS2 GS glow parity. Retain original native dynamic diffuse/alpha and restore texture/stream state exactly if adopting this path.

Side windows can be admitted by source signatures, but intact branches must retain the one flat triangle separately from five glass triangles; do not apply glass to all six. Front screen30/31 must either retain the currently bound native texture/state while replacing source geometry, or obtain a verified current texture-resource branch mapping. Using identical geometry/UV as proof of intact versus cracked would be false. Damage-deformed positions must fail closed to native Stock, preserving the already established damage policy.

No integration/build, native memory modification, new per-frame controller reads, source asset writes or renderer edits were performed by this research subtask.
