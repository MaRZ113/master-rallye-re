# Bounded decal implementation

`XtrailFidelityMode=0` is Stock/default. Mode1 changes only verified X-Trail
CAR13/root.14 when working ReflectionMode4 is active and the baseline coordinate
policy is Stock. Existing RaceModelMode1 body partition stays independent.

The source-normal table contains20position hashes, original normal float32 bits,
UV bits and grayscale diffuse guards. Original PC normals independently match
PS2 within1.19e-7; UVs match exactly. XYZ geometry is not embedded. Current complete
CPU-mirror coverage, VB/IB generations/revisions and full14-face digest must match,
and every current vertex's UV/diffuse must be source-compatible. Missing/ambiguous
data returns the original draw path. Same triangle count/texture/callsite alone
cannot admit anything. Unsupported executable/version/mode defaults off.

New normals augment the current24-byte XYZ/diffuse/UV records to36-byte
XYZ/normal/diffuse/UV records. The42triangle vertices are expanded in current
original IB order, retaining original positions, UV, tint and winding. There is
one native `DrawPrimitiveUP`, replacing the original DIP; no original-plus-overlay
pass, delayed replay, private actor or full body replacement. This format change
is necessary because PC's original0x142 upload has no normals for environment
coordinates. All normals remain original float32; no invented sphere/smoothing.

Current race generation/owner certificate, same native/tracked world and texture1
matrix, generic original emitter, native/effective shaders/buffers/textures/states,
opaque/Zwriting material, standard primary texture×diffuse/UV0, disabled stage1,
disabled stage2, CURRENT result register and texture-generation admission are
mandatory. Drivers must support ADD, normal TEXGEN, two stages/textures and14faces.
No expensive native buffer readback or per-frame disk scan is introduced. A bounded
16-entry cache is keyed by device/reset/resources/generations/revisions/ranges.

Stage1 temporarily uses ADD(CURRENT,TEXTURE), camera-space-normal TCI and COUNT2,
with the existing Mode4 mixed source. Stage0, primary texture, world/view/projection,
sampler policy, alpha test/blend, depth test/write, culling and fog are preserved.
No PS2 alpha-normalization or pixel-parity claim is made.

The native transaction captures8stage1states, texture1, FVF, original stream0
and indices/base. It marks attempted writes before each setter, restores only
changed/attempted slots, retains GetTexture/GetStream/GetIndices references, and
arms possible UP stream/index side effects even when the native draw fails. Both
bindings are restored defensively. This follows the project's existing D3D8
capture/UP restoration discipline; no D3D9 behavior is silently assumed as a PS2
or retail-driver contract. [Microsoft's D3D9 UP documentation](https://learn.microsoft.com/en-us/windows/win32/api/d3d9/nf-d3d9-idirect3ddevice9-drawprimitiveup)
is only a comparative API warning about stream side effects.

Partial setter failure repairs before Stock fallback. Once a draw or native
mutation is committed, exception handling returns handled status after repair;
it cannot replay the original geometry. The original submitted UP HRESULT is
returned even if later restoration fails. Pending repair blocks later draws via
the existing wrapper repair path. Real Reset releases retained references/caches;
failed Reset remains gated by the reflection owner; window reset-echo never clears
an unrecovered transaction. A successful real Reset clears the recovery gate.

Only0001 overlay changed: CMake source/test target, draw hook/repair in staged
visual_wrappers, and staged wrappers Reset callbacks. The original renderer and
0002generator patch remain unchanged; exact Git-object/patch/generator checks pass.
`.build`/`.staging` are reused. No new texture/model assets or game writes.

Diagnostics are separately opt-in and bounded to one unsuccessful and one successful
record/device generation. `ps2_xtrail_decal` reports expected source hash, actual
upload validation, native generation/revision, apply/draw/restore HRESULT and pending
state. Expected hash with `source_upload_verified=false` is explicitly not a match.

Wheel texture/UV transplantation and complete mode20 headlight rendering were not
implemented. Their exact source contracts and missing admission links are reported
separately. Frontend models are entirely unchanged.
