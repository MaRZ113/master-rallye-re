# Original reflection pilot: independently checked runtime evidence

The first pilot has a **technical runtime PASS** for its selected Tata material;
PS2 visual parity was not achieved. The supplied A/B audit was checked against
the original local session and F10 files. These results describe the original
DLL below, not the new mixed-source implementation.

| Artifact | SHA-256 |
|---|---|
| Original PS2-enabled DLL recorded by both sessions | `4ea89fa69d7fcb3f498a15f5707ed70a69c0d97b748a55a00a765a28f0658675` |
| Stock session `session-20261013-030203-51776.jsonl` | `6de38afe3ec669ac83ed6cc62ede300a276431ce12d34fe8adf729934eebe5f6` |
| Mode-1 session `session-20261013-030244-21152.jsonl` | `827a7814dd65e6a30a7f46db32848bb742b73e3a659e0535f5d80653ac92c9fb` |
| Stock F10 `frame-51776-d1-00003068.jsonl` | `ceec7a5c95074b9c84d67228799d528086438a8e1d73c0ab9fad0852667b1549` |
| Mode-1 F10 `frame-21152-d1-00001724.jsonl` | `27e6fb97f59633cb396520dad0eebc753ad1db84de1189d05fe66f041d8204d0` |

The logs were read from `D:\Game\Master Rallye Pristine\MRRRenderer\logs`.
The user audit pairs Stock screenshot `tata_0.jpg` with frame 3068 and mode-1
screenshot `tata_1.jpg` with frame 1724. Screenshots and raw logs are private
runtime evidence; they are not included in the source handoff.

## Draw identity and state transaction

The accepted geometry signature is
`f80ae53d8c8691ebb8387680b0555343e10100459949c56e3338c484b680e669`.
It belongs to Tata `car.dx` compiled record 19, containing 55 triangles and
48 source vertices. The live call in both F10 frames is
`DrawIndexedPrimitive(4,3746,48,11499,55)`.
Those numerical arguments are corroborating observations, not classifier rules.

At mode-1 frame 324, the exact geometry is rejected with
`live_race_owner_unverified`. At frame 328 it is accepted with
`exact_tata_bonnet_native_opaque_environment_material`, current VB/IB generations
624/625 and revisions 282/357. These observations support the existing fail-closed
owner and resource-generation checks; they do not justify relaxing them.

At F10 frame 1724 the actual native sequence is:

| Sequence | Native operation | HRESULT |
|---:|---|---:|
| 479 | Stage 1 COLOROP = ADD (7) | 0 |
| 480 | Stage 1 texture = private weighted ENV image | 0 |
| 481 | Original 55-triangle indexed draw | 0 |
| 482 | Restore original stage-1 texture | 0 |
| 483 | Restore COLOROP = MODULATEALPHA_ADDCOLOR (18) | 0 |

Stock frame 3068 contains the same target draw at sequence 479 without the four
PS2-port native overrides. WORLD, VIEW, PROJECTION and TEXTURE1 matrix bits match
between these target calls. The baseline annotation `reflection_feature=Stock`
and its `reflection_modified_draws=0` counter describe the frozen renderer's
separate feature. The explicit `native_override` events are the evidence for
this extension. The draw record's logical state is intentionally unchanged.

## Correct target description: two body-panel regions

The historical classifier name says "bonnet". The selected source record is
more accurately a **Tata body-panel material with hood and roof regions**.
The runtime audit finds changes in both screen regions; the windshield, bumper
and sampled terrain remain unchanged.

Independent source reconstruction finds 44 exact XYZ positions among the
48 source vertices and two exact-position shared-edge components, containing
28 and 27 faces. Raw index connectivity instead splits them into 28/17/10
because material/vertex seams duplicate indices. These are geometry component
counts, not model-instance counts. Their compact bounds and screen projection
are recorded in [body-panel-components.json](body-panel-components.json).
Source faces 0–27 project approximately to (595.325,484.038)–(1315.839,792.490);
faces 28–54 project to (769.604,165.934)–(1132.453,253.715). This calculation uses
captured WORLD/VIEW and the effective Free Camera projection, not the different
game-facing logical projection. It was independently regenerated from the
hash-checked retail DX and both target frame records using the read-only SDK.

The compiled-source component relationship is `CONFIRMED_BY_BYTES`.
Associating those source regions with the screenshot's hood and roof through
captured matrices is `STATIC_INFERENCE`; it is not a per-pixel draw mask.
The native target draw and its four successful override/restore operations are
confirmed live PC proxy observations. No PS2 live draw was captured here.

## What the A/B can and cannot explain

The supplied screenshot audit reports warmer/darker paint: mean RGB change is
approximately (-14.88,-32.55,-44.88) in the hood ROI and
(-17.44,-29.38,-35.16) in the roof ROI. These are rectangular image samples,
not geometry masks or a calibrated PS2 comparison.

Mode 1 changed both the environment texture and COLOROP. This test therefore
does not isolate the cause of the lost native PC highlight. It also lacked the
original PS2 48/128 framebuffer term. The next controls separate those changes
before interpreting the new mixed-source result.

Both sessions also contain an applied foliage Mode-3 event, at frames 474 and
327 respectively. There is no measured contamination of the Tata draw, but all
foliage, pixel-probe and course-object experiments must be disabled for the next
reflection test. The session files have 33/16 malformed `freecam_window_input`
lines (`activation_result` lacks string quotes); both F10 files parse without
errors. This logger limitation is retained without changing the frozen renderer.
