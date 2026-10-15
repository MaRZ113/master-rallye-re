# Current X-Trail race chassis evidence

Evidence: recorded live PC observation plus hash-verified protected retail DX; not yet a private-model runtime acceptance.

`source-live-layout.json` contains all 32 PC physical records, source unsigned float32 triangle multiset signatures, and bounded observations from PID 17120 frames 2358 and 2658. Source car.dx SHA-256: e334085754f81d20d237a70e653b533344771e6409468e2e09252e380b3d063f. SDK reader is reused without modification.

Both actual `race_epoch_snapshot` records certify race generation 6, owner lifetime 1, unique human actor 44310376 / AI 518418728, camera 42565136. Header Free Camera summary fields are older/incomplete and must not replace the later native race certificate. These addresses are observations only; never classifier constants.

## Pose and buffers

Records 0 through 15 have one layout association under the current chassis WORLD, emitter RVA 0x17707e and IB relocation +7461. The native buffers are VB 343998368 (creation serial 624) and IB 261393952 (625). Flat records use FVF0x142 / stride24, reflective records FVF0x152 / stride36. Vertex offsets are packed independently by vertex layout; a universal vertex-base delta would be wrong.

The chassis WORLD is exactly identical across the 16 records within each frame. Translation changes from (221.147583,32.9223518,161.376923) to (221.375519,32.8674164,161.87822), with changed rotation. This supports native chassis-local geometry plus current WORLD; it is not an axis-flip or fitted-transform authority. Native wheel draws must retain their distinct WORLD transforms.

F10 layout association alone is not exact uploaded-geometry confirmation. At interception require exact current CPU mirror geometry digest, resource generation/revision, descriptors, and native matrices matching effective state.

## Smallest safe draw owner join

Reuse the byte-verified shared emitter queue seam and `frontend_queue_owner`: caller stack +0x48 selects the two proved queue iterator layouts; stack +0x28 is manager; manager+0x44/+0x48 is bounded current record pointer vector; selected record stores instance then current mesh. Do not reuse the overwritten stack +0x4c slot as owner. This seam is shared renderer infrastructure, despite its frontend function name.

Current instance+0xb0 -> packet; packet+0x74 -> same instance; instance+0x8c -> compiled model. These offsets have original consumer assembly evidence in PORT2. For racing use current CAR hierarchy membership, not COMPLETE's hardcoded 24 flat leaves. CAR has 27 top-level source paths and 32 physical records including conditional children. Reject unknown node types; traverse only byte-verified structures with caps.

Before suppression combine this draw-local owner/model membership with the live race certificate and exact complete selected chassis signature set. The existing global certificate alone does not associate a draw with the human actor. For a one-human pilot reject multiple competing X-Trail chassis owners and require same source-set/current WORLD coherence. An actor->body packet direct link remains independently unobserved; do not claim one.

## Scope partition

Records0..15: visible rigid chassis/interior/body, including headlamp glass10 and decal13. Driver body/head/helmet16..20, additional lamps21..25 and conditional windscreens26..31 should stay native unless separately proven. Source23/24,26/27,28/29,30/31 intentionally have equal geometry hashes but different conditional materials; a hash alone cannot select those slots. Glow25 occurs in frame2358 and is absent2658, consistent with native braking state. These must not be part of an unconditional complete-set warmup.

Recommended first pilot: replace a proved opaque chassis subset with original CAR.PSM mesh/material subsets; keep native driver, all wheels, conditional lamps/glow and windows. Preserve headlight/decal paths unless replacement is explicitly source-backed and suppresses the corresponding PC record once. Damage revision/topology mismatch -> whole affected chassis Stock before any GPU replacement; never discover mismatch after partial suppression.

No memory reads, writes, private native calls or new debugger breakpoints were performed in this owner pass. Additional capture is only needed if the new draw-local certificate fails; diagnose the exact gate rather than repeat broad sampling.
