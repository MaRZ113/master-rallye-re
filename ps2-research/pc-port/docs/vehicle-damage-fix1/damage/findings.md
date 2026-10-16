# DAMAGE-FIX1: bounded runtime comparison

## Confirmed current supplied evidence

Inputs are the original read-only logs in `D:/Game/Master Rallye Pristine/MRRRenderer/logs`. Exact capture hashes, original draw layouts, FVF, buffer generations and texture generations are retained in `runtime-comparison.json`. Executable SHA is `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`; both captures identify proxy `ac0e0ddd779264ce7cbc990d7534c10e9bba13a75630fa751478374c44afb3fc`.

- Frame23999:790 draw records; original main thirteen CAR records are suppressed (`forwarded=false`); private BODY submissions total1980 triangles, the entire unconditional original PS2 CAR including restored crew. The primary batch is1330 faces; static crew and separate trim/glass/lamp draws account for the rest. Root0 is filtered221 faces and root7 filtered6; no evidence of duplicated source crew in this capture.
- Frame32683:606 draw records; original main thirteen CAR records are forwarded (`forwarded=true`). Private BODY submissions total14 triangles only, the separately working number decal. Crew, main chassis and glass source draws have reverted to native. Thus the visible regression is a replacement/suppression fallback, not merely a still-active PS2 body with a failed Mode4 texture transaction.
- Healthy original buffers are VB generation701 and IB700. Damaged sources are relocated into VB1293 and VB1508, with IB1302; per-record vertex/triangle counts, FVF layouts and native primary/secondary texture generations remain consistent. These observations prove relocation/new upload resources, not unchanged geometry or topology bytes.
- All original BODY draw WORLD matrices within each capture are bit-identical. This rules out a visible per-draw chassis WORLD split in these captures; it does not independently establish the private native owner queue certificate.

Draw ordinals and pointer values are diagnostic observations only, never persistent identity.

## Exact remaining gate limitation

The supplied session has one-shot claim-bit diagnostics. It records successful replacement at15133 and16189 with draw/restore HRESULT0, but no later gate/digest identifying the damage fallback. The session extends past the F10 frames; late details are absent due bounded one-shot logging, not proven file truncation.135 malformed JSON lines are skipped and counted by this comparison; relevant race/reflection records parse successfully. Neither F10 has vertex/index bytes or current queue/owner/model pointers; no buffer sidecars exist beside these logs.

Source code revalidates resource generations and revisions, then recomputes exact position-only `source_hash` at gate7 after relocation. A changed position digest is a plausible cause. A changed native hierarchy/current owner gate could also fail earlier. Do not label gate7 as runtime-proven until new bounded gate telemetry records it.

## Minimal safe next observation

For each of healthy, first damage and further damage, collect one same-session F10 containing the exact current owner/model/queue identity, gate/reason, full source geometry digest, stable normalized topology+ordered UV+diffuse certificate, source vertex count, FVF, VB/IB generations and upload revisions. Export only the13 candidate records' mirrored raw current vertex/index ranges, under a capped single-frame diagnostic. Current buffer copies must be generation/revision checked before and after copying. No GPU depth read or native mutation is needed.

A damage-aware acceptance certificate must preserve exact source topology and ordered immutable attributes, current owner/model and native resource generations; it must never replace exact source identity with draw count, texture name, historical pointer or a loose position tolerance. Terrano's current code only accepts its unique330-vertex/324-face ordered-UV plus normalized topology digest under a current native BODY proof; it neither establishes X-Trail's certificate nor transfers deformation to private geometry.

For genuine damage continuity, first prove a source-backed PC-to-PS2 vertex correspondence and transfer actual native position deltas to corresponding private vertices. Positions alone can have duplicated UV/material seams with conflicting deltas. Unknown or ambiguous correspondence, topology or upload revisions must retain explicit Stock fallback rather than render an undamaged private replacement while claiming native damage preservation.


## New same-session DAMAGE-FIX1 probe evidence (PID47284)

The user supplied healthy1869, damaged2684 and further-damaged4497 captures using proxy `dc8261a32f5908f3ad4a0d43559ea4b0a4508e2fed1bd30d0f1d0f2ca8a5a70f`. `trio-analysis.json` records hashes and exact per-source UV/topology checks without embedding proprietary source bytes.

**Exact first failed gate is now confirmed:** race gate0, native context_gate5. Target packet46152728, instance595858720, compiled model518940072 and root518852664 remain unchanged. The healthy target context completes gate7. In damaged records, `owner_matches_last=true` additionally compares all32 reconstructed root mesh slots, strongly isolating the failure to the emitted current mesh not belonging to the original model root list. This establishes a current queue-owner/model association but does not yet authorize replacement of unknown private clone meshes. A bounded hierarchy/clone-membership certificate is required; simply dropping the `found` check would weaken ownership validation.

All captured source records preserve their exact original ordered UV plus normalized topology digest. PC15 (80vertices/140faces) changes its position digest at first damage; PC0 (362vertices/265faces) changes at further damage. Original healthy positions match protected PC source bit-for-bit. PC15 moves10 native vertices with maximum component displacement0.199643254; further PC0 moves6 with maximum0.198690176. Exact duplicate source-position groups have no conflicting current native deltas in these samples.

The generic32-row capture budget does not include the entire13-record target in every frame: healthy captures11, first damage5, further damage6. Missing records are explicit in `trio-analysis.json`; do not label all13 independently runtime verified from this set.

Position candidate feasibility for private PS2 geometry is documented separately. Root17 has172 referenced PS2 vertices and no unmapped candidate within0.005 of original PC15;18 duplicated native-slot candidate groups all agree on captured native deltas, and30 PS2 vertices would move. This is a source-candidate construction tolerance, never runtime identity. Filtered PS2root0 has8 vertices not mapped to PC0 alone, although some have other-source counterparts; a complete original-source mapping must account for those static interior differences. No private geometry or game memory was modified during this analysis.


### Reproducible index-only deformation draft

`generate_correspondence.py` verifies the protected PC source and private converted PS2 CAR hashes, then emits only PS2 global vertex indices, native candidate indices and exact certificate hashes. It embeds no original XYZ, UV, native triangle stream or textures. The draft remains in ignored `generated/` for main integration review. Original positions must instead come from runtime HEALTHY data admitted by all three certificates: original full geometry hash, exact ordered native position SHA, and exact ordered UV/native triangle stream SHA. CPU positions are data-only references, never retained native pointers. A new process which starts already damaged has no healthy reference and must retain Stock.

The original compiler swaps the first two indices of every source DX triangle. Applying exactly that conversion yields the complete native ordered UV-plus-winding/index stream certificate in all22 sampled target source observations. This is stricter than sorted unoriented topology. Original healthy ordered-position SHA matches all11 captured profiles. The two changed sources correctly fail ordered-position SHA after damage but retain the stricter UV/winding signature.

The final whitelist includes **all** native source indices within the bounded offline source correspondence tolerance, rather than selecting a nearest candidate at runtime. All whitelisted candidate native deltas agree exactly (maximum difference0) in every available sampled source. Future disagreement, missing reference, revision change or certificate mismatch must fail closed before any chassis suppression. Source0/7 have explicitly count0 mappings for8/4 authored static interior vertices; those are not silently assigned guessed nearest positions.

Available FVF0x152 samples show no normal/color change against healthy. The actually deformed records0 and15 use FVF0x142/24-byte vertices and do not carry normals; no claim is made about deformation of original PS2 normals from these captures. Main integration should report its explicit normal policy and preserve source normals unless a independently justified update is implemented.
